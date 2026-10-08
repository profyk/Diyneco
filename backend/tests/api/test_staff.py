"""Staff, invitations and custom roles: the cannot-grant rule, step-up, perms_v, tenancy."""

from __future__ import annotations

import re
import secrets
import uuid

from sqlalchemy import text


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


async def _role_id(owner_engine, code: str) -> str:
    async with owner_engine.connect() as conn:
        return str(
            (
                await conn.execute(
                    text("SELECT id FROM app.roles WHERE hotel_id IS NULL AND code = :c"), {"c": code}
                )
            ).scalar_one()
        )


async def _gm(factory, hotel) -> dict[str, str]:
    h = await factory.auth(hotel, "general_manager")
    return await factory.step_up(hotel, "general_manager", h)


async def test_list_staff(client, factory):
    hotel = await factory.hotel(roles=("general_manager", "receptionist"))
    r = await client.get("/staff", headers=await factory.auth(hotel, "general_manager"))
    assert r.status_code == 200, r.text
    members = {m["roles"][0]["code"]: m for m in r.json()["data"]}
    assert set(members) == {"general_manager", "receptionist"}
    assert members["receptionist"]["has_pin"] is True
    assert members["general_manager"]["mfa_enabled"] is True
    denied = await client.get("/staff", headers=await factory.auth(hotel, "receptionist"))
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"


async def test_invite_accept_and_sign_in_end_to_end(client, factory, owner_engine, mailbox):
    hotel = await factory.hotel(roles=("general_manager",))
    gm = await _gm(factory, hotel)
    email = f"thandi.{secrets.token_hex(3)}@example.com"
    body = {
        "name": "Thandi M",
        "email": email,
        "department": "Front desk",
        "role_ids": [await _role_id(owner_engine, "receptionist")],
    }
    r = await client.post("/staff/invitations", json=body, headers={**gm, **idem()})
    assert r.status_code == 201, r.text
    assert r.json()["roles"][0]["code"] == "receptionist"
    pending = (await client.get("/staff/invitations", headers=gm)).json()["data"]
    assert [p["email"] for p in pending] == [email]

    mail = next(m for m in reversed(mailbox.sent) if m.to == email and m.template == "staff_invitation")
    token = re.search(r"(inv_\S+)", mail.body).group(1)
    password = f"Staff-Password-{secrets.token_hex(4)}"
    accepted = await client.post(
        f"/auth/invitations/{token}/accept",
        json={"name": "Thandi M", "password": password, "pin": "2468"},
        headers=idem(),
    )
    assert accepted.status_code == 201, accepted.text
    login = await client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    assert login.json()["hotels"][0]["roles"] == ["receptionist"]
    staff = (await client.get("/staff", headers=gm)).json()["data"]
    assert any(m["email"] == email and m["department"] == "Front desk" for m in staff)
    assert (await client.get("/staff/invitations", headers=gm)).json()["data"] == []


async def test_invite_requires_step_up(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("general_manager",))
    h = await factory.auth(hotel, "general_manager")
    r = await client.post(
        "/staff/invitations",
        json={
            "name": "X",
            "email": "x@example.com",
            "role_ids": [await _role_id(owner_engine, "receptionist")],
        },
        headers={**h, **idem()},
    )
    assert r.json()["error"]["code"] == "STEP_UP_REQUIRED"


async def test_cannot_invite_with_more_access_than_you_have(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("general_manager",))
    gm = await _gm(factory, hotel)
    r = await client.post(
        "/staff/invitations",
        json={
            "name": "Boss",
            "email": "boss@example.com",
            "role_ids": [await _role_id(owner_engine, "hotel_owner")],
        },
        headers={**gm, **idem()},
    )
    assert r.json()["error"]["code"] == "PERMISSION_DENIED"
    assert "subscription.manage" in r.json()["error"]["details"]["permissions"]


