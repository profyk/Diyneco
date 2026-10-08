"""Signup, hotel profile and settings, permissions and roles, cross-tenant access."""

from __future__ import annotations

import secrets
import uuid

import pytest
from sqlalchemy import text

from app.services.signup import invoice_prefix


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


def signup_body(email: str | None = None) -> dict:
    return {
        "owner": {
            "name": "Naledi Khumalo",
            "email": email or f"naledi.{secrets.token_hex(3)}@example.com",
            "password": f"Owner-Password-{secrets.token_hex(4)}",
        },
        "hotel": {
            "name": "Grand Example Hotel",
            "phone": "+27 21 555 0100",
            "address": {"line1": "1 Beach Rd", "city": "Cape Town", "country": "ZA"},
        },
    }


async def test_signup_creates_pending_hotel_owner_and_outbox_event(client, owner_engine, mailbox):
    body = signup_body()
    r = await client.post("/signup", json=body, headers=idem())
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "verification_sent"
    assert "access_token" not in r.text  # no tokens from signup (G12)
    async with owner_engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT h.id, h.status, s.invoice_prefix, p.code AS plan, sub.status AS sub_status, r.code AS role, "
                    "es.last_seq FROM app.users u JOIN app.hotel_users hu ON hu.user_id = u.id "
                    "JOIN app.hotels h ON h.id = hu.hotel_id JOIN app.hotel_settings s ON s.hotel_id = h.id "
                    "JOIN app.subscriptions sub ON sub.hotel_id = h.id JOIN app.plans p ON p.id = sub.plan_id "
                    "JOIN app.user_roles ur ON ur.hotel_user_id = hu.id JOIN app.roles r ON r.id = ur.role_id "
                    "JOIN app.event_seq es ON es.hotel_id = h.id WHERE u.email = :e"
                ),
                {"e": body["owner"]["email"]},
            )
        ).one()
        events = (
            await conn.execute(
                text("SELECT type, seq, channels FROM app.event_outbox WHERE hotel_id = :h"), {"h": row.id}
            )
        ).all()
    assert (row.status, row.invoice_prefix, row.plan, row.sub_status, row.role) == (
        "pending_approval",
        "GEH",
        "starter",
        "trialing",
        "hotel_owner",
    )
    assert [(e.type, e.seq, e.channels) for e in events] == [("TENANT_CREATED", 1, ["platform"])]
    assert row.last_seq == 1
    assert any(m.to == body["owner"]["email"] and m.template == "email_verify" for m in mailbox.sent)


async def test_signup_with_existing_email_reveals_nothing(client, mailbox, owner_engine):
    body = signup_body()
    await client.post("/signup", json=body, headers=idem())
    again = await client.post("/signup", json={**body, "hotel": {"name": "Second Hotel"}}, headers=idem())
    assert again.status_code == 201
    assert again.json() == (await client.post("/signup", json=signup_body(), headers=idem())).json()
    assert mailbox.sent[-2].template == "signup_existing_account" or any(
        m.template == "signup_existing_account" and m.to == body["owner"]["email"] for m in mailbox.sent
    )
    async with owner_engine.connect() as conn:
        count = (
            await conn.execute(text("SELECT count(*) FROM app.hotels WHERE name = 'Second Hotel'"))
        ).scalar_one()
    assert count == 0


async def test_signup_rejects_weak_password_and_unknown_fields(client):
    weak = signup_body()
    weak["owner"]["password"] = "short"
    assert (await client.post("/signup", json=weak, headers=idem())).status_code == 400
    extra = signup_body()
    extra["hotel"]["status"] = "active"
    r = await client.post("/signup", json=extra, headers=idem())
    assert r.status_code == 400
    assert r.json()["error"]["details"]["fields"][0]["type"] == "extra_forbidden"


def test_invoice_prefix_from_name():
    assert invoice_prefix("Grand Example Hotel") == "GEH"
    assert invoice_prefix("Seabreeze Lodge") == "SL"
    assert invoice_prefix("Mountain") == "MOU"


