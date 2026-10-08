"""Outbox sequencing, the worker drain and maintenance, email delivery status, password hashing."""

from __future__ import annotations

import asyncio
import contextlib

from argon2 import PasswordHasher
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core import crypto
from app.db.session import TenantContext, set_tenant
from app.realtime.bus import Event, EventBus
from app.realtime.outbox import emit
from app.worker import drain_once, maintenance


def ctx_for(hotel_id) -> TenantContext:
    return TenantContext(hotel_id=hotel_id, actor_type="system", actor_id=None, actor_label="test")


async def test_seq_is_gapless_per_hotel_under_concurrency(factory, api_engine, owner_engine):
    a = await factory.hotel(roles=())
    b = await factory.hotel(roles=())
    maker = async_sessionmaker(api_engine)

    async def emit_one(hotel_id, n):
        async with maker() as s, s.begin():
            await set_tenant(s, hotel_id)
            return await emit(s, ctx_for(hotel_id), "TEST_EVENT", [f"hotel:{hotel_id}:ops"], {"n": n})

    seqs = await asyncio.gather(*[emit_one(h.id, n) for n in range(8) for h in (a, b)])
    async with owner_engine.connect() as conn:
        for hotel in (a, b):
            stored = (
                (
                    await conn.execute(
                        text("SELECT seq FROM app.event_outbox WHERE hotel_id = :h ORDER BY seq"),
                        {"h": hotel.id},
                    )
                )
                .scalars()
                .all()
            )
            assert stored == list(range(1, 9))
    assert sorted(seqs) == sorted(list(range(1, 9)) * 2)


async def test_worker_drains_in_order_and_marks_published(factory, api_engine, worker_engine, owner_engine):
    hotel = await factory.hotel(roles=())
    maker = async_sessionmaker(api_engine)
    async with maker() as s, s.begin():
        await set_tenant(s, hotel.id)
        for n in range(3):
            await emit(
                s, ctx_for(hotel.id), "ORDER_READY", [f"hotel:{hotel.id}:room-service"], {"order_number": n}
            )

    received: list[Event] = []
    bus = EventBus()

    async def collect(event: Event) -> None:
        received.append(event)

    bus.subscribe(collect)
    worker_maker = async_sessionmaker(worker_engine)
    total = 0
    while (n := await drain_once(worker_maker, bus, batch=500)) > 0:
        total += n
    mine = [e for e in received if e.hotel_id == str(hotel.id)]
    assert [e.seq for e in mine] == [1, 2, 3]
    assert [e.data["order_number"] for e in mine] == [0, 1, 2]
    assert mine[0].channels == [f"hotel:{hotel.id}:room-service"]
    async with owner_engine.connect() as conn:
        pending = (
            await conn.execute(
                text("SELECT count(*) FROM app.event_outbox WHERE hotel_id = :h AND published_at IS NULL"),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert pending == 0
    assert await drain_once(worker_maker, bus) == 0


async def test_failed_publish_is_retried(factory, api_engine, worker_engine):
    hotel = await factory.hotel(roles=())
    async with async_sessionmaker(api_engine)() as s, s.begin():
        await set_tenant(s, hotel.id)
        await emit(s, ctx_for(hotel.id), "ORDER_READY", ["x"], {})
    worker_maker = async_sessionmaker(worker_engine)
    while await drain_once(worker_maker, EventBus(), batch=500):
        pass  # clear anything left by other tests

    async with async_sessionmaker(api_engine)() as s, s.begin():
        await set_tenant(s, hotel.id)
        await emit(s, ctx_for(hotel.id), "ORDER_READY", ["x"], {"retry": True})
    failing = EventBus()

    async def boom(event: Event) -> None:
        raise RuntimeError("bus down")

    failing.subscribe(boom)
    with contextlib.suppress(RuntimeError):
        await drain_once(worker_maker, failing)
    ok = EventBus()
    got: list[Event] = []

    async def collect(event: Event) -> None:
        got.append(event)

    ok.subscribe(collect)
    assert await drain_once(worker_maker, ok) == 1
    assert got[0].data == {"retry": True}


async def test_worker_cannot_read_tenant_tables_directly(worker_engine):
    async with worker_engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM app.event_outbox"))).scalar_one() == 0
        assert (await conn.execute(text("SELECT count(*) FROM app.guests"))).scalar_one() == 0


async def test_maintenance_is_idempotent(worker_engine):
    maker = async_sessionmaker(worker_engine)
    first = await maintenance(maker)
    second = await maintenance(maker)
    assert second["partitions_created"] == 0
    assert set(first) == {"partitions_created", "outbox_purged", "idempotency_expired"}


async def test_emails_are_sent_after_commit_and_marked(client, factory, mailbox, owner_engine):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    before = len(mailbox.sent)
    await client.post("/auth/password/forgot", json={"email": user.email})
    assert len(mailbox.sent) == before + 1
    async with owner_engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT status, sent_at, provider_message_id FROM app.notifications "
                    "WHERE recipient = :e AND template = 'password_reset'"
                ),
                {"e": user.email},
            )
        ).one()
    assert row.status == "sent" and row.sent_at is not None and row.provider_message_id.startswith("console-")


async def test_rolled_back_request_sends_no_email(client, factory, mailbox):
    hotel = await factory.hotel(roles=("receptionist",))
    before = len(mailbox.sent)
    # Wrong token: the request fails, nothing is committed, nothing is sent.
    r = await client.post(
        "/auth/password/reset", json={"token": "x" * 43, "new_password": "Another-Password-1"}
    )
    assert r.status_code == 400
    assert len(mailbox.sent) == before
    assert hotel.id


def test_production_argon2_parameters():
    hasher = PasswordHasher(**crypto.ARGON2_PARAMS)
    encoded = hasher.hash("correct horse battery staple")
    assert encoded.startswith("$argon2id$v=19$m=65536,t=3,p=1$")
    assert crypto.ARGON2_PARAMS["salt_len"] == 16
