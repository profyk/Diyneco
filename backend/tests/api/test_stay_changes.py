"""Extending, shortening and moving stays."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import text

from tests.api.test_billing import walk_in
from tests.api.test_checkout import pair_tablet
from tests.api.test_room_service import idem, ready_order, zar


async def etag(client, headers, stay_id: str) -> str:
    r = await client.get(f"/stays/{stay_id}", headers=headers)
    assert r.status_code == 200, r.text
    return r.headers["ETag"]


async def test_extend_and_shorten_a_checked_in_stay(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel, nights=2)
    rec = await factory.auth(hotel, "receptionist")
    arrival = date.fromisoformat(stay["arrival_date"])

    missing = await client.patch(
        f"/stays/{stay['id']}", json={"departure_date": str(arrival + timedelta(days=5))}, headers=rec
    )
    assert missing.status_code == 412
    tag = await etag(client, rec, stay["id"])
    longer = await client.patch(
        f"/stays/{stay['id']}",
        json={"departure_date": str(arrival + timedelta(days=5))},
        headers={**rec, "If-Match": tag},
    )
    assert longer.status_code == 200, longer.text
    assert longer.json()["nights"] == 5 and longer.json()["folio"]["accommodation"] == zar(750000)
    stale = await client.patch(
        f"/stays/{stay['id']}",
        json={"departure_date": str(arrival + timedelta(days=3))},
        headers={**rec, "If-Match": tag},
    )
    assert stale.status_code == 412

    shorter = await client.patch(
        f"/stays/{stay['id']}",
        json={"departure_date": str(arrival + timedelta(days=3))},
        headers={**rec, "If-Match": longer.headers["ETag"]},
    )
    assert shorter.status_code == 200, shorter.text
    assert shorter.json()["folio"]["accommodation"] == zar(450000)
    folio = (await client.get(f"/folios/{stay['id']}", headers=rec)).json()
    reversed_nights = [e for e in folio["entries"] if e["type"] == "reversal"]
    assert len(reversed_nights) == 2 and all(e["amount"] == zar(-150000) for e in reversed_nights)

    tag = shorter.headers["ETag"]
    for body, field in (
        ({"departure_date": str(arrival - timedelta(days=1))}, "departure_date"),
        ({"arrival_date": str(arrival + timedelta(days=1))}, "arrival_date"),
        ({"departure_date": str(arrival + timedelta(days=91))}, "departure_date"),
    ):
        r = await client.patch(f"/stays/{stay['id']}", json=body, headers={**rec, "If-Match": tag})
        assert r.json()["error"]["code"] == "VALIDATION_FAILED", r.text
        assert r.json()["error"]["details"]["fields"][0]["field"] == field

    async with owner_engine.connect() as conn:
        audited = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM app.audit_logs WHERE hotel_id = :h AND action = 'stay.change_dates'"
                ),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert audited == 2


async def test_dates_respect_other_bookings_and_reservations_move_freely(client, factory):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel, nights=2)
    rec = await factory.auth(hotel, "receptionist")
    arrival = date.fromisoformat(stay["arrival_date"])
    booking = await client.post(
        "/stays",
        json={
            "room_id": str(hotel.room_ids[0]),
            "guest": {"name": "Later Guest"},
            "arrival_date": str(arrival + timedelta(days=4)),
            "departure_date": str(arrival + timedelta(days=6)),
        },
        headers={**rec, **idem()},
    )
    assert booking.status_code == 201, booking.text
    clash = await client.patch(
        f"/stays/{stay['id']}",
        json={"departure_date": str(arrival + timedelta(days=5))},
        headers={**rec, "If-Match": await etag(client, rec, stay["id"])},
    )
    assert clash.json()["error"]["code"] == "ROOM_NOT_AVAILABLE"

    moved = await client.patch(
        f"/stays/{booking.json()['id']}",
        json={
            "arrival_date": str(arrival + timedelta(days=10)),
            "departure_date": str(arrival + timedelta(days=12)),
        },
        headers={**rec, "If-Match": await etag(client, rec, booking.json()["id"])},
    )
    assert moved.status_code == 200, moved.text
    assert (moved.json()["nights"], moved.json()["folio"]) == (2, None)
    ok = await client.patch(
        f"/stays/{stay['id']}",
        json={"departure_date": str(arrival + timedelta(days=5))},
        headers={**rec, "If-Match": await etag(client, rec, stay["id"])},
    )
    assert ok.status_code == 200, ok.text


async def test_move_a_checked_in_guest(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=3)
    gm = await factory.auth(hotel, "general_manager")
    old_tablet = await pair_tablet(client, gm, hotel.room_ids[0])
    new_tablet = await pair_tablet(client, gm, hotel.room_ids[1])
    stay = await walk_in(client, factory, hotel, nights=2)
    rec = await factory.auth(hotel, "receptionist")
    other = (
        await client.post(
            f"/rooms/{hotel.room_ids[2]}/walk-in",
            json={"guest": {"name": "Neighbour"}, "nights": 1},
            headers={**rec, **idem()},
        )
    ).json()
    assert other["room"]["id"] == str(hotel.room_ids[2])

    body = {"room_id": str(hotel.room_ids[1]), "reason": "Air conditioning broken"}
    r = await client.post(f"/stays/{stay['id']}/move", json=body, headers={**rec, **idem()})
    assert r.json()["error"]["code"] == "STEP_UP_REQUIRED"
    rec_s = await factory.step_up(hotel, "receptionist", rec)
    occupied = await client.post(
        f"/stays/{stay['id']}/move", json={"room_id": str(hotel.room_ids[2])}, headers={**rec_s, **idem()}
    )
    assert occupied.json()["error"]["code"] == "ROOM_NOT_AVAILABLE"
    moved = await client.post(f"/stays/{stay['id']}/move", json=body, headers={**rec_s, **idem()})
    assert moved.status_code == 200, moved.text
    assert moved.json()["room"]["id"] == str(hotel.room_ids[1])

    async with owner_engine.connect() as conn:
        statuses = dict(
            (
                await conn.execute(
                    text("SELECT id, status FROM app.rooms WHERE id IN (:a, :b)"),
                    {"a": hotel.room_ids[0], "b": hotel.room_ids[1]},
                )
            ).all()
        )
        reason = (
            await conn.execute(
                text("SELECT reason FROM app.audit_logs WHERE hotel_id = :h AND action = 'stay.move'"),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert (statuses[hotel.room_ids[0]], statuses[hotel.room_ids[1]]) == ("cleaning", "occupied")
    assert reason == "Air conditioning broken"

    # The old room's tablet resets and shows nothing; the guest's session follows them.
    assert (await client.post("/devices/heartbeat", json={}, headers=old_tablet)).json()["commands"] == [
        "RESET"
    ]
    await client.post("/devices/heartbeat", json={"completed_commands": ["RESET"]}, headers=old_tablet)
    assert (await client.get("/guest/session", headers=old_tablet)).json()["state"] == "idle"
    assert (await client.get("/guest/session", headers=new_tablet)).json()["state"] == "active"
    folio = (await client.get("/guest/folio", headers=new_tablet)).json()
    assert folio["totals"]["accommodation"] == zar(300000)


async def test_move_waits_for_open_orders_and_is_tenant_scoped(client, factory, owner_engine):
    hotel, gm, _order, stay = await ready_order(
        client, factory, owner_engine, hotel=await factory.hotel(rooms=2)
    )
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    r = await client.post(
        f"/stays/{stay['id']}/move", json={"room_id": str(hotel.room_ids[1])}, headers={**gm_s, **idem()}
    )
    assert r.json()["error"]["code"] == "OPEN_ORDERS"

    other = await factory.hotel(rooms=1)
    gm_b = await factory.step_up(other, "general_manager", await factory.auth(other, "general_manager"))
    for resp in (
        await client.post(
            f"/stays/{stay['id']}/move", json={"room_id": str(other.room_ids[0])}, headers={**gm_b, **idem()}
        ),
        await client.patch(
            f"/stays/{stay['id']}", json={"departure_date": "2030-01-01"}, headers={**gm_b, "If-Match": '"1"'}
        ),
        await client.post(
            f"/stays/{stay['id']}/move", json={"room_id": str(other.room_ids[0])}, headers={**gm_s, **idem()}
        ),
    ):
        assert resp.status_code == 404, resp.text
