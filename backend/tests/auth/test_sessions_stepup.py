"""Refresh rotation and reuse, token validation, sessions, step-up, PIN, password reset,
email verification and invitation acceptance."""

from __future__ import annotations

import json
import secrets
import time
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from sqlalchemy import text

from app.core import crypto
from app.core.jwt import AUDIENCE, JwtKeys
from scripts.gen_dev_keys import ed25519_jwk
from tests.auth.test_login_mfa import login


async def tokens_for(client, user):
    r = await login(client, user)
    assert r.status_code == 200, r.text
    return r.json()


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- Refresh ----------------------------------------------------------------------------------


async def test_refresh_rotates_and_reuse_revokes_the_family(client, factory, mailbox):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    first = await tokens_for(client, user)
    second = (await client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})).json()
    assert second["refresh_token"] != first["refresh_token"]
    assert (await client.get("/hotel", headers=bearer(second["access_token"]))).status_code == 200

    reuse = await client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert reuse.status_code == 401
    # The whole family is gone: the newest refresh token and its access token no longer work.
    assert (
        await client.post("/auth/refresh", json={"refresh_token": second["refresh_token"]})
    ).status_code == 401
    assert (await client.get("/hotel", headers=bearer(second["access_token"]))).status_code == 401
    assert any(m.to == user.email and m.template == "session_reuse" for m in mailbox.sent)


async def test_refresh_picks_up_role_changes_and_old_access_tokens_fail(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    t = await tokens_for(client, user)
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.hotel_users SET perms_version = perms_version + 1 WHERE id = :id"),
            {"id": user.hotel_user_id},
        )
    stale = await client.get("/hotel", headers=bearer(t["access_token"]))
    assert stale.status_code == 401 and stale.json()["error"]["details"] == {"reason": "perms_changed"}
    fresh = (await client.post("/auth/refresh", json={"refresh_token": t["refresh_token"]})).json()
    assert (await client.get("/hotel", headers=bearer(fresh["access_token"]))).status_code == 200


async def test_web_clients_get_an_httponly_cookie_not_a_body_token(client, factory):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    r = await client.post(
        "/auth/login",
        json={"email": user.email, "password": user.password},
        headers={"Origin": "http://localhost:3001"},
    )
    assert r.json()["refresh_token"] is None
    cookie = r.headers["set-cookie"]
    assert cookie.startswith("__Host-diyneco_rt=")
    for flag in ("HttpOnly", "Secure", "SameSite=strict", "Path=/"):
        assert flag.lower() in cookie.lower()


async def test_expired_refresh_is_rejected(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("receptionist",))
    t = await tokens_for(client, hotel.users["receptionist"])
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.sessions SET expires_at = now() - interval '1 second' WHERE refresh_hash = :h"),
            {"h": crypto.sha256(t["refresh_token"])},
        )
    assert (await client.post("/auth/refresh", json={"refresh_token": t["refresh_token"]})).status_code == 401


# --- Access token validation -------------------------------------------------------------------


async def test_expired_forged_and_wrong_type_tokens_are_rejected(client, factory, app_state):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    good, _sid = await factory.token(hotel, user)
    claims = app_state.jwt.verify(good, "access")

    expired, _ = app_state.jwt.sign(
        "access", {k: claims[k] for k in ("sub", "kind", "sid", "hid", "perms_v", "amr")}, -1
    )
    other_keys = JwtKeys.from_config(
        json.dumps({"keys": [ed25519_jwk(app_state.jwt.active_kid)]}),
        app_state.jwt.active_kid,
        app_state.jwt.issuer,
    )
    forged, _ = other_keys.sign(
        "access", {k: claims[k] for k in ("sub", "kind", "sid", "hid", "perms_v", "amr")}, 900
    )
    unknown_kid = pyjwt.encode(
        {**claims, "exp": int(time.time()) + 900},
        app_state.jwt.keys[app_state.jwt.active_kid].key,
        algorithm="EdDSA",
        headers={"kid": "nope"},
    )
    hs256 = pyjwt.encode(
        {**claims, "exp": int(time.time()) + 900, "aud": AUDIENCE},
        "s" * 32,
        algorithm="HS256",
        headers={"kid": app_state.jwt.active_kid},
    )
    step_up_as_access, _ = app_state.jwt.sign(
        "step_up", {"sub": claims["sub"], "sid": claims["sid"], "hid": claims["hid"]}, 300
    )
    for token in (expired, forged, unknown_kid, hs256, step_up_as_access, "garbage"):
        r = await client.get("/hotel", headers=bearer(token))
        assert r.status_code == 401, token
        assert r.json()["error"]["code"] == "UNAUTHENTICATED"
    assert (await client.get("/hotel")).status_code == 401
    assert (await client.get("/hotel", headers=bearer(good))).status_code == 200


