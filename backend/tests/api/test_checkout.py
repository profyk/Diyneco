"""Checkout, invoices, PDF bills, email and credit notes; build spec test case 70 end to end."""

from __future__ import annotations

import hashlib
from datetime import date

from sqlalchemy import text

from tests.api.test_billing import laundry, walk_in
from tests.api.test_ordering import set_settings
from tests.api.test_room_service import idem, ready_order, zar

ADDRESS = {"line1": "12 Long Street", "city": "Cape Town", "postal_code": "8001", "country": "ZA"}


async def pin_step_up(client, headers: dict[str, str]) -> dict[str, str]:
    """A manager enters their PIN (factory users have PIN 1234)."""
    r = await client.post("/auth/step-up", json={"pin": "1234"}, headers=headers)
    assert r.status_code == 200, r.text
    return {**headers, "X-Step-Up": r.json()["step_up_token"]}


async def pair_tablet(client, gm, room_id) -> dict[str, str]:
    code = (
        await client.post(
            "/devices/pairings", json={"type": "guest", "room_id": str(room_id)}, headers={**gm, **idem()}
        )
    ).json()["code"]
    cred = (await client.post("/devices/pair", json={"code": code}, headers=idem())).json()[
        "device_credential"
    ]
    token = (await client.post("/devices/token", json={"device_credential": cred})).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def settle(client, factory, hotel, stay_id: str) -> None:
    rec = await factory.auth(hotel, "receptionist")
    balance = (await client.get(f"/folios/{stay_id}", headers=rec)).json()["totals"]["balance"]
    if balance["amount_minor"] > 0:
        r = await client.post(
            "/payments",
            json={"stay_id": stay_id, "method": "cash", "amount_received": balance},
            headers={**rec, **idem()},
        )
        assert r.status_code == 201, r.text


async def fetch_pdf(client, url: str) -> bytes:
    r = await client.get(url.split("/api/v1", 1)[1])
    assert r.status_code == 200, r.text
    return r.content


