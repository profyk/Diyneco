"""Worldwide hotels: country catalogue, data region, locale, tax IDs and currency decimals (D69)."""

from __future__ import annotations

import secrets

import pytest
from sqlalchemy import text

from app.core.countries import COUNTRIES, tax_id_ok
from app.core.currencies import CURRENCIES, format_minor, to_minor
from tests.api.test_room_service import idem


def test_catalogues_are_consistent():
    import zoneinfo

    for c in COUNTRIES.values():
        zoneinfo.ZoneInfo(c.timezone)
        assert c.currency in CURRENCIES, c.code
    assert (
        CURRENCIES["JPY"].decimals == 0
        and CURRENCIES["BHD"].decimals == 3
        and CURRENCIES["ZAR"].decimals == 2
    )


@pytest.mark.parametrize(
    ("country", "value", "ok"),
    [
        ("ZA", "4123456789", True),
        ("ZA", "123", False),
        ("GB", "GB123456789", True),
        ("DE", "DE123456789", True),
        ("AU", "51 824 753 556", True),
        ("IN", "27AAPFU0939F1ZV", True),
        ("IN", "12345", False),
        ("KE", "P051234567A", True),
        ("BW", "C01234567", True),  # no listed format: the general rule applies
        ("BW", "x", False),
    ],
)
def test_tax_ids_follow_the_country(country, value, ok):
    assert tax_id_ok(country, value) is ok


def test_amounts_follow_the_currency_decimals():
    assert (
        to_minor("1500", "JPY") == 1500
        and to_minor("12.50", "EUR") == 1250
        and to_minor("2.125", "BHD") == 2125
    )
    with pytest.raises(ValueError):
        to_minor("1.5", "JPY")
    assert format_minor(150000, "ZAR") == "R 1,500.00"
    assert format_minor(1500, "JPY") == "¥ 1,500"
    assert format_minor(2125, "BHD") == "BHD 2.125"


async def test_countries_endpoint_is_public(client):
    r = await client.get("/countries")
    assert r.status_code == 200
    za = next(c for c in r.json()["data"] if c["code"] == "ZA")
    assert za["currency"] == "ZAR" and za["region"] == "af-south" and za["tax_label"] == "VAT"
    yen = next(c for c in (await client.get("/currencies")).json()["data"] if c["code"] == "JPY")
    assert yen["decimals"] == 0


async def test_signup_takes_country_defaults(client, factory, owner_engine):
    async with owner_engine.begin() as conn:  # Japan takes signups for this test only (D84)
        await conn.execute(
            text("INSERT INTO app.operational_countries (country) VALUES ('JP') ON CONFLICT DO NOTHING")
        )
    try:
        await _signup_in_japan(client, owner_engine)
    finally:
        async with owner_engine.begin() as conn:
            await conn.execute(text("DELETE FROM app.operational_countries WHERE country = 'JP'"))


async def _signup_in_japan(client, owner_engine):
    email = f"owner.{secrets.token_hex(3)}@example.com"
    body = {
        "owner": {"name": "Aiko Owner", "email": email, "password": f"Owner-Password-{secrets.token_hex(4)}"},
        "hotel": {"name": "Kyoto Garden Inn", "country": "JP"},  # currency follows the country
    }
    r = await client.post("/signup", json=body, headers=idem())
    assert r.status_code in (200, 201, 202), r.text
    async with owner_engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT s.currency, s.timezone, s.locale, h.data_region FROM app.hotels h "
                    "JOIN app.hotel_settings s ON s.hotel_id = h.id WHERE h.name = 'Kyoto Garden Inn'"
                )
            )
        ).one()
    assert tuple(row) == ("JPY", "Asia/Tokyo", "ja-JP", "ap-southeast")
    unknown = await client.post(
        "/signup",
        json={
            **body,
            "owner": {**body["owner"], "email": f"x{email}"},
            "hotel": {**body["hotel"], "country": "XX"},
        },
        headers=idem(),
    )
    assert unknown.json()["error"]["details"]["fields"][0]["field"] == "hotel.country"


