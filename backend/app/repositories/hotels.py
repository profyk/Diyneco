"""Hotel, settings and subscription reads/writes. Every method takes a TenantContext and
filters by its hotel_id; RLS enforces the same rule underneath."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import TenantContext
from app.models.tenancy import Hotel, HotelSettings, Plan, Subscription


class HotelRepository:
    def __init__(self, session: AsyncSession, ctx: TenantContext) -> None:
        self.s = session
        self.ctx = ctx

    async def get(self) -> Hotel | None:
        return (await self.s.execute(select(Hotel).where(Hotel.id == self.ctx.hotel_id))).scalar_one_or_none()

    async def current_plan(self) -> tuple[Plan, Subscription] | None:
        row = (
            await self.s.execute(
                select(Plan, Subscription)
                .join(Subscription, Subscription.plan_id == Plan.id)
                .where(
                    Subscription.hotel_id == self.ctx.hotel_id,
                    Subscription.status.in_(("trialing", "active", "past_due")),
                )
            )
        ).first()
        return (row[0], row[1]) if row else None

    async def update(self, expected_version: int, values: dict[str, Any]) -> Hotel | None:
        """Optimistic update. None when the version no longer matches."""
        return (
            await self.s.execute(
                update(Hotel)
                .where(Hotel.id == self.ctx.hotel_id, Hotel.version == expected_version)
                .values(**values, version=Hotel.version + 1)
                .returning(Hotel)
            )
        ).scalar_one_or_none()

    async def get_settings(self) -> HotelSettings | None:
        return (
            await self.s.execute(select(HotelSettings).where(HotelSettings.hotel_id == self.ctx.hotel_id))
        ).scalar_one_or_none()

    async def update_settings(self, expected_version: int, values: dict[str, Any]) -> HotelSettings | None:
        return (
            await self.s.execute(
                update(HotelSettings)
                .where(HotelSettings.hotel_id == self.ctx.hotel_id, HotelSettings.version == expected_version)
                .values(**values, version=HotelSettings.version + 1)
                .returning(HotelSettings)
            )
        ).scalar_one_or_none()