async def test_spec_case_70_end_to_end(client, factory, owner_engine, mailbox):
    """Room 259 orders R3,000; kitchen and room service see it; staff enter R4,000 and the
    system records a R1,000 tip; the merchant sees R3,000 F&B + R1,000 tip; the guest checks
    out with a manager's PIN; the tablet resets; the next guest sees nothing of the previous
    one; management still sees the history."""
    hotel = await factory.hotel(rooms=1)
    room_id = hotel.room_ids[0]
    async with owner_engine.begin() as conn:
        await conn.execute(text("UPDATE app.rooms SET number = '259' WHERE id = :r"), {"r": room_id})
    await set_settings(
        owner_engine,
        hotel,
        vat_registered=True,
        vat_number="4123456789",
        room_charge_auto_limit_minor=10000000,
    )
    gm = await factory.auth(hotel, "general_manager")
    cat = (await client.post("/menu/categories", json={"name": "Mains"}, headers={**gm, **idem()})).json()
    item = (
        await client.post(
            "/menu/items",
            json={
                "name": "Seafood platter",
                "price": zar(300000),
                "station_id": str(hotel.station_id),
                "category_id": cat["id"],
            },
            headers={**gm, **idem()},
        )
    ).json()
    tablet = await pair_tablet(client, gm, room_id)
    stay = await walk_in(client, factory, hotel, nights=1)

    # Room 259 orders R3,000.
    order = await client.post(
        "/guest/orders",
        json={"lines": [{"menu_item_id": item["id"], "quantity": 1}], "quoted_total": zar(300000)},
        headers={**tablet, **idem()},
    )
    assert order.status_code == 201, order.text
    order = order.json()
    assert order["total"] == zar(300000)

    # Kitchen receives the correct order (and never sees prices).
    km = await factory.auth(hotel, "kitchen_manager")
    board = (await client.get("/kitchen/orders", headers=km)).json()["data"]
    ticket = next(o for o in board if o["id"] == order["id"])
    assert ticket["room"] == "259" and [i["name"] for i in ticket["items"]] == ["Seafood platter"]
    assert "total" not in ticket and "price" not in str(ticket).lower()
    await client.post(f"/kitchen/orders/{order['id']}/accept", headers={**km, **idem()})
    await client.post(f"/kitchen/orders/{order['id']}/start", headers={**km, **idem()})
    await client.post(f"/kitchen/order-items/{ticket['items'][0]['id']}/ready", headers={**km, **idem()})

    # Room service receives the correct amount; the guest sees R3,000.
    ss = await factory.auth(hotel, "room_service_staff")
    ready = (await client.get("/deliveries", params={"scope": "ready"}, headers=ss)).json()["data"]
    assert [(d["room"], d["amount_due"]) for d in ready] == [("259", zar(300000))]
    guest_folio = (await client.get("/guest/folio", headers=tablet)).json()
    assert guest_folio["totals"]["food_and_beverage"] == zar(300000)
    for step in ("claim", "picked-up", "delivered"):
        assert (
            await client.post(f"/deliveries/{order['id']}/{step}", headers={**ss, **idem()})
        ).status_code == 200

    # Staff enter R4,000; the system calculates a R1,000 tip.
    paid = await client.post(
        "/payments",
        json={
            "order_id": order["id"],
            "method": "card_terminal",
            "amount_received": zar(400000),
            "terminal_reference": "4F82C1",
            "confirm_tip": True,
        },
        headers={**ss, **idem()},
    )
    assert (paid.json()["amount_due"], paid.json()["tip"]) == (zar(300000), zar(100000))

    # The merchant sees R3,000 F&B and a R1,000 tip that is not on the bill.
    folio = (await client.get(f"/folios/{stay['id']}", headers=gm)).json()
    assert (folio["totals"]["fnb"], folio["totals"]["tips"]) == (zar(300000), zar(100000))

    # The guest checks out: reception settles the room, a manager enters their PIN.
    await settle(client, factory, hotel, stay["id"])
    summary = (await client.get(f"/stays/{stay['id']}/checkout-summary", headers=gm)).json()
    assert summary["can_check_out"] is True and summary["open_orders"] == []
    assert (await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**gm, **idem()})).json()[
        "error"
    ]["code"] == "STEP_UP_REQUIRED"
    gm_pin = await pin_step_up(client, gm)
    out = await client.post(
        f"/stays/{stay['id']}/checkout",
        json={"bill_delivery": ["pdf", "email"], "email_to": ["guest@example.com"]},
        headers={**gm_pin, **idem()},
    )
    assert out.status_code == 200, out.text
    invoice = out.json()["invoice"]
    year = date.today().year
    assert invoice["number"] == f"TST-{year}-000001"
    assert invoice["kind"] == "abridged_tax_invoice" and invoice["title"] == "Tax Invoice"
    assert invoice["totals"]["fnb"] == zar(300000) and invoice["totals"]["tips"] == zar(100000)
    assert invoice["totals"]["balance"] == zar(0)
    assert [i["category"] for i in invoice["items"]] == ["accommodation", "food"]
    assert invoice["supplier"]["vat_number"] == "4123456789"

    # The PDF is stored, signed for download and matches its recorded hash.
    url = (await client.get(f"/invoices/{invoice['id']}/pdf", headers=gm)).json()["url"]
    pdf = await fetch_pdf(client, url)
    assert pdf.startswith(b"%PDF") and hashlib.sha256(pdf).hexdigest() == invoice["sha256"]
    sent = [m for m in mailbox.sent if m.to == "guest@example.com" and invoice["number"] in m.subject]
    assert len(sent) == 1 and sent[0].attachments[0][0] == f"{invoice['number']}.pdf"

    # The tablet resets.
    beat = (await client.post("/devices/heartbeat", json={}, headers=tablet)).json()
    assert beat["commands"] == ["RESET"]
    async with owner_engine.connect() as conn:
        resets = (
            await conn.execute(
                text(
                    "SELECT channels FROM app.event_outbox WHERE hotel_id = :h AND type = 'RESET_ROOM_SESSION'"
                ),
                {"h": hotel.id},
            )
        ).all()
        room_status = (
            await conn.execute(text("SELECT status FROM app.rooms WHERE id = :r"), {"r": room_id})
        ).scalar_one()
    assert len(resets) == 1 and f"hotel:{hotel.id}:room:{room_id}" in resets[0].channels
    assert room_status == "cleaning"
    await client.post("/devices/heartbeat", json={"completed_commands": ["RESET"]}, headers=tablet)
    assert (await client.get("/guest/session", headers=tablet)).json()["state"] == "idle"

    # A new guest cannot see the previous guest's orders.
    async with owner_engine.begin() as conn:
        await conn.execute(text("UPDATE app.rooms SET status = 'available' WHERE id = :r"), {"r": room_id})
    await walk_in(client, factory, hotel, nights=1)
    assert (await client.get("/guest/orders", headers=tablet)).json()["data"] == []
    assert (await client.get(f"/guest/orders/{order['id']}", headers=tablet)).status_code == 404
    assert (await client.get("/guest/folio", headers=tablet)).json()["totals"]["food_and_beverage"] == zar(0)

    # Previous guest history remains available to authorised management.
    assert (await client.get(f"/orders/{order['id']}", headers=gm)).json()["status"] == "CLOSED"
    history = (await client.get(f"/stays/{stay['id']}/invoices", headers=gm)).json()["data"]
    assert [i["number"] for i in history] == [invoice["number"]]
    assert (await client.get(f"/folios/{stay['id']}", headers=gm)).json()["status"] == "closed"
    ss_history = await client.get(f"/stays/{stay['id']}/invoices", headers=ss)
    assert ss_history.json()["error"]["code"] == "PERMISSION_DENIED"


