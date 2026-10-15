"""Guest service requests (D93): the tablet asks during the stay, staff take and finish them,
the guest only sees their own stay's requests, moves never go backwards, and a request from
another hotel does not exist."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from tests.api.test_ordering import idem, setup
from tests.api.test_privacy import checked_out_guest


async def test_a_guest_asks_and_staff_take_it_to_done(client, factory, owner_engine):
    hotel, _gm, tablet, _items, stay = await setup(client, factory, owner_engine)
    asked = await client.post(
        "/guest/requests", json={"kind": "towels", "note": "Two bath towels"}, headers={**tablet, **idem()}
    )
    assert asked.status_code == 201, asked.text
    req = asked.json()
    assert req["status"] == "open" and "assigned_to" not in req

    rec = await factory.auth(hotel, "receptionist")
    board = (await client.get("/requests", headers=rec)).json()
    mine = next(r for r in board["data"] if r["id"] == req["id"])
    assert mine["room"] and mine["source"] == "guest" and mine["stay_id"] == stay["id"]
    assert board["summary"]["open"] >= 1

    started = await client.post(f"/requests/{req['id']}/start", headers={**rec, **idem()})
    assert started.status_code == 200, started.text
    assert started.json()["status"] == "in_progress" and started.json()["assigned_to"]["name"]
    # The guest cannot cancel once someone is on it.
    late = await client.post(f"/guest/requests/{req['id']}/cancel", headers={**tablet, **idem()})
    assert late.status_code == 409
    done = await client.post(f"/requests/{req['id']}/done", headers={**rec, **idem()})
    assert done.json()["status"] == "done" and done.json()["completed_at"]
    # Never backwards.
    again = await client.post(f"/requests/{req['id']}/acknowledge", headers={**rec, **idem()})
    assert again.status_code == 409

    seen = (await client.get("/guest/requests", headers=tablet)).json()["data"]
    assert [r["status"] for r in seen if r["id"] == req["id"]] == ["done"]
    summary = (await client.get("/requests", headers=rec)).json()["summary"]
    assert summary["done_today"] >= 1 and summary["median_minutes_to_done"] is not None

    async with owner_engine.connect() as conn:
        types = (
            (
                await conn.execute(
                    text(
                        "SELECT type FROM app.event_outbox WHERE hotel_id = :h AND payload->>'request_id' = :r"
                    ),
                    {"h": hotel.id, "r": req["id"]},
                )
            )
            .scalars()
            .all()
        )
        audit = (
            await conn.execute(
                text("SELECT count(*) FROM app.audit_logs WHERE hotel_id = :h AND entity_id = :r"),
                {"h": hotel.id, "r": req["id"]},
            )
        ).scalar_one()
    assert types[0] == "REQUEST_CREATED" and types.count("REQUEST_UPDATED") == 2
    assert audit == 3


async def test_the_requests_report_counts_by_kind_and_by_who_finished(client, factory, owner_engine):
    hotel, gm, tablet, _items, _stay = await setup(client, factory, owner_engine)
    ids = []
    for kind in ("towels", "towels", "maintenance"):
        r = await client.post("/guest/requests", json={"kind": kind}, headers={**tablet, **idem()})
        ids.append(r.json()["id"])
    rec = await factory.auth(hotel, "receptionist")
    await client.post(f"/requests/{ids[0]}/done", headers={**rec, **idem()})
    await client.post(f"/requests/{ids[2]}/cancel", json={}, headers={**rec, **idem()})
    today = datetime.now(UTC).date()
    span = {"from": str(today - timedelta(days=1)), "to": str(today + timedelta(days=1))}
    report = await client.get("/reports/requests", params=span, headers=gm)
    assert report.status_code == 200, report.text
    kinds = {k["kind"]: k for k in report.json()["kinds"]}
    assert kinds["towels"]["requests"] == 2 and kinds["towels"]["done"] == 1
    assert kinds["towels"]["from_guests"] == 2 and kinds["towels"]["median_minutes_to_done"] == 0
    assert kinds["maintenance"]["cancelled"] == 1 and kinds["maintenance"]["median_minutes_to_done"] is None
    assert [s["done"] for s in report.json()["staff"]] == [1]
    kitchen = await factory.auth(hotel, "kitchen_staff")
    assert (await client.get("/reports/requests", params=span, headers=kitchen)).status_code == 403


async def test_guest_rules_wake_up_time_cancel_and_no_stay(client, factory, owner_engine):
    _hotel, _gm, tablet, _items, _stay = await setup(client, factory, owner_engine)
    no_time = await client.post("/guest/requests", json={"kind": "wake_up"}, headers={**tablet, **idem()})
    assert no_time.status_code == 400
    far = (datetime.now(UTC) + timedelta(days=30)).isoformat()
    assert (
        await client.post(
            "/guest/requests", json={"kind": "wake_up", "due_at": far}, headers={**tablet, **idem()}
        )
    ).status_code == 400
    soon = (datetime.now(UTC) + timedelta(hours=8)).isoformat()
    wake = await client.post(
        "/guest/requests", json={"kind": "wake_up", "due_at": soon}, headers={**tablet, **idem()}
    )
    assert wake.status_code == 201, wake.text
    off = await client.post(f"/guest/requests/{wake.json()['id']}/cancel", headers={**tablet, **idem()})
    assert off.status_code == 200 and off.json()["status"] == "cancelled"
    unknown = await client.post("/guest/requests", json={"kind": "spa_day"}, headers={**tablet, **idem()})
    assert unknown.status_code == 400

    _h2, _gm2, idle_tablet, _i2, _s2 = await setup(client, factory, owner_engine, check_in=False)
    assert (
        await client.post("/guest/requests", json={"kind": "towels"}, headers={**idle_tablet, **idem()})
    ).status_code == 422  # NO_ACTIVE_STAY
    assert (await client.get("/guest/requests", headers=idle_tablet)).json()["data"] == []


async def test_a_room_cannot_flood_the_team(client, factory, owner_engine):
    _hotel, _gm, tablet, _items, _stay = await setup(client, factory, owner_engine)
    for _ in range(10):
        r = await client.post("/guest/requests", json={"kind": "other"}, headers={**tablet, **idem()})
        assert r.status_code == 201
    assert (
        await client.post("/guest/requests", json={"kind": "other"}, headers={**tablet, **idem()})
    ).status_code == 400


async def test_staff_log_requests_and_permissions_and_tenancy_hold(client, factory, owner_engine):
    hotel, _gm, tablet, _items, _stay = await setup(client, factory, owner_engine, rooms=2)
    rs = await factory.auth(hotel, "room_service_staff")
    logged = await client.post(
        "/requests",
        json={"room_id": str(hotel.room_ids[1]), "kind": "maintenance", "note": "Shower drips"},
        headers={**rs, **idem()},
    )
    assert logged.status_code == 201, logged.text
    item = logged.json()
    assert item["source"] == "staff" and item["stay_id"] is None and item["created_by"]["name"]
    # The tablet of another room never sees it.
    assert all(
        r["id"] != item["id"] for r in (await client.get("/guest/requests", headers=tablet)).json()["data"]
    )

    kitchen = await factory.auth(hotel, "kitchen_staff")
    assert (await client.get("/requests", headers=kitchen)).status_code == 403
    finance = await factory.auth(hotel, "finance_manager")
    assert (
        await client.post(f"/requests/{item['id']}/done", headers={**finance, **idem()})
    ).status_code == 403

    # Assign only to someone who can handle requests.
    rec = await factory.auth(hotel, "receptionist")
    rec_id = hotel.users["receptionist"].user_id
    given = await client.post(
        f"/requests/{item['id']}/assign", json={"user_id": str(rec_id)}, headers={**rs, **idem()}
    )
    assert given.status_code == 200 and given.json()["status"] == "acknowledged", given.text
    kitchen_id = hotel.users["kitchen_staff"].user_id
    assert (
        await client.post(
            f"/requests/{item['id']}/assign", json={"user_id": str(kitchen_id)}, headers={**rs, **idem()}
        )
    ).status_code == 404
    mine = (await client.get("/requests", params={"scope": "mine"}, headers=rec)).json()["data"]
    assert [r["id"] for r in mine] == [item["id"]]
    cancelled = await client.post(
        f"/requests/{item['id']}/cancel", json={"reason": "Fixed already"}, headers={**rec, **idem()}
    )
    assert cancelled.json()["status"] == "cancelled" and cancelled.json()["cancelled_by"] == "staff"

    other = await factory.hotel(roles=("receptionist",))
    stranger = await factory.auth(other, "receptionist")
    assert (
        await client.post(f"/requests/{item['id']}/done", headers={**stranger, **idem()})
    ).status_code == 404
    assert (
        await client.post(
            "/requests",
            json={"room_id": str(hotel.room_ids[0]), "kind": "towels"},
            headers={**stranger, **idem()},
        )
    ).status_code == 404


async def test_anonymising_a_guest_redacts_request_notes(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    rows = await checked_out_guest(factory, owner_engine, hotel)
    gm = await factory.auth(hotel, "general_manager")
    async with owner_engine.begin() as conn:
        rid = (
            await conn.execute(
                text(
                    "INSERT INTO app.service_requests (hotel_id, room_id, room_number, stay_id, kind, note, "
                    "source, created_by) VALUES (:h, :room, '101', :s, 'other', 'Call me on 082 555 0101', "
                    "'staff', :u) RETURNING id"
                ),
                {
                    "h": hotel.id,
                    "room": hotel.room_ids[0],
                    "s": rows["stay_id"],
                    "u": hotel.users["general_manager"].user_id,
                },
            )
        ).scalar_one()
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    r = await client.post(
        f"/guests/{rows['guest_id']}/anonymise", json={"reason": "Guest asked"}, headers={**gm_s, **idem()}
    )
    assert r.status_code == 200, r.text
    async with owner_engine.connect() as conn:
        note = (
            await conn.execute(text("SELECT note FROM app.service_requests WHERE id = :r"), {"r": rid})
        ).scalar_one()
    assert "082" not in note
