"""Diyneco's invoices and credit notes to hotels (DECISIONS D78): drafted and issued by billing
administrators, numbered safely under concurrent requests, frozen by the database once issued,
corrected only by voiding (plain, unpaid) or credit notes, and visible to their own hotel only.

Company settings are one shared row: tests that switch VAT on restore it."""

from __future__ import annotations

import asyncio
import re

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.api.test_admin import platform, step_up
from tests.api.test_room_service import idem
from tests.api.test_subscriptions import _vat

LINE = {"description": "Extra tablet setup", "unit_amount_minor": 50000}


async def _draft(client, admin, hotel_id, **body) -> dict:
    out = await client.post(
        f"/admin/hotels/{hotel_id}/invoices",
        json={"currency": "ZAR", "lines": [LINE], "reason": "Approved by ops", **body},
        headers={**admin, **idem()},
    )
    assert out.status_code == 201, out.text
    return out.json()


async def _issue(client, factory, admin, hotel_id, invoice_id):
    return await client.post(
        f"/admin/hotels/{hotel_id}/invoices/{invoice_id}/issue", headers={**step_up(factory, admin), **idem()}
    )


async def test_a_manual_invoice_is_drafted_issued_numbered_and_emailed(
    client, factory, owner_engine, mailbox, app_state
):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    hotel = await factory.hotel()
    draft = await _draft(
        client,
        admin,
        hotel.id,
        lines=[LINE, {"description": "Training", "quantity": 2, "unit_amount_minor": 25000}],
    )
    assert draft["status"] == "draft" and draft["number"] is None and draft["is_tax_invoice"] is False
    assert (
        draft["subtotal"]["amount_minor"],
        draft["tax"]["amount_minor"],
        draft["total"]["amount_minor"],
    ) == (
        100000,
        0,
        100000,
    )
    owner = await factory.auth(hotel, "hotel_owner")
    # The hotel never sees Diyneco's drafts.
    assert (await client.get("/subscription/invoices", headers=owner)).json()["data"] == []
    assert (await client.get(f"/subscription/invoices/{draft['id']}", headers=owner)).status_code == 404

    no_step_up = await client.post(
        f"/admin/hotels/{hotel.id}/invoices/{draft['id']}/issue", headers={**admin, **idem()}
    )
    assert no_step_up.json()["error"]["code"] == "STEP_UP_REQUIRED"
    issued = await _issue(client, factory, admin, hotel.id, draft["id"])
    assert issued.status_code == 200, issued.text
    inv = issued.json()
    assert inv["status"] == "issued" and re.fullmatch(r"INV-\d{6}", inv["number"])
    assert inv["seller"]["legal_name"] == "Diyneco Tech (Pty) Ltd" and inv["seller"]["vat_number"] is None
    assert inv["buyer"]["hotel_name"] == hotel.name and inv["due_on"] and inv["has_pdf"]
    assert inv["balance"]["amount_minor"] == 100000

    mail = next(
        m
        for m in reversed(mailbox.sent)
        if m.template == "subscription_invoice" and inv["number"] in m.subject
    )
    assert mail.subject.startswith("Diyneco: Invoice ") and mail.attachments[0][0] == f"{inv['number']}.pdf"
    assert mail.attachments[0][1][:4] == b"%PDF"

    mine = (await client.get("/subscription/invoices", headers=owner)).json()["data"]
    assert [i["number"] for i in mine] == [inv["number"]]
    link = await client.get(f"/subscription/invoices/{inv['id']}/pdf", headers=owner)
    assert link.status_code == 200 and link.json()["url"].startswith("http")
    twice = await _issue(client, factory, admin, hotel.id, draft["id"])
    assert twice.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_numbers_stay_unique_under_concurrent_issues(client, factory):
    admin = await platform(factory)
    hotel = await factory.hotel()
    drafts = [await _draft(client, admin, hotel.id) for _ in range(6)]
    headers = step_up(factory, admin)
    results = await asyncio.gather(
        *[
            client.post(f"/admin/hotels/{hotel.id}/invoices/{d['id']}/issue", headers={**headers, **idem()})
            for d in drafts
        ]
    )
    numbers = [r.json()["number"] for r in results]
    assert all(r.status_code == 200 for r in results), [r.text for r in results]
    assert len(set(numbers)) == 6
    values = sorted(int(n.split("-")[-1]) for n in numbers)
    assert values == list(range(values[0], values[0] + 6))  # gapless


async def test_an_issued_invoice_is_frozen_by_the_database(client, factory, owner_engine):
    admin = await platform(factory)
    hotel = await factory.hotel()
    inv = (
        await _issue(client, factory, admin, hotel.id, (await _draft(client, admin, hotel.id))["id"])
    ).json()
    for sql in (
        "UPDATE app.subscription_invoices SET total_minor = 1, subtotal_minor = 1 WHERE id = :i",
        "UPDATE app.subscription_invoices SET buyer = '{}' WHERE id = :i",
        "UPDATE app.subscription_invoices SET pdf_path = 'elsewhere.pdf' WHERE id = :i",
        "DELETE FROM app.subscription_invoices WHERE id = :i",
    ):
        with pytest.raises(DBAPIError, match=r"frozen|never deleted"):
            async with owner_engine.begin() as conn:
                await conn.execute(text(sql), {"i": inv["id"]})
    with pytest.raises(DBAPIError, match="cannot go from"):
        async with owner_engine.begin() as conn:
            await conn.execute(
                text("UPDATE app.subscription_invoices SET status = 'draft' WHERE id = :i"), {"i": inv["id"]}
            )
    with pytest.raises(DBAPIError, match="only be added to a draft"):
        async with owner_engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO app.subscription_invoice_lines (hotel_id, invoice_id, position, code, description, "
                    "unit_amount_minor, total_minor) VALUES (:h, :i, 9, 'x', 'x', 1, 1)"
                ),
                {"h": hotel.id, "i": inv["id"]},
            )