async def test_checkout_gates_and_override(client, factory, owner_engine):
    hotel, gm, order, stay = await ready_order(client, factory, owner_engine)
    rec = await factory.step_up(hotel, "receptionist", await factory.auth(hotel, "receptionist"))
    r = await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**rec, **idem()})
    assert r.status_code == 409 and r.json()["error"]["code"] == "OPEN_ORDERS"
    assert r.json()["error"]["details"]["orders"][0]["status"] == "READY"

    ss = await factory.auth(hotel, "room_service_staff")
    for step in ("claim", "picked-up", "delivered", "leave-on-room"):
        await client.post(f"/deliveries/{order['id']}/{step}", headers={**ss, **idem()})
    r = await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**rec, **idem()})
    assert r.json()["error"]["code"] == "OUTSTANDING_BALANCE"
    owed = r.json()["error"]["details"]["balance"]["amount_minor"]
    assert owed == 300000 + 150000

    override = {"override": True, "override_reason": "Company will pay by EFT"}
    r = await client.post(f"/stays/{stay['id']}/checkout", json=override, headers={**rec, **idem()})
    assert r.status_code == 422 and r.json()["error"]["code"] == "OVERRIDE_NOT_ALLOWED"
    await set_settings(owner_engine, hotel, checkout_override_allowed=True)
    r = await client.post(f"/stays/{stay['id']}/checkout", json=override, headers={**rec, **idem()})
    assert r.json()["error"]["code"] == "PERMISSION_DENIED"  # receptionists lack checkout.override
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    r = await client.post(
        f"/stays/{stay['id']}/checkout", json={"override": True}, headers={**gm_s, **idem()}
    )
    assert r.json()["error"]["code"] == "REASON_REQUIRED"
    r = await client.post(f"/stays/{stay['id']}/checkout", json=override, headers={**gm_s, **idem()})
    assert r.status_code == 200, r.text
    assert r.json()["override_reason"] == "Company will pay by EFT"
    assert r.json()["invoice"]["totals"]["balance"] == zar(owed)
    again = await client.post(f"/stays/{stay['id']}/checkout", json=override, headers={**gm_s, **idem()})
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"

    # The database refuses entries on a closed folio; the balance goes to accounts receivable
    # (Phase 8), not onto the closed bill.
    rec_plain = await factory.auth(hotel, "receptionist")
    late = await client.post(
        "/payments",
        json={"stay_id": stay["id"], "method": "cash", "amount_received": zar(owed)},
        headers={**rec_plain, **idem()},
    )
    assert late.json()["error"]["code"] == "INVALID_TRANSITION"
    async with owner_engine.connect() as conn:
        audit = (
            await conn.execute(
                text("SELECT reason FROM app.audit_logs WHERE hotel_id = :h AND action = 'stay.check_out'"),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert audit == "Company will pay by EFT"


async def test_invoice_kind_numbering_recipient_and_retry(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    gm = await factory.step_up(hotel, "general_manager", await factory.auth(hotel, "general_manager"))
    year = date.today().year

    # Not VAT-registered: a guest statement.
    stay = await walk_in(client, factory, hotel, nights=1)
    await settle(client, factory, hotel, stay["id"])
    key = idem()
    first = await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**gm, **key})
    assert first.json()["invoice"]["kind"] == "guest_statement"
    assert first.json()["invoice"]["number"] == f"TST-{year}-000001"
    replay = await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**gm, **key})
    assert replay.headers.get("Idempotent-Replayed") == "true"
    assert replay.json()["invoice"]["id"] == first.json()["invoice"]["id"]

    # VAT-registered and over the abridged limit: a full tax invoice, which needs an address.
    await set_settings(owner_engine, hotel, vat_registered=True, vat_number="4123456789")
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.rooms SET status = 'available' WHERE id = :r"), {"r": hotel.room_ids[0]}
        )
    stay = await walk_in(client, factory, hotel, nights=4)  # 4 x R1,725 incl. VAT > R5,000
    await settle(client, factory, hotel, stay["id"])
    r = await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**gm, **idem()})
    assert r.json()["error"]["details"]["reason"] == "recipient_address_required"
    r = await client.post(
        f"/stays/{stay['id']}/checkout", json={"recipient_address": ADDRESS}, headers={**gm, **idem()}
    )
    invoice = r.json()["invoice"]
    assert (invoice["kind"], invoice["number"]) == ("tax_invoice", f"TST-{year}-000002")
    assert invoice["recipient"]["address"]["line1"] == "12 Long Street"
    assert invoice["totals"]["vat_included"] == zar(4 * 22500)

    # The failed attempt did not use up a number.
    async with owner_engine.connect() as conn:
        numbers = (
            (
                await conn.execute(
                    text("SELECT number FROM app.invoices WHERE hotel_id = :h ORDER BY number"),
                    {"h": hotel.id},
                )
            )
            .scalars()
            .all()
        )
    assert numbers == [f"TST-{year}-000001", f"TST-{year}-000002"]


