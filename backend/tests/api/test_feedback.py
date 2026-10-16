"""Guest feedback (D98): the tablet rates a finished request, a delivered order or the stay,
once each; managers see the averages and comments; comments stay out of events."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from tests.api.test_ordering import cart, idem, setup, zar


async def _done_request(client, factory, hotel, tablet) -> str:
    asked = await client.post("/guest/requests", json={"kind": "towels"}, headers={**tablet, **idem()})
    rec = await factory.auth(hotel, "receptionist")
    await client.post(f"/requests/{asked.json()['id']}/done", headers={**rec, **idem()})
    return asked.json()["id"]


async def test_a_guest_rates_a_finished_request_and_the_stay_once_each(client, factory, owner_engine):
    hotel, gm, tablet, _items, _stay = await setup(client, factory, owner_engine)
    req = await _done_request(client, factory, hotel, tablet)
    rated = await client.post(
        "/guest/feedback",
        json={"subject": "request", "request_id": req, "rating": 2, "comment": "Took a while"},
        headers={**tablet, **idem()},
    )
    assert rated.status_code == 201, rated.text
    again = await client.post(
        "/guest/feedback",
        json={"subject": "request", "request_id": req, "rating": 5},
        headers={**tablet, **idem()},
    )
    assert again.status_code == 409
    stay = await client.post(
        "/guest/feedback", json={"subject": "stay", "rating": 5}, headers={**tablet, **idem()}
    )
    assert stay.status_code == 201, stay.text
    mine = (await client.get("/guest/feedback", headers=tablet)).json()["data"]
    assert {f["subject"] for f in mine} == {"request", "stay"}

    today = datetime.now(UTC).date()
    span = {"from": str(today - timedelta(days=1)), "to": str(today + timedelta(days=1))}
    report = (await client.get("/reports/feedback", params=span, headers=gm)).json()
    assert report["ratings"] == 2 and report["average"] == 3.5
    assert report["distribution"] == [0, 1, 0, 0, 1]
    assert report["recent"][0]["comment"] == "Took a while"  # comments first

    async with owner_engine.connect() as conn:
        payloads = (
            (
                await conn.execute(
                    text(
                        "SELECT payload FROM app.event_outbox WHERE hotel_id = :h AND type = 'FEEDBACK_RECEIVED'"
                    ),
                    {"h": hotel.id},
                )
            )
            .scalars()
            .all()
        )
    assert payloads and all("comment" not in p for p in payloads)
    assert any(p["low"] for p in payloads)


async def test_only_finished_things_of_this_stay_can_be_rated(client, factory, owner_engine):
    hotel, _gm, tablet, items, _stay = await setup(client, factory, owner_engine)
    open_req = await client.post("/guest/requests", json={"kind": "pillows"}, headers={**tablet, **idem()})
    early = await client.post(
        "/guest/feedback",
        json={"subject": "request", "request_id": open_req.json()["id"], "rating": 4},
        headers={**tablet, **idem()},
    )
    assert early.status_code == 409
    order = await client.post(
        "/guest/orders", json={"lines": cart(items), "quoted_total": zar(36000)}, headers={**tablet, **idem()}
    )
    not_delivered = await client.post(
        "/guest/feedback",
        json={"subject": "order", "order_id": order.json()["id"], "rating": 4},
        headers={**tablet, **idem()},
    )
    assert not_delivered.status_code == 409
    mismatched = await client.post(
        "/guest/feedback", json={"subject": "order", "rating": 4}, headers={**tablet, **idem()}
    )
    assert mismatched.status_code == 400

    # Another room's tablet cannot rate this room's request.
    _h2, _gm2, other_tablet, _i2, _s2 = await setup(client, factory, owner_engine)
    req = await _done_request(client, factory, hotel, tablet)
    stranger = await client.post(
        "/guest/feedback",
        json={"subject": "request", "request_id": req, "rating": 1},
        headers={**other_tablet, **idem()},
    )
    assert stranger.status_code == 404
    kitchen = await factory.auth(hotel, "kitchen_staff")
    today = datetime.now(UTC).date()
    span = {"from": str(today), "to": str(today)}
    assert (await client.get("/reports/feedback", params=span, headers=kitchen)).status_code == 403
