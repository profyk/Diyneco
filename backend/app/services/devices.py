"""Device registry, pairing and device credentials (API spec, Devices; security spec,
Device and kiosk security).

- A pairing code is 6 random digits, stored as SHA-256(code + pepper), valid 15 minutes and
  single use. Wrong codes count per IP; 5 in 15 minutes locks pairing from that IP.
- Redeeming a code creates the device and returns a 256-bit credential once. A replayed
  pair request returns the stored response without the credential (DECISIONS D23).
- The credential is exchanged for a 1-hour device token bound to hotel, device and room;
  every device request re-checks the binding, so a revoked or rebound tablet stops working.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.writer import write_audit
from app.core import crypto
from app.core.errors import AppError
from app.core.logging import security_event
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.domain import Device, KitchenStation, Room
from app.models.tenancy import Hotel
from app.realtime.outbox import emit, hotel_channel
from app.repositories.devices import DeviceRepository
from app.services.plans import ensure_capacity

PAIRING_TTL = timedelta(minutes=15)
DEVICE_TOKEN_TTL_S = 60 * 60
OFFLINE_AFTER = timedelta(seconds=90)
PAIR_FAIL_LIMIT = 5

# Allowed manual transitions: action -> (from states, to state)
TRANSITIONS: dict[str, tuple[set[str], str]] = {
    "lock": ({"active", "reset_required"}, "locked"),
    "unlock": ({"locked", "disabled"}, "active"),
    "reset": ({"active", "locked", "reset_required"}, "reset_required"),
    "disable": ({"active", "locked", "reset_required"}, "disabled"),
}


def code_hash(st: AppState, code: str) -> bytes:
    return crypto.sha256(f"{code}:{st.settings.pairing_code_pepper}")


def connection(device: Device, now: datetime | None = None) -> str:
    if device.status == "revoked" or (device.kind == "guest" and device.room_id is None):
        return "needs_pairing"
    now = now or datetime.now(UTC)
    if device.last_seen_at is not None and now - device.last_seen_at <= OFFLINE_AFTER:
        return "online"
    return "offline"


def device_payload(device: Device, room: Room | None, stations: list[KitchenStation]) -> dict[str, Any]:
    return {
        "id": device.id,
        "label": device.label,
        "kind": device.kind,
        "status": device.status,
        "connection": connection(device),
        "room": {"id": room.id, "number": room.number} if room else None,
        "stations": [{"id": s.id, "name": s.name} for s in stations],
        "os": device.os,
        "app_version": device.app_version,
        "last_seen_at": device.last_seen_at,
        "paired_at": device.paired_at,
        "created_at": device.created_at,
    }


async def _payloads(repo: DeviceRepository, devices: list[Device]) -> list[dict[str, Any]]:
    rooms = await repo.rooms([d.room_id for d in devices if d.room_id])
    stations = await repo.stations_by_device([d.id for d in devices if d.kind == "kitchen"])
    return [
        device_payload(d, rooms.get(d.room_id) if d.room_id else None, stations.get(d.id, []))
        for d in devices
    ]


def _channels(ctx: TenantContext, device: Device) -> list[str]:
    channels = [hotel_channel(ctx.hotel_id, "ops")]
    if device.kind == "guest" and device.room_id is not None:
        channels.append(hotel_channel(ctx.hotel_id, f"room:{device.room_id}"))
    return channels


# --- Registry ------------------------------------------------------------------------------


async def list_devices(
    uow: UnitOfWork,
    ctx: TenantContext,
    *,
    kind: str | None,
    status: str | None,
    room_id: uuid.UUID | None,
    after: list[Any] | None,
    limit: int,
) -> list[dict[str, Any]]:
    repo = DeviceRepository(uow.session, ctx)
    devices = await repo.list_page(kind=kind, status=status, room_id=room_id, after=after, limit=limit)
    return await _payloads(repo, devices)


async def get_device(uow: UnitOfWork, ctx: TenantContext, device_id: uuid.UUID) -> dict[str, Any]:
    repo = DeviceRepository(uow.session, ctx)
    device = await repo.get(device_id)
    if device is None:
        raise AppError("NOT_FOUND")
    return (await _payloads(repo, [device]))[0]


async def change_state(
    uow: UnitOfWork, ctx: TenantContext, device_id: uuid.UUID, action: str
) -> dict[str, Any]:
    repo = DeviceRepository(uow.session, ctx)
    device = await repo.get(device_id, for_update=True)
    if device is None:
        raise AppError("NOT_FOUND")
    allowed, target = TRANSITIONS[action]
    if device.status not in allowed:
        raise AppError(
            "INVALID_TRANSITION",
            f"A device that is {device.status.replace('_', ' ')} cannot be {action}ed.",
            details={"status": device.status},
        )
    before = device.status
    device = await repo.update(device_id, {"status": target})
    await write_audit(
        uow.session,
        ctx,
        f"device.{action}",
        "device",
        device_id,
        old_value={"status": before},
        new_value={"status": target},
    )
    event = {
        "lock": "DEVICE_LOCKED",
        "unlock": "DEVICE_UNLOCKED",
        "reset": "RESET_ROOM_SESSION",
        "disable": "DEVICE_DISABLED",
    }[action]
    await emit(
        uow.session,
        ctx,
        event,
        _channels(ctx, device),
        {"device_id": str(device_id), "room_id": str(device.room_id) if device.room_id else None},
    )
    return (await _payloads(repo, [device]))[0]


async def reset_room_tablet(uow: UnitOfWork, ctx: TenantContext, room_id: uuid.UUID, reason: str) -> None:
    """Called when a guest leaves a room (checkout, room move): the next guest must never see
    this one's data. The tablet is told to clear its session and cache; guest endpoints
    already answer only for the room's active stay. A locked tablet stays locked."""
    repo = DeviceRepository(uow.session, ctx)
    device = await repo.live_guest_device_for_room(room_id)
    if device is not None and device.status == "active":
        await repo.update(device.id, {"status": "reset_required"})
    await emit(
        uow.session,
        ctx,
        "RESET_ROOM_SESSION",
        [hotel_channel(ctx.hotel_id, f"room:{room_id}")],
        {"device_id": str(device.id) if device else None, "room_id": str(room_id), "reason": reason},
    )