async def test_tax_invoices_carry_vat_and_are_corrected_by_credit_notes(client, factory, owner_engine):
    admin = await platform(factory)
    hotel = await factory.hotel()
    try:
        await _vat(owner_engine, on=True)
        draft = await _draft(client, admin, hotel.id)
        assert draft["is_tax_invoice"] and (draft["tax"]["amount_minor"], draft["total"]["amount_minor"]) == (
            7500,
            57500,
        )
        inv = (await _issue(client, factory, admin, hotel.id, draft["id"])).json()
        assert inv["seller"]["vat_number"] == "4123456789" and inv["tax_rate_bp"] == 1500

        void = await client.post(
            f"/admin/hotels/{hotel.id}/invoices/{inv['id']}/void",
            json={"reason": "Wrong hotel"},
            headers={**step_up(factory, admin), **idem()},
        )
        assert void.json()["error"]["code"] == "INVALID_TRANSITION"  # a tax invoice is credited, never voided

        url = f"/admin/hotels/{hotel.id}/invoices/{inv['id']}/credit"
        too_much = await client.post(
            url,
            json={"reason": "Goodwill", "amount_minor": 60000},
            headers={**step_up(factory, admin), **idem()},
        )
        assert too_much.json()["error"]["code"] == "VALIDATION_FAILED"
        part = await client.post(
            url,
            json={"reason": "Goodwill", "amount_minor": 11500},
            headers={**step_up(factory, admin), **idem()},
        )
        assert part.status_code == 201, part.text
        note = part.json()
        assert note["kind"] == "credit_note" and re.fullmatch(r"CN-\d{6}", note["number"])
        assert (note["total"]["amount_minor"], note["tax"]["amount_minor"]) == (11500, 1500)
        assert note["credits_number"] == inv["number"]
        rest = await client.post(
            url, json={"reason": "Cancelled order"}, headers={**step_up(factory, admin), **idem()}
        )
        assert rest.json()["total"]["amount_minor"] == 46000
        original = (
            await client.get(
                f"/subscription/invoices/{inv['id']}", headers=await factory.auth(hotel, "hotel_owner")
            )
        ).json()
        assert original["status"] == "credited" and original["credited"]["amount_minor"] == 57500
        assert original["balance"]["amount_minor"] == 0

        # The VAT position changed after drafting: issuing is refused rather than wrong.
        stale = await _draft(client, admin, hotel.id)
        await _vat(owner_engine, on=False)
        refused = await _issue(client, factory, admin, hotel.id, stale["id"])
        assert refused.json()["error"]["code"] == "INVALID_TRANSITION"
    finally:
        await _vat(owner_engine, on=False)


async def test_plain_unpaid_invoices_and_drafts_can_be_voided(client, factory, owner_engine):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    hotel = await factory.hotel()
    draft = await _draft(client, admin, hotel.id)
    discarded = await client.post(
        f"/admin/hotels/{hotel.id}/invoices/{draft['id']}/void",
        json={"reason": "Typo"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert discarded.json()["status"] == "void" and discarded.json()["number"] is None
    inv = (
        await _issue(client, factory, admin, hotel.id, (await _draft(client, admin, hotel.id))["id"])
    ).json()
    voided = await client.post(
        f"/admin/hotels/{hotel.id}/invoices/{inv['id']}/void",
        json={"reason": "Charged twice"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert (
        voided.json()["status"] == "void" and voided.json()["number"] == inv["number"]
    )  # the number is never reused
    async with owner_engine.connect() as conn:
        events = (
            await conn.execute(
                text(
                    "SELECT status_from, status_to, reason FROM app.subscription_invoice_events WHERE invoice_id = :i ORDER BY created_at"
                ),
                {"i": inv["id"]},
            )
        ).all()
    assert [(e.status_from, e.status_to) for e in events] == [
        (None, "draft"),
        ("draft", "issued"),
        ("issued", "void"),
    ]
    assert events[-1].reason == "Charged twice"


async def test_invoices_belong_to_their_hotel_and_to_billing_administrators(client, factory):
    admin = await platform(factory)
    support = await platform(factory, "platform_support")
    a = await factory.hotel(roles=("hotel_owner", "receptionist"))
    b = await factory.hotel()
    inv = (await _issue(client, factory, admin, a.id, (await _draft(client, admin, a.id))["id"])).json()
    owner_b = await factory.auth(b, "hotel_owner")
    assert (await client.get(f"/subscription/invoices/{inv['id']}", headers=owner_b)).status_code == 404
    assert (await client.get(f"/subscription/invoices/{inv['id']}/pdf", headers=owner_b)).status_code == 404
    assert inv["id"] not in [
        i["id"] for i in (await client.get("/subscription/invoices", headers=owner_b)).json()["data"]
    ]
    receptionist = await factory.auth(a, "receptionist")
    assert (await client.get("/subscription/invoices", headers=receptionist)).json()["error"][
        "code"
    ] == "PERMISSION_DENIED"
    denied = await client.post(
        f"/admin/hotels/{a.id}/invoices",
        json={"currency": "ZAR", "lines": [LINE], "reason": "Sneaky"},
        headers={**support, **idem()},
    )
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
    # Amounts and tax come from the server; a client cannot send totals.
    sneaky = await client.post(
        f"/admin/hotels/{a.id}/invoices",
        json={"currency": "ZAR", "lines": [LINE], "reason": "x" * 5, "total_minor": 1},
        headers={**admin, **idem()},
    )
    assert sneaky.json()["error"]["code"] == "VALIDATION_FAILED"
