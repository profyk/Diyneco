"""Platform admin (API spec, Platform admin; security spec, Platform roles).

Platform requests carry no hotel, so RLS hides every tenant row from them. Cross-hotel reads
come only from the `app.admin_*` definer functions, which return aggregates and never a guest
field. A write to one hotel (status, subscription, support grant) runs under that hotel's
context and is audited there, so the hotel sees what Diyneco staff did (DECISIONS D48).
"""

from __future__ import annotations

import json
import time
import uuid
import zoneinfo
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import insert, select, text, update

from app.audit.writer import write_audit, write_platform_audit
from app.core.errors import AppError
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.tenancy import Hotel, Plan, Subscription, SupportGrant
from app.realtime.outbox import emit, hotel_channel
from app.repositories.hotels import HotelRepository
from app.services.pricing import money

PLATFORM_TZ = zoneinfo.ZoneInfo("Africa/Johannesburg")
TRANSITIONS = {
    "approve": ({"pending_approval"}, "active", "TENANT_APPROVED"),
    "suspend": ({"active"}, "suspended", "TENANT_SUSPENDED"),
    "reactivate": ({"suspended"}, "active", "TENANT_REACTIVATED"),
}
OWNER_EMAILS_SQL = text(
    "SELECT u.email FROM app.hotel_users hu "
    "JOIN app.users u ON u.id = hu.user_id "
    "JOIN app.user_roles ur ON ur.hotel_user_id = hu.id "
    "JOIN app.roles r ON r.id = ur.role_id "
    "WHERE hu.hotel_id = :h AND hu.status = 'active' AND r.code = 'hotel_owner' AND r.hotel_id IS NULL"
)


# --- Reads (aggregates only) ---------------------------------------------------------------


async def metrics(uow: UnitOfWork) -> dict[str, Any]:
    today = datetime.now(PLATFORM_TZ).date()
    row = (
        (
            await uow.session.execute(
                text("SELECT * FROM app.admin_metrics(:d, :m)"), {"d": today, "m": today.replace(day=1)}
            )
        )
        .mappings()
        .one()
    )
    active_now = int(row["active_subscriptions"])
    cancelled = int(row["cancelled_this_month"])
    base = active_now + cancelled
    return {
        "as_of": datetime.now(UTC),
        "hotels": int(row["hotels"]),
        "active_hotels": int(row["active_hotels"]),
        "pending_hotels": int(row["pending_hotels"]),
        "suspended_hotels": int(row["suspended_hotels"]),
        "rooms": int(row["rooms"]),
        "connected_devices": int(row["connected_devices"]),
        "active_stays": int(row["active_stays"]),
        "orders_today": int(row["orders_today"]),
        "orders_this_month": int(row["orders_month"]),
        "mrr": money(int(row["mrr_minor"]), "ZAR"),
        "active_subscriptions": active_now,
        "cancelled_this_month": cancelled,
        "churn_bp": (cancelled * 10000 // base) if base else 0,
    }


async def hotels(uow: UnitOfWork) -> list[dict[str, Any]]:
    rows = (await uow.session.execute(text("SELECT * FROM app.admin_hotels()"))).mappings().all()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "slug": r["slug"],
            "status": r["status"],
            "status_reason": r["status_reason"],
            "created_at": r["created_at"],
            "plan": r["plan_code"],
            "subscription_status": r["subscription_status"],
            "renews_on": r["renews_on"],
            "counts": {
                "rooms": int(r["rooms"]),
                "devices": int(r["devices"]),
                "connected_devices": int(r["connected_devices"]),
                "staff": int(r["staff"]),
                "active_stays": int(r["active_stays"]),
            },
            "last_activity": r["last_activity"],
        }
        for r in rows
    ]


async def analytics(uow: UnitOfWork, days: int) -> list[dict[str, Any]]:
    rows = (await uow.session.execute(text("SELECT * FROM app.admin_analytics(:d)"), {"d": days})).mappings()
    return [
        {
            "day": r["day"],
            "orders": int(r["orders"]),
            "new_hotels": int(r["new_hotels"]),
            "checkins": int(r["checkins"]),
        }
        for r in rows
    ]


