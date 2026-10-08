"""Engine, one transaction per request, and the tenant context.

The API connects as diyneco_api (no BYPASSRLS). Each request runs in one transaction; once the
principal is known, `app.hotel_id`, `app.actor_user` and `app.actor_device` are set with
set_config(..., is_local => true), the parameterisable form of SET LOCAL, so they vanish at
commit or rollback and can never leak to the next request on a pooled connection.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

log = logging.getLogger("diyneco.db")


@dataclass(frozen=True)
class TenantContext:
    """Who is acting, for which hotel. Every repository method takes one; there is no
    unscoped query helper. Built only from an authenticated principal (or, for the few
    pre-tenant flows such as signup and invitation acceptance, by the service that just
    established the hotel)."""

    hotel_id: uuid.UUID
    actor_type: str  # user | device | api_key | system | platform
    actor_id: uuid.UUID | None
    actor_label: str
    device_id: uuid.UUID | None = None
    ip: str | None = None
    request_id: str | None = None


def make_engine(url: str, application_name: str) -> AsyncEngine:
    return create_async_engine(
        url,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={
            "server_settings": {
                "search_path": "app, extensions",
                "application_name": application_name,
            }
        },
    )


async def set_tenant(
    session: AsyncSession,
    hotel_id: uuid.UUID | None,
    actor_user: uuid.UUID | None = None,
    actor_device: uuid.UUID | None = None,
) -> None:
    await session.execute(
        text(
            "SELECT set_config('app.hotel_id', :h, true), "
            "set_config('app.actor_user', :u, true), "
            "set_config('app.actor_device', :d, true)"
        ),
        {
            "h": str(hotel_id) if hotel_id else "",
            "u": str(actor_user) if actor_user else "",
            "d": str(actor_device) if actor_device else "",
        },
    )


@dataclass
class UnitOfWork:
    """The request's session plus work to run only after a successful commit (emails,
    in-process event fan-out). Nothing irreversible happens before commit."""

    session: AsyncSession
    sessionmaker: async_sessionmaker[AsyncSession]
    _after_commit: list[Callable[[], Awaitable[None]]] = field(default_factory=list)

    def after_commit(self, fn: Callable[[], Awaitable[None]]) -> None:
        self._after_commit.append(fn)

    async def run_after_commit(self) -> None:
        for fn in self._after_commit:
            try:
                await fn()
            except Exception:
                log.exception("after-commit task failed")


class Database:
    def __init__(self, url: str, application_name: str) -> None:
        self.engine = make_engine(url, application_name)
        self.sessionmaker = async_sessionmaker(self.engine, expire_on_commit=False, autoflush=False)

    async def dispose(self) -> None:
        await self.engine.dispose()
