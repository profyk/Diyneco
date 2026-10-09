"""Devices, their stations and pairing codes for one hotel."""

from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import TenantContext
from app.models.domain import Device, DevicePairing, DeviceStation, KitchenStation, Room


class DeviceRepository:
    def __init__(self, session: AsyncSession, ctx: TenantContext) -> None:
        self.s = session
        self.ctx = ctx

    async def list_page(
        self,
        *,
        kind: str | None,
        status: str | None,
        room_id: uuid.UUID | None,
        after: list[Any] | None,
        limit: int,
    ) -> list[Device]:
        q = select(Device).where(Device.hotel_id == self.ctx.hotel_id)
        if kind is not None:
            q = q.where(Device.kind == kind)
        if status is not None:
            q = q.where(Device.status == status)
        if room_id is not None:
            q = q.where(Device.room_id == room_id)
        if after is not None:
            q = q.where(Device.label > str(after[0]))
        q = q.order_by(Device.label).limit(limit + 1)
        return list((await self.s.execute(q)).scalars())

    async def get(self, device_id: uuid.UUID, *, for_update: bool = False) -> Device | None:
        q = select(Device).where(Device.hotel_id == self.ctx.hotel_id, Device.id == device_id)
        if for_update:
            q = q.with_for_update()
        return (await self.s.execute(q)).scalar_one_or_none()

    async def live_guest_device_for_room(self, room_id: uuid.UUID) -> Device | None:
        return (
            await self.s.execute(
                select(Device).where(
                    Device.hotel_id == self.ctx.hotel_id,
                    Device.room_id == room_id,
                    Device.kind == "guest",
                    Device.status != "revoked",
                )
            )
        ).scalar_one_or_none()

    async def labels_like(self, prefix: str) -> set[str]:
        return set(
            (
                await self.s.execute(
                    select(Device.label).where(
                        Device.hotel_id == self.ctx.hotel_id, Device.label.startswith(prefix)
                    )
                )
            ).scalars()
        )

    async def create(self, values: dict[str, Any]) -> Device:
        return (
            await self.s.execute(
                insert(Device).values(hotel_id=self.ctx.hotel_id, **values).returning(Device)
            )
        ).scalar_one()

    async def update(self, device_id: uuid.UUID, values: dict[str, Any]) -> Device:
        return (
            await self.s.execute(
                update(Device)
                .where(Device.hotel_id == self.ctx.hotel_id, Device.id == device_id)
                .values(**values, updated_at=text("now()"))
                .returning(Device)
            )
        ).scalar_one()

    async def set_stations(self, device_id: uuid.UUID, station_ids: list[uuid.UUID]) -> None:
        await self.s.execute(
            delete(DeviceStation).where(
                DeviceStation.hotel_id == self.ctx.hotel_id, DeviceStation.device_id == device_id
            )
        )
        if station_ids:
            await self.s.execute(
                insert(DeviceStation),
                [
                    {"hotel_id": self.ctx.hotel_id, "device_id": device_id, "station_id": s}
                    for s in station_ids
                ],
            )

    async def stations_by_device(self, device_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[KitchenStation]]:
        out: dict[uuid.UUID, list[KitchenStation]] = defaultdict(list)
        if device_ids:
            for device_id, station in (
                await self.s.execute(
                    select(DeviceStation.device_id, KitchenStation)
                    .join(KitchenStation, KitchenStation.id == DeviceStation.station_id)
                    .where(
                        DeviceStation.hotel_id == self.ctx.hotel_id, DeviceStation.device_id.in_(device_ids)
                    )
                    .order_by(KitchenStation.sort_order, KitchenStation.name)
                )
            ).all():
                out[device_id].append(station)
        return out

    async def rooms(self, room_ids: list[uuid.UUID]) -> dict[uuid.UUID, Room]:
        if not room_ids:
            return {}
        return {
            r.id: r
            for r in (
                await self.s.execute(
                    select(Room).where(Room.hotel_id == self.ctx.hotel_id, Room.id.in_(room_ids))
                )
            ).scalars()
        }

    async def live_room(self, room_id: uuid.UUID) -> Room | None:
        return (
            await self.s.execute(
                select(Room).where(
                    Room.hotel_id == self.ctx.hotel_id, Room.id == room_id, Room.deleted_at.is_(None)
                )
            )
        ).scalar_one_or_none()

    async def active_stations(self, station_ids: list[uuid.UUID]) -> list[KitchenStation]:
        if not station_ids:
            return []
        return list(
            (
                await self.s.execute(
                    select(KitchenStation).where(
                        KitchenStation.hotel_id == self.ctx.hotel_id,
                        KitchenStation.id.in_(station_ids),
                        KitchenStation.is_active.is_(True),
                    )
                )
            ).scalars()
        )

    # --- pairing codes -------------------------------------------------------------------

    async def create_pairing(self, values: dict[str, Any]) -> DevicePairing:
        return (
            await self.s.execute(
                insert(DevicePairing).values(hotel_id=self.ctx.hotel_id, **values).returning(DevicePairing)
            )
        ).scalar_one()

    async def pairing(self, pairing_id: uuid.UUID) -> DevicePairing | None:
        return (
            await self.s.execute(
                select(DevicePairing).where(
                    DevicePairing.hotel_id == self.ctx.hotel_id, DevicePairing.id == pairing_id
                )
            )
        ).scalar_one_or_none()

    async def mark_pairing_used(self, pairing_id: uuid.UUID, device_id: uuid.UUID) -> None:
        await self.s.execute(
            update(DevicePairing)
            .where(DevicePairing.hotel_id == self.ctx.hotel_id, DevicePairing.id == pairing_id)
            .values(used_by_device=device_id)
        )
