"""API keys and webhooks (API spec, Subscription, API keys and webhooks; security spec,
Credentials).

API keys: `dyk_live_` or `dyk_test_` + 32 random bytes in base62, shown once, stored as a
SHA-256 hash with a display prefix. A key holds a subset of a vetted scope list and of its
creator's permissions; sandbox (`dyk_test_`) keys are read-only, and production keys need a
plan that allows them (D50).

Webhooks: https only, events from a fixed list, a signing secret shown once and stored
encrypted. Deliveries are made by the worker (app.services.webhook_delivery).
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert, select, update

from app.audit.writer import write_audit
from app.core import crypto
from app.core.errors import AppError
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork
from app.models.events import ApiKey, Webhook, WebhookDelivery
from app.realtime.outbox import emit
from app.repositories.hotels import HotelRepository
from app.services import plans

BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
PREFIX_LEN = 16  # "dyk_live_" + 7 characters, shown in the UI

READ_SCOPES = frozenset(
    {
        "hotel.read",
        "settings.read",
        "rooms.read",
        "devices.read",
        "menu.read",
        "kitchen.view",
        "orders.read",
        "deliveries.view",
        "stays.read",
        "guests.read",
        "folio.read",
        "payments.read",
        "invoices.read",
        "reports.read",
        "reports.finance",
        "subscription.read",
    }
)
WRITE_SCOPES = frozenset({"rooms.status", "menu.availability"})
API_KEY_SCOPES = READ_SCOPES | WRITE_SCOPES

WEBHOOK_EVENTS = frozenset(
    {
        "NEW_ORDER",
        "ORDER_PENDING_APPROVAL",
        "ORDER_ACCEPTED",
        "ORDER_PREPARING",
        "ORDER_READY",
        "ORDER_DELIVERING",
        "ORDER_DELIVERED",
        "ORDER_CLOSED",
        "ORDER_CANCELLED",
        "ORDER_DECLINED",
        "DELIVERY_ASSIGNED",
        "DELIVERY_RELEASED",
        "PAYMENT_UPDATED",
        "FOLIO_UPDATED",
        "STAY_CHECKED_IN",
        "STAY_CHECKED_OUT",
        "STAY_MOVED",
        "MENU_UPDATED",
        "ADJUSTMENT_REQUESTED",
        "HOTEL_UPDATED",
        "SETTINGS_UPDATED",
        "DEVICE_PAIRED",
        "DEVICE_REVOKED",
    }
)
PING = "ping"


def _base62(nbytes: int) -> str:
    n = int.from_bytes(secrets.token_bytes(nbytes), "big")
    out = []
    while n:
        n, r = divmod(n, 62)
        out.append(BASE62[r])
    return "".join(reversed(out)).rjust(43, "0")


def new_key(environment: str) -> str:
    return ("dyk_live_" if environment == "production" else "dyk_test_") + _base62(32)


def key_scopes(environment: str, scopes: list[str] | set[str] | frozenset[str]) -> frozenset[str]:
    """What a key may actually do: its scopes, read-only for sandbox keys."""
    allowed = frozenset(scopes) & API_KEY_SCOPES
    return allowed & READ_SCOPES if environment == "sandbox" else allowed


# --- API keys -------------------------------------------------------------------------------


def key_payload(k: ApiKey) -> dict[str, Any]:
    return {
        "id": k.id,
        "name": k.name,
        "environment": k.environment,
        "prefix": k.prefix,
        "scopes": sorted(k.scopes),
        "created_by": k.created_by,
        "created_at": k.created_at,
        "last_used_at": k.last_used_at,
        "usage_count": k.usage_count,
        "status": "revoked" if k.revoked_at else "active",
        "revoked_at": k.revoked_at,
    }


async def list_keys(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    keys = (
        await uow.session.execute(
            select(ApiKey).where(ApiKey.hotel_id == ctx.hotel_id).order_by(ApiKey.created_at.desc())
        )
    ).scalars()
    return [key_payload(k) for k in keys]


async def create_key(
    uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any], caller_permissions: frozenset[str]
) -> dict[str, Any]:
    scopes = set(body["scopes"])
    unknown = sorted(scopes - API_KEY_SCOPES)
    if unknown:
        raise AppError(
            "VALIDATION_FAILED",
            "API keys cannot hold these permissions.",
            details={"reason": "scope_not_allowed", "scopes": unknown},
        )
    if body["environment"] == "sandbox" and scopes & WRITE_SCOPES:
        raise AppError(
            "VALIDATION_FAILED",
            "Sandbox keys are read-only.",
            details={"reason": "sandbox_read_only", "scopes": sorted(scopes & WRITE_SCOPES)},
        )
    lacking = sorted(scopes - caller_permissions)
    if lacking:
        raise AppError(
            "PERMISSION_DENIED",
            "You cannot give a key access you do not have.",
            details={"permissions": lacking},
        )
    if body["environment"] == "production":
        current = await HotelRepository(uow.session, ctx).current_plan()
        if current is None or not current[0].features.get("api_production_keys"):
            raise AppError(
                "PLAN_LIMIT_REACHED",
                "Your plan does not include production API keys.",
                details={"resource": "api_production_keys"},
            )
    await plans.ensure_capacity(uow, ctx, "api_keys")
    if ctx.actor_id is None:
        raise AppError("UNAUTHENTICATED")
    secret = new_key(body["environment"])
    key = (
        await uow.session.execute(
            insert(ApiKey)
            .values(
                hotel_id=ctx.hotel_id,
                name=body["name"],
                environment=body["environment"],
                prefix=secret[:PREFIX_LEN],
                secret_hash=crypto.sha256(secret),
                scopes=sorted(scopes),
                created_by=ctx.actor_id,
            )
            .returning(ApiKey)
        )
    ).scalar_one()
    await write_audit(
        uow.session,
        ctx,
        "api_key.create",
        "api_key",
        key.id,
        new_value={"name": key.name, "environment": key.environment, "scopes": sorted(scopes)},
    )
    return {**key_payload(key), "secret": secret}


async def revoke_key(uow: UnitOfWork, ctx: TenantContext, key_id: uuid.UUID) -> None:
    key = (
        await uow.session.execute(
            select(ApiKey).where(ApiKey.hotel_id == ctx.hotel_id, ApiKey.id == key_id).with_for_update()
        )
    ).scalar_one_or_none()
    if key is None:
        raise AppError("NOT_FOUND")
    if key.revoked_at is None:
        await uow.session.execute(
            update(ApiKey).where(ApiKey.id == key.id).values(revoked_at=datetime.now(UTC))
        )
        await write_audit(uow.session, ctx, "api_key.revoke", "api_key", key.id, old_value={"name": key.name})


# --- Webhooks -------------------------------------------------------------------------------


def webhook_payload(w: Webhook) -> dict[str, Any]:
    return {
        "id": w.id,
        "url": w.url,
        "events": sorted(w.events),
        "status": w.status,
        "failure_count": w.failure_count,
        "created_at": w.created_at,
    }


def secret_context(webhook_id: uuid.UUID) -> str:
    return f"webhook_secret:{webhook_id}"


async def list_webhooks(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    hooks = (
        await uow.session.execute(
            select(Webhook).where(Webhook.hotel_id == ctx.hotel_id).order_by(Webhook.created_at.desc())
        )
    ).scalars()
    return [webhook_payload(w) for w in hooks]


async def create_webhook(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]
) -> dict[str, Any]:
    events = set(body["events"])
    unknown = sorted(events - WEBHOOK_EVENTS)
    if unknown:
        raise AppError(
            "VALIDATION_FAILED",
            "Unknown event types.",
            details={"reason": "unknown_events", "events": unknown},
        )
    webhook_id = uuid.uuid4()
    secret = "whsec_" + _base62(32)
    encrypted = await st.keyring.encrypt(str(ctx.hotel_id), secret.encode(), secret_context(webhook_id))
    hook = (
        await uow.session.execute(
            insert(Webhook)
            .values(
                id=webhook_id,
                hotel_id=ctx.hotel_id,
                url=body["url"],
                events=sorted(events),
                secret_enc=encrypted,
            )
            .returning(Webhook)
        )
    ).scalar_one()
    await write_audit(
        uow.session,
        ctx,
        "webhook.create",
        "webhook",
        hook.id,
        new_value={"url": hook.url, "events": hook.events},
    )
    return {**webhook_payload(hook), "signing_secret": secret}


async def _webhook(uow: UnitOfWork, ctx: TenantContext, webhook_id: uuid.UUID) -> Webhook:
    hook = (
        await uow.session.execute(
            select(Webhook).where(Webhook.hotel_id == ctx.hotel_id, Webhook.id == webhook_id)
        )
    ).scalar_one_or_none()
    if hook is None:
        raise AppError("NOT_FOUND")
    return hook


async def test_webhook(uow: UnitOfWork, ctx: TenantContext, webhook_id: uuid.UUID) -> dict[str, Any]:
    """Queues a `ping` event addressed to this endpoint only; the worker delivers it."""
    hook = await _webhook(uow, ctx, webhook_id)
    seq = await emit(uow.session, ctx, PING, ["webhook"], {"webhook_id": str(hook.id)})
    return {"webhook_id": hook.id, "queued": True, "seq": seq}


async def set_webhook_status(
    uow: UnitOfWork, ctx: TenantContext, webhook_id: uuid.UUID, status: str
) -> dict[str, Any]:
    hook = await _webhook(uow, ctx, webhook_id)
    if hook.status != status:
        hook = (
            await uow.session.execute(
                update(Webhook)
                .where(Webhook.id == hook.id)
                .values(status=status, failure_count=0)
                .returning(Webhook)
            )
        ).scalar_one()
        await write_audit(
            uow.session, ctx, f"webhook.{'enable' if status == 'active' else 'disable'}", "webhook", hook.id
        )
    return webhook_payload(hook)


async def deliveries(uow: UnitOfWork, ctx: TenantContext, webhook_id: uuid.UUID) -> list[dict[str, Any]]:
    await _webhook(uow, ctx, webhook_id)
    rows = (
        await uow.session.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.hotel_id == ctx.hotel_id, WebhookDelivery.webhook_id == webhook_id)
            .order_by(WebhookDelivery.created_at.desc())
            .limit(100)
        )
    ).scalars()
    return [
        {
            "id": d.id,
            "event_id": d.event_id,
            "attempt": d.attempt,
            "status_code": d.status_code,
            "error": d.error,
            "next_attempt_at": d.next_attempt_at,
            "created_at": d.created_at,
            "state": "pending"
            if d.next_attempt_at is not None
            else ("delivered" if _ok(d.status_code) else "failed"),
        }
        for d in rows
    ]


def _ok(code: int | None) -> bool:
    return code is not None and 200 <= code < 300
