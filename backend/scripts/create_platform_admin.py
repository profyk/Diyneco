"""Creates the first Diyneco Super Admin in a new environment (DECISIONS D71, D75).

    uv run python scripts/create_platform_admin.py --email ops@diyneco.co.za --name "Ops Lead"

Run once per environment by whoever operates the database. The account starts as 'invited'
with no password: the script prints a one-time link (72 hours) to the Admin panel's
/accept-invite page, where the person chooses their password; two-step sign-in is set up at
their first sign-in. Further staff are invited from Admin > Diyneco staff. Refuses an email
that already has an account, so it can never turn a hotel account into a platform one.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.audit.writer import write_platform_audit
from app.core.config import get_settings
from app.models import tenancy as t
from app.services.auth import create_one_time_token
from app.services.platform_staff import INVITE_TTL


async def main(email: str, name: str) -> int:
    settings = get_settings()
    if not settings.migrations_database_url:
        print("MIGRATIONS_DATABASE_URL is not set.", file=sys.stderr)
        return 1
    url = settings.migrations_database_url.replace("postgresql+psycopg://", "postgresql+asyncpg://")
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": "app, extensions"}})
    async with async_sessionmaker(engine)() as s, s.begin():
        if (await s.execute(select(t.User.id).where(t.User.email == email))).first() is not None:
            print("That email already has an account; use another address.", file=sys.stderr)
            await engine.dispose()
            return 1
        user_id = (
            await s.execute(
                insert(t.User)
                .values(email=email, name=name, is_platform=True, status="invited")
                .returning(t.User.id)
            )
        ).scalar_one()
        role_id = (
            await s.execute(
                select(t.Role.id).where(t.Role.hotel_id.is_(None), t.Role.code == "platform_super_admin")
            )
        ).scalar_one()
        await s.execute(insert(t.PlatformUserRole).values(user_id=user_id, role_id=role_id))
        token = await create_one_time_token(s, user_id, "platform_invite", INVITE_TTL)
        await write_platform_audit(
            s,
            actor_type="system",
            actor_id=None,
            actor_label="create_platform_admin.py",
            action="platform.staff_invited",
            entity_type="user",
            entity_id=user_id,
            ip=None,
            request_id=None,
            new_value={
                "email": email,
                "roles": ["platform_super_admin"],
                "at": datetime.now(UTC).isoformat(),
            },
        )
    await engine.dispose()
    base = (settings.admin_app_url or "<Admin panel address>").rstrip("/")
    print(f"Super Admin {email} created. Send them this link (valid 72 hours, works once):")
    print(f"{base}/accept-invite?token={token}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.email.strip(), args.name.strip())))