async def test_device_and_kitchen_tokens_cannot_call_staff_endpoints(client, factory):
    hotel = await factory.hotel(roles=("receptionist",))
    for kind in ("device", "kitchen_session", "api_key"):
        token, _ = await factory.token(hotel, hotel.users["receptionist"], kind=kind)
        assert (await client.get("/hotel", headers=bearer(token))).status_code == 401


async def test_deactivated_user_is_rejected_immediately(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("receptionist",))
    headers = await factory.auth(hotel, "receptionist")
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.hotel_users SET status = 'deactivated' WHERE id = :id"),
            {"id": hotel.users["receptionist"].hotel_user_id},
        )
    assert (await client.get("/hotel", headers=headers)).status_code == 401


# --- Sessions -------------------------------------------------------------------------------


async def test_logout_revokes_the_session(client, factory):
    hotel = await factory.hotel(roles=("receptionist",))
    t = await tokens_for(client, hotel.users["receptionist"])
    assert (await client.post("/auth/logout", headers=bearer(t["access_token"]))).status_code == 204
    assert (await client.get("/hotel", headers=bearer(t["access_token"]))).status_code == 401
    assert (await client.post("/auth/refresh", json={"refresh_token": t["refresh_token"]})).status_code == 401


async def test_list_and_revoke_own_sessions_only(client, factory, app_state):
    hotel = await factory.hotel(roles=("receptionist", "kitchen_staff"))
    me = hotel.users["receptionist"]
    a = await tokens_for(client, me)
    b = await tokens_for(client, me)
    listed = (await client.get("/auth/sessions", headers=bearer(a["access_token"]))).json()["data"]
    assert len(listed) == 2 and sum(s["current"] for s in listed) == 1
    b_sid = app_state.jwt.verify(b["access_token"], "access")["sid"]
    other_token, other_sid = await factory.token(hotel, hotel.users["kitchen_staff"])
    assert (
        await client.delete(f"/auth/sessions/{other_sid}", headers=bearer(a["access_token"]))
    ).status_code == 404
    assert (
        await client.delete(f"/auth/sessions/{b_sid}", headers=bearer(a["access_token"]))
    ).status_code == 204
    assert (await client.get("/hotel", headers=bearer(b["access_token"]))).status_code == 401
    assert (await client.get("/auth/sessions", headers=bearer(other_token))).status_code == 200


async def test_at_most_ten_active_sessions(client, factory, app_state, owner_engine):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    first = await tokens_for(client, user)
    for _ in range(9):
        await tokens_for(client, user)
    await app_state.limiter.reset()
    await tokens_for(client, user)  # the 11th sign-in retires the oldest
    async with owner_engine.connect() as conn:
        active = (
            await conn.execute(
                text("SELECT count(*) FROM app.sessions WHERE user_id = :u AND revoked_at IS NULL"),
                {"u": user.user_id},
            )
        ).scalar_one()
    assert active == 10
    assert (await client.get("/hotel", headers=bearer(first["access_token"]))).status_code == 401


async def test_x_hotel_id_must_match_the_token(client, factory):
    hotel = await factory.hotel(roles=("receptionist",))
    other = await factory.hotel(roles=())
    headers = await factory.auth(hotel, "receptionist")
    assert (await client.get("/hotel", headers={**headers, "X-Hotel-Id": str(hotel.id)})).status_code == 200
    r = await client.get("/hotel", headers={**headers, "X-Hotel-Id": str(other.id)})
    assert r.status_code == 404


