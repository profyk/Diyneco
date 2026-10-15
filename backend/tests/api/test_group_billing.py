"""Owners paying for several properties at once, and the group discount (DECISIONS D89).

Every property keeps its own invoice and receives its own payment; one sandbox checkout
settles them all, oldest first, never beyond what an invoice still owes."""

from __future__ import annotations

import uuid

from sqlalchemy import text

from tests.api.test_admin import platform
from tests.api.test_room_service import idem
from tests.api.test_sub_payments import _pay_sandbox, _subscribe, _trial_hotel
from tests.api.test_subscriptions import _plan
from tests.factories import SeededHotel, SeededUser

NEW_HOTEL = {
    "hotel": {
        "name": "Second Lodge",
        "country": "ZA",
        "address": {"line1": "2 Main Road", "city": "Knysna", "province_code": "ZA-WC"},
    }
}


async def _second_property(client, factory, owner_engine, hotel: SeededHotel) -> SeededHotel:
    """The owner of `hotel` adds another property; it is approved so it can subscribe."""
    owner = hotel.users["hotel_owner"]
    headers = await factory.step_up(hotel, "hotel_owner", await factory.auth(hotel, "hotel_owner"))
    r = await client.post("/hotels", json=NEW_HOTEL, headers={**headers, **idem()})
    assert r.status_code == 201, r.text
    hotel_id = uuid.UUID(r.json()["hotel_id"])
    async with owner_engine.begin() as conn:
        await conn.execute(text("UPDATE app.hotels SET status = 'active' WHERE id = :h"), {"h": hotel_id})
        hu = (
            await conn.execute(
                text("SELECT id FROM app.hotel_users WHERE hotel_id = :h AND user_id = :u"),
                {"h": hotel_id, "u": owner.user_id},
            )
        ).scalar_one()
        await conn.execute(
            text(
                "UPDATE app.hotel_users SET pin_hash = (SELECT pin_hash FROM app.hotel_users WHERE id = :o) WHERE id = :n"
            ),
            {"o": owner.hotel_user_id, "n": hu},
        )
    me = SeededUser(
        "hotel_owner", owner.email, owner.password, owner.user_id, hu, owner.name, owner.totp_secret
    )
    return SeededHotel(id=hotel_id, name="Second Lodge", users={"hotel_owner": me})


async def _two_open_invoices(client, factory, owner_engine):
    admin = await platform(factory)
    plan = await _plan(client, factory, admin)
    first = await _trial_hotel(factory, owner_engine, roles=("hotel_owner",))
    second = await _second_property(client, factory, owner_engine, first)
    a = await _subscribe(client, factory, first, plan["code"])
    b = await _subscribe(client, factory, second, plan["code"])
    return first, second, a["invoice"], b["invoice"]


async def test_one_payment_settles_every_propertys_own_invoice(client, factory, owner_engine):
    first, second, inv_a, inv_b = await _two_open_invoices(client, factory, owner_engine)
    owner = await factory.auth(first, "hotel_owner")

    statement = (await client.get("/portfolio/billing", headers=owner)).json()
    numbers = {i["number"] for i in statement["invoices"]}
    assert {inv_a["number"], inv_b["number"]} <= numbers
    due = statement["due"][0]
    assert due["currency"] == inv_a["total"]["currency"]

    start = await client.post(
        "/portfolio/payments", json={"currency": due["currency"]}, headers={**owner, **idem()}
    )
    assert start.status_code == 201, start.text
    group = start.json()
    assert group["invoices"] >= 2 and group["status"] == "pending" and group["test_mode"]
    assert group["amount"]["amount_minor"] == due["amount_minor"]

    # Another owner sees nothing of it.
    stranger = await factory.hotel(roles=("hotel_owner",))
    assert (
        await client.get(
            f"/portfolio/payments/{group['id']}", headers=await factory.auth(stranger, "hotel_owner")
        )
    ).status_code == 404

    done = await client.post(
        f"/portfolio/payments/{group['id']}/sandbox",
        json={"outcome": "succeeded"},
        headers={**owner, **idem()},
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "succeeded" and done.json()["unallocated"]["amount_minor"] == 0

    async with owner_engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT i.number, i.status, p.hotel_id, p.amount_minor, p.provider_payment_id "
                    "FROM app.subscription_invoices i JOIN app.subscription_payments p ON p.invoice_id = i.id "
                    "WHERE i.number IN (:a, :b)"
                ),
                {"a": inv_a["number"], "b": inv_b["number"]},
            )
        ).all()
    assert {r.number for r in rows} == {inv_a["number"], inv_b["number"]}
    assert all(r.status == "paid" for r in rows)
    assert {r.hotel_id for r in rows} == {first.id, second.id}  # each hotel received its own payment
    assert all(r.provider_payment_id.startswith(f"sbx_grp_{group['id']}:") for r in rows)