async def test_get_and_patch_hotel_with_etag_and_audit(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("general_manager",))
    headers = await factory.auth(hotel, "general_manager")
    r = await client.get("/hotel", headers=headers)
    assert r.status_code == 200
    assert r.headers["ETag"] == '"1"'
    assert r.json()["plan"] == {"code": "starter", "name": "Starter", "subscription_status": "active"}
    assert r.json()["logo_url"] is None

    no_match = await client.patch("/hotel", json={"name": "Renamed"}, headers=headers)
    assert no_match.status_code == 412
    ok = await client.patch("/hotel", json={"name": "Renamed"}, headers={**headers, "If-Match": '"1"'})
    assert ok.status_code == 200 and ok.json()["name"] == "Renamed" and ok.headers["ETag"] == '"2"'
    stale = await client.patch("/hotel", json={"name": "Again"}, headers={**headers, "If-Match": '"1"'})
    assert stale.status_code == 412 and stale.json()["error"]["code"] == "PRECONDITION_FAILED"
    null_name = await client.patch("/hotel", json={"name": None}, headers={**headers, "If-Match": '"2"'})
    assert null_name.status_code == 400

    async with owner_engine.connect() as conn:
        audit = (
            await conn.execute(
                text(
                    "SELECT actor_id, actor_label, old_value, new_value, request_id "
                    "FROM app.audit_logs WHERE hotel_id = :h AND action = 'hotel.update'"
                ),
                {"h": hotel.id},
            )
        ).one()
    assert audit.actor_id == hotel.users["general_manager"].user_id
    assert audit.actor_label == "General Manager (General Manager)"
    assert audit.old_value == {"name": hotel.name} and audit.new_value == {"name": "Renamed"}
    assert audit.request_id == ok.headers["X-Request-Id"]


async def test_settings_patch_needs_permission_step_up_and_audits_each_field(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("general_manager", "receptionist", "reception_manager"))
    gm = await factory.auth(hotel, "general_manager")
    r = await client.get("/hotel/settings", headers=gm)
    assert r.status_code == 200
    settings = r.json()
    assert settings["room_charge_auto_approve_limit"] == {"amount_minor": 50000, "currency": "ZAR"}
    assert settings["vat_rate_bp"] == 1500

    # A receptionist can neither read nor change settings; step-up does not help.
    rec = await factory.auth(hotel, "receptionist")
    assert (await client.get("/hotel/settings", headers=rec)).status_code == 403
    rec_stepped = await factory.step_up(hotel, "receptionist", rec)
    denied = await client.patch(
        "/hotel/settings", json={"wifi_name": "x"}, headers={**rec_stepped, "If-Match": '"1"'}
    )
    assert denied.status_code == 403 and denied.json()["error"]["code"] == "PERMISSION_DENIED"
    # A reception manager may read but not update.
    rm = await factory.auth(hotel, "reception_manager")
    assert (await client.get("/hotel/settings", headers=rm)).status_code == 200
    rm_stepped = await factory.step_up(hotel, "reception_manager", rm)
    assert (
        await client.patch(
            "/hotel/settings", json={"wifi_name": "x"}, headers={**rm_stepped, "If-Match": '"1"'}
        )
    ).status_code == 403

    stepped = await factory.step_up(hotel, "general_manager", gm)
    patch = {
        "wifi_name": "GrandGuest",
        "room_service_fee": {"amount_minor": 5000, "currency": "ZAR"},
        "checkout_time": "11:00",
    }
    ok = await client.patch("/hotel/settings", json=patch, headers={**stepped, "If-Match": '"1"'})
    assert ok.status_code == 200, ok.text
    assert ok.json()["room_service_fee"] == {"amount_minor": 5000, "currency": "ZAR"}
    assert ok.json()["checkout_time"] == "11:00"
    async with owner_engine.connect() as conn:
        audits = (
            await conn.execute(
                text(
                    "SELECT old_value, new_value FROM app.audit_logs "
                    "WHERE hotel_id = :h AND action = 'settings.update' ORDER BY id"
                ),
                {"h": hotel.id},
            )
        ).all()
    assert sorted(next(iter(a.new_value)) for a in audits) == [
        "checkout_time",
        "room_service_fee",
        "wifi_name",
    ]


