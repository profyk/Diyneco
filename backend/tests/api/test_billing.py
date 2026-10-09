"""Folio view, other charges, discounts and two-person adjustments."""

from __future__ import annotations

import uuid

from sqlalchemy import text

from tests.api.test_room_service import idem, ready_order, zar


async def walk_in(client, factory, hotel, nights: int = 2) -> dict:
    rec = await factory.auth(hotel, "receptionist")
    r = await client.post(
        f"/rooms/{hotel.room_ids[0]}/walk-in",
        json={"guest": {"name": "Folio Guest"}, "nights": nights},
        headers={**rec, **idem()},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def category_id(owner_engine, code: str) -> str:
    async with owner_engine.connect() as conn:
        return str(
            (
                await conn.execute(
                    text("SELECT id FROM app.charge_categories WHERE hotel_id IS NULL AND code = :c"),
                    {"c": code},
                )
            ).scalar_one()
        )


async def laundry(client, rec, stay_id: str, owner_engine, amount: int = 5000, quantity: int = 2):
    return await client.post(
        f"/folios/{stay_id}/charges",
        json={
            "charge_category_id": await category_id(owner_engine, "laundry"),
            "description": "Laundry",
            "amount": zar(amount),
            "quantity": quantity,
        },
        headers={**rec, **idem()},
    )


async def test_folio_view_and_other_charges(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel)
    rec = await factory.auth(hotel, "receptionist")
    folio = (await client.get(f"/folios/{stay['id']}", headers=rec)).json()
    assert folio["totals"]["accommodation"] == zar(300000)  # 2 nights at R1,500
    assert folio["totals"]["balance"] == zar(300000) and len(folio["entries"]) == 2

    r = await laundry(client, rec, stay["id"], owner_engine)
    assert r.status_code == 201, r.text
    assert r.json()["totals"]["other"] == zar(10000)
    assert r.json()["totals"]["balance"] == zar(310000)

    # Rooms, tips and payments have their own flows.
    for code in ("accommodation", "tip", "payment"):
        bad = await client.post(
            f"/folios/{stay['id']}/charges",
            json={
                "charge_category_id": await category_id(owner_engine, code),
                "description": "x",
                "amount": zar(100),
            },
            headers={**rec, **idem()},
        )
        assert bad.json()["error"]["code"] == "VALIDATION_FAILED", (code, bad.text)

    km = await factory.auth(hotel, "kitchen_manager")
    denied = await laundry(client, km, stay["id"], owner_engine)
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
    no_key = await client.post(
        f"/folios/{stay['id']}/charges",
        json={
            "charge_category_id": await category_id(owner_engine, "laundry"),
            "description": "x",
            "amount": zar(1),
        },
        headers=rec,
    )
    assert no_key.status_code == 400


async def test_discount_needs_permission_step_up_and_reason(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel)
    body = {"kind": "percent", "percent_bp": 1000, "applies_to": "accommodation", "reason": "Loyal guest"}
    rec = await factory.auth(hotel, "receptionist")
    r = await client.post(f"/folios/{stay['id']}/discounts", json=body, headers={**rec, **idem()})
    assert r.json()["error"]["code"] == "PERMISSION_DENIED"
    gm = await factory.auth(hotel, "general_manager")
    r = await client.post(f"/folios/{stay['id']}/discounts", json=body, headers={**gm, **idem()})
    assert r.json()["error"]["code"] == "STEP_UP_REQUIRED"
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    r = await client.post(f"/folios/{stay['id']}/discounts", json=body, headers={**gm_s, **idem()})
    assert r.status_code == 201, r.text
    assert r.json()["totals"]["accommodation"] == zar(270000)
    assert [e["type"] for e in r.json()["entries"]].count("discount") == 1

    too_big = {"kind": "fixed", "amount": zar(999999), "applies_to": "accommodation", "reason": "x"}
    r = await client.post(f"/folios/{stay['id']}/discounts", json=too_big, headers={**gm_s, **idem()})
    assert r.json()["error"]["code"] == "AMOUNT_INVALID"
    nothing = {"kind": "fixed", "amount": zar(100), "applies_to": "fnb", "reason": "x"}
    r = await client.post(f"/folios/{stay['id']}/discounts", json=nothing, headers={**gm_s, **idem()})
    assert r.json()["error"]["code"] == "INVALID_TRANSITION"
    no_reason = {**body, "reason": ""}
    r = await client.post(f"/folios/{stay['id']}/discounts", json=no_reason, headers={**gm_s, **idem()})
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"

    async with owner_engine.connect() as conn:
        audited = (
            await conn.execute(
                text("SELECT count(*) FROM app.audit_logs WHERE hotel_id = :h AND action = 'folio.discount'"),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert audited == 1


async def test_adjustment_needs_a_second_person(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel)
    rec = await factory.auth(hotel, "receptionist")
    folio = (await laundry(client, rec, stay["id"], owner_engine)).json()
    entry = next(e for e in folio["entries"] if e["category"] == "laundry")

    rm = await factory.auth(hotel, "reception_manager")
    req = await client.post(
        "/adjustments",
        json={"folio_entry_id": entry["id"], "new_amount": zar(2500), "reason": "Wrong item count"},
        headers={**rm, **idem()},
    )
    assert req.status_code == 201, req.text
    adj = req.json()
    assert (adj["status"], adj["original"], adj["new_amount"]) == ("pending", zar(10000), zar(2500))

    # Requesting alone changes nothing on the bill.
    assert (await client.get(f"/folios/{stay['id']}", headers=rec)).json()["totals"]["other"] == zar(10000)

    # The requester can never approve their own request.
    gm = await factory.step_up(hotel, "general_manager", await factory.auth(hotel, "general_manager"))
    own = await client.post(
        "/adjustments",
        json={"folio_entry_id": entry["id"], "new_amount": zar(0), "reason": "GM's own request"},
        headers={**gm, **idem()},
    )
    self_approve = await client.post(f"/adjustments/{own.json()['id']}/approve", headers={**gm, **idem()})
    assert self_approve.status_code == 403 and self_approve.json()["error"]["code"] == "SELF_APPROVAL"

    no_step_up = await client.post(
        f"/adjustments/{adj['id']}/approve",
        headers={**(await factory.auth(hotel, "general_manager")), **idem()},
    )
    assert no_step_up.json()["error"]["code"] == "STEP_UP_REQUIRED"
    key = idem()
    approved = await client.post(f"/adjustments/{adj['id']}/approve", headers={**gm, **key})
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    replay = await client.post(f"/adjustments/{adj['id']}/approve", headers={**gm, **key})
    assert replay.headers.get("Idempotent-Replayed") == "true"
    again = await client.post(f"/adjustments/{adj['id']}/approve", headers={**gm, **idem()})
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"

    after = (await client.get(f"/folios/{stay['id']}", headers=rec)).json()
    assert after["totals"]["other"] == zar(2500)
    assert [e["type"] for e in after["entries"]].count("adjustment") == 1

    # The GM's own request was made against R100 and is now stale; a third person cannot
    # approve it blindly.
    fin = await factory.step_up(hotel, "finance_manager", await factory.auth(hotel, "finance_manager"))
    stale = await client.post(f"/adjustments/{own.json()['id']}/approve", headers={**fin, **idem()})
    assert stale.json()["error"]["code"] == "INVALID_TRANSITION"
    assert stale.json()["error"]["details"]["current"] == zar(2500)

    # A new request starts from the current amount.
    second = await client.post(
        "/adjustments",
        json={"folio_entry_id": entry["id"], "new_amount": zar(0), "reason": "Laundry was free"},
        headers={**rm, **idem()},
    )
    assert second.json()["original"] == zar(2500)
    rejected = await client.post(
        f"/adjustments/{second.json()['id']}/reject", json={"reason": "It was not"}, headers={**fin, **idem()}
    )
    assert rejected.json()["status"] == "rejected"
    assert (await client.get(f"/folios/{stay['id']}", headers=rec)).json()["totals"]["other"] == zar(2500)


async def test_order_adjustment_and_validation(client, factory, owner_engine):
    hotel, gm, order, stay = await ready_order(client, factory, owner_engine)
    rm = await factory.auth(hotel, "reception_manager")
    req = await client.post(
        "/adjustments",
        json={"order_id": order["id"], "new_amount": zar(250000), "reason": "Cold food"},
        headers={**rm, **idem()},
    )
    assert req.json()["original"] == zar(300000)
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    assert (
        await client.post(f"/adjustments/{req.json()['id']}/approve", headers={**gm_s, **idem()})
    ).status_code == 200
    folio = (await client.get(f"/folios/{stay['id']}", headers=gm)).json()
    assert folio["totals"]["fnb"] == zar(250000)

    both = await client.post(
        "/adjustments",
        json={
            "order_id": order["id"],
            "folio_entry_id": str(uuid.uuid4()),
            "new_amount": zar(1),
            "reason": "abc",
        },
        headers={**rm, **idem()},
    )
    assert both.json()["error"]["code"] == "VALIDATION_FAILED"
    same = await client.post(
        "/adjustments",
        json={"order_id": order["id"], "new_amount": zar(250000), "reason": "No change"},
        headers={**rm, **idem()},
    )
    assert same.json()["error"]["code"] == "AMOUNT_INVALID"
    rec = await factory.auth(hotel, "receptionist")
    reject_denied = await client.post(
        f"/adjustments/{req.json()['id']}/reject", json={"reason": "x"}, headers={**rec, **idem()}
    )
    assert reject_denied.json()["error"]["code"] == "PERMISSION_DENIED"


async def test_folios_and_adjustments_are_tenant_scoped(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel)
    rec = await factory.auth(hotel, "receptionist")
    folio = (await laundry(client, rec, stay["id"], owner_engine)).json()
    entry = next(e for e in folio["entries"] if e["category"] == "laundry")
    rm = await factory.auth(hotel, "reception_manager")
    adj = (
        await client.post(
            "/adjustments",
            json={"folio_entry_id": entry["id"], "new_amount": zar(0), "reason": "Mistake"},
            headers={**rm, **idem()},
        )
    ).json()

    other = await factory.hotel(rooms=1)
    gm_b = await factory.step_up(other, "general_manager", await factory.auth(other, "general_manager"))
    assert (await client.get(f"/folios/{stay['id']}", headers=gm_b)).status_code == 404
    assert (await laundry(client, gm_b, stay["id"], owner_engine)).status_code == 404
    for r in (
        await client.post(f"/adjustments/{adj['id']}/approve", headers={**gm_b, **idem()}),
        await client.post(
            "/adjustments",
            json={"folio_entry_id": entry["id"], "new_amount": zar(0), "reason": "Mistake"},
            headers={**gm_b, **idem()},
        ),
    ):
        assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"
