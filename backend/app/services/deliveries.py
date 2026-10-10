"""Room-service deliveries (API spec, Orders, kitchen and deliveries; Order lifecycle).

READY -> ASSIGNED (claim or assign; first claim wins) -> PICKED_UP -> DELIVERED -> CLOSED.
ASSIGNED -> READY on release. Only the assignee moves an assigned delivery forward.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert, select, update

from app.audit.writer import write_audit
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.domain import Delivery, Order, Payment
from app.models.tenancy import HotelUser, RolePermission, User, UserRole
from app.realtime.outbox import emit, hotel_channel
from app.repositories.orders import OrderRepository
from app.services.pricing import money

MINE = ("ASSIGNED", "PICKED_UP", "DELIVERED")


async def _delivery(uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID) -> Delivery | None:
    return (
        await uow.session.execute(
            select(Delivery)
            .where(Delivery.hotel_id == ctx.hotel_id, Delivery.order_id == order_id)
            .with_for_update()
        )
    ).scalar_one_or_none()


async def payloads(uow: UnitOfWork, ctx: TenantContext, orders: list[Order]) -> list[dict[str, Any]]:
    s = uow.session
    ids = [o.id for o in orders]
    repo = OrderRepository(s, ctx)
    items = await repo.items(ids)
    deliveries = (
        {
            d.order_id: d
            for d in (
                await s.execute(
                    select(Delivery).where(Delivery.hotel_id == ctx.hotel_id, Delivery.order_id.in_(ids))
                )
            ).scalars()
        }
        if ids
        else {}
    )
    paid = (
        set(
            (
                await s.execute(
                    select(Payment.order_id).where(
                        Payment.hotel_id == ctx.hotel_id,
                        Payment.order_id.in_(ids),
                        Payment.status.in_(("paid", "partial")),
                    )
                )
            ).scalars()
        )
        if ids
        else set()
    )
    user_ids = [d.assigned_to for d in deliveries.values() if d.assigned_to]
    names = (
        dict((await s.execute(select(User.id, User.name).where(User.id.in_(user_ids)))).all())
        if user_ids
        else {}
    )
    less = await OrderRepository(uow.session, ctx).voided_totals(ids)
    out = []
    for o in orders:
        d = deliveries.get(o.id)
        out.append(
            {
                "order_id": o.id,
                "number": o.number,
                "status": o.status,
                "room": o.room_number,
                "special_instructions": o.special_instructions,
                "items": [
                    {"name": i.name, "quantity": i.quantity, "note": i.note} for i in items.get(o.id, [])
                ],
                "amount_due": money(o.total_minor - less.get(o.id, (0, 0))[0], o.currency),
                "paid": o.id in paid,
                "assigned_to": {"id": d.assigned_to, "name": names.get(d.assigned_to, "")}
                if d and d.assigned_to
                else None,
                "ready_at": o.ready_at,
                "assigned_at": d.assigned_at if d else None,
                "picked_up_at": d.picked_up_at if d else None,
                "delivered_at": d.delivered_at if d else None,
            }
        )
    return out


async def list_deliveries(uow: UnitOfWork, ctx: TenantContext, scope: str) -> list[dict[str, Any]]:
    q = select(Order).where(Order.hotel_id == ctx.hotel_id)
    if scope == "ready":
        q = q.where(Order.status == "READY")
    elif scope == "all":  # dispatch view: everything waiting or on its way, whoever has it
        q = q.where(Order.status.in_(("READY", *MINE)))
    else:
        q = q.where(
            Order.status.in_(MINE),
            Order.id.in_(
                select(Delivery.order_id).where(
                    Delivery.hotel_id == ctx.hotel_id, Delivery.assigned_to == ctx.actor_id
                )
            ),
        )
    orders = list((await uow.session.execute(q.order_by(Order.ready_at, Order.number))).scalars())
    return await payloads(uow, ctx, orders)


async def _event(
    uow: UnitOfWork, ctx: TenantContext, order: Order, event: str, channels: list[str], **extra: Any
) -> None:
    await emit(
        uow.session,
        ctx,
        event,
        [hotel_channel(ctx.hotel_id, c) for c in channels],
        {"order_id": str(order.id), "order_number": order.number, "room": order.room_number, **extra},
    )


async def _assign(
    uow: UnitOfWork, ctx: TenantContext, order: Order, to_user: uuid.UUID, by: uuid.UUID | None
) -> None:
    now = datetime.now(UTC)
    d = await _delivery(uow, ctx, order.id)
    values = {"assigned_to": to_user, "assigned_by": by, "assigned_at": now}
    if d is None:
        await uow.session.execute(insert(Delivery).values(hotel_id=ctx.hotel_id, order_id=order.id, **values))
    else:
        await uow.session.execute(update(Delivery).where(Delivery.id == d.id).values(**values))


async def _locked_order(uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID) -> Order:
    order = await OrderRepository(uow.session, ctx).get(order_id, for_update=True)
    if order is None:
        raise AppError("NOT_FOUND")
    return order


async def claim(uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID) -> dict[str, Any]:
    order = await _locked_order(uow, ctx, order_id)
    if order.status in MINE:
        raise AppError("ALREADY_CLAIMED", "Someone else is already taking this order.")
    if order.status != "READY":
        raise AppError("INVALID_TRANSITION", details={"status": order.status})
    order = await OrderRepository(uow.session, ctx).update(order_id, {"status": "ASSIGNED"})
    await _assign(uow, ctx, order, ctx.actor_id, ctx.actor_id)  # type: ignore[arg-type]
    await write_audit(uow.session, ctx, "delivery.claim", "order", order_id)
    await _event(uow, ctx, order, "DELIVERY_ASSIGNED", ["room-service", "ops"], assigned_to=str(ctx.actor_id))
    return (await payloads(uow, ctx, [order]))[0]


async def assign(
    uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID, user_id: uuid.UUID
) -> dict[str, Any]:
    target = (
        await uow.session.execute(
            select(HotelUser.id)
            .join(UserRole, UserRole.hotel_user_id == HotelUser.id)
            .join(RolePermission, RolePermission.role_id == UserRole.role_id)
            .where(
                HotelUser.hotel_id == ctx.hotel_id,
                HotelUser.user_id == user_id,
                HotelUser.status == "active",
                RolePermission.permission_code == "deliveries.update",
            )
        )
    ).first()
    if target is None:
        raise AppError("NOT_FOUND", "That person cannot deliver orders.")
    order = await _locked_order(uow, ctx, order_id)
    if order.status not in ("READY", "ASSIGNED"):
        raise AppError("INVALID_TRANSITION", details={"status": order.status})
    if order.status == "READY":
        order = await OrderRepository(uow.session, ctx).update(order_id, {"status": "ASSIGNED"})
    await _assign(uow, ctx, order, user_id, ctx.actor_id)
    await write_audit(
        uow.session, ctx, "delivery.assign", "order", order_id, new_value={"assigned_to": str(user_id)}
    )
    await _event(uow, ctx, order, "DELIVERY_ASSIGNED", ["room-service", "ops"], assigned_to=str(user_id))
    return (await payloads(uow, ctx, [order]))[0]


async def _as_assignee(
    uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID, expected: str
) -> tuple[Order, Delivery]:
    order = await _locked_order(uow, ctx, order_id)
    d = await _delivery(uow, ctx, order_id)
    if d is None or d.assigned_to != ctx.actor_id:
        raise AppError("PERMISSION_DENIED", "This delivery is assigned to someone else.")
    if order.status != expected:
        raise AppError("INVALID_TRANSITION", details={"status": order.status})
    return order, d


async def release(uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID) -> dict[str, Any]:
    order, d = await _as_assignee(uow, ctx, order_id, "ASSIGNED")
    order = await OrderRepository(uow.session, ctx).update(order_id, {"status": "READY"})
    await uow.session.execute(
        update(Delivery)
        .where(Delivery.id == d.id)
        .values(
            assigned_to=None, assigned_by=None, assigned_at=None, released_count=Delivery.released_count + 1
        )
    )
    await write_audit(uow.session, ctx, "delivery.release", "order", order_id)
    await _event(uow, ctx, order, "DELIVERY_RELEASED", ["room-service", "ops"])
    return (await payloads(uow, ctx, [order]))[0]


async def picked_up(uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID) -> dict[str, Any]:
    order, d = await _as_assignee(uow, ctx, order_id, "ASSIGNED")
    order = await OrderRepository(uow.session, ctx).update(order_id, {"status": "PICKED_UP"})
    await uow.session.execute(
        update(Delivery).where(Delivery.id == d.id).values(picked_up_at=datetime.now(UTC))
    )
    await _event(uow, ctx, order, "ORDER_DELIVERING", [f"room:{order.room_id}", "ops"])
    return (await payloads(uow, ctx, [order]))[0]


async def delivered(uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID) -> dict[str, Any]:
    order, d = await _as_assignee(uow, ctx, order_id, "PICKED_UP")
    order = await OrderRepository(uow.session, ctx).update(order_id, {"status": "DELIVERED"})
    await uow.session.execute(
        update(Delivery).where(Delivery.id == d.id).values(delivered_at=datetime.now(UTC))
    )
    await write_audit(uow.session, ctx, "delivery.delivered", "order", order_id)
    await _event(uow, ctx, order, "ORDER_DELIVERED", [f"room:{order.room_id}", "ops"])
    return (await payloads(uow, ctx, [order]))[0]


async def leave_on_room(uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID) -> dict[str, Any]:
    order, _ = await _as_assignee(uow, ctx, order_id, "DELIVERED")
    order = await OrderRepository(uow.session, ctx).update(
        order_id, {"status": "CLOSED", "closed_at": datetime.now(UTC)}
    )
    await write_audit(
        uow.session,
        ctx,
        "delivery.left_on_room",
        "order",
        order_id,
        new_value={"total_minor": order.total_minor},
    )
    await _event(uow, ctx, order, "ORDER_CLOSED", ["ops"])
    return (await payloads(uow, ctx, [order]))[0]
