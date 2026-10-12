"""Diyneco's company billing settings and tax rates (DECISIONS D72): seeded with the names
only, edited by Super Admins with step-up and a reason, VAT only when consistently
registered, tax rates effective-dated and never rewritten once in force.

Settings are one shared row, so every test restores them; scheduled rates use Iceland (IS),
a country no other test bills in."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.api.test_admin import platform, step_up
from tests.api.test_room_service import idem

RESET = (
    "UPDATE app.company_settings SET legal_name = 'Diyneco Tech (Pty) Ltd', trading_name = 'Diyneco', "
    "registration_number = NULL, registered_address = '{}', business_address = '{}', billing_email = NULL, "
    "billing_phone = NULL, logo_path = NULL, vat_registered = false, vat_number = NULL, "
    "vat_effective_date = NULL, invoice_prefix = 'INV', credit_note_prefix = 'CN', number_padding = 6, "
    "number_reset = 'never', payment_terms_days = 7, bank_details = '{}', payment_instructions = NULL"
)


@pytest_asyncio.fixture(loop_scope="session")
async def fresh_company(owner_engine):
    async with owner_engine.begin() as conn:
        await conn.execute(text(RESET))
    yield
    async with owner_engine.begin() as conn:
        await conn.execute(text(RESET))
        await conn.execute(text("DELETE FROM app.tax_rates WHERE country = 'IS'"))


def _body(current: dict, **changes) -> dict:
    keep = [
        "legal_name",
        "trading_name",
        "registration_number",
        "registered_address",
        "business_address",
        "billing_email",
        "billing_phone",
        "vat_registered",
        "vat_number",
        "vat_effective_date",
        "invoice_prefix",
        "credit_note_prefix",
        "number_padding",
        "number_reset",
        "payment_terms_days",
        "bank_details",
        "payment_instructions",
    ]
    return {
        **{k: current[k] for k in keep},
        "version": current["version"],
        "reason": "Test change",
        **changes,
    }


async def test_seeded_with_names_only_and_never_invented(client, factory, fresh_company):
    admin = await platform(factory)
    out = await client.get("/admin/company", headers=admin)
    assert out.status_code == 200, out.text
    c = out.json()
    assert (c["legal_name"], c["trading_name"], c["country"], c["currency"], c["timezone"]) == (
        "Diyneco Tech (Pty) Ltd",
        "Diyneco",
        "ZA",
        "ZAR",
        "Africa/Johannesburg",
    )
    assert (
        c["registration_number"] is None and c["vat_number"] is None and not any(c["bank_details"].values())
    )
    assert c["vat_registered"] is False
    assert c["tax_today"] == {"charged": False, "tax_name": None, "rate_bp": None}
    assert c["invoice_example"] == "Invoice INV-000001"
    assert set(c["missing"]) == {
        "registration_number",
        "registered_address",
        "billing_email",
        "payment_instructions",
    }

    support = await platform(factory, "platform_support")
    assert (await client.get("/admin/company", headers=support)).json()["error"][
        "code"
    ] == "PERMISSION_DENIED"
    hotel = await factory.hotel()
    owner = await factory.auth(hotel, "hotel_owner")
    assert (await client.get("/admin/company", headers=owner)).status_code in (401, 403)


async def test_edits_need_step_up_a_reason_and_the_current_version(
    client, factory, fresh_company, owner_engine
):
    admin = await platform(factory)
    c = (await client.get("/admin/company", headers=admin)).json()
    body = _body(
        c,
        registration_number="2026/123456/07",
        registered_address={
            "line1": "1 Long Street",
            "city": "Cape Town",
            "postal_code": "8001",
            "country": "ZA",
        },
        billing_email="billing@diyneco.co.za",
        bank_details={"bank_name": "Test Bank", "account_number": "1234567890", "branch_code": "250655"},
        payment_terms_days=14,
    )
    assert (await client.put("/admin/company", json=body, headers=admin)).json()["error"][
        "code"
    ] == "STEP_UP_REQUIRED"
    no_reason = await client.put(
        "/admin/company", json={**body, "reason": ""}, headers=step_up(factory, admin)
    )
    assert no_reason.json()["error"]["code"] == "VALIDATION_FAILED"
    bad_reg = await client.put(
        "/admin/company", json={**body, "registration_number": "123"}, headers=step_up(factory, admin)
    )
    assert bad_reg.json()["error"]["details"]["fields"][0]["field"] == "registration_number"

    saved = await client.put("/admin/company", json=body, headers=step_up(factory, admin))
    assert saved.status_code == 200, saved.text
    assert saved.json()["version"] == c["version"] + 1 and saved.json()["payment_terms_days"] == 14
    assert saved.json()["missing"] == []
    stale = await client.put("/admin/company", json=body, headers=step_up(factory, admin))
    assert stale.json()["error"]["code"] == "PRECONDITION_FAILED"

    async with owner_engine.connect() as conn:
        entry = (
            await conn.execute(
                text(
                    "SELECT new_value FROM app.audit_logs WHERE action = 'platform.company_tax_changed' "
                    "ORDER BY created_at DESC LIMIT 1"
                )
            )
        ).scalar_one()
    assert entry["reason"] == "Test change"
    assert (
        entry["from"]["registration_number"] is None
        and entry["to"]["registration_number"] == "2026/123456/07"
    )
    # Bank account numbers never land in the audit log in full.
    assert entry["to"]["bank_details"]["account_number"] == "…7890"


async def test_vat_registration_must_be_complete_and_charges_from_its_date(client, factory, fresh_company):
    admin = await platform(factory)
    c = (await client.get("/admin/company", headers=admin)).json()
    put = lambda **k: client.put("/admin/company", json=_body(c, **k), headers=step_up(factory, admin))  # noqa: E731
    missing_number = await put(vat_registered=True, vat_effective_date="2026-01-01")
    assert missing_number.json()["error"]["details"]["fields"][0]["field"] == "vat_number"
    bad_number = await put(vat_registered=True, vat_number="123", vat_effective_date="2026-01-01")
    assert bad_number.json()["error"]["details"]["fields"][0]["field"] == "vat_number"
    no_date = await put(vat_registered=True, vat_number="4123456789")
    assert no_date.json()["error"]["details"]["fields"][0]["field"] == "vat_effective_date"
    no_identity = await put(vat_registered=True, vat_number="4123456789", vat_effective_date="2026-01-01")
    assert no_identity.json()["error"]["details"]["fields"][0]["field"] == "vat_registered"

    identity = {"registration_number": "2026/123456/07", "registered_address": {"line1": "1 Long Street"}}
    future = (date.today() + timedelta(days=30)).isoformat()
    later = await put(vat_registered=True, vat_number="4123456789", vat_effective_date=future, **identity)
    assert later.status_code == 200, later.text
    assert later.json()["tax_today"]["charged"] is False  # not yet in effect
    c = later.json()
    now = await put(vat_registered=True, vat_number="4123456789", vat_effective_date="2026-01-01", **identity)
    assert now.json()["tax_today"] == {"charged": True, "tax_name": "VAT", "rate_bp": 1500}
    assert now.json()["invoice_example"].startswith("Tax invoice ")


async def test_rates_are_scheduled_ahead_and_never_rewritten(client, factory, fresh_company, owner_engine):
    admin = await platform(factory)
    tomorrow = date.today() + timedelta(days=2)
    body = {
        "country": "IS",
        "tax_name": "VSK",
        "rate_bp": 2400,
        "effective_from": tomorrow.isoformat(),
        "reason": "Law",
    }
    past = await client.post(
        "/admin/tax-rates",
        json={**body, "effective_from": "2020-01-01"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert past.json()["error"]["details"]["fields"][0]["field"] == "effective_from"
    made = await client.post("/admin/tax-rates", json=body, headers={**step_up(factory, admin), **idem()})
    assert made.status_code == 201, made.text
    row = next(r for r in made.json()["data"] if r["country"] == "IS")
    assert row["scheduled"] and not row["in_force"]
    za = next(r for r in made.json()["data"] if r["country"] == "ZA")
    assert za["in_force"] and za["rate_bp"] == 1500

    twice = await client.post("/admin/tax-rates", json=body, headers={**step_up(factory, admin), **idem()})
    assert twice.json()["error"]["code"] == "INVALID_TRANSITION"
    gone = await client.delete(f"/admin/tax-rates/{row['id']}", headers=step_up(factory, admin))
    assert gone.status_code == 200 and all(r["country"] != "IS" for r in gone.json()["data"])
    in_force = await client.delete(f"/admin/tax-rates/{za['id']}", headers=step_up(factory, admin))
    assert in_force.json()["error"]["code"] == "INVALID_TRANSITION"

    # The database refuses rewriting a rate, even from the owner role.
    with pytest.raises(DBAPIError, match="append-only"):
        async with owner_engine.begin() as conn:
            await conn.execute(text("UPDATE app.tax_rates SET rate_bp = 1400 WHERE id = :i"), {"i": za["id"]})
    with pytest.raises(DBAPIError, match="already in force"):
        async with owner_engine.begin() as conn:
            await conn.execute(text("DELETE FROM app.tax_rates WHERE id = :i"), {"i": za["id"]})


async def test_logo_upload_is_png_or_jpeg(client, factory, fresh_company):
    admin = await platform(factory)
    svg = await client.post(
        "/admin/company/logo",
        json={"content_type": "image/svg+xml", "size_bytes": 100},
        headers=step_up(factory, admin),
    )
    assert svg.json()["error"]["code"] == "VALIDATION_FAILED"
    ok = await client.post(
        "/admin/company/logo",
        json={"content_type": "image/png", "size_bytes": 1000},
        headers=step_up(factory, admin),
    )
    assert ok.status_code == 200, ok.text
    after = (await client.get("/admin/company", headers=admin)).json()
    assert after["logo_url"] and after["version"] > 1
