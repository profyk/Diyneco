"""The order state machine and amount lock enforced by app.orders_guard_transition.

Every (from, to) pair of the 11 statuses is tried as diyneco_api: the 12 transitions in the
API spec's lifecycle succeed and write a status-history row; every other change fails with
SQLSTATE P0004."""

from __future__ import annotations

import itertools
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import as_hotel
from tests.db.test_financial_safeguards import sqlstate

STATUSES = [
    "PENDING_APPROVAL",
    "NEW",
    "ACCEPTED",
    "PREPARING",
    "READY",
    "ASSIGNED",
    "PICKED_UP",
    "DELIVERED",
    "CLOSED",
    "DECLINED",
    "CANCELLED",
]
ALLOWED = {
    ("PENDING_APPROVAL", "NEW"),
    ("PENDING_APPROVAL", "DECLINED"),
    ("NEW", "ACCEPTED"),
    ("NEW", "CANCELLED"),
    ("ACCEPTED", "PREPARING"),
    ("ACCEPTED", "CANCELLED"),
    ("PREPARING", "READY"),
    ("READY", "ASSIGNED"),
    ("ASSIGNED", "READY"),
    ("ASSIGNED", "PICKED_UP"),
    ("PICKED_UP", "DELIVERED"),
    ("DELIVERED", "CLOSED"),
    # Management may cancel until delivery (user decision, D67).
    ("PREPARING", "CANCELLED"),
    ("READY", "CANCELLED"),
    ("ASSIGNED", "CANCELLED"),
    ("PICKED_UP", "CANCELLED"),
}


@pytest.fixture
async def order_env(factory):
    hotel = await factory.hotel(roles=("kitchen_staff",))
    rows = await factory.stay_with_folio(hotel)
    return hotel, rows["stay_id"]


async def test_transition_matrix(order_env, factory, api_session):
    hotel, stay_id = order_env
    actor = hotel.users["kitchen_staff"].user_id
    orders = {status: [] for status in STATUSES}
    for f in STATUSES:
        for _ in STATUSES:
            orders[f].append(await factory.order(hotel, stay_id, status=f))
    await as_hotel(api_session, hotel.id)
    await api_session.execute(text("SELECT set_config('app.actor_user', :u, true)"), {"u": str(actor)})
    tried = 0
    for (f, t), order_id in zip(
        itertools.product(STATUSES, STATUSES),
        [o for status in STATUSES for o in orders[status]],
        strict=True,
    ):
        if f == t:
            continue
        stmt = text("UPDATE app.orders SET status = :t WHERE id = :id")
        if (f, t) in ALLOWED:
            async with api_session.begin_nested():
                await api_session.execute(stmt, {"t": t, "id": order_id})
            history = (
                await api_session.execute(
                    text(
                        "SELECT from_status, to_status, actor_user FROM app.order_status_history "
                        "WHERE order_id = :id"
                    ),
                    {"id": order_id},
                )
            ).one()
            assert (history.from_status, history.to_status, history.actor_user) == (f, t, actor)
        else:
            with pytest.raises(DBAPIError) as err:
                async with api_session.begin_nested():
                    await api_session.execute(stmt, {"t": t, "id": order_id})
            assert sqlstate(err.value) == "P0004", f"{f} -> {t} should be rejected"
        tried += 1
    assert tried == 11 * 10


@pytest.mark.parametrize("column", ["subtotal_minor", "fee_minor", "total_minor", "vat_minor"])
async def test_amounts_locked_after_acceptance(order_env, factory, api_session, column):
    hotel, stay_id = order_env
    order_id = await factory.order(hotel, stay_id, status="NEW")
    await as_hotel(api_session, hotel.id)
    await api_session.execute(
        text(
            "UPDATE app.orders SET status = 'ACCEPTED', locked_at = now(), accepted_at = now() WHERE id = :id"
        ),
        {"id": order_id},
    )
    # total = subtotal + fee must still hold, so move two columns together where needed.
    changes = {
        "subtotal_minor": "subtotal_minor = subtotal_minor - 100, total_minor = total_minor - 100",
        "fee_minor": "fee_minor = 0, total_minor = subtotal_minor",
        "total_minor": "subtotal_minor = subtotal_minor + 1, total_minor = total_minor + 1",
        "vat_minor": "vat_minor = vat_minor + 1",
    }[column]
    with pytest.raises(DBAPIError) as err:
        async with api_session.begin_nested():
            await api_session.execute(
                text(f"UPDATE app.orders SET {changes} WHERE id = :id"), {"id": order_id}
            )
    assert sqlstate(err.value) == "P0003"
    # Status can still move on.
    await api_session.execute(
        text("UPDATE app.orders SET status = 'PREPARING' WHERE id = :id"), {"id": order_id}
    )


async def test_amounts_can_change_before_lock(order_env, factory, api_session):
    hotel, stay_id = order_env
    order_id = await factory.order(hotel, stay_id, status="PENDING_APPROVAL")
    await as_hotel(api_session, hotel.id)
    await api_session.execute(
        text("UPDATE app.orders SET fee_minor = 0, total_minor = subtotal_minor WHERE id = :id"),
        {"id": order_id},
    )


async def test_cross_tenant_order_update_touches_nothing(order_env, factory, api_session):
    hotel, stay_id = order_env
    order_id = await factory.order(hotel, stay_id, status="NEW")
    other = await factory.hotel(roles=())
    await as_hotel(api_session, other.id)
    result = await api_session.execute(
        text("UPDATE app.orders SET status = 'ACCEPTED' WHERE id = :id"), {"id": order_id}
    )
    assert result.rowcount == 0
    assert uuid.UUID(str(order_id))
