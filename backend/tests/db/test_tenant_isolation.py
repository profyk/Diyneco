"""Tenant isolation at the database layer, connected as diyneco_api (no BYPASSRLS)."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import as_hotel
from tests.db.test_financial_safeguards import sqlstate


async def tenant_tables(owner_engine) -> list[tuple[str, str]]:
    """(table, tenant column) for every app table the migration check treats as tenant data."""
    async with owner_engine.connect() as conn:
        rows = (
            (
                await conn.execute(
                    text(
                        "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                        "WHERE n.nspname = 'app' AND c.relkind IN ('r','p') AND NOT c.relispartition "
                        "AND EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid "
                        "AND a.attname = 'hotel_id' AND NOT a.attisdropped) ORDER BY 1"
                    )
                )
            )
            .scalars()
            .all()
        )
    return [("hotels", "id"), *[(r, "hotel_id") for r in rows]]


@pytest.fixture
async def two_hotels(factory, client):
    a = await factory.hotel()
    b = await factory.hotel()
    for h in (a, b):
        rows = await factory.stay_with_folio(h)
        await factory.order(h, rows["stay_id"])
        # Produce audit, outbox and idempotency rows through the API.
        headers = await factory.auth(h, "general_manager")
        r = await client.get("/hotel", headers=headers)
        etag = r.headers["ETag"]
        r = await client.patch(
            "/hotel", json={"phone": "+27 21 555 0100"}, headers={**headers, "If-Match": etag}
        )
        assert r.status_code == 200, r.text
    return a, b


async def test_no_hotel_context_sees_zero_rows_in_every_tenant_table(two_hotels, api_session, owner_engine):
    await as_hotel(api_session, None)
    populated = 0
    for table, column in await tenant_tables(owner_engine):
        # roles, charge_categories and feature_flags share system rows (hotel_id NULL) by design.
        count = (
            await api_session.execute(text(f"SELECT count(*) FROM app.{table} WHERE {column} IS NOT NULL"))
        ).scalar_one()
        assert count == 0, f"app.{table} leaked {count} hotel rows without a hotel context"
        async with owner_engine.connect() as conn:
            populated += bool((await conn.execute(text(f"SELECT count(*) FROM app.{table}"))).scalar_one())
    assert populated >= 15  # the check above ran against real data, not empty tables


async def test_hotel_a_cannot_see_hotel_b_rows_in_any_table(two_hotels, api_session, owner_engine):
    a, b = two_hotels
    await as_hotel(api_session, a.id)
    for table, column in await tenant_tables(owner_engine):
        leaked = (
            await api_session.execute(
                text(f"SELECT count(*) FROM app.{table} WHERE {column} = :b"), {"b": b.id}
            )
        ).scalar_one()
        assert leaked == 0, f"app.{table}: hotel A sees {leaked} rows of hotel B"
        foreign = (
            await api_session.execute(
                text(f"SELECT count(*) FROM app.{table} WHERE {column} IS DISTINCT FROM :a"), {"a": a.id}
            )
        ).scalar_one()
        if table not in ("roles", "charge_categories", "feature_flags"):  # system rows are shared
            assert foreign == 0, f"app.{table}: hotel A sees rows of other hotels"


@pytest.mark.parametrize(
    ("table", "columns"),
    [
        ("guests", "(hotel_id, full_name) VALUES (:b, 'Intruder')"),
        ("kitchen_stations", "(hotel_id, name) VALUES (:b, 'Intruder bar')"),
        (
            "audit_logs",
            "(hotel_id, actor_type, actor_label, action, entity_type) VALUES (:b, 'system', 'x', 'x', 'x')",
        ),
        ("event_outbox", "(hotel_id, type, channels, payload) VALUES (:b, 'X', '{}', '{}')"),
        ("hotel_settings", "(hotel_id, invoice_prefix) VALUES (:b, 'X')"),
    ],
)
async def test_hotel_a_cannot_insert_rows_for_hotel_b(factory, api_session, table, columns):
    a = await factory.hotel(roles=())
    b_id = uuid.uuid4()
    await as_hotel(api_session, a.id)
    with pytest.raises(DBAPIError) as err:
        await api_session.execute(text(f"INSERT INTO app.{table} {columns}"), {"b": b_id})
    assert sqlstate(err.value) in ("42501", "23503")  # RLS WITH CHECK (or FK when B does not exist)


async def test_hotel_a_cannot_insert_for_existing_hotel_b(factory, api_session):
    a = await factory.hotel(roles=())
    b = await factory.hotel(roles=())
    await as_hotel(api_session, a.id)
    with pytest.raises(DBAPIError) as err:
        await api_session.execute(
            text("INSERT INTO app.guests (hotel_id, full_name) VALUES (:b, 'x')"), {"b": b.id}
        )
    assert sqlstate(err.value) == "42501"


async def test_hotel_a_cannot_update_hotel_b_rows(factory, api_session):
    a = await factory.hotel(roles=())
    b = await factory.hotel(roles=())
    await as_hotel(api_session, a.id)
    result = await api_session.execute(
        text("UPDATE app.rooms SET floor = 'x' WHERE hotel_id = :b"), {"b": b.id}
    )
    assert result.rowcount == 0


# --- Composite foreign keys: a row in hotel A can never point at a parent in hotel B --------


async def test_composite_fk_blocks_cross_hotel_parent(factory, owner_engine):
    a = await factory.hotel(roles=())
    b = await factory.hotel(roles=())
    b_rows = await factory.stay_with_folio(b)
    cases = [
        (
            "INSERT INTO app.stays (hotel_id, room_id, guest_id, arrival_date, departure_date, nightly_rate_minor) "
            "VALUES (:a, :b_room, :b_guest, :d1, :d2, 1000)"
        ),
        (
            "INSERT INTO app.folio_entries (hotel_id, folio_id, entry_type, category_id, description, "
            "unit_amount_minor, amount_minor, business_date) VALUES (:a, :b_folio, 'charge', :cat, 'x', 1, 1, :d1)"
        ),
        "INSERT INTO app.devices (hotel_id, label, kind, room_id) VALUES (:a, 'X-1', 'guest', :b_room)",
        "INSERT INTO app.rooms (hotel_id, room_type_id, number) VALUES (:a, :b_room_type, '999')",
    ]
    params = {
        "a": a.id,
        "b_room": b.room_ids[1],
        "b_guest": b_rows["guest_id"],
        "b_folio": b_rows["folio_id"],
        "b_room_type": b.room_type_id,
        "cat": b_rows["food_category"],
        "d1": date.today(),
        "d2": date.today() + timedelta(days=1),
    }
    for sql in cases:
        async with owner_engine.connect() as conn:  # owner bypasses RLS: only the FK can stop it
            tx = await conn.begin()
            with pytest.raises(DBAPIError) as err:
                await conn.execute(text(sql), params)
            assert sqlstate(err.value) == "23503", sql
            await tx.rollback()


async def test_user_role_must_be_system_or_same_hotel(factory, owner_engine):
    a = await factory.hotel(roles=("receptionist",))
    b = await factory.hotel(roles=())
    async with owner_engine.begin() as conn:
        b_role = (
            await conn.execute(
                text(
                    "INSERT INTO app.roles (hotel_id, code, name) VALUES (:b, 'custom', 'Custom') "
                    "RETURNING id"
                ),
                {"b": b.id},
            )
        ).scalar_one()
    async with owner_engine.connect() as conn:
        tx = await conn.begin()
        with pytest.raises(DBAPIError) as err:
            await conn.execute(
                text("INSERT INTO app.user_roles (hotel_id, hotel_user_id, role_id) VALUES (:a, :hu, :r)"),
                {"a": a.id, "hu": a.users["receptionist"].hotel_user_id, "r": b_role},
            )
        assert sqlstate(err.value) == "23503"
        await tx.rollback()


async def test_folio_balances_view_respects_rls(factory, api_session):
    a = await factory.hotel(roles=())
    b = await factory.hotel(roles=())
    await factory.stay_with_folio(a)
    b_rows = await factory.stay_with_folio(b)
    await as_hotel(api_session, a.id)
    rows = (await api_session.execute(text("SELECT hotel_id, balance_minor FROM app.folio_balances"))).all()
    assert rows and all(r.hotel_id == a.id for r in rows)
    leaked = (
        await api_session.execute(
            text("SELECT count(*) FROM app.folio_balances WHERE folio_id = :f"), {"f": b_rows["folio_id"]}
        )
    ).scalar_one()
    assert leaked == 0
    assert rows[0].balance_minor == 15000


# --- Partial unique indexes ----------------------------------------------------------------


async def test_one_live_stay_per_room(factory, api_session):
    hotel = await factory.hotel(roles=())
    first = await factory.stay_with_folio(hotel, status="active")
    await as_hotel(api_session, hotel.id)
    insert = text(
        "INSERT INTO app.stays (hotel_id, room_id, guest_id, status, arrival_date, departure_date, "
        "nightly_rate_minor) VALUES (:h, :r, :g, :st, :d1, :d2, 1000)"
    )
    params = {
        "h": hotel.id,
        "r": hotel.room_ids[0],
        "g": first["guest_id"],
        "d1": date.today(),
        "d2": date.today() + timedelta(days=1),
    }
    for live in ("checked_in", "active", "checkout_pending"):
        with pytest.raises(DBAPIError) as err:
            async with api_session.begin_nested():
                await api_session.execute(insert, {**params, "st": live})
        assert sqlstate(err.value) == "23505"
    for not_live in ("reserved", "checked_out", "cancelled"):
        async with api_session.begin_nested():
            await api_session.execute(insert, {**params, "st": not_live})


async def test_one_guest_tablet_per_room(factory, api_session):
    hotel = await factory.hotel(roles=())
    await as_hotel(api_session, hotel.id)
    insert = text(
        "INSERT INTO app.devices (hotel_id, label, kind, room_id, status) VALUES (:h, :l, 'guest', :r, :s)"
    )
    await api_session.execute(
        insert, {"h": hotel.id, "l": "DY-101-01", "r": hotel.room_ids[0], "s": "active"}
    )
    with pytest.raises(DBAPIError) as err:
        async with api_session.begin_nested():
            await api_session.execute(
                insert, {"h": hotel.id, "l": "DY-101-02", "r": hotel.room_ids[0], "s": "locked"}
            )
    assert sqlstate(err.value) == "23505"
    # A revoked tablet does not count; another room is fine.
    await api_session.execute(
        insert, {"h": hotel.id, "l": "DY-101-03", "r": hotel.room_ids[0], "s": "revoked"}
    )
    await api_session.execute(
        insert, {"h": hotel.id, "l": "DY-102-01", "r": hotel.room_ids[1], "s": "active"}
    )


# --- Definer functions and helpers -----------------------------------------------------------


async def test_redeem_pairing_is_single_use_and_tenant_free(factory, api_session, owner_engine):
    hotel = await factory.hotel(roles=("hotel_admin",))
    code_hash = uuid.uuid4().bytes
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO app.device_pairings (hotel_id, kind, room_id, code_hash, created_by, expires_at) "
                "VALUES (:h, 'guest', :r, :c, :u, now() + interval '15 minutes')"
            ),
            {"h": hotel.id, "r": hotel.room_ids[0], "c": code_hash, "u": hotel.users["hotel_admin"].user_id},
        )
    await as_hotel(api_session, None)  # pairing runs before any hotel is known
    first = (await api_session.execute(text("SELECT * FROM app.redeem_pairing(:c)"), {"c": code_hash})).all()
    second = (await api_session.execute(text("SELECT * FROM app.redeem_pairing(:c)"), {"c": code_hash})).all()
    assert len(first) == 1 and first[0].hotel_id == hotel.id
    assert second == []


async def test_uuid_v7_is_version_7_and_time_ordered(api_session):
    ids = [(await api_session.execute(text("SELECT app.uuid_v7()"))).scalar_one() for _ in range(20)]
    assert all(u.version == 7 for u in ids)
    assert all(u.variant == uuid.RFC_4122 for u in ids)
    stamps = [int.from_bytes(u.bytes[:6]) for u in ids]
    assert stamps == sorted(stamps)
