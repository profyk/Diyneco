"""Menu pipeline: CSV import (check, then all or nothing), ingredients, deleting a category."""

from __future__ import annotations

from app.services.menu_import import TEMPLATE
from tests.api.test_menu import _category, _item, idem


async def _groups(client, gm):
    temp = await client.post(
        "/menu/modifier-groups",
        json={"name": "Steak temperature", "min_select": 1, "max_select": 1},
        headers={**gm, **idem()},
    )
    sauce = await client.post(
        "/menu/modifier-groups",
        json={"name": "Sauce", "min_select": 0, "max_select": 2},
        headers={**gm, **idem()},
    )
    assert temp.status_code == 201 and sauce.status_code == 201


def csv_headers(gm):
    return {**gm, **idem(), "Content-Type": "text/csv"}


async def test_import_checks_then_creates_items_categories_and_options(client, factory):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    await _groups(client, gm)
    stations = (await client.get("/kitchen-stations", headers=gm)).json()["data"]
    body = TEMPLATE.replace(",Bar,", f",{stations[0]['name']},")

    check = await client.post("/menu/items/import", content=body.encode(), headers=csv_headers(gm))
    assert check.status_code == 200, check.text
    assert (
        check.json()["valid"]
        and check.json()["rows"] == 2
        and check.json()["new_categories"] == ["Grill", "Drinks"]
    )
    assert (await client.get("/menu/items", headers=gm)).json()["data"] == []

    done = await client.post("/menu/items/import?commit=true", content=body.encode(), headers=csv_headers(gm))
    assert done.status_code == 201, done.text
    assert done.json()["created"] == 2
    items = {i["name"]: i for i in (await client.get("/menu/items", headers=gm)).json()["data"]}
    steak = items["Rump steak 300 g"]
    assert steak["price"]["amount_minor"] == 24500 and steak["ingredients"] == [
        "beef",
        "potato",
        "salt",
        "pepper",
    ]
    assert [g["name"] for g in steak["modifier_groups"]] == ["Steak temperature", "Sauce"]
    assert items["Fresh orange juice"]["charge_category"] == "beverage"
    sections = {
        c["name"]: c["section"] for c in (await client.get("/menu/categories", headers=gm)).json()["data"]
    }
    assert sections == {"Grill": "food", "Drinks": "drinks"}


async def test_import_reports_every_problem_and_writes_nothing(client, factory):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    body = (
        "category,name,description,price,type,station,dietary,allergens,ingredients,options\n"
        "Mains,,,R12,snack,Nowhere,meaty,nuts,,Toppings\n"
        "Mains,Halaal burger,,99.00,food,,halaal,,,\n"
    )
    r = await client.post("/menu/items/import", content=body.encode(), headers=csv_headers(gm))
    fields = {(e["line"], e["field"]) for e in r.json()["errors"]}
    assert {
        (2, "name"),
        (2, "price"),
        (2, "type"),
        (2, "station"),
        (2, "dietary"),
        (2, "allergens"),
        (2, "options"),
    } <= fields
    assert not r.json()["valid"]
    commit = await client.post(
        "/menu/items/import?commit=true", content=body.encode(), headers=csv_headers(gm)
    )
    assert commit.json()["error"]["code"] == "VALIDATION_FAILED"
    assert (await client.get("/menu/items", headers=gm)).json()["data"] == []
    bad_header = await client.post(
        "/menu/items/import", content=b"name,price\nx,1\n", headers=csv_headers(gm)
    )
    assert bad_header.json()["error"]["code"] == "VALIDATION_FAILED"


async def test_ingredients_and_deleting_a_category_with_its_items(client, factory):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    cat = await _category(client, gm)
    item = await _item(client, gm, hotel, cat["id"], ingredients=["chicken", "brioche bun"])
    assert item["ingredients"] == ["chicken", "brioche bun"]

    refused = await client.delete(f"/menu/categories/{cat['id']}", headers=gm)
    assert refused.json()["error"]["code"] == "INVALID_TRANSITION"
    no_pin = await client.delete(f"/menu/categories/{cat['id']}?with_items=true", headers=gm)
    assert no_pin.json()["error"]["code"] == "STEP_UP_REQUIRED"
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    gone = await client.delete(f"/menu/categories/{cat['id']}?with_items=true", headers=gm_s)
    assert gone.status_code == 204, gone.text
    assert (await client.get("/menu/items", headers=gm)).json()["data"] == []
    assert (await client.get("/menu/categories", headers=gm)).json()["data"] == []