async def test_duplicate_and_member_invitations_rejected_and_cancel(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("general_manager", "receptionist"))
    gm = await _gm(factory, hotel)
    rec_role = await _role_id(owner_engine, "receptionist")
    member = await client.post(
        "/staff/invitations",
        json={"name": "R", "email": hotel.users["receptionist"].email, "role_ids": [rec_role]},
        headers={**gm, **idem()},
    )
    assert member.status_code == 400
    body = {"name": "N", "email": f"n.{secrets.token_hex(3)}@example.com", "role_ids": [rec_role]}
    first = await client.post("/staff/invitations", json=body, headers={**gm, **idem()})
    again = await client.post("/staff/invitations", json=body, headers={**gm, **idem()})
    assert again.status_code == 400
    cancel = await client.delete(f"/staff/invitations/{first.json()['id']}", headers=gm)
    assert cancel.status_code == 204
    twice = await client.delete(f"/staff/invitations/{first.json()['id']}", headers=gm)
    assert twice.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_set_roles_bumps_perms_version_and_old_token_fails(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("general_manager", "receptionist"))
    gm = await _gm(factory, hotel)
    rec_headers = await factory.auth(hotel, "receptionist")
    assert (await client.get("/rooms", headers=rec_headers)).status_code == 200
    target = hotel.users["receptionist"].user_id
    r = await client.put(
        f"/staff/{target}/roles",
        json={"role_ids": [await _role_id(owner_engine, "reception_manager")]},
        headers=gm,
    )
    assert r.status_code == 200, r.text
    assert [x["code"] for x in r.json()["roles"]] == ["reception_manager"]
    stale = await client.get("/rooms", headers=rec_headers)
    assert stale.status_code == 401
    assert stale.json()["error"]["details"]["reason"] == "perms_changed"


async def test_cannot_act_on_self_or_on_someone_with_more_access(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("hotel_owner", "general_manager"))
    gm = await _gm(factory, hotel)
    me = await client.post(f"/staff/{hotel.users['general_manager'].user_id}/deactivate", headers=gm)
    assert me.json()["error"]["code"] == "PERMISSION_DENIED"
    owner = await client.post(f"/staff/{hotel.users['hotel_owner'].user_id}/deactivate", headers=gm)
    assert owner.json()["error"]["code"] == "PERMISSION_DENIED"


async def test_owner_rule_and_superior_rule(client, factory, owner_engine):
    """An owner may deactivate a co-owner; an admin (no subscription.manage) may not touch an owner."""
    hotel = await factory.hotel(roles=("hotel_owner", "hotel_admin"))
    second = await factory.hotel(roles=("hotel_owner",))  # borrow a ready user, add to this hotel
    co = second.users["hotel_owner"]
    async with owner_engine.begin() as conn:
        hu = (
            await conn.execute(
                text("INSERT INTO app.hotel_users (hotel_id, user_id) VALUES (:h, :u) RETURNING id"),
                {"h": hotel.id, "u": co.user_id},
            )
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO app.user_roles (hotel_id, hotel_user_id, role_id) "
                "SELECT :h, :hu, id FROM app.roles WHERE hotel_id IS NULL AND code = 'hotel_owner'"
            ),
            {"h": hotel.id, "hu": hu},
        )
    admin = await factory.step_up(hotel, "hotel_admin", await factory.auth(hotel, "hotel_admin"))
    denied = await client.post(f"/staff/{co.user_id}/deactivate", headers=admin)
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
    owner = await factory.step_up(hotel, "hotel_owner", await factory.auth(hotel, "hotel_owner"))
    ok = await client.post(f"/staff/{co.user_id}/deactivate", headers=owner)
    assert ok.status_code == 200, ok.text


async def test_deactivate_revokes_sessions_and_keeps_history(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("general_manager", "receptionist"))
    gm = await _gm(factory, hotel)
    rec = await factory.auth(hotel, "receptionist")
    target = hotel.users["receptionist"]
    r = await client.post(f"/staff/{target.user_id}/deactivate", headers=gm)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "deactivated"
    assert (await client.get("/rooms", headers=rec)).status_code == 401
    login = await client.post("/auth/login", json={"email": target.email, "password": target.password})
    assert login.status_code in (401, 403)
    async with owner_engine.connect() as conn:
        live = (
            await conn.execute(
                text("SELECT count(*) FROM app.sessions WHERE user_id = :u AND revoked_at IS NULL"),
                {"u": target.user_id},
            )
        ).scalar_one()
        audit = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM app.audit_logs WHERE hotel_id = :h AND action = 'staff.deactivate'"
                ),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert live == 0
    assert audit == 1
    again = await client.post(f"/staff/{target.user_id}/deactivate", headers=gm)
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_pin_reset_clears_pin(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("general_manager", "kitchen_staff"))
    gm = await _gm(factory, hotel)
    target = hotel.users["kitchen_staff"]
    assert (await client.post(f"/staff/{target.user_id}/pin/reset", headers=gm)).status_code == 204
    staff = {m["user_id"]: m for m in (await client.get("/staff", headers=gm)).json()["data"]}
    assert staff[str(target.user_id)]["has_pin"] is False


async def test_patch_staff_department(client, factory):
    hotel = await factory.hotel(roles=("general_manager", "receptionist"))
    gm = await _gm(factory, hotel)
    target = hotel.users["receptionist"].user_id
    r = await client.patch(f"/staff/{target}", json={"department": "Night desk"}, headers=gm)
    assert r.status_code == 200, r.text
    assert r.json()["department"] == "Night desk"


