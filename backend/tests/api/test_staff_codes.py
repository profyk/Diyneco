"""Staff codes (D82): a manager issues an 8-digit code; the member signs in to room service
with the Hotel ID, the code and their PIN. Codes are per hotel, replaceable and removable;
roles that must use two-step sign-in never get one."""

from __future__ import annotations

import re

from sqlalchemy import text

from tests.factories import PIN


async def _issue(client, factory, hotel, role="room_service_staff", by="general_manager"):
    manager = await factory.step_up(hotel, by, await factory.auth(hotel, by))
    r = await client.post(f"/staff/{hotel.users[role].user_id}/staff-code", headers=manager)
    return manager, r


def _login(hotel_code: str, staff_code: str, pin: str = PIN) -> dict[str, str]:
    return {"hotel_code": hotel_code, "staff_code": staff_code, "pin": pin}


async def test_issue_and_sign_in(client, factory):
    hotel = await factory.hotel(rooms=1)
    manager, r = await _issue(client, factory, hotel)
    assert r.status_code == 201, r.text
    issued = r.json()
    assert re.fullmatch(r"\d{8}", issued["staff_code"])
    assert re.fullmatch(r"DYN-[0-9A-HJKMNP-TV-Z]{13}", issued["hotel_code"])

    signed = await client.post(
        "/auth/staff-code/login", json=_login(issued["hotel_code"], issued["staff_code"])
    )
    assert signed.status_code == 200, signed.text
    assert signed.json()["mfa_enrolment_required"] is False
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {signed.json()['access_token']}"})
    assert me.json()["user"]["id"] == str(hotel.users["room_service_staff"].user_id)
    assert me.json()["hotel"]["code"] == issued["hotel_code"]
    assert me.json()["permissions"] and "staff.manage" not in me.json()["permissions"]

    listed = {s["user_id"]: s for s in (await client.get("/staff", headers=manager)).json()["data"]}
    assert listed[str(hotel.users["room_service_staff"].user_id)]["has_staff_code"] is True
    assert listed[str(hotel.users["receptionist"].user_id)]["has_staff_code"] is False


async def test_reissue_replaces_and_remove_ends_the_code(client, factory):
    hotel = await factory.hotel(rooms=1)
    manager, first = await _issue(client, factory, hotel)
    _, second = await _issue(client, factory, hotel)
    old = await client.post(
        "/auth/staff-code/login", json=_login(first.json()["hotel_code"], first.json()["staff_code"])
    )
    if first.json()["staff_code"] != second.json()["staff_code"]:
        assert old.status_code == 401 and old.json()["error"]["code"] == "UNAUTHENTICATED"
    user_id = hotel.users["room_service_staff"].user_id
    assert (await client.delete(f"/staff/{user_id}/staff-code", headers=manager)).status_code == 204
    gone = await client.post(
        "/auth/staff-code/login", json=_login(second.json()["hotel_code"], second.json()["staff_code"])
    )
    assert gone.status_code == 401
    again = await client.delete(f"/staff/{user_id}/staff-code", headers=manager)
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_wrong_pin_counts_against_the_pin_and_wrong_hotel_finds_nothing(client, factory):
    hotel, other = await factory.hotel(rooms=1), await factory.hotel(rooms=1)
    _, r = await _issue(client, factory, hotel)
    issued = r.json()
    wrong_pin = await client.post(
        "/auth/staff-code/login", json=_login(issued["hotel_code"], issued["staff_code"], "9999")
    )
    assert wrong_pin.status_code == 403 and wrong_pin.json()["error"]["code"] == "PIN_INVALID"
    assert wrong_pin.json()["error"]["details"]["attempts_left"] == 4

    _, r_other = await _issue(client, factory, other)
    crossed = await client.post(
        "/auth/staff-code/login", json=_login(r_other.json()["hotel_code"], issued["staff_code"])
    )
    if issued["staff_code"] != r_other.json()["staff_code"]:
        assert crossed.status_code == 401 and crossed.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_wrong_codes_lock_the_ip(client, factory):
    hotel = await factory.hotel(rooms=1)
    _, r = await _issue(client, factory, hotel)
    issued = r.json()
    wrong = "00000000" if issued["staff_code"] != "00000000" else "11111111"
    for _ in range(10):
        bad = await client.post("/auth/staff-code/login", json=_login(issued["hotel_code"], wrong))
        assert bad.json()["error"]["code"] in ("UNAUTHENTICATED", "RATE_LIMITED")
    locked = await client.post(
        "/auth/staff-code/login", json=_login(issued["hotel_code"], issued["staff_code"])
    )
    assert locked.status_code == 429 and locked.json()["error"]["code"] == "RATE_LIMITED"


