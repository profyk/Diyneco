"""Devices: pairing, credentials, tokens, heartbeat, lock/reset/disable, reassign, unpair."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import text

from tests.factories import pair_body


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


async def _code(client, headers, room_id) -> dict:
    r = await client.post(
        "/devices/pairings", json={"type": "guest", "room_id": str(room_id)}, headers={**headers, **idem()}
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert re.fullmatch(r"\d{8}", body["code"])
    assert re.fullmatch(r"DYN-[0-9A-HJKMNP-TV-Z]{13}", body["hotel_code"])
    assert body["qr_payload"] == f"diyneco:pair:{body['hotel_code']}:{body['code']}"
    return body


async def _paired(client, factory, hotel, room_index=0):
    gm = await factory.auth(hotel, "general_manager")
    code = await _code(client, gm, hotel.room_ids[room_index])
    r = await client.post(
        "/devices/pair",
        json=pair_body(code, device_info={"model": "Tab A9", "os": "Android 14"}),
        headers=idem(),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    tok = await client.post("/devices/token", json={"device_credential": body["device_credential"]})
    assert tok.status_code == 200, tok.text
    return gm, body, {"Authorization": f"Bearer {tok.json()['access_token']}"}


async def test_pair_issue_token_and_heartbeat(client, factory):
    hotel = await factory.hotel(rooms=1)
    gm, body, device = await _paired(client, factory, hotel)
    assert body["room"]["number"] == "101"
    assert body["label"] == "DY-101-01"
    assert body["device_credential"].startswith("dvc_")
    hb = await client.post("/devices/heartbeat", json={"app_version": "1.0.0", "battery": 80}, headers=device)
    assert hb.status_code == 200, hb.text
    assert hb.json()["commands"] == []
    listed = (await client.get("/devices", headers=gm)).json()["data"]
    assert [(d["label"], d["status"], d["connection"], d["app_version"]) for d in listed] == [
        ("DY-101-01", "active", "online", "1.0.0")
    ]


async def test_pair_replay_never_returns_the_credential_again(client, factory):
    hotel = await factory.hotel(rooms=1)
    gm = await factory.auth(hotel, "general_manager")
    code = await _code(client, gm, hotel.room_ids[0])
    h = idem()
    first = await client.post("/devices/pair", json=pair_body(code), headers=h)
    replay = await client.post("/devices/pair", json=pair_body(code), headers=h)
    assert first.json()["device_credential"]
    assert replay.headers.get("Idempotent-Replayed") == "true"
    assert replay.json()["device_credential"] is None
    assert replay.json()["device_id"] == first.json()["device_id"]


async def test_code_is_single_use_and_wrong_codes_lock_the_ip(client, factory):
    hotel = await factory.hotel(rooms=2)
    gm = await factory.auth(hotel, "general_manager")
    code = await _code(client, gm, hotel.room_ids[0])
    assert (await client.post("/devices/pair", json=pair_body(code), headers=idem())).status_code == 201
    used = await client.post("/devices/pair", json=pair_body(code), headers=idem())
    assert used.json()["error"]["code"] == "PAIRING_INVALID"
    for _ in range(4):
        wrong = await client.post(
            "/devices/pair", json={**pair_body(code), "code": "00000000"}, headers=idem()
        )
        assert wrong.json()["error"]["code"] == "PAIRING_INVALID"
    good = await _code(client, gm, hotel.room_ids[1])
    locked = await client.post("/devices/pair", json=pair_body(good), headers=idem())
    assert locked.json()["error"]["code"] == "RATE_LIMITED"


async def test_setup_code_works_only_with_its_own_hotel_id(client, factory):
    """D82: the code is looked up only inside the hotel the Hotel ID names."""
    hotel, other = await factory.hotel(rooms=1), await factory.hotel(rooms=1)
    gm = await factory.auth(hotel, "general_manager")
    code = await _code(client, gm, hotel.room_ids[0])
    other_code = await _code(client, await factory.auth(other, "general_manager"), other.room_ids[0])
    assert other_code["hotel_code"] != code["hotel_code"]
    crossed = await client.post(
        "/devices/pair", json={**pair_body(code), "hotel_code": other_code["hotel_code"]}, headers=idem()
    )
    assert crossed.json()["error"]["code"] == "PAIRING_INVALID"
    unknown = await client.post(
        "/devices/pair", json={**pair_body(code), "hotel_code": "DYN-ZZZZZZZZZZZZZ"}, headers=idem()
    )
    assert unknown.json()["error"]["code"] == "PAIRING_INVALID"
    # Typed loosely on a tablet: lower case, spaces, no dash, O for zero all still match.
    loose = code["hotel_code"].lower().replace("-", " ").replace("0", "o")
    ok = await client.post("/devices/pair", json={**pair_body(code), "hotel_code": loose}, headers=idem())
    assert ok.status_code == 201, ok.text


async def test_setup_needs_the_issuing_managers_pin(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    gm = await factory.auth(hotel, "general_manager")
    code = await _code(client, gm, hotel.room_ids[0])
    wrong = await client.post("/devices/pair", json=pair_body(code, pin="9999"), headers=idem())
    assert wrong.status_code == 403 and wrong.json()["error"]["code"] == "PIN_INVALID"
    assert wrong.json()["error"]["details"]["attempts_left"] == 4
    # A wrong PIN does not use up the code.
    right = await client.post("/devices/pair", json=pair_body(code), headers=idem())
    assert right.status_code == 201, right.text

    # Once the manager has lost access, codes they made stop working.
    kitchen = (
        await client.post(
            "/devices/pairings",
            json={"type": "kitchen", "station_id": str(hotel.station_id)},
            headers={**gm, **idem()},
        )
    ).json()
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.hotel_users SET status = 'deactivated' WHERE id = :h"),
            {"h": hotel.users["general_manager"].hotel_user_id},
        )
    gone = await client.post("/devices/pair", json=pair_body(kitchen), headers=idem())
    assert gone.json()["error"]["code"] == "PAIRING_INVALID"


async def test_setup_request_shape(client, factory):
    hotel = await factory.hotel(rooms=1)
    gm = await factory.auth(hotel, "general_manager")
    code = await _code(client, gm, hotel.room_ids[0])
    for bad in (
        {**pair_body(code), "code": code["code"][:6]},  # the old 6-digit codes
        {**pair_body(code), "hotel_code": "not-a-hotel"},
        {k: v for k, v in pair_body(code).items() if k != "pin"},
    ):
        r = await client.post("/devices/pair", json=bad, headers=idem())
        assert r.status_code == 400, r.text


async def test_one_tablet_per_room(client, factory):
    hotel = await factory.hotel(rooms=1)
    gm, _, _ = await _paired(client, factory, hotel)
    again = await client.post(
        "/devices/pairings",
        json={"type": "guest", "room_id": str(hotel.room_ids[0])},
        headers={**gm, **idem()},
    )
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_pairing_request_shape(client, factory):
    hotel = await factory.hotel(rooms=1)
    gm = await factory.auth(hotel, "general_manager")
    both = await client.post(
        "/devices/pairings",
        json={"type": "guest", "room_id": str(hotel.room_ids[0]), "station_id": str(hotel.station_id)},
        headers={**gm, **idem()},
    )
    assert both.status_code == 400
    kitchen = await client.post(
        "/devices/pairings",
        json={"type": "kitchen", "station_id": str(hotel.station_id)},
        headers={**gm, **idem()},
    )
    assert kitchen.status_code == 201
    paired = await client.post("/devices/pair", json=pair_body(kitchen.json()), headers=idem())
    assert paired.status_code == 201, paired.text
    assert paired.json()["room"] is None
    assert [s["name"] for s in paired.json()["stations"]] == ["Main Kitchen"]
    assert paired.json()["label"] == "KITCHEN-01"


async def test_lock_unlock_and_disable(client, factory):
    hotel = await factory.hotel(rooms=1)
    gm, body, device = await _paired(client, factory, hotel)
    did = body["device_id"]
    locked = await client.post(f"/devices/{did}/lock", headers={**gm, **idem()})
    assert locked.status_code == 200, locked.text
    assert locked.json()["status"] == "locked"
    hb = await client.post("/devices/heartbeat", json={}, headers=device)
    assert hb.json()["commands"] == ["LOCK"]
    twice = await client.post(f"/devices/{did}/lock", headers={**gm, **idem()})
    assert twice.json()["error"]["code"] == "INVALID_TRANSITION"
    assert (await client.post(f"/devices/{did}/unlock", headers={**gm, **idem()})).json()[
        "status"
    ] == "active"
    await client.post(f"/devices/{did}/disable", headers={**gm, **idem()})
    blocked = await client.post("/devices/heartbeat", json={}, headers=device)
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "DEVICE_DISABLED"
    no_token = await client.post("/devices/token", json={"device_credential": body["device_credential"]})
    assert no_token.json()["error"]["code"] == "DEVICE_DISABLED"
    await client.post(f"/devices/{did}/unlock", headers={**gm, **idem()})
    assert (await client.post("/devices/heartbeat", json={}, headers=device)).status_code == 200


async def test_reset_emits_event_and_clears_on_ack(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    gm, body, device = await _paired(client, factory, hotel)
    r = await client.post(f"/devices/{body['device_id']}/reset", headers={**gm, **idem()})
    assert r.json()["status"] == "reset_required"
    assert (await client.post("/devices/heartbeat", json={}, headers=device)).json()["commands"] == ["RESET"]
    done = await client.post("/devices/heartbeat", json={"completed_commands": ["RESET"]}, headers=device)
    assert done.json() | {"server_time": None} == {"status": "active", "commands": [], "server_time": None}
    async with owner_engine.connect() as conn:
        events = (
            await conn.execute(
                text("SELECT type, channels FROM app.event_outbox WHERE hotel_id = :h ORDER BY seq"),
                {"h": hotel.id},
            )
        ).all()
    reset = [e for e in events if e.type == "RESET_ROOM_SESSION"]
    assert reset and f"hotel:{hotel.id}:room:{hotel.room_ids[0]}" in reset[0].channels


async def test_reassign_invalidates_old_token(client, factory):
    hotel = await factory.hotel(rooms=2)
    gm, body, device = await _paired(client, factory, hotel)
    no_step = await client.post(
        f"/devices/{body['device_id']}/reassign",
        json={"room_id": str(hotel.room_ids[1])},
        headers={**gm, **idem()},
    )
    assert no_step.json()["error"]["code"] == "STEP_UP_REQUIRED"
    s = await factory.step_up(hotel, "general_manager", gm)
    moved = await client.post(
        f"/devices/{body['device_id']}/reassign",
        json={"room_id": str(hotel.room_ids[1])},
        headers={**s, **idem()},
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["room"]["number"] == "102"
    old = await client.post("/devices/heartbeat", json={}, headers=device)
    assert old.status_code == 401
    assert old.json()["error"]["code"] == "DEVICE_UNAUTHORISED"
    fresh = await client.post("/devices/token", json={"device_credential": body["device_credential"]})
    assert fresh.status_code == 200


async def test_unpair_revokes_credential_and_frees_the_room(client, factory):
    hotel = await factory.hotel(rooms=1)
    gm, body, device = await _paired(client, factory, hotel)
    s = await factory.step_up(hotel, "general_manager", gm)
    gone = await client.delete(f"/devices/{body['device_id']}/pairing", headers={**s, **idem()})
    assert gone.status_code == 204
    assert (await client.post("/devices/heartbeat", json={}, headers=device)).status_code == 401
    token = await client.post("/devices/token", json={"device_credential": body["device_credential"]})
    assert token.json()["error"]["code"] == "DEVICE_UNAUTHORISED"
    assert (await _code(client, gm, hotel.room_ids[0]))["code"].isdigit()  # room can be paired again


async def test_room_with_tablet_cannot_be_deleted(client, factory):
    hotel = await factory.hotel(rooms=1)
    gm, _, _ = await _paired(client, factory, hotel)
    s = await factory.step_up(hotel, "general_manager", gm)
    r = await client.delete(f"/rooms/{hotel.room_ids[0]}", headers=s)
    assert r.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_device_token_is_not_a_staff_token_and_vice_versa(client, factory):
    hotel = await factory.hotel(rooms=1)
    gm, _, device = await _paired(client, factory, hotel)
    assert (await client.get("/rooms", headers=device)).status_code == 401
    assert (await client.post("/devices/heartbeat", json={}, headers=gm)).status_code == 401
    forged = await client.post("/devices/token", json={"device_credential": "dvc_" + "x" * 40})
    assert forged.json()["error"]["code"] == "DEVICE_UNAUTHORISED"


async def test_devices_cross_tenant_and_permissions(client, factory):
    a = await factory.hotel(rooms=1)
    b = await factory.hotel(rooms=1)
    _, body, _ = await _paired(client, factory, a)
    gm_b = await factory.auth(b, "general_manager")
    assert (
        await client.post(f"/devices/{body['device_id']}/lock", headers={**gm_b, **idem()})
    ).status_code == 404
    assert (await client.get("/devices", headers=gm_b)).json()["data"] == []
    other_room = await client.post(
        "/devices/pairings", json={"type": "guest", "room_id": str(a.room_ids[0])}, headers={**gm_b, **idem()}
    )
    assert other_room.status_code == 404
    rec = await factory.auth(a, "receptionist")
    assert (await client.get("/devices", headers=rec)).status_code == 200
    denied = await client.post(f"/devices/{body['device_id']}/lock", headers={**rec, **idem()})
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
