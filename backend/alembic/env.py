"""Alembic environment. Migrations run as diyneco_owner via MIGRATIONS_DATABASE_URL."""

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, pool, text

from alembic import context

sys.path.insert(0, str(Path(__file__).parent))  # makes alembic_helpers importable

config = context.config


def _url() -> str:
    url = os.environ.get("MIGRATIONS_DATABASE_URL")
    if not url:
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("MIGRATIONS_DATABASE_URL="):
                    url = line.split("=", 1)[1].split("#", 1)[0].strip().strip('"')
    if not url:
        raise SystemExit("MIGRATIONS_DATABASE_URL is not set")
    return url


def run_migrations_offline() -> None:
    context.configure(url=_url(), literal_binds=True, version_table_schema="public")
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        connection.execute(text("SET search_path = app, extensions, public"))
        connection.commit()
        context.configure(
            connection=connection,
            version_table_schema="public",
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