async def health(st: AppState, uow: UnitOfWork, realtime: Any) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {"api": {"status": "ok"}}
    started = time.perf_counter()
    try:
        await uow.session.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "latency_ms": round((time.perf_counter() - started) * 1000, 1)}
    except Exception:  # pragma: no cover - reported, never raised
        checks["database"] = {"status": "down"}
    q = (await uow.session.execute(text("SELECT * FROM app.admin_outbox_health()"))).mappings().one()
    oldest = float(q["oldest_pending_seconds"])
    checks["queue"] = {
        "status": "ok" if oldest < 60 else "degraded",
        "pending_events": int(q["pending"]),
        "oldest_pending_seconds": round(oldest, 1),
    }
    subscribers = sum(len(v) for v in getattr(realtime, "subscribers", {}).values())
    checks["realtime"] = {"status": "ok", "subscribers": subscribers}
    provider = st.settings.email_provider
    checks["email"] = {
        "status": "ok" if provider != "console" else "development",
        "provider": provider,
    }
    statuses = {c["status"] for c in checks.values()}
    overall = "down" if "down" in statuses else "degraded" if "degraded" in statuses else "ok"
    return {"status": overall, "checks": checks, "checked_at": datetime.now(UTC)}


# --- One hotel -----------------------------------------------------------------------------


async def _enter(uow: UnitOfWork, ctx: TenantContext) -> Hotel:
    """Switch this transaction to the target hotel's context (for its RLS and audit)."""
    s = uow.session
    exists = (await s.execute(text("SELECT app.admin_hotel_exists(:h)"), {"h": ctx.hotel_id})).scalar_one()
    if not exists:
        raise AppError("NOT_FOUND")
    await set_tenant(s, ctx.hotel_id, ctx.actor_id)
    hotel = await HotelRepository(s, ctx).get()
    if hotel is None:  # pragma: no cover - checked above
        raise AppError("NOT_FOUND")
    return hotel


async def _owner_emails(uow: UnitOfWork, hotel_id: uuid.UUID) -> list[str]:
    return [str(e) for e in (await uow.session.execute(OWNER_EMAILS_SQL, {"h": hotel_id})).scalars()]


async def set_status(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, action: str, reason: str | None
) -> dict[str, Any]:
    allowed_from, target, event = TRANSITIONS[action]
    hotel = await _enter(uow, ctx)
    if hotel.status not in allowed_from:
        raise AppError(
            "INVALID_TRANSITION",
            f"A {hotel.status.replace('_', ' ')} hotel cannot be {action}d.",
            details={"status": hotel.status},
        )
    reason = (reason or "").strip() or None
    if action == "suspend" and not reason:
        raise AppError("REASON_REQUIRED", "Give a reason for the suspension.")
    updated = await HotelRepository(uow.session, ctx).update(
        hotel.version, {"status": target, "status_reason": reason if action == "suspend" else None}
    )
    if updated is None:  # pragma: no cover - row locked by the update itself
        raise AppError("PRECONDITION_FAILED")
    await write_audit(
        uow.session,
        ctx,
        f"hotel.{action}",
        "hotel",
        hotel.id,
        old_value={"status": hotel.status},
        new_value={"status": target},
        reason=reason,
    )
    await emit(uow.session, ctx, event, ["platform"], {"hotel_id": str(hotel.id), "status": target})
    await emit(
        uow.session,
        ctx,
        "HOTEL_UPDATED",
        [hotel_channel(hotel.id, "ops")],
        {"hotel_id": str(hotel.id), "status": target},
    )
    if action in ("approve", "reactivate"):
        for email in await _owner_emails(uow, hotel.id):
            await st.mailer.queue(
                uow,
                hotel_id=hotel.id,
                template=f"hotel_{action}d",
                to=email,
                subject=f"{hotel.name} is live on Diyneco"
                if action == "approve"
                else f"{hotel.name} is active again",
                body=(
                    f"{hotel.name} is now active on Diyneco. Your tablets, kitchen displays and staff "
                    "apps can take orders."
                ),
            )
    return _hotel_status_payload(updated)


def _hotel_status_payload(h: Hotel) -> dict[str, Any]:
    return {"id": h.id, "name": h.name, "status": h.status, "status_reason": h.status_reason}


