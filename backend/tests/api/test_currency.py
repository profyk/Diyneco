"""Currencies are chosen, never assumed (DECISIONS D57): each hotel picks its operating currency,
each plan its billing currency, and the database has no default to fall back on."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.api.test_admin import platform
from tests.api.test_billing import walk_in
from tests.api.test_hotel_endpoints import signup_body
from tests.api.test_room_service import idem


async def settings_headers(client, factory, hotel) -> dict[str, str]:
    owner = await factory.step_up(hotel, "hotel_owner", await factory.auth(hotel, "hotel_owner"))
    etag = (await client.get("/hotel/settings", headers=owner)).headers["ETag"]
    return {**owner, "If-Match": etag}


async def test_currency_catalogue_is_public(client):
    data = (await client.get("/currencies")).json()["data"]
    codes = {c["code"] for c in data}
    assert {"ZAR", "USD", "EUR", "BWP", "NAD", "KES"} <= codes
    assert next(c for c in data if c["code"] == "EUR")["symbol"] == "€"


async def test_signup_needs_a_supported_currency(client):
    body = signup_body()
    body["hotel"].pop("currency")
    assert (await client.post("/signup", json=body, headers=idem())).json()["error"][
        "code"
    ] == "VALIDATION_FAILED"
    body["hotel"]["currency"] = "XYZ"
    r = await client.post("/signup", json=body, headers=idem())
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"


async def test_hotel_changes_currency_until_money_is_recorded(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    headers = await settings_headers(client, factory, hotel)
    mismatch = await client.patch(
        "/hotel/settings",
        json={"currency": "USD", "room_service_fee": {"amount_minor": 500, "currency": "ZAR"}},
        headers=headers,
    )
    assert mismatch.json()["error"]["code"] == "AMOUNT_INVALID"
    changed = await client.patch(
        "/hotel/settings",
        json={"currency": "USD", "room_service_fee": {"amount_minor": 500, "currency": "USD"}},
        headers=headers,
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["currency"] == "USD" and changed.json()["room_service_fee"]["currency"] == "USD"
    owner = await factory.auth(hotel, "hotel_owner")
    assert (await client.get("/auth/me", headers=owner)).json()["hotel"]["currency"] == "USD"
    async with owner_engine.connect() as conn:
        rt = (
            await conn.execute(
                text("SELECT currency FROM app.room_types WHERE hotel_id = :h"), {"h": hotel.id}
            )
        ).scalar_one()
    assert rt == "USD"
    # New stays and bills follow the hotel's currency.
    stay = await walk_in(client, factory, hotel)
    assert stay["nightly_rate"]["currency"] == "USD"
    headers = await settings_headers(client, factory, hotel)
    late = await client.patch("/hotel/settings", json={"currency": "EUR"}, headers=headers)
    assert late.json()["error"]["code"] == "INVALID_TRANSITION"
    unsupported = await client.patch("/hotel/settings", json={"currency": "XYZ"}, headers=headers)
    assert unsupported.json()["error"]["code"] == "VALIDATION_FAILED"


async def test_no_currency_default_in_the_database(owner_engine, factory):
    hotel = await factory.hotel(rooms=1)
    with pytest.raises(IntegrityError):
        async with owner_engine.begin() as conn:
            await conn.execute(
                text("INSERT INTO app.room_types (hotel_id, name, base_rate_minor) VALUES (:h, 'X', 100)"),
                {"h": hotel.id},
            )


async def test_plans_bill_in_their_own_currency_and_mrr_is_per_currency(client, factory, owner_engine):
    admin = await platform(factory)
    import uuid as _uuid

    code = f"usd_{_uuid.uuid4().hex[:6]}"
    plan = (
        await client.post(
            "/admin/plans",
            json={"code": code, "name": "Global", "monthly_price": {"amount_minor": 9900, "currency": "USD"}},
            headers={**admin, **idem()},
        )
    ).json()
    assert plan["monthly_price"] == {"amount_minor": 9900, "currency": "USD"}
    bad = await client.post(
        "/admin/plans",
        json={"code": f"{code}x", "name": "Bad", "monthly_price": {"amount_minor": 1, "currency": "XYZ"}},
        headers={**admin, **idem()},
    )
    assert bad.json()["error"]["code"] == "VALIDATION_FAILED"
    moved = await client.patch(
        f"/admin/plans/{plan['id']}",
        json={"monthly_price": {"amount_minor": 8900, "currency": "EUR"}},
        headers=admin,
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["monthly_price"] == {"amount_minor": 8900, "currency": "EUR"}

    hotel = await factory.hotel(rooms=1)
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.subscriptions SET plan_id = :p WHERE hotel_id = :h"),
            {"p": plan["id"], "h": hotel.id},
        )
    mrr = (await client.get("/admin/metrics", headers=admin)).json()["mrr"]
    by = {m["currency"]: m["amount_minor"] for m in mrr}
    assert by.get("EUR", 0) >= 8900 and "ZAR" in by  # never summed across currencies