async def test_custom_role_subset_only_and_system_roles_locked(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("hotel_admin", "receptionist"))
    h = await factory.auth(hotel, "hotel_admin")
    s = await factory.step_up(hotel, "hotel_admin", h)
    ok = await client.post(
        "/roles",
        json={"name": "Night Auditor", "permissions": ["folio.read", "rooms.read"]},
        headers={**s, **idem()},
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["is_system"] is False
    too_much = await client.post(
        "/roles", json={"name": "Payer", "permissions": ["subscription.manage"]}, headers={**s, **idem()}
    )
    assert too_much.json()["error"]["code"] == "PERMISSION_DENIED"
    unknown = await client.post(
        "/roles", json={"name": "Odd", "permissions": ["platform.support"]}, headers={**s, **idem()}
    )
    assert unknown.status_code == 400
    system = await client.patch(
        f"/roles/{await _role_id(owner_engine, 'receptionist')}", json={"name": "Desk"}, headers=s
    )
    assert system.json()["error"]["code"] == "INVALID_TRANSITION"
    roles = (await client.get("/roles", headers=h)).json()["data"]
    assert any(r["name"] == "Night Auditor" for r in roles)


async def test_editing_custom_role_bumps_holders(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("hotel_admin", "receptionist"))
    h = await factory.auth(hotel, "hotel_admin")
    s = await factory.step_up(hotel, "hotel_admin", h)
    role = (
        await client.post(
            "/roles", json={"name": "Viewer", "permissions": ["rooms.read"]}, headers={**s, **idem()}
        )
    ).json()
    target = hotel.users["receptionist"].user_id
    assert (
        await client.put(f"/staff/{target}/roles", json={"role_ids": [role["id"]]}, headers=s)
    ).status_code == 200
    holder = await factory.auth(hotel, "receptionist")
    assert (await client.get("/rooms", headers=holder)).status_code == 200
    patched = await client.patch(
        f"/roles/{role['id']}", json={"permissions": ["rooms.read", "hotel.read"]}, headers=s
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["permissions"] == ["hotel.read", "rooms.read"]
    assert (await client.get("/rooms", headers=holder)).status_code == 401  # perms_v bumped


async def test_staff_cross_tenant_is_404(client, factory, owner_engine):
    a = await factory.hotel(roles=("general_manager", "receptionist"))
    b = await factory.hotel(roles=("receptionist",))
    gm = await _gm(factory, a)
    other = b.users["receptionist"].user_id
    assert (await client.post(f"/staff/{other}/deactivate", headers=gm)).status_code == 404
    assert (await client.patch(f"/staff/{other}", json={"department": "X"}, headers=gm)).status_code == 404
    hb = await factory.auth(b, "receptionist")
    del hb
    b_admin = await factory.hotel(roles=("hotel_admin",))
    sa = await factory.step_up(b_admin, "hotel_admin", await factory.auth(b_admin, "hotel_admin"))
    custom = (
        await client.post(
            "/roles", json={"name": "Secret", "permissions": ["rooms.read"]}, headers={**sa, **idem()}
        )
    ).json()
    ga = await factory.step_up(a, "general_manager", await factory.auth(a, "general_manager"))
    assign = await client.put(
        f"/staff/{a.users['receptionist'].user_id}/roles", json={"role_ids": [custom["id"]]}, headers=ga
    )
    assert assign.status_code == 404
    assert all(r["name"] != "Secret" for r in (await client.get("/roles", headers=gm)).json()["data"])


async def test_staff_plan_limit_counts_pending_invitations(client, factory, owner_engine):
    hotel = await factory.hotel(roles=("general_manager",))
    async with owner_engine.begin() as conn:
        plan = (
            await conn.execute(
                text(
                    "INSERT INTO app.plans (code, name, monthly_price_minor, currency, limits) "
                    "VALUES (:c, 'Tiny', 0, 'ZAR', '{\"staff\": 2}') RETURNING id"
                ),
                {"c": f"tiny_{secrets.token_hex(3)}"},
            )
        ).scalar_one()
        await conn.execute(
            text("UPDATE app.subscriptions SET plan_id = :p WHERE hotel_id = :h"), {"p": plan, "h": hotel.id}
        )
    gm = await _gm(factory, hotel)
    role = await _role_id(owner_engine, "receptionist")
    first = await client.post(
        "/staff/invitations",
        json={"name": "A", "email": "a1@example.com", "role_ids": [role]},
        headers={**gm, **idem()},
    )
    assert first.status_code == 201, first.text
    second = await client.post(
        "/staff/invitations",
        json={"name": "B", "email": "b1@example.com", "role_ids": [role]},
        headers={**gm, **idem()},
    )
    assert second.json()["error"]["code"] == "PLAN_LIMIT_REACHED"
