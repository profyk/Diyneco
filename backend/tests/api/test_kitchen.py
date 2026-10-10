"""Kitchen display: PIN sign-in on a paired display, price-free board, accept/start,
item-level readiness across stations, undo, permissions and tenancy."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from tests.factories import PIN


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


def zar(n: int) -> dict:
    return {"amount_minor": n, "currency": "ZAR"}


async def _display(client, gm, station_ids) -> dict[str, str]:
    code = (
        await client.post(
            "/devices/pairings",
            json={"type": "kitchen", "station_ids": [str(s) for s in station_ids]},
            headers={**gm, **idem()},
        )
    ).json()["code"]
    cred = (await client.post("/devices/pair", json={"code": code}, headers=idem())).json()[
        "device_credential"
    ]
    token = (await client.post("/devices/token", json={"device_credential": cred})).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _sign_in(client, display, user) -> dict[str, str]:
    r = await client.post(
        "/auth/kitchen/sign-in", json={"user_id": str(user.user_id), "pin": PIN}, headers=display
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def kitchen_setup(client, factory, *, stations=("Main Kitchen",)):
    hotel = await factory.hotel(rooms=1)
    gm = await factory.auth(hotel, "general_manager")
    station_ids = {"Main Kitchen": hotel.station_id}
    for name in stations:
        if name not in station_ids:
            r = await client.post("/kitchen-stations", json={"name": name}, headers={**gm, **idem()})
            station_ids[name] = uuid.UUID(r.json()["id"])
    cat = (await client.post("/menu/categories", json={"name": "All"}, headers={**gm, **idem()})).json()
    items = {}
    for name, station in zip(("Burger", "Cocktail", "Cake"), stations, strict=False):
        r = await client.post(
            "/menu/items",
            json={
                "name": name,
                "price": zar(10000),
                "station_id": str(station_ids[station]),
                "category_id": cat["id"],
            },
            headers={**gm, **idem()},
        )
        items[name] = r.json()["id"]
    rec = await factory.auth(hotel, "receptionist")
    await client.post(
        f"/rooms/{hotel.room_ids[0]}/walk-in",
        json={"guest": {"name": "G"}, "nights": 1},
        headers={**rec, **idem()},
    )

    async def order(names, total=None):
        lines = [{"menu_item_id": items[n], "quantity": 1} for n in names]
        total = total or 10000 * len(names)
        r = await client.post(
            "/orders",
            json={"room_id": str(hotel.room_ids[0]), "lines": lines, "quoted_total": zar(total)},
            headers={**rec, **idem()},
        )
        assert r.status_code == 201, r.text
        return r.json()

    return hotel, gm, station_ids, order


async def test_order_split_across_three_stations_is_ready_only_when_all_items_are(
    client, factory, owner_engine
):
    """Phase 4 exit criterion."""
    hotel, gm, stations, order = await kitchen_setup(
        client, factory, stations=("Main Kitchen", "Bar", "Dessert Station")
    )
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.hotel_settings SET room_charge_auto_limit_minor = 100000 WHERE hotel_id = :h"),
            {"h": hotel.id},
        )
    placed = await order(["Burger", "Cocktail", "Cake"])
    staff = hotel.users["kitchen_staff"]
    sessions = {}
    for name, sid in stations.items():
        display = await _display(client, gm, [sid])
        sessions[name] = await _sign_in(client, display, staff)
        board = (await client.get("/kitchen/orders", headers=sessions[name])).json()["data"]
        assert [o["id"] for o in board] == [placed["id"]]
        assert "total" not in str(board) and "price" not in str(board) and "amount" not in str(board)
    accepted = await client.post(
        f"/kitchen/orders/{placed['id']}/accept", headers={**sessions["Main Kitchen"], **idem()}
    )
    assert accepted.status_code == 200, accepted.text
    for name in stations:
        r = await client.post(f"/kitchen/orders/{placed['id']}/start", headers={**sessions[name], **idem()})
        assert r.status_code == 200, r.text
    statuses = []
    for name in stations:
        board = (await client.get("/kitchen/orders", headers=sessions[name])).json()["data"][0]
        mine = next(i for i in board["items"] if i["mine"])
        r = await client.post(
            f"/kitchen/order-items/{mine['id']}/ready", headers={**sessions[name], **idem()}
        )
        assert r.status_code == 200, r.text
        statuses.append(r.json()["status"])
    assert statuses == ["PREPARING", "PREPARING", "READY"]
    detail = (await client.get(f"/orders/{placed['id']}", headers=gm)).json()
    assert [h["to_status"] for h in detail["history"]] == ["NEW", "ACCEPTED", "PREPARING", "READY"]
    async with owner_engine.connect() as conn:
        ready = (
            await conn.execute(
                text("SELECT channels FROM app.event_outbox WHERE hotel_id = :h AND type = 'ORDER_READY'"),
                {"h": hotel.id},
            )
        ).scalar_one()
        locked = (
            await conn.execute(text("SELECT locked_at FROM app.orders WHERE id = :o"), {"o": placed["id"]})
        ).scalar_one()
    assert f"hotel:{hotel.id}:room-service" in ready
    assert locked is not None


async def test_device_token_shows_the_board_but_cannot_act(client, factory):
    _hotel, gm, stations, order = await kitchen_setup(client, factory)
    placed = await order(["Burger"])
    display = await _display(client, gm, [stations["Main Kitchen"]])
    board = await client.get("/kitchen/orders", headers=display)
    assert board.status_code == 200 and board.json()["data"][0]["id"] == placed["id"]
    act = await client.post(f"/kitchen/orders/{placed['id']}/accept", headers={**display, **idem()})
    assert act.status_code == 401


async def test_kitchen_session_has_kitchen_permissions_only(client, factory):
    hotel, gm, stations, _order = await kitchen_setup(client, factory)
    display = await _display(client, gm, [stations["Main Kitchen"]])
    km = await _sign_in(client, display, hotel.users["kitchen_manager"])  # also holds menu.manage etc.
    assert (await client.get("/orders", headers=km)).json()["error"]["code"] == "PERMISSION_DENIED"
    assert (await client.get("/menu/items", headers=km)).json()["error"]["code"] == "PERMISSION_DENIED"
    assert (await client.get("/kitchen/orders", headers=km)).status_code == 200


async def test_sign_in_rules(client, factory):
    hotel, gm, stations, _ = await kitchen_setup(client, factory)
    display = await _display(client, gm, [stations["Main Kitchen"]])
    staff = hotel.users["kitchen_staff"]
    wrong = await client.post(
        "/auth/kitchen/sign-in", json={"user_id": str(staff.user_id), "pin": "9999"}, headers=display
    )
    assert (
        wrong.json()["error"]["code"] == "PIN_INVALID"
        and wrong.json()["error"]["details"]["attempts_left"] == 4
    )
    rec = hotel.users["receptionist"]  # no kitchen.view
    no_kitchen = await client.post(
        "/auth/kitchen/sign-in", json={"user_id": str(rec.user_id), "pin": PIN}, headers=display
    )
    assert no_kitchen.json()["error"]["code"] == "PIN_INVALID"
    names = [s["name"] for s in (await client.get("/kitchen/staff", headers=display)).json()["data"]]
    assert "Kitchen Staff" in names and "Receptionist" not in names
    first = await _sign_in(client, display, staff)
    await _sign_in(client, display, hotel.users["kitchen_manager"])
    assert (await client.get("/kitchen/orders", headers=first)).status_code == 401  # replaced on this display
    guest_code = (
        await client.post(
            "/devices/pairings",
            json={"type": "guest", "room_id": str(hotel.room_ids[0])},
            headers={**gm, **idem()},
        )
    ).json()["code"]
    gcred = (await client.post("/devices/pair", json={"code": guest_code}, headers=idem())).json()[
        "device_credential"
    ]
    tablet = {
        "Authorization": f"Bearer {(await client.post('/devices/token', json={'device_credential': gcred})).json()['access_token']}"
    }
    from_tablet = await client.post(
        "/auth/kitchen/sign-in", json={"user_id": str(staff.user_id), "pin": PIN}, headers=tablet
    )
    assert from_tablet.status_code == 401


async def test_disabling_the_display_ends_its_session(client, factory):
    hotel, gm, stations, _ = await kitchen_setup(client, factory)
    display = await _display(client, gm, [stations["Main Kitchen"]])
    session = await _sign_in(client, display, hotel.users["kitchen_staff"])
    device_id = (await client.get("/devices", params={"type": "kitchen"}, headers=gm)).json()["data"][0]["id"]
    await client.post(f"/devices/{device_id}/disable", headers={**gm, **idem()})
    assert (await client.get("/kitchen/orders", headers=session)).status_code in (401, 403)


async def test_transitions_and_undo(client, factory, owner_engine):
    hotel, gm, stations, order = await kitchen_setup(client, factory, stations=("Main Kitchen", "Bar"))
    placed = await order(["Burger", "Cocktail"])
    display = await _display(client, gm, [stations["Main Kitchen"]])
    ks = await _sign_in(client, display, hotel.users["kitchen_staff"])
    early = await client.post(f"/kitchen/orders/{placed['id']}/start", headers={**ks, **idem()})
    assert early.json()["error"]["code"] == "INVALID_TRANSITION"
    await client.post(f"/kitchen/orders/{placed['id']}/accept", headers={**ks, **idem()})
    again = await client.post(f"/kitchen/orders/{placed['id']}/accept", headers={**ks, **idem()})
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"
    await client.post(f"/kitchen/orders/{placed['id']}/start", headers={**ks, **idem()})
    board = (await client.get("/kitchen/orders", headers=ks)).json()["data"][0]
    mine = next(i for i in board["items"] if i["mine"])
    theirs = next(i for i in board["items"] if not i["mine"])
    other_station = await client.post(f"/kitchen/order-items/{theirs['id']}/ready", headers={**ks, **idem()})
    assert other_station.status_code == 404
    await client.post(f"/kitchen/order-items/{mine['id']}/ready", headers={**ks, **idem()})
    undo = await client.post(f"/kitchen/order-items/{mine['id']}/unready", headers={**ks, **idem()})
    assert (
        undo.status_code == 200
        and next(i for i in undo.json()["items"] if i["mine"])["prep_status"] == "PREPARING"
    )
    await client.post(f"/kitchen/order-items/{mine['id']}/ready", headers={**ks, **idem()})
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.order_items SET ready_at = :t WHERE id = :i"),
            {"t": datetime.now(UTC) - timedelta(minutes=3), "i": mine["id"]},
        )
    late = await client.post(f"/kitchen/order-items/{mine['id']}/unready", headers={**ks, **idem()})
    assert late.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_kitchen_cannot_change_amounts_and_order_locks(client, factory, owner_engine):
    hotel, gm, stations, order = await kitchen_setup(client, factory)
    placed = await order(["Burger"])
    display = await _display(client, gm, [stations["Main Kitchen"]])
    ks = await _sign_in(client, display, hotel.users["kitchen_staff"])
    priced = await client.post(
        f"/kitchen/orders/{placed['id']}/accept", json={"total": zar(1)}, headers={**ks, **idem()}
    )
    assert priced.status_code == 200  # no kitchen endpoint reads a body, so amounts cannot be sent
    detail = (await client.get(f"/orders/{placed['id']}", headers=gm)).json()
    assert detail["total"] == zar(10000)
    s = await factory.step_up(hotel, "general_manager", gm)
    await client.post(f"/kitchen/orders/{placed['id']}/start", headers={**ks, **idem()})
    late_cancel = await client.post(
        f"/orders/{placed['id']}/cancel", json={"reason": "late"}, headers={**s, **idem()}
    )
    # Management may cancel while it is being prepared (D67); the charge is reversed.
    assert late_cancel.json()["status"] == "CANCELLED", late_cancel.text


async def test_kitchen_cross_tenant(client, factory):
    _a, _gm_a, _stations_a, order_a = await kitchen_setup(client, factory)
    placed = await order_a(["Burger"])
    b, gm_b, stations_b, _ = await kitchen_setup(client, factory)
    display_b = await _display(client, gm_b, [stations_b["Main Kitchen"]])
    ks_b = await _sign_in(client, display_b, b.users["kitchen_staff"])
    assert (await client.get("/kitchen/orders", headers=ks_b)).json()["data"] == []
    r = await client.post(f"/kitchen/orders/{placed['id']}/accept", headers={**ks_b, **idem()})
    assert r.status_code == 404


async def test_kitchen_staff_mark_dishes_sold_out_from_the_display(client, factory):
    hotel, gm, stations, _order = await kitchen_setup(client, factory)
    display = await _display(client, gm, [stations["Main Kitchen"]])
    cook = await _sign_in(client, display, hotel.users["kitchen_staff"])
    menu = (await client.get("/kitchen/menu", headers=cook)).json()["data"]
    assert menu and all("price" not in m for m in menu)
    burger = next(m for m in menu if m["name"] == "Burger")
    r = await client.post(
        f"/kitchen/menu-items/{burger['id']}/availability", json={"available": False}, headers=cook
    )
    assert r.status_code == 200, r.text
    assert r.json()["is_available"] is False and "price" not in r.json()
    item = (await client.get(f"/menu/items/{burger['id']}", headers=gm)).json()
    assert item["is_available"] is False and item["available_now"] is False
    # The session still cannot read prices or orders.
    assert (await client.get("/menu/items", headers=cook)).json()["error"]["code"] == "PERMISSION_DENIED"
