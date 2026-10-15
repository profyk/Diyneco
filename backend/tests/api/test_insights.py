"""Platform insights, owners and the enriched hotel list (DECISIONS D87): platform staff only,
aggregates only, money per currency."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from app.services.insights import monthly_minor
from tests.api.test_admin import platform

NEW_HOTEL = {
    "hotel": {
        "name": "Insight Lodge Two",
        "country": "ZA",
        "property_type": "lodge",
        "address": {"line1": "1 Main Road", "city": "George", "province_code": "ZA-WC"},
    }
}


def test_mrr_is_the_monthly_equivalent():
    assert monthly_minor(120000, "year") == 10000
    assert monthly_minor(30000, "quarter") == 10000
    assert monthly_minor(10000, "month") == 10000
    assert monthly_minor(None, "month") == 0 and monthly_minor(10000, None) == 0


async def test_insights_are_for_platform_staff_only(client, factory):
    hotel = await factory.hotel(roles=("hotel_owner",))
    assert (
        await client.get("/admin/insights", headers=await factory.auth(hotel, "hotel_owner"))
    ).status_code == 403
    assert (
        await client.get("/admin/owners", headers=await factory.auth(hotel, "hotel_owner"))
    ).status_code == 403
    admin = await platform(factory)
    bad = await client.get(
        "/admin/insights",
        params={"since": date.today().isoformat(), "until": (date.today() - timedelta(days=3)).isoformat()},
        headers=admin,
    )
    assert bad.status_code == 400


async def test_insights_count_signups_funnel_and_breakdowns(client, factory):
    await factory.hotel(roles=("hotel_owner",))
    admin = await platform(factory)
    r = await client.get("/admin/insights", headers=admin)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["totals"]["hotels"] >= 1 and body["period"]["signups"] >= 1
    assert body["funnel"][0]["step"] == "signed_up"
    assert body["funnel"][0]["hotels"] >= body["funnel"][-1]["hotels"]
    assert len(body["days"]) == 30 and sum(d["signups"] for d in body["days"]) == body["period"]["signups"]
    za = next(c for c in body["by_country"] if c["key"] == "ZA")
    assert za["label"] == "South Africa" and za["hotels"] >= 1
    assert any(u["role"] == "hotel_owner" for u in body["users"])
    assert body["cohorts"] and body["cohorts"][-1]["signups"] >= 1


async def test_owners_list_their_properties(client, factory):
    hotel = await factory.hotel(roles=("hotel_owner",))
    owner = hotel.users["hotel_owner"]
    headers = await factory.step_up(hotel, "hotel_owner", await factory.auth(hotel, "hotel_owner"))
    added = await client.post(
        "/hotels", json=NEW_HOTEL, headers={**headers, "Idempotency-Key": str(uuid.uuid4())}
    )
    assert added.status_code == 201, added.text

    admin = await platform(factory)
    owners = (await client.get("/admin/owners", headers=admin)).json()["data"]
    mine = next(o for o in owners if o["email"] == owner.email)
    assert {h["name"] for h in mine["hotels"]} == {hotel.name, "Insight Lodge Two"}
    assert mine["countries"] == ["ZA"]
    insights = (await client.get("/admin/insights", headers=admin)).json()
    assert insights["totals"]["multi_property_owners"] >= 1

    listed = (await client.get("/admin/hotels", headers=admin)).json()["data"]
    two = next(h for h in listed if h["name"] == "Insight Lodge Two")
    assert (two["country"], two["province"], two["city"], two["property_type"]) == (
        "ZA",
        "Western Cape",
        "George",
        "lodge",
    )
    assert two["activated"] is False and two["gmv_30d"]["currency"] == "ZAR"
