"""Payments and tips (API spec, Payment rules; CLAUDE.md money rules).

1. The server computes `amount_due` from the order or the folio; clients never send it.
2. tip = max(0, received - due). A positive tip needs `confirm_tip`, otherwise
   409 TIP_CONFIRMATION_REQUIRED with the computed figures.
3. Received below due is a `partial` payment; the remainder stays on the folio.
4. card_terminal needs a terminal reference; no card data is ever accepted.
5. One payment per order (409 ALREADY_PAID), enforced again by a unique index.

On the folio, the payment entry is negative and covers at most the amount due; the tip is
its own positive entry in the `tip` category, which `folio_balances` keeps out of the
balance, so tips are never hotel revenue. Room-service staff may record a payment only for
an order assigned to them (security spec, hard limits).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import insert, select

from app.audit.writer import write_audit
from app.billing.folio import FolioLedger, Line, business_date
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.domain import Delivery, Folio, Order, Payment, PaymentAllocation, Stay, Tip
from app.models.tenancy import User
from app.realtime.outbox import emit, hotel_channel
from app.repositories.hotels import HotelRepository
from app.repositories.orders import OrderRepository
from app.repositories.stays import StayRepository
from app.services.pricing import money

PAYABLE_ORDER = ("PICKED_UP", "DELIVERED")
LATE_LIMIT = timedelta(hours=72)
LATE_AFTER = timedelta(minutes=10)


def figures(due: int, received: int) -> dict[str, int]:
    return {
        "due": due,
        "received": received,
        "difference": received - due,
        "tip": max(0, received - due),
        "shortfall": max(0, due - received),
    }


async def _target(
    uow: UnitOfWork,
    ctx: TenantContext,
    order_id: uuid.UUID | None,
    stay_id: uuid.UUID | None,
    permissions: frozenset[str],
    *,
    lock: bool,
) -> tuple[Order | None, Stay, Folio, int]:
    """(order, stay, folio, amount due)."""
    s = uow.session
    ledger = FolioLedger(s, ctx)
    order: Order | None = None
    if order_id is not None:
        order = await OrderRepository(s, ctx).get(order_id, for_update=lock)
        if order is None:
            raise AppError("NOT_FOUND")
        if "deliveries.manage" not in permissions:
            assignee = (
                await s.execute(
                    select(Delivery.assigned_to).where(
                        Delivery.hotel_id == ctx.hotel_id, Delivery.order_id == order.id
                    )
                )
            ).scalar_one_or_none()
            if assignee != ctx.actor_id:
                raise AppError(
                    "PERMISSION_DENIED", "You can only take payment for orders you are delivering."
                )
        paid = (
            await s.execute(
                select(Payment.id).where(
                    Payment.hotel_id == ctx.hotel_id,
                    Payment.order_id == order.id,
                    Payment.status.in_(("paid", "partial")),
                )
            )
        ).first()
        if paid is not None:
            raise AppError("ALREADY_PAID", "This order already has a payment.")
        if order.status not in PAYABLE_ORDER:
            raise AppError(
                "INVALID_TRANSITION",
                "Take payment when the order is handed over.",
                details={"status": order.status},
            )
        stay_id = order.stay_id
    assert stay_id is not None  # noqa: S101 - the schema requires one target
    stay = await StayRepository(s, ctx).stay(stay_id, for_update=lock)
    if stay is None:
        raise AppError("NOT_FOUND")
    folio = await ledger.folio_for_stay(stay.id)
    if folio is None or folio.status != "open":
        raise AppError("INVALID_TRANSITION", "This bill is closed.")
    if order is not None:
        due = order.total_minor
    else:
        if "folio.read" not in permissions:
            raise AppError("PERMISSION_DENIED", "You can only take payment for orders you are delivering.")
        due = (await ledger.balance(folio.id))["balance"]
        if due <= 0:
            raise AppError("INVALID_TRANSITION", "Nothing is owed on this bill.")
    return order, stay, folio, due


def _received(currency: str, amount: dict[str, Any]) -> int:
    if amount["currency"] != currency:
        raise AppError("AMOUNT_INVALID", "Currency must match the bill's currency.")
    if amount["amount_minor"] <= 0:
        raise AppError("AMOUNT_INVALID", "Enter the amount received.")
    return int(amount["amount_minor"])


async def preview(
    uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any], permissions: frozenset[str]
) -> dict[str, Any]:
    _, _stay, folio, due = await _target(
        uow, ctx, body.get("order_id"), body.get("stay_id"), permissions, lock=False
    )
    received = _received(folio.currency, body["amount_received"])
    f = figures(due, received)
    c = folio.currency
    return {
        "amount_due": money(f["due"], c),
        "amount_received": money(f["received"], c),
        "difference": money(abs(f["difference"]), c),
        "tip": money(f["tip"], c),
        "shortfall": money(f["shortfall"], c),
        "status": "paid" if received >= due else "partial",
    }


def _occurred_at(body: dict[str, Any]) -> tuple[datetime, str | None]:
    now = datetime.now(UTC)
    occurred = body.get("occurred_at") or now
    if occurred.tzinfo is None:
        raise AppError("VALIDATION_FAILED", "occurred_at needs a time zone (use UTC with Z).")
    if occurred > now + timedelta(minutes=1) or occurred < now - LATE_LIMIT:
        raise AppError("VALIDATION_FAILED", "A late payment can be at most 72 hours old.")
    reason = (body.get("late_reason") or "").strip() or None
    if occurred < now - LATE_AFTER and reason is None:
        raise AppError("REASON_REQUIRED", "Say why this payment is entered late.")
    return occurred, reason


async def record(
    uow: UnitOfWork,
    ctx: TenantContext,
    body: dict[str, Any],
    permissions: frozenset[str],
    idempotency_key: uuid.UUID,
) -> dict[str, Any]:
    s = uow.session
    order, stay, folio, due = await _target(
        uow, ctx, body.get("order_id"), body.get("stay_id"), permissions, lock=True
    )
    received = _received(folio.currency, body["amount_received"])
    f = figures(due, received)
    c = folio.currency
    if f["tip"] > 0 and not body.get("confirm_tip"):
        raise AppError(
            "TIP_CONFIRMATION_REQUIRED",
            f"The guest gave {f['tip'] / 100:.2f} more than the amount due. Confirm it as a tip.",
            details={k: money(v, c) for k, v in f.items() if k != "difference"},
        )
    occurred, late_reason = _occurred_at(body)
    status = "paid" if received >= due else "partial"
    payment = (
        await s.execute(
            insert(Payment)
            .values(
                hotel_id=ctx.hotel_id,
                folio_id=folio.id,
                order_id=order.id if order else None,
                method=body["method"],
                status=status,
                amount_due_minor=due,
                amount_received_minor=received,
                tip_amount_minor=f["tip"],
                currency=c,
                provider_reference=body.get("terminal_reference"),
                recorded_by=ctx.actor_id,
                recorded_by_device=ctx.device_id,
                occurred_at=occurred,
                late_reason=late_reason,
                idempotency_key=idempotency_key,
            )
            .returning(Payment)
        )
    ).scalar_one()
    settings = await HotelRepository(s, ctx).get_settings()
    on = business_date(settings.timezone if settings else "Africa/Johannesburg", occurred)
    ledger = FolioLedger(s, ctx)
    label = f"Order #{order.number}" if order else "Bill"
    applied = min(received, due)
    lines = [
        Line(
            category="payment",
            description=f"{label}: {body['method'].replace('_', ' ')} payment",
            unit_amount_minor=-applied,
            quantity=1,
            vat_rate_bp=0,
            vat_minor=0,
            business_date=on,
            order_id=order.id if order else None,
            payment_id=payment.id,
        )
    ]
    entries = await ledger.post(folio, lines, entry_type="payment")
    await s.execute(
        insert(PaymentAllocation).values(
            hotel_id=ctx.hotel_id, payment_id=payment.id, folio_entry_id=entries[0].id, amount_minor=applied
        )
    )
    if f["tip"] > 0:
        tip_entry = (
            await ledger.post(
                folio,
                [
                    Line(
                        category="tip",
                        description=f"{label}: tip",
                        unit_amount_minor=f["tip"],
                        quantity=1,
                        vat_rate_bp=0,
                        vat_minor=0,
                        business_date=on,
                        order_id=order.id if order else None,
                        payment_id=payment.id,
                    )
                ],
                entry_type="tip",
            )
        )[0]
        await s.execute(
            insert(Tip).values(
                hotel_id=ctx.hotel_id,
                payment_id=payment.id,
                folio_entry_id=tip_entry.id,
                amount_minor=f["tip"],
                staff_user_id=ctx.actor_id,
                confirmed_by=ctx.actor_id,
            )
        )
    if order is not None:
        repo = OrderRepository(s, ctx)
        if order.status == "PICKED_UP":
            await repo.update(order.id, {"status": "DELIVERED"})
        await repo.update(order.id, {"status": "CLOSED", "closed_at": datetime.now(UTC)})
    await write_audit(
        s,
        ctx,
        "payment.record",
        "payment",
        payment.id,
        new_value={
            "method": payment.method,
            "status": status,
            "due_minor": due,
            "received_minor": received,
            "tip_minor": f["tip"],
            "order_number": order.number if order else None,
            "late": late_reason is not None,
        },
    )
    data = {
        "payment_id": str(payment.id),
        "stay_id": str(stay.id),
        "order_id": str(order.id) if order else None,
    }
    await emit(
        s,
        ctx,
        "PAYMENT_UPDATED",
        [hotel_channel(ctx.hotel_id, f"room:{stay.room_id}"), hotel_channel(ctx.hotel_id, "ops")],
        data,
    )
    await emit(
        s,
        ctx,
        "FOLIO_UPDATED",
        [hotel_channel(ctx.hotel_id, f"room:{stay.room_id}")],
        {"stay_id": str(stay.id)},
    )
    return (await payment_payloads(uow, ctx, [payment]))[0]


async def payment_payloads(
    uow: UnitOfWork, ctx: TenantContext, payments: list[Payment]
) -> list[dict[str, Any]]:
    s = uow.session
    folio_ids = list({p.folio_id for p in payments})
    stays = (
        dict(
            (
                await s.execute(
                    select(Folio.id, Folio.stay_id).where(
                        Folio.hotel_id == ctx.hotel_id, Folio.id.in_(folio_ids)
                    )
                )
            ).all()
        )
        if folio_ids
        else {}
    )
    user_ids = list({p.recorded_by for p in payments if p.recorded_by})
    names = (
        dict((await s.execute(select(User.id, User.name).where(User.id.in_(user_ids)))).all())
        if user_ids
        else {}
    )
    return [
        {
            "id": p.id,
            "order_id": p.order_id,
            "stay_id": stays[p.folio_id],
            "method": p.method,
            "status": p.status,
            "amount_due": money(p.amount_due_minor, p.currency),
            "amount_received": money(p.amount_received_minor, p.currency),
            "tip": money(p.tip_amount_minor, p.currency),
            "terminal_reference": p.provider_reference,
            "recorded_by": {"id": p.recorded_by, "name": names.get(p.recorded_by, "")}
            if p.recorded_by
            else None,
            "occurred_at": p.occurred_at,
            "late_reason": p.late_reason,
            "created_at": p.created_at,
        }
        for p in payments
    ]


async def list_payments(
    uow: UnitOfWork,
    ctx: TenantContext,
    *,
    method: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    staff_id: uuid.UUID | None,
    after: list[Any] | None,
    limit: int,
) -> list[tuple[Payment, dict[str, Any]]]:
    q = select(Payment).where(Payment.hotel_id == ctx.hotel_id)
    if method is not None:
        q = q.where(Payment.method == method)
    if date_from is not None:
        q = q.where(Payment.occurred_at >= date_from)
    if date_to is not None:
        q = q.where(Payment.occurred_at < date_to)
    if staff_id is not None:
        q = q.where(Payment.recorded_by == staff_id)
    if after is not None:
        q = q.where(Payment.id < uuid.UUID(str(after[0])))
    rows = list((await uow.session.execute(q.order_by(Payment.id.desc()).limit(limit + 1))).scalars())
    return list(zip(rows, await payment_payloads(uow, ctx, rows), strict=True))
