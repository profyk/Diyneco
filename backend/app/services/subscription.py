"""The hotel's own view of its subscription, and plan change requests (the platform applies
them through /admin)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, text

from app.audit.writer import write_audit
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.tenancy import Plan
from app.realtime.outbox import emit
from app.repositories.hotels import HotelRepository
from app.services.admin import plan_payload
from app.services.plans import _COUNT_SQL


async def view(uow: UnitOfWork, ctx: TenantContext) -> dict[str, Any]:
    current = await HotelRepository(uow.session, ctx).current_plan()
    usage = {}
    limits: dict[str, Any] = {}
    if current is not None:
        limits = {**current[0].limits, **(current[1].limit_overrides or {})}
    for resource, sql in _COUNT_SQL.items():
        used = int((await uow.session.execute(text(sql), {"h": ctx.hotel_id})).scalar_one())
        limit = limits.get(resource)
        usage[resource] = {"used": used, "limit": int(limit) if limit is not None else None}
    if current is None:
        return {
            "plan": None,
            "status": None,
            "starts_on": None,
            "renews_on": None,
            "limits": {},
            "usage": usage,
        }
    plan, sub = current
    return {
        "plan": plan_payload(plan),
        "status": sub.status,
        "starts_on": sub.starts_on,
        "renews_on": sub.renews_on,
        "limits": limits,
        "usage": usage,
    }


async def request_change(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    plan = (
        await uow.session.execute(
            select(Plan).where(Plan.code == body["plan_code"], Plan.is_active.is_(True))
        )
    ).scalar_one_or_none()
    if plan is None:
        raise AppError("NOT_FOUND", "Unknown plan.")
    current = await HotelRepository(uow.session, ctx).current_plan()
    if current is not None and current[0].id == plan.id:
        raise AppError("INVALID_TRANSITION", "You are already on that plan.")
    await write_audit(
        uow.session,
        ctx,
        "subscription.change_request",
        "plan",
        plan.id,
        old_value={"plan": current[0].code if current else None},
        new_value={"plan": plan.code},
        reason=body.get("note"),
    )
    await emit(
        uow.session,
        ctx,
        "SUBSCRIPTION_CHANGE_REQUESTED",
        ["platform"],
        {"hotel_id": str(ctx.hotel_id), "plan": plan.code},
    )
    return {"requested_plan": plan.code, "status": "received"}
