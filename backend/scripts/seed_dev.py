"""Development seed: two demo hotels with rooms, kitchen stations and one user per role.

    uv run python scripts/seed_dev.py

Refuses to run unless APP_ENV=development. Safe to re-run: existing demo hotels are left as
they are. Every demo user has the password printed at the end and PIN 1234; users in
MFA-required roles (owner, admin, general manager, finance) enrol TOTP at first sign-in.
Menus and a paired demo tablet are added when those features arrive (Phases 3 and 4).
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import crypto
from app.core.config import get_settings
from app.models import domain as d
from app.models import events as ev
from app.models import tenancy as t

DEMO_PASSWORD = "Diyneco-Demo-Password-2026"  # development only; never valid elsewhere
DEMO_PIN = "1234"

HOTELS = [
    {
        "slug": "grand-example-hotel",
        "name": "Grand Example Hotel",
        "domain": "grandexample.example",
        "prefix": "GEH",
        "currency": "ZAR",
        "address": {
            "line1": "1 Beach Road",
            "city": "Cape Town",
            "province": "Western Cape",
            "country": "ZA",
        },
        "room_types": [
            ("Standard", 150000, 2, [f"{n}" for n in range(101, 111)]),
            ("Deluxe", 250000, 2, [f"{n}" for n in range(201, 206)]),
            ("Suite", 450000, 4, ["259", "301"]),
        ],
        "stations": ["Main Kitchen", "Bar", "Dessert Station", "Pool Bar"],
    },
    {
        "slug": "seabreeze-lodge",
        "name": "Seabreeze Lodge",
        "domain": "seabreeze.example",
        "prefix": "SBL",
        "currency": "NAD",
        "address": {
            "line1": "12 Dune Lane",
            "city": "Plettenberg Bay",
            "province": "Western Cape",
            "country": "ZA",
        },
        "room_types": [
            ("Garden Room", 120000, 2, [f"Garden {n}" for n in range(1, 7)]),
            ("Ocean Suite", 320000, 3, ["Ocean 1", "Ocean 2"]),
        ],
        "stations": ["Kitchen", "Bar"],
    },
]

ROLES = [
    ("hotel_owner", "owner", "Hotel Owner"),
    ("hotel_admin", "admin", "Hotel Admin"),
    ("general_manager", "gm", "General Manager"),
    ("reception_manager", "reception.manager", "Reception Manager"),
    ("receptionist", "reception", "Receptionist"),
    ("finance_manager", "finance", "Finance Manager"),
    ("kitchen_manager", "kitchen.manager", "Kitchen Manager"),
    ("kitchen_staff", "kitchen", "Kitchen Staff"),
    ("room_service_manager", "roomservice.manager", "Room-Service Manager"),
    ("room_service_staff", "roomservice", "Room-Service Staff"),
]


async def seed_hotel(s: AsyncSession, spec: dict) -> list[str]:  # type: ignore[type-arg]
    existing = (await s.execute(select(t.Hotel.id).where(t.Hotel.slug == spec["slug"]))).scalar_one_or_none()
    if existing is not None:
        return [f"{spec['name']}: already seeded"]
    hotel_id = (
        await s.execute(
            insert(t.Hotel)
            .values(
                name=spec["name"],
                slug=spec["slug"],
                status="active",
                address=spec["address"],
                email=f"hello@{spec['domain']}",
            )
            .returning(t.Hotel.id)
        )
    ).scalar_one()
    await s.execute(
        insert(t.HotelSettings).values(
            hotel_id=hotel_id,
            invoice_prefix=spec["prefix"],
            wifi_name=f"{spec['prefix']}-Guest",
            currency=spec["currency"],
        )
    )
    plan = (await s.execute(select(t.Plan.id).where(t.Plan.code == "professional"))).scalar_one()
    await s.execute(
        insert(t.Subscription).values(
            hotel_id=hotel_id, plan_id=plan, status="active", starts_on=date.today()
        )
    )
    await s.execute(insert(ev.EventSeq).values(hotel_id=hotel_id))
    await s.execute(insert(d.OrderNumberSequence).values(hotel_id=hotel_id))

    rooms = 0
    for name, rate, capacity, numbers in spec["room_types"]:
        rt = (
            await s.execute(
                insert(d.RoomType)
                .values(
                    hotel_id=hotel_id,
                    name=name,
                    base_rate_minor=rate,
                    capacity=capacity,
                    currency=spec["currency"],
                )
                .returning(d.RoomType.id)
            )
        ).scalar_one()
        for number in numbers:
            floor = number[0] if number[0].isdigit() else None
            await s.execute(
                insert(d.Room).values(hotel_id=hotel_id, room_type_id=rt, number=number, floor=floor)
            )
            rooms += 1
    for i, station in enumerate(spec["stations"]):
        await s.execute(insert(d.KitchenStation).values(hotel_id=hotel_id, name=station, sort_order=i))

    password_hash = crypto.hash_secret(DEMO_PASSWORD)
    pin_hash = crypto.hash_secret(DEMO_PIN)
    lines = [f"{spec['name']}: {rooms} rooms, {len(spec['stations'])} stations"]
    for code, local, label in ROLES:
        email = f"{local}@{spec['domain']}"
        user_id = (
            await s.execute(
                insert(t.User)
                .values(
                    email=email,
                    name=f"{label} ({spec['prefix']})",
                    password_hash=password_hash,
                    email_verified_at=datetime.now(UTC),
                )
                .returning(t.User.id)
            )
        ).scalar_one()
        hu = (
            await s.execute(
                insert(t.HotelUser)
                .values(hotel_id=hotel_id, user_id=user_id, pin_hash=pin_hash)
                .returning(t.HotelUser.id)
            )
        ).scalar_one()
        role_id = (
            await s.execute(select(t.Role.id).where(t.Role.hotel_id.is_(None), t.Role.code == code))
        ).scalar_one()
        await s.execute(insert(t.UserRole).values(hotel_id=hotel_id, hotel_user_id=hu, role_id=role_id))
        lines.append(f"  {email:<42} {label}")
    return lines


async def main() -> int:
    settings = get_settings()
    if settings.app_env != "development":
        print("Refusing to seed: APP_ENV is not 'development'.", file=sys.stderr)
        return 1
    if not settings.migrations_database_url:
        print("MIGRATIONS_DATABASE_URL is not set.", file=sys.stderr)
        return 1
    url = settings.migrations_database_url.replace("postgresql+psycopg://", "postgresql+asyncpg://")
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": "app, extensions"}})
    output: list[str] = []
    async with async_sessionmaker(engine)() as s, s.begin():
        for spec in HOTELS:
            output += await seed_hotel(s, spec)
    await engine.dispose()
    print("\n".join(output))
    print(f"\nPassword for every demo user: {DEMO_PASSWORD}\nPIN: {DEMO_PIN}")
    print("Owner, admin, GM and finance users set up two-step sign-in (TOTP) at first sign-in.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
