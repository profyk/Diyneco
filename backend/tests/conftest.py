"""Test harness.

- The test database is rebuilt from empty with the real migrations once per run.
- The app under test connects as diyneco_api, exactly like production; RLS applies.
- Fixtures seed data through an owner connection (BYPASSRLS), which tests never use to
  assert isolation.
- Argon2 cost is lowered for speed; production parameters are tested separately.

Requires TEST_DATABASE_URL, TEST_WORKER_DATABASE_URL and TEST_MIGRATIONS_DATABASE_URL
(read from the environment or backend/.env).
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core import crypto
from app.core.config import Settings
from app.main import build_state, create_app
from app.notifications.email import ConsoleEmailProvider
from tests.factories import Factory

BACKEND = Path(__file__).resolve().parent.parent


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        env_file = BACKEND / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith(f"{name}="):
                    value = line.split("=", 1)[1].strip().strip("'\"")
    if not value:
        pytest.exit(f"{name} is not set; see backend/README or .env.example", returncode=2)
    return value


TEST_DATABASE_URL = _env("TEST_DATABASE_URL")
TEST_WORKER_DATABASE_URL = _env("TEST_WORKER_DATABASE_URL")
TEST_MIGRATIONS_DATABASE_URL = _env("TEST_MIGRATIONS_DATABASE_URL")
OWNER_ASYNC_URL = TEST_MIGRATIONS_DATABASE_URL.replace("postgresql+psycopg://", "postgresql+asyncpg://")


def _rebuild_schema() -> None:
    import psycopg

    dsn = TEST_MIGRATIONS_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("DROP SCHEMA IF EXISTS app CASCADE")
        conn.execute("DROP TABLE IF EXISTS public.alembic_version")
    env = {**os.environ, "MIGRATIONS_DATABASE_URL": TEST_MIGRATIONS_DATABASE_URL}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.exit(f"alembic upgrade failed:\n{result.stderr}", returncode=3)


def pytest_sessionstart(session: pytest.Session) -> None:
    _rebuild_schema()
    crypto.set_hash_params(time_cost=1, memory_cost=1024)


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        app_env="development",
        api_base_url="http://testserver",
        cors_allowed_origins=["http://localhost:3001"],  # type: ignore[arg-type]
        database_url=TEST_DATABASE_URL,
        worker_database_url=TEST_WORKER_DATABASE_URL,
        migrations_database_url=TEST_MIGRATIONS_DATABASE_URL,
        redis_url=None,
        jwt_signing_keys_json=_env("JWT_SIGNING_KEYS_JSON"),
        jwt_active_kid=_env("JWT_ACTIVE_KID"),
        pairing_code_pepper=_env("PAIRING_CODE_PEPPER"),
        kms_master_key_id="local-test",
        kms_provider="local",
        kms_local_master_key=_env("KMS_LOCAL_MASTER_KEY"),
        email_provider="console",
        log_level="warning",
    )


@pytest.fixture(scope="session")
def mailbox() -> ConsoleEmailProvider:
    return ConsoleEmailProvider(echo=False)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def app_state(settings: Settings, mailbox: ConsoleEmailProvider):  # type: ignore[no-untyped-def]
    state = build_state(settings, email_provider=mailbox)
    yield state
    await state.db.dispose()


@pytest.fixture(scope="session")
def app(settings: Settings, app_state):  # type: ignore[no-untyped-def]
    return create_app(settings, state=app_state)


@pytest_asyncio.fixture(loop_scope="session")
async def client(app, app_state) -> AsyncIterator[httpx.AsyncClient]:  # type: ignore[no-untyped-def]
    await app_state.limiter.reset()
    # Like a real server: an unhandled error becomes the 500 envelope, not a test-side exception.
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver/api/v1") as c:
        yield c


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def owner_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        OWNER_ASYNC_URL, connect_args={"server_settings": {"search_path": "app, extensions"}}
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def api_engine() -> AsyncIterator[AsyncEngine]:
    """Raw connection as diyneco_api, for database-level isolation tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL, connect_args={"server_settings": {"search_path": "app, extensions"}}
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def worker_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        TEST_WORKER_DATABASE_URL, connect_args={"server_settings": {"search_path": "app, extensions"}}
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def factory(owner_engine: AsyncEngine, app_state) -> Factory:  # type: ignore[no-untyped-def]
    return Factory(async_sessionmaker(owner_engine, expire_on_commit=False), app_state)


@pytest_asyncio.fixture(loop_scope="session")
async def api_session(api_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """A diyneco_api session inside a transaction that is always rolled back."""
    async with async_sessionmaker(api_engine)() as s:
        await s.begin()
        try:
            yield s
        finally:
            await s.rollback()


async def as_hotel(session: AsyncSession, hotel_id: object | None) -> None:
    await session.execute(
        text("SELECT set_config('app.hotel_id', :h, true)"), {"h": str(hotel_id) if hotel_id else ""}
    )
