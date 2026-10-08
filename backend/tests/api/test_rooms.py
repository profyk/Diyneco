"""Room types and rooms: create, ranges, CSV import, status rules, permissions, tenancy."""

from __future__ import annotations

import uuid

from sqlalchemy import text

from app.services.rooms import parse_rate


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


def zar(amount: int) -> dict:
    return {"amount_minor": amount, "currency": "ZAR"}


async def _room_type(client, headers, name="Deluxe", rate=250000) -> dict:
    r = await client.post(
        "/room-types",
        json={"name": name, "base_rate": zar(rate), "capacity": 3, "amenities": ["Sea view", "sea view"]},
        headers={**headers, **idem()},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_room_type_create_list_and_duplicate_name(client, factory):
    hotel = await factory.hotel(rooms=0)
    h = await factory.auth(hotel, "general_manager")
    rt = await _room_type(client, h)
    assert rt["base_rate"] == zar(250000)
    assert rt["amenities"] == ["Sea view"]
    dup = await client.post(
        "/room-types", json={"name": "deluxe", "base_rate": zar(1)}, headers={**h, **idem()}
    )
    assert dup.status_code == 400
    listed = (await client.get("/room-types", headers=h)).json()["data"]
    assert {t["name"] for t in listed} == {"Standard", "Deluxe"}


async def test_room_type_rate_change_needs_step_up_but_rename_does_not(client, factory):
    hotel = await factory.hotel(rooms=0)
    h = await factory.auth(hotel, "general_manager")
    rt = await _room_type(client, h)
    rename = await client.patch(
        f"/room-types/{rt['id']}", json={"name": "Deluxe King"}, headers={**h, "If-Match": '"1"'}
    )
    assert rename.status_code == 200, rename.text
    assert rename.headers["ETag"] == '"2"'
    rate = await client.patch(
        f"/room-types/{rt['id']}", json={"base_rate": zar(300000)}, headers={**h, "If-Match": '"2"'}
    )
    assert rate.json()["error"]["code"] == "STEP_UP_REQUIRED"
    stepped = await factory.step_up(hotel, "general_manager", h)
    ok = await client.patch(
        f"/room-types/{rt['id']}", json={"base_rate": zar(300000)}, headers={**stepped, "If-Match": '"2"'}
    )
    assert ok.status_code == 200
    assert ok.json()["base_rate"] == zar(300000)
    stale = await client.patch(
        f"/room-types/{rt['id']}", json={"capacity": 4}, headers={**h, "If-Match": '"2"'}
    )
    assert stale.status_code == 412


async def test_money_must_use_hotel_currency(client, factory):
    hotel = await factory.hotel(rooms=0)
    h = await factory.auth(hotel, "general_manager")
    r = await client.post(
        "/room-types",
        json={"name": "Euro", "base_rate": {"amount_minor": 100, "currency": "EUR"}},
        headers={**h, **idem()},
    )
    assert r.json()["error"]["code"] == "AMOUNT_INVALID"
    floaty = await client.post(
        "/room-types",
        json={"name": "Float", "base_rate": {"amount_minor": 10.5, "currency": "ZAR"}},
        headers={**h, **idem()},
    )
    assert floaty.status_code == 400


async def test_create_single_room_and_reject_duplicate_number(client, factory):
    hotel = await factory.hotel(rooms=1)  # room 101 exists
    h = await factory.auth(hotel, "general_manager")
    r = await client.post(
        "/rooms",
        json={"number": "259", "floor": "2", "room_type_id": str(hotel.room_type_id)},
        headers={**h, **idem()},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "available"
    assert body["rate"] is None and body["effective_rate"] == zar(150000)
    dup = await client.post(
        "/rooms", json={"number": "101", "room_type_id": str(hotel.room_type_id)}, headers={**h, **idem()}
    )
    assert dup.status_code == 400
    assert dup.json()["error"]["details"]["existing"] == ["101"]


async def test_bulk_ranges_all_or_nothing(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=0)
    h = await factory.auth(hotel, "general_manager")
    rt = str(hotel.room_type_id)
    ok = await client.post(
        "/rooms/bulk",
        json={"ranges": [{"from": 301, "to": 310, "floor": 3, "room_type_id": rt}]},
        headers={**h, **idem()},
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["created"] == 10
    clash = await client.post(
        "/rooms/bulk",
        json={
            "ranges": [
                {"from": 401, "to": 405, "floor": 4, "room_type_id": rt},
                {"from": 310, "to": 311, "floor": 3, "room_type_id": rt},
            ]
        },
        headers={**h, **idem()},
    )
    assert clash.status_code == 400
    async with owner_engine.connect() as conn:
        n = (
            await conn.execute(text("SELECT count(*) FROM app.rooms WHERE hotel_id = :h"), {"h": hotel.id})
        ).scalar_one()
    assert n == 10  # nothing from the failed call was written


async def test_bulk_rejects_more_than_2000_rooms(client, factory):
    hotel = await factory.hotel(rooms=0)
    h = await factory.auth(hotel, "general_manager")
    r = await client.post(
        "/rooms/bulk",
        json={"ranges": [{"from": 1, "to": 2001, "room_type_id": str(hotel.room_type_id)}]},
        headers={**h, **idem()},
    )
    assert r.status_code == 400


async def test_plan_limit_on_rooms(client, factory):
    hotel = await factory.hotel(rooms=0)  # starter plan: 50 rooms
    h = await factory.auth(hotel, "general_manager")
    r = await client.post(
        "/rooms/bulk",
        json={"ranges": [{"from": 1, "to": 51, "room_type_id": str(hotel.room_type_id)}]},
        headers={**h, **idem()},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "PLAN_LIMIT_REACHED"
    assert r.json()["error"]["details"]["limit"] == 50


async def test_list_rooms_natural_order_filters_and_cursor(client, factory):
    hotel = await factory.hotel(rooms=0)
    h = await factory.auth(hotel, "receptionist")
    gm = await factory.auth(hotel, "general_manager")
    rt = str(hotel.room_type_id)
    await client.post(
        "/rooms/bulk",
        json={
            "ranges": [
                {"from": 1000, "to": 1001, "floor": 10, "room_type_id": rt},
                {"from": 99, "to": 101, "floor": 1, "room_type_id": rt},
            ]
        },
        headers={**gm, **idem()},
    )
    first = await client.get("/rooms", params={"limit": 3}, headers=h)
    assert first.status_code == 200, first.text
    assert [r["number"] for r in first.json()["data"]] == ["99", "100", "101"]
    second = await client.get("/rooms", params={"limit": 3, "cursor": first.json()["next_cursor"]}, headers=h)
    assert [r["number"] for r in second.json()["data"]] == ["1000", "1001"]
    assert second.json()["next_cursor"] is None
    floor = await client.get("/rooms", params={"floor": "10"}, headers=h)
    assert len(floor.json()["data"]) == 2
    bad = await client.get("/rooms", params={"colour": "red"}, headers=h)
    assert bad.status_code == 400
    bad_cursor = await client.get("/rooms", params={"cursor": "nope"}, headers=h)
    assert bad_cursor.status_code == 400


CSV_OK = (
    "room_number,floor,room_type,rate,capacity,amenities\n"
    "501,5,Standard,1850.50,2,Wi-Fi|Balcony\n"
    "502,5,standard,,,\n"
)


async def test_csv_import_dry_run_then_commit(client, factory):
    hotel = await factory.hotel(rooms=0)
    h = {**(await factory.auth(hotel, "general_manager")), "Content-Type": "text/csv"}
    dry = await client.post("/rooms/import", content=CSV_OK, headers={**h, **idem()})
    assert dry.status_code == 200, dry.text
    assert dry.json() == {"committed": False, "valid": True, "rows": 2, "errors": [], "created": 0}
    assert (await client.get("/rooms", headers=h)).json()["data"] == []
    done = await client.post(
        "/rooms/import", params={"commit": "true"}, content=CSV_OK, headers={**h, **idem()}
    )
    assert done.status_code == 201, done.text
    assert done.json()["created"] == 2
    rooms = {r["number"]: r for r in (await client.get("/rooms", headers=h)).json()["data"]}
    assert rooms["501"]["rate"] == zar(185050)
    assert rooms["501"]["amenities"] == ["Wi-Fi", "Balcony"]
    assert rooms["502"]["rate"] is None


async def test_csv_import_reports_every_bad_line_and_writes_nothing(client, factory):
    hotel = await factory.hotel(rooms=1)  # 101 exists
    h = {**(await factory.auth(hotel, "general_manager")), "Content-Type": "text/csv"}
    bad = (
        "room_number,floor,room_type,rate,capacity,amenities\n"
        "101,1,Standard,100,2,\n"  # exists
        "601,6,Penthouse,100,2,\n"  # unknown type
        "602,6,Standard,12.345,2,\n"  # bad rate
        "602,6,Standard,10,99,\n"  # duplicate + bad capacity
    )
    dry = await client.post("/rooms/import", content=bad, headers={**h, **idem()})
    report = dry.json()
    assert report["valid"] is False
    problems = {(e["line"], e["field"]) for e in report["errors"]}
    assert problems == {
        (2, "room_number"),
        (3, "room_type"),
        (4, "rate"),
        (5, "room_number"),
        (5, "capacity"),
    }
    commit = await client.post(
        "/rooms/import", params={"commit": "true"}, content=bad, headers={**h, **idem()}
    )
    assert commit.status_code == 400
    assert len((await client.get("/rooms", headers=h)).json()["data"]) == 1


async def test_csv_import_rejects_wrong_header(client, factory):
    hotel = await factory.hotel(rooms=0)
    h = {**(await factory.auth(hotel, "general_manager")), "Content-Type": "text/csv"}
    r = await client.post("/rooms/import", content="number,type\n1,Standard\n", headers={**h, **idem()})
    assert r.status_code == 400


def test_parse_rate_is_exact():
    assert parse_rate("1500") == 150000
    assert parse_rate("R 1 850.05") == 185005
    assert parse_rate("0.1") == 10
    assert parse_rate("12.345") is None
    assert parse_rate("-5") is None
    assert parse_rate("1e3") is None


async def test_room_status_rules(client, factory):
    hotel = await factory.hotel(rooms=2)
    h = await factory.auth(hotel, "receptionist")
    room = hotel.room_ids[0]
    ok = await client.post(f"/rooms/{room}/status", json={"status": "cleaning"}, headers=h)
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "cleaning"
    occupied = await client.post(f"/rooms/{room}/status", json={"status": "occupied"}, headers=h)
    assert occupied.status_code == 400  # occupancy comes from check-in only
    await factory.stay_with_folio(hotel, room_index=1)
    blocked = await client.post(
        f"/rooms/{hotel.room_ids[1]}/status", json={"status": "maintenance"}, headers=h
    )
    assert blocked.json()["error"]["code"] == "ROOM_OCCUPIED"


async def test_patch_room_requires_if_match_and_checks_number(client, factory):
    hotel = await factory.hotel(rooms=2)
    h = await factory.auth(hotel, "general_manager")
    room = hotel.room_ids[0]
    missing = await client.patch(f"/rooms/{room}", json={"floor": "1"}, headers=h)
    assert missing.status_code == 412
    taken = await client.patch(f"/rooms/{room}", json={"number": "102"}, headers={**h, "If-Match": '"1"'})
    assert taken.status_code == 400
    ok = await client.patch(
        f"/rooms/{room}", json={"rate": zar(99900), "floor": "1"}, headers={**h, "If-Match": '"1"'}
    )
    assert ok.status_code == 200
    assert ok.json()["effective_rate"] == zar(99900)


async def test_delete_room_needs_step_up_and_no_history(client, factory):
    hotel = await factory.hotel(rooms=2)
    h = await factory.auth(hotel, "general_manager")
    no_step = await client.delete(f"/rooms/{hotel.room_ids[0]}", headers=h)
    assert no_step.json()["error"]["code"] == "STEP_UP_REQUIRED"
    s = await factory.step_up(hotel, "general_manager", h)
    assert (await client.delete(f"/rooms/{hotel.room_ids[0]}", headers=s)).status_code == 204
    assert (await client.get(f"/rooms/{hotel.room_ids[0]}", headers=h)).status_code == 404
    await factory.stay_with_folio(hotel, room_index=1, status="checked_out")
    history = await client.delete(f"/rooms/{hotel.room_ids[1]}", headers=s)
    assert history.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_room_permissions(client, factory):
    hotel = await factory.hotel(rooms=1)
    rec = await factory.auth(hotel, "receptionist")
    ks = await factory.auth(hotel, "kitchen_staff")
    assert (await client.get("/rooms", headers=ks)).json()["error"]["code"] == "PERMISSION_DENIED"
    create = await client.post(
        "/rooms", json={"number": "9", "room_type_id": str(hotel.room_type_id)}, headers={**rec, **idem()}
    )
    assert create.json()["error"]["code"] == "PERMISSION_DENIED"


async def test_rooms_cross_tenant_is_404(client, factory):
    a = await factory.hotel(rooms=1)
    b = await factory.hotel(rooms=1)
    h = await factory.auth(a, "general_manager")
    assert (await client.get(f"/rooms/{b.room_ids[0]}", headers=h)).status_code == 404
    assert (
        await client.post(f"/rooms/{b.room_ids[0]}/status", json={"status": "cleaning"}, headers=h)
    ).status_code == 404
    other_type = await client.post(
        "/rooms", json={"number": "77", "room_type_id": str(b.room_type_id)}, headers={**h, **idem()}
    )
    assert other_type.status_code == 404
    assert [r["id"] for r in (await client.get("/rooms", headers=h)).json()["data"]] == [str(a.room_ids[0])]


async def test_create_room_is_idempotent(client, factory):
    hotel = await factory.hotel(rooms=0)
    h = {**(await factory.auth(hotel, "general_manager")), **idem()}
    body = {"number": "12", "room_type_id": str(hotel.room_type_id)}
    first = await client.post("/rooms", json=body, headers=h)
    again = await client.post("/rooms", json=body, headers=h)
    assert first.status_code == again.status_code == 201
    assert again.headers.get("Idempotent-Replayed") == "true"
    assert first.json()["id"] == again.json()["id"]
