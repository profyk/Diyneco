"""Test data, inserted through the owner connection (BYPASSRLS).

Every call creates fresh hotels and users with unique names, so tests never share state and
never need cleanup.
"""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import crypto
from app.core.jwt import ACCESS_TTL_S
from app.core.state import AppState
from app.models import domain as d
from app.models import events as ev
from app.models import tenancy as t
from app.services import mfa

ALL_HOTEL_ROLES = (
    "hotel_owner", "hotel_admin", "general_manager", "reception_manager", "receptionist",
    "finance_manager", "kitchen_manager", "kitchen_staff", "room_service_manager", "room_service_staff",
)
MFA_ROLES = {"hotel_owner", "hotel_admin", "general_manager", "finance_manager"}
PIN = "1234"


def strong_password() -> str:
    return f"Test-Password-{secrets.token_hex(6)}"


@dataclass
class SeededUser:
    role: str
    email: str
    password: str
    user_id: uuid.UUID
    hotel_user_id: uuid.UUID | None
    name: str
    totp_secret: str | None = None


@dataclass
class SeededHotel:
    id: uuid.UUID
    name: str
    users: dict[str, SeededUser] = field(default_factory=dict)
    room_type_id: uuid.UUID | None = None
    room_ids: list[uuid.UUID] = field(default_factory=list)
    station_id: uuid.UUID | None = None


