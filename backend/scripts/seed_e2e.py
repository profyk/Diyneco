"""Browser end-to-end test accounts (development only).

    uv run python scripts/seed_e2e.py > ../packages/e2e/.accounts.json

Creates a fresh Diyneco Super Admin with a confirmed two-step sign-in whose secret is printed,
so a browser test can sign in to the Admin panel on every run, and prints the demo hotel's
receptionist (from seed_dev.py) for the Merchant app. Refuses to run unless
APP_ENV=development. The output holds credentials for local demo accounts only.
"""

from __future__ import annotations

import asyncio
import json
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import insert, select

from app.core import crypto
from app.core.config import get_settings
from app.core.crypto import LocalKms
from app.core.state import Keyring
from app.db.session import Database
from app.models import tenancy as t
from app.services import mfa
from scripts.seed_dev import DEMO_PASSWORD, DEMO_PIN


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
    await db.dispose()
    print(
        json.dumps(
            {
                "admin": {"email": email, "password": password, "totp_secret": secret},
                "receptionist": {"email": "reception@grandexample.example", "password": DEMO_PASSWORD},
                "pin": DEMO_PIN,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
