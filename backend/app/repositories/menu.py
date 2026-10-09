"""Kitchen stations and the menu of one hotel. Deleted rows (deleted_at set) are hidden."""

from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import TenantContext
from app.models.domain import (
    KitchenStation,
    MenuCategory,
    MenuItem,
    MenuItemModifier,
    MenuModifier,
    MenuModifierGroup,
    MenuSchedule,
)


class MenuRepository:
    def __init__(self, session: AsyncSession, ctx: TenantContext) -> None:
        self.s = session
        self.ctx = ctx
        self.h = ctx.hotel_id

    # --- stations ------------------------------------------------------------------------

    async def stations(self, *, active_only: bool = False) -> list[KitchenStation]:
        q = select(KitchenStation).where(KitchenStation.hotel_id == self.h)
        if active_only:
            q = q.where(KitchenStation.is_active.is_(True))
        return list(
            (await self.s.execute(q.order_by(KitchenStation.sort_order, KitchenStation.name))).scalars()
        )

    async def station(self, station_id: uuid.UUID, *, for_update: bool = False) -> KitchenStation | None:
        q = select(KitchenStation).where(KitchenStation.hotel_id == self.h, KitchenStation.id == station_id)
        if for_update:
            q = q.with_for_update()
        return (await self.s.execute(q)).scalar_one_or_none()

    async def station_name_taken(self, name: str, exclude: uuid.UUID | None = None) -> bool:
        q = select(KitchenStation.id).where(KitchenStation.hotel_id == self.h, KitchenStation.name == name)
        if exclude is not None:
            q = q.where(KitchenStation.id != exclude)
        return (await self.s.execute(q)).first() is not None

    async def create_station(self, values: dict[str, Any]) -> KitchenStation:
        return (
            await self.s.execute(
                insert(KitchenStation).values(hotel_id=self.h, **values).returning(KitchenStation)
            )
        ).scalar_one()

    async def update_station(self, station_id: uuid.UUID, values: dict[str, Any]) -> KitchenStation:
        return (
            await self.s.execute(
                update(KitchenStation)
                .where(KitchenStation.hotel_id == self.h, KitchenStation.id == station_id)
                .values(**values)
                .returning(KitchenStation)
            )
        ).scalar_one()

    async def live_items_at_station(self, station_id: uuid.UUID) -> int:
        return int(
            (
                await self.s.execute(
                    select(func.count()).where(
                        MenuItem.hotel_id == self.h,
                        MenuItem.station_id == station_id,
                        MenuItem.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )

    # --- schedules -----------------------------------------------------------------------

    async def schedules(self) -> list[MenuSchedule]:
        return list(
            (
                await self.s.execute(
                    select(MenuSchedule).where(MenuSchedule.hotel_id == self.h).order_by(MenuSchedule.name)
                )
            ).scalars()
        )

    async def schedule(self, schedule_id: uuid.UUID) -> MenuSchedule | None:
        return (
            await self.s.execute(
                select(MenuSchedule).where(MenuSchedule.hotel_id == self.h, MenuSchedule.id == schedule_id)
            )
        ).scalar_one_or_none()

    async def create_schedule(self, name: str, windows: list[dict[str, Any]]) -> MenuSchedule:
        return (
            await self.s.execute(
                insert(MenuSchedule)
                .values(hotel_id=self.h, name=name, windows=windows)
                .returning(MenuSchedule)
            )
        ).scalar_one()

    # --- categories ----------------------------------------------------------------------

    async def categories(self) -> list[MenuCategory]:
        return list(
            (
                await self.s.execute(
                    select(MenuCategory)
                    .where(MenuCategory.hotel_id == self.h, MenuCategory.deleted_at.is_(None))
                    .order_by(MenuCategory.sort_order, MenuCategory.name)
                )
            ).scalars()
        )

    async def category(self, category_id: uuid.UUID) -> MenuCategory | None:
        return (
            await self.s.execute(
                select(MenuCategory).where(
                    MenuCategory.hotel_id == self.h,
                    MenuCategory.id == category_id,
                    MenuCategory.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()

    async def create_category(self, values: dict[str, Any]) -> MenuCategory:
        return (
            await self.s.execute(
                insert(MenuCategory).values(hotel_id=self.h, **values).returning(MenuCategory)
            )
        ).scalar_one()

    async def update_category(self, category_id: uuid.UUID, values: dict[str, Any]) -> MenuCategory:
        return (
            await self.s.execute(
                update(MenuCategory)
                .where(MenuCategory.hotel_id == self.h, MenuCategory.id == category_id)
                .values(**values)
                .returning(MenuCategory)
            )
        ).scalar_one()

    async def live_items_in_category(self, category_id: uuid.UUID) -> int:
        return int(
            (
                await self.s.execute(
                    select(func.count()).where(
                        MenuItem.hotel_id == self.h,
                        MenuItem.category_id == category_id,
                        MenuItem.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )

    # --- items ---------------------------------------------------------------------------

    async def items(
        self,
        *,
        category_id: uuid.UUID | None = None,
        station_id: uuid.UUID | None = None,
        ids: list[uuid.UUID] | None = None,
    ) -> list[MenuItem]:
        q = select(MenuItem).where(MenuItem.hotel_id == self.h, MenuItem.deleted_at.is_(None))
        if category_id is not None:
            q = q.where(MenuItem.category_id == category_id)
        if station_id is not None:
            q = q.where(MenuItem.station_id == station_id)
        if ids is not None:
            q = q.where(MenuItem.id.in_(ids))
        return list((await self.s.execute(q.order_by(MenuItem.sort_order, MenuItem.name))).scalars())

    async def item(self, item_id: uuid.UUID, *, for_update: bool = False) -> MenuItem | None:
        q = select(MenuItem).where(
            MenuItem.hotel_id == self.h, MenuItem.id == item_id, MenuItem.deleted_at.is_(None)
        )
        if for_update:
            q = q.with_for_update()
        return (await self.s.execute(q)).scalar_one_or_none()

    async def create_item(self, values: dict[str, Any]) -> MenuItem:
        return (
            await self.s.execute(insert(MenuItem).values(hotel_id=self.h, **values).returning(MenuItem))
        ).scalar_one()

    async def update_item(
        self, item_id: uuid.UUID, expected_version: int | None, values: dict[str, Any]
    ) -> MenuItem | None:
        q = update(MenuItem).where(
            MenuItem.hotel_id == self.h, MenuItem.id == item_id, MenuItem.deleted_at.is_(None)
        )
        if expected_version is not None:
            q = q.where(MenuItem.version == expected_version)
        return (
            await self.s.execute(q.values(**values, version=MenuItem.version + 1).returning(MenuItem))
        ).scalar_one_or_none()

    # --- modifiers -----------------------------------------------------------------------

    async def groups(self, ids: list[uuid.UUID] | None = None) -> list[MenuModifierGroup]:
        q = select(MenuModifierGroup).where(
            MenuModifierGroup.hotel_id == self.h, MenuModifierGroup.deleted_at.is_(None)
        )
        if ids is not None:
            q = q.where(MenuModifierGroup.id.in_(ids))
        return list((await self.s.execute(q.order_by(MenuModifierGroup.name))).scalars())

    async def create_group(self, values: dict[str, Any]) -> MenuModifierGroup:
        return (
            await self.s.execute(
                insert(MenuModifierGroup).values(hotel_id=self.h, **values).returning(MenuModifierGroup)
            )
        ).scalar_one()

    async def options(self, group_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[MenuModifier]]:
        out: dict[uuid.UUID, list[MenuModifier]] = defaultdict(list)
        if group_ids:
            for m in (
                await self.s.execute(
                    select(MenuModifier)
                    .where(
                        MenuModifier.hotel_id == self.h,
                        MenuModifier.group_id.in_(group_ids),
                        MenuModifier.deleted_at.is_(None),
                    )
                    .order_by(MenuModifier.sort_order, MenuModifier.name)
                )
            ).scalars():
                out[m.group_id].append(m)
        return out

    async def create_option(self, values: dict[str, Any]) -> MenuModifier:
        return (
            await self.s.execute(
                insert(MenuModifier).values(hotel_id=self.h, **values).returning(MenuModifier)
            )
        ).scalar_one()

    async def item_groups(self, item_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[uuid.UUID]]:
        out: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
        if item_ids:
            for item_id, group_id in (
                await self.s.execute(
                    select(MenuItemModifier.item_id, MenuItemModifier.group_id)
                    .where(MenuItemModifier.hotel_id == self.h, MenuItemModifier.item_id.in_(item_ids))
                    .order_by(MenuItemModifier.sort_order)
                )
            ).all():
                out[item_id].append(group_id)
        return out

    async def set_item_groups(self, item_id: uuid.UUID, group_ids: list[uuid.UUID]) -> None:
        await self.s.execute(
            delete(MenuItemModifier).where(
                MenuItemModifier.hotel_id == self.h, MenuItemModifier.item_id == item_id
            )
        )
        if group_ids:
            await self.s.execute(
                insert(MenuItemModifier),
                [
                    {"hotel_id": self.h, "item_id": item_id, "group_id": g, "sort_order": i}
                    for i, g in enumerate(group_ids)
                ],
            )

    async def guest_room_channels(self) -> list[uuid.UUID]:
        """Rooms that have a live guest tablet (for MENU_UPDATED)."""
        rows = await self.s.execute(
            text(
                "SELECT room_id FROM app.devices WHERE hotel_id = :h AND kind = 'guest' "
                "AND status <> 'revoked' AND room_id IS NOT NULL"
            ),
            {"h": self.h},
        )
        return [r[0] for r in rows]
