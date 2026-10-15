"""Operational countries, the richer sign-up form and the emailed sign-up code (DECISIONS D84).

Japan (JP) and Kenya (KE) are switched on and off here only; every test puts them back."""

from __future__ import annotations

import re
import secrets
import uuid

import pytest_asyncio
from sqlalchemy import text

from app.core.countries import COUNTRIES
from tests.api.test_admin import platform, step_up


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


@pytest_asyncio.fixture(loop_scope="session")
async def restore_countries(owner_engine):
    yield
    async with owner_engine.begin() as conn:
        await conn.execute(text("DELETE FROM app.operational_countries WHERE country IN ('JP', 'KE')"))


def signup_body(**hotel) -> dict:
    return {
        "owner": {
            "name": "Lindiwe Owner",
            "email": f"owner.{secrets.token_hex(4)}@example.com",
            "password": f"Owner-Password-{secrets.token_hex(4)}",
            "phone": "+27821234567",
        },
        "hotel": {"name": "Sunbird Lodge", "country": "ZA", **hotel},
    }


def code_from(mailbox, email: str) -> str:
    message = [m for m in mailbox.sent if m.to == email and m.template == "email_verify"][-1]
    m = re.match(r"^(\d{6}) is your Diyneco confirmation code$", message.subject)
    assert m, message.subject
    assert m.group(1) in message.body
    return m.group(1)


def test_every_inhabited_country_is_known_with_its_zones():
    assert len(COUNTRIES) == 242
    for c in COUNTRIES.values():
        assert c.timezones and c.timezones[0] == c.timezone, c.code
    assert (
        COUNTRIES["US"].timezone == "America/New_York" and "America/Los_Angeles" in COUNTRIES["US"].timezones
    )
    assert COUNTRIES["ZA"].tax_rate_bp == 1500  # the detailed entries are kept
    assert COUNTRIES["KR"].currency == "KRW" and COUNTRIES["KR"].tax_rate_bp is None


async def test_signup_lists_only_operational_countries(client, factory, restore_countries):
    listed = {c["code"]: c for c in (await client.get("/countries")).json()["data"]}
    assert "ZA" in listed and "JP" not in listed
    assert listed["ZA"]["timezones"] == ["Africa/Johannesburg"]

    admin = await platform(factory)
    support = await platform(factory, "platform_support")
    assert (await client.get("/admin/countries", headers=support)).status_code == 403
    every = (await client.get("/admin/countries", headers=admin)).json()["data"]
    assert len(every) == 242
    za = next(c for c in every if c["code"] == "ZA")
    assert za["operational"] is True and za["hotels"] >= 0

    change = {"operational": True, "reason": "Launching in Japan"}
    assert (await client.put("/admin/countries/JP", json=change, headers=admin)).status_code == 403  # step-up
    on = await client.put("/admin/countries/JP", json=change, headers=step_up(factory, admin))
    assert on.status_code == 200, on.text
    assert on.json()["operational"] is True and on.json()["enabled_at"] is not None
    assert "JP" in {c["code"] for c in (await client.get("/countries")).json()["data"]}
    unknown = await client.put("/admin/countries/XX", json=change, headers=step_up(factory, admin))
    assert unknown.status_code == 404

    off = await client.put(
        "/admin/countries/JP",
        json={"operational": False, "reason": "Paused"},
        headers=step_up(factory, admin),
    )
    assert off.json()["operational"] is False
    assert "JP" not in {c["code"] for c in (await client.get("/countries")).json()["data"]}


async def test_country_changes_are_audited(client, factory, owner_engine, restore_countries):
    admin = await platform(factory)
    r = await client.put(
        "/admin/countries/KE",
        json={"operational": True, "reason": "Nairobi pilot"},
        headers=step_up(factory, admin),
    )
    assert r.status_code == 200
    async with owner_engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT action, new_value FROM app.audit_logs WHERE action = 'platform.country_enabled' "
                    "AND new_value->>'country' = 'KE' ORDER BY created_at DESC LIMIT 1"
                )
            )
        ).one()
    assert row.new_value["reason"] == "Nairobi pilot"


async def test_signup_refuses_countries_that_are_not_operational(client):
    r = await client.post("/signup", json=signup_body(country="JP"), headers=idem())
    assert r.status_code == 400
    assert r.json()["error"]["details"]["fields"][0]["field"] == "hotel.country"


