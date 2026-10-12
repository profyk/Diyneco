"""Diyneco staff accounts (DECISIONS D71): invited from the admin panel, set their password
from the link, change roles, are deactivated and reactivated, and the platform never loses
its last active Super Admin."""

from __future__ import annotations

import re
import secrets

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.api.test_admin import platform, step_up
from tests.api.test_room_service import idem
from tests.api.test_staff import _gm, _role_id

PASSWORD = "Correct-Horse-Battery-9"


def _token(mailbox, email: str) -> str:
    mail = next(m for m in reversed(mailbox.sent) if m.to == email and m.template == "platform_invitation")
    return mail.body.split("\n\n")[-2].strip()


async def _invite(client, factory, admin, roles=("platform_support",)) -> tuple[dict, str]:
    email = f"staff.{secrets.token_hex(4)}@diyneco.example"
    out = await client.post(
        "/admin/staff",
        json={"name": "New Staff", "email": email, "roles": list(roles)},
        headers={**step_up(factory, admin), **idem()},
    )
    assert out.status_code == 201, out.text
    return out.json(), email


async def test_invited_staff_choose_a_password_then_sign_in_with_two_step(client, factory, mailbox):
    admin = await platform(factory)
    support = await platform(factory, "platform_support")
    body = {"name": "X", "email": "x@diyneco.example", "roles": ["platform_support"]}
    refused = await client.post("/admin/staff", json=body, headers={**step_up(factory, support), **idem()})
    assert refused.json()["error"]["code"] == "PERMISSION_DENIED"
    no_step_up = await client.post("/admin/staff", json=body, headers={**admin, **idem()})
    assert no_step_up.json()["error"]["code"] == "STEP_UP_REQUIRED"

    staff, email = await _invite(client, factory, admin)
    assert staff["status"] == "invited" and staff["roles"] == ["platform_support"]
    assert not staff["mfa_enrolled"]
    listed = (await client.get("/admin/staff", headers=admin)).json()["data"]
    assert any(s["id"] == staff["id"] for s in listed)
    roles = (await client.get("/admin/staff/roles", headers=admin)).json()["data"]
    assert {"platform_super_admin", "platform_support"} <= {r["code"] for r in roles}

    # No password yet, so no sign-in.
    login = await client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert login.json()["error"]["code"] == "UNAUTHENTICATED"

    # A resend replaces the first link.
    first = _token(mailbox, email)
    resent = await client.post(f"/admin/staff/{staff['id']}/resend-invitation", headers={**admin, **idem()})
    assert resent.status_code == 200, resent.text
    second = _token(mailbox, email)
    assert first != second
    stale = await client.post(
        "/auth/platform-invitations/accept", json={"token": first, "password": PASSWORD}
    )
    assert stale.json()["error"]["code"] == "VALIDATION_FAILED"
    weak = await client.post("/auth/platform-invitations/accept", json={"token": second, "password": "short"})
    assert weak.json()["error"]["code"] == "VALIDATION_FAILED"
    ok = await client.post("/auth/platform-invitations/accept", json={"token": second, "password": PASSWORD})
    assert ok.status_code == 204, ok.text
    again = await client.post(
        "/auth/platform-invitations/accept", json={"token": second, "password": PASSWORD}
    )
    assert again.json()["error"]["code"] == "VALIDATION_FAILED"

    # Signed in, but two-step sign-in must be set up before anything else.
    signed_in = await client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert signed_in.status_code == 200, signed_in.text
    headers = {"Authorization": f"Bearer {signed_in.json()['access_token']}"}
    assert (await client.get("/admin/metrics", headers=headers)).json()["error"]["code"] == "MFA_REQUIRED"
    assert (await client.get("/admin/staff", headers=admin)).json()["data"]
    row = next(
        s for s in (await client.get("/admin/staff", headers=admin)).json()["data"] if s["id"] == staff["id"]
    )
    assert row["status"] == "active"


async def test_email_in_use_and_unknown_roles_are_refused(client, factory):
    admin = await platform(factory)
    hotel = await factory.hotel()
    _, email = await _invite(client, factory, admin)
    taken = await client.post(
        "/admin/staff",
        json={"name": "Again", "email": email.upper(), "roles": ["platform_support"]},
        headers={**step_up(factory, admin), **idem()},
    )
    assert taken.json()["error"]["code"] == "INVALID_TRANSITION"
    unknown = await client.post(
        "/admin/staff",
        json={"name": "X", "email": f"x.{secrets.token_hex(4)}@diyneco.example", "roles": ["platform_ghost"]},
        headers={**step_up(factory, admin), **idem()},
    )
    assert unknown.json()["error"]["code"] == "VALIDATION_FAILED"
    hotel_role = await client.post(
        "/admin/staff",
        json={"name": "X", "email": f"x.{secrets.token_hex(4)}@diyneco.example", "roles": ["hotel_owner"]},
        headers={**step_up(factory, admin), **idem()},
    )
    assert hotel_role.status_code == 422 or hotel_role.json()["error"]["code"] == "VALIDATION_FAILED"
    # Hotel staff cannot reach the endpoints at all.
    owner = await factory.auth(hotel, "hotel_owner")
    assert (await client.get("/admin/staff", headers=owner)).status_code in (401, 403)


