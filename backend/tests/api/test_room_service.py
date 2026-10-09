"""Room service: claim/release/assign, pick-up, delivery, payments and tips."""

from __future__ import annotations

import uuid

from sqlalchemy import text


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


def zar(n: int) -> dict:
    return {"amount_minor": n, "currency": "ZAR"}


async def ready_order(client, factory, owner_engine, *, price=300000, hotel=None):
    """A checked-in guest's order of `price`, taken through the kitchen to READY."""
    hotel = hotel or await factory.hotel(rooms=1)
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.hotel_settings SET room_charge_auto_limit_minor = 10000000 WHERE hotel_id = :h"),
            {"h": hotel.id},
        )
    gm = await factory.auth(hotel, "general_manager")
    cat = (await client.post("/menu/categories", json={"name": "All"}, headers={**gm, **idem()})).json()
    item = (
        await client.post(
            "/menu/items",
            json={
                "name": "Seafood platter",
                "price": zar(price),
                "station_id": str(hotel.station_id),
                "category_id": cat["id"],
            },
            headers={**gm, **idem()},
        )
    ).json()
    rec = await factory.auth(hotel, "receptionist")
    stay = (
        await client.post(
            f"/rooms/{hotel.room_ids[0]}/walk-in",
            json={"guest": {"name": "G"}, "nights": 1},
            headers={**rec, **idem()},
        )
    ).json()
    order = (
        await client.post(
            "/orders",
            json={
                "room_id": str(hotel.room_ids[0]),
                "lines": [{"menu_item_id": item["id"], "quantity": 1}],
                "quoted_total": zar(price),
            },
            headers={**rec, **idem()},
        )
    ).json()
    km = await factory.auth(hotel, "kitchen_manager")
    await client.post(f"/kitchen/orders/{order['id']}/accept", headers={**km, **idem()})
    await client.post(f"/kitchen/orders/{order['id']}/start", headers={**km, **idem()})
    board = (await client.get("/kitchen/orders", headers=km)).json()["data"]
    item_id = next(o for o in board if o["id"] == order["id"])["items"][0]["id"]
    ready = await client.post(f"/kitchen/order-items/{item_id}/ready", headers={**km, **idem()})
    assert ready.json()["status"] == "READY", ready.text
    return hotel, gm, order, stay


async def test_spec_case_r3000_due_r4000_received_r1000_tip_no_duplicates(client, factory, owner_engine):
    """Phase 5 exit criterion and build spec test case 70 (payment part)."""
    hotel, gm, order, stay = await ready_order(client, factory, owner_engine)
    ss = await factory.auth(hotel, "room_service_staff")
    ready = (await client.get("/deliveries", params={"scope": "ready"}, headers=ss)).json()["data"]
    assert [d["order_id"] for d in ready] == [order["id"]] and ready[0]["amount_due"] == zar(300000)
    assert (
        await client.post(f"/deliveries/{order['id']}/claim", headers={**ss, **idem()})
    ).status_code == 200
    await client.post(f"/deliveries/{order['id']}/picked-up", headers={**ss, **idem()})
    await client.post(f"/deliveries/{order['id']}/delivered", headers={**ss, **idem()})
    preview = await client.post(
        "/payments/preview", json={"order_id": order["id"], "amount_received": zar(400000)}, headers=ss
    )
    assert preview.json() | {"status": None} == {
        "amount_due": zar(300000),
        "amount_received": zar(400000),
        "difference": zar(100000),
        "tip": zar(100000),
        "shortfall": zar(0),
        "status": None,
    }
    body = {
        "order_id": order["id"],
        "method": "card_terminal",
        "amount_received": zar(400000),
        "terminal_reference": "4F82C1",
    }
    unconfirmed = await client.post("/payments", json=body, headers={**ss, **idem()})
    assert unconfirmed.status_code == 409
    assert unconfirmed.json()["error"]["code"] == "TIP_CONFIRMATION_REQUIRED"
    assert unconfirmed.json()["error"]["details"]["tip"] == zar(100000)
    key = idem()
    paid = await client.post("/payments", json={**body, "confirm_tip": True}, headers={**ss, **key})
    assert paid.status_code == 201, paid.text
    assert (paid.json()["amount_due"], paid.json()["tip"], paid.json()["status"]) == (
        zar(300000),
        zar(100000),
        "paid",
    )
    retry = await client.post("/payments", json={**body, "confirm_tip": True}, headers={**ss, **key})
    assert retry.headers.get("Idempotent-Replayed") == "true" and retry.json()["id"] == paid.json()["id"]
    again = await client.post("/payments", json={**body, "confirm_tip": True}, headers={**ss, **idem()})
    assert again.json()["error"]["code"] == "ALREADY_PAID"

    async with owner_engine.connect() as conn:
        counts = (
            await conn.execute(
                text(
                    "SELECT (SELECT count(*) FROM app.payments WHERE hotel_id = :h), "
                    "(SELECT count(*) FROM app.tips WHERE hotel_id = :h), "
                    "(SELECT count(*) FROM app.folio_entries WHERE hotel_id = :h AND entry_type IN ('payment','tip'))"
                ),
                {"h": hotel.id},
            )
        ).one()
        bal = (
            await conn.execute(
                text("SELECT fnb_minor, tips_minor, paid_minor FROM app.folio_balances WHERE stay_id = :s"),
                {"s": stay["id"]},
            )
        ).one()
    assert tuple(counts) == (1, 1, 2)
    # Merchant sees R3,000 F&B and R1,000 tip; the tip is not revenue and not on the balance.
    assert (bal.fnb_minor, bal.tips_minor, bal.paid_minor) == (300000, 100000, 300000)
    folio = (await client.get(f"/stays/{stay['id']}", headers=gm)).json()["folio"]
    assert folio["balance"] == zar(
        stay["folio"]["accommodation"]["amount_minor"]
    )  # only the room is still owed
    detail = (await client.get(f"/orders/{order['id']}", headers=gm)).json()
    assert detail["status"] == "CLOSED"


