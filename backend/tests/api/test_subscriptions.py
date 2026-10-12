"""A hotel's subscription (DECISIONS D76): signup starts a plan-free trial with configurable
length and limits, quotes are computed on the server from published plans and Diyneco's tax
position, cancellation follows the status rules, and the billing contact belongs to its hotel.

Company settings are one shared row: tests that switch VAT on restore it."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import text

from tests.api.test_admin import platform, step_up
from tests.api.test_company import RESET
from tests.api.test_hotel_endpoints import signup_body
from tests.api.test_plans import draft_plan, price
from tests.api.test_room_service import idem


async def _publish(client, factory, admin, plan_id: str) -> None:
    out = await client.post(
        f"/admin/plans/{plan_id}/publish",
        json={"reason": "Go live"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert out.status_code == 200, out.text


async def _plan(client, factory, admin, **fields) -> dict:
    plan = await draft_plan(client, admin, **fields)
    assert (await price(client, factory, admin, plan["id"], "month", 49900)).status_code == 201
    assert (await price(client, factory, admin, plan["id"], "year", 499000)).status_code == 201
    await _publish(client, factory, admin, plan["id"])
    return plan


async def _vat(owner_engine, on: bool) -> None:
    async with owner_engine.begin() as conn:
        await conn.execute(text(RESET))
        if on:
            await conn.execute(
                text(
                    "UPDATE app.company_settings SET registration_number = '2026/123456/07', "
                    'registered_address = \'{"line1": "1 Long Street"}\', vat_registered = true, '
                    "vat_number = '4123456789', vat_effective_date = '2020-01-01'"
                )
            )


async def test_signup_starts_a_plan_free_trial_with_configured_limits(client, factory, owner_engine):
    body = signup_body()
    signed = await client.post("/signup", json=body, headers=idem())
    assert signed.status_code == 201, signed.text
    async with owner_engine.connect() as conn:
        sub = (
            await conn.execute(
                text(
                    "SELECT s.plan_id, s.status, s.starts_on, s.trial_ends_on FROM app.subscriptions s "
                    "JOIN app.hotel_users hu ON hu.hotel_id = s.hotel_id JOIN app.users u ON u.id = hu.user_id "
                    "WHERE u.email = :e"
                ),
                {"e": body["owner"]["email"]},
            )
        ).one()
        trial_days = (await conn.execute(text("SELECT trial_days FROM app.billing_settings"))).scalar_one()
    assert sub.plan_id is None and sub.status == "trial"
    assert sub.trial_ends_on - sub.starts_on == timedelta(days=trial_days)

    hotel = await factory.hotel(rooms=1)
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.subscriptions SET plan_id = NULL, status = 'trial' WHERE hotel_id = :h"),
            {"h": hotel.id},
        )
        limits = (await conn.execute(text("SELECT trial_limits FROM app.billing_settings"))).scalar_one()
    owner = await factory.auth(hotel, "hotel_owner")
    view = (await client.get("/subscription", headers=owner)).json()
    assert view["status"] == "trial" and view["plan"] is None and view["price"] is None
    assert view["usage"]["rooms"] == {"used": 1, "limit": limits["rooms"]}


async def test_quotes_are_computed_on_the_server(client, factory, owner_engine):
    admin = await platform(factory)
    plan = await _plan(client, factory, admin, setup_fee_minor=100000)
    hotel = await factory.hotel()
    owner = await factory.auth(hotel, "hotel_owner")
    try:
        await _vat(owner_engine, on=False)
        q = await client.post(
            "/subscription/quote", json={"plan_code": plan["code"], "interval": "year"}, headers=owner
        )
        assert q.status_code == 200, q.text
        q = q.json()
        assert [line["code"] for line in q["lines"]] == ["subscription", "setup_fee"]
        assert (q["subtotal_minor"], q["tax_minor"], q["total_minor"]) == (599000, 0, 599000)
        assert q["tax_charged"] is False and q["renews_at_minor"] == 499000
        today = date.fromisoformat(q["period_start"])
        assert date.fromisoformat(q["period_end"]).year == today.year + 1

        await _vat(owner_engine, on=True)
        q = (
            await client.post(
                "/subscription/quote", json={"plan_code": plan["code"], "interval": "month"}, headers=owner
            )
        ).json()
        # Prices exclude VAT: 499.00 + 15% = 573.85; setup 1,000.00 + 15% = 1,150.00.
        assert [line["total_minor"] for line in q["lines"]] == [57385, 115000]
        assert (q["subtotal_minor"], q["tax_minor"], q["total_minor"]) == (149900, 22485, 172385)
        assert (q["tax_name"], q["tax_rate_bp"]) == ("VAT", 1500)

        inclusive = await _plan(client, factory, admin, tax_treatment="inclusive")
        q = (
            await client.post(
                "/subscription/quote",
                json={"plan_code": inclusive["code"], "interval": "month"},
                headers=owner,
            )
        ).json()
        assert (q["total_minor"], q["tax_minor"]) == (49900, 6509)  # 499.00 includes 65.09 VAT
    finally:
        await _vat(owner_engine, on=False)

    draft = await draft_plan(client, admin)
    hidden = await client.post(
        "/subscription/quote", json={"plan_code": draft["code"], "interval": "month"}, headers=owner
    )
    assert hidden.json()["error"]["code"] == "NOT_FOUND"
    quarter = await client.post(
        "/subscription/quote", json={"plan_code": plan["code"], "interval": "quarter"}, headers=owner
    )
    assert quarter.json()["error"]["code"] == "NOT_FOUND"  # not offered quarterly
    sneaky = await client.post(
        "/subscription/quote",
        json={"plan_code": plan["code"], "interval": "month", "total_minor": 1},
        headers=owner,
    )
    assert sneaky.json()["error"]["code"] == "VALIDATION_FAILED"  # no client-sent amounts


async def test_promotions_and_introductory_prices(client, factory):
    admin = await platform(factory)
    plan = await draft_plan(
        client, admin, promo_discount_bp=2000, promo_ends_on=(date.today() + timedelta(days=10)).isoformat()
    )
    priced = await price(
        client,
        factory,
        admin,
        plan["id"],
        "month",
        99900,
        intro_amount={"amount_minor": 49900, "currency": "ZAR"},
        intro_periods=3,
    )
    assert priced.status_code == 201, priced.text
    await _publish(client, factory, admin, plan["id"])
    hotel = await factory.hotel()
    owner = await factory.auth(hotel, "hotel_owner")
    q = (
        await client.post(
            "/subscription/quote", json={"plan_code": plan["code"], "interval": "month"}, headers=owner
        )
    ).json()
    line = q["lines"][0]
    assert (line["amount_minor"], line["discount_minor"], line["total_minor"]) == (49900, 9980, 39920)
    assert q["intro_periods"] == 3 and q["renews_at_minor"] == 99900


async def test_cancelling_follows_the_status_rules(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("hotel_owner", "receptionist"))
    owner = await factory.auth(hotel, "hotel_owner")
    owner_su = await factory.step_up(hotel, "hotel_owner", owner)
    receptionist = await factory.auth(hotel, "receptionist")
    body = {"reason": "Moving to another system"}
    denied = await client.post("/subscription/cancel", json=body, headers={**receptionist, **idem()})
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
    no_step_up = await client.post("/subscription/cancel", json=body, headers={**owner, **idem()})
    assert no_step_up.json()["error"]["code"] == "STEP_UP_REQUIRED"

    # A paid subscription runs to the end of its period.
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE app.subscriptions SET status = 'active', interval = 'month', amount_minor = 49900, "
                "currency = 'ZAR', anchor_day = 1, tax_treatment = 'exclusive', renews_on = :r WHERE hotel_id = :h"
            ),
            {"h": hotel.id, "r": date.today() + timedelta(days=20)},
        )
    scheduled = await client.post("/subscription/cancel", json=body, headers={**owner_su, **idem()})
    assert scheduled.status_code == 200, scheduled.text
    assert scheduled.json()["status"] == "cancellation_scheduled" and scheduled.json()["cancel_at_period_end"]
    assert scheduled.json()["price"] == {"amount_minor": 49900, "currency": "ZAR"}
    resumed = await client.post("/subscription/resume", headers={**owner, **idem()})
    assert resumed.json()["status"] == "active"
    again = await client.post("/subscription/resume", headers={**owner, **idem()})
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"

    # A trial ends at once.
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.subscriptions SET status = 'trial' WHERE hotel_id = :h"), {"h": hotel.id}
        )
    ended = await client.post("/subscription/cancel", json=body, headers={**owner_su, **idem()})
    assert ended.json()["status"] is None  # no current subscription any more
    async with owner_engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT status, ended_on, cancel_reason FROM app.subscriptions WHERE hotel_id = :h"),
                {"h": hotel.id},
            )
        ).one()
        audit = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM app.audit_logs WHERE hotel_id = :h AND action = 'subscription.cancel'"
                ),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert row.status == "cancelled" and row.ended_on is not None and row.cancel_reason == body["reason"]
    assert audit == 2


async def test_the_billing_contact_belongs_to_its_hotel(client, factory):
    a = await factory.hotel()
    b = await factory.hotel()
    owner_a = await factory.auth(a, "hotel_owner")
    owner_b = await factory.auth(b, "hotel_owner")
    empty = (await client.get("/subscription/billing-contact", headers=owner_a)).json()
    assert empty["version"] == 0 and empty["legal_name"] is None
    body = {
        "version": 0,
        "legal_name": "Grand Example Hotel (Pty) Ltd",
        "vat_number": "4987654321",
        "billing_email": "accounts@grand.example.com",
        "address": {"line1": "2 Beach Road", "city": "Durban"},
    }
    saved = await client.put("/subscription/billing-contact", json=body, headers=owner_a)
    assert saved.status_code == 200, saved.text
    assert saved.json()["version"] == 1 and saved.json()["address"] == {
        "line1": "2 Beach Road",
        "city": "Durban",
    }
    stale = await client.put("/subscription/billing-contact", json=body, headers=owner_a)
    assert stale.json()["error"]["code"] == "PRECONDITION_FAILED"
    bad = await client.put(
        "/subscription/billing-contact", json={**body, "version": 1, "vat_number": "123"}, headers=owner_a
    )
    assert bad.json()["error"]["details"]["fields"][0]["field"] == "vat_number"
    # Another hotel sees only its own (empty) contact.
    assert (await client.get("/subscription/billing-contact", headers=owner_b)).json()["version"] == 0
