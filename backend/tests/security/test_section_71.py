"""Build spec section 71, Security testing: one test per listed attack, run against the real
API and database (Phase 9 exit criterion). Many of these behaviours are also covered where
they are built; this file is the checklist a reviewer can read top to bottom.

Unauthorized hotel access, cross-tenant API requests, invalid device credentials, expired
sessions, privilege escalation, unauthorized checkout, unauthorized bill modification,
unauthorized discounts, unauthorized payment modification, replay requests, duplicate payment
submissions, duplicate orders.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.jwt import ACCESS_TTL_S
from tests.api.test_billing import laundry, walk_in
from tests.api.test_checkout import settle
from tests.api.test_room_service import idem, ready_order, zar


async def paired_tablet(client, gm, room_id) -> tuple[dict[str, str], str, str]:
    code = (
        await client.post(
            "/devices/pairings", json={"type": "guest", "room_id": str(room_id)}, headers={**gm, **idem()}
        )
    ).json()["code"]
    paired = (await client.post("/devices/pair", json={"code": code}, headers=idem())).json()
    token = (
        await client.post("/devices/token", json={"device_credential": paired["device_credential"]})
    ).json()
    return (
        {"Authorization": f"Bearer {token['access_token']}"},
        paired["device_credential"],
        paired["device_id"],
    )


# 1. Unauthorized hotel access -------------------------------------------------------------


async def test_unauthorized_hotel_access(client, factory, owner_engine):
    a = await factory.hotel(rooms=1)
    b = await factory.hotel(rooms=1)
    gm_a = await factory.auth(a, "general_manager")
    # A token is bound to one hotel; asking for another hotel is "not found", never "forbidden".
    r = await client.get("/hotel", headers={**gm_a, "X-Hotel-Id": str(b.id)})
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"
    # Switching hotels needs a membership there.
    login = await client.post(
        "/auth/login",
        json={
            "email": a.users["general_manager"].email,
            "password": a.users["general_manager"].password,
            "hotel_id": str(b.id),
        },
    )
    assert login.status_code in (401, 404)
    # A deactivated member loses access immediately, even with an unexpired token.
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.hotel_users SET status = 'deactivated' WHERE id = :m"),
            {"m": a.users["general_manager"].hotel_user_id},
        )
    assert (await client.get("/hotel", headers=gm_a)).status_code == 401


# 2. Cross-tenant API requests -------------------------------------------------------------


async def test_cross_tenant_requests_return_not_found(client, factory, owner_engine):
    hotel, gm, order, stay = await ready_order(client, factory, owner_engine)
    _, _, device_id = await paired_tablet(client, gm, hotel.room_ids[0])
    rec = await factory.auth(hotel, "receptionist")
    folio = (await laundry(client, rec, stay["id"], owner_engine)).json()
    entry = next(e for e in folio["entries"] if e["category"] == "laundry")
    rm = await factory.auth(hotel, "reception_manager")
    adj = (
        await client.post(
            "/adjustments",
            json={"folio_entry_id": entry["id"], "new_amount": zar(0), "reason": "Test only"},
            headers={**rm, **idem()},
        )
    ).json()
    other = await factory.hotel(rooms=1)
    attacker = await factory.step_up(other, "general_manager", await factory.auth(other, "general_manager"))
    reads = [
        f"/rooms/{hotel.room_ids[0]}",
        f"/stays/{stay['id']}",
        f"/orders/{order['id']}",
        f"/folios/{stay['id']}",
        f"/devices/{device_id}",
        f"/stays/{stay['id']}/checkout-summary",
    ]
    for path in reads:
        r = await client.get(path, headers=attacker)
        assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND", path
    writes = [
        (f"/orders/{order['id']}/cancel", {"reason": "x"}),
        (f"/adjustments/{adj['id']}/approve", None),
        (
            f"/folios/{stay['id']}/charges",
            {"charge_category_id": entry["id"], "description": "x", "amount": zar(1)},
        ),
        (f"/stays/{stay['id']}/checkout", {}),
        (f"/devices/{device_id}/lock", None),
        (f"/deliveries/{order['id']}/claim", None),
    ]
    for path, body in writes:
        r = await client.post(path, json=body, headers={**attacker, **idem()})
        assert r.status_code == 404, (path, r.text)
    # Nothing changed for the victim hotel.
    assert (await client.get(f"/orders/{order['id']}", headers=gm)).json()["status"] == "READY"


# 3. Invalid device credentials ------------------------------------------------------------


async def test_invalid_device_credentials(client, factory):
    hotel = await factory.hotel(rooms=1)
    gm = await factory.auth(hotel, "general_manager")
    tablet, credential, device_id = await paired_tablet(client, gm, hotel.room_ids[0])
    assert (
        await client.post("/devices/token", json={"device_credential": "dvc_" + "x" * 40})
    ).status_code == 401
    forged = tablet["Authorization"][:-4] + (
        "AAAA" if not tablet["Authorization"].endswith("AAAA") else "BBBB"
    )
    assert (await client.get("/guest/session", headers={"Authorization": forged})).status_code == 401
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    unpaired = await client.delete(f"/devices/{device_id}/pairing", headers={**gm_s, **idem()})
    assert unpaired.status_code == 204, unpaired.text
    assert (await client.get("/guest/session", headers=tablet)).status_code == 401
    assert (await client.post("/devices/token", json={"device_credential": credential})).status_code == 401
    # A staff token is not a device token, and a device token is not a staff token.
    assert (await client.get("/guest/session", headers=gm)).status_code == 401


# 4. Expired sessions ----------------------------------------------------------------------


async def test_expired_and_revoked_sessions(client, factory, app_state):
    hotel = await factory.hotel(roles=("general_manager",))
    user = hotel.users["general_manager"]
    token, _sid = await factory.token(hotel, user)
    claims = app_state.jwt.verify(token, "access")
    expired, _ = app_state.jwt.sign(
        "access",
        {k: v for k, v in claims.items() if k not in ("iat", "exp", "nbf", "iss", "aud", "jti", "typ")},
        -60,
    )
    r = await client.get("/hotel", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401
    headers = {"Authorization": f"Bearer {token}"}
    assert (await client.get("/hotel", headers=headers)).status_code == 200
    out = await client.post("/auth/logout", headers=headers)
    assert out.status_code == 204, out.text
    assert (await client.get("/hotel", headers=headers)).status_code == 401  # revoked before it expired
    assert ACCESS_TTL_S <= 15 * 60


# 5. Privilege escalation ------------------------------------------------------------------


async def test_privilege_escalation_is_refused(client, factory):
    hotel = await factory.hotel()
    rec = await factory.step_up(hotel, "receptionist", await factory.auth(hotel, "receptionist"))
    me = hotel.users["receptionist"].user_id
    roles = (await client.get("/roles", headers=await factory.auth(hotel, "hotel_owner"))).json()["data"]
    gm_role = next(r for r in roles if r.get("code") == "general_manager")
    r = await client.put(f"/staff/{me}/roles", json={"role_ids": [gm_role["id"]]}, headers=rec)
    assert r.status_code == 403
    r = await client.post(
        "/roles", json={"name": "Super", "permissions": ["folio.adjust.approve"]}, headers={**rec, **idem()}
    )
    assert r.status_code == 403
    # A manager cannot hand out a permission they do not hold either.
    gm = await factory.step_up(hotel, "general_manager", await factory.auth(hotel, "general_manager"))
    own = await client.post(
        "/roles", json={"name": "Owner-ish", "permissions": ["subscription.manage"]}, headers={**gm, **idem()}
    )
    assert own.status_code == 403
    # Nobody changes their own access.
    owner = await factory.step_up(hotel, "hotel_owner", await factory.auth(hotel, "hotel_owner"))
    self_change = await client.put(
        f"/staff/{hotel.users['hotel_owner'].user_id}/roles",
        json={"role_ids": [gm_role["id"]]},
        headers=owner,
    )
    assert self_change.status_code == 403


# 6. Unauthorized checkout -----------------------------------------------------------------


async def test_unauthorized_checkout(client, factory):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel)
    await settle(client, factory, hotel, stay["id"])
    for role in ("room_service_staff", "kitchen_manager", "finance_manager"):
        h = await factory.step_up(hotel, role, await factory.auth(hotel, role))
        r = await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**h, **idem()})
        assert r.json()["error"]["code"] == "PERMISSION_DENIED", role
    rec = await factory.auth(hotel, "receptionist")
    r = await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**rec, **idem()})
    assert r.json()["error"]["code"] == "STEP_UP_REQUIRED"
    assert (await client.get(f"/stays/{stay['id']}", headers=rec)).json()["status"] == "active"


# 7. Unauthorized bill modification --------------------------------------------------------


async def test_unauthorized_bill_modification(client, factory, owner_engine, api_engine):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel)
    rec = await factory.auth(hotel, "receptionist")
    folio = (await laundry(client, rec, stay["id"], owner_engine)).json()
    entry = next(e for e in folio["entries"] if e["category"] == "laundry")
    req = (
        await client.post(
            "/adjustments",
            json={"folio_entry_id": entry["id"], "new_amount": zar(0), "reason": "Remove it"},
            headers={**rec, **idem()},
        )
    ).json()
    rec_s = await factory.step_up(hotel, "receptionist", rec)
    assert (
        await client.post(f"/adjustments/{req['id']}/approve", headers={**rec_s, **idem()})
    ).status_code == 403
    # No endpoint edits or deletes a folio entry, and the database refuses it outright.
    async with api_engine.connect() as conn:
        for sql in (
            "UPDATE app.folio_entries SET amount_minor = 0, unit_amount_minor = 0 WHERE id = :e",
            "DELETE FROM app.folio_entries WHERE id = :e",
        ):
            async with conn.begin():
                await conn.execute(text("SELECT set_config('app.hotel_id', :h, true)"), {"h": str(hotel.id)})
                with pytest.raises(DBAPIError):
                    await conn.execute(text(sql), {"e": entry["id"]})
                await conn.rollback()
    after = (await client.get(f"/folios/{stay['id']}", headers=rec)).json()
    assert after["totals"]["other"] == zar(10000)


# 8. Unauthorized discounts ----------------------------------------------------------------


async def test_unauthorized_discounts(client, factory):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel)
    body = {"kind": "percent", "percent_bp": 10000, "applies_to": "all", "reason": "Friend"}
    # Discounts are for managers and finance only (security spec role matrix).
    for role in ("receptionist", "room_service_staff", "kitchen_manager"):
        h = await factory.step_up(hotel, role, await factory.auth(hotel, role))
        r = await client.post(f"/folios/{stay['id']}/discounts", json=body, headers={**h, **idem()})
        assert r.json()["error"]["code"] in ("PERMISSION_DENIED",), role
    gm = await factory.auth(hotel, "general_manager")
    r = await client.post(f"/folios/{stay['id']}/discounts", json=body, headers={**gm, **idem()})
    assert r.json()["error"]["code"] == "STEP_UP_REQUIRED"
    assert (await client.get(f"/folios/{stay['id']}", headers=gm)).json()["totals"]["accommodation"] == zar(
        300000
    )


# 9. Unauthorized payment modification -----------------------------------------------------


async def test_unauthorized_payment_modification(client, factory, owner_engine, api_engine, app):
    hotel, gm, order, _stay = await ready_order(client, factory, owner_engine)
    ss = await factory.auth(hotel, "room_service_staff")
    for step in ("claim", "picked-up", "delivered"):
        await client.post(f"/deliveries/{order['id']}/{step}", headers={**ss, **idem()})
    # Someone else's delivery cannot be paid by another room-service member.
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.deliveries SET assigned_to = :u WHERE order_id = :o"),
            {
                "u": hotel.users["general_manager"].user_id,
                "o": order["id"],
            },
        )
    other_staff = await client.post(
        "/payments",
        json={"order_id": order["id"], "method": "cash", "amount_received": zar(300000)},
        headers={**ss, **idem()},
    )
    assert other_staff.status_code == 403, other_staff.text
    assert other_staff.json()["error"]["code"] == "PERMISSION_DENIED"
    paid = await client.post(
        "/payments",
        json={"order_id": order["id"], "method": "cash", "amount_received": zar(300000)},
        headers={**gm, **idem()},
    )
    assert paid.status_code == 201, paid.text
    payment_id = paid.json()["id"]
    # There is no route that edits or deletes a payment.
    methods = {
        m
        for r in app.routes
        for m in (getattr(r, "methods", None) or ())
        if "/payments/" in getattr(r, "path", "")
    }
    assert not methods & {"PUT", "PATCH", "DELETE"}
    for verb in ("put", "patch", "delete"):
        r = await client.request(verb.upper(), f"/payments/{payment_id}", headers=gm)
        assert r.status_code in (404, 405)
    # And the database refuses it.
    async with api_engine.connect() as conn, conn.begin():
        await conn.execute(text("SELECT set_config('app.hotel_id', :h, true)"), {"h": str(hotel.id)})
        with pytest.raises(DBAPIError):
            await conn.execute(
                text("UPDATE app.payments SET amount_received_minor = 1 WHERE id = :p"), {"p": payment_id}
            )
        await conn.rollback()


# 10. Replay requests ----------------------------------------------------------------------


async def test_replayed_requests(client, factory, owner_engine, app_state):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel)
    rec = await factory.auth(hotel, "receptionist")
    key = idem()
    body = {"charge_category_id": None, "description": "Laundry", "amount": zar(5000)}
    async with owner_engine.connect() as conn:
        body["charge_category_id"] = str(
            (
                await conn.execute(
                    text("SELECT id FROM app.charge_categories WHERE hotel_id IS NULL AND code = 'laundry'")
                )
            ).scalar_one()
        )
    first = await client.post(f"/folios/{stay['id']}/charges", json=body, headers={**rec, **key})
    replay = await client.post(f"/folios/{stay['id']}/charges", json=body, headers={**rec, **key})
    assert replay.headers.get("Idempotent-Replayed") == "true" and replay.json() == first.json()
    changed = await client.post(
        f"/folios/{stay['id']}/charges", json={**body, "amount": zar(9999)}, headers={**rec, **key}
    )
    assert changed.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    other_user = await factory.auth(hotel, "reception_manager")
    stolen_key = await client.post(f"/folios/{stay['id']}/charges", json=body, headers={**other_user, **key})
    assert stolen_key.headers.get("Idempotent-Replayed") != "true"  # keys are per principal
    entries = (await client.get(f"/folios/{stay['id']}", headers=rec)).json()["entries"]
    assert sum(1 for e in entries if e["category"] == "laundry") == 2  # rec's once, the manager's once
    # A step-up token is bound to the session that asked for it.
    gm = await factory.auth(hotel, "general_manager")
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    gm_other_session = await factory.auth(hotel, "general_manager")
    borrowed = {**gm_other_session, "X-Step-Up": gm_s["X-Step-Up"]}
    r = await client.post(
        f"/folios/{stay['id']}/discounts",
        json={"kind": "fixed", "amount": zar(100), "applies_to": "all", "reason": "x"},
        headers={**borrowed, **idem()},
    )
    assert r.json()["error"]["code"] == "STEP_UP_REQUIRED"
    assert app_state is not None


# 11. Duplicate payment submissions --------------------------------------------------------


async def test_duplicate_payment_submissions(client, factory, owner_engine):
    hotel, _gm, order, _stay = await ready_order(client, factory, owner_engine)
    ss = await factory.auth(hotel, "room_service_staff")
    for step in ("claim", "picked-up", "delivered"):
        await client.post(f"/deliveries/{order['id']}/{step}", headers={**ss, **idem()})
    body = {"order_id": order["id"], "method": "cash", "amount_received": zar(300000)}
    key = idem()
    first = await client.post("/payments", json=body, headers={**ss, **key})
    again_same_key = await client.post("/payments", json=body, headers={**ss, **key})
    again_new_key = await client.post("/payments", json=body, headers={**ss, **idem()})
    assert first.status_code == 201
    assert again_same_key.json()["id"] == first.json()["id"]
    assert again_new_key.json()["error"]["code"] == "ALREADY_PAID"
    async with owner_engine.connect() as conn:
        n = (
            await conn.execute(
                text("SELECT count(*) FROM app.payments WHERE order_id = :o"), {"o": order["id"]}
            )
        ).scalar_one()
    assert n == 1


# 12. Duplicate orders ---------------------------------------------------------------------


async def test_duplicate_orders(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    gm = await factory.auth(hotel, "general_manager")
    cat = (await client.post("/menu/categories", json={"name": "Mains"}, headers={**gm, **idem()})).json()
    item = (
        await client.post(
            "/menu/items",
            json={
                "name": "Burger",
                "price": zar(14500),
                "station_id": str(hotel.station_id),
                "category_id": cat["id"],
            },
            headers={**gm, **idem()},
        )
    ).json()
    tablet, _, _ = await paired_tablet(client, gm, hotel.room_ids[0])
    await walk_in(client, factory, hotel)
    body = {"lines": [{"menu_item_id": item["id"], "quantity": 2}], "quoted_total": zar(29000)}
    key = idem()
    responses = [await client.post("/guest/orders", json=body, headers={**tablet, **key}) for _ in range(3)]
    assert len({r.json()["id"] for r in responses}) == 1
    assert [r.headers.get("Idempotent-Replayed") for r in responses] == [None, "true", "true"]
    async with owner_engine.connect() as conn:
        n = (
            await conn.execute(text("SELECT count(*) FROM app.orders WHERE hotel_id = :h"), {"h": hotel.id})
        ).scalar_one()
        posted = (
            await conn.execute(
                text("SELECT count(*) FROM app.folio_entries WHERE hotel_id = :h AND order_id IS NOT NULL"),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert n == 1 and posted == 1
