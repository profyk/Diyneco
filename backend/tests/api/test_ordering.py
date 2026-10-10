"""Guest ordering end to end: paired tablet, active stay, server pricing, room-charge rules,
idempotency, approval, folio posting, cancellation, guest data limited to the active stay."""

from __future__ import annotations

import uuid

from sqlalchemy import text


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


def zar(n: int) -> dict:
    return {"amount_minor": n, "currency": "ZAR"}


async def set_settings(owner_engine, hotel, **values) -> None:
    sets = ", ".join(f"{k} = :{k}" for k in values)
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(f"UPDATE app.hotel_settings SET {sets} WHERE hotel_id = :h"), {"h": hotel.id, **values}
        )


async def setup(client, factory, owner_engine, *, check_in=True, rooms=1, fee=5000):
    hotel = await factory.hotel(rooms=rooms)
    await set_settings(
        owner_engine, hotel, room_service_fee_minor=fee, vat_registered=True, vat_number="4123456789"
    )
    gm = await factory.auth(hotel, "general_manager")
    cat = (await client.post("/menu/categories", json={"name": "Mains"}, headers={**gm, **idem()})).json()
    items = {}
    for name, price, cc in (("Chicken Burger", 14500, "food"), ("Coke", 1000, "beverage")):
        r = await client.post(
            "/menu/items",
            json={
                "name": name,
                "price": zar(price),
                "station_id": str(hotel.station_id),
                "category_id": cat["id"],
                "charge_category": cc,
            },
            headers={**gm, **idem()},
        )
        assert r.status_code == 201, r.text
        items[name] = r.json()["id"]
    code = (
        await client.post(
            "/devices/pairings",
            json={"type": "guest", "room_id": str(hotel.room_ids[0])},
            headers={**gm, **idem()},
        )
    ).json()["code"]
    cred = (await client.post("/devices/pair", json={"code": code}, headers=idem())).json()[
        "device_credential"
    ]
    token = (await client.post("/devices/token", json={"device_credential": cred})).json()["access_token"]
    tablet = {"Authorization": f"Bearer {token}"}
    stay = None
    if check_in:
        rec = await factory.auth(hotel, "receptionist")
        stay = (
            await client.post(
                f"/rooms/{hotel.room_ids[0]}/walk-in",
                json={"guest": {"name": "Guest"}, "nights": 2},
                headers={**rec, **idem()},
            )
        ).json()
    return hotel, gm, tablet, items, stay


def cart(items, burgers=2, cokes=2):
    return [
        {"menu_item_id": items["Chicken Burger"], "quantity": burgers},
        {"menu_item_id": items["Coke"], "quantity": cokes},
    ]