@pytest.mark.parametrize(
    ("patch", "code"),
    [
        ({"vat_registered": True}, "VALIDATION_FAILED"),  # VAT number required
        ({"room_service_fee": {"amount_minor": 100, "currency": "USD"}}, "AMOUNT_INVALID"),
        ({"room_service_fee": {"amount_minor": -1, "currency": "ZAR"}}, "VALIDATION_FAILED"),
        ({"room_service_fee": {"amount_minor": 10.5, "currency": "ZAR"}}, "VALIDATION_FAILED"),
        ({"timezone": "Mars/Olympus"}, "VALIDATION_FAILED"),
        ({"currency": "USD"}, "VALIDATION_FAILED"),
        ({"vat_rate_bp": 20000}, "VALIDATION_FAILED"),
    ],
)
async def test_settings_validation(client, factory, patch, code):
    hotel = await factory.hotel(roles=("general_manager",))
    headers = await factory.step_up(hotel, "general_manager", await factory.auth(hotel, "general_manager"))
    r = await client.patch("/hotel/settings", json=patch, headers={**headers, "If-Match": '"1"'})
    assert r.status_code in (400, 422), r.text
    assert r.json()["error"]["code"] == code


async def test_suspended_hotel_can_read_but_not_write(client, factory):
    hotel = await factory.hotel(roles=("general_manager",), status="suspended")
    headers = await factory.auth(hotel, "general_manager")
    assert (await client.get("/hotel", headers=headers)).status_code == 200
    r = await client.patch("/hotel", json={"name": "x"}, headers={**headers, "If-Match": '"1"'})
    assert r.status_code == 403 and r.json()["error"]["code"] == "HOTEL_SUSPENDED"


async def test_permissions_and_roles_catalogue(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("general_manager", "kitchen_staff"))
    other = await factory.hotel(roles=())
    async with owner_engine.begin() as conn:
        for h, code in ((hotel.id, "night_auditor"), (other.id, "secret_role")):
            await conn.execute(
                text("INSERT INTO app.roles (hotel_id, code, name) VALUES (:h, :c, :c)"), {"h": h, "c": code}
            )
    headers = await factory.auth(hotel, "general_manager")
    perms = (await client.get("/permissions", headers=headers)).json()["data"]
    assert len(perms) == 52 and all(not p["code"].startswith("platform.") for p in perms)
    assert {p["code"] for p in perms if p["sensitive"]} >= {"settings.update", "folio.adjust.approve"}
    roles = (await client.get("/roles", headers=headers)).json()["data"]
    codes = [r["code"] for r in roles]
    assert len([r for r in roles if r["is_system"]]) == 10
    assert "night_auditor" in codes and "secret_role" not in codes
    assert not any(c.startswith("platform_") for c in codes)
    kitchen = await factory.auth(hotel, "kitchen_staff")
    assert (await client.get("/roles", headers=kitchen)).status_code == 403


# --- Cross-tenant ---------------------------------------------------------------------------


async def test_each_hotel_sees_only_itself(client, factory):
    a = await factory.hotel(roles=("general_manager",))
    b = await factory.hotel(roles=("general_manager",))
    for hotel in (a, b):
        headers = await factory.auth(hotel, "general_manager")
        assert (await client.get("/hotel", headers=headers)).json()["id"] == str(hotel.id)
        assert (await client.get("/hotel/settings", headers=headers)).status_code == 200


async def test_token_for_hotel_b_from_hotel_a_member_is_rejected(client, factory, app_state):
    """A member of hotel A cannot reach hotel B by forging hid: there is no membership."""
    a = await factory.hotel(roles=("general_manager",))
    b = await factory.hotel(roles=())
    good, _sid = await factory.token(a, a.users["general_manager"])
    claims = app_state.jwt.verify(good, "access")
    forged, _ = app_state.jwt.sign(
        "access", {**{k: claims[k] for k in ("sub", "kind", "sid", "amr", "perms_v")}, "hid": str(b.id)}, 900
    )
    r = await client.get("/hotel", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


async def test_platform_tokens_cannot_read_hotel_data(client, factory):
    admin = await factory.platform_user()
    token, _ = await factory.token(None, admin)
    r = await client.get("/hotel", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
