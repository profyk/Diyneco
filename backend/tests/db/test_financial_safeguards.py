"""Append-only financial tables, closed folios, the payment tip rule, and partitions."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import as_hotel

FINANCIAL_TABLES = [
    "folio_entries", "payments", "payment_allocations", "tips",
    "invoices", "invoice_items", "audit_logs", "order_status_history",
]


def sqlstate(exc: DBAPIError) -> str | None:
    orig = exc.orig
    return getattr(orig, "sqlstate", None) or getattr(getattr(orig, "__cause__", None), "sqlstate", None)


@pytest.mark.parametrize("table", FINANCIAL_TABLES)
@pytest.mark.parametrize("statement", ["UPDATE app.{t} SET hotel_id = hotel_id", "DELETE FROM app.{t}",
                                       "TRUNCATE app.{t}"])
async def test_financial_tables_reject_update_delete_truncate_as_api(api_session, table, statement):
    with pytest.raises(DBAPIError) as err:
        await api_session.execute(text(statement.format(t=table)))
    assert sqlstate(err.value) == "42501"  # insufficient_privilege


async def test_append_only_trigger_blocks_even_the_owner(factory, owner_engine):
    hotel = await factory.hotel(roles=())
    rows = await factory.stay_with_folio(hotel)
    async with owner_engine.connect() as conn:
        tx = await conn.begin()
        with pytest.raises(DBAPIError) as err:
            await conn.execute(text("UPDATE app.folio_entries SET description = 'x' WHERE id = :id"),
                               {"id": rows["entry_id"]})
        assert sqlstate(err.value) == "P0001"
        await tx.rollback()
        tx = await conn.begin()
        with pytest.raises(DBAPIError) as err:
            await conn.execute(text("DELETE FROM app.folio_entries WHERE id = :id"), {"id": rows["entry_id"]})
        assert sqlstate(err.value) == "P0001"
        await tx.rollback()


async def test_every_financial_table_has_the_trigger(owner_engine):
    async with owner_engine.connect() as conn:
        names = set(
            (
                await conn.execute(
                    text("SELECT c.relname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
                         "JOIN pg_proc p ON p.oid = t.tgfoid WHERE p.proname = 'forbid_change' "
                         "AND NOT t.tgisinternal AND NOT c.relispartition")
                )
            ).scalars()
        )
    assert set(FINANCIAL_TABLES) <= names


async def test_closed_folio_rejects_new_entries(factory, api_session, owner_engine):
    hotel = await factory.hotel(roles=())
    rows = await factory.stay_with_folio(hotel)
    async with owner_engine.begin() as conn:
        await conn.execute(text("UPDATE app.folios SET status = 'closed', closed_at = now() WHERE id = :f"),
                           {"f": rows["folio_id"]})
    await as_hotel(api_session, hotel.id)
    with pytest.raises(DBAPIError) as err:
        await api_session.execute(
            text("INSERT INTO app.folio_entries (hotel_id, folio_id, entry_type, category_id, description, "
                 "unit_amount_minor, amount_minor, business_date) "
                 "VALUES (:h, :f, 'charge', :c, 'late', 100, 100, :d)"),
            {"h": hotel.id, "f": rows["folio_id"], "c": rows["food_category"], "d": date.today()},
        )
    assert sqlstate(err.value) == "P0002"


@pytest.mark.parametrize(
    ("due", "received", "tip", "ok"),
    [
        (300000, 400000, 100000, True),   # spec example: R3,000 due, R4,000 received, R1,000 tip
        (300000, 300000, 0, True),
        (300000, 250000, 0, True),        # underpayment: partial, no tip
        (300000, 400000, 0, False),       # overpayment recorded without its tip
        (300000, 400000, 50000, False),   # tip that is not the difference
        (300000, 250000, 1000, False),    # tip on an underpayment
    ],
)
async def test_payments_tip_must_equal_overpayment(factory, api_session, due, received, tip, ok):
    hotel = await factory.hotel(roles=())
    rows = await factory.stay_with_folio(hotel)
    await as_hotel(api_session, hotel.id)
    stmt = text(
        "INSERT INTO app.payments (hotel_id, folio_id, method, status, amount_due_minor, amount_received_minor, "
        "tip_amount_minor, provider_reference, idempotency_key) "
        "VALUES (:h, :f, 'card_terminal', 'paid', :due, :rec, :tip, '4F82C1', :k)"
    )
    params = {"h": hotel.id, "f": rows["folio_id"], "due": due, "rec": received, "tip": tip, "k": uuid.uuid4()}
    if ok:
        await api_session.execute(stmt, params)
    else:
        with pytest.raises(DBAPIError) as err:
            await api_session.execute(stmt, params)
        assert sqlstate(err.value) == "23514"  # check_violation


async def test_partitions_are_not_reachable_directly(api_session, owner_engine):
    async with owner_engine.connect() as conn:
        partitions = (
            await conn.execute(text("SELECT relname FROM pg_class WHERE relispartition AND relkind = 'r' "
                                    "AND relnamespace = 'app'::regnamespace"))
        ).scalars().all()
    assert partitions
    for name in partitions:
        with pytest.raises(DBAPIError) as err:
            async with api_session.begin_nested():
                await api_session.execute(text(f"SELECT 1 FROM app.{name} LIMIT 1"))
        assert sqlstate(err.value) == "42501"
