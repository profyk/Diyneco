"""The subscription billing engine (DECISIONS D79; owner's brief, sections 6 and 10).

Hotel actions:
- subscribe: a published plan on one interval, after the hotel accepts the terms. The price is
  computed on the server (the same quote the hotel saw), agreed on the subscription, and the
  first invoice is issued at once; the subscription is pending payment until it is paid.
- change_plan: an upgrade on the same interval applies at once with a prorated invoice for the
  rest of the period when proration is on; every other change (downgrades, interval changes,
  upgrades without proration) is scheduled for the next renewal.

The worker (run) visits each hotel with billing work every few minutes, in its own
transaction, and is safe to repeat: renewal invoices are unique per subscription and period
start in the database, and every notice has a dedupe key.
- Trials: a reminder before the trial ends; at the end the trial expires (data is kept).
- Renewals: renewal_lead_days before a period ends, the next period's invoice is issued, due
  when the period starts; a scheduled change, or a price change that existing subscribers get
  at their next renewal (after its notice), applies from that period. The period then moves
  on when it starts. A scheduled cancellation ends the subscription at the end of the period.
- Overdue: an open invoice past its due date becomes overdue and its subscription past due.
  Reminders go out on the configured days around the due date. After the grace period a past
  due subscription is suspended (when the settings say so), and an unpaid first invoice ends a
  subscription that never started (voided, or credited when it is a tax invoice).
- Standing (review): once nothing is overdue, a past-due or suspended subscription is active
  again, and a pending one starts when its first invoice is paid.

Suspension never deletes data or invoices, and billing stays reachable (see app.api.deps).
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.audit.writer import write_audit
from app.billing import notices
from app.billing.notices import BillingDeps, money_text
from app.billing.periods import MONTHS, period_end
from app.billing.quote import INTERVAL_NAMES
from app.billing.vat import div_half_up
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.tenancy import (
    BillingSettings,
    LegalDocument,
    Plan,
    PlanPrice,
    Subscription,
    SubscriptionInvoice,
)
from app.repositories.hotels import CURRENT_STATUSES
from app.services import catalogue, company, sub_invoices
from app.services import subscription as sub_service

log = logging.getLogger("diyneco.billing")

PAID_STATUSES = ("active", "past_due", "suspended", "cancellation_scheduled")


async def _settings(uow: UnitOfWork) -> BillingSettings:
    return (await uow.session.execute(select(BillingSettings))).scalar_one()


async def _today(uow: UnitOfWork) -> date:
    return company.today_in((await company.company_row(uow)).timezone)


async def _current(uow: UnitOfWork, ctx: TenantContext) -> Subscription | None:
    return (
        await uow.session.execute(
            select(Subscription)
            .where(Subscription.hotel_id == ctx.hotel_id, Subscription.status.in_(CURRENT_STATUSES))
            .with_for_update()
        )
    ).scalar_one_or_none()


async def _plan(uow: UnitOfWork, plan_id: uuid.UUID | None) -> Plan | None:
    if plan_id is None:
        return None
    return (await uow.session.execute(select(Plan).where(Plan.id == plan_id))).scalar_one_or_none()


async def _price_now(uow: UnitOfWork, plan: Plan, interval: str) -> PlanPrice:
    rows = (await catalogue._prices(uow, [plan.id]))[plan.id]
    price = catalogue.current_prices(rows, datetime.now(UTC)).get(interval)
    if price is None:
        raise AppError("NOT_FOUND", "That plan is not offered on that billing interval.")
    return price


def _per_month(amount_minor: int, interval: str) -> int:
    return catalogue.per_month(amount_minor, interval)


def _line(plan: Plan, interval: str, start: date, end: date) -> str:
    last = end - timedelta(days=1)
    return f"{plan.name}, {INTERVAL_NAMES[interval]}: {start:%d %b %Y} to {last:%d %b %Y}"


# --- Subscribing ---------------------------------------------------------------------------


async def subscribe(
    deps: BillingDeps, uow: UnitOfWork, ctx: TenantContext, plan_code: str, interval: str
) -> dict[str, Any]:
    current = await _current(uow, ctx)
    if current is not None and current.status == "pending_payment":
        raise AppError(
            "INVALID_TRANSITION",
            "A subscription is already waiting for payment. Pay its invoice, or cancel it to choose again.",
        )
    if current is not None and current.status in PAID_STATUSES:
        raise AppError(
            "INVALID_TRANSITION", "This hotel already has a subscription. Change its plan instead."
        )
    q = await sub_service.quote(uow, ctx, plan_code, interval)
    plan = (await uow.session.execute(select(Plan).where(Plan.code == plan_code))).scalar_one()
    price = await _price_now(uow, plan, interval)
    start = q["period_start"]
    end = q["period_end"]
    values = {
        "plan_id": plan.id,
        "status": "pending_payment",
        "starts_on": start,
        "renews_on": end,
        "interval": interval,
        "plan_price_id": price.id,
        "amount_minor": price.amount_minor,
        "currency": price.currency,
        "intro_amount_minor": price.intro_amount_minor,
        # The first period is the first introductory one.
        "intro_periods_left": max(0, (price.intro_periods or 0) - 1)
        if price.intro_amount_minor is not None
        else 0,
        "tax_treatment": plan.tax_treatment,
        "anchor_day": start.day,
        "current_period_start": start,
        "cancel_reason": None,
        "cancelled_at": None,
        "ended_on": None,
        "pending_plan_id": None,
        "pending_plan_price_id": None,
        "pending_interval": None,
    }
    if current is not None:  # a trial becomes the paid subscription
        before = current.status
        for k, v in values.items():
            setattr(current, k, v)
        current.version += 1
        sub = current
    else:
        before = None
        sub = Subscription(hotel_id=ctx.hotel_id, **values)
        uow.session.add(sub)
    await uow.session.flush()
    draft = await sub_invoices.create_draft(
        uow,
        ctx,
        lines=[
            {
                "code": line["code"],
                "description": _line(plan, interval, start, end)
                if line["code"] == "subscription"
                else line["description"],
                "quantity": 1,
                "unit_amount_minor": line["amount_minor"],
                "discount_minor": line["discount_minor"],
            }
            for line in q["lines"]
        ],
        currency=q["currency"],
        prices_include_tax=q["prices_include_tax"],
        period_start=start,
        period_end=end,
        subscription_id=sub.id,
        purpose="initial",
        plan_id=plan.id,
        reason="Subscription",
    )
    if draft.total_minor != q["total_minor"]:  # the hotel must be charged what it was shown
        raise AppError("PRICE_CHANGED", "The price changed while you were deciding. Check the new quote.")
    inv = await sub_invoices.issue(deps, uow, ctx, draft.id)
    terms = (
        await uow.session.execute(
            select(LegalDocument.id, LegalDocument.version)
            .where(LegalDocument.kind == "terms", LegalDocument.status == "published")
            .order_by(LegalDocument.version.desc())
            .limit(1)
        )
    ).first()
    await write_audit(
        uow.session,
        ctx,
        "subscription.subscribe",
        "subscription",
        sub.id,
        old_value={"status": before} if before else None,
        new_value={
            "plan": plan.code,
            "interval": interval,
            "amount_minor": price.amount_minor,
            "currency": price.currency,
            "invoice": inv.number,
            "total_minor": inv.total_minor,
            "terms_accepted": True,
            "terms_document": {"id": str(terms[0]), "version": terms[1]} if terms else None,
        },
    )
    return {"subscription": await sub_service.view(uow, ctx), "invoice": await sub_invoices.payload(uow, inv)}


# --- Changing plan -------------------------------------------------------------------------


async def change_plan(
    deps: BillingDeps, uow: UnitOfWork, ctx: TenantContext, plan_code: str, interval: str
) -> dict[str, Any]:
    sub = await _current(uow, ctx)
    if sub is None or sub.status != "active" or sub.plan_id is None or sub.amount_minor is None:
        raise AppError(
            "INVALID_TRANSITION", "Only an active paid subscription can change plan. Subscribe first."
        )
    assert sub.interval and sub.renews_on and sub.current_period_start and sub.currency  # noqa: S101
    target = (
        await uow.session.execute(select(Plan).where(Plan.code == plan_code, Plan.status == "published"))
    ).scalar_one_or_none()
    if target is None:
        raise AppError("NOT_FOUND", "Unknown plan.")
    current_plan = await _plan(uow, sub.plan_id)
    assert current_plan is not None  # noqa: S101
    if target.id == sub.plan_id and interval == sub.interval:
        if sub.pending_plan_id is None:
            raise AppError("INVALID_TRANSITION", "You are already on that plan.")
        sub.pending_plan_id = sub.pending_plan_price_id = sub.pending_interval = None
        sub.version += 1
        await write_audit(uow.session, ctx, "subscription.change_withdrawn", "subscription", sub.id)
        await uow.session.flush()
        return {"subscription": await sub_service.view(uow, ctx), "invoice": None, "effective": "withdrawn"}
    price = await _price_now(uow, target, interval)
    if price.currency != sub.currency:
        raise AppError("INVALID_TRANSITION", "That plan is billed in another currency. Contact Diyneco.")
    upgrade = _per_month(price.amount_minor, interval) > _per_month(sub.amount_minor, sub.interval)
    if upgrade and not current_plan.can_upgrade:
        raise AppError("INVALID_TRANSITION", "Your plan cannot be upgraded online. Contact Diyneco.")
    if not upgrade and not current_plan.can_downgrade:
        raise AppError("INVALID_TRANSITION", "Your plan cannot be downgraded online. Contact Diyneco.")
    settings = await _settings(uow)
    today = await _today(uow)
    old = {"plan": current_plan.code, "interval": sub.interval, "amount_minor": sub.amount_minor}
    invoice = None
    if upgrade and interval == sub.interval and settings.proration_enabled:
        days = (sub.renews_on - sub.current_period_start).days
        left = (sub.renews_on - today).days
        charge = div_half_up((price.amount_minor - sub.amount_minor) * left, days) if days > 0 else 0
        if charge > 0:
            draft = await sub_invoices.create_draft(
                uow,
                ctx,
                lines=[
                    {
                        "code": "proration",
                        "description": (
                            f"Upgrade from {current_plan.name} to {target.name} for {left} of {days} days"
                        ),
                        "quantity": 1,
                        "unit_amount_minor": charge,
                    }
                ],
                currency=sub.currency,
                prices_include_tax=target.tax_treatment == "inclusive",
                period_start=today,
                period_end=sub.renews_on,
                subscription_id=sub.id,
                purpose="proration",
                plan_id=target.id,
                reason="Upgrade",
            )
            invoice = await sub_invoices.issue(deps, uow, ctx, draft.id)
        sub.plan_id, sub.plan_price_id, sub.amount_minor = target.id, price.id, price.amount_minor
        sub.intro_amount_minor, sub.intro_periods_left = None, 0
        sub.tax_treatment = target.tax_treatment
        sub.pending_plan_id = sub.pending_plan_price_id = sub.pending_interval = None
        effective = "now"
        await notices.notify(
            deps,
            uow,
            ctx,
            "plan_upgraded",
            {
                "plan": target.name,
                "effective_on": today.isoformat(),
                "detail": f"Invoice {invoice.number} covers the rest of this period." if invoice else "",
            },
            subscription_id=sub.id,
        )
    else:
        sub.pending_plan_id, sub.pending_plan_price_id, sub.pending_interval = target.id, price.id, interval
        effective = "renewal"
        await notices.notify(
            deps,
            uow,
            ctx,
            "plan_change_scheduled",
            {
                "plan": target.name,
                "interval": INTERVAL_NAMES[interval],
                "effective_on": sub.renews_on.isoformat(),
                "amount": money_text(price.amount_minor, price.currency),
                "detail": "Upgrades apply at once only when proration is offered." if upgrade else "",
            },
            subscription_id=sub.id,
        )
    sub.version += 1
    await uow.session.flush()
    await write_audit(
        uow.session,
        ctx,
        "subscription.plan_change",
        "subscription",
        sub.id,
        old_value=old,
        new_value={
            "plan": target.code,
            "interval": interval,
            "amount_minor": price.amount_minor,
            "effective": effective,
            "invoice": invoice.number if invoice else None,
        },
    )
    return {
        "subscription": await sub_service.view(uow, ctx),
        "invoice": await sub_invoices.payload(uow, invoice) if invoice else None,
        "effective": effective,
    }


# --- Standing ------------------------------------------------------------------------------


async def _overdue_invoices(uow: UnitOfWork, sub: Subscription, today: date) -> list[SubscriptionInvoice]:
    rows = (
        (
            await uow.session.execute(
                select(SubscriptionInvoice).where(
                    SubscriptionInvoice.subscription_id == sub.id,
                    SubscriptionInvoice.kind == "invoice",
                    SubscriptionInvoice.status.in_(sub_invoices.OPEN),
                    SubscriptionInvoice.due_on < today,
                )
            )
        )
        .scalars()
        .all()
    )
    return [i for i in rows if (await sub_invoices.amounts(uow, i))["balance"] > 0]


async def review(deps: BillingDeps, uow: UnitOfWork, ctx: TenantContext, subscription_id: uuid.UUID) -> None:
    """After money or a credit: start a pending subscription whose first invoice is settled,
    and reactivate a past-due or suspended one once nothing is overdue."""
    sub = (
        await uow.session.execute(
            select(Subscription).where(Subscription.id == subscription_id).with_for_update()
        )
    ).scalar_one_or_none()
    if sub is None:
        return
    today = await _today(uow)
    if sub.status == "pending_payment":
        first = (
            await uow.session.execute(
                select(SubscriptionInvoice)
                .where(
                    SubscriptionInvoice.subscription_id == sub.id, SubscriptionInvoice.purpose == "initial"
                )
                .order_by(SubscriptionInvoice.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if first is None or first.status != "paid":
            return
        sub.status = "active"
        sub.version += 1
        await uow.session.flush()
        plan = await _plan(uow, sub.plan_id)
        await write_audit(
            uow.session,
            ctx,
            "subscription.activated",
            "subscription",
            sub.id,
            old_value={"status": "pending_payment"},
            new_value={"status": "active"},
        )
        await notices.notify(
            deps,
            uow,
            ctx,
            "subscription_confirmed",
            {
                "plan": plan.name if plan else "",
                "interval": INTERVAL_NAMES.get(sub.interval or "", ""),
                "period_start": sub.current_period_start.isoformat() if sub.current_period_start else "",
                "renews_on": sub.renews_on.isoformat() if sub.renews_on else "",
                "amount": money_text(sub.amount_minor or 0, sub.currency or "ZAR"),
            },
            dedupe=f"confirmed:{sub.id}",
            subscription_id=sub.id,
        )
        return
    if sub.status in ("past_due", "suspended") and not await _overdue_invoices(uow, sub, today):
        before = sub.status
        sub.status, sub.past_due_since, sub.suspended_at = "active", None, None
        sub.version += 1
        await uow.session.flush()
        await write_audit(
            uow.session,
            ctx,
            "subscription.reactivated",
            "subscription",
            sub.id,
            old_value={"status": before},
            new_value={"status": "active"},
        )
        await notices.record(uow, ctx, "subscription.reactivated", subscription_id=sub.id)
        if before == "suspended":
            await notices.notify(deps, uow, ctx, "subscription_reactivated", {}, subscription_id=sub.id)


# --- The worker ----------------------------------------------------------------------------


async def _policy_price(uow: UnitOfWork, sub: Subscription, starts: date, tz: str) -> PlanPrice | None:
    """A price change existing subscribers get at their next renewal: in force when the period
    starts and announced at least its notice days before."""
    if sub.plan_id is None or sub.interval is None:
        return None
    moment = datetime.combine(starts, time(0), ZoneInfo(tz))
    rows = (
        (
            await uow.session.execute(
                select(PlanPrice)
                .where(
                    PlanPrice.plan_id == sub.plan_id,
                    PlanPrice.interval == sub.interval,
                    PlanPrice.withdrawn_at.is_(None),
                    PlanPrice.effective_from <= moment,
                    PlanPrice.existing_policy == "next_renewal",
                )
                .order_by(PlanPrice.effective_from.desc())
            )
        )
        .scalars()
        .all()
    )
    for r in rows:
        if r.id == sub.plan_price_id:
            return None
        if r.created_at + timedelta(days=r.notice_days or 0) <= moment:
            return r
    return None


async def _renewal_invoice(uow: UnitOfWork, sub: Subscription) -> SubscriptionInvoice | None:
    return (
        await uow.session.execute(
            select(SubscriptionInvoice).where(
                SubscriptionInvoice.subscription_id == sub.id,
                SubscriptionInvoice.period_start == sub.renews_on,
                SubscriptionInvoice.purpose.in_(("initial", "renewal")),
                SubscriptionInvoice.status != "void",
            )
        )
    ).scalar_one_or_none()


async def _renew(
    deps: BillingDeps, uow: UnitOfWork, ctx: TenantContext, sub: Subscription, today: date, tz: str
) -> None:
    assert sub.renews_on and sub.interval and sub.anchor_day and sub.currency and sub.amount_minor is not None  # noqa: S101
    settings = await _settings(uow)
    starts = sub.renews_on
    if (
        today >= starts - timedelta(days=settings.renewal_lead_days)
        and await _renewal_invoice(uow, sub) is None
    ):
        if sub.pending_plan_id is None:
            policy = await _policy_price(uow, sub, starts, tz)
            if policy is not None:
                sub.pending_plan_id, sub.pending_plan_price_id, sub.pending_interval = (
                    sub.plan_id,
                    policy.id,
                    sub.interval,
                )
        if sub.pending_plan_id is not None:
            plan = await _plan(uow, sub.pending_plan_id)
            price = (
                await uow.session.execute(select(PlanPrice).where(PlanPrice.id == sub.pending_plan_price_id))
            ).scalar_one()
            interval, amount = sub.pending_interval or sub.interval, price.amount_minor
        else:
            plan = await _plan(uow, sub.plan_id)
            interval = sub.interval
            amount = (
                sub.intro_amount_minor
                if sub.intro_periods_left > 0 and sub.intro_amount_minor is not None
                else sub.amount_minor
            )
        assert plan is not None  # noqa: S101
        ends = period_end(starts, interval, sub.anchor_day)
        # The group discount (D89) as it stands when the renewal is invoiced.
        group_bp = await sub_service.group_discount_bp(uow, ctx)
        draft = await sub_invoices.create_draft(
            uow,
            ctx,
            lines=[
                {
                    "code": "subscription",
                    "description": _line(plan, interval, starts, ends)
                    + (f" (group discount {group_bp / 100:g}%)" if group_bp else ""),
                    "quantity": 1,
                    "unit_amount_minor": amount,
                    "discount_minor": div_half_up(amount * group_bp, 10000) if group_bp else 0,
                }
            ],
            currency=sub.currency,
            prices_include_tax=plan.tax_treatment == "inclusive",
            period_start=starts,
            period_end=ends,
            subscription_id=sub.id,
            purpose="renewal",
            plan_id=plan.id,
            reason="Renewal",
        )
        inv = await sub_invoices.issue(deps, uow, ctx, draft.id, due_on=max(starts, today))
        await notices.notify(
            deps,
            uow,
            ctx,
            "upcoming_renewal",
            {
                "plan": plan.name,
                "renews_on": starts.isoformat(),
                "amount": money_text(inv.total_minor, inv.currency),
                "interval": INTERVAL_NAMES[interval],
            },
            dedupe=f"renewal_notice:{sub.id}:{starts.isoformat()}",
            subscription_id=sub.id,
            invoice_id=inv.id,
        )
    if today >= starts and await _renewal_invoice(uow, sub) is not None:
        if not await notices.record(
            uow,
            ctx,
            "subscription.renewed",
            dedupe=f"renewed:{sub.id}:{starts.isoformat()}",
            subscription_id=sub.id,
            detail={"period_start": starts.isoformat()},
        ):
            return
        old_plan = sub.plan_id
        if sub.pending_plan_id is not None:
            price = (
                await uow.session.execute(select(PlanPrice).where(PlanPrice.id == sub.pending_plan_price_id))
            ).scalar_one()
            new_plan = await _plan(uow, sub.pending_plan_id)
            sub.plan_id, sub.plan_price_id, sub.amount_minor = (
                sub.pending_plan_id,
                price.id,
                price.amount_minor,
            )
            sub.interval = sub.pending_interval
            sub.intro_amount_minor, sub.intro_periods_left = None, 0
            if new_plan is not None:
                sub.tax_treatment = new_plan.tax_treatment
            sub.pending_plan_id = sub.pending_plan_price_id = sub.pending_interval = None
        elif sub.intro_periods_left > 0:
            sub.intro_periods_left -= 1
        assert sub.interval  # noqa: S101
        sub.current_period_start = starts
        sub.renews_on = period_end(starts, sub.interval, sub.anchor_day)
        sub.version += 1
        await uow.session.flush()
        await write_audit(
            uow.session,
            ctx,
            "subscription.renewed",
            "subscription",
            sub.id,
            new_value={
                "period_start": starts.isoformat(),
                "renews_on": sub.renews_on.isoformat(),
                "plan_changed": old_plan != sub.plan_id,
            },
        )


async def _invoices(
    deps: BillingDeps, uow: UnitOfWork, ctx: TenantContext, sub: Subscription | None, today: date
) -> None:
    settings = await _settings(uow)
    tz = (await company.company_row(uow)).timezone
    rows = (
        (
            await uow.session.execute(
                select(SubscriptionInvoice)
                .where(
                    SubscriptionInvoice.hotel_id == ctx.hotel_id,
                    SubscriptionInvoice.kind == "invoice",
                    SubscriptionInvoice.status.in_(sub_invoices.OPEN),
                    SubscriptionInvoice.due_on.is_not(None),
                )
                .order_by(SubscriptionInvoice.due_on)
                .with_for_update()
            )
        )
        .scalars()
        .all()
    )
    for inv in rows:
        assert inv.due_on is not None and inv.issued_at is not None  # noqa: S101
        balance = (await sub_invoices.amounts(uow, inv))["balance"]
        if balance <= 0:
            continue
        issued_on = inv.issued_at.astimezone(ZoneInfo(tz)).date()
        grace_ends = inv.due_on + timedelta(days=settings.grace_days)
        if today > inv.due_on and inv.status in ("issued", "partially_paid"):
            before = inv.status
            inv.status = "overdue"
            await uow.session.flush()
            await sub_invoices._event(uow, ctx, inv.id, before, "overdue", "Past its due date")
        for offset in sorted(set(settings.reminder_offsets)):
            day = inv.due_on + timedelta(days=offset)
            if day < issued_on or today < day:
                continue
            values = {
                "invoice": inv.number,
                "balance": money_text(balance, inv.currency),
                "due_on": inv.due_on.isoformat(),
                "grace_ends_on": grace_ends.isoformat(),
            }
            await notices.notify(
                deps,
                uow,
                ctx,
                "invoice_overdue" if offset > 0 else "payment_reminder",
                values,
                dedupe=f"reminder:{inv.id}:{offset}",
                subscription_id=inv.subscription_id,
                invoice_id=inv.id,
            )
        if sub is None or inv.subscription_id != sub.id or today <= inv.due_on:
            continue
        if sub.status == "active":
            sub.status, sub.past_due_since = "past_due", inv.due_on
            sub.version += 1
            await uow.session.flush()
            await write_audit(
                uow.session,
                ctx,
                "subscription.past_due",
                "subscription",
                sub.id,
                old_value={"status": "active"},
                new_value={"status": "past_due", "invoice": inv.number},
            )
        if today <= grace_ends:
            continue
        if sub.status == "past_due" and settings.suspend_after_grace:
            sub.status, sub.suspended_at = "suspended", datetime.now(UTC)
            sub.version += 1
            await uow.session.flush()
            await write_audit(
                uow.session,
                ctx,
                "subscription.suspended",
                "subscription",
                sub.id,
                old_value={"status": "past_due"},
                new_value={"status": "suspended", "invoice": inv.number},
            )
            await notices.notify(
                deps,
                uow,
                ctx,
                "subscription_suspended",
                {"invoice": inv.number, "balance": money_text(balance, inv.currency)},
                dedupe=f"suspended:{sub.id}:{inv.id}",
                subscription_id=sub.id,
                invoice_id=inv.id,
            )
        elif sub.status == "pending_payment" and inv.purpose == "initial":
            if await sub_invoices.paid_total(uow, inv.id):
                continue  # part paid: Diyneco settles it by hand
            reason = "Not started: the first invoice was not paid"
            await sub_service.cancel_pending(deps, uow, ctx, sub, reason)
            sub.status = "expired"
            await uow.session.flush()
            await write_audit(
                uow.session,
                ctx,
                "subscription.expired",
                "subscription",
                sub.id,
                old_value={"status": "pending_payment"},
                new_value={"status": "expired"},
                reason=reason,
            )
            await notices.notify(
                deps,
                uow,
                ctx,
                "subscription_cancelled",
                {"ends_on": today.isoformat(), "reason": reason},
                dedupe=f"expired:{sub.id}",
                subscription_id=sub.id,
            )


async def process_hotel(deps: BillingDeps, uow: UnitOfWork, ctx: TenantContext, today: date) -> None:
    tz = (await company.company_row(uow)).timezone
    settings = await _settings(uow)
    sub = await _current(uow, ctx)
    trial_ends = sub.trial_ends_on if sub is not None and sub.status == "trial" else None
    if sub is not None and trial_ends is not None:
        if today >= trial_ends:
            sub.status, sub.ended_on = "expired", trial_ends
            sub.version += 1
            await uow.session.flush()
            await write_audit(
                uow.session,
                ctx,
                "subscription.trial_ended",
                "subscription",
                sub.id,
                old_value={"status": "trial"},
                new_value={"status": "expired"},
            )
            await notices.notify(
                deps,
                uow,
                ctx,
                "trial_ended",
                {"trial_ends_on": trial_ends.isoformat()},
                dedupe=f"trial_ended:{sub.id}",
                subscription_id=sub.id,
            )
            sub = None
        elif today >= trial_ends - timedelta(days=settings.renewal_lead_days):
            await notices.notify(
                deps,
                uow,
                ctx,
                "trial_ending",
                {"trial_ends_on": trial_ends.isoformat()},
                dedupe=f"trial_ending:{sub.id}",
                subscription_id=sub.id,
            )
    if (
        sub is not None
        and sub.status == "cancellation_scheduled"
        and sub.renews_on
        and today >= sub.renews_on
    ):
        sub.status, sub.ended_on = "cancelled", sub.renews_on
        sub.version += 1
        await uow.session.flush()
        await write_audit(
            uow.session,
            ctx,
            "subscription.ended",
            "subscription",
            sub.id,
            old_value={"status": "cancellation_scheduled"},
            new_value={"status": "cancelled"},
        )
        await notices.notify(
            deps,
            uow,
            ctx,
            "subscription_cancelled",
            {"ends_on": sub.renews_on.isoformat(), "reason": sub.cancel_reason or ""},
            dedupe=f"ended:{sub.id}",
            subscription_id=sub.id,
        )
        sub = None
    if (
        sub is not None
        and sub.status in ("active", "past_due")
        and sub.renews_on is not None
        and sub.amount_minor is not None
        and sub.anchor_day is not None
    ):
        await _renew(deps, uow, ctx, sub, today, tz)
    await _invoices(deps, uow, ctx, sub, today)


async def run(
    deps: BillingDeps, sessionmaker: async_sessionmaker[AsyncSession], today: date | None = None
) -> int:
    """One pass over every hotel with billing work; each hotel in its own transaction, so one
    hotel's failure never stops the others. Returns the number of hotels processed."""
    async with sessionmaker() as s, s.begin():
        hotels = [r[0] for r in (await s.execute(text("SELECT hotel_id FROM app.billing_hotels()"))).all()]
    done = 0
    for hotel_id in hotels:
        try:
            async with sessionmaker() as s:
                uow = UnitOfWork(session=s, sessionmaker=sessionmaker)
                async with s.begin():
                    await set_tenant(s, hotel_id)
                    ctx = TenantContext(
                        hotel_id=hotel_id, actor_type="system", actor_id=None, actor_label="Billing"
                    )
                    await process_hotel(deps, uow, ctx, today or await _today(uow))
                await uow.run_after_commit()
            done += 1
        except Exception:
            log.exception("billing run failed for a hotel", extra={"hotel_id": str(hotel_id)})
    return done


def months(interval: str) -> int:
    return MONTHS[interval]