async def test_spec_example_quote_and_place(client, factory, owner_engine):
    """API spec: 2 burgers + 2 cokes = R310 + R50 fee = R360, VAT included R46.96."""
    hotel, _gm, tablet, items, _stay = await setup(client, factory, owner_engine)
    quote = await client.post("/guest/orders/quote", json={"lines": cart(items)}, headers=tablet)
    assert quote.status_code == 200, quote.text
    q = quote.json()
    assert (q["subtotal"], q["fee"], q["total"], q["vat_included"]) == (
        zar(31000),
        zar(5000),
        zar(36000),
        zar(4696),
    )
    assert q["needs_approval"] is False
    order = await client.post(
        "/guest/orders",
        json={"lines": cart(items), "special_instructions": "No onions.", "quoted_total": zar(36000)},
        headers={**tablet, **idem()},
    )
    assert order.status_code == 201, order.text
    body = order.json()
    assert body["status"] == "NEW" and body["room"] == "101" and body["number"] >= 10001
    assert body["vat_included"] == zar(4696)
    folio = (await client.get("/guest/folio", headers=tablet)).json()
    assert folio["totals"]["food_and_beverage"] == zar(36000)
    assert len(folio["food_and_beverage"]) == 3  # two lines and the fee
    async with owner_engine.connect() as conn:
        event = (
            await conn.execute(
                text("SELECT channels FROM app.event_outbox WHERE hotel_id = :h AND type = 'NEW_ORDER'"),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert f"hotel:{hotel.id}:kitchen:{hotel.station_id}" in event


async def test_retrying_an_order_never_duplicates_it(client, factory, owner_engine):
    hotel, _gm, tablet, items, _ = await setup(client, factory, owner_engine)
    h = {**tablet, **idem()}
    body = {"lines": cart(items), "quoted_total": zar(36000)}
    first = await client.post("/guest/orders", json=body, headers=h)
    second = await client.post("/guest/orders", json=body, headers=h)
    assert first.status_code == second.status_code == 201
    assert second.headers.get("Idempotent-Replayed") == "true"
    assert first.json()["id"] == second.json()["id"]
    changed = await client.post("/guest/orders", json={**body, "special_instructions": "x"}, headers=h)
    assert changed.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    async with owner_engine.connect() as conn:
        n = (
            await conn.execute(text("SELECT count(*) FROM app.orders WHERE hotel_id = :h"), {"h": hotel.id})
        ).scalar_one()
        charges = (
            await conn.execute(
                text("SELECT count(*) FROM app.folio_entries WHERE hotel_id = :h AND order_id IS NOT NULL"),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert n == 1 and charges == 3


async def test_price_changed_between_quote_and_order(client, factory, owner_engine):
    _, _, tablet, items, _ = await setup(client, factory, owner_engine)
    r = await client.post(
        "/guest/orders", json={"lines": cart(items), "quoted_total": zar(35000)}, headers={**tablet, **idem()}
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "PRICE_CHANGED"
    assert r.json()["error"]["details"]["quote"]["total"] == zar(36000)


async def test_client_cannot_send_prices(client, factory, owner_engine):
    _, _, tablet, items, _ = await setup(client, factory, owner_engine)
    lines = [{"menu_item_id": items["Coke"], "quantity": 1, "unit_price": zar(1)}]
    r = await client.post("/guest/orders/quote", json={"lines": lines}, headers=tablet)
    assert r.status_code == 400


async def test_over_limit_waits_for_approval_then_posts(client, factory, owner_engine):
    hotel, gm, tablet, items, _stay = await setup(client, factory, owner_engine)  # limit R500
    big = cart(items, burgers=4, cokes=0)[:1]  # 4 x R145 + R50 = R630
    order = (
        await client.post(
            "/guest/orders", json={"lines": big, "quoted_total": zar(63000)}, headers={**tablet, **idem()}
        )
    ).json()
    assert order["status"] == "PENDING_APPROVAL"
    folio = (await client.get("/guest/folio", headers=tablet)).json()
    assert folio["totals"]["food_and_beverage"] == zar(0)
    no_step = await client.post(f"/orders/{order['id']}/approve", headers={**gm, **idem()})
    assert no_step.json()["error"]["code"] == "STEP_UP_REQUIRED"
    s = await factory.step_up(hotel, "general_manager", gm)
    approved = await client.post(f"/orders/{order['id']}/approve", headers={**s, **idem()})
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "NEW"
    assert [h["to_status"] for h in approved.json()["history"]] == ["PENDING_APPROVAL", "NEW"]
    folio = (await client.get("/guest/folio", headers=tablet)).json()
    assert folio["totals"]["food_and_beverage"] == zar(63000)


async def test_decline_needs_reason_and_posts_nothing(client, factory, owner_engine):
    _hotel, gm, tablet, items, _ = await setup(client, factory, owner_engine)
    big = cart(items, burgers=4, cokes=0)[:1]
    order = (
        await client.post(
            "/guest/orders", json={"lines": big, "quoted_total": zar(63000)}, headers={**tablet, **idem()}
        )
    ).json()
    empty = await client.post(
        f"/orders/{order['id']}/decline", json={"reason": " "}, headers={**gm, **idem()}
    )
    assert empty.json()["error"]["code"] == "REASON_REQUIRED"
    declined = await client.post(
        f"/orders/{order['id']}/decline", json={"reason": "Kitchen closed"}, headers={**gm, **idem()}
    )
    assert declined.json()["status"] == "DECLINED"
    mine = (await client.get(f"/guest/orders/{order['id']}", headers=tablet)).json()
    assert mine["decline_reason"] == "Kitchen closed"


async def test_cancel_reverses_folio_charges(client, factory, owner_engine):
    hotel, gm, tablet, items, _ = await setup(client, factory, owner_engine)
    order = (
        await client.post(
            "/guest/orders",
            json={"lines": cart(items), "quoted_total": zar(36000)},
            headers={**tablet, **idem()},
        )
    ).json()
    s = await factory.step_up(hotel, "general_manager", gm)
    cancelled = await client.post(
        f"/orders/{order['id']}/cancel", json={"reason": "Guest changed mind"}, headers={**s, **idem()}
    )
    assert cancelled.status_code == 200, cancelled.text
    folio = (await client.get("/guest/folio", headers=tablet)).json()
    assert folio["totals"]["food_and_beverage"] == zar(0)
    again = await client.post(
        f"/orders/{order['id']}/cancel", json={"reason": "again"}, headers={**s, **idem()}
    )
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_room_charge_rules(client, factory, owner_engine):
    hotel, _gm, tablet, items, stay = await setup(client, factory, owner_engine)
    body = {"lines": cart(items), "quoted_total": zar(36000)}
    rec = await factory.auth(hotel, "receptionist")
    await client.post(f"/stays/{stay['id']}/block-charges", headers=rec)
    blocked = await client.post("/guest/orders", json=body, headers={**tablet, **idem()})
    assert blocked.json()["error"]["code"] == "STAY_BLOCKED"
    await client.post(f"/stays/{stay['id']}/unblock-charges", headers=rec)
    await set_settings(owner_engine, hotel, room_charging_enabled=False)
    off = await client.post("/guest/orders", json=body, headers={**tablet, **idem()})
    assert off.json()["error"]["code"] == "ROOM_CHARGE_DISABLED"
    await set_settings(owner_engine, hotel, room_charging_enabled=True)
    too_big = await client.post(
        "/guest/orders/quote",
        json={"lines": [{"menu_item_id": items["Coke"], "quantity": 100}]},
        headers=tablet,
    )
    assert too_big.json()["error"]["code"] == "ORDER_TOO_LARGE"
    km = await factory.auth(hotel, "kitchen_manager")
    await client.post(f"/menu/items/{items['Coke']}/availability", json={"available": False}, headers=km)
    sold_out = await client.post("/guest/orders/quote", json={"lines": cart(items)}, headers=tablet)
    assert sold_out.json()["error"]["code"] == "ITEM_UNAVAILABLE"


async def test_no_stay_means_welcome_state_and_no_orders(client, factory, owner_engine):
    _hotel, _gm, tablet, items, _ = await setup(client, factory, owner_engine, check_in=False)
    session = (await client.get("/guest/session", headers=tablet)).json()
    assert session["state"] == "idle" and session["stay"] is None and session["ordering_enabled"] is False
    r = await client.post(
        "/guest/orders", json={"lines": cart(items), "quoted_total": zar(36000)}, headers={**tablet, **idem()}
    )
    assert r.json()["error"]["code"] == "NO_ACTIVE_STAY"
    assert (await client.get("/guest/orders", headers=tablet)).json()["data"] == []
    assert (await client.get("/guest/folio", headers=tablet)).json()["error"]["code"] == "NO_ACTIVE_STAY"


async def test_pending_hotel_cannot_take_orders(client, factory, owner_engine):
    hotel, _gm, tablet, items, _ = await setup(client, factory, owner_engine)
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.hotels SET status = 'pending_approval' WHERE id = :h"), {"h": hotel.id}
        )
    r = await client.post(
        "/guest/orders", json={"lines": cart(items), "quoted_total": zar(36000)}, headers={**tablet, **idem()}
    )
    assert r.json()["error"]["code"] == "ROOM_CHARGE_DISABLED"
    assert r.json()["error"]["details"]["reason"] == "hotel_pending_approval"


async def test_guest_menu_session_and_info(client, factory, owner_engine):
    hotel, _gm, tablet, _items, _ = await setup(client, factory, owner_engine)
    session = (await client.get("/guest/session", headers=tablet)).json()
    assert session["state"] == "active" and session["ordering_enabled"] is True
    assert session["room"]["number"] == "101"
    assert "name" not in (session["stay"] or {})
    menu = (await client.get("/guest/menu", headers=tablet)).json()
    names = [i["name"] for c in menu["categories"] for i in c["items"]]
    assert set(names) == {"Chicken Burger", "Coke"}
    info = (await client.get("/guest/info", headers=tablet)).json()
    assert info["hotel_name"] == hotel.name


async def test_staff_phone_order_and_order_list(client, factory, owner_engine):
    hotel, _gm, _tablet, items, _ = await setup(client, factory, owner_engine)
    rec = await factory.auth(hotel, "receptionist")
    r = await client.post(
        "/orders",
        json={"room_id": str(hotel.room_ids[0]), "lines": cart(items, 1, 1), "quoted_total": zar(20500)},
        headers={**rec, **idem()},
    )
    assert r.status_code == 201, r.text
    listed = (await client.get("/orders", headers=rec)).json()["data"]
    assert listed[0]["placed_by"] == "staff" and listed[0]["total"] == zar(20500)
    ks = await factory.auth(hotel, "kitchen_staff")
    assert (await client.get("/orders", headers=ks)).json()["error"]["code"] == "PERMISSION_DENIED"


async def test_new_guest_never_sees_previous_guests_orders(client, factory, owner_engine):
    hotel, gm, tablet, items, stay = await setup(client, factory, owner_engine)
    order = (
        await client.post(
            "/guest/orders",
            json={"lines": cart(items), "quoted_total": zar(36000)},
            headers={**tablet, **idem()},
        )
    ).json()
    # End the stay directly (checkout itself arrives in Phase 6) and check a new guest in.
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.stays SET status = 'checked_out' WHERE id = :s"), {"s": stay["id"]}
        )
        await conn.execute(
            text("UPDATE app.rooms SET status = 'available' WHERE id = :r"), {"r": hotel.room_ids[0]}
        )
    rec = await factory.auth(hotel, "receptionist")
    await client.post(
        f"/rooms/{hotel.room_ids[0]}/walk-in",
        json={"guest": {"name": "Next"}, "nights": 1},
        headers={**rec, **idem()},
    )
    assert (await client.get("/guest/orders", headers=tablet)).json()["data"] == []
    assert (await client.get(f"/guest/orders/{order['id']}", headers=tablet)).status_code == 404
    assert (await client.get("/guest/folio", headers=tablet)).json()["totals"]["food_and_beverage"] == zar(0)
    assert (await client.get(f"/orders/{order['id']}", headers=gm)).status_code == 200  # history kept


async def test_tablet_cannot_order_for_another_room_or_hotel(client, factory, owner_engine):
    _hotel, _gm, tablet, items, _ = await setup(client, factory, owner_engine)
    sneaky = {"lines": cart(items), "quoted_total": zar(36000), "room_id": str(uuid.uuid4())}
    assert (await client.post("/guest/orders", json=sneaky, headers={**tablet, **idem()})).status_code == 400
    other, _, _, _, _ = await setup(client, factory, owner_engine)
    other_gm = await factory.auth(other, "general_manager")
    order = (
        await client.post(
            "/guest/orders",
            json={"lines": cart(items), "quoted_total": zar(36000)},
            headers={**tablet, **idem()},
        )
    ).json()
    assert (await client.get(f"/orders/{order['id']}", headers=other_gm)).status_code == 404


async def test_staff_quote_then_phone_order(client, factory, owner_engine):
    hotel, _gm, _tablet, items, _stay = await setup(client, factory, owner_engine)
    rec = await factory.auth(hotel, "receptionist")
    lines = cart(items, burgers=1, cokes=1)
    quote = await client.post(
        "/orders/quote", json={"room_id": str(hotel.room_ids[0]), "lines": lines}, headers=rec
    )
    assert quote.status_code == 200, quote.text
    placed = await client.post(
        "/orders",
        json={"room_id": str(hotel.room_ids[0]), "lines": lines, "quoted_total": quote.json()["total"]},
        headers={**rec, **idem()},
    )
    assert placed.status_code == 201, placed.text
    assert placed.json()["total"] == quote.json()["total"]
    other = await factory.hotel(rooms=1)
    stranger = await factory.auth(other, "receptionist")
    r = await client.post(
        "/orders/quote", json={"room_id": str(hotel.room_ids[0]), "lines": lines}, headers=stranger
    )
    assert r.status_code in (404, 422)