async def test_first_claim_wins_and_release(client, factory, owner_engine):
    hotel, _gm, order, _ = await ready_order(client, factory, owner_engine)
    ss = await factory.auth(hotel, "room_service_staff")
    sm = await factory.auth(hotel, "room_service_manager")
    assert (
        await client.post(f"/deliveries/{order['id']}/claim", headers={**ss, **idem()})
    ).status_code == 200
    second = await client.post(f"/deliveries/{order['id']}/claim", headers={**sm, **idem()})
    assert second.status_code == 409 and second.json()["error"]["code"] == "ALREADY_CLAIMED"
    not_mine = await client.post(f"/deliveries/{order['id']}/picked-up", headers={**sm, **idem()})
    assert not_mine.json()["error"]["code"] == "PERMISSION_DENIED"
    mine = (await client.get("/deliveries", params={"scope": "mine"}, headers=ss)).json()["data"]
    assert [d["order_id"] for d in mine] == [order["id"]]
    released = await client.post(f"/deliveries/{order['id']}/release", headers={**ss, **idem()})
    assert released.json()["status"] == "READY" and released.json()["assigned_to"] is None
    assigned = await client.post(
        f"/deliveries/{order['id']}/assign",
        json={"user_id": str(hotel.users["room_service_staff"].user_id)},
        headers={**sm, **idem()},
    )
    assert assigned.json()["status"] == "ASSIGNED"
    denied = await client.post(
        f"/deliveries/{order['id']}/assign",
        json={"user_id": str(hotel.users["room_service_staff"].user_id)},
        headers={**ss, **idem()},
    )
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
    kitchen_person = await client.post(
        f"/deliveries/{order['id']}/assign",
        json={"user_id": str(hotel.users["kitchen_staff"].user_id)},
        headers={**sm, **idem()},
    )
    assert kitchen_person.status_code == 404


async def test_staff_only_pay_for_their_own_deliveries(client, factory, owner_engine):
    hotel, gm, order, _ = await ready_order(client, factory, owner_engine)
    ss = await factory.auth(hotel, "room_service_staff")
    other = await factory.auth(hotel, "receptionist")  # payments.record, not the assignee
    await client.post(f"/deliveries/{order['id']}/claim", headers={**ss, **idem()})
    await client.post(f"/deliveries/{order['id']}/picked-up", headers={**ss, **idem()})
    body = {"order_id": order["id"], "method": "cash", "amount_received": zar(300000)}
    r = await client.post("/payments", json=body, headers={**other, **idem()})
    assert r.json()["error"]["code"] == "PERMISSION_DENIED"
    ok = await client.post("/payments", json=body, headers={**ss, **idem()})
    assert ok.status_code == 201 and ok.json()["tip"] == zar(0)
    assert (await client.get(f"/orders/{order['id']}", headers=gm)).json()["status"] == "CLOSED"


