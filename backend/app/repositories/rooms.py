"""Room types and rooms of one hotel. Every query filters by the context's hotel_id; RLS
enforces the same rule underneath. Deleted rows (deleted_at set) are invisible here."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import and_, func, insert, select, text, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import TenantContext
from app.models.domain import Device, Room, RoomType, Stay

LIVE_STAY = ("checked_in", "active", "checkout_pending")


class RoomTypeRepository:
    def __init__(self, session: AsyncSession, ctx: TenantContext) -> None:
        self.s = session
        self.ctx = ctx

    def _base(self) -> Any:
        return select(RoomType).where(RoomType.hotel_id == self.ctx.hotel_id, RoomType.deleted_at.is_(None))

    async def list_with_counts(self) -> list[tuple[RoomType, int]]:
        counts = (
            select(Room.room_type_id, func.count().label("n"))
            .where(Room.hotel_id == self.ctx.hotel_id, Room.deleted_at.is_(None))
            .group_by(Room.room_type_id)
            .subquery()
        )
        rows = (
            await self.s.execute(
                select(RoomType, func.coalesce(counts.c.n, 0))
                .outerjoin(counts, counts.c.room_type_id == RoomType.id)
                .where(RoomType.hotel_id == self.ctx.hotel_id, RoomType.deleted_at.is_(None))
                .order_by(func.lower(RoomType.name))
            )
        ).all()
        return [(r[0], int(r[1])) for r in rows]

    async def get(self, room_type_id: uuid.UUID, *, for_update: bool = False) -> RoomType | None:
        q = self._base().where(RoomType.id == room_type_id)
        if for_update:
            q = q.with_for_update()
        return (await self.s.execute(q)).scalar_one_or_none()

    async def by_lower_names(self) -> dict[str, RoomType]:
        return {rt.name.lower(): rt for rt in (await self.s.execute(self._base())).scalars().all()}

    async def name_taken(self, name: str, exclude: uuid.UUID | None = None) -> bool:
        q = select(RoomType.id).where(
            RoomType.hotel_id == self.ctx.hotel_id,
            RoomType.deleted_at.is_(None),
            func.lower(RoomType.name) == name.lower(),
        )
        if exclude is not None:
            q = q.where(RoomType.id != exclude)
        return (await self.s.execute(q)).first() is not None

    async def room_count(self, room_type_id: uuid.UUID) -> int:
        return int(
            (
                await self.s.execute(
                    select(func.count()).where(
                        Room.hotel_id == self.ctx.hotel_id,
                        Room.room_type_id == room_type_id,
                        Room.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )

    async def create(self, values: dict[str, Any]) -> RoomType:
        return (
            await self.s.execute(
                insert(RoomType).values(hotel_id=self.ctx.hotel_id, **values).returning(RoomType)
            )
        ).scalar_one()

    async def update(
        self, room_type_id: uuid.UUID, expected_version: int, values: dict[str, Any]
    ) -> RoomType | None:
        return (
            await self.s.execute(
                update(RoomType)
                .where(
                    RoomType.hotel_id == self.ctx.hotel_id,
                    RoomType.id == room_type_id,
                    RoomType.deleted_at.is_(None),
                    RoomType.version == expected_version,
                )
                .values(**values, version=RoomType.version + 1, updated_at=text("now()"))
                .returning(RoomType)
            )
        ).scalar_one_or_none()


def room_sort_key(room: Room) -> list[Any]:
    return [len(room.number), room.number, str(room.id)]


class RoomRepository:
    def __init__(self, session: AsyncSession, ctx: TenantContext) -> None:
        self.s = session
        self.ctx = ctx

    def _base(self) -> Any:
        return select(Room).where(Room.hotel_id == self.ctx.hotel_id, Room.deleted_at.is_(None))

    async def list_page(
        self,
        *,
        status: str | None,
        floor: str | None,
        room_type_id: uuid.UUID | None,
        after: list[Any] | None,
        limit: int,
    ) -> list[Room]:
        """Natural number order (101 before 1001), keyset-paginated."""
        q = self._base()
        if status is not None:
            q = q.where(Room.status == status)
        if floor is not None:
            q = q.where(Room.floor == floor)
        if room_type_id is not None:
            q = q.where(Room.room_type_id == room_type_id)
        key = tuple_(func.length(Room.number), Room.number, Room.id)
        if after is not None:
            q = q.where(key > tuple_(int(after[0]), str(after[1]), uuid.UUID(str(after[2]))))
        q = q.order_by(func.length(Room.number), Room.number, Room.id).limit(limit + 1)
        return list((await self.s.execute(q)).scalars().all())

    async def get(self, room_id: uuid.UUID, *, for_update: bool = False) -> Room | None:
        q = self._base().where(Room.id == room_id)
        if for_update:
            q = q.with_for_update()
        return (await self.s.execute(q)).scalar_one_or_none()

    async def get_many(self, room_ids: list[uuid.UUID]) -> list[Room]:
        if not room_ids:
            return []
        return list((await self.s.execute(self._base().where(Room.id.in_(room_ids)))).scalars().all())

    async def existing_numbers(self, numbers: list[str]) -> set[str]:
        if not numbers:
            return set()
        found: set[str] = set()
        for start in range(0, len(numbers), 1000):
            chunk = numbers[start : start + 1000]
            found |= set(
                (
                    await self.s.execute(
                        select(Room.number).where(
                            Room.hotel_id == self.ctx.hotel_id,
                            Room.deleted_at.is_(None),
                            Room.number.in_(chunk),
                        )
                    )
                )
                .scalars()
                .all()
            )
        return found

    async def create_many(self, rows: list[dict[str, Any]]) -> list[Room]:
        if not rows:
            return []
        created: list[Room] = []
        for start in range(0, len(rows), 500):
            chunk = [{**r, "hotel_id": self.ctx.hotel_id} for r in rows[start : start + 500]]
            created.extend((await self.s.execute(insert(Room).returning(Room), chunk)).scalars().all())
        return created

    async def update(
        self, room_id: uuid.UUID, expected_version: int | None, values: dict[str, Any]
    ) -> Room | None:
        conds = [Room.hotel_id == self.ctx.hotel_id, Room.id == room_id, Room.deleted_at.is_(None)]
        if expected_version is not None:
            conds.append(Room.version == expected_version)
        return (
            await self.s.execute(
                update(Room)
                .where(and_(*conds))
                .values(**values, version=Room.version + 1, updated_at=text("now()"))
                .returning(Room)
            )
        ).scalar_one_or_none()

    async def has_live_stay(self, room_id: uuid.UUID) -> bool:
        return (
            await self.s.execute(
                select(Stay.id).where(
                    Stay.hotel_id == self.ctx.hotel_id, Stay.room_id == room_id, Stay.status.in_(LIVE_STAY)
                )
            )
        ).first() is not None

    async def has_any_stay(self, room_id: uuid.UUID) -> bool:
        return (
            await self.s.execute(
                select(Stay.id).where(Stay.hotel_id == self.ctx.hotel_id, Stay.room_id == room_id).limit(1)
            )
        ).first() is not None

    async def has_bound_device(self, room_id: uuid.UUID) -> bool:
        return (
            await self.s.execute(
                select(Device.id).where(
                    Device.hotel_id == self.ctx.hotel_id,
                    Device.room_id == room_id,
                    Device.status != "revoked",
                )
            )
        ).first() is not None
