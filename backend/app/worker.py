"""Background worker: drains the event outbox to the in-process bus and queues webhook
deliveries, delivers due webhooks, emails each hotel's daily close after 06:00 local time,
keeps monthly partitions ahead, and deletes expired idempotency keys and old published events.

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
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy import CursorResult, delete, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.crypto import LocalKms
from app.core.jwt import JwtKeys
from app.core.logging import configure_logging
from app.core.monitoring import init_monitoring
from app.core.state import Keyring
from app.db.session import Database, UnitOfWork, set_tenant
from app.integrations.storage import Storage, build_storage
from app.models.events import IdempotencyKey
from app.notifications.email import Mailer, build_email_provider
from app.realtime.bus import Event, EventBus
from app.services import daily_close_job, images, integrations, privacy, webhook_delivery
from app.services.admin import OWNER_EMAILS_SQL

log = logging.getLogger("diyneco.worker")

BATCH = 100
POLL_S = 0.5
MAINTENANCE_EVERY_S = 3600
JOBS_EVERY_S = 300
IMAGES_EVERY_S = 60


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
        await webhook_delivery.enqueue(s, ordered)
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
    keyring: Keyring | None = None
    mailer: Mailer | None = None
    http: httpx.AsyncClient | None = None
    storage: Storage | None = None
    assets_bucket: str = "hotel-assets"
    _stop: asyncio.Event = field(default_factory=asyncio.Event)

    def stop(self) -> None:
        self._stop.set()

    async def _decrypt(self, hotel_id: uuid.UUID, webhook_id: uuid.UUID, secret_enc: bytes) -> str:
        assert self.keyring is not None  # noqa: S101 - set in _main
        plain = await self.keyring.decrypt(str(hotel_id), secret_enc, integrations.secret_context(webhook_id))
        return plain.decode()

    async def _webhook_disabled(self, hotel_id: uuid.UUID, hook: Any) -> None:
        if self.mailer is None:
            return
        async with self.db.sessionmaker() as s:
            uow = UnitOfWork(session=s, sessionmaker=self.db.sessionmaker)
            async with s.begin():
                await set_tenant(s, hotel_id)
                for email in (await s.execute(OWNER_EMAILS_SQL, {"h": hotel_id})).scalars():
                    await self.mailer.queue(
                        uow,
                        hotel_id=hotel_id,
                        template="webhook_disabled",
                        to=str(email),
                        subject="A Diyneco webhook was turned off",
                        body=(
                            f"Deliveries to {hook.url} failed for 24 hours, so the webhook was turned off. "
                            "Fix the endpoint, then turn it back on in Settings > Integrations."
                        ),
                        subject_ref={"webhook_id": str(hook.id)},
                    )
            await uow.run_after_commit()

    async def run(self) -> None:
        last_maintenance = 0.0
        last_jobs = 0.0
        last_images = 0.0
        while not self._stop.is_set():
            try:
                if time.monotonic() - last_maintenance > MAINTENANCE_EVERY_S:
                    await maintenance(self.db.sessionmaker)
                    last_maintenance = time.monotonic()
                if self.mailer is not None and time.monotonic() - last_jobs > JOBS_EVERY_S:
                    await daily_close_job.send_daily_closes(self.db.sessionmaker, self.mailer)
                    await privacy.run_retention(self.db.sessionmaker)
                    last_jobs = time.monotonic()
                if self.storage is not None and time.monotonic() - last_images > IMAGES_EVERY_S:
                    await images.process_pending(self.db.sessionmaker, self.storage, self.assets_bucket)
                    last_images = time.monotonic()
                drained = await drain_once(self.db.sessionmaker, self.bus)
                if self.http is not None and self.keyring is not None:
                    await webhook_delivery.deliver_due(
                        self.db.sessionmaker, self.http, self._decrypt, notify_disabled=self._webhook_disabled
                    )
            except Exception:
                log.exception("worker iteration failed")
                drained = 0
            if drained == 0:
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(self._stop.wait(), timeout=POLL_S)


async def _main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_monitoring(settings, "worker")
    if not settings.worker_database_url:
        raise SystemExit("WORKER_DATABASE_URL is not set")
    db = Database(settings.worker_database_url, "diyneco-worker")
    kms = LocalKms(settings.kms_local_master_key or "", settings.kms_master_key_id)
    provider = build_email_provider(
        settings.email_provider,
        smtp_url=settings.email_smtp_url,
        key=settings.email_provider_key,
        echo=settings.is_development,
    )
    worker = Worker(
        db,
        keyring=Keyring(kms=kms, db=db),
        mailer=Mailer(provider=provider, sender=settings.email_from),
        http=httpx.AsyncClient(),
        storage=build_storage(
            settings,
            JwtKeys.from_config(
                settings.jwt_signing_keys_json, settings.jwt_active_kid, settings.api_base_url
            ),
        ),
        assets_bucket=settings.storage_bucket_assets,
    )
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
        if worker.http is not None:
            await worker.http.aclose()
        await worker.db.dispose()
        log.info("worker stopped")


if __name__ == "__main__":
    asyncio.run(_main())