async def test_partial_payment_leaves_the_rest_on_the_folio(client, factory, owner_engine):
    hotel, gm, order, stay = await ready_order(client, factory, owner_engine)
    ss = await factory.auth(hotel, "room_service_staff")
    await client.post(f"/deliveries/{order['id']}/claim", headers={**ss, **idem()})
    await client.post(f"/deliveries/{order['id']}/picked-up", headers={**ss, **idem()})
    await client.post(f"/deliveries/{order['id']}/delivered", headers={**ss, **idem()})
    r = await client.post(
        "/payments",
        json={"order_id": order["id"], "method": "cash", "amount_received": zar(100000)},
        headers={**ss, **idem()},
    )
    assert r.json()["status"] == "partial"
    folio = (await client.get(f"/stays/{stay['id']}", headers=gm)).json()["folio"]
    assert folio["fnb"] == zar(300000) and folio["paid"] == zar(100000)


async def test_card_rules_and_card_data_rejected(client, factory, owner_engine):
    hotel, _gm, order, _ = await ready_order(client, factory, owner_engine)
    ss = await factory.auth(hotel, "room_service_staff")
    await client.post(f"/deliveries/{order['id']}/claim", headers={**ss, **idem()})
    await client.post(f"/deliveries/{order['id']}/picked-up", headers={**ss, **idem()})
    no_ref = await client.post(
        "/payments",
        json={"order_id": order["id"], "method": "card_terminal", "amount_received": zar(300000)},
        headers={**ss, **idem()},
    )
    assert no_ref.status_code == 400
    pan = await client.post(
        "/payments",
        json={
            "order_id": order["id"],
            "method": "card_terminal",
            "amount_received": zar(300000),
            "terminal_reference": "4111111111111111",
        },
        headers={**ss, **idem()},
    )
    assert pan.json()["error"]["code"] == "CARD_DATA_REJECTED"
    cvv = await client.post(
        "/payments", json={"order_id": order["id"], "cvv": "123"}, headers={**ss, **idem()}
    )
    assert cvv.json()["error"]["code"] == "CARD_DATA_REJECTED"


async def test_late_payment_needs_reason(client, factory, owner_engine):
    from datetime import UTC, datetime, timedelta

    hotel, _gm, order, _ = await ready_order(client, factory, owner_engine)
    ss = await factory.auth(hotel, "room_service_staff")
    await client.post(f"/deliveries/{order['id']}/claim", headers={**ss, **idem()})
    await client.post(f"/deliveries/{order['id']}/picked-up", headers={**ss, **idem()})
    earlier = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    body = {"order_id": order["id"], "method": "cash", "amount_received": zar(300000), "occurred_at": earlier}
    no_reason = await client.post("/payments", json=body, headers={**ss, **idem()})
    assert no_reason.json()["error"]["code"] == "REASON_REQUIRED"
    too_old = await client.post(
        "/payments",
        json={
            **body,
            "occurred_at": (datetime.now(UTC) - timedelta(hours=80)).isoformat(),
            "late_reason": "Wi-Fi outage",
        },
        headers={**ss, **idem()},
    )
    assert too_old.status_code == 400
    ok = await client.post(
        "/payments", json={**body, "late_reason": "Wi-Fi outage"}, headers={**ss, **idem()}
    )
    assert ok.status_code == 201 and ok.json()["late_reason"] == "Wi-Fi outage"


async def test_reception_settles_the_bill_and_lists_payments(client, factory, owner_engine):
    hotel, _gm, _order, stay = await ready_order(client, factory, owner_engine)
    rec = await factory.auth(hotel, "receptionist")
    due = (
        await client.post(
            "/payments/preview", json={"stay_id": stay["id"], "amount_received": zar(1)}, headers=rec
        )
    ).json()
    owed = due["amount_due"]["amount_minor"]
    paid = await client.post(
        "/payments",
        json={"stay_id": stay["id"], "method": "eft", "amount_received": zar(owed)},
        headers={**rec, **idem()},
    )
    assert paid.status_code == 201, paid.text
    nothing = await client.post(
        "/payments/preview", json={"stay_id": stay["id"], "amount_received": zar(1)}, headers=rec
    )
    assert nothing.json()["error"]["code"] == "INVALID_TRANSITION"
    listed = (await client.get("/payments", params={"method": "eft"}, headers=rec)).json()["data"]
    assert [p["id"] for p in listed] == [paid.json()["id"]]
    ss = await factory.auth(hotel, "room_service_staff")
    assert (await client.get("/payments", headers=ss)).json()["error"]["code"] == "PERMISSION_DENIED"


async def test_room_service_cross_tenant(client, factory, owner_engine):
    _hotel, _gm, order, _ = await ready_order(client, factory, owner_engine)
    other = await factory.hotel(rooms=1)
    ss_b = await factory.auth(other, "room_service_staff")
    assert (await client.get("/deliveries", headers=ss_b)).json()["data"] == []
    assert (
        await client.post(f"/deliveries/{order['id']}/claim", headers={**ss_b, **idem()})
    ).status_code == 404