async def test_roles_change_at_once_and_deactivation_signs_out(client, factory):
    admin = await platform(factory)
    member_user = await factory.platform_user("platform_support")
    token, _ = await factory.token(None, member_user)
    member = {"Authorization": f"Bearer {token}"}
    assert (await client.get("/admin/staff", headers=member)).json()["error"]["code"] == "PERMISSION_DENIED"

    url = f"/admin/staff/{member_user.user_id}"
    promoted = await client.put(
        f"{url}/roles", json={"roles": ["platform_super_admin"]}, headers=step_up(factory, admin)
    )
    assert promoted.status_code == 200, promoted.text
    assert promoted.json()["roles"] == ["platform_super_admin"]
    assert (await client.get("/admin/staff", headers=member)).status_code == 200

    # Nobody changes or deactivates their own account.
    own = await client.put(
        f"/admin/staff/{member_user.user_id}/roles",
        json={"roles": ["platform_support"]},
        headers=step_up(factory, member),
    )
    assert own.json()["error"]["code"] == "PERMISSION_DENIED"

    off = await client.post(f"{url}/deactivate", headers={**step_up(factory, admin), **idem()})
    assert off.status_code == 200 and off.json()["status"] == "deactivated"
    assert (await client.get("/admin/staff", headers=member)).json()["error"]["code"] == "UNAUTHENTICATED"
    twice = await client.post(f"{url}/deactivate", headers={**step_up(factory, admin), **idem()})
    assert twice.json()["error"]["code"] == "INVALID_TRANSITION"
    back = await client.post(f"{url}/reactivate", headers={**step_up(factory, admin), **idem()})
    assert back.json()["status"] == "active"


async def test_the_last_super_admin_cannot_be_removed(client, factory, owner_engine):
    a_user = await factory.platform_user()
    b_user = await factory.platform_user()
    a_token, _ = await factory.token(None, a_user)
    a = {"Authorization": f"Bearer {a_token}"}
    # Make A and B the only active Super Admins for the length of the test.
    async with owner_engine.begin() as conn:
        others = list(
            (
                await conn.execute(
                    text(
                        "SELECT DISTINCT u.id FROM app.users u "
                        "JOIN app.platform_user_roles p ON p.user_id = u.id "
                        "JOIN app.roles r ON r.id = p.role_id WHERE r.code = 'platform_super_admin' "
                        "AND u.status = 'active' AND u.id <> ALL(:keep)"
                    ),
                    {"keep": [a_user.user_id, b_user.user_id]},
                )
            )
            .scalars()
            .all()
        )
        await conn.execute(
            text("UPDATE app.users SET status = 'locked' WHERE id = ANY(:ids)"), {"ids": others}
        )
    try:
        out = await client.post(
            f"/admin/staff/{b_user.user_id}/deactivate", headers={**step_up(factory, a), **idem()}
        )
        assert out.status_code == 200, out.text  # A is still there
        # A is now the last one: the database refuses a commit that removes it, whatever the path.
        with pytest.raises(DBAPIError, match="at least one active Super Admin"):
            async with owner_engine.begin() as conn:
                await conn.execute(
                    text("UPDATE app.users SET status = 'deactivated' WHERE id = :u"), {"u": a_user.user_id}
                )
        with pytest.raises(DBAPIError, match="at least one active Super Admin"):
            async with owner_engine.begin() as conn:
                await conn.execute(
                    text("DELETE FROM app.platform_user_roles WHERE user_id = :u"), {"u": a_user.user_id}
                )
        # Reactivating B makes room again.
        back = await client.post(
            f"/admin/staff/{b_user.user_id}/reactivate", headers={**step_up(factory, a), **idem()}
        )
        assert back.json()["status"] == "active"
    finally:
        async with owner_engine.begin() as conn:
            await conn.execute(
                text("UPDATE app.users SET status = 'active' WHERE id = ANY(:ids)"), {"ids": others}
            )


async def test_a_platform_account_cannot_join_a_hotel(client, factory, owner_engine, mailbox):
    staff = await factory.platform_user("platform_support")
    hotel = await factory.hotel(roles=("general_manager",))
    email = f"platform.{secrets.token_hex(4)}@diyneco.example"
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.users SET email = :e WHERE id = :u"), {"e": email, "u": staff.user_id}
        )
    gm = await _gm(factory, hotel)
    body = {
        "name": "Platform",
        "email": email,
        "role_ids": [await _role_id(owner_engine, "receptionist")],
    }
    inv = await client.post("/staff/invitations", json=body, headers={**gm, **idem()})
    assert inv.status_code == 201, inv.text
    mail = next(m for m in reversed(mailbox.sent) if m.to == email and m.template == "staff_invitation")
    token = re.search(r"(inv_\S+)", mail.body).group(1)
    out = await client.post(
        f"/auth/invitations/{token}/accept",
        json={"name": "Platform", "password": staff.password, "pin": "2468"},
        headers=idem(),
    )
    assert out.json()["error"]["code"] == "INVALID_TRANSITION"