@dataclass
class Factory:
    sessionmaker: async_sessionmaker[AsyncSession]
    state: AppState

    async def _system_role(self, s: AsyncSession, code: str) -> uuid.UUID:
        return (await s.execute(select(t.Role.id).where(t.Role.hotel_id.is_(None), t.Role.code == code))).scalar_one()

    async def user(
        self, s: AsyncSession, *, name: str, is_platform: bool = False, with_totp: bool = False
    ) -> tuple[uuid.UUID, str, str, str | None]:
        email = f"{name.lower().replace(' ', '.')}.{secrets.token_hex(4)}@example.test"
        password = strong_password()
        user_id = (
            await s.execute(
                insert(t.User)
                .values(email=email, name=name, password_hash=crypto.hash_secret(password),
                        email_verified_at=datetime.now(UTC), is_platform=is_platform)
                .returning(t.User.id)
            )
        ).scalar_one()
        secret = None
        if with_totp:
            secret = mfa.new_secret()
            await s.execute(
                insert(t.MfaFactor).values(
                    user_id=user_id, kind="totp", confirmed_at=datetime.now(UTC),
                    secret_enc=await self.state.keyring.encrypt("platform", secret.encode(), f"mfa:{user_id}"),
                )
            )
        return user_id, email, password, secret

    async def hotel(
        self, *, roles: tuple[str, ...] = ALL_HOTEL_ROLES, name: str | None = None, mfa_for_required: bool = True,
        status: str = "active", rooms: int = 2,
    ) -> SeededHotel:
        name = name or f"Hotel {secrets.token_hex(3)}"
        async with self.sessionmaker() as s, s.begin():
            hotel_id = (
                await s.execute(
                    insert(t.Hotel).values(name=name, slug=f"h-{secrets.token_hex(6)}", status=status)
                    .returning(t.Hotel.id)
                )
            ).scalar_one()
            await s.execute(insert(t.HotelSettings).values(hotel_id=hotel_id, invoice_prefix="TST"))
            plan_id = (await s.execute(select(t.Plan.id).where(t.Plan.code == "starter"))).scalar_one()
            await s.execute(insert(t.Subscription).values(hotel_id=hotel_id, plan_id=plan_id, status="active",
                                                          starts_on=date.today()))
            await s.execute(insert(ev.EventSeq).values(hotel_id=hotel_id))
            await s.execute(insert(d.OrderNumberSequence).values(hotel_id=hotel_id))
            seeded = SeededHotel(id=hotel_id, name=name)
            for role in roles:
                with_totp = mfa_for_required and role in MFA_ROLES
                uid, email, password, secret = await self.user(s, name=role.replace("_", " ").title(),
                                                               with_totp=with_totp)
                hu = (
                    await s.execute(
                        insert(t.HotelUser).values(hotel_id=hotel_id, user_id=uid, pin_hash=crypto.hash_secret(PIN))
                        .returning(t.HotelUser.id)
                    )
                ).scalar_one()
                await s.execute(insert(t.UserRole).values(hotel_id=hotel_id, hotel_user_id=hu,
                                                          role_id=await self._system_role(s, role)))
                seeded.users[role] = SeededUser(role, email, password, uid, hu, role.replace("_", " ").title(), secret)
            seeded.room_type_id = (
                await s.execute(
                    insert(d.RoomType).values(hotel_id=hotel_id, name="Standard", base_rate_minor=150000)
                    .returning(d.RoomType.id)
                )
            ).scalar_one()
            for n in range(rooms):
                seeded.room_ids.append(
                    (
                        await s.execute(
                            insert(d.Room).values(hotel_id=hotel_id, room_type_id=seeded.room_type_id,
                                                  number=str(101 + n)).returning(d.Room.id)
                        )
                    ).scalar_one()
                )
            seeded.station_id = (
                await s.execute(
                    insert(d.KitchenStation).values(hotel_id=hotel_id, name="Main Kitchen")
                    .returning(d.KitchenStation.id)
                )
            ).scalar_one()
        return seeded

    async def platform_user(self, role: str = "platform_super_admin") -> SeededUser:
        async with self.sessionmaker() as s, s.begin():
            uid, email, password, secret = await self.user(s, name="Platform Admin", is_platform=True, with_totp=True)
            await s.execute(insert(t.PlatformUserRole).values(user_id=uid, role_id=await self._system_role(s, role)))
        return SeededUser(role, email, password, uid, None, "Platform Admin", secret)

    async def token(
        self, hotel: SeededHotel | None, user: SeededUser, *, amr: tuple[str, ...] = ("pwd", "mfa"),
        mfa_pending: bool = False, perms_v: int | None = None, kind: str | None = None,
    ) -> tuple[str, uuid.UUID]:
        """Mint an access token with a real session row, skipping the login flow."""
        async with self.sessionmaker() as s, s.begin():
            sid = (
                await s.execute(
                    insert(t.Session).values(
                        user_id=user.user_id, family_id=uuid.uuid4(), active_hotel_id=hotel.id if hotel else None,
                        refresh_hash=crypto.sha256(secrets.token_hex(16)), amr=list(amr),
                        expires_at=datetime.now(UTC) + timedelta(days=1),
                    ).returning(t.Session.id)
                )
            ).scalar_one()
            if hotel is not None and perms_v is None:
                perms_v = (
                    await s.execute(select(t.HotelUser.perms_version).where(t.HotelUser.id == user.hotel_user_id))
                ).scalar_one()
        claims: dict[str, Any] = {"sub": str(user.user_id), "kind": kind or ("staff" if hotel else "platform"),
                                  "sid": str(sid), "amr": list(amr)}
        if hotel is not None:
            claims["hid"] = str(hotel.id)
            claims["perms_v"] = perms_v
        if mfa_pending:
            claims["mfa_pending"] = True
        token, _ = self.state.jwt.sign("access", claims, ACCESS_TTL_S)
        return token, sid

    async def auth(self, hotel: SeededHotel, role: str) -> dict[str, str]:
        token, _ = await self.token(hotel, hotel.users[role])
        return {"Authorization": f"Bearer {token}"}

    async def step_up(self, hotel: SeededHotel, role: str, headers: dict[str, str]) -> dict[str, str]:
        from app.core.jwt import STEP_UP_TTL_S

        claims = self.state.jwt.verify(headers["Authorization"].split(" ", 1)[1], "access")
        token, _ = self.state.jwt.sign("step_up", {"sub": claims["sub"], "sid": claims["sid"], "hid": claims["hid"]},
                                       STEP_UP_TTL_S)
        return {**headers, "X-Step-Up": token}

    # --- domain rows for database tests ----------------------------------------------------

    async def stay_with_folio(self, hotel: SeededHotel, room_index: int = 0, status: str = "active") -> dict[str, Any]:
        async with self.sessionmaker() as s, s.begin():
            guest = (
                await s.execute(insert(d.Guest).values(hotel_id=hotel.id, full_name="Test Guest").returning(d.Guest.id))
            ).scalar_one()
            stay = (
                await s.execute(
                    insert(d.Stay).values(hotel_id=hotel.id, room_id=hotel.room_ids[room_index], guest_id=guest,
                                          status=status, arrival_date=date.today(),
                                          departure_date=date.today() + timedelta(days=2),
                                          nightly_rate_minor=150000).returning(d.Stay.id)
                )
            ).scalar_one()
            folio = (
                await s.execute(insert(d.Folio).values(hotel_id=hotel.id, stay_id=stay).returning(d.Folio.id))
            ).scalar_one()
            food = (
                await s.execute(select(d.ChargeCategory.id).where(d.ChargeCategory.hotel_id.is_(None),
                                                                  d.ChargeCategory.code == "food"))
            ).scalar_one()
            entry = (
                await s.execute(
                    insert(d.FolioEntry).values(
                        hotel_id=hotel.id, folio_id=folio, entry_type="charge", category_id=food,
                        description="Breakfast", unit_amount_minor=15000, amount_minor=15000,
                        business_date=date.today(),
                    ).returning(d.FolioEntry.id)
                )
            ).scalar_one()
        return {"guest_id": guest, "stay_id": stay, "folio_id": folio, "entry_id": entry, "food_category": food}

    async def order(self, hotel: SeededHotel, stay_id: uuid.UUID, status: str = "NEW") -> uuid.UUID:
        async with self.sessionmaker() as s, s.begin():
            number = (
                await s.execute(
                    text("UPDATE app.order_number_sequences SET next_number = next_number + 1 "
                         "WHERE hotel_id = :h RETURNING next_number - 1"), {"h": hotel.id}
                )
            ).scalar_one()
            order_id = (
                await s.execute(
                    insert(d.Order).values(
                        hotel_id=hotel.id, number=number, stay_id=stay_id, room_id=hotel.room_ids[0],
                        room_number="101", status=status, subtotal_minor=31000, fee_minor=5000,
                        total_minor=36000, idempotency_key=uuid.uuid4(),
                    ).returning(d.Order.id)
                )
            ).scalar_one()
        return order_id
