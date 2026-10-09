"""Kitchen stations and menu admin: schedules, categories, items, prices, modifiers."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.services.schedules import is_open, next_open


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


def zar(n: int) -> dict:
    return {"amount_minor": n, "currency": "ZAR"}


async def _category(client, h, name="Mains", schedule_id=None) -> dict:
    body = {"name": name}
    if schedule_id:
        body["schedule_id"] = schedule_id
    r = await client.post("/menu/categories", json=body, headers={**h, **idem()})
    assert r.status_code == 201, r.text
    return r.json()


async def _item(client, h, hotel, category_id, **extra) -> dict:
    body = {
        "name": "Chicken Burger",
        "description": "Chicken breast, cheese, lettuce and sauce.",
        "price": zar(14500),
        "station_id": str(hotel.station_id),
        "category_id": category_id,
        "allergens": ["gluten", "dairy"],
        **extra,
    }
    r = await client.post("/menu/items", json=body, headers={**h, **idem()})
    assert r.status_code == 201, r.text
    return r.json()


def test_schedule_windows():
    breakfast = [{"days": [1, 2, 3, 4, 5], "from": "06:00", "to": "11:00"}]
    monday_7 = datetime(2026, 10, 5, 7, 0)
    assert is_open(breakfast, monday_7)
    assert not is_open(breakfast, datetime(2026, 10, 5, 11, 0))
    assert not is_open(breakfast, datetime(2026, 10, 10, 7, 0))  # Saturday
    assert next_open(breakfast, datetime(2026, 10, 9, 12, 0)) == datetime(2026, 10, 12, 6, 0)
    late = [{"days": [5], "from": "22:00", "to": "02:00"}]
    assert is_open(late, datetime(2026, 10, 10, 1, 30))  # Friday's window, Saturday 01:30
    assert not is_open(late, datetime(2026, 10, 11, 1, 30))
    assert is_open([{"days": [1, 2, 3, 4, 5, 6, 7], "from": "00:00", "to": "00:00"}], monday_7)
    assert is_open(None, monday_7)


async def test_stations_crud_and_delete_rules(client, factory):
    hotel = await factory.hotel(rooms=0)
    km = await factory.auth(hotel, "kitchen_manager")
    bar = await client.post(
        "/kitchen-stations", json={"name": "Bar", "sort_order": 2}, headers={**km, **idem()}
    )
    assert bar.status_code == 201, bar.text
    dup = await client.post("/kitchen-stations", json={"name": "Bar"}, headers={**km, **idem()})
    assert dup.status_code == 400
    names = [s["name"] for s in (await client.get("/kitchen-stations", headers=km)).json()["data"]]
    assert names == ["Main Kitchen", "Bar"]
    category = await _category(client, km)
    await _item(client, km, hotel, category["id"])
    busy = await client.delete(f"/kitchen-stations/{hotel.station_id}", headers=km)
    assert busy.json()["error"]["code"] == "INVALID_TRANSITION"
    assert (await client.delete(f"/kitchen-stations/{bar.json()['id']}", headers=km)).status_code == 204
    rec = await factory.auth(hotel, "receptionist")
    denied = await client.post("/kitchen-stations", json={"name": "Pool Bar"}, headers={**rec, **idem()})
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"


async def test_item_create_list_and_schedule_availability(client, factory):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    never = await client.post(
        "/menu/schedules",
        json={"name": "Never", "windows": [{"days": [1], "from": "00:00", "to": "00:01"}]},
        headers={**gm, **idem()},
    )
    assert never.status_code == 201, never.text
    assert never.json()["windows"] == [{"days": [1], "from": "00:00", "to": "00:01"}]
    always = await _category(client, gm, "Drinks")
    scheduled = await _category(client, gm, "Odd hours", never.json()["id"])
    coke = await _item(
        client, gm, hotel, always["id"], name="Coke", price=zar(1000), charge_category="beverage"
    )
    odd = await _item(client, gm, hotel, scheduled["id"], name="Midnight snack")
    assert coke["available_now"] is True
    assert coke["allergens"] == ["dairy", "gluten"]
    listed = {i["name"]: i for i in (await client.get("/menu/items", headers=gm)).json()["data"]}
    assert set(listed) == {"Coke", "Midnight snack"}
    assert listed["Midnight snack"]["next_available_at"] is not None
    now = (await client.get("/menu/items", params={"available": "true"}, headers=gm)).json()["data"]
    # The "Never" window is Monday 00:00-00:01 only.
    assert odd["available_now"] is False
    assert [i["id"] for i in now] == [coke["id"]]


async def test_bad_allergen_and_currency(client, factory):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    cat = await _category(client, gm)
    base = {"name": "X", "price": zar(100), "station_id": str(hotel.station_id), "category_id": cat["id"]}
    nuts = await client.post("/menu/items", json={**base, "allergens": ["walnuts"]}, headers={**gm, **idem()})
    assert nuts.status_code == 400
    euro = await client.post(
        "/menu/items",
        json={**base, "price": {"amount_minor": 100, "currency": "EUR"}},
        headers={**gm, **idem()},
    )
    assert euro.json()["error"]["code"] == "AMOUNT_INVALID"


async def test_halaal_needs_menu_certify(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=0)
    km = await factory.auth(hotel, "kitchen_manager")  # holds menu.certify
    cat = await _category(client, km)
    ok = await _item(client, km, hotel, cat["id"], dietary_tags=["halaal"])
    assert ok["dietary_tags"] == ["halaal"]
    # A custom role with menu.manage but without menu.certify
    admin = await factory.step_up(hotel, "hotel_admin", await factory.auth(hotel, "hotel_admin"))
    role = (
        await client.post(
            "/roles",
            json={"name": "Menu editor", "permissions": ["menu.read", "menu.manage"]},
            headers={**admin, **idem()},
        )
    ).json()
    target = hotel.users["kitchen_staff"].user_id
    assert (
        await client.put(f"/staff/{target}/roles", json={"role_ids": [role["id"]]}, headers=admin)
    ).status_code == 200
    editor = await factory.auth(hotel, "kitchen_staff")
    r = await client.post(
        "/menu/items",
        json={
            "name": "Lamb",
            "price": zar(100),
            "station_id": str(hotel.station_id),
            "category_id": cat["id"],
            "dietary_tags": ["kosher"],
        },
        headers={**editor, **idem()},
    )
    assert r.json()["error"]["code"] == "PERMISSION_DENIED"


async def test_price_change_needs_permission_and_step_up(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=0)
    km = await factory.auth(hotel, "kitchen_manager")  # menu.manage, no menu.price.update
    item = await _item(client, km, hotel, (await _category(client, km))["id"])
    rename = await client.patch(
        f"/menu/items/{item['id']}", json={"name": "Big Burger"}, headers={**km, "If-Match": '"1"'}
    )
    assert rename.status_code == 200, rename.text
    price = await client.patch(
        f"/menu/items/{item['id']}", json={"price": zar(15500)}, headers={**km, "If-Match": '"2"'}
    )
    assert price.json()["error"]["code"] == "PERMISSION_DENIED"
    gm = await factory.auth(hotel, "general_manager")
    no_step = await client.patch(
        f"/menu/items/{item['id']}", json={"price": zar(15500)}, headers={**gm, "If-Match": '"2"'}
    )
    assert no_step.json()["error"]["code"] == "STEP_UP_REQUIRED"
    s = await factory.step_up(hotel, "general_manager", gm)
    ok = await client.patch(
        f"/menu/items/{item['id']}", json={"price": zar(15500)}, headers={**s, "If-Match": '"2"'}
    )
    assert ok.status_code == 200
    assert ok.json()["price"] == zar(15500)
    from sqlalchemy import text

    async with owner_engine.connect() as conn:
        audit = (
            await conn.execute(
                text(
                    "SELECT old_value, new_value FROM app.audit_logs WHERE hotel_id = :h AND action = 'menu.price_update'"
                ),
                {"h": hotel.id},
            )
        ).one()
    assert audit.old_value["price_minor"] == 14500 and audit.new_value["price_minor"] == 15500


async def test_availability_and_modifiers(client, factory):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    item = await _item(client, gm, hotel, (await _category(client, gm))["id"])
    km = await factory.auth(hotel, "kitchen_manager")
    sold = await client.post(f"/menu/items/{item['id']}/availability", json={"available": False}, headers=km)
    assert sold.json()["is_available"] is False and sold.json()["available_now"] is False
    group = await client.post(
        "/menu/modifier-groups",
        json={"name": "Extras", "min_select": 0, "max_select": 3},
        headers={**gm, **idem()},
    )
    assert group.status_code == 201, group.text
    opt = await client.post(
        f"/menu/modifier-groups/{group.json()['id']}/options",
        json={"name": "Extra cheese", "price_delta": zar(1500)},
        headers={**gm, **idem()},
    )
    assert opt.status_code == 201, opt.text
    attached = await client.put(
        f"/menu/items/{item['id']}/modifier-groups", json={"group_ids": [group.json()["id"]]}, headers=gm
    )
    assert attached.status_code == 200, attached.text
    groups = attached.json()["modifier_groups"]
    assert groups[0]["options"][0]["price_delta"] == zar(1500)
    bad = await client.post(
        "/menu/modifier-groups",
        json={"name": "Bad", "min_select": 3, "max_select": 1},
        headers={**gm, **idem()},
    )
    assert bad.status_code == 400


async def test_menu_cross_tenant(client, factory):
    a = await factory.hotel(rooms=0)
    b = await factory.hotel(rooms=0)
    ga = await factory.auth(a, "general_manager")
    gb = await factory.auth(b, "general_manager")
    item = await _item(client, ga, a, (await _category(client, ga))["id"])
    assert (await client.get(f"/menu/items/{item['id']}", headers=gb)).status_code == 404
    assert (await client.get("/menu/items", headers=gb)).json()["data"] == []
    cat_b = await _category(client, gb)
    foreign_station = await client.post(
        "/menu/items",
        json={"name": "X", "price": zar(1), "station_id": str(a.station_id), "category_id": cat_b["id"]},
        headers={**gb, **idem()},
    )
    assert foreign_station.status_code == 404
