"""Browser end-to-end test accounts (development only).

    uv run python scripts/seed_e2e.py > ../packages/e2e/.accounts.json

Creates a fresh Diyneco Super Admin with a confirmed two-step sign-in whose secret is printed,
so a browser test can sign in to the Admin panel on every run, and prints the demo hotel's
receptionist (from seed_dev.py) for the Merchant app. For the subscription journey it adds a
fresh owner (with two-step sign-in) to the demo hotel, puts the demo hotel back on a free trial
(ending any current subscription; nothing is deleted) and publishes a test plan priced in the
database. Refuses to run unless APP_ENV=development. The output holds credentials for local
demo accounts only.
"""

from __future__ import annotations

import asyncio
import json
import secrets
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import insert, select, text, update

from app.core import crypto
from app.core.config import get_settings
from app.core.crypto import LocalKms
from app.core.state import Keyring
from app.db.session import Database
from app.models import tenancy as t
from app.services import mfa
from scripts.seed_dev import DEMO_PASSWORD, DEMO_PIN, HOTELS


async def main() -> int:
    settings = get_settings()
    if settings.app_env != "development" or not settings.migrations_database_url:
        print("Refusing to seed: development only, with MIGRATIONS_DATABASE_URL set.", file=sys.stderr)
        return 1
    url = settings.migrations_database_url.replace("postgresql+psycopg://", "postgresql+asyncpg://")
    db = Database(url, "diyneco-e2e-seed")
    keyring = Keyring(kms=LocalKms(settings.kms_local_master_key or "", settings.kms_master_key_id), db=db)
    email = f"e2e.admin.{secrets.token_hex(4)}@diyneco.example"
    password = f"E2e-Admin-{secrets.token_hex(6)}"
    secret = mfa.new_secret()
    async with db.sessionmaker() as s, s.begin():
        user_id = (
            await s.execute(
                insert(t.User)
                .values(
                    email=email,
                    name="E2E Admin",
                    password_hash=crypto.hash_secret(password),
                    email_verified_at=datetime.now(UTC),
                    is_platform=True,
                )
                .returning(t.User.id)
            )
        ).scalar_one()
        role_id = (
            await s.execute(
                select(t.Role.id).where(t.Role.hotel_id.is_(None), t.Role.code == "platform_super_admin")
            )
        ).scalar_one()
        await s.execute(insert(t.PlatformUserRole).values(user_id=user_id, role_id=role_id))
        await s.execute(
            insert(t.MfaFactor).values(
                user_id=user_id,
                kind="totp",
                confirmed_at=datetime.now(UTC),
                secret_enc=await keyring.encrypt("platform", secret.encode(), f"mfa:{user_id}"),
            )
        )
        owner = await _trial_owner(s, keyring)
        plan = await _published_plan(s)
    await db.dispose()
    print(
        json.dumps(
            {
                "admin": {"email": email, "password": password, "totp_secret": secret},
                "receptionist": {"email": "reception@grandexample.example", "password": DEMO_PASSWORD},
                "owner": owner,
                "plan": plan,
                "pin": DEMO_PIN,
            },
            indent=2,
        )
    )
    return 0


async def _trial_owner(s, keyring: Keyring) -> dict[str, str]:  # type: ignore[no-untyped-def]
    hotel_id = (await s.execute(select(t.Hotel.id).where(t.Hotel.slug == HOTELS[0]["slug"]))).scalar_one()
    email = f"e2e.owner.{secrets.token_hex(4)}@diyneco.example"
    password = f"E2e-Owner-{secrets.token_hex(6)}"
    secret = mfa.new_secret()
    user_id = (
        await s.execute(
            insert(t.User)
            .values(
                email=email,
                name="E2E Owner",
                password_hash=crypto.hash_secret(password),
                email_verified_at=datetime.now(UTC),
            )
            .returning(t.User.id)
        )
    ).scalar_one()
    member = (
        await s.execute(
            insert(t.HotelUser)
            .values(hotel_id=hotel_id, user_id=user_id, pin_hash=crypto.hash_secret(DEMO_PIN))
            .returning(t.HotelUser.id)
        )
    ).scalar_one()
    role = (
        await s.execute(select(t.Role.id).where(t.Role.hotel_id.is_(None), t.Role.code == "hotel_owner"))
    ).scalar_one()
    await s.execute(insert(t.UserRole).values(hotel_id=hotel_id, hotel_user_id=member, role_id=role))
    await s.execute(
        insert(t.MfaFactor).values(
            user_id=user_id,
            kind="totp",
            confirmed_at=datetime.now(UTC),
            secret_enc=await keyring.encrypt("platform", secret.encode(), f"mfa:{user_id}"),
        )
    )
    # Back to a free trial: the current subscription ends (kept as history), a new trial starts.
    await s.execute(
        update(t.Subscription)
        .where(
            t.Subscription.hotel_id == hotel_id,
            t.Subscription.status.notin_(("cancelled", "expired")),
        )
        .values(status="cancelled", ended_on=date.today(), cancelled_at=datetime.now(UTC))
    )
    await s.execute(
        insert(t.Subscription).values(
            hotel_id=hotel_id,
            plan_id=None,
            status="trial",
            starts_on=date.today(),
            trial_ends_on=date.today() + timedelta(days=14),
        )
    )
    return {"email": email, "password": password, "totp_secret": secret}


async def _published_plan(s) -> dict[str, str]:  # type: ignore[no-untyped-def]
    code = f"e2e_{secrets.token_hex(4)}"
    name = f"E2E Plan {code[4:]}"
    plan_id = (
        await s.execute(
            insert(t.Plan)
            .values(
                code=code,
                name=name,
                currency="ZAR",
                status="published",
                published_at=datetime.now(UTC),
                display_order=99,
                limits={"rooms": 500, "devices": 500, "staff": 500, "api_keys": 5},
                features={},
            )
            .returning(t.Plan.id)
        )
    ).scalar_one()
    await s.execute(
        text(
            "INSERT INTO app.plan_prices (plan_id, interval, amount_minor, currency, reason) "
            "VALUES (:p, 'month', 49900, 'ZAR', 'E2E price')"
        ),
        {"p": plan_id},
    )
    return {"code": code, "name": name}


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
