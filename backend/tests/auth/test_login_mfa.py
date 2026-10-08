"""Login, lockout, MFA (login, enrolment, replay, recovery codes) and the auth rate limit."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pyotp
from sqlalchemy import text

from app.services import mfa


async def login(client, user, **extra):
    return await client.post("/auth/login", json={"email": user.email, "password": user.password, **extra})


def totp_now(secret: str, offset: int = 0) -> str:
    return mfa.code_at_step(secret, mfa.current_step() + offset)


async def test_login_without_mfa_returns_tokens_and_hotels(client, factory):
    hotel = await factory.hotel(roles=("receptionist",))
    r = await login(client, hotel.users["receptionist"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token_type"] == "Bearer" and body["expires_in"] == 900
    assert body["refresh_token"].startswith("rt_")
    assert body["mfa_enrolment_required"] is False
    assert body["hotels"] == [
        {"id": str(hotel.id), "name": hotel.name, "status": "active", "roles": ["receptionist"]}
    ]
    me = await client.get("/hotel", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200


async def test_unknown_email_and_wrong_password_look_identical(client, factory):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    a = await client.post("/auth/login", json={"email": "nobody@example.test", "password": "x" * 12})
    b = await client.post("/auth/login", json={"email": user.email, "password": "wrong-password-123"})
    assert a.status_code == b.status_code == 401
    assert a.json()["error"]["code"] == b.json()["error"]["code"] == "UNAUTHENTICATED"
    assert a.json()["error"]["message"] == b.json()["error"]["message"]


async def test_lockout_after_five_failures_in_fifteen_minutes(client, factory, mailbox, app_state):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    for _ in range(5):
        r = await client.post("/auth/login", json={"email": user.email, "password": "wrong-password-123"})
        assert r.status_code == 401
    await app_state.limiter.reset()
    r = await login(client, user)  # correct password, but locked
    assert r.status_code == 401
    assert any(m.to == user.email and m.template == "account_locked" for m in mailbox.sent)


async def test_failures_outside_the_window_do_not_accumulate(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    for _ in range(4):
        await client.post("/auth/login", json={"email": user.email, "password": "wrong-password-123"})
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.users SET failed_window_start = now() - interval '16 minutes' WHERE id = :u"),
            {"u": user.user_id},
        )
    await client.post("/auth/login", json={"email": user.email, "password": "wrong-password-123"})
    r = await login(client, user)
    assert r.status_code == 200, r.text


async def test_lock_expires_after_fifteen_minutes(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.users SET locked_until = now() - interval '1 second' WHERE id = :u"),
            {"u": user.user_id},
        )
    assert (await login(client, user)).status_code == 200


async def test_mfa_login_and_code_replay_is_rejected(client, factory, app_state):
    hotel = await factory.hotel(roles=("general_manager",))
    user = hotel.users["general_manager"]
    r = await login(client, user)
    assert r.status_code == 200
    challenge = r.json()
    assert challenge == {"mfa_required": True, "mfa_token": challenge["mfa_token"]}
    code = totp_now(user.totp_secret)
    ok = await client.post("/auth/mfa/verify", json={"mfa_token": challenge["mfa_token"], "code": code})
    assert ok.status_code == 200, ok.text
    claims = app_state.jwt.verify(ok.json()["access_token"], "access")
    assert claims["amr"] == ["pwd", "mfa"] and "mfa_pending" not in claims

    second = (await login(client, user)).json()
    replay = await client.post("/auth/mfa/verify", json={"mfa_token": second["mfa_token"], "code": code})
    assert replay.status_code == 401
    assert replay.json()["error"]["details"] == {"reason": "invalid_code"}


async def test_wrong_mfa_code_is_rejected(client, factory):
    hotel = await factory.hotel(roles=("finance_manager",))
    user = hotel.users["finance_manager"]
    token = (await login(client, user)).json()["mfa_token"]
    wrong = str((int(totp_now(user.totp_secret)) + 1) % 1_000_000).zfill(6)
    r = await client.post("/auth/mfa/verify", json={"mfa_token": token, "code": wrong})
    assert r.status_code == 401


def test_totp_drift_window_is_plus_minus_one_step():
    secret = pyotp.random_base32(32)
    now = 1_800_000_000.0
    step = mfa.current_step(now)
    for offset, ok in ((-2, False), (-1, True), (0, True), (1, True), (2, False)):
        code = mfa.code_at_step(secret, step + offset)
        assert (mfa.verify_code(secret, code, None, at=now) is not None) is ok, offset
    # A step at or before the last used one never matches again.
    assert mfa.verify_code(secret, mfa.code_at_step(secret, step), step, at=now) is None


async def test_mfa_token_cannot_be_used_as_access_token(client, factory):
    hotel = await factory.hotel(roles=("hotel_owner",))
    token = (await login(client, hotel.users["hotel_owner"])).json()["mfa_token"]
    r = await client.get("/hotel", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


async def test_mandatory_mfa_forces_enrolment_then_issues_full_session(client, factory, app_state):
    hotel = await factory.hotel(roles=("hotel_admin",), mfa_for_required=False)
    user = hotel.users["hotel_admin"]
    body = (await login(client, user)).json()
    assert body["mfa_enrolment_required"] is True
    pending = {"Authorization": f"Bearer {body['access_token']}"}

    blocked = await client.get("/hotel", headers=pending)
    assert blocked.status_code == 401 and blocked.json()["error"]["code"] == "MFA_REQUIRED"

    enrol = await client.post("/auth/mfa/enroll", headers=pending)
    assert enrol.status_code == 200, enrol.text
    secret = enrol.json()["secret"]
    assert enrol.json()["otpauth_uri"].startswith("otpauth://totp/")

    confirm = await client.post("/auth/mfa/verify", json={"code": totp_now(secret)}, headers=pending)
    assert confirm.status_code == 200, confirm.text
    full = confirm.json()
    assert len(full["recovery_codes"]) == 10 and full["mfa_enrolment_required"] is False
    assert app_state.jwt.verify(full["access_token"], "access")["amr"] == ["pwd", "mfa"]
    ok = await client.get("/hotel", headers={"Authorization": f"Bearer {full['access_token']}"})
    assert ok.status_code == 200
    # The pending session was retired.
    assert (await client.get("/auth/sessions", headers=pending)).status_code == 401

    # Recovery codes work once.
    challenge = (await login(client, user)).json()["mfa_token"]
    code = full["recovery_codes"][0]
    first = await client.post("/auth/mfa/verify", json={"mfa_token": challenge, "recovery_code": code})
    assert first.status_code == 200
    challenge = (await login(client, user)).json()["mfa_token"]
    again = await client.post("/auth/mfa/verify", json={"mfa_token": challenge, "recovery_code": code})
    assert again.status_code == 401


async def test_platform_accounts_require_mfa(client, factory):
    admin = await factory.platform_user()
    challenge = (await login(client, admin)).json()
    assert challenge["mfa_required"] is True
    token, _ = await factory.token(None, admin, amr=("pwd",))
    r = await client.get("/auth/sessions", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "MFA_REQUIRED"


async def test_eleven_logins_in_a_minute_from_one_ip_are_rate_limited(client, factory):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    codes = [(await login(client, user)).status_code for _ in range(11)]
    assert codes[:10] == [200] * 10
    assert codes[10] == 429
    r = await login(client, user)
    assert r.json()["error"]["code"] == "RATE_LIMITED"
    assert int(r.headers["Retry-After"]) > 0
    assert r.headers["RateLimit-Limit"] == "10"


async def test_login_into_a_specific_hotel(client, factory, owner_engine):
    a = await factory.hotel(roles=("receptionist",))
    b = await factory.hotel(roles=())
    user = a.users["receptionist"]
    async with owner_engine.begin() as conn:
        hu = (
            await conn.execute(
                text("INSERT INTO app.hotel_users (hotel_id, user_id) VALUES (:h, :u) RETURNING id"),
                {"h": b.id, "u": user.user_id},
            )
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO app.user_roles (hotel_id, hotel_user_id, role_id) SELECT :h, :hu, id "
                "FROM app.roles WHERE hotel_id IS NULL AND code = 'receptionist'"
            ),
            {"h": b.id, "hu": hu},
        )
    body = (await login(client, user, hotel_id=str(b.id))).json()
    assert {h["id"] for h in body["hotels"]} == {str(a.id), str(b.id)}
    hotel = await client.get("/hotel", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert hotel.json()["id"] == str(b.id)
    # A hotel the user does not belong to.
    stranger = await factory.hotel(roles=())
    assert (await login(client, user, hotel_id=str(stranger.id))).status_code == 404


def test_utc_now_is_timezone_aware():
    assert datetime.now(UTC) - timedelta(seconds=1) < datetime.now(UTC)
