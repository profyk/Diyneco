"""Guests, billing profiles and stays of one hotel."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import TenantContext
from app.models.domain import BillingProfile, Guest, Room, Stay

LIVE = ("checked_in", "active", "checkout_pending")


class StayRepository:
    def __init__(self, session: AsyncSession, ctx: TenantContext) -> None:
        self.s = session
        self.h = ctx.hotel_id

    # --- guests --------------------------------------------------------------------------

    async def search_guests(self, q: str | None, limit: int) -> list[Guest]:
        query = select(Guest).where(Guest.hotel_id == self.h, Guest.anonymised_at.is_(None))
        if q:
            like = f"%{q.replace('%', '').replace('_', '')}%"
            query = query.where(
                or_(Guest.full_name.ilike(like), Guest.email.ilike(like), Guest.phone.ilike(like))
            )
        return list((await self.s.execute(query.order_by(Guest.full_name).limit(limit))).scalars())

    async def guest(self, guest_id: uuid.UUID, *, for_update: bool = False) -> Guest | None:
        q = select(Guest).where(Guest.hotel_id == self.h, Guest.id == guest_id)
        if for_update:
            q = q.with_for_update()
        return (await self.s.execute(q)).scalar_one_or_none()

    async def create_guest(self, values: dict[str, Any]) -> Guest:
        return (
            await self.s.execute(insert(Guest).values(hotel_id=self.h, **values).returning(Guest))
        ).scalar_one()

    async def update_guest(self, guest_id: uuid.UUID, values: dict[str, Any]) -> Guest:
        return (
            await self.s.execute(
                update(Guest)
                .where(Guest.hotel_id == self.h, Guest.id == guest_id)
                .values(**values)
                .returning(Guest)
            )
        ).scalar_one()

    async def stays_of_guest(self, guest_id: uuid.UUID) -> list[Stay]:
        return list(
            (
                await self.s.execute(
                    select(Stay)
                    .where(Stay.hotel_id == self.h, Stay.guest_id == guest_id)
                    .order_by(Stay.arrival_date.desc())
                )
            ).scalars()
        )

    # --- billing profiles ----------------------------------------------------------------

    async def search_profiles(self, q: str | None, limit: int) -> list[BillingProfile]:
        query = select(BillingProfile).where(BillingProfile.hotel_id == self.h)
        if q:
            query = query.where(BillingProfile.company_name.ilike(f"%{q.replace('%', '')}%"))
        return list(
            (await self.s.execute(query.order_by(BillingProfile.company_name).limit(limit))).scalars()
        )

    async def profile(self, profile_id: uuid.UUID) -> BillingProfile | None:
        return (
            await self.s.execute(
                select(BillingProfile).where(
                    BillingProfile.hotel_id == self.h, BillingProfile.id == profile_id
                )
            )
        ).scalar_one_or_none()

    async def create_profile(self, values: dict[str, Any]) -> BillingProfile:
        return (
            await self.s.execute(
                insert(BillingProfile).values(hotel_id=self.h, **values).returning(BillingProfile)
            )
        ).scalar_one()

    # --- stays ---------------------------------------------------------------------------

    async def stay(self, stay_id: uuid.UUID, *, for_update: bool = False) -> Stay | None:
        q = select(Stay).where(Stay.hotel_id == self.h, Stay.id == stay_id)
        if for_update:
            q = q.with_for_update()
        return (await self.s.execute(q)).scalar_one_or_none()

    async def live_stay_for_room(self, room_id: uuid.UUID) -> Stay | None:
        return (
            await self.s.execute(
                select(Stay).where(Stay.hotel_id == self.h, Stay.room_id == room_id, Stay.status.in_(LIVE))
            )
        ).scalar_one_or_none()

    async def list_stays(
        self,
        *,
        status: str | None,
        room_id: uuid.UUID | None,
        date_from: date | None,
        date_to: date | None,
        after: list[Any] | None,
        limit: int,
    ) -> list[Stay]:
        q = select(Stay).where(Stay.hotel_id == self.h)
        if status is not None:
            q = q.where(Stay.status == status)
        if room_id is not None:
            q = q.where(Stay.room_id == room_id)
        if date_from is not None:
            q = q.where(Stay.departure_date >= date_from)
        if date_to is not None:
            q = q.where(Stay.arrival_date <= date_to)
        if after is not None:
            q = q.where(Stay.id < uuid.UUID(str(after[0])))
        return list((await self.s.execute(q.order_by(Stay.id.desc()).limit(limit + 1))).scalars())

    async def overlapping(
        self, room_id: uuid.UUID, arrival: date, departure: date, exclude: uuid.UUID | None
    ) -> bool:
        q = select(func.count()).where(
            Stay.hotel_id == self.h,
            Stay.room_id == room_id,
            Stay.status.in_(("reserved", *LIVE)),
            Stay.arrival_date < departure,
            Stay.departure_date > arrival,
        )
        if exclude is not None:
            q = q.where(Stay.id != exclude)
        return int((await self.s.execute(q)).scalar_one()) > 0

    async def create_stay(self, values: dict[str, Any]) -> Stay:
        return (
            await self.s.execute(insert(Stay).values(hotel_id=self.h, **values).returning(Stay))
        ).scalar_one()

    async def update_stay(self, stay_id: uuid.UUID, values: dict[str, Any]) -> Stay:
        return (
            await self.s.execute(
                update(Stay)
                .where(Stay.hotel_id == self.h, Stay.id == stay_id)
                .values(**values, version=Stay.version + 1)
                .returning(Stay)
            )
        ).scalar_one()

    async def rooms(self, room_ids: list[uuid.UUID]) -> dict[uuid.UUID, Room]:
        if not room_ids:
            return {}
        rows = await self.s.execute(select(Room).where(Room.hotel_id == self.h, Room.id.in_(room_ids)))
        return {r.id: r for r in rows.scalars()}

    async def guests(self, guest_ids: list[uuid.UUID]) -> dict[uuid.UUID, Guest]:
        if not guest_ids:
            return {}
        rows = await self.s.execute(select(Guest).where(Guest.hotel_id == self.h, Guest.id.in_(guest_ids)))
        return {g.id: g for g in rows.scalars()}