async def put_subscription(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    s = uow.session
    await _enter(uow, ctx)
    plan = (await s.execute(select(Plan).where(Plan.id == body["plan_id"]))).scalar_one_or_none()
    if plan is None:
        raise AppError("NOT_FOUND", "Unknown plan.")
    if not plan.is_active and body["status"] != "cancelled":
        raise AppError("INVALID_TRANSITION", "That plan is no longer offered.")
    if body.get("renews_on") and body["renews_on"] <= body["starts_on"]:
        raise AppError("VALIDATION_FAILED", "The renewal date must be after the start date.")
    current = (
        await s.execute(
            select(Subscription)
            .where(
                Subscription.hotel_id == ctx.hotel_id,
                Subscription.status.in_(("trialing", "active", "past_due")),
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    values = {
        "plan_id": plan.id,
        "status": body["status"],
        "starts_on": body["starts_on"],
        "renews_on": body.get("renews_on"),
        "limit_overrides": body.get("limit_overrides") or {},
        "cancelled_at": datetime.now(UTC) if body["status"] == "cancelled" else None,
    }
    old = None
    if current is None:
        if body["status"] == "cancelled":
            raise AppError("INVALID_TRANSITION", "This hotel has no current subscription to cancel.")
        sub = (
            await s.execute(
                insert(Subscription).values(hotel_id=ctx.hotel_id, **values).returning(Subscription)
            )
        ).scalar_one()
    else:
        old = {"plan_id": str(current.plan_id), "status": current.status}
        sub = (
            await s.execute(
                update(Subscription)
                .where(Subscription.id == current.id)
                .values(**values, updated_at=text("now()"))
                .returning(Subscription)
            )
        ).scalar_one()
    await write_audit(
        s,
        ctx,
        "subscription.set",
        "subscription",
        sub.id,
        old_value=old,
        new_value={"plan": plan.code, "status": sub.status, "limit_overrides": sub.limit_overrides},
    )
    return subscription_payload(sub, plan)


def subscription_payload(sub: Subscription, plan: Plan) -> dict[str, Any]:
    return {
        "id": sub.id,
        "hotel_id": sub.hotel_id,
        "plan": plan_payload(plan),
        "status": sub.status,
        "starts_on": sub.starts_on,
        "renews_on": sub.renews_on,
        "cancelled_at": sub.cancelled_at,
        "limits": {**plan.limits, **sub.limit_overrides},
        "limit_overrides": sub.limit_overrides,
    }


# --- Plans and flags (platform-wide) -------------------------------------------------------


def plan_payload(p: Plan) -> dict[str, Any]:
    return {
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "monthly_price": money(p.monthly_price_minor, p.currency),
        "limits": p.limits,
        "features": p.features,
        "is_active": p.is_active,
    }


async def list_plans(uow: UnitOfWork) -> list[dict[str, Any]]:
    plans = (await uow.session.execute(select(Plan).order_by(Plan.monthly_price_minor, Plan.code))).scalars()
    return [plan_payload(p) for p in plans]


async def create_plan(uow: UnitOfWork, actor: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    s = uow.session
    taken = (await s.execute(select(Plan.id).where(Plan.code == body["code"]))).first()
    if taken is not None:
        raise AppError("VALIDATION_FAILED", "A plan with that code exists.", details={"reason": "code_taken"})
    plan_id = (
        await s.execute(
            text("SELECT app.admin_create_plan(:c, :n, :p, :cur, CAST(:l AS jsonb), CAST(:f AS jsonb))"),
            {
                "c": body["code"],
                "n": body["name"],
                "p": body["monthly_price"]["amount_minor"],
                "cur": body["monthly_price"]["currency"],
                "l": json.dumps(body.get("limits") or {}),
                "f": json.dumps(body.get("features") or {}),
            },
        )
    ).scalar_one()
    await write_platform_audit(
        s,
        action="plan.create",
        entity_type="plan",
        entity_id=plan_id,
        new_value={"code": body["code"]},
        **actor,
    )
    plan = (await s.execute(select(Plan).where(Plan.id == plan_id))).scalar_one()
    return plan_payload(plan)


async def list_flags(uow: UnitOfWork) -> list[dict[str, Any]]:
    rows = (await uow.session.execute(text("SELECT * FROM app.admin_flags()"))).mappings().all()
    return [dict(r) for r in rows]


async def set_flags(
    uow: UnitOfWork, actor: dict[str, Any], changes: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    s = uow.session
    for c in changes:
        hotel_id = c.get("hotel_id")
        if hotel_id is not None:
            exists = (
                await s.execute(text("SELECT app.admin_hotel_exists(:h)"), {"h": hotel_id})
            ).scalar_one()
            if not exists:
                raise AppError("NOT_FOUND", "Unknown hotel.")
        await s.execute(
            text("SELECT app.admin_set_flag(:k, :h, :e, :u)"),
            {"k": c["key"], "h": hotel_id, "e": c["enabled"], "u": actor["actor_id"]},
        )
        await write_platform_audit(
            s,
            action="flag.set",
            entity_type="feature_flag",
            entity_id=None,
            new_value={
                "key": c["key"],
                "hotel_id": str(hotel_id) if hotel_id else None,
                "enabled": c["enabled"],
            },
            **actor,
        )
    return await list_flags(uow)


# --- Support access ------------------------------------------------------------------------


def grant_payload(g: SupportGrant) -> dict[str, Any]:
    now = datetime.now(UTC)
    return {
        "id": g.id,
        "hotel_id": g.hotel_id,
        "platform_user_id": g.platform_user_id,
        "ticket_reference": g.ticket_reference,
        "reason": g.reason,
        "starts_at": g.starts_at,
        "expires_at": g.expires_at,
        "revoked_at": g.revoked_at,
        "active": g.revoked_at is None and g.expires_at > now,
    }


async def grant_support(
    st: AppState,
    uow: UnitOfWork,
    ctx: TenantContext,
    body: dict[str, Any],
    *,
    session_id: uuid.UUID,
    amr: tuple[str, ...],
) -> dict[str, Any]:
    """Time-boxed (max 60 minutes) read access to one hotel with a ticket reference. Audited
    in the hotel's log, visible to the hotel, which can revoke it, and its owners are emailed."""
    hotel = await _enter(uow, ctx)
    if ctx.actor_id is None:
        raise AppError("UNAUTHENTICATED")
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=body["minutes"])
    grant = (
        await uow.session.execute(
            insert(SupportGrant)
            .values(
                hotel_id=hotel.id,
                platform_user_id=ctx.actor_id,
                ticket_reference=body["ticket_reference"],
                reason=(body.get("reason") or "").strip() or None,
                starts_at=now,
                expires_at=expires,
            )
            .returning(SupportGrant)
        )
    ).scalar_one()
    await write_audit(
        uow.session,
        ctx,
        "support.access_granted",
        "support_grant",
        grant.id,
        new_value={"ticket": grant.ticket_reference, "minutes": body["minutes"], "by": ctx.actor_label},
        reason=grant.reason,
    )
    for email in await _owner_emails(uow, hotel.id):
        await st.mailer.queue(
            uow,
            hotel_id=hotel.id,
            template="support_access",
            to=email,
            subject=f"Diyneco support opened read access to {hotel.name}",
            body=(
                f"{ctx.actor_label} from Diyneco support can view {hotel.name} (read only, no guest "
                f"details) until {expires.astimezone(PLATFORM_TZ):%H:%M} for ticket "
                f"{grant.ticket_reference}. You can end this access from Settings."
            ),
        )
    token, _ = st.jwt.sign(
        "access",
        {
            "sub": str(ctx.actor_id),
            "kind": "support",
            "sid": str(session_id),
            "hid": str(hotel.id),
            "gid": str(grant.id),
            "amr": list(amr),
        },
        max(1, int((expires - now).total_seconds())),
    )
    return {"grant": grant_payload(grant), "access_token": token, "token_type": "Bearer"}


async def list_grants(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    grants = (
        await uow.session.execute(
            select(SupportGrant)
            .where(SupportGrant.hotel_id == ctx.hotel_id)
            .order_by(SupportGrant.starts_at.desc())
            .limit(100)
        )
    ).scalars()
    return [grant_payload(g) for g in grants]


async def revoke_grant(uow: UnitOfWork, ctx: TenantContext, grant_id: uuid.UUID) -> dict[str, Any]:
    s = uow.session
    grant = (
        await s.execute(
            select(SupportGrant)
            .where(SupportGrant.hotel_id == ctx.hotel_id, SupportGrant.id == grant_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if grant is None:
        raise AppError("NOT_FOUND")
    if grant.revoked_at is None and grant.expires_at > datetime.now(UTC):
        grant = (
            await s.execute(
                update(SupportGrant)
                .where(SupportGrant.id == grant.id)
                .values(revoked_at=datetime.now(UTC), revoked_by=ctx.actor_id)
                .returning(SupportGrant)
            )
        ).scalar_one()
        await write_audit(s, ctx, "support.access_revoked", "support_grant", grant.id)
    return grant_payload(grant)
