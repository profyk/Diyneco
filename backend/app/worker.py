"""Background worker: drains the event outbox to the in-process bus, keeps monthly partitions
ahead, and deletes expired idempotency keys and old published events.

    uv run python -m app.worker

Runs as diyneco_worker (WORKER_DATABASE_URL). It has no BYPASSRLS; cross-hotel work goes
through the narrow SECURITY DEFINER functions app.outbox_claim, app.outbox_mark_published,
app.outbox_purge and app.ensure_partitions (DECISIONS G5, G14).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
import time
from dataclasses import dataclass, field

from sqlalchemy import CursorResult, delete, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.models.events import IdempotencyKey
from app.realtime.bus import Event, EventBus

log = logging.getLogger("diyneco.worker")

BATCH = 100
POLL_S = 0.5
MAINTENANCE_EVERY_S = 3600


async def drain_once(
    sessionmaker: async_sessionmaker[AsyncSession], bus: EventBus, batch: int = BATCH
) -> int:
    """Claim a batch, publish in (hotel, seq) order, mark published, all in one transaction.
    If publishing fails the transaction rolls back and the batch is retried."""
    async with sessionmaker() as s, s.begin():
        rows = (await s.execute(text("SELECT * FROM app.outbox_claim(:n)"), {"n": batch})).mappings().all()
        if not rows:
            return 0
        ordered = sorted(rows, key=lambda r: (str(r["hotel_id"]), r["seq"] or 0, r["created_at"]))
        for r in ordered:
            await bus.publish(
                Event(
                    event_id=str(r["id"]),
                    hotel_id=str(r["hotel_id"]) if r["hotel_id"] else None,
                    seq=r["seq"],
                    type=r["type"],
                    channels=list(r["channels"]),
                    occurred_at=r["created_at"],
                    data=dict(r["payload"]),
                )
            )
        await s.execute(text("SELECT app.outbox_mark_published(:ids)"), {"ids": [r["id"] for r in ordered]})
        return len(ordered)


async def maintenance(sessionmaker: async_sessionmaker[AsyncSession]) -> dict[str, int]:
    async with sessionmaker() as s, s.begin():
        created = (await s.execute(text("SELECT app.ensure_partitions(3)"))).scalar_one()
        purged = (await s.execute(text("SELECT app.outbox_purge(interval '7 days')"))).scalar_one()
        result_ = await s.execute(delete(IdempotencyKey).where(IdempotencyKey.expires_at < text("now()")))
        expired = result_.rowcount if isinstance(result_, CursorResult) else 0
    result = {
        "partitions_created": int(created),
        "outbox_purged": int(purged),
        "idempotency_expired": int(expired),
    }
    log.info("maintenance done", extra=result)
    return result


@dataclass
class Worker:
    db: Database
    bus: EventBus = field(default_factory=EventBus)
    _stop: asyncio.Event = field(default_factory=asyncio.Event)

    def stop(self) -> None:
        self._stop.set()

    async def run(self) -> None:
        last_maintenance = 0.0
        while not self._stop.is_set():
            try:
                if time.monotonic() - last_maintenance > MAINTENANCE_EVERY_S:
                    await maintenance(self.db.sessionmaker)
                    last_maintenance = time.monotonic()
                drained = await drain_once(self.db.sessionmaker, self.bus)
            except Exception:
                log.exception("worker iteration failed")
                drained = 0
            if drained == 0:
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(self._stop.wait(), timeout=POLL_S)


async def _main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    if not settings.worker_database_url:
        raise SystemExit("WORKER_DATABASE_URL is not set")
    worker = Worker(Database(settings.worker_database_url, "diyneco-worker"))
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, worker.stop)
        except NotImplementedError:  # Windows
            signal.signal(sig, lambda *_: worker.stop())
    log.info("worker started")
    try:
        await worker.run()
    finally:
        await worker.db.dispose()
        log.info("worker stopped")


if __name__ == "__main__":
    asyncio.run(_main())
