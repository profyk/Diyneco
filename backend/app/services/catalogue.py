"""Plans & Pricing (DECISIONS D74): the plan catalogue and its price history.

Plans and prices are data edited in the admin panel; nothing here holds a price, a plan name,
an interval's price or a limit. A plan is a draft until a Super Admin publishes it (only
published plans can be subscribed to), and archiving takes it off sale without touching
anyone already on it. A price belongs to one billing interval (month, quarter, year) and is
in force from a moment on; a change is a new row with a reason and says whether existing
subscribers keep their price (new subscriptions only) or move at their next renewal after the
configured notice. Rows already in force are never rewritten.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import select, text

from app.audit.writer import write_platform_audit
from app.core.currencies import is_supported
from app.core.errors import AppError
from app.db.session import UnitOfWork
from app.models.tenancy import BillingSettings, Plan, PlanPrice
from app.services import company
from app.services.pricing import money

MONTHS = {"month": 1, "quarter": 3, "year": 12}
FIELDS = (
    "name",
    "currency",
    "short_description",
    "description",
    "highlights",
    "display_order",
    "recommended",
    "setup_fee_minor",
    "trial_days",
    "tax_treatment",
    "support_level",
    "overage_policy",
    "can_upgrade",
    "can_downgrade",
    "promo_discount_bp",
    "promo_ends_on",
    "limits",
    "features",
)


def _field(field: str, problem: str, code: str = "VALIDATION_FAILED") -> AppError:
    return AppError(
        code, problem, details={"fields": [{"field": field, "problem": problem, "type": "value_error"}]}
    )


def _now() -> datetime:
    return datetime.now(UTC)


async def _today(uow: UnitOfWork) -> date:
    return company.today_in((await company.company_row(uow)).timezone)


def per_month(amount_minor: int, interval: str) -> int:
    """An interval's price spread over its months, rounded half up (display only)."""
    months = MONTHS[interval]
    return (amount_minor * 2 + months) // (2 * months)


# --- Reading -------------------------------------------------------------------------------


