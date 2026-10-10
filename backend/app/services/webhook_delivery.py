"""Webhook delivery, run by the worker (API spec, Webhook delivery).

When the worker drains an event it queues a delivery for every active webhook of that hotel
that subscribed to the event type (a `ping` goes only to the webhook it names). Due
deliveries are found across hotels through app.webhook_due and each is worked under its
hotel's context:

- body `{id, type, created_at, hotel_id, data}`; event data are ids and numbers, never guest
  contact details;
- header `Diyneco-Signature: t=<unix>,v1=<hex HMAC-SHA256 of "t.body">`;
- https only, no redirects, 10 s timeout, and the host must not resolve to a private,
  loopback, link-local or otherwise internal address (no server-side request forgery);
- a failure is retried after 1 m, 5 m, 30 m, 2 h, 6 h and 12 h; after the seventh failed
  attempt the webhook is disabled and the hotel's owners are emailed.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import ipaddress
import json
import logging
import socket
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit

import httpx
from sqlalchemy import insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import set_tenant
from app.models.events import Webhook, WebhookDelivery

log = logging.getLogger("diyneco.webhooks")

RETRY_AFTER_S = (60, 300, 1800, 7200, 21600, 43200)
MAX_ATTEMPTS = len(RETRY_AFTER_S) + 1
TIMEOUT_S = 10.0
PING = "ping"
Decrypt = Callable[[uuid.UUID, uuid.UUID, bytes], Awaitable[str]]
Notify = Callable[[uuid.UUID, Webhook], Awaitable[None]]


def sign(secret: str, body: bytes, now: int | None = None) -> str:
    t = int(now if now is not None else time.time())
    mac = hmac.new(secret.encode(), f"{t}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={t},v1={mac}"


def verify(secret: str, body: bytes, header: str, tolerance_s: int = 300, now: int | None = None) -> bool:
    """What a receiver does; used by tests and documented for integrators."""
    try:
        parts = dict(p.split("=", 1) for p in header.split(","))
        t = int(parts["t"])
    except (KeyError, ValueError):
        return False
    if abs(int(now if now is not None else time.time()) - t) > tolerance_s:
        return False
    expected = hmac.new(secret.encode(), f"{t}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, parts.get("v1", ""))


class UnsafeDestination(Exception):
    pass


async def check_destination(url: str) -> None:
    """Refuses anything but https to a public address."""
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        raise UnsafeDestination("not an https URL")
    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(parts.hostname, parts.port or 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise UnsafeDestination("host does not resolve") from exc
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if not address.is_global or address.is_multicast:
            raise UnsafeDestination("host resolves to a non-public address")


async def enqueue(s: AsyncSession, events: list[Any]) -> int:
    """Called inside the outbox drain transaction. Queues the first attempt for each
    subscribed webhook. Events without a hotel are platform-level and never sent out."""
    queued = 0
    for hotel_id in {e["hotel_id"] for e in events if e["hotel_id"] is not None}:
        await set_tenant(s, hotel_id)
        hooks = list(
            (
                await s.execute(
                    select(Webhook).where(Webhook.hotel_id == hotel_id, Webhook.status == "active")
                )
            ).scalars()
        )
        if not hooks:
            continue
        rows = []
        for e in (e for e in events if e["hotel_id"] == hotel_id):
            if e["type"] == PING:
                target = str((e["payload"] or {}).get("webhook_id"))
                targets = [h for h in hooks if str(h.id) == target]
            else:
                targets = [h for h in hooks if e["type"] in h.events]
            rows += [
                {
                    "hotel_id": hotel_id,
                    "webhook_id": h.id,
                    "event_id": e["id"],
                    "attempt": 1,
                    "next_attempt_at": datetime.now(UTC),
                }
                for h in targets
            ]
        if rows:
            await s.execute(insert(WebhookDelivery), rows)
            queued += len(rows)
    await set_tenant(s, None)
    return queued


def body_of(event: Any) -> bytes:
    data = dict(event.payload or {})
    data.pop("webhook_id", None) if event.type == PING else None
    return json.dumps(
        {
            "id": str(event.id),
            "type": event.type,
            "created_at": event.created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "hotel_id": str(event.hotel_id),
            "data": data,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


async def deliver_due(
    sessionmaker: async_sessionmaker[AsyncSession],
    client: httpx.AsyncClient,
    decrypt: Decrypt,
    *,
    notify_disabled: Notify | None = None,
    guard: Callable[[str], Awaitable[None]] = check_destination,
    limit: int = 50,
) -> int:
    async with sessionmaker() as s, s.begin():
        due = (await s.execute(text("SELECT * FROM app.webhook_due(:n)"), {"n": limit})).all()
    sent = 0
    for delivery_id, hotel_id in due:
        try:
            ok, disabled = await _attempt(sessionmaker, client, decrypt, guard, delivery_id, hotel_id)
            sent += ok
            if disabled is not None and notify_disabled is not None:
                await notify_disabled(hotel_id, disabled)  # after the commit above
        except Exception:
            log.exception("webhook delivery failed unexpectedly", extra={"delivery_id": str(delivery_id)})
    return sent


async def _attempt(
    sessionmaker: async_sessionmaker[AsyncSession],
    client: httpx.AsyncClient,
    decrypt: Decrypt,
    guard: Callable[[str], Awaitable[None]],
    delivery_id: uuid.UUID,
    hotel_id: uuid.UUID,
) -> tuple[bool, Webhook | None]:
    """(delivered, the webhook if this attempt disabled it)."""
    async with sessionmaker() as s, s.begin():
        await set_tenant(s, hotel_id)
        d = (
            await s.execute(
                select(WebhookDelivery)
                .where(WebhookDelivery.id == delivery_id, WebhookDelivery.next_attempt_at.is_not(None))
                .with_for_update(skip_locked=True)
            )
        ).scalar_one_or_none()
        if d is None:
            return False, None  # another worker took it
        hook = (await s.execute(select(Webhook).where(Webhook.id == d.webhook_id))).scalar_one()
        event = (
            await s.execute(
                text("SELECT id, hotel_id, type, payload, created_at FROM app.event_outbox WHERE id = :e"),
                {"e": d.event_id},
            )
        ).first()
        status_code: int | None = None
        error: str | None = None
        if hook.status != "active":
            error = "webhook disabled"
        elif event is None:
            error = "event expired"
        else:
            body = body_of(event)
            try:
                await guard(hook.url)
                secret = await decrypt(hotel_id, hook.id, hook.secret_enc)
                r = await client.post(
                    hook.url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Diyneco-Webhooks/1",
                        "Diyneco-Signature": sign(secret, body),
                        "Diyneco-Event": event.type,
                        "Diyneco-Delivery": str(d.id),
                    },
                    timeout=TIMEOUT_S,
                    follow_redirects=False,
                )
                status_code = r.status_code
                if not 200 <= r.status_code < 300:
                    error = f"HTTP {r.status_code}"
            except UnsafeDestination as exc:
                error = f"refused: {exc}"
            except httpx.HTTPError as exc:
                error = type(exc).__name__
        await s.execute(
            update(WebhookDelivery)
            .where(WebhookDelivery.id == d.id)
            .values(status_code=status_code, error=error, next_attempt_at=None)
        )
        if error is None:
            await s.execute(update(Webhook).where(Webhook.id == hook.id).values(failure_count=0))
            return True, None
        if hook.status != "active" or event is None:
            return False, None
        await s.execute(
            update(Webhook).where(Webhook.id == hook.id).values(failure_count=Webhook.failure_count + 1)
        )
        if d.attempt < MAX_ATTEMPTS:
            await s.execute(
                insert(WebhookDelivery).values(
                    hotel_id=hotel_id,
                    webhook_id=hook.id,
                    event_id=d.event_id,
                    attempt=d.attempt + 1,
                    next_attempt_at=datetime.now(UTC) + timedelta(seconds=RETRY_AFTER_S[d.attempt - 1]),
                )
            )
        else:
            await s.execute(update(Webhook).where(Webhook.id == hook.id).values(status="disabled"))
            log.warning("webhook disabled after repeated failures", extra={"webhook_id": str(hook.id)})
            return False, hook
        return False, None