async def test_company_billing_on_the_invoice(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    await set_settings(owner_engine, hotel, vat_registered=True, vat_number="4123456789")
    rec = await factory.auth(hotel, "receptionist")
    profile = (
        await client.post(
            "/billing-profiles",
            json={
                "company_name": "ABC Tech (Pty) Ltd",
                "vat_number": "4987654321",
                "billing_address": {"line1": "1 Main Road", "city": "Johannesburg"},
                "billing_email": "accounts@abctech.example",
            },
            headers={**rec, **idem()},
        )
    ).json()
    stay = (
        await client.post(
            f"/rooms/{hotel.room_ids[0]}/walk-in",
            json={
                "guest": {"name": "Thandi Mokoena"},
                "nights": 4,
                "billing": {
                    "type": "company",
                    "billing_profile_id": profile["id"],
                    "purchase_order": "PO-7781",
                },
            },
            headers={**rec, **idem()},
        )
    ).json()
    await settle(client, factory, hotel, stay["id"])
    gm = await factory.step_up(hotel, "general_manager", await factory.auth(hotel, "general_manager"))
    out = await client.post(
        f"/stays/{stay['id']}/checkout", json={"bill_delivery": ["pdf", "email"]}, headers={**gm, **idem()}
    )
    assert out.status_code == 200, out.text
    recipient = out.json()["invoice"]["recipient"]
    assert recipient | {"address": None} == {
        "type": "company",
        "name": "ABC Tech (Pty) Ltd",
        "registration_number": None,
        "vat_number": "4987654321",
        "address": None,
        "email": "accounts@abctech.example",
        "purchase_order": "PO-7781",
        "traveller": "Thandi Mokoena",
    }
    assert out.json()["emailed_to"] == ["accounts@abctech.example"]
    assert out.json()["invoice"]["kind"] == "tax_invoice"


async def test_long_stay_needs_vat_confirmation(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel, nights=30)
    await settle(client, factory, hotel, stay["id"])
    gm = await factory.step_up(hotel, "general_manager", await factory.auth(hotel, "general_manager"))
    summary = (await client.get(f"/stays/{stay['id']}/checkout-summary", headers=gm)).json()
    assert summary["flags"] == ["long_stay"]
    r = await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**gm, **idem()})
    assert r.json()["error"]["details"]["reason"] == "long_stay_confirmation_required"
    r = await client.post(
        f"/stays/{stay['id']}/checkout", json={"confirm_long_stay_vat": True}, headers={**gm, **idem()}
    )
    assert r.status_code == 200 and r.json()["invoice"]["flags"] == ["long_stay"]