async def reassign(
    uow: UnitOfWork, ctx: TenantContext, device_id: uuid.UUID, room_id: uuid.UUID
) -> dict[str, Any]:
    repo = DeviceRepository(uow.session, ctx)
    device = await repo.get(device_id, for_update=True)
    if device is None:
        raise AppError("NOT_FOUND")
    if device.kind != "guest":
        raise AppError("INVALID_TRANSITION", "Only guest tablets are assigned to rooms.")
    if device.status == "revoked":
        raise AppError("INVALID_TRANSITION", "This device was unpaired; pair it again.")
    room = await repo.live_room(room_id)
    if room is None:
        raise AppError("NOT_FOUND")
    if device.room_id == room_id:
        return (await _payloads(repo, [device]))[0]
    if await repo.live_guest_device_for_room(room_id) is not None:
        raise AppError("INVALID_TRANSITION", "That room already has a tablet. Unpair or move it first.")
    old_channels = _channels(ctx, device)
    old_room = device.room_id
    # A new guest session starts in the new room: the old binding ends, the tablet resets.
    device = await repo.update(device_id, {"room_id": room_id, "status": "reset_required"})
    await write_audit(
        uow.session,
        ctx,
        "device.reassign",
        "device",
        device_id,
        old_value={"room_id": str(old_room) if old_room else None},
        new_value={"room_id": str(room_id)},
    )
    await emit(
        uow.session,
        ctx,
        "RESET_ROOM_SESSION",
        old_channels,
        {"device_id": str(device_id), "room_id": str(old_room) if old_room else None, "reason": "reassigned"},
    )
    await emit(
        uow.session,
        ctx,
        "DEVICE_REASSIGNED",
        [hotel_channel(ctx.hotel_id, "ops")],
        {"device_id": str(device_id), "room_id": str(room_id)},
    )
    return (await _payloads(repo, [device]))[0]


async def revoke(uow: UnitOfWork, ctx: TenantContext, device_id: uuid.UUID) -> None:
    repo = DeviceRepository(uow.session, ctx)
    device = await repo.get(device_id, for_update=True)
    if device is None:
        raise AppError("NOT_FOUND")
    if device.status == "revoked":
        raise AppError("INVALID_TRANSITION", "This device is already unpaired.")
    channels = _channels(ctx, device)
    await repo.update(
        device_id, {"status": "revoked", "revoked_at": datetime.now(UTC), "credential_hash": None}
    )
    await write_audit(
        uow.session, ctx, "device.revoke", "device", device_id, old_value={"status": device.status}
    )
    await emit(
        uow.session,
        ctx,
        "DEVICE_REVOKED",
        channels,
        {"device_id": str(device_id), "room_id": str(device.room_id) if device.room_id else None},
    )


# --- Pairing -------------------------------------------------------------------------------