async def test_hotel_settings_show_locale_and_tax_label_and_check_tax_ids(client, factory):
    hotel = await factory.hotel(roles=("general_manager",))
    gm = await factory.auth(hotel, "general_manager")
    settings = await client.get("/hotel/settings", headers=gm)
    assert settings.json()["locale"] == "en-ZA" and settings.json()["tax_label"] == "VAT"
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    bad = await client.patch(
        "/hotel/settings",
        json={"vat_number": "GB123"},
        headers={**gm_s, "If-Match": settings.headers["ETag"]},
    )
    assert bad.json()["error"]["details"]["fields"][0]["field"] == "vat_number"
    good = await client.patch(
        "/hotel/settings",
        json={"vat_number": "4123456789", "locale": "en-GB", "tax_label": "VAT"},
        headers={**gm_s, "If-Match": settings.headers["ETag"]},
    )
    assert good.status_code == 200, good.text
    assert good.json()["locale"] == "en-GB"
    hotel_out = (await client.get("/hotel", headers=gm)).json()
    assert hotel_out["country"] == "ZA" and hotel_out["data_region"] == "af-south"


def test_web_apps_use_the_same_currency_decimals():
    """packages/api-client keeps its own table; it must match the API's catalogue exactly."""
    import re
    from pathlib import Path

    source = (Path(__file__).parents[3] / "packages/api-client/src/money.ts").read_text(encoding="utf-8")

    def listed(name: str) -> set[str]:
        m = re.search(name + r" = new Set\(\[([^\]]*)\]\)", source)
        assert m, name
        return set(re.findall(r'"([A-Z]{3})"', m.group(1)))

    assert listed("ZERO_DECIMALS") == {c.code for c in CURRENCIES.values() if c.decimals == 0}
    assert listed("THREE_DECIMALS") == {c.code for c in CURRENCIES.values() if c.decimals == 3}


def test_bills_name_the_hotels_tax_and_print_every_currency():
    from app.billing import invoice_pdf

    assert invoice_pdf.amount(125000, "TRY") == "TRY 1,250.00"  # ₺ is not in the PDF fonts
    assert invoice_pdf.amount(1500, "JPY") == "¥ 1,500"
    assert invoice_pdf.amount(2125, "BHD") == "BHD 2.125"
    assert invoice_pdf._tax({"tax_label": "GST"}) == "GST"
    assert invoice_pdf._tax({}) == "VAT"  # invoices issued before D69
    doc = {
        "title": "Tax Invoice",
        "kind": "tax_invoice",
        "number": "AUS-2026-000001",
        "issued_at": "2026-10-12 10:00",
        "currency": "AUD",
        "supplier": {"name": "Harbour Hotel", "vat_number": "51824753556", "tax_label": "GST"},
        "recipient": {"name": "A Guest", "address": {"line1": "1 George St"}},
        "totals": {
            "accommodation_minor": 22000,
            "fnb_minor": 0,
            "other_minor": 0,
            "charges_minor": 22000,
            "vat_minor": 2000,
            "tips_minor": 0,
            "paid_minor": 0,
            "balance_minor": 22000,
            "flags": [],
        },
        "items": [{"description": "Night", "quantity": 1, "vat_rate_bp": 1000, "amount_minor": 22000}],
        "vat_registered": True,
        "vat_rate_bp": 1000,
    }
    assert invoice_pdf.render(doc).startswith(b"%PDF")


async def test_me_carries_the_hotels_locale_time_zone_and_tax_name(client, factory):
    hotel = await factory.hotel(roles=("general_manager",))
    gm = await factory.auth(hotel, "general_manager")
    me = (await client.get("/auth/me", headers=gm)).json()["hotel"]
    assert (me["locale"], me["timezone"], me["tax_label"]) == ("en-ZA", "Africa/Johannesburg", "VAT")
