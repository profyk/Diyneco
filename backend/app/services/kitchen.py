"""Kitchen display (API spec, Orders, kitchen and deliveries; security spec, Kitchen display).

- A paired kitchen display can show its stations' board with its device token alone.
- Acting needs a staff PIN sign-in on that display: an 8-hour session with `kitchen.*`
  permissions only, ended early when another person signs in on the same display.
- Kitchen payloads never contain prices or totals.
- An order spanning several stations reaches READY only when every item is ready.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import insert, select, update

from app.audit.writer import write_audit
from app.core import crypto
from app.core.errors import AppError
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork
from app.models.domain import DeviceStation, KitchenStation, Order, OrderItem
from app.models.tenancy import HotelUser, RolePermission, Session, User, UserRole
from app.realtime.outbox import emit, hotel_channel
from app.repositories.menu import MenuRepository
from app.repositories.orders import OrderRepository
from app.services.auth import check_member_pin

KITCHEN_SESSION_TTL = timedelta(hours=8)
UNREADY_WINDOW = timedelta(minutes=2)
BOARD_STATUSES = ("NEW", "ACCEPTED", "PREPARING", "READY")


async def device_stations(uow: UnitOfWork, ctx: TenantContext, device_id: uuid.UUID) -> set[uuid.UUID]:
    return set(
        (
            await uow.session.execute(
                select(DeviceStation.station_id).where(
                    DeviceStation.hotel_id == ctx.hotel_id, DeviceStation.device_id == device_id
                )
            )
        ).scalars()
    )


async def all_stations(uow: UnitOfWork, ctx: TenantContext) -> set[uuid.UUID]:
    return set(
        (
            await uow.session.execute(
                select(KitchenStation.id).where(
                    KitchenStation.hotel_id == ctx.hotel_id, KitchenStation.is_active.is_(True)
                )
            )
        ).scalars()
    )


# --- Sign-in -------------------------------------------------------------------------------


async def _kitchen_members(uow: UnitOfWork, ctx: TenantContext) -> list[tuple[HotelUser, User]]:
    rows = (
        await uow.session.execute(
            select(HotelUser, User)
            .join(User, User.id == HotelUser.user_id)
            .where(
                HotelUser.hotel_id == ctx.hotel_id,
                HotelUser.status == "active",
                User.status == "active",
                HotelUser.id.in_(
                    select(UserRole.hotel_user_id)
                    .join(RolePermission, RolePermission.role_id == UserRole.role_id)
                    .where(
                        UserRole.hotel_id == ctx.hotel_id, RolePermission.permission_code == "kitchen.view"
                    )
                ),
            )
            .order_by(User.name)
        )
    ).all()
    return [(r[0], r[1]) for r in rows]


async def staff_for_sign_in(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    """Names for the display's sign-in picker: id and display name only."""
    return [{"user_id": u.id, "name": u.name} for _, u in await _kitchen_members(uow, ctx)]


async def sign_in(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, device_id: uuid.UUID, user_id: uuid.UUID, pin: str
) -> dict[str, Any]:
    member = next(((hu, u) for hu, u in await _kitchen_members(uow, ctx) if u.id == user_id), None)
    if member is None:
        raise AppError("PIN_INVALID", "That PIN is not correct.", details={"attempts_left": None})
    hu, user = member
    # No row lock here: a wrong PIN is recorded in its own transaction on this same row.
    await check_member_pin(st, ctx.hotel_id, hu, pin)
    now = datetime.now(UTC)
    # One person per display: a new sign-in ends the previous kitchen session on it.
    await uow.session.execute(
        update(Session)
        .where(Session.device_id == device_id, Session.revoked_at.is_(None))
        .values(revoked_at=now, revoked_reason="kitchen_sign_in")
    )
    expires = now + KITCHEN_SESSION_TTL
    session_id = (
        await uow.session.execute(
            insert(Session)
            .values(
                user_id=user.id,
                family_id=uuid.uuid4(),
                active_hotel_id=ctx.hotel_id,
                refresh_hash=crypto.sha256(secrets.token_bytes(32)),  # no refresh: the session simply ends
                device_id=device_id,
                ip=ctx.ip,
                amr=["pin"],
                expires_at=expires,
            )
            .returning(Session.id)
        )
    ).scalar_one()
    claims = {
        "sub": str(user.id),
        "kind": "kitchen_session",
        "sid": str(session_id),
        "hid": str(ctx.hotel_id),
        "did": str(device_id),
        "perms_v": hu.perms_version,
        "amr": ["pin"],
    }
    ttl = int(KITCHEN_SESSION_TTL.total_seconds())
    token, _ = st.jwt.sign("access", claims, ttl)
    await write_audit(
        uow.session, ctx, "kitchen.sign_in", "hotel_user", hu.id, new_value={"device_id": str(device_id)}
    )
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": ttl,
        "user": {"id": user.id, "name": user.name},
    }


