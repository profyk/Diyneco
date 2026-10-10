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
