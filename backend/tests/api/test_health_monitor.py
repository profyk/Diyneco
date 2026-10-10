"""Platform health watch: HEALTH_DEGRADED when the event queue falls behind, then recovery."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.services.health_monitor import HealthMonitor, problems


def test_problem_rules():
    ok = {"pending_events": 3, "oldest_pending_seconds": 2.0, "failed_emails_hour": 0, "stuck_emails": 0}
    assert problems(ok) == {}
    bad = {"pending_events": 900, "oldest_pending_seconds": 400.0, "failed_emails_hour": 7, "stuck_emails": 2}
    assert set(problems(bad)) == {"event_queue_behind", "emails_failing", "emails_stuck"}


async def test_degraded_then_recovered_once(worker_engine, owner_engine, factory):
    hotel = await factory.hotel(rooms=0)
    maker = async_sessionmaker(worker_engine, expire_on_commit=False)
    async with owner_engine.begin() as conn:
        # Publish everything already queued, then add one event stuck for ten minutes.
        await conn.execute(
            text("UPDATE app.event_outbox SET published_at = now() WHERE published_at IS NULL")
        )
        await conn.execute(
            text(
                "INSERT INTO app.event_outbox (hotel_id, seq, type, channels, payload, created_at) "
                "VALUES (:h, NULL, 'TEST', ARRAY['x'], '{}', now() - interval '10 minutes')"
            ),
            {"h": hotel.id},
        )
    monitor = HealthMonitor()
    assert await monitor.check(maker) == "HEALTH_DEGRADED"
    assert await monitor.check(maker) is None  # unchanged: no repeat alert
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.event_outbox SET published_at = now() WHERE published_at IS NULL")
        )
    assert await monitor.check(maker) == "HEALTH_RECOVERED"
    async with owner_engine.connect() as conn:
        events = (
            await conn.execute(
                text(
                    "SELECT type, hotel_id, channels FROM app.event_outbox "
                    "WHERE type LIKE 'HEALTH_%' ORDER BY created_at DESC LIMIT 2"
                )
            )
        ).all()
    assert [e.type for e in events] == ["HEALTH_RECOVERED", "HEALTH_DEGRADED"]
    assert all(e.hotel_id is None and e.channels == ["platform"] for e in events)


async def test_only_health_events_can_be_emitted_without_a_hotel(worker_engine):
    import pytest
    from sqlalchemy.exc import DBAPIError

    async with worker_engine.connect() as conn:
        with pytest.raises(DBAPIError):
            await conn.execute(text("SELECT app.emit_platform_event('TENANT_APPROVED', '{}')"))