# --- Board ---------------------------------------------------------------------------------


async def board(uow: UnitOfWork, ctx: TenantContext, stations: set[uuid.UUID]) -> list[dict[str, Any]]:
    if not stations:
        return []
    s = uow.session
    orders = list(
        (
            await s.execute(
                select(Order)
                .where(
                    Order.hotel_id == ctx.hotel_id,
                    Order.status.in_(BOARD_STATUSES),
                    Order.id.in_(
                        select(OrderItem.order_id).where(
                            OrderItem.hotel_id == ctx.hotel_id, OrderItem.station_id.in_(stations)
                        )
                    ),
                )
                .order_by(Order.created_at)
            )
        ).scalars()
    )
    return await _payloads(uow, ctx, orders, stations)


async def _payloads(
    uow: UnitOfWork, ctx: TenantContext, orders: list[Order], stations: set[uuid.UUID]
) -> list[dict[str, Any]]:
    repo = OrderRepository(uow.session, ctx)
    items = await repo.items([o.id for o in orders])
    mods = await repo.modifiers([i.id for its in items.values() for i in its])
    names = {
        sid: name
        for sid, name in (
            await uow.session.execute(
                select(KitchenStation.id, KitchenStation.name).where(KitchenStation.hotel_id == ctx.hotel_id)
            )
        ).all()
    }
    return [
        {
            # Deliberately no prices, totals or payment data (security spec, Kitchen).
            "id": o.id,
            "number": o.number,
            "status": o.status,
            "room": o.room_number,
            "special_instructions": o.special_instructions,
            "created_at": o.created_at,
            "accepted_at": o.accepted_at,
            "ready_at": o.ready_at,
            "items": [
                {
                    "id": i.id,
                    "name": i.name,
                    "quantity": i.quantity,
                    "note": i.note,
                    "modifiers": [{"group": m.group_name, "name": m.name} for m in mods.get(i.id, [])],
                    "station": {"id": i.station_id, "name": names.get(i.station_id, "")},
                    "prep_status": i.prep_status,
                    "ready_at": i.ready_at,
                    "mine": i.station_id in stations,
                }
                for i in items.get(o.id, [])
            ],
        }
        for o in orders
    ]


async def _order_for(
    uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID, stations: set[uuid.UUID]
) -> Order:
    order = await OrderRepository(uow.session, ctx).get(order_id, for_update=True)
    if order is None:
        raise AppError("NOT_FOUND")
    items = (await OrderRepository(uow.session, ctx).items([order_id])).get(order_id, [])
    if not any(i.station_id in stations for i in items):
        raise AppError("NOT_FOUND")  # not on this display's board
    return order


def _transition(order: Order) -> AppError:
    return AppError("INVALID_TRANSITION", details={"status": order.status})


async def _notify(uow: UnitOfWork, ctx: TenantContext, order: Order, event: str, extra: list[str]) -> None:
    stations = {
        i.station_id for i in (await OrderRepository(uow.session, ctx).items([order.id])).get(order.id, [])
    }
    data = {"order_id": str(order.id), "order_number": order.number, "room": order.room_number}
    channels = [hotel_channel(ctx.hotel_id, c) for c in (*extra, f"room:{order.room_id}", "ops")]
    await emit(uow.session, ctx, event, channels, data)
    # Other stations' boards refresh too.
    await emit(
        uow.session,
        ctx,
        "ORDER_UPDATED",
        [hotel_channel(ctx.hotel_id, f"kitchen:{s}") for s in sorted(stations, key=str)],
        {**data, "status": order.status},
    )


async def accept(
    uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID, stations: set[uuid.UUID]
) -> dict[str, Any]:
    order = await _order_for(uow, ctx, order_id, stations)
    if order.status != "NEW":
        raise _transition(order)
    now = datetime.now(UTC)
    order = await OrderRepository(uow.session, ctx).update(
        order_id, {"status": "ACCEPTED", "accepted_at": now, "locked_at": now}
    )
    await write_audit(
        uow.session, ctx, "kitchen.accept", "order", order_id, new_value={"number": order.number}
    )
    await _notify(uow, ctx, order, "ORDER_ACCEPTED", [])
    return (await _payloads(uow, ctx, [order], stations))[0]