# --- Step-up and PIN ----------------------------------------------------------------------


async def test_step_up_with_pin_and_password(client, factory, app_state):
    hotel = await factory.hotel(roles=("general_manager",))
    headers = await factory.auth(hotel, "general_manager")
    r = await client.post("/auth/step-up", json={"pin": "1234"}, headers=headers)
    assert r.status_code == 200, r.text
    claims = app_state.jwt.verify(r.json()["step_up_token"], "step_up")
    assert claims["exp"] - claims["iat"] == 300
    r = await client.post(
        "/auth/step-up", json={"password": hotel.users["general_manager"].password}, headers=headers
    )
    assert r.status_code == 200


async def test_wrong_pin_counts_down_then_locks(client, factory, app_state):
    hotel = await factory.hotel(roles=("receptionist",))
    headers = await factory.auth(hotel, "receptionist")
    lefts = []
    for _ in range(5):
        r = await client.post("/auth/step-up", json={"pin": "9999"}, headers=headers)
        assert r.status_code == 403 and r.json()["error"]["code"] == "PIN_INVALID"
        lefts.append(r.json()["error"]["details"]["attempts_left"])
    assert lefts == [4, 3, 2, 1, 0]
    await app_state.limiter.reset()
    locked = await client.post("/auth/step-up", json={"pin": "1234"}, headers=headers)
    assert locked.status_code == 403 and "locked_until" in locked.json()["error"]["details"]


async def test_step_up_token_is_bound_and_expires(client, factory, app_state):
    hotel = await factory.hotel(roles=("general_manager",))
    gm = hotel.users["general_manager"]
    headers = await factory.auth(hotel, "general_manager")
    settings_etag = (await client.get("/hotel/settings", headers=headers)).headers["ETag"]
    patch = {"wifi_name": "GuestNet"}

    missing = await client.patch(
        "/hotel/settings", json=patch, headers={**headers, "If-Match": settings_etag}
    )
    assert missing.status_code == 403 and missing.json()["error"]["code"] == "STEP_UP_REQUIRED"

    claims = app_state.jwt.verify(headers["Authorization"].split()[1], "access")
    expired, _ = app_state.jwt.sign(
        "step_up", {"sub": claims["sub"], "sid": claims["sid"], "hid": claims["hid"]}, -1
    )
    r = await client.patch(
        "/hotel/settings", json=patch, headers={**headers, "If-Match": settings_etag, "X-Step-Up": expired}
    )
    assert r.status_code == 403 and r.json()["error"]["code"] == "STEP_UP_REQUIRED"

    other_session_headers = await factory.auth(hotel, "general_manager")  # same user, new session
    other = await factory.step_up(hotel, "general_manager", other_session_headers)
    r = await client.patch(
        "/hotel/settings",
        json=patch,
        headers={**headers, "If-Match": settings_etag, "X-Step-Up": other["X-Step-Up"]},
    )
    assert r.status_code == 403, "a step-up token from another session must not work"

    ok = await client.patch(
        "/hotel/settings",
        json=patch,
        headers={**await factory.step_up(hotel, "general_manager", headers), "If-Match": settings_etag},
    )
    assert ok.status_code == 200, ok.text
    assert gm.user_id


async def test_set_pin_needs_step_up(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("receptionist",))
    headers = await factory.auth(hotel, "receptionist")
    assert (await client.put("/auth/pin", json={"pin": "482913"}, headers=headers)).status_code == 403
    stepped = await factory.step_up(hotel, "receptionist", headers)
    assert (await client.put("/auth/pin", json={"pin": "48291"}, headers=stepped)).status_code == 204
    assert (await client.put("/auth/pin", json={"pin": "12ab"}, headers=stepped)).status_code == 400
    assert (await client.post("/auth/step-up", json={"pin": "48291"}, headers=headers)).status_code == 200


# --- Password reset, email verification, invitations ----------------------------------------


def _token_from(mailbox, email: str, template: str) -> str:
    message = [m for m in mailbox.sent if m.to == email and m.template == template][-1]
    return next(w for w in message.body.split() if len(w) > 30 and " " not in w)