async def _prices(uow: UnitOfWork, plan_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[PlanPrice]]:
    rows = (
        (
            await uow.session.execute(
                select(PlanPrice)
                .where(PlanPrice.plan_id.in_(plan_ids), PlanPrice.withdrawn_at.is_(None))
                .order_by(PlanPrice.effective_from.desc(), PlanPrice.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    out: dict[uuid.UUID, list[PlanPrice]] = {i: [] for i in plan_ids}
    for r in rows:
        out[r.plan_id].append(r)
    return out


def _price_out(p: PlanPrice, in_force: bool) -> dict[str, Any]:
    return {
        "id": p.id,
        "interval": p.interval,
        "amount": money(p.amount_minor, p.currency),
        "intro_amount": money(p.intro_amount_minor, p.currency) if p.intro_amount_minor is not None else None,
        "intro_periods": p.intro_periods,
        "per_month": money(per_month(p.amount_minor, p.interval), p.currency),
        "effective_from": p.effective_from,
        "existing_policy": p.existing_policy,
        "notice_days": p.notice_days,
        "reason": p.reason,
        "in_force": in_force,
    }


def current_prices(rows: list[PlanPrice], now: datetime) -> dict[str, PlanPrice]:
    """The price in force per interval: the latest row on or before now (rows newest first)."""
    current: dict[str, PlanPrice] = {}
    for r in rows:
        if r.effective_from <= now and r.interval not in current:
            current[r.interval] = r
    return current


def plan_payload(plan: Plan, rows: list[PlanPrice], now: datetime | None = None) -> dict[str, Any]:
    now = now or _now()
    current = current_prices(rows, now)
    in_force_ids = {r.id for r in current.values()}
    return {
        **{f: getattr(plan, f) for f in FIELDS if f != "setup_fee_minor"},
        "id": plan.id,
        "code": plan.code,
        "status": plan.status,
        "setup_fee": money(plan.setup_fee_minor, plan.currency),
        "published_at": plan.published_at,
        "archived_at": plan.archived_at,
        "version": plan.version,
        "prices": {i: _price_out(r, True) for i, r in current.items()},
        "scheduled": [_price_out(r, False) for r in rows if r.effective_from > now],
        "history": [
            _price_out(r, False) for r in rows if r.effective_from <= now and r.id not in in_force_ids
        ],
    }


async def plan_out(uow: UnitOfWork, plan: Plan) -> dict[str, Any]:
    return plan_payload(plan, (await _prices(uow, [plan.id]))[plan.id])


async def list_plans(uow: UnitOfWork) -> list[dict[str, Any]]:
    plans = (await uow.session.execute(select(Plan).order_by(Plan.display_order, Plan.name))).scalars().all()
    prices = await _prices(uow, [p.id for p in plans])
    now = _now()
    return [plan_payload(p, prices[p.id], now) for p in plans]


async def _plan(uow: UnitOfWork, plan_id: uuid.UUID) -> Plan:
    plan = (await uow.session.execute(select(Plan).where(Plan.id == plan_id))).scalar_one_or_none()
    if plan is None:
        raise AppError("NOT_FOUND")
    return plan


async def _reload(uow: UnitOfWork, plan_id: uuid.UUID) -> Plan:
    uow.session.expire_all()
    return await _plan(uow, plan_id)


def _public(plan: Plan, rows: list[PlanPrice], today: date, now: datetime) -> dict[str, Any]:
    current = current_prices(rows, now)
    monthly = current.get("month")
    prices = []
    for interval in ("month", "quarter", "year"):
        p = current.get(interval)
        if p is None:
            continue
        saving = None
        if monthly is not None and interval != "month" and monthly.amount_minor:
            full = monthly.amount_minor * MONTHS[interval]
            saving = (full - p.amount_minor) * 10000 // full
        prices.append(
            {
                "interval": interval,
                "amount": money(p.amount_minor, p.currency),
                "per_month": money(per_month(p.amount_minor, interval), p.currency),
                "intro_amount": money(p.intro_amount_minor, p.currency)
                if p.intro_amount_minor is not None
                else None,
                "intro_periods": p.intro_periods,
                "saving_bp": saving,
            }
        )
    promo_live = plan.promo_discount_bp > 0 and plan.promo_ends_on is not None and plan.promo_ends_on >= today
    return {
        **{
            f: getattr(plan, f)
            for f in (
                "code",
                "name",
                "short_description",
                "description",
                "highlights",
                "recommended",
                "currency",
                "tax_treatment",
                "trial_days",
                "support_level",
                "overage_policy",
                "limits",
            )
        },
        "setup_fee": money(plan.setup_fee_minor, plan.currency),
        "promo_discount_bp": plan.promo_discount_bp if promo_live else 0,
        "promo_ends_on": plan.promo_ends_on if promo_live else None,
        "prices": prices,
    }


async def public_plans(uow: UnitOfWork) -> dict[str, Any]:
    """The pricing page: published plans with a price in force, in display order."""
    plans = (
        (
            await uow.session.execute(
                select(Plan).where(Plan.status == "published").order_by(Plan.display_order, Plan.name)
            )
        )
        .scalars()
        .all()
    )
    prices = await _prices(uow, [p.id for p in plans])
    today, now = await _today(uow), _now()
    data = [_public(p, prices[p.id], today, now) for p in plans]
    tax = await company.tax_on(uow, today)
    return {
        "data": [d for d in data if d["prices"]],
        "tax_charged": tax["charged"],
        "tax_name": tax["tax_name"],
        "tax_rate_bp": tax["rate_bp"],
    }


async def preview(uow: UnitOfWork, plan_id: uuid.UUID) -> dict[str, Any]:
    """How a plan would appear on the pricing page, whatever its status."""
    plan = await _plan(uow, plan_id)
    rows = (await _prices(uow, [plan.id]))[plan.id]
    return _public(plan, rows, await _today(uow), _now())


# --- Writing -------------------------------------------------------------------------------


def _jsonable(values: dict[str, Any]) -> dict[str, Any]:
    return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in values.items()}


async def _check(uow: UnitOfWork, values: dict[str, Any], plan: Plan | None) -> None:
    currency = values.get("currency") or (plan.currency if plan else None)
    if currency is None or not is_supported(currency):
        raise _field("currency", "That currency is not supported.")
    discount = values.get("promo_discount_bp", plan.promo_discount_bp if plan else 0)
    ends = values.get("promo_ends_on", plan.promo_ends_on if plan else None)
    if discount and (ends is None or ends < await _today(uow)):
        raise _field("promo_ends_on", "A promotional discount needs an end date that is not in the past.")


async def create_plan(uow: UnitOfWork, actor: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    values = {k: v for k, v in body.items() if v is not None and (k in FIELDS or k == "code")}
    await _check(uow, values, None)
    if (await uow.session.execute(select(Plan.id).where(Plan.code == values["code"]))).first() is not None:
        raise _field("code", "A plan with that code exists.")
    plan_id = (
        await uow.session.execute(
            text("SELECT app.admin_save_plan(NULL, CAST(:p AS jsonb))"), {"p": json.dumps(_jsonable(values))}
        )
    ).scalar_one()
    await write_platform_audit(
        uow.session,
        **actor,
        action="plan.create",
        entity_type="plan",
        entity_id=plan_id,
        new_value=_jsonable(values),
    )
    return await plan_out(uow, await _reload(uow, plan_id))


async def update_plan(
    uow: UnitOfWork, actor: dict[str, Any], plan_id: uuid.UUID, body: dict[str, Any]
) -> dict[str, Any]:
    plan = await _plan(uow, plan_id)
    if body.pop("version") != plan.version:
        raise AppError("PRECONDITION_FAILED")
    reason = body.pop("reason", None)
    if plan.status == "archived":
        raise AppError("INVALID_TRANSITION", "Restore the plan to a draft before changing it.")
    if plan.status == "published" and not reason:
        raise _field("reason", "Changes to a published plan need a reason.")
    nullable = {"short_description", "description", "support_level", "overage_policy", "promo_ends_on"}
    values = {k: v for k, v in body.items() if k in FIELDS and (v is not None or k in nullable)}
    if "currency" in values and values["currency"] != plan.currency:
        has_prices = (
            await uow.session.execute(select(PlanPrice.id).where(PlanPrice.plan_id == plan_id))
        ).first()
        if has_prices is not None:
            raise _field("currency", "The currency is fixed once the plan has a price.")
    await _check(uow, values, plan)
    before = {k: getattr(plan, k) for k in values}
    changed = {k: v for k, v in values.items() if before[k] != v}
    if not changed:
        raise AppError("VALIDATION_FAILED", "Nothing changed.")
    await uow.session.execute(
        text("SELECT app.admin_save_plan(:id, CAST(:p AS jsonb))"),
        {"id": plan_id, "p": json.dumps(_jsonable(changed))},
    )
    await write_platform_audit(
        uow.session,
        **actor,
        action="plan.update",
        entity_type="plan",
        entity_id=plan_id,
        new_value={
            "code": plan.code,
            "reason": reason,
            "from": _jsonable({k: before[k] for k in changed}),
            "to": _jsonable(changed),
        },
    )
    return await plan_out(uow, await _reload(uow, plan_id))


async def add_price(
    uow: UnitOfWork, actor: dict[str, Any], plan_id: uuid.UUID, body: dict[str, Any]
) -> dict[str, Any]:
    plan = await _plan(uow, plan_id)
    if plan.status == "archived":
        raise AppError("INVALID_TRANSITION", "An archived plan is not priced.")
    amount, intro = body["amount"], body.get("intro_amount")
    if amount["currency"] != plan.currency or (intro and intro["currency"] != plan.currency):
        raise _field("amount", f"This plan is billed in {plan.currency}.")
    if (intro is None) != (body.get("intro_periods") is None):
        raise _field(
            "intro_periods", "An introductory price needs its number of periods, and the other way round."
        )
    if intro and intro["amount_minor"] >= amount["amount_minor"]:
        raise _field("intro_amount", "The introductory price must be lower than the price.")
    now = _now()
    starts = body.get("effective_from")
    policy = body.get("existing_policy", "new_only")
    if plan.status == "draft":
        # Nobody pays a draft's price yet: it applies at once and there is nobody to notify.
        if starts is not None:
            raise _field(
                "effective_from", "A draft's price applies at once; schedule changes once published."
            )
        policy = "new_only"
    elif starts is not None and starts <= now:
        raise _field(
            "effective_from", "Leave the start empty for a change at once, or choose a later moment."
        )
    notice = None
    if policy == "next_renewal":
        settings = (await uow.session.execute(select(BillingSettings))).scalar_one()
        notice = settings.price_change_notice_days
    rows = (await _prices(uow, [plan_id]))[plan_id]
    current = current_prices(rows, now).get(body["interval"])
    if (
        starts is None
        and current is not None
        and current.amount_minor == amount["amount_minor"]
        and current.intro_amount_minor == (intro["amount_minor"] if intro else None)
        and current.intro_periods == body.get("intro_periods")
    ):
        raise AppError("VALIDATION_FAILED", "That is already the price.")
    if starts is not None and any(
        r.interval == body["interval"] and r.effective_from == starts for r in rows
    ):
        raise AppError("INVALID_TRANSITION", "A price already starts at that moment. Withdraw it first.")
    price_id = (
        await uow.session.execute(
            text(
                "SELECT app.admin_add_plan_price(:plan, :interval, :amount, :intro, :periods, :starts, "
                ":policy, :notice, :reason, :user)"
            ),
            {
                "plan": plan_id,
                "interval": body["interval"],
                "amount": amount["amount_minor"],
                "intro": intro["amount_minor"] if intro else None,
                "periods": body.get("intro_periods"),
                "starts": starts,
                "policy": policy,
                "notice": notice,
                "reason": body["reason"],
                "user": actor["actor_id"],
            },
        )
    ).scalar_one()
    await write_platform_audit(
        uow.session,
        **actor,
        action="plan.price_changed",
        entity_type="plan_price",
        entity_id=price_id,
        new_value={
            "plan": plan.code,
            "interval": body["interval"],
            "from": current.amount_minor if current else None,
            "to": amount["amount_minor"],
            "currency": plan.currency,
            "intro": intro["amount_minor"] if intro else None,
            "intro_periods": body.get("intro_periods"),
            "effective_from": starts.isoformat() if starts else "now",
            "existing_policy": policy,
            "notice_days": notice,
            "reason": body["reason"],
        },
    )
    return await plan_out(uow, await _reload(uow, plan_id))


async def withdraw_price(
    uow: UnitOfWork, actor: dict[str, Any], plan_id: uuid.UUID, price_id: uuid.UUID
) -> dict[str, Any]:
    row = (
        await uow.session.execute(
            select(PlanPrice).where(PlanPrice.id == price_id, PlanPrice.plan_id == plan_id)
        )
    ).scalar_one_or_none()
    if row is None or row.withdrawn_at is not None:
        raise AppError("NOT_FOUND")
    done = (
        await uow.session.execute(text("SELECT app.admin_withdraw_plan_price(:p)"), {"p": price_id})
    ).scalar_one_or_none()
    if not done:
        raise AppError("INVALID_TRANSITION", "A price already in force cannot be withdrawn; add a new one.")
    await write_platform_audit(
        uow.session,
        **actor,
        action="plan.price_withdrawn",
        entity_type="plan_price",
        entity_id=price_id,
        new_value={
            "interval": row.interval,
            "amount": row.amount_minor,
            "effective_from": row.effective_from.isoformat(),
        },
    )
    return await plan_out(uow, await _reload(uow, plan_id))


TRANSITIONS = {
    "publish": ({"draft"}, "published"),
    "archive": ({"draft", "published"}, "archived"),
    "restore": ({"archived"}, "draft"),
}


async def set_status(
    uow: UnitOfWork, actor: dict[str, Any], plan_id: uuid.UUID, action: str, reason: str
) -> dict[str, Any]:
    plan = await _plan(uow, plan_id)
    allowed, target = TRANSITIONS[action]
    if plan.status not in allowed:
        raise AppError("INVALID_TRANSITION", f"A {plan.status} plan cannot be {action}ed.")
    if action == "publish":
        rows = (await _prices(uow, [plan_id]))[plan_id]
        if not current_prices(rows, _now()):
            raise AppError("INVALID_TRANSITION", "Give the plan a price before publishing it.")
        await _check(uow, {}, plan)
    await uow.session.execute(
        text("SELECT app.admin_save_plan(:id, CAST(:p AS jsonb))"),
        {"id": plan_id, "p": json.dumps({"status": target})},
    )
    await write_platform_audit(
        uow.session,
        **actor,
        action=f"plan.{action}",
        entity_type="plan",
        entity_id=plan_id,
        new_value={"code": plan.code, "from": plan.status, "to": target, "reason": reason},
    )
    return await plan_out(uow, await _reload(uow, plan_id))


# --- Billing settings ----------------------------------------------------------------------


SETTINGS_FIELDS = ("price_change_notice_days", "trial_days", "trial_limits")


async def billing_settings(uow: UnitOfWork) -> dict[str, Any]:
    s = (await uow.session.execute(select(BillingSettings))).scalar_one()
    return {**{f: getattr(s, f) for f in SETTINGS_FIELDS}, "version": s.version, "updated_at": s.updated_at}


async def put_billing_settings(
    uow: UnitOfWork, actor: dict[str, Any], body: dict[str, Any]
) -> dict[str, Any]:
    """Applies to changes from now on: trials already running keep their end date."""
    s = (await uow.session.execute(select(BillingSettings).with_for_update())).scalar_one()
    if body["version"] != s.version:
        raise AppError("PRECONDITION_FAILED")
    before = {f: getattr(s, f) for f in SETTINGS_FIELDS}
    changed = {f: body[f] for f in SETTINGS_FIELDS if before[f] != body[f]}
    if not changed:
        raise AppError("VALIDATION_FAILED", "Nothing changed.")
    for f, v in changed.items():
        setattr(s, f, v)
    s.version += 1
    s.updated_by = actor["actor_id"]
    await write_platform_audit(
        uow.session,
        **actor,
        action="platform.billing_settings_changed",
        entity_type="billing_settings",
        entity_id=None,
        new_value={"reason": body["reason"], "from": {f: before[f] for f in changed}, "to": changed},
    )
    await uow.session.flush()
    return await billing_settings(uow)


def renewal_notice_deadline(created_at: datetime, notice_days: int) -> datetime:
    """The earliest moment a 'next_renewal' price may reach an existing subscriber."""
    return created_at + timedelta(days=notice_days)
