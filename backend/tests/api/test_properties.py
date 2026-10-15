"""Owners with several properties (DECISIONS D86): adding a property, one free trial per owner,
trials granted by the platform, and the portfolio across the owner's hotels only."""

from __future__ import annotations

import uuid

from sqlalchemy import text

from tests.api.test_admin import platform, step_up
from tests.factories import SeededHotel, SeededUser


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


NEW_HOTEL = {
    "hotel": {
        "name": "Sunbird Lodge Two",
        "country": "ZA",
        "property_type": "lodge",
        "room_count": 12,
        "address": {"line1": "3 Main Road", "city": "Knysna", "province_code": "ZA-WC"},
    }
}


async def _add(client, factory, hotel, role="hotel_owner"):
    headers = await factory.step_up(hotel, role, await factory.auth(hotel, role))
    return await client.post("/hotels", json=NEW_HOTEL, headers={**headers, **idem()})


async def _as_owner_of(factory, owner_engine, owner: SeededUser, hotel_id: uuid.UUID) -> dict[str, str]:
    async with owner_engine.connect() as conn:
        hu = (
            await conn.execute(
                text("SELECT id FROM app.hotel_users WHERE hotel_id = :h AND user_id = :u"),
                {"h": hotel_id, "u": owner.user_id},
            )
        ).scalar_one()
    there = SeededHotel(id=hotel_id, name="new")
    me = SeededUser(
        "hotel_owner", owner.email, owner.password, owner.user_id, hu, owner.name, owner.totp_secret
    )
    token, _ = await factory.token(there, me)
    return {"Authorization": f"Bearer {token}"}


async def test_an_owner_adds_a_property_without_a_second_free_trial(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("hotel_owner", "general_manager"))
    owner = hotel.users["hotel_owner"]

    no_step_up = await client.post(
        "/hotels", json=NEW_HOTEL, headers={**await factory.auth(hotel, "hotel_owner"), **idem()}
    )
    assert no_step_up.status_code == 403
    assert (await _add(client, factory, hotel, "general_manager")).status_code == 403  # owners only

    r = await _add(client, factory, hotel)
    assert r.status_code == 201, r.text
    new = r.json()
    assert new["status"] == "pending_approval" and new["subscription_status"] is None
    assert new["code"].startswith("DYN-")

    async with owner_engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT h.address->>'province' AS province, h.property_type, "
                    "(SELECT count(*) FROM app.subscriptions s WHERE s.hotel_id = h.id) AS subs, "
                    "(SELECT r.code FROM app.user_roles ur JOIN app.roles r ON r.id = ur.role_id "
                    " JOIN app.hotel_users hu ON hu.id = ur.hotel_user_id "
                    " WHERE hu.hotel_id = h.id AND hu.user_id = :u) AS role "
                    "FROM app.hotels h WHERE h.id = :h"
                ),
                {"h": new["hotel_id"], "u": owner.user_id},
            )
        ).one()
    assert tuple(row) == ("Western Cape", "lodge", 0, "hotel_owner")

    # One login, both hotels: the owner switches between them with /auth/refresh.
    async with owner_engine.connect() as conn:
        mine = (
            await conn.execute(text("SELECT hotel_id FROM app.user_memberships(:u)"), {"u": owner.user_id})
        ).scalars()
        assert {str(h) for h in mine} == {str(hotel.id), new["hotel_id"]}


async def test_a_property_without_a_plan_cannot_grow_until_a_trial_or_plan(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("hotel_owner",))
    owner = hotel.users["hotel_owner"]
    new_id = uuid.UUID((await _add(client, factory, hotel)).json()["hotel_id"])
    there = await _as_owner_of(factory, owner_engine, owner, new_id)
    # Pending approval refuses most writes anyway; approve it to see the plan rule alone.
    async with owner_engine.begin() as conn:
        await conn.execute(text("UPDATE app.hotels SET status = 'active' WHERE id = :h"), {"h": new_id})

    room_type = await client.post(
        "/room-types",
        json={"name": "Standard", "base_rate": {"amount_minor": 100000, "currency": "ZAR"}},
        headers={**there, **idem()},
    )
    assert room_type.status_code == 201, room_type.text
    room = {"number": "1", "room_type_id": room_type.json()["id"]}
    blocked = await client.post("/rooms", json=room, headers={**there, **idem()})
    assert blocked.status_code == 422 and blocked.json()["error"]["code"] == "PLAN_LIMIT_REACHED"

    admin = await platform(factory)
    billing = await platform(factory, "platform_support")
    grant = {"days": 14, "reason": "Second lodge for an existing customer"}
    assert (
        await client.post(f"/admin/hotels/{new_id}/trial", json=grant, headers=billing)
    ).status_code == 403
    assert (
        await client.post(f"/admin/hotels/{new_id}/trial", json=grant, headers=admin)
    ).status_code == 403  # step-up
    ok = await client.post(f"/admin/hotels/{new_id}/trial", json=grant, headers=step_up(factory, admin))
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "trial" and ok.json()["trial_ends_on"] is not None
    async with owner_engine.connect() as conn:
        audited = (
            await conn.execute(
                text(
                    "SELECT reason FROM app.audit_logs WHERE hotel_id = :h AND action = 'subscription.trial_granted'"
                ),
                {"h": new_id},
            )
        ).scalar_one()
    assert audited == grant["reason"]
    assert (await client.post("/rooms", json=room, headers={**there, **idem()})).status_code == 201

    # A hotel on a plan is never put back on a trial.
    on_plan = await client.post(
        f"/admin/hotels/{hotel.id}/trial", json=grant, headers=step_up(factory, admin)
    )
    assert on_plan.status_code == 409


async def test_the_portfolio_shows_only_the_owners_hotels(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("hotel_owner", "receptionist"))
    other = await factory.hotel(roles=("hotel_owner",))  # someone else's hotel
    await _add(client, factory, hotel)
    owner_headers = await factory.auth(hotel, "hotel_owner")

    r = await client.get("/portfolio", headers=owner_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    names = [h["name"] for h in body["data"]]
    assert len(names) == 2 and other.name not in names and hotel.name in names
    assert body["totals"]["properties"] == 2
    assert [t["currency"] for t in body["totals"]["revenue"]] == ["ZAR"]
    first = next(h for h in body["data"] if h["hotel_id"] == str(hotel.id))
    assert first["rooms"] == 2 and first["subscription_status"] == "active"

    assert (
        await client.get("/portfolio", headers=await factory.auth(hotel, "receptionist"))
    ).status_code == 403
    # The request's own hotel context is restored afterwards: a normal read still works.
    assert (await client.get("/hotel", headers=owner_headers)).json()["id"] == str(hotel.id)