async def test_two_step_roles_never_get_a_code(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    _, gm = await _issue(client, factory, hotel, role="general_manager", by="hotel_owner")
    assert gm.json()["error"]["code"] == "INVALID_TRANSITION"

    # Someone who already has a code and is then promoted signs in with email instead.
    _, r = await _issue(client, factory, hotel)
    owner = await factory.step_up(hotel, "hotel_owner", await factory.auth(hotel, "hotel_owner"))
    roles = (await client.get("/roles", headers=owner)).json()["data"]
    finance = next(x["id"] for x in roles if x["code"] == "finance_manager")
    member = hotel.users["room_service_staff"].user_id
    promoted = await client.put(f"/staff/{member}/roles", json={"role_ids": [finance]}, headers=owner)
    assert promoted.status_code == 200, promoted.text
    refused = await client.post(
        "/auth/staff-code/login", json=_login(r.json()["hotel_code"], r.json()["staff_code"])
    )
    assert refused.status_code == 401 and refused.json()["error"]["details"]["reason"] == "use_email"


async def test_issuing_needs_step_up_and_staff_manage(client, factory):
    hotel = await factory.hotel(rooms=1)
    member = hotel.users["room_service_staff"].user_id
    no_step = await client.post(
        f"/staff/{member}/staff-code", headers=await factory.auth(hotel, "general_manager")
    )
    assert no_step.json()["error"]["code"] == "STEP_UP_REQUIRED"
    staff = await factory.step_up(hotel, "receptionist", await factory.auth(hotel, "receptionist"))
    denied = await client.post(f"/staff/{member}/staff-code", headers=staff)
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"


async def test_deactivating_removes_the_code(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    manager, r = await _issue(client, factory, hotel)
    member = hotel.users["room_service_staff"].user_id
    assert (await client.post(f"/staff/{member}/deactivate", headers=manager)).status_code == 200
    async with owner_engine.begin() as conn:
        left = (
            await conn.execute(
                text("SELECT staff_code_hash FROM app.hotel_users WHERE id = :h"),
                {"h": hotel.users["room_service_staff"].hotel_user_id},
            )
        ).scalar_one()
    assert left is None
    after = await client.post(
        "/auth/staff-code/login", json=_login(r.json()["hotel_code"], r.json()["staff_code"])
    )
    assert after.status_code == 401


async def test_hotel_id_never_changes(owner_engine, factory):
    hotel = await factory.hotel(rooms=1)
    async with owner_engine.connect() as conn:
        code = (
            await conn.execute(text("SELECT code FROM app.hotels WHERE id = :h"), {"h": hotel.id})
        ).scalar_one()
        assert re.fullmatch(r"DYN-[0-9A-HJKMNP-TV-Z]{13}", code)
        try:
            await conn.execute(
                text("UPDATE app.hotels SET code = 'DYN-ZZZZZZZZZZZZZ' WHERE id = :h"), {"h": hotel.id}
            )
        except Exception as exc:
            assert "never changes" in str(exc)
        else:
            raise AssertionError("the Hotel ID changed")
