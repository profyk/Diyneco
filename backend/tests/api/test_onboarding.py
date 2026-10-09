"""Logo upload through signed URLs, and the onboarding checklist from sign-up to rooms + staff."""

from __future__ import annotations

import secrets
import uuid

import pyotp
from sqlalchemy import text

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


def _path(url: str) -> str:
    return url.split("/api/v1", 1)[1]


async def test_logo_upload_round_trip(client, factory):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    start = await client.post(
        "/hotel/logo", json={"content_type": "image/png", "size_bytes": len(PNG)}, headers=gm
    )
    assert start.status_code == 200, start.text
    upload = start.json()
    assert upload["method"] == "PUT" and upload["max_bytes"] == 2 * 1024 * 1024
    put = await client.put(_path(upload["upload_url"]), content=PNG, headers=upload["headers"])
    assert put.status_code == 204, put.text
    logo_url = (await client.get("/hotel", headers=gm)).json()["logo_url"]
    assert logo_url
    got = await client.get(_path(logo_url))
    assert got.status_code == 200
    assert got.content == PNG
    assert got.headers["content-type"] == "image/png"


async def test_logo_rules(client, factory):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    gif = await client.post("/hotel/logo", json={"content_type": "image/gif", "size_bytes": 10}, headers=gm)
    assert gif.status_code == 400
    big = await client.post(
        "/hotel/logo", json={"content_type": "image/png", "size_bytes": 3_000_000}, headers=gm
    )
    assert big.status_code == 400
    upload = (
        await client.post("/hotel/logo", json={"content_type": "image/png", "size_bytes": 10}, headers=gm)
    ).json()
    wrong_type = await client.put(
        _path(upload["upload_url"]), content=PNG, headers={"Content-Type": "text/html"}
    )
    assert wrong_type.status_code == 400
    rec = await factory.auth(hotel, "receptionist")
    denied = await client.post(
        "/hotel/logo", json={"content_type": "image/png", "size_bytes": 10}, headers=rec
    )
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"


async def test_storage_tokens_cannot_be_forged_or_swapped(client, factory):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    upload = (
        await client.post("/hotel/logo", json={"content_type": "image/png", "size_bytes": 10}, headers=gm)
    ).json()
    token = upload["upload_url"].rsplit("/", 1)[1]
    assert (await client.get(f"/dev-storage/{token}")).status_code == 404  # a put token cannot read
    assert (await client.get("/dev-storage/not-a-token")).status_code == 404


async def test_signup_to_rooms_and_staff_without_manual_db_work(client, owner_engine, mailbox):
    """Phase 2 exit criterion: a hotel goes from sign-up to rooms + staff through the API."""
    email = f"owner.{secrets.token_hex(3)}@example.com"
    password = f"Owner-Password-{secrets.token_hex(4)}"
    signup = await client.post(
        "/signup",
        json={
            "owner": {"name": "Lindiwe Owner", "email": email, "password": password},
            "hotel": {
                "name": "Karoo Lodge",
                "phone": "+27 23 555 0100",
                "address": {"city": "Prince Albert"},
            },
        },
        headers=idem(),
    )
    assert signup.status_code == 201, signup.text
    verify = next(m for m in reversed(mailbox.sent) if m.to == email and m.template == "email_verify")
    code = verify.body.strip().rsplit("\n", 1)[-1].strip()
    assert (await client.post("/auth/email/verify", json={"token": code})).status_code == 204

    # The owner must enrol MFA (D12) before doing anything else.
    login = (await client.post("/auth/login", json={"email": email, "password": password})).json()
    pending = {"Authorization": f"Bearer {login['access_token']}"}
    enrol = (await client.post("/auth/mfa/enroll", headers=pending)).json()
    confirmed = await client.post(
        "/auth/mfa/verify", json={"code": pyotp.TOTP(enrol["secret"]).now()}, headers=pending
    )
    assert confirmed.status_code == 200, confirmed.text
    owner = {"Authorization": f"Bearer {confirmed.json()['access_token']}"}

    steps = (await client.get("/hotel/onboarding", headers=owner)).json()
    done = {s["key"]: s["done"] for s in steps["steps"]}
    assert done["account"] and done["hotel_profile"]
    assert not done["rooms"] and steps["next_step"] == "settings"

    step_up = await client.post("/auth/step-up", json={"password": password}, headers=owner)
    owner_s = {**owner, "X-Step-Up": step_up.json()["step_up_token"]}
    settings = await client.get("/hotel/settings", headers=owner)
    patched = await client.patch(
        "/hotel/settings",
        json={"room_charging_enabled": True, "vat_registered": False},
        headers={**owner_s, "If-Match": settings.headers["ETag"]},
    )
    assert patched.status_code == 200, patched.text

    rt = await client.post(
        "/room-types",
        json={"name": "Garden Room", "base_rate": {"amount_minor": 120000, "currency": "ZAR"}},
        headers={**owner, **idem()},
    )
    assert rt.status_code == 201, rt.text
    rooms = await client.post(
        "/rooms/bulk",
        json={"ranges": [{"from": 1, "to": 12, "floor": 0, "room_type_id": rt.json()["id"]}]},
        headers={**owner, **idem()},
    )
    assert rooms.status_code == 201, rooms.text

    roles = (await client.get("/roles", headers=owner)).json()["data"]
    reception = next(r["id"] for r in roles if r["code"] == "receptionist")
    invite = await client.post(
        "/staff/invitations",
        json={
            "name": "Sipho Desk",
            "email": f"sipho.{secrets.token_hex(3)}@example.com",
            "role_ids": [reception],
        },
        headers={**owner_s, **idem()},
    )
    assert invite.status_code == 201, invite.text

    steps = (await client.get("/hotel/onboarding", headers=owner)).json()
    done = {s["key"]: s["done"] for s in steps["steps"]}
    for key in (
        "account",
        "hotel_profile",
        "settings",
        "room_types",
        "rooms",
        "staff_invites",
        "room_charging",
    ):
        assert done[key], key
    for key in ("menu", "devices", "tablet_pairing"):
        assert not done[key], key
    assert steps["total"] == 11 and steps["completed"] == 7
    async with owner_engine.connect() as conn:
        status = (
            await conn.execute(
                text(
                    "SELECT h.status FROM app.hotels h JOIN app.hotel_users hu ON hu.hotel_id = h.id "
                    "JOIN app.users u ON u.id = hu.user_id WHERE u.email = :e"
                ),
                {"e": email},
            )
        ).scalar_one()
    assert status == "pending_approval"  # Diyneco approves in Phase 7; setup works meanwhile