async def start(
    uow: UnitOfWork, ctx: TenantContext, order_id: uuid.UUID, stations: set[uuid.UUID]
) -> dict[str, Any]:
    order = await _order_for(uow, ctx, order_id, stations)
    if order.status not in ("ACCEPTED", "PREPARING"):
        raise _transition(order)
    repo = OrderRepository(uow.session, ctx)
    await uow.session.execute(
        update(OrderItem)
        .where(
            OrderItem.hotel_id == ctx.hotel_id,
            OrderItem.order_id == order_id,
            OrderItem.station_id.in_(stations),
            OrderItem.prep_status == "PENDING",
        )
        .values(prep_status="PREPARING")
    )
    if order.status == "ACCEPTED":
        order = await repo.update(order_id, {"status": "PREPARING"})
        await _notify(uow, ctx, order, "ORDER_PREPARING", [])
    return (await _payloads(uow, ctx, [order], stations))[0]


async def _item(
    uow: UnitOfWork, ctx: TenantContext, item_id: uuid.UUID, stations: set[uuid.UUID]
) -> tuple[OrderItem, Order]:
    item = (
        await uow.session.execute(
            select(OrderItem)
            .where(OrderItem.hotel_id == ctx.hotel_id, OrderItem.id == item_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if item is None or item.station_id not in stations:
        raise AppError("NOT_FOUND")
    order = await OrderRepository(uow.session, ctx).get(item.order_id, for_update=True)
    if order is None:  # pragma: no cover - FK
        raise AppError("NOT_FOUND")
    return item, order


async def item_ready(
    uow: UnitOfWork, ctx: TenantContext, item_id: uuid.UUID, stations: set[uuid.UUID]
) -> dict[str, Any]:
    item, order = await _item(uow, ctx, item_id, stations)
    if order.status != "PREPARING":
        raise _transition(order)
    if item.prep_status == "READY":
        raise AppError("INVALID_TRANSITION", details={"status": order.status, "item_status": "READY"})
    now = datetime.now(UTC)
    await uow.session.execute(
        update(OrderItem)
        .where(OrderItem.id == item.id)
        .values(prep_status="READY", ready_at=now, ready_by=ctx.actor_id)
    )
    remaining = (
        await uow.session.execute(
            select(OrderItem.id).where(
                OrderItem.hotel_id == ctx.hotel_id,
                OrderItem.order_id == order.id,
                OrderItem.prep_status != "READY",
            )
        )
    ).first()
    repo = OrderRepository(uow.session, ctx)
    await write_audit(
        uow.session,
        ctx,
        "kitchen.item_ready",
        "order_item",
        item.id,
        new_value={"order_number": order.number},
    )
    if remaining is None:
        order = await repo.update(order.id, {"status": "READY", "ready_at": now})
        await _notify(uow, ctx, order, "ORDER_READY", ["room-service"])
    else:
        await _notify(uow, ctx, order, "ORDER_ITEM_READY", [])
    return (await _payloads(uow, ctx, [order], stations))[0]


async def item_unready(
    uow: UnitOfWork, ctx: TenantContext, item_id: uuid.UUID, stations: set[uuid.UUID]
) -> dict[str, Any]:
    item, order = await _item(uow, ctx, item_id, stations)
    if item.prep_status != "READY" or order.status != "PREPARING":
        raise AppError(
            "INVALID_TRANSITION",
            "Only an item of an order still being prepared can be undone.",
            details={"status": order.status, "item_status": item.prep_status},
        )
    if item.ready_at is None or datetime.now(UTC) - item.ready_at > UNREADY_WINDOW:
        raise AppError("INVALID_TRANSITION", "Ready can only be undone within 2 minutes.")
    await uow.session.execute(
        update(OrderItem)
        .where(OrderItem.id == item.id)
        .values(prep_status="PREPARING", ready_at=None, ready_by=None)
    )
    await write_audit(
        uow.session,
        ctx,
        "kitchen.item_unready",
        "order_item",
        item.id,
        new_value={"order_number": order.number},
    )
    await _notify(uow, ctx, order, "ORDER_ITEM_READY", [])
    return (await _payloads(uow, ctx, [order], stations))[0]


async def menu_for_stations(
    uow: UnitOfWork, ctx: TenantContext, stations: Any, *, item_id: uuid.UUID | None = None
) -> list[dict[str, Any]]:
    """Live menu items (name, category, availability; never prices) for the given stations."""
    repo = MenuRepository(uow.session, ctx)
    categories = {c.id: c for c in await repo.categories()}
    items = await repo.items(ids=[item_id]) if item_id else await repo.items()
    station_ids = None if stations is None else {getattr(s, "id", s) for s in stations}
    out = [
        {
            "id": i.id,
            "name": i.name,
            "category": categories[i.category_id].name if i.category_id in categories else "",
            "station_id": i.station_id,
            "is_available": i.is_available,
        }
        for i in items
        if station_ids is None or i.station_id in station_ids
    ]
    return sorted(out, key=lambda x: (x["category"], x["name"]))