async def test_signup_keeps_the_profile_and_checks_the_time_zone(client, owner_engine):
    wrong_zone = await client.post("/signup", json=signup_body(timezone="Europe/London"), headers=idem())
    assert wrong_zone.json()["error"]["details"]["fields"][0]["field"] == "hotel.timezone"

    body = signup_body(property_type="lodge", room_count=24, website="https://sunbird.example.com")
    r = await client.post("/signup", json=body, headers=idem())
    assert r.status_code == 201, r.text
    async with owner_engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT h.property_type, h.room_count, h.website, u.phone, s.currency FROM app.users u "
                    "JOIN app.hotel_users hu ON hu.user_id = u.id JOIN app.hotels h ON h.id = hu.hotel_id "
                    "JOIN app.hotel_settings s ON s.hotel_id = h.id WHERE u.email = :e"
                ),
                {"e": body["owner"]["email"]},
            )
        ).one()
    # No currency was sent: it follows the country.
    assert tuple(row) == ("lodge", 24, "https://sunbird.example.com", "+27821234567", "ZAR")

    bad = signup_body(room_count=0)
    bad["owner"]["phone"] = "082 123 4567"  # not international format
    refused = await client.post("/signup", json=bad, headers=idem())
    assert refused.status_code == 400
    fields = {f["field"] for f in refused.json()["error"]["details"]["fields"]}
    assert {"owner.phone", "hotel.room_count"} <= fields, fields


async def test_the_emailed_code_confirms_the_address_once(client, mailbox, owner_engine):
    body = signup_body()
    email = body["owner"]["email"]
    assert (await client.post("/signup", json=body, headers=idem())).status_code == 201
    code = code_from(mailbox, email)
    wrong = "000000" if code != "000000" else "111111"

    bad = await client.post("/auth/email/verify-code", json={"email": email, "code": wrong})
    assert bad.status_code == 400 and bad.json()["error"]["details"]["fields"][0]["field"] == "code"
    unknown = await client.post("/auth/email/verify-code", json={"email": f"x{email}", "code": code})
    assert unknown.json()["error"]["message"] == bad.json()["error"]["message"]  # no account discovery

    assert (
        await client.post("/auth/email/verify-code", json={"email": email, "code": code})
    ).status_code == 204
    assert (
        await client.post("/auth/email/verify-code", json={"email": email, "code": code})
    ).status_code == 400
    async with owner_engine.connect() as conn:
        verified = (
            await conn.execute(text("SELECT email_verified_at FROM app.users WHERE email = :e"), {"e": email})
        ).scalar_one()
    assert verified is not None


async def test_five_wrong_codes_end_a_code_and_resend_is_throttled(client, mailbox, owner_engine, app_state):
    body = signup_body()
    email = body["owner"]["email"]
    await client.post("/signup", json=body, headers=idem())
    code = code_from(mailbox, email)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        await client.post("/auth/email/verify-code", json={"email": email, "code": wrong})
    # The right code no longer works after 5 wrong tries.
    assert (
        await client.post("/auth/email/verify-code", json={"email": email, "code": code})
    ).status_code == 400

    sent = len(mailbox.sent)
    assert (await client.post("/auth/email/resend", json={"email": email})).status_code == 202
    assert len(mailbox.sent) == sent  # within a minute of the last code: nothing new
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE app.one_time_tokens SET created_at = created_at - interval '2 minutes' WHERE user_id = "
                "(SELECT id FROM app.users WHERE email = :e)"
            ),
            {"e": email},
        )
    assert (await client.post("/auth/email/resend", json={"email": email})).status_code == 202
    fresh = code_from(mailbox, email)
    assert (
        await client.post("/auth/email/verify-code", json={"email": email, "code": fresh})
    ).status_code == 204
    # Unknown and confirmed addresses get the same answer and no email.
    await app_state.limiter.reset()  # these routes allow 10 calls a minute per address
    sent = len(mailbox.sent)
    for address in (email, f"nobody.{secrets.token_hex(3)}@example.com"):
        assert (await client.post("/auth/email/resend", json={"email": address})).status_code == 202
    assert len(mailbox.sent) == sent
