"""Orders, their items, modifiers and status history, for one hotel."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import TenantContext
from app.models.domain import Order, OrderItem, OrderItemModifier, OrderStatusHistory


class OrderRepository:
    def __init__(self, session: AsyncSession, ctx: TenantContext) -> None:
        self.s = session
        self.h = ctx.hotel_id

    async def next_number(self) -> int:
        return int(
            (
                await self.s.execute(
                    text(
                        "UPDATE app.order_number_sequences SET next_number = next_number + 1 "
                        "WHERE hotel_id = :h RETURNING next_number - 1"
                    ),
                    {"h": self.h},
                )
            ).scalar_one()
        )

    async def by_idempotency_key(self, key: uuid.UUID) -> Order | None:
        return (
            await self.s.execute(select(Order).where(Order.hotel_id == self.h, Order.idempotency_key == key))
        ).scalar_one_or_none()

    async def create(self, values: dict[str, Any]) -> Order:
        return (
            await self.s.execute(insert(Order).values(hotel_id=self.h, **values).returning(Order))
        ).scalar_one()

    async def add_items(self, order_id: uuid.UUID, items: list[dict[str, Any]]) -> list[OrderItem]:
        rows = [{**i, "hotel_id": self.h, "order_id": order_id} for i in items]
        return list((await self.s.execute(insert(OrderItem).returning(OrderItem), rows)).scalars())

    async def add_modifiers(self, rows: list[dict[str, Any]]) -> None:
        if rows:
            await self.s.execute(insert(OrderItemModifier), [{**r, "hotel_id": self.h} for r in rows])

    async def add_history(
        self, order_id: uuid.UUID, from_status: str | None, to_status: str, actor_user: Any, actor_device: Any
    ) -> None:
        await self.s.execute(
            insert(OrderStatusHistory).values(
                hotel_id=self.h,
                order_id=order_id,
                from_status=from_status,
                to_status=to_status,
                actor_user=actor_user,
                actor_device=actor_device,
            )
        )

    async def get(self, order_id: uuid.UUID, *, for_update: bool = False) -> Order | None:
        q = select(Order).where(Order.hotel_id == self.h, Order.id == order_id)
        if for_update:
            q = q.with_for_update()
        return (await self.s.execute(q)).scalar_one_or_none()

    async def update(self, order_id: uuid.UUID, values: dict[str, Any]) -> Order:
        return (
            await self.s.execute(
                update(Order)
                .where(Order.hotel_id == self.h, Order.id == order_id)
                .values(**values)
                .returning(Order)
            )
        ).scalar_one()

    async def list_page(
        self,
        *,
        status: str | None = None,
        room_id: uuid.UUID | None = None,
        stay_id: uuid.UUID | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        after: list[Any] | None = None,
        limit: int = 50,
    ) -> list[Order]:
        q = select(Order).where(Order.hotel_id == self.h)
        if status is not None:
            q = q.where(Order.status == status)
        if room_id is not None:
            q = q.where(Order.room_id == room_id)
        if stay_id is not None:
            q = q.where(Order.stay_id == stay_id)
        if created_from is not None:
            q = q.where(Order.created_at >= created_from)
        if created_to is not None:
            q = q.where(Order.created_at < created_to)
        if after is not None:
            q = q.where(Order.number < int(after[0]))
        return list((await self.s.execute(q.order_by(Order.number.desc()).limit(limit + 1))).scalars())

    async def items(self, order_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[OrderItem]]:
        out: dict[uuid.UUID, list[OrderItem]] = defaultdict(list)
        if order_ids:
            for item in (
                await self.s.execute(
                    select(OrderItem)
                    .where(OrderItem.hotel_id == self.h, OrderItem.order_id.in_(order_ids))
                    .order_by(OrderItem.id)
                )
            ).scalars():
                out[item.order_id].append(item)
        return out

    async def modifiers(self, item_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[OrderItemModifier]]:
        out: dict[uuid.UUID, list[OrderItemModifier]] = defaultdict(list)
        if item_ids:
            for m in (
                await self.s.execute(
                    select(OrderItemModifier).where(
                        OrderItemModifier.hotel_id == self.h, OrderItemModifier.order_item_id.in_(item_ids)
                    )
                )
            ).scalars():
                out[m.order_item_id].append(m)
        return out

    async def history(self, order_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[OrderStatusHistory]]:
        out: dict[uuid.UUID, list[OrderStatusHistory]] = defaultdict(list)
        if order_ids:
            for h in (
                await self.s.execute(
                    select(OrderStatusHistory)
                    .where(OrderStatusHistory.hotel_id == self.h, OrderStatusHistory.order_id.in_(order_ids))
                    .order_by(OrderStatusHistory.created_at, OrderStatusHistory.id)
                )
            ).scalars():
                out[h.order_id].append(h)
        return out
