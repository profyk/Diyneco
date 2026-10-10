"""The folio for staff: view, other charges, discounts and two-person adjustments (API spec,
Folios, payments, checkout and invoices).

The folio is append-only. A discount is a negative `discount` entry per revenue group; an
approved adjustment posts a correcting `adjustment` entry for the difference. Nobody approves
their own adjustment (SELF_APPROVAL, also a database CHECK).
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, insert, select, text, update

from app.audit.writer import write_audit
from app.billing.folio import FolioLedger, Line, business_date
from app.billing.vat import vat_included
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.domain import Adjustment, ChargeCategory, Discount, Folio, FolioEntry, Order, Stay
from app.realtime.outbox import emit, hotel_channel
from app.repositories.hotels import HotelRepository
from app.repositories.stays import StayRepository
from app.services.pricing import money

GROUP_CATEGORY = {"accommodation": "accommodation", "fnb": "food", "other": "other_services"}
OPEN_STAY = ("checked_in", "active", "checkout_pending")


async def _settings(uow: UnitOfWork, ctx: TenantContext) -> Any:
    st = await HotelRepository(uow.session, ctx).get_settings()
    if st is None:
        raise AppError("NOT_FOUND")
    return st


async def stay_and_folio(
    uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID, *, lock: bool = False
) -> tuple[Stay, Folio]:
    stay = await StayRepository(uow.session, ctx).stay(stay_id, for_update=lock)
    if stay is None:
        raise AppError("NOT_FOUND")
    folio = await FolioLedger(uow.session, ctx).folio_for_stay(stay.id)
    if folio is None:
        raise AppError("NOT_FOUND", "This stay has no bill yet; check the guest in first.")
    return stay, folio


async def entries_with_groups(
    uow: UnitOfWork, ctx: TenantContext, folio_id: uuid.UUID
) -> list[tuple[FolioEntry, ChargeCategory]]:
    rows = (
        await uow.session.execute(
            select(FolioEntry, ChargeCategory)
            .join(ChargeCategory, ChargeCategory.id == FolioEntry.category_id)
            .where(FolioEntry.hotel_id == ctx.hotel_id, FolioEntry.folio_id == folio_id)
            .order_by(FolioEntry.created_at, FolioEntry.id)
        )
    ).all()
    return [(r[0], r[1]) for r in rows]


async def view(uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID) -> dict[str, Any]:
    stay, folio = await stay_and_folio(uow, ctx, stay_id)
    c = folio.currency
    rows = await entries_with_groups(uow, ctx, folio.id)
    balance = await FolioLedger(uow.session, ctx).balance(folio.id)
    by_category: dict[str, int] = defaultdict(int)
    vat = 0
    for e, cat in rows:
        if cat.revenue_group not in ("tip", "payment"):
            by_category[cat.code] += e.amount_minor
            vat += e.vat_minor
    return {
        "stay_id": stay.id,
        "folio_id": folio.id,
        "status": folio.status,
        "entries": [
            {
                "id": e.id,
                "type": e.entry_type,
                "category": cat.code,
                "group": cat.revenue_group,
                "description": e.description,
                "quantity": e.quantity,
                "unit_amount": money(e.unit_amount_minor, c),
                "amount": money(e.amount_minor, c),
                "vat": money(e.vat_minor, c),
                "business_date": e.business_date,
                "order_id": e.order_id,
                "payment_id": e.payment_id,
                "reverses_entry_id": e.reverses_entry_id,
                "created_at": e.created_at,
            }
            for e, cat in rows
        ],
        "totals": {
            "accommodation": money(balance["accommodation"], c),
            "fnb": money(balance["fnb"], c),
            "other": money(balance["other"], c),
            "vat_included": money(vat, c),
            "tips": money(balance["tips"], c),
            "paid": money(balance["paid"], c),
            "balance": money(balance["balance"], c),
        },
        "by_category": {k: money(v, c) for k, v in sorted(by_category.items())},
    }


def _require_open(stay: Stay, folio: Folio) -> None:
    # A checked-out stay's folio is open again only after its invoice was credited (D44).
    if folio.status != "open" or stay.status not in (*OPEN_STAY, "checked_out"):
        raise AppError("INVALID_TRANSITION", "This bill is closed.")


async def add_charge(
    uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID, body: dict[str, Any]
) -> dict[str, Any]:
    stay, folio = await stay_and_folio(uow, ctx, stay_id, lock=True)
    _require_open(stay, folio)
    category = (
        await uow.session.execute(
            select(ChargeCategory).where(
                ChargeCategory.id == body["charge_category_id"],
                (ChargeCategory.hotel_id.is_(None)) | (ChargeCategory.hotel_id == ctx.hotel_id),
            )
        )
    ).scalar_one_or_none()
    if category is None:
        raise AppError("NOT_FOUND", "Unknown charge category.")
    if not category.is_revenue or category.code.startswith("accommodation"):
        raise AppError(
            "VALIDATION_FAILED", "Use this for other services; rooms, tips and payments have their own flows."
        )
    if body["amount"]["currency"] != folio.currency:
        raise AppError("AMOUNT_INVALID", "Currency must match the bill's currency.")
    unit = int(body["amount"]["amount_minor"])
    if unit <= 0:
        raise AppError("AMOUNT_INVALID", "A charge must be above zero.")
    settings = await _settings(uow, ctx)
    rate = (
        (category.vat_rate_bp if category.vat_rate_bp is not None else settings.vat_rate_bp)
        if settings.vat_registered
        else 0
    )
    qty = body.get("quantity", 1)
    entry = (
        await FolioLedger(uow.session, ctx).post(
            folio,
            [
                Line(
                    category=category.code,
                    description=body["description"],
                    unit_amount_minor=unit,
                    quantity=qty,
                    vat_rate_bp=rate,
                    vat_minor=vat_included(unit * qty, rate),
                    business_date=business_date(settings.timezone),
                )
            ],
        )
    )[0]
    await write_audit(
        uow.session,
        ctx,
        "folio.charge",
        "folio_entry",
        entry.id,
        new_value={"category": category.code, "amount_minor": entry.amount_minor, "stay_id": str(stay.id)},
    )
    await emit(
        uow.session,
        ctx,
        "FOLIO_UPDATED",
        [hotel_channel(ctx.hotel_id, f"room:{stay.room_id}"), hotel_channel(ctx.hotel_id, "ops")],
        {"stay_id": str(stay.id)},
    )
    return await view(uow, ctx, stay_id)


async def add_discount(
    uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID, body: dict[str, Any]
) -> dict[str, Any]:
    reason = (body.get("reason") or "").strip()
    if not reason:
        raise AppError("REASON_REQUIRED")
    stay, folio = await stay_and_folio(uow, ctx, stay_id, lock=True)
    _require_open(stay, folio)
    settings = await _settings(uow, ctx)
    rows = await entries_with_groups(uow, ctx, folio.id)
    groups = ["accommodation", "fnb", "other"] if body["applies_to"] == "all" else [body["applies_to"]]
    base = {g: sum(e.amount_minor for e, cat in rows if cat.revenue_group == g) for g in groups}
    total_base = sum(base.values())
    if total_base <= 0:
        raise AppError("INVALID_TRANSITION", "There is nothing to discount in that category.")
    if body["kind"] == "percent":
        wanted = (total_base * body["percent_bp"] + 5000) // 10000
        if wanted <= 0:
            raise AppError("AMOUNT_INVALID", "That discount rounds to nothing.")
    else:
        if body["amount"]["currency"] != folio.currency:
            raise AppError("AMOUNT_INVALID", "Currency must match the bill's currency.")
        wanted = int(body["amount"]["amount_minor"])
        if wanted > total_base:
            raise AppError("AMOUNT_INVALID", "A discount cannot be larger than the charges it applies to.")
    # Split across groups in proportion to their charges; the last group takes the remainder.
    parts: dict[str, int] = {}
    left = wanted
    for i, g in enumerate(groups):
        share = left if i == len(groups) - 1 else (wanted * base[g]) // total_base
        parts[g] = share
        left -= share
    discount_id = (
        await uow.session.execute(
            insert(Discount)
            .values(
                hotel_id=ctx.hotel_id,
                folio_id=folio.id,
                kind=body["kind"],
                percent_bp=body.get("percent_bp") if body["kind"] == "percent" else None,
                amount_minor=wanted if body["kind"] == "fixed" else None,
                applies_to=body["applies_to"],
                reason=reason,
                created_by=ctx.actor_id,
            )
            .returning(Discount.id)
        )
    ).scalar_one()
    rate = settings.vat_rate_bp if settings.vat_registered else 0
    on = business_date(settings.timezone)
    await FolioLedger(uow.session, ctx).post(
        folio,
        [
            Line(
                category=GROUP_CATEGORY[g],
                description=f"Discount: {reason}",
                unit_amount_minor=-amount,
                quantity=1,
                vat_rate_bp=rate,
                vat_minor=-vat_included(amount, rate),
                business_date=on,
            )
            for g, amount in parts.items()
            if amount > 0
        ],
        entry_type="discount",
    )
    await write_audit(
        uow.session,
        ctx,
        "folio.discount",
        "discount",
        discount_id,
        new_value={"kind": body["kind"], "applies_to": body["applies_to"], "amount_minor": wanted},
        reason=reason,
    )
    await emit(
        uow.session,
        ctx,
        "FOLIO_UPDATED",
        [hotel_channel(ctx.hotel_id, f"room:{stay.room_id}"), hotel_channel(ctx.hotel_id, "ops")],
        {"stay_id": str(stay.id)},
    )
    return await view(uow, ctx, stay_id)


# --- Adjustments ---------------------------------------------------------------------------


def adjustment_payload(a: Adjustment, currency: str) -> dict[str, Any]:
    return {
        "id": a.id,
        "folio_id": a.folio_id,
        "target_entry_id": a.target_entry_id,
        "order_id": a.order_id,
        "original": money(a.original_minor, currency),
        "new_amount": money(a.new_minor, currency),
        "reason": a.reason,
        "status": a.status,
        "requested_by": a.requested_by,
        "requested_at": a.requested_at,
        "decided_by": a.decided_by,
        "decided_at": a.decided_at,
        "decision_note": a.decision_note,
    }


async def _current_amount(
    uow: UnitOfWork, ctx: TenantContext, *, entry_id: uuid.UUID | None, order_id: uuid.UUID | None
) -> int:
    """What the guest is charged now for one entry or one order: the original charge plus
    every reversal and approved adjustment of it."""
    s = uow.session
    if entry_id is not None:
        adjusted = select(Adjustment.id).where(
            Adjustment.hotel_id == ctx.hotel_id,
            Adjustment.target_entry_id == entry_id,
            Adjustment.status == "approved",
        )
        cond = (
            (FolioEntry.id == entry_id)
            | (FolioEntry.reverses_entry_id == entry_id)
            | (FolioEntry.adjustment_id.in_(adjusted))
        )
    else:
        cond = (FolioEntry.order_id == order_id) & FolioEntry.entry_type.in_(
            ("charge", "reversal", "adjustment")
        )
    total = (
        await s.execute(
            select(func.coalesce(func.sum(FolioEntry.amount_minor), 0)).where(
                FolioEntry.hotel_id == ctx.hotel_id, cond
            )
        )
    ).scalar_one()
    return int(total)


async def request_adjustment(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    reason = (body.get("reason") or "").strip()
    if len(reason) < 3:
        raise AppError("REASON_REQUIRED", "Give a reason for the adjustment.")
    s = uow.session
    entry: FolioEntry | None = None
    order: Order | None = None
    if body.get("folio_entry_id"):
        entry = (
            await s.execute(
                select(FolioEntry).where(
                    FolioEntry.hotel_id == ctx.hotel_id, FolioEntry.id == body["folio_entry_id"]
                )
            )
        ).scalar_one_or_none()
        if entry is None:
            raise AppError("NOT_FOUND")
        if entry.entry_type != "charge":
            raise AppError("VALIDATION_FAILED", "Only charges can be adjusted.")
        folio_id = entry.folio_id
        original = await _current_amount(uow, ctx, entry_id=entry.id, order_id=None)
    else:
        order = (
            await s.execute(select(Order).where(Order.hotel_id == ctx.hotel_id, Order.id == body["order_id"]))
        ).scalar_one_or_none()
        if order is None:
            raise AppError("NOT_FOUND")
        if not order.posted_to_folio or order.status in ("CANCELLED", "DECLINED"):
            raise AppError("INVALID_TRANSITION", "This order is not on the bill.")
        folio_id = (
            await s.execute(
                select(Folio.id).where(Folio.hotel_id == ctx.hotel_id, Folio.stay_id == order.stay_id)
            )
        ).scalar_one()
        original = await _current_amount(uow, ctx, entry_id=None, order_id=order.id)
    folio = (
        await s.execute(select(Folio).where(Folio.hotel_id == ctx.hotel_id, Folio.id == folio_id))
    ).scalar_one()
    if folio.status != "open":
        raise AppError("INVALID_TRANSITION", "This bill is closed.")
    if body["new_amount"]["currency"] != folio.currency:
        raise AppError("AMOUNT_INVALID", "Currency must match the bill's currency.")
    new = int(body["new_amount"]["amount_minor"])
    if new == original:
        raise AppError("AMOUNT_INVALID", "The new amount is the same as the current one.")
    if ctx.actor_id is None:
        raise AppError("UNAUTHENTICATED")
    adj = (
        await s.execute(
            insert(Adjustment)
            .values(
                hotel_id=ctx.hotel_id,
                folio_id=folio.id,
                target_entry_id=entry.id if entry else None,
                order_id=order.id if order else None,
                original_minor=original,
                new_minor=new,
                reason=reason,
                requested_by=ctx.actor_id,
            )
            .returning(Adjustment)
        )
    ).scalar_one()
    await write_audit(
        s,
        ctx,
        "folio.adjust_request",
        "adjustment",
        adj.id,
        old_value={"amount_minor": original},
        new_value={"amount_minor": new},
        reason=reason,
    )
    await emit(
        s, ctx, "ADJUSTMENT_REQUESTED", [hotel_channel(ctx.hotel_id, "ops")], {"adjustment_id": str(adj.id)}
    )
    return adjustment_payload(adj, folio.currency)


async def _pending(uow: UnitOfWork, ctx: TenantContext, adjustment_id: uuid.UUID) -> Adjustment:
    adj = (
        await uow.session.execute(
            select(Adjustment)
            .where(Adjustment.hotel_id == ctx.hotel_id, Adjustment.id == adjustment_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if adj is None:
        raise AppError("NOT_FOUND")
    if adj.status != "pending":
        raise AppError("INVALID_TRANSITION", details={"status": adj.status})
    if adj.requested_by == ctx.actor_id:
        raise AppError("SELF_APPROVAL", "Someone else must decide on your own adjustment.")
    return adj


async def approve_adjustment(uow: UnitOfWork, ctx: TenantContext, adjustment_id: uuid.UUID) -> dict[str, Any]:
    s = uow.session
    adj = await _pending(uow, ctx, adjustment_id)
    folio = (
        await s.execute(select(Folio).where(Folio.hotel_id == ctx.hotel_id, Folio.id == adj.folio_id))
    ).scalar_one()
    if folio.status != "open":
        raise AppError("INVALID_TRANSITION", "This bill is closed.")
    current = await _current_amount(uow, ctx, entry_id=adj.target_entry_id, order_id=adj.order_id)
    if current != adj.original_minor:
        raise AppError(
            "INVALID_TRANSITION",
            "The amount changed after this adjustment was requested; reject it and request again.",
            details={"current": money(current, folio.currency)},
        )
    settings = await _settings(uow, ctx)
    order_id = adj.order_id
    if adj.target_entry_id is not None:
        target = (
            await s.execute(
                select(FolioEntry).where(
                    FolioEntry.hotel_id == ctx.hotel_id, FolioEntry.id == adj.target_entry_id
                )
            )
        ).scalar_one()
        category_id, rate, label = target.category_id, target.vat_rate_bp, target.description
        order_id = target.order_id
    else:
        target = (
            await s.execute(
                select(FolioEntry)
                .where(
                    FolioEntry.hotel_id == ctx.hotel_id,
                    FolioEntry.order_id == adj.order_id,
                    FolioEntry.entry_type == "charge",
                )
                .order_by(FolioEntry.created_at)
                .limit(1)
            )
        ).scalar_one()
        category_id, rate = target.category_id, target.vat_rate_bp
        order_no = (
            await s.execute(
                select(Order.number).where(Order.hotel_id == ctx.hotel_id, Order.id == adj.order_id)
            )
        ).scalar_one()
        label = f"Order #{order_no}"
    delta = adj.new_minor - adj.original_minor
    code = (await s.execute(select(ChargeCategory.code).where(ChargeCategory.id == category_id))).scalar_one()
    entry = (
        await FolioLedger(s, ctx).post(
            folio,
            [
                Line(
                    category=code,
                    description=f"Adjustment: {label} ({adj.reason})",
                    unit_amount_minor=delta,
                    quantity=1,
                    vat_rate_bp=rate,
                    vat_minor=vat_included(delta, rate),
                    business_date=business_date(settings.timezone),
                    order_id=order_id,
                    adjustment_id=adj.id,
                )
            ],
            entry_type="adjustment",
        )
    )[0]
    await s.execute(
        update(Adjustment)
        .where(Adjustment.id == adj.id)
        .values(status="approved", decided_by=ctx.actor_id, decided_at=datetime.now(UTC))
    )
    await write_audit(
        s,
        ctx,
        "folio.adjust_approve",
        "adjustment",
        adj.id,
        old_value={"amount_minor": adj.original_minor},
        new_value={"amount_minor": adj.new_minor, "entry_id": str(entry.id)},
    )
    stay = (await s.execute(select(Stay).where(Stay.id == folio.stay_id))).scalar_one()
    await emit(
        s,
        ctx,
        "FOLIO_UPDATED",
        [hotel_channel(ctx.hotel_id, f"room:{stay.room_id}"), hotel_channel(ctx.hotel_id, "ops")],
        {"stay_id": str(stay.id)},
    )
    adj = (await s.execute(select(Adjustment).where(Adjustment.id == adj.id))).scalar_one()
    return adjustment_payload(adj, folio.currency)


async def reject_adjustment(
    uow: UnitOfWork, ctx: TenantContext, adjustment_id: uuid.UUID, reason: str
) -> dict[str, Any]:
    if not reason.strip():
        raise AppError("REASON_REQUIRED")
    s = uow.session
    adj = await _pending(uow, ctx, adjustment_id)
    await s.execute(
        update(Adjustment)
        .where(Adjustment.id == adj.id)
        .values(
            status="rejected",
            decided_by=ctx.actor_id,
            decided_at=datetime.now(UTC),
            decision_note=reason.strip(),
        )
    )
    await write_audit(s, ctx, "folio.adjust_reject", "adjustment", adj.id, reason=reason.strip())
    adj = (await s.execute(select(Adjustment).where(Adjustment.id == adj.id))).scalar_one()
    currency = (await s.execute(select(Folio.currency).where(Folio.id == adj.folio_id))).scalar_one()
    return adjustment_payload(adj, currency)


async def list_adjustments(uow: UnitOfWork, ctx: TenantContext, status: str | None) -> list[dict[str, Any]]:
    """Adjustments with where they belong and who asked, newest first (approval queue)."""
    rows = (
        (
            await uow.session.execute(
                text(
                    "SELECT a.id, f.currency, s.id AS stay_id, r.number AS room, u.name AS requested_by_name "
                    "FROM app.adjustments a JOIN app.folios f ON f.id = a.folio_id "
                    "JOIN app.stays s ON s.id = f.stay_id JOIN app.rooms r ON r.id = s.room_id "
                    "LEFT JOIN app.users u ON u.id = a.requested_by "
                    "WHERE a.hotel_id = :h AND (CAST(:st AS text) IS NULL OR a.status = :st) "
                    "ORDER BY a.requested_at DESC LIMIT 200"
                ),
                {"h": ctx.hotel_id, "st": status},
            )
        )
        .mappings()
        .all()
    )
    by_id = {r["id"]: r for r in rows}
    adjustments = (
        await uow.session.execute(
            select(Adjustment).where(Adjustment.hotel_id == ctx.hotel_id, Adjustment.id.in_(list(by_id)))
        )
    ).scalars()
    out = []
    for a in adjustments:
        extra = by_id[a.id]
        out.append(
            {
                **adjustment_payload(a, extra["currency"]),
                "stay_id": extra["stay_id"],
                "room": extra["room"],
                "requested_by_name": extra["requested_by_name"],
            }
        )
    return sorted(out, key=lambda x: x["requested_at"], reverse=True)


async def chargeable_categories(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    """Categories staff may use for other charges (D42): revenue, not accommodation."""
    rows = (
        await uow.session.execute(
            select(ChargeCategory)
            .where(
                (ChargeCategory.hotel_id.is_(None)) | (ChargeCategory.hotel_id == ctx.hotel_id),
                ChargeCategory.is_revenue.is_(True),
                ~ChargeCategory.code.startswith("accommodation"),
            )
            .order_by(ChargeCategory.revenue_group, ChargeCategory.name)
        )
    ).scalars()
    return [
        {"id": c.id, "code": c.code, "name": c.name, "group": c.revenue_group, "vat_rate_bp": c.vat_rate_bp}
        for c in rows
    ]
