"""Order placement and the approval lifecycle (API spec, Guest tablet endpoints, Orders and
Order lifecycle; build spec section 11, Room charge).

Placement checks, in order: hotel can take orders, room charging enabled, active stay, stay
not blocked, cart priced by the server, quoted total still matches. Orders above the
auto-approve limit wait in PENDING_APPROVAL and never reach the kitchen or the folio until a
manager approves. Charges post to the folio when an order becomes NEW; a cancellation posts
reversing entries. The client's Idempotency-Key is also stored on the order itself.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update

from app.audit.writer import write_audit
from app.billing.folio import FolioLedger, Line, business_date
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.domain import Order, OrderItem, Payment, Room, Stay
from app.models.tenancy import Hotel
from app.realtime.outbox import emit, hotel_channel
from app.repositories.hotels import HotelRepository
from app.repositories.orders import OrderRepository
from app.repositories.rooms import RoomRepository
from app.repositories.stays import StayRepository
from app.services.pricing import PricedCart, money, price_cart, quote_payload

# Until it is delivered (user decision, D67); paid orders are corrected with an adjustment.
CANCELLABLE = ("NEW", "ACCEPTED", "PREPARING", "READY", "ASSIGNED", "PICKED_UP")
ACTIVE_ORDER_STATUSES = (
    "PENDING_APPROVAL",
    "NEW",
    "ACCEPTED",
    "PREPARING",
    "READY",
    "ASSIGNED",
    "PICKED_UP",
    "DELIVERED",
)


async def _settings(uow: UnitOfWork, ctx: TenantContext) -> Any:
    st = await HotelRepository(uow.session, ctx).get_settings()
    if st is None:
        raise AppError("NOT_FOUND")
    return st


async def _ordering_context(
    uow: UnitOfWork, ctx: TenantContext, room_id: uuid.UUID
) -> tuple[Any, Room, Stay]:
    """Room-charge rules (build spec 11). Device binding is checked by the device principal."""
    hotel = await HotelRepository(uow.session, ctx).get()
    if hotel is None:
        raise AppError("NOT_FOUND")
    if hotel.status in ("suspended", "closed"):
        raise AppError("HOTEL_SUSPENDED")
    if hotel.status != "active":
        raise AppError(
            "ROOM_CHARGE_DISABLED",
            "Ordering starts once Diyneco approves this hotel.",
            details={"reason": "hotel_pending_approval"},
        )
    settings = await _settings(uow, ctx)
    if not settings.room_charging_enabled:
        raise AppError("ROOM_CHARGE_DISABLED", "Room charging is switched off at this hotel.")
    room = await RoomRepository(uow.session, ctx).get(room_id)
    if room is None:
        raise AppError("NOT_FOUND")
    stay = await StayRepository(uow.session, ctx).live_stay_for_room(room.id)
    if stay is None or stay.status != "active":
        raise AppError("NO_ACTIVE_STAY", "There is no guest checked in to this room.")
    if stay.charges_blocked:
        raise AppError("STAY_BLOCKED", "Room charges are paused for this stay. Please contact reception.")
    return settings, room, stay


async def quote(
    uow: UnitOfWork, ctx: TenantContext, room_id: uuid.UUID, lines: list[dict[str, Any]]
) -> dict[str, Any]:
    settings, _, _ = await _ordering_context(uow, ctx, room_id)
    return quote_payload(await price_cart(uow.session, ctx, settings, lines))


def _channels_for_new(ctx: TenantContext, cart_stations: set[uuid.UUID]) -> list[str]:
    return [hotel_channel(ctx.hotel_id, f"kitchen:{s}") for s in sorted(cart_stations, key=str)] + [
        hotel_channel(ctx.hotel_id, "ops")
    ]


async def _post_charges(uow: UnitOfWork, ctx: TenantContext, order: Order, settings: Any) -> None:
    ledger = FolioLedger(uow.session, ctx)
    folio = await ledger.folio_for_stay(order.stay_id)
    if folio is None:  # pragma: no cover - an active stay always has a folio
        raise AppError("NO_ACTIVE_STAY")
    items = (await OrderRepository(uow.session, ctx).items([order.id])).get(order.id, [])
    on = business_date(settings.timezone)
    lines = [
        Line(
            category=i.charge_category_code,
            description=f"Order #{order.number}: {i.name}",
            unit_amount_minor=i.unit_price_minor,
            quantity=i.quantity,
            vat_rate_bp=i.vat_rate_bp,
            vat_minor=i.vat_minor,
            business_date=on,
            order_id=order.id,
            order_item_id=i.id,
        )
        for i in items
    ]
    if order.fee_minor:
        fee_vat = order.vat_minor - sum(i.vat_minor for i in items)
        lines.append(
            Line(
                category="room_service_fee",
                description=f"Order #{order.number}: room-service fee",
                unit_amount_minor=order.fee_minor,
                quantity=1,
                vat_rate_bp=settings.vat_rate_bp if settings.vat_registered else 0,
                vat_minor=fee_vat,
                business_date=on,
                order_id=order.id,
            )
        )
    await ledger.post(folio, lines)
    await OrderRepository(uow.session, ctx).update(order.id, {"posted_to_folio": True})


def placed_payload(order: Order) -> dict[str, Any]:
    c = order.currency
    return {
        "id": order.id,
        "number": order.number,
        "status": order.status,
        "room": order.room_number,
        "subtotal": money(order.subtotal_minor, c),
        "fee": money(order.fee_minor, c),
        "total": money(order.total_minor, c),
        "vat_included": money(order.vat_minor, c),
        "created_at": order.created_at,
    }


async def place(
    uow: UnitOfWork,
    ctx: TenantContext,
    *,
    room_id: uuid.UUID,
    body: dict[str, Any],
    idempotency_key: uuid.UUID,
    placed_by_user: uuid.UUID | None,
) -> dict[str, Any]:
    settings, room, stay = await _ordering_context(uow, ctx, room_id)
    repo = OrderRepository(uow.session, ctx)
    cart: PricedCart = await price_cart(uow.session, ctx, settings, body["lines"])
    quoted = body["quoted_total"]
    if quoted["currency"] != cart.currency or quoted["amount_minor"] != cart.total_minor:
        raise AppError(
            "PRICE_CHANGED",
            "Prices changed since you looked. Please check the new total.",
            details={"quote": quote_payload(cart)},
        )
    status = "PENDING_APPROVAL" if cart.needs_approval else "NEW"
    order = await repo.create(
        {
            "number": await repo.next_number(),
            "stay_id": stay.id,
            "room_id": room.id,
            "room_number": room.number,
            "device_id": ctx.device_id,
            "placed_by_user": placed_by_user,
            "late_reason": body.get("late_reason"),
            "status": status,
            "payment_method": body.get("payment_method", "room_charge"),
            "special_instructions": body.get("special_instructions"),
            "subtotal_minor": cart.subtotal_minor,
            "fee_minor": cart.fee_minor,
            "total_minor": cart.total_minor,
            "vat_minor": cart.vat_minor,
            "currency": cart.currency,
            "needs_approval": cart.needs_approval,
            "idempotency_key": idempotency_key,
        }
    )
    items = await repo.add_items(
        order.id,
        [
            {
                "menu_item_id": p.menu_item_id,
                "station_id": p.station_id,
                "name": p.name,
                "description": p.description,
                "charge_category_code": p.charge_category,
                "unit_price_minor": p.unit_price_minor,
                "quantity": p.quantity,
                "line_total_minor": p.line_total_minor,
                "vat_rate_bp": p.vat_rate_bp,
                "vat_minor": p.vat_minor,
                "note": p.note,
            }
            for p in cart.lines
        ],
    )
    await repo.add_modifiers(
        [
            {
                "order_item_id": item.id,
                "modifier_id": m.id,
                "group_name": m.group,
                "name": m.name,
                "price_delta_minor": m.price_delta_minor,
            }
            for item, p in zip(items, cart.lines, strict=True)
            for m in p.modifiers
        ]
    )
    await repo.add_history(order.id, None, status, placed_by_user, ctx.device_id)
    await write_audit(
        uow.session,
        ctx,
        "order.create",
        "order",
        order.id,
        new_value={
            "number": order.number,
            "total_minor": order.total_minor,
            "status": status,
            "room": room.number,
        },
    )
    event = {"order_id": str(order.id), "order_number": order.number, "room": room.number}
    if status == "NEW":
        await _post_charges(uow, ctx, order, settings)
        await emit(
            uow.session, ctx, "NEW_ORDER", _channels_for_new(ctx, {p.station_id for p in cart.lines}), event
        )
    else:
        await emit(uow.session, ctx, "ORDER_PENDING_APPROVAL", [hotel_channel(ctx.hotel_id, "ops")], event)
    return placed_payload(order)


# --- Staff actions -------------------------------------------------------------------------


async def _locked(repo: OrderRepository, order_id: uuid.UUID) -> Order:
    order = await repo.get(order_id, for_update=True)
    if order is None:
        raise AppError("NOT_FOUND")
    return order


def _transition_error(order: Order) -> AppError:
    return AppError("INVALID_TRANSITION", details={"status": order.status})


async def approve(uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID) -> dict[str, Any]:
    repo = OrderRepository(uow.session, ctx)
    order = await _locked(repo, order_id)
    if order.status != "PENDING_APPROVAL":
        raise _transition_error(order)
    stay = await StayRepository(uow.session, ctx).stay(order.stay_id)
    if stay is None or stay.status != "active":
        raise AppError("NO_ACTIVE_STAY", "The guest is no longer checked in; decline this order.")
    settings = await _settings(uow, ctx)
    order = await repo.update(
        order_id, {"status": "NEW", "approved_by": ctx.actor_id, "approved_at": datetime.now(UTC)}
    )
    await _post_charges(uow, ctx, order, settings)
    await write_audit(
        uow.session, ctx, "order.approve", "order", order_id, new_value={"number": order.number}
    )
    stations = {i.station_id for i in (await repo.items([order_id])).get(order_id, [])}
    event = {"order_id": str(order.id), "order_number": order.number, "room": order.room_number}
    await emit(uow.session, ctx, "NEW_ORDER", _channels_for_new(ctx, stations), event)
    return await get_order(uow, ctx, order_id)


async def decline(uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID, reason: str) -> dict[str, Any]:
    if not reason.strip():
        raise AppError("REASON_REQUIRED")
    repo = OrderRepository(uow.session, ctx)
    order = await _locked(repo, order_id)
    if order.status != "PENDING_APPROVAL":
        raise _transition_error(order)
    order = await repo.update(order_id, {"status": "DECLINED", "decline_reason": reason.strip()})
    await write_audit(uow.session, ctx, "order.decline", "order", order_id, reason=reason.strip())
    await emit(
        uow.session,
        ctx,
        "ORDER_DECLINED",
        [hotel_channel(ctx.hotel_id, f"room:{order.room_id}"), hotel_channel(ctx.hotel_id, "ops")],
        {"order_id": str(order.id), "order_number": order.number, "room": order.room_number},
    )
    return await get_order(uow, ctx, order_id)


async def cancel(uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID, reason: str) -> dict[str, Any]:
    if not reason.strip():
        raise AppError("REASON_REQUIRED")
    repo = OrderRepository(uow.session, ctx)
    order = await _locked(repo, order_id)
    if order.status not in CANCELLABLE:
        raise _transition_error(order)
    await _refuse_if_paid(uow, ctx, order)
    settings = await _settings(uow, ctx)
    stations = {i.station_id for i in (await repo.items([order_id])).get(order_id, [])}
    order = await repo.update(order_id, {"status": "CANCELLED"})
    reversed_count = 0
    if order.posted_to_folio:
        ledger = FolioLedger(uow.session, ctx)
        folio = await ledger.folio_for_stay(order.stay_id)
        if folio is not None and folio.status == "open":
            reversed_count = await ledger.reverse_order(
                folio, order.id, f"Order #{order.number} cancelled", business_date(settings.timezone)
            )
    await write_audit(
        uow.session,
        ctx,
        "order.cancel",
        "order",
        order_id,
        new_value={"number": order.number, "reversed_entries": reversed_count},
        reason=reason.strip(),
    )
    await emit(
        uow.session,
        ctx,
        "ORDER_CANCELLED",
        [hotel_channel(ctx.hotel_id, f"kitchen:{s}") for s in sorted(stations, key=str)]
        + [
            hotel_channel(ctx.hotel_id, "room-service"),
            hotel_channel(ctx.hotel_id, f"room:{order.room_id}"),
            hotel_channel(ctx.hotel_id, "ops"),
        ],
        {"order_id": str(order.id), "order_number": order.number, "room": order.room_number},
    )
    return await get_order(uow, ctx, order_id)


# --- Reads ---------------------------------------------------------------------------------


async def order_payloads(uow: UnitOfWork, ctx: TenantContext, orders: list[Order]) -> list[dict[str, Any]]:
    repo = OrderRepository(uow.session, ctx)
    ids = [o.id for o in orders]
    items = await repo.items(ids)
    voided = await repo.items(ids, voided=True)
    less = await repo.voided_totals(ids)
    mods = await repo.modifiers([i.id for its in items.values() for i in its])
    history = await repo.history(ids)
    out = []
    for o in orders:
        c = o.currency
        out.append(
            {
                "id": o.id,
                "number": o.number,
                "status": o.status,
                "room": o.room_number,
                "room_id": o.room_id,
                "stay_id": o.stay_id,
                "payment_method": o.payment_method,
                "special_instructions": o.special_instructions,
                "subtotal": money(o.subtotal_minor - less.get(o.id, (0, 0))[0], c),
                "fee": money(o.fee_minor, c),
                "total": money(o.total_minor - less.get(o.id, (0, 0))[0], c),
                "vat_included": money(o.vat_minor - less.get(o.id, (0, 0))[1], c),
                "needs_approval": o.needs_approval,
                "decline_reason": o.decline_reason,
                "placed_by": "staff" if o.placed_by_user else "guest",
                "items": [
                    {
                        "id": i.id,
                        "name": i.name,
                        "quantity": i.quantity,
                        "unit_price": money(i.unit_price_minor, c),
                        "line_total": money(i.line_total_minor, c),
                        "station_id": i.station_id,
                        "prep_status": i.prep_status,
                        "note": i.note,
                        "modifiers": [
                            {
                                "group": m.group_name,
                                "name": m.name,
                                "price_delta": money(m.price_delta_minor, c),
                            }
                            for m in mods.get(i.id, [])
                        ],
                    }
                    for i in items.get(o.id, [])
                ],
                "voided_items": [
                    {
                        "id": i.id,
                        "name": i.name,
                        "quantity": i.quantity,
                        "line_total": money(i.line_total_minor, c),
                        "reason": i.void_reason or "",
                        "voided_at": i.voided_at,
                    }
                    for i in voided.get(o.id, [])
                ],
                "history": [
                    {"from_status": h.from_status, "to_status": h.to_status, "at": h.created_at}
                    for h in history.get(o.id, [])
                ],
                "created_at": o.created_at,
            }
        )
    return out


async def get_order(
    uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID, stay_id: uuid.UUID | None = None
) -> dict[str, Any]:
    order = await OrderRepository(uow.session, ctx).get(order_id)
    if order is None or (stay_id is not None and order.stay_id != stay_id):
        raise AppError("NOT_FOUND")
    return (await order_payloads(uow, ctx, [order]))[0]


async def list_orders(
    uow: UnitOfWork, ctx: TenantContext, **filters: Any
) -> list[tuple[Order, dict[str, Any]]]:
    orders = await OrderRepository(uow.session, ctx).list_page(**filters)
    return list(zip(orders, await order_payloads(uow, ctx, orders), strict=True))


async def hotel_of(uow: UnitOfWork, ctx: TenantContext) -> Hotel:
    hotel = await HotelRepository(uow.session, ctx).get()
    if hotel is None:
        raise AppError("NOT_FOUND")
    return hotel


async def _refuse_if_paid(uow: UnitOfWork, ctx: TenantContext, order: Order) -> None:
    paid = (
        await uow.session.execute(
            select(Payment.id).where(
                Payment.hotel_id == ctx.hotel_id,
                Payment.order_id == order.id,
                Payment.status.in_(("paid", "partial")),
            )
        )
    ).first()
    if paid is not None:
        raise AppError(
            "ALREADY_PAID", "This order has a payment. Correct the bill with an adjustment instead."
        )


async def void_item(
    uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID, item_id: uuid.UUID, reason: str
) -> dict[str, Any]:
    """Cancels one line: it leaves the kitchen ticket and the total, and its charge is reversed.
    Voiding the last line cancels the whole order (with its room-service fee)."""
    if not reason.strip():
        raise AppError("REASON_REQUIRED")
    repo = OrderRepository(uow.session, ctx)
    order = await _locked(repo, order_id)
    if order.status not in CANCELLABLE:
        raise _transition_error(order)
    await _refuse_if_paid(uow, ctx, order)
    live = (await repo.items([order_id])).get(order_id, [])
    item = next((i for i in live if i.id == item_id), None)
    if item is None:
        raise AppError("NOT_FOUND")
    if len(live) == 1:
        return await cancel(uow, ctx, order_id, reason)
    settings = await _settings(uow, ctx)
    await uow.session.execute(
        update(OrderItem)
        .where(OrderItem.hotel_id == ctx.hotel_id, OrderItem.id == item_id)
        .values(voided_at=datetime.now(UTC), voided_by=ctx.actor_id, void_reason=reason.strip())
    )
    reversed_count = 0
    if order.posted_to_folio:
        ledger = FolioLedger(uow.session, ctx)
        folio = await ledger.folio_for_stay(order.stay_id)
        if folio is not None and folio.status == "open":
            reversed_count = await ledger.reverse_order_item(
                folio,
                order.id,
                item.id,
                f"Order #{order.number}: {item.name}",
                f"Order #{order.number}: {item.name} voided",
                business_date(settings.timezone),
            )
    await write_audit(
        uow.session,
        ctx,
        "order.item_void",
        "order",
        order_id,
        old_value={"item": item.name, "quantity": item.quantity, "line_total_minor": item.line_total_minor},
        new_value={"reversed_entries": reversed_count},
        reason=reason.strip(),
    )
    await emit(
        uow.session,
        ctx,
        "ORDER_UPDATED",
        [
            hotel_channel(ctx.hotel_id, f"kitchen:{item.station_id}"),
            hotel_channel(ctx.hotel_id, f"room:{order.room_id}"),
            hotel_channel(ctx.hotel_id, "ops"),
        ],
        {
            "order_id": str(order.id),
            "order_number": order.number,
            "room": order.room_number,
            "voided": item.name,
        },
    )
    return await get_order(uow, ctx, order_id)
