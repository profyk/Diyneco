"""Transactional outbox. Events are written in the same transaction as the change, with a
per-hotel `seq` taken from app.event_seq inside that transaction, and leave only after
commit (the worker drains them). Payloads carry ids and numbers only, never personal data."""

from __future__ import annotations

from typing import Any

from sqlalchemy import insert, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import TenantContext
from app.models.events import EventOutbox


async def emit(
    session: AsyncSession,
    ctx: TenantContext,
    event_type: str,
    channels: list[str],
    payload: dict[str, Any],
) -> int:
    """Queue one event and return its seq. The UPDATE row-locks the hotel's counter, so
    concurrent transactions of one hotel get consecutive numbers in commit order."""
    row = (
        await session.execute(
            text("UPDATE app.event_seq SET last_seq = last_seq + 1 WHERE hotel_id = :h RETURNING last_seq"),
            {"h": ctx.hotel_id},
        )
    ).first()
    if row is None:
        raise RuntimeError("event_seq row missing for hotel")
    seq = int(row[0])
    await session.execute(
        insert(EventOutbox).values(
            hotel_id=ctx.hotel_id, seq=seq, type=event_type, channels=channels, payload=payload
        )
    )
    return seq


def hotel_channel(hotel_id: object, suffix: str) -> str:
    return f"hotel:{hotel_id}:{suffix}"
