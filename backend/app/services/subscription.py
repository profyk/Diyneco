"""The hotel's own view of its subscription (DECISIONS D76): status, trial, agreed price and
period, usage against limits, a server-side quote for a published plan, the billing contact,
cancellation, and plan change requests (the platform applies them through /admin).

Subscribing to a plan (pending payment, invoice, payment) arrives with invoicing and payments;
until then a quote is informational and a change is requested from Diyneco.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, text

from app.audit.writer import write_audit
from app.billing.quote import quote as compute_quote
from app.core.countries import tax_id_ok
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.tenancy import Plan, Subscription, SubscriptionBillingContact
from app.realtime.outbox import emit
from app.repositories.hotels import CURRENT_STATUSES, HotelRepository
from app.services import catalogue, company
from app.services.plans import _COUNT_SQL, current_limits
from app.services.pricing import money

CONTACT_FIELDS = ("legal_name", "vat_number", "billing_email", "phone", "contact_name", "address")


async def view(uow: UnitOfWork, ctx: TenantContext) -> dict[str, Any]:
    current = await HotelRepository(uow.session, ctx).current_subscription()
    limits = await current_limits(uow, ctx) or {}
    usage = {}
    for resource, sql in _COUNT_SQL.items():
        used = int((await uow.session.execute(text(sql), {"h": ctx.hotel_id})).scalar_one())
        limit = limits.get(resource)
        usage[resource] = {"used": used, "limit": int(limit) if limit is not None else None}
    empty: dict[str, Any] = {
        "plan": None,
        "status": None,
        "starts_on": None,
        "renews_on": None,
        "trial_ends_on": None,
        "interval": None,
        "price": None,
        "current_period_start": None,
        "cancel_at_period_end": False,
        "limits": limits,
        "usage": usage,
    }
    if current is None:
        return empty
    sub, plan = current
    return {
        **empty,
        "plan": await catalogue.plan_out(uow, plan) if plan is not None else None,
        "status": sub.status,
        "starts_on": sub.starts_on,
        "renews_on": sub.renews_on,
        "trial_ends_on": sub.trial_ends_on,
        "interval": sub.interval,
        "price": money(sub.amount_minor, sub.currency)
        if sub.amount_minor is not None and sub.currency
        else None,
        "current_period_start": sub.current_period_start,
        "cancel_at_period_end": sub.status == "cancellation_scheduled",
    }


async def _published(uow: UnitOfWork, code: str) -> Plan:
    plan = (
        await uow.session.execute(select(Plan).where(Plan.code == code, Plan.status == "published"))
    ).scalar_one_or_none()
    if plan is None:
        raise AppError("NOT_FOUND", "Unknown plan.")
    return plan


async def quote(uow: UnitOfWork, ctx: TenantContext, plan_code: str, interval: str) -> dict[str, Any]:
    """What the hotel would pay for a published plan today; nothing is stored or charged."""
    plan = await _published(uow, plan_code)
    rows = (await catalogue._prices(uow, [plan.id]))[plan.id]
    price = catalogue.current_prices(rows, datetime.now(UTC)).get(interval)
    if price is None:
        raise AppError("NOT_FOUND", "That plan is not offered on that billing interval.")
    settings = await company.company_row(uow)
    today = company.today_in(settings.timezone)
    promo = plan.promo_discount_bp if plan.promo_ends_on is not None and plan.promo_ends_on >= today else 0
    paid_before = (
        await uow.session.execute(
            select(Subscription.id).where(
                Subscription.hotel_id == ctx.hotel_id, Subscription.amount_minor.is_not(None)
            )
        )
    ).first()
    out = compute_quote(
        plan_name=plan.name,
        interval=interval,
        amount_minor=price.amount_minor,
        intro_amount_minor=price.intro_amount_minor,
        currency=price.currency,
        tax_treatment=plan.tax_treatment,
        setup_fee_minor=plan.setup_fee_minor,
        promo_discount_bp=promo,
        first_subscription=paid_before is None,
        tax=await company.tax_on(uow, today, settings),
        start=today,
    )
    return {
        **out,
        "plan_code": plan.code,
        "plan_name": plan.name,
        "interval": interval,
        "intro_periods": price.intro_periods if price.intro_amount_minor is not None else None,
        "trial_days": plan.trial_days,
    }


async def request_change(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    plan = await _published(uow, body["plan_code"])
    current = await HotelRepository(uow.session, ctx).current_subscription()
    current_plan = current[1] if current else None
    if current_plan is not None and current_plan.id == plan.id:
        raise AppError("INVALID_TRANSITION", "You are already on that plan.")
    await write_audit(
        uow.session,
        ctx,
        "subscription.change_request",
        "plan",
        plan.id,
        old_value={"plan": current_plan.code if current_plan else None},
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


async def _current_locked(uow: UnitOfWork, ctx: TenantContext) -> Subscription:
    sub = (
        await uow.session.execute(
            select(Subscription)
            .where(Subscription.hotel_id == ctx.hotel_id, Subscription.status.in_(CURRENT_STATUSES))
            .with_for_update()
        )
    ).scalar_one_or_none()
    if sub is None:
        raise AppError("NOT_FOUND", "This hotel has no current subscription.")
    return sub


async def cancel(uow: UnitOfWork, ctx: TenantContext, reason: str) -> dict[str, Any]:
    """A trial ends at once; a paid subscription runs to the end of the period it was paid for
    and then ends (nothing is refunded or deleted, and invoices stay). Hotel data is never
    deleted for a cancellation."""
    sub = await _current_locked(uow, ctx)
    before = sub.status
    today = company.today_in((await company.company_row(uow)).timezone)
    if sub.status == "trial":
        sub.status, sub.ended_on, sub.cancelled_at = "cancelled", today, datetime.now(UTC)
    elif sub.status in ("active", "past_due"):
        sub.status, sub.cancelled_at = "cancellation_scheduled", datetime.now(UTC)
    else:
        raise AppError(
            "INVALID_TRANSITION", f"A subscription that is {before.replace('_', ' ')} cannot be cancelled."
        )
    sub.cancel_reason = reason
    sub.version += 1
    await write_audit(
        uow.session,
        ctx,
        "subscription.cancel",
        "subscription",
        sub.id,
        old_value={"status": before},
        new_value={"status": sub.status, "ends_on": (sub.ended_on or sub.renews_on or today).isoformat()},
        reason=reason,
    )
    await emit(uow.session, ctx, "SUBSCRIPTION_CANCELLED", ["platform"], {"hotel_id": str(ctx.hotel_id)})
    await uow.session.flush()
    return await view(uow, ctx)


async def resume(uow: UnitOfWork, ctx: TenantContext) -> dict[str, Any]:
    """Withdraws a scheduled cancellation before the period ends."""
    sub = await _current_locked(uow, ctx)
    if sub.status != "cancellation_scheduled":
        raise AppError("INVALID_TRANSITION", "Only a scheduled cancellation can be withdrawn.")
    sub.status, sub.cancelled_at, sub.cancel_reason = "active", None, None
    sub.version += 1
    await write_audit(
        uow.session,
        ctx,
        "subscription.resume",
        "subscription",
        sub.id,
        old_value={"status": "cancellation_scheduled"},
        new_value={"status": "active"},
    )
    await uow.session.flush()
    return await view(uow, ctx)


# --- Billing contact -----------------------------------------------------------------------


def _contact_out(c: SubscriptionBillingContact | None) -> dict[str, Any]:
    if c is None:
        return {**dict.fromkeys(CONTACT_FIELDS), "address": {}, "version": 0}
    return {**{f: getattr(c, f) for f in CONTACT_FIELDS}, "version": c.version}


async def billing_contact(uow: UnitOfWork, ctx: TenantContext) -> dict[str, Any]:
    c = (
        await uow.session.execute(
            select(SubscriptionBillingContact).where(SubscriptionBillingContact.hotel_id == ctx.hotel_id)
        )
    ).scalar_one_or_none()
    return _contact_out(c)


async def put_billing_contact(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    values = {f: body.get(f) for f in CONTACT_FIELDS}
    values["address"] = {k: v for k, v in (values["address"] or {}).items() if v}
    values["billing_email"] = str(values["billing_email"]) if values["billing_email"] else None
    if values["vat_number"]:
        country = (await HotelRepository(uow.session, ctx).get()).country  # type: ignore[union-attr]
        if not tax_id_ok(country, values["vat_number"]):
            raise AppError(
                "VALIDATION_FAILED",
                "This is not a valid VAT number.",
                details={"fields": [{"field": "vat_number", "problem": "Not valid.", "type": "value_error"}]},
            )
    c = (
        await uow.session.execute(
            select(SubscriptionBillingContact)
            .where(SubscriptionBillingContact.hotel_id == ctx.hotel_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if (c.version if c else 0) != body["version"]:
        raise AppError("PRECONDITION_FAILED")
    before = _contact_out(c)
    if c is None:
        c = SubscriptionBillingContact(hotel_id=ctx.hotel_id, **values, version=1, updated_by=ctx.actor_id)
        uow.session.add(c)
    else:
        for f, v in values.items():
            setattr(c, f, v)
        c.version += 1
        c.updated_by = ctx.actor_id
    await uow.session.flush()
    await write_audit(
        uow.session,
        ctx,
        "subscription.billing_contact",
        "hotel",
        ctx.hotel_id,
        old_value={f: before[f] for f in CONTACT_FIELDS},
        new_value=values,
    )
    return _contact_out(c)