async def test_credit_note_cancels_and_reopens_the_bill(client, factory, owner_engine, mailbox):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel, nights=1)
    rec = await factory.auth(hotel, "receptionist")
    await laundry(client, rec, stay["id"], owner_engine)
    await settle(client, factory, hotel, stay["id"])
    gm = await factory.step_up(hotel, "general_manager", await factory.auth(hotel, "general_manager"))
    invoice = (await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**gm, **idem()})).json()[
        "invoice"
    ]

    rec_s = await factory.step_up(hotel, "receptionist", rec)
    denied = await client.post(
        f"/invoices/{invoice['id']}/credit-note",
        json={"reason": "Laundry was free"},
        headers={**rec_s, **idem()},
    )
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
    no_step_up = await client.post(
        f"/invoices/{invoice['id']}/credit-note",
        json={"reason": "Laundry was free"},
        headers={**(await factory.auth(hotel, "general_manager")), **idem()},
    )
    assert no_step_up.json()["error"]["code"] == "STEP_UP_REQUIRED"
    note = await client.post(
        f"/invoices/{invoice['id']}/credit-note",
        json={"reason": "Laundry was free"},
        headers={**gm, **idem()},
    )
    assert note.status_code == 201, note.text
    note = note.json()
    assert (note["kind"], note["credits_invoice_id"], note["reason"]) == (
        "credit_note",
        invoice["id"],
        "Laundry was free",
    )
    assert note["number"] == f"TST-{date.today().year}-000002"
    assert note["totals"]["charges"] == zar(-invoice["totals"]["charges"]["amount_minor"])
    twice = await client.post(
        f"/invoices/{invoice['id']}/credit-note", json={"reason": "Again"}, headers={**gm, **idem()}
    )
    assert twice.json()["error"]["code"] == "INVALID_TRANSITION"

    # The bill re-opens for corrections; the room and tablet are untouched; checkout issues anew.
    folio = (await client.get(f"/folios/{stay['id']}", headers=rec)).json()
    assert folio["status"] == "open"
    entry = next(e for e in folio["entries"] if e["category"] == "laundry")
    rm = await factory.auth(hotel, "reception_manager")
    adj = (
        await client.post(
            "/adjustments",
            json={"folio_entry_id": entry["id"], "new_amount": zar(0), "reason": "Laundry was free"},
            headers={**rm, **idem()},
        )
    ).json()
    assert (
        await client.post(f"/adjustments/{adj['id']}/approve", headers={**gm, **idem()})
    ).status_code == 200
    reissued = await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**gm, **idem()})
    assert reissued.status_code == 200, reissued.text
    new = reissued.json()["invoice"]
    assert new["number"] == f"TST-{date.today().year}-000003"
    assert new["totals"]["other"] == zar(0) and new["totals"]["balance"] == zar(-10000)
    history = (await client.get(f"/stays/{stay['id']}/invoices", headers=gm)).json()["data"]
    assert [i["kind"] for i in history] == ["guest_statement", "credit_note", "guest_statement"]

    emailed = await client.post(
        f"/invoices/{note['id']}/email", json={"to": ["finance@example.com"]}, headers={**rec, **idem()}
    )
    assert emailed.json()["queued_to"] == ["finance@example.com"]
    assert any(m.to == "finance@example.com" and note["number"] in m.subject for m in mailbox.sent)


async def test_invoices_and_checkout_are_tenant_scoped(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    stay = await walk_in(client, factory, hotel, nights=1)
    await settle(client, factory, hotel, stay["id"])
    gm = await factory.step_up(hotel, "general_manager", await factory.auth(hotel, "general_manager"))
    invoice = (await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**gm, **idem()})).json()[
        "invoice"
    ]
    other = await factory.hotel(rooms=1)
    gm_b = await factory.step_up(other, "general_manager", await factory.auth(other, "general_manager"))
    for r in (
        await client.get(f"/invoices/{invoice['id']}", headers=gm_b),
        await client.get(f"/invoices/{invoice['id']}/pdf", headers=gm_b),
        await client.get(f"/stays/{stay['id']}/invoices", headers=gm_b),
        await client.get(f"/stays/{stay['id']}/checkout-summary", headers=gm_b),
        await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**gm_b, **idem()}),
        await client.post(
            f"/invoices/{invoice['id']}/email", json={"to": ["x@example.com"]}, headers={**gm_b, **idem()}
        ),
        await client.post(
            f"/invoices/{invoice['id']}/credit-note", json={"reason": "steal"}, headers={**gm_b, **idem()}
        ),
    ):
        assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND", r.text