async def create_pairing(
    st: AppState,
    uow: UnitOfWork,
    ctx: TenantContext,
    kind: str,
    room_id: uuid.UUID | None,
    stations: list[uuid.UUID],
) -> dict[str, Any]:
    repo = DeviceRepository(uow.session, ctx)
    if kind == "guest":
        assert room_id is not None  # noqa: S101 - guaranteed by the request schema
        if await repo.live_room(room_id) is None:
            raise AppError("NOT_FOUND")
        if await repo.live_guest_device_for_room(room_id) is not None:
            raise AppError("INVALID_TRANSITION", "This room already has a tablet. Unpair or move it first.")
    else:
        found = await repo.active_stations(stations)
        if len(found) != len(stations):
            raise AppError("NOT_FOUND", "One of the stations does not exist.")
    await ensure_capacity(uow, ctx, "devices")
    if ctx.actor_id is None:
        raise AppError("UNAUTHENTICATED")
    expires = datetime.now(UTC) + PAIRING_TTL
    for _ in range(5):
        code = f"{secrets.randbelow(1_000_000):06d}"
        taken = (
            await uow.session.execute(
                text("SELECT 1 FROM app.device_pairings WHERE code_hash = :c AND used_at IS NULL"),
                {"c": code_hash(st, code)},
            )
        ).first()
        if taken is None:
            break
    else:  # pragma: no cover - a million codes, 15-minute lifetime
        raise AppError("SERVICE_UNAVAILABLE")
    pairing = await repo.create_pairing(
        {
            "kind": kind,
            "room_id": room_id,
            "station_ids": stations or None,
            "code_hash": code_hash(st, code),
            "created_by": ctx.actor_id,
            "expires_at": expires,
        }
    )
    await write_audit(
        uow.session,
        ctx,
        "device.pairing_created",
        "device_pairing",
        pairing.id,
        new_value={"kind": kind, "room_id": str(room_id) if room_id else None},
    )
    return {"code": code, "qr_payload": f"diyneco:pair:{code}", "expires_at": expires}


async def _new_label(repo: DeviceRepository, kind: str, room: Room | None) -> str:
    base = f"DY-{room.number}-" if room is not None else "KITCHEN-"
    taken = await repo.labels_like(base)
    n = 1
    while f"{base}{n:02d}" in taken:
        n += 1
    return f"{base}{n:02d}"


async def pair(
    st: AppState, uow: UnitOfWork, code: str, info: dict[str, Any], ip: str | None, request_id: str | None
) -> dict[str, Any]:
    ip_key = ip or "unknown"
    if await st.limiter.peek("pair_fail", ip_key) >= PAIR_FAIL_LIMIT:
        security_event("device.pairing_locked", ip=ip)
        raise AppError("RATE_LIMITED", "Too many wrong codes. Try again in 15 minutes.")
    s = uow.session
    found = (
        await s.execute(text("SELECT * FROM app.redeem_pairing(:c)"), {"c": code_hash(st, code)})
    ).first()
    if found is None:
        await st.limiter.hit("pair_fail", ip_key)
        security_event("device.pairing_failed", ip=ip)
        raise AppError("PAIRING_INVALID", "This code is wrong, used or expired. Ask reception for a new one.")
    await set_tenant(s, found.hotel_id)
    hotel = (await s.execute(select(Hotel).where(Hotel.id == found.hotel_id))).scalar_one()
    if hotel.status in ("suspended", "closed"):
        raise AppError("HOTEL_SUSPENDED")
    ctx = TenantContext(
        hotel_id=hotel.id,
        actor_type="system",
        actor_id=None,
        actor_label="Device pairing",
        ip=ip,
        request_id=request_id,
    )
    repo = DeviceRepository(s, ctx)
    pairing = await repo.pairing(found.pairing_id)
    if pairing is None:  # pragma: no cover - the definer function just returned it
        raise AppError("PAIRING_INVALID")
    room = await repo.live_room(pairing.room_id) if pairing.room_id else None
    if pairing.kind == "guest" and (room is None or await repo.live_guest_device_for_room(room.id)):
        raise AppError("PAIRING_INVALID", "This room can no longer be paired. Ask reception for a new code.")
    stations = await repo.active_stations(list(pairing.station_ids or []))
    if pairing.kind == "kitchen" and not stations:
        raise AppError("PAIRING_INVALID", "These stations no longer exist. Ask for a new code.")
    await ensure_capacity(uow, ctx, "devices")
    credential = crypto.random_token("dvc_")
    now = datetime.now(UTC)
    device = await repo.create(
        {
            "label": await _new_label(repo, pairing.kind, room),
            "kind": pairing.kind,
            "room_id": room.id if room else None,
            "credential_hash": crypto.sha256(credential),
            "status": "active",
            "os": info.get("os"),
            "app_version": info.get("app_version"),
            "paired_at": now,
            "last_seen_at": now,
            "last_ip": ip,
        }
    )
    if pairing.kind == "kitchen":
        await repo.set_stations(device.id, [x.id for x in stations])
    await repo.mark_pairing_used(pairing.id, device.id)
    device_ctx = TenantContext(
        hotel_id=hotel.id,
        actor_type="device",
        actor_id=None,
        actor_label=device.label,
        device_id=device.id,
        ip=ip,
        request_id=request_id,
    )
    await write_audit(
        s,
        device_ctx,
        "device.paired",
        "device",
        device.id,
        new_value={
            "kind": device.kind,
            "room_id": str(device.room_id) if device.room_id else None,
            "model": info.get("model"),
        },
    )
    await emit(
        s,
        device_ctx,
        "DEVICE_PAIRED",
        [hotel_channel(hotel.id, "ops")],
        {"device_id": str(device.id), "room_id": str(device.room_id) if device.room_id else None},
    )
    return {
        "device_id": device.id,
        "device_credential": credential,
        "label": device.label,
        "kind": device.kind,
        "hotel": {"id": hotel.id, "name": hotel.name},
        "room": {"id": room.id, "number": room.number} if room else None,
        "stations": [{"id": x.id, "name": x.name} for x in stations],
    }