async def test_forgot_password_never_reveals_accounts_and_reset_revokes_sessions(client, factory, mailbox):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    t = await tokens_for(client, user)
    for email in (user.email, "nobody@example.test"):
        r = await client.post("/auth/password/forgot", json={"email": email})
        assert r.status_code == 202 and r.json() == {"status": "accepted"}
    token = _token_from(mailbox, user.email, "password_reset")

    weak = await client.post("/auth/password/reset", json={"token": token, "new_password": "short"})
    assert weak.status_code == 400  # rejected before the token is spent
    new_password = f"New-Password-{secrets.token_hex(4)}"
    ok = await client.post("/auth/password/reset", json={"token": token, "new_password": new_password})
    assert ok.status_code == 204, ok.text
    assert (await client.get("/hotel", headers=bearer(t["access_token"]))).status_code == 401
    again = await client.post(
        "/auth/password/reset", json={"token": token, "new_password": new_password + "x"}
    )
    assert again.status_code == 400
    user.password = new_password
    assert (await login(client, user)).status_code == 200


async def test_common_passwords_are_rejected(client, factory, mailbox):
    hotel = await factory.hotel(roles=("receptionist",))
    user = hotel.users["receptionist"]
    await client.post("/auth/password/forgot", json={"email": user.email})
    token = _token_from(mailbox, user.email, "password_reset")
    r = await client.post("/auth/password/reset", json={"token": token, "new_password": "password1234"})
    assert r.status_code == 400
    assert r.json()["error"]["details"]["fields"][0]["type"] == "password_policy"


async def test_invitation_acceptance(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("hotel_admin",))
    token = crypto.random_token()
    email = f"new.staff.{secrets.token_hex(3)}@example.test"
    async with owner_engine.begin() as conn:
        role = (
            await conn.execute(
                text("SELECT id FROM app.roles WHERE hotel_id IS NULL AND code = 'receptionist'")
            )
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO app.invitations (hotel_id, email, name, role_ids, token_hash, invited_by, expires_at) "
                "VALUES (:h, :e, 'New Staff', ARRAY[:r]::uuid[], :t, :by, :exp)"
            ),
            {
                "h": hotel.id,
                "e": email,
                "r": role,
                "t": crypto.sha256(token),
                "by": hotel.users["hotel_admin"].user_id,
                "exp": datetime.now(UTC) + timedelta(days=7),
            },
        )
    password = f"Staff-Password-{secrets.token_hex(4)}"
    key = str(uuid.uuid4())
    body = {"name": "New Staff", "password": password, "pin": "2468"}
    r = await client.post(f"/auth/invitations/{token}/accept", json=body, headers={"Idempotency-Key": key})
    assert r.status_code == 201, r.text
    assert r.json()["hotel_id"] == str(hotel.id)
    replay = await client.post(
        f"/auth/invitations/{token}/accept", json=body, headers={"Idempotency-Key": key}
    )
    assert replay.status_code == 201 and replay.headers["Idempotent-Replayed"] == "true"
    reused = await client.post(
        f"/auth/invitations/{token}/accept", json=body, headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert reused.status_code == 404
    signed_in = (await client.post("/auth/login", json={"email": email, "password": password})).json()
    assert signed_in["hotels"][0]["roles"] == ["receptionist"]


async def test_email_verification(client, factory, mailbox, owner_engine):
    r = await client.post(
        "/signup",
        json={
            "owner": {
                "name": "Thandi Owner",
                "email": f"thandi.{secrets.token_hex(3)}@example.com",
                "password": f"Owner-Password-{secrets.token_hex(4)}",
            },
            "hotel": {"name": "Verify Lodge"},
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert r.status_code == 201, r.text
    email = mailbox.sent[-1].to
    token = _token_from(mailbox, email, "email_verify")
    assert (await client.post("/auth/email/verify", json={"token": token})).status_code == 204
    assert (await client.post("/auth/email/verify", json={"token": token})).status_code == 400
    async with owner_engine.connect() as conn:
        verified = (
            await conn.execute(text("SELECT email_verified_at FROM app.users WHERE email = :e"), {"e": email})
        ).scalar_one()
    assert verified is not None