async def test_option_groups_and_choices_can_be_edited_sold_out_and_removed(client, factory):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    group = (
        await client.post(
            "/menu/modifier-groups",
            json={"name": "Extras", "min_select": 0, "max_select": 3},
            headers={**gm, **idem()},
        )
    ).json()
    cheese = (
        await client.post(
            f"/menu/modifier-groups/{group['id']}/options",
            json={"name": "Cheese", "price_delta": {"amount_minor": 1500, "currency": "ZAR"}},
            headers={**gm, **idem()},
        )
    ).json()["options"][0]
    cat = await _category(client, gm)
    item = await _item(client, gm, hotel, cat["id"])
    await client.put(
        f"/menu/items/{item['id']}/modifier-groups", json={"group_ids": [group["id"]]}, headers=gm
    )

    renamed = await client.patch(
        f"/menu/modifier-groups/{group['id']}", json={"name": "Add-ons", "max_select": 2}, headers=gm
    )
    assert renamed.json()["name"] == "Add-ons" and renamed.json()["max_select"] == 2
    bad = await client.patch(f"/menu/modifier-groups/{group['id']}", json={"min_select": 3}, headers=gm)
    assert bad.json()["error"]["code"] == "VALIDATION_FAILED"

    repriced = await client.patch(
        f"/menu/modifier-options/{cheese['id']}",
        json={"price_delta": {"amount_minor": 2000, "currency": "ZAR"}},
        headers=gm,
    )
    assert repriced.json()["options"][0]["price_delta"]["amount_minor"] == 2000
    # The kitchen may mark a choice sold out but not reprice it.
    cook = await factory.auth(hotel, "kitchen_manager")
    sold_out = await client.patch(
        f"/menu/modifier-options/{cheese['id']}", json={"is_available": False}, headers=cook
    )
    assert sold_out.status_code == 200, (
        sold_out.text and sold_out.json()["options"][0]["is_available"] is False
    )
    no_price = await client.patch(
        f"/menu/modifier-options/{cheese['id']}",
        json={"price_delta": {"amount_minor": 1, "currency": "ZAR"}},
        headers=cook,
    )
    assert no_price.status_code == 403

    left = await client.delete(f"/menu/modifier-options/{cheese['id']}", headers=gm)
    assert left.json()["options"] == []
    assert (await client.delete(f"/menu/modifier-groups/{group['id']}", headers=gm)).status_code == 204
    after = (await client.get(f"/menu/items/{item['id']}", headers=gm)).json()
    assert after["modifier_groups"] == []


async def test_standard_layout_sections_and_station_routing(client, factory):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    first = await client.post("/menu/standard-layout", headers=gm)
    assert first.status_code == 200, first.text
    body = first.json()
    assert {"Bar", "Pastry", "Cold kitchen"} <= set(body["created_stations"])
    cats = {c["name"]: c for c in body["categories"]}
    stations = {s["name"].lower(): s["id"] for s in body["stations"]}
    assert cats["Wines"]["section"] == "drinks" and cats["Desserts"]["section"] == "food"
    assert cats["Desserts"]["default_station_id"] == stations["pastry"]
    again = (await client.post("/menu/standard-layout", headers=gm)).json()
    assert again["created_stations"] == [] and again["created_categories"] == []

    # An item without a station is prepared where its category says.
    r = await client.post(
        "/menu/items",
        json={
            "name": "Malva pudding",
            "price": {"amount_minor": 6500, "currency": "ZAR"},
            "category_id": cats["Desserts"]["id"],
        },
        headers={**gm, **idem()},
    )
    assert r.status_code == 201, r.text and r.json()["station_id"] == stations["pastry"]
    assert r.json()["station_id"] == stations["pastry"]

    # Routing a category moves its dishes and its future ones.
    moved = await client.post(
        f"/menu/categories/{cats['Desserts']['id']}/station",
        json={"station_id": stations["main kitchen"]},
        headers=gm,
    )
    assert moved.json()["moved_items"] == 1 and moved.json()["default_station_id"] == stations["main kitchen"]
    item = (await client.get("/menu/items", headers=gm)).json()["data"][0]
    assert item["station_id"] == stations["main kitchen"]

    # A category without a station needs one on the item.
    plain = await _category(client, gm, name="Specials")
    no_station = await client.post(
        "/menu/items",
        json={"name": "Soup", "price": {"amount_minor": 5000, "currency": "ZAR"}, "category_id": plain["id"]},
        headers={**gm, **idem()},
    )
    assert no_station.json()["error"]["details"]["fields"][0]["field"] == "station_id"