# --- Device credentials and tokens ---------------------------------------------------------


async def issue_token(st: AppState, uow: UnitOfWork, credential: str, ip: str | None) -> dict[str, Any]:
    s = uow.session
    found = (
        await s.execute(text("SELECT * FROM app.device_lookup(:c)"), {"c": crypto.sha256(credential)})
    ).first()
    if found is None:
        security_event("device.credential_invalid", ip=ip)
        raise AppError("DEVICE_UNAUTHORISED")
    await set_tenant(s, found.hotel_id, actor_device=found.device_id)
    device = await check_device(s, found.hotel_id, found.device_id, room_claim=None, allow_locked=True)
    claims = {
        "sub": str(device.id),
        "kind": "device",
        "dk": device.kind,
        "hid": str(device.hotel_id),
        "rid": str(device.room_id) if device.room_id else None,
    }
    token, _ = st.jwt.sign("access", claims, DEVICE_TOKEN_TTL_S)
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": DEVICE_TOKEN_TTL_S,
        "device_id": device.id,
    }


async def check_device(
    s: AsyncSession, hotel_id: uuid.UUID, device_id: uuid.UUID, *, room_claim: str | None, allow_locked: bool
) -> Device:
    """API spec device checks, in order: credential valid and not revoked, device enabled,
    hotel active, device still bound to this room, room still exists."""
    device = (
        await s.execute(select(Device).where(Device.hotel_id == hotel_id, Device.id == device_id))
    ).scalar_one_or_none()
    if device is None or device.status == "revoked":
        raise AppError("DEVICE_UNAUTHORISED")
    if device.status == "disabled" or (device.status == "locked" and not allow_locked):
        raise AppError("DEVICE_DISABLED")
    hotel_status = (await s.execute(select(Hotel.status).where(Hotel.id == hotel_id))).scalar_one_or_none()
    if hotel_status is None or hotel_status == "closed":
        raise AppError("DEVICE_UNAUTHORISED")
    if room_claim is not None and str(device.room_id) != room_claim:
        raise AppError("DEVICE_UNAUTHORISED", "This tablet was moved. Pair it again.")
    if device.kind == "guest":
        room = (
            await s.execute(
                select(Room.id).where(
                    Room.hotel_id == hotel_id, Room.id == device.room_id, Room.deleted_at.is_(None)
                )
            )
        ).first()
        if room is None:
            raise AppError("DEVICE_UNAUTHORISED")
    return device


async def heartbeat(uow: UnitOfWork, device: Device, body: dict[str, Any], ip: str | None) -> dict[str, Any]:
    ctx = TenantContext(
        hotel_id=device.hotel_id,
        actor_type="device",
        actor_id=None,
        actor_label=device.label,
        device_id=device.id,
        ip=ip,
    )
    repo = DeviceRepository(uow.session, ctx)
    values: dict[str, Any] = {"last_seen_at": datetime.now(UTC), "last_ip": ip}
    if body.get("app_version"):
        values["app_version"] = body["app_version"]
    if "RESET" in body.get("completed_commands", []) and device.status == "reset_required":
        values["status"] = "active"
    device = await repo.update(device.id, values)
    commands = []
    if device.status == "reset_required":
        commands.append("RESET")
    if device.status == "locked":
        commands.append("LOCK")
    return {"status": device.status, "commands": commands, "server_time": datetime.now(UTC)}