async def test_an_invoice_paid_meanwhile_is_not_paid_twice(client, factory, owner_engine):
    first, second, inv_a, inv_b = await _two_open_invoices(client, factory, owner_engine)
    owner = await factory.auth(first, "hotel_owner")
    currency = inv_a["total"]["currency"]
    group = (
        await client.post("/portfolio/payments", json={"currency": currency}, headers={**owner, **idem()})
    ).json()

    await _pay_sandbox(client, factory, second, inv_b["id"])  # paid on its own before the group completes

    done = (
        await client.post(
            f"/portfolio/payments/{group['id']}/sandbox",
            json={"outcome": "succeeded"},
            headers={**owner, **idem()},
        )
    ).json()
    assert done["status"] == "succeeded"
    assert (
        done["unallocated"]["amount_minor"] == inv_b["total"]["amount_minor"]
    )  # kept for a refund, never applied twice
    async with owner_engine.connect() as conn:
        paid_b = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM app.subscription_payments p JOIN app.subscription_invoices i ON i.id = p.invoice_id WHERE i.number = :n"
                ),
                {"n": inv_b["number"]},
            )
        ).scalar_one()
    assert paid_b == 1


async def test_a_failed_group_checkout_leaves_every_invoice_open(client, factory, owner_engine):
    first, _second, inv_a, _inv_b = await _two_open_invoices(client, factory, owner_engine)
    owner = await factory.auth(first, "hotel_owner")
    group = (
        await client.post(
            "/portfolio/payments", json={"currency": inv_a["total"]["currency"]}, headers={**owner, **idem()}
        )
    ).json()
    done = (
        await client.post(
            f"/portfolio/payments/{group['id']}/sandbox",
            json={"outcome": "failed"},
            headers={**owner, **idem()},
        )
    ).json()
    assert done["status"] == "failed"
    statement = (await client.get("/portfolio/billing", headers=owner)).json()
    assert inv_a["number"] in {i["number"] for i in statement["invoices"]}


async def test_the_group_discount_applies_from_the_set_number_of_properties(client, factory, owner_engine):
    admin = await platform(factory)
    plan = await _plan(client, factory, admin)
    first = await _trial_hotel(factory, owner_engine, roles=("hotel_owner",))
    second = await _second_property(client, factory, owner_engine, first)
    a = await _subscribe(client, factory, first, plan["code"])
    await _pay_sandbox(client, factory, first, a["invoice"]["id"])
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE app.billing_settings SET group_discount_bp = 1000, group_discount_min_properties = 2"
            )
        )
    try:
        quote = await client.post(
            "/subscription/quote",
            json={"plan_code": plan["code"], "interval": "month"},
            headers=await factory.auth(second, "hotel_owner"),
        )
        assert quote.status_code == 200, quote.text
        q = quote.json()
        assert q["group_discount_bp"] == 1000
        line = next(x for x in q["lines"] if x["code"] == "subscription")
        assert line["discount_minor"] == line["amount_minor"] // 10
        # A lone hotel gets none.
        lone = await _trial_hotel(factory, owner_engine, roles=("hotel_owner",))
        alone = (
            await client.post(
                "/subscription/quote",
                json={"plan_code": plan["code"], "interval": "month"},
                headers=await factory.auth(lone, "hotel_owner"),
            )
        ).json()
        assert alone["group_discount_bp"] == 0
    finally:
        async with owner_engine.begin() as conn:
            await conn.execute(
                text(
                    "UPDATE app.billing_settings SET group_discount_bp = 0, group_discount_min_properties = 3"
                )
            )
