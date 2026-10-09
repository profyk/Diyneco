"""WebSocket gateway (API spec, Realtime WebSocket protocol).

Events are notifications, not data; clients refetch over REST. The source of truth is
`app.event_outbox`: one hub task per API process polls each hotel that has subscribers for
rows with a higher `seq` and fans them out. Rows only become visible after commit, and the
per-hotel `seq` is taken under a row lock inside the writing transaction, so a hotel's
events are seen in order and never before their transaction committed.

Handshake: {"op":"auth","token":...} within 5 s -> {"op":"ready","channels":[...]};
{"op":"subscribe","channels":[...],"since_seq":N} replays the last 24 h after N, then live.
Close codes: 4401 not authenticated, 4403 channel not allowed, 4409 device rebound or
revoked, 4410 hotel suspended, 4429 too many connections (5 per principal).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select, text
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from app.core.errors import AppError
from app.core.state import AppState
from app.db.session import set_tenant
from app.models.domain import DeviceStation, KitchenStation
from app.models.tenancy import Hotel, HotelUser, RolePermission, Session, User, UserRole
from app.services.devices import check_device

log = logging.getLogger("diyneco.realtime")

AUTH_TIMEOUT_S = 5
PING_EVERY_S = 25
REVALIDATE_EVERY_S = 30
POLL_EVERY_S = 0.5
MAX_CONNECTIONS = 5


class Close(Exception):
    def __init__(self, code: int, reason: str = "") -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason


@dataclass
class WsPrincipal:
    key: str  # one per user or device, for the connection limit
    hotel_id: uuid.UUID
    allowed: set[str]
    revalidate: Callable[[], Awaitable[None]]


# --- Authentication ------------------------------------------------------------------------


async def authenticate(st: AppState, token: str) -> WsPrincipal:
    try:
        claims = st.jwt.verify(token, "access")
    except AppError as exc:
        raise Close(4401, "invalid token") from exc
    kind = claims.get("kind")
    if kind == "device":
        return await _device_principal(st, claims)
    if kind == "staff":
        return await _staff_principal(st, claims)
    raise Close(4401, "unsupported principal")  # platform channel arrives with the admin panel


async def _device_principal(st: AppState, claims: dict[str, Any]) -> WsPrincipal:
    try:
        device_id = uuid.UUID(str(claims["sub"]))
        hotel_id = uuid.UUID(str(claims["hid"]))
    except (KeyError, ValueError) as exc:
        raise Close(4401) from exc
    room_claim = claims.get("rid") if claims.get("dk") == "guest" else None

    async def load() -> set[str]:
        async with st.db.sessionmaker() as s, s.begin():
            await set_tenant(s, hotel_id, actor_device=device_id)
            try:
                device = await check_device(s, hotel_id, device_id, room_claim=room_claim, allow_locked=True)
            except AppError as exc:
                raise Close(4409, "device rebound or revoked") from exc
            if (
                await s.execute(select(Hotel.status).where(Hotel.id == hotel_id))
            ).scalar_one() == "suspended":
                raise Close(4410, "hotel suspended")
            if device.kind == "guest":
                return {f"hotel:{hotel_id}:room:{device.room_id}"}
            stations = (
                await s.execute(
                    select(DeviceStation.station_id).where(
                        DeviceStation.hotel_id == hotel_id, DeviceStation.device_id == device_id
                    )
                )
            ).scalars()
            return {f"hotel:{hotel_id}:kitchen:{sid}" for sid in stations}

    principal = WsPrincipal(
        key=f"device:{device_id}", hotel_id=hotel_id, allowed=await load(), revalidate=_noop
    )

    async def revalidate() -> None:
        principal.allowed = await load()

    principal.revalidate = revalidate
    return principal


async def _staff_principal(st: AppState, claims: dict[str, Any]) -> WsPrincipal:
    try:
        user_id = uuid.UUID(str(claims["sub"]))
        session_id = uuid.UUID(str(claims["sid"]))
        hotel_id = uuid.UUID(str(claims["hid"]))
    except (KeyError, ValueError) as exc:
        raise Close(4401) from exc
    if claims.get("mfa_pending"):
        raise Close(4401, "mfa required")

    async def load() -> set[str]:
        async with st.db.sessionmaker() as s, s.begin():
            await set_tenant(s, hotel_id, user_id)
            live = (
                await s.execute(
                    select(Session.id).where(
                        Session.id == session_id,
                        Session.user_id == user_id,
                        Session.revoked_at.is_(None),
                        Session.expires_at > text("now()"),
                    )
                )
            ).first()
            user_status = (
                await s.execute(select(User.status).where(User.id == user_id))
            ).scalar_one_or_none()
            member = (
                await s.execute(
                    select(HotelUser).where(HotelUser.user_id == user_id, HotelUser.status == "active")
                )
            ).scalar_one_or_none()
            if live is None or user_status != "active" or member is None or member.hotel_id != hotel_id:
                raise Close(4401, "session ended")
            if claims.get("perms_v") != member.perms_version:
                raise Close(4401, "access changed")
            hotel_status = (await s.execute(select(Hotel.status).where(Hotel.id == hotel_id))).scalar_one()
            if hotel_status == "suspended":
                raise Close(4410, "hotel suspended")
            perms = set(
                (
                    await s.execute(
                        select(RolePermission.permission_code)
                        .join(UserRole, UserRole.role_id == RolePermission.role_id)
                        .where(UserRole.hotel_user_id == member.id)
                    )
                ).scalars()
            )
            channels: set[str] = set()
            if "orders.read" in perms:
                channels.add(f"hotel:{hotel_id}:ops")
            if "deliveries.view" in perms:
                channels.add(f"hotel:{hotel_id}:room-service")
            if "kitchen.view" in perms:
                for sid in (
                    await s.execute(
                        select(KitchenStation.id).where(
                            KitchenStation.hotel_id == hotel_id, KitchenStation.is_active.is_(True)
                        )
                    )
                ).scalars():
                    channels.add(f"hotel:{hotel_id}:kitchen:{sid}")
            return channels

    principal = WsPrincipal(key=f"user:{user_id}", hotel_id=hotel_id, allowed=await load(), revalidate=_noop)

    async def revalidate() -> None:
        principal.allowed = await load()

    principal.revalidate = revalidate
    return principal


async def _noop() -> None:
    return None


# --- Hub -----------------------------------------------------------------------------------


@dataclass(eq=False)  # identity hashing: each connection is its own subscriber
class Subscriber:
    principal: WsPrincipal
    channels: set[str]
    queue: asyncio.Queue[dict[str, Any]] = field(default_factory=lambda: asyncio.Queue(maxsize=1000))


def envelope(row: Any, channel: str) -> dict[str, Any]:
    return {
        "op": "event",
        "seq": int(row.seq),
        "event_id": str(row.id),
        "type": row.type,
        "channel": channel,
        "occurred_at": row.created_at.isoformat().replace("+00:00", "Z"),
        "data": row.payload,
    }


class Hub:
    def __init__(self, st: AppState) -> None:
        self.st = st
        self.subscribers: dict[uuid.UUID, set[Subscriber]] = defaultdict(set)
        self.last_seq: dict[uuid.UUID, int] = {}
        self.connections: dict[str, int] = defaultdict(int)
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def current_seq(self, hotel_id: uuid.UUID) -> int:
        async with self.st.db.sessionmaker() as s, s.begin():
            await set_tenant(s, hotel_id)
            return int(
                (
                    await s.execute(
                        text("SELECT coalesce(max(seq), 0) FROM app.event_outbox WHERE hotel_id = :h"),
                        {"h": hotel_id},
                    )
                ).scalar_one()
            )

    async def replay(
        self, hotel_id: uuid.UUID, channels: set[str], since: int, until: int
    ) -> list[dict[str, Any]]:
        async with self.st.db.sessionmaker() as s, s.begin():
            await set_tenant(s, hotel_id)
            rows = (
                await s.execute(
                    text(
                        "SELECT id, seq, type, channels, payload, created_at FROM app.event_outbox "
                        "WHERE hotel_id = :h AND seq > :since AND seq <= :until AND channels && :ch "
                        "AND created_at > now() - interval '24 hours' ORDER BY seq"
                    ),
                    {"h": hotel_id, "since": since, "until": until, "ch": sorted(channels)},
                )
            ).all()
        return [envelope(r, next(c for c in r.channels if c in channels)) for r in rows]

    async def add(self, sub: Subscriber) -> int:
        """Registers a subscriber and returns the seq it is live from."""
        hotel = sub.principal.hotel_id
        if hotel not in self.last_seq:
            self.last_seq[hotel] = await self.current_seq(hotel)
        self.subscribers[hotel].add(sub)
        self.start()
        return self.last_seq[hotel]

    def remove(self, sub: Subscriber) -> None:
        hotel = sub.principal.hotel_id
        self.subscribers[hotel].discard(sub)
        if not self.subscribers[hotel]:
            self.subscribers.pop(hotel, None)
            self.last_seq.pop(hotel, None)

    async def poll_once(self) -> None:
        for hotel in list(self.subscribers):
            since = self.last_seq.get(hotel, 0)
            async with self.st.db.sessionmaker() as s, s.begin():
                await set_tenant(s, hotel)
                rows = (
                    await s.execute(
                        text(
                            "SELECT id, seq, type, channels, payload, created_at FROM app.event_outbox "
                            "WHERE hotel_id = :h AND seq > :since ORDER BY seq LIMIT 500"
                        ),
                        {"h": hotel, "since": since},
                    )
                ).all()
            for row in rows:
                for sub in list(self.subscribers.get(hotel, ())):
                    channel = next((c for c in row.channels if c in sub.channels), None)
                    if channel is not None:
                        try:
                            sub.queue.put_nowait(envelope(row, channel))
                        except asyncio.QueueFull:
                            log.warning("realtime subscriber queue full; client will resync")
                if hotel in self.last_seq:
                    self.last_seq[hotel] = int(row.seq)

    async def _run(self) -> None:
        while self.subscribers:
            try:
                await self.poll_once()
            except Exception:
                log.exception("realtime poll failed")
            await asyncio.sleep(POLL_EVERY_S)


# --- Connection ----------------------------------------------------------------------------


async def serve(ws: WebSocket, st: AppState, hub: Hub) -> None:
    await ws.accept()
    principal: WsPrincipal | None = None
    sub: Subscriber | None = None
    try:
        try:
            first = await asyncio.wait_for(ws.receive_json(), timeout=AUTH_TIMEOUT_S)
        except (TimeoutError, ValueError) as exc:
            raise Close(4401, "authenticate first") from exc
        if (
            not isinstance(first, dict)
            or first.get("op") != "auth"
            or not isinstance(first.get("token"), str)
        ):
            raise Close(4401, "authenticate first")
        principal = await authenticate(st, first["token"])
        if hub.connections[principal.key] >= MAX_CONNECTIONS:
            principal = None
            raise Close(4429, "too many connections")
        hub.connections[principal.key] += 1
        await ws.send_json({"op": "ready", "channels": sorted(principal.allowed)})
        sub = await _session(ws, hub, principal)
    except Close as c:
        if ws.application_state != WebSocketState.DISCONNECTED:
            await ws.close(code=c.code, reason=c.reason)
    except WebSocketDisconnect:
        pass
    finally:
        if sub is not None:
            hub.remove(sub)
        if principal is not None:
            hub.connections[principal.key] -= 1


async def _session(ws: WebSocket, hub: Hub, principal: WsPrincipal) -> Subscriber | None:
    sub: Subscriber | None = None
    reader = asyncio.create_task(ws.receive_json())
    sender: asyncio.Task[dict[str, Any]] | None = None
    loop = asyncio.get_running_loop()
    next_ping = loop.time() + PING_EVERY_S
    next_check = loop.time() + REVALIDATE_EVERY_S
    missed_pongs = 0
    try:
        while True:
            waits: set[asyncio.Task[Any]] = {reader}
            if sub is not None:
                sender = sender or asyncio.create_task(sub.queue.get())
                waits.add(sender)
            timeout = max(0.0, min(next_ping, next_check) - loop.time())
            done, _ = await asyncio.wait(waits, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
            if reader in done:
                msg = reader.result()
                reader = asyncio.create_task(ws.receive_json())
                op = msg.get("op") if isinstance(msg, dict) else None
                if op == "pong":
                    missed_pongs = 0
                elif op == "subscribe":
                    sub = await _subscribe(ws, hub, principal, sub, msg)
                    sender = None
                elif op == "ping":
                    await ws.send_json({"op": "pong"})
            if sender is not None and sender in done:
                await ws.send_json(sender.result())
                sender = None
            now = loop.time()
            if now >= next_check:
                await principal.revalidate()
                if sub is not None and not sub.channels <= principal.allowed:
                    raise Close(4403, "channel no longer allowed")
                next_check = now + REVALIDATE_EVERY_S
            if now >= next_ping:
                if missed_pongs >= 2:
                    raise Close(1001, "no pong")
                missed_pongs += 1
                await ws.send_json({"op": "ping"})
                next_ping = now + PING_EVERY_S
    finally:
        reader.cancel()
        if sender is not None:
            sender.cancel()
        if sub is not None:
            hub.remove(sub)


async def _subscribe(
    ws: WebSocket, hub: Hub, principal: WsPrincipal, current: Subscriber | None, msg: dict[str, Any]
) -> Subscriber:
    channels = msg.get("channels")
    if not isinstance(channels, list) or not channels or not all(isinstance(c, str) for c in channels):
        raise Close(4403, "no channels")
    wanted = set(channels)
    if not wanted <= principal.allowed:
        raise Close(4403, "channel not allowed")
    if current is not None:
        hub.remove(current)
    sub = Subscriber(principal=principal, channels=wanted)
    live_from = await hub.add(sub)
    since = msg.get("since_seq")
    if isinstance(since, int) and 0 <= since < live_from:
        for event in await hub.replay(principal.hotel_id, wanted, since, live_from):
            await ws.send_json(event)
    await ws.send_json({"op": "subscribed", "channels": sorted(wanted), "seq": live_from})
    return sub
