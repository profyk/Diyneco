"""Platform admin: metrics, hotels, approval and suspension, subscriptions, plans, flags,
health, support access; and the Phase 7 exit criterion: no endpoint lets Diyneco staff read
guest personal data."""

from __future__ import annotations

import re
import uuid
from datetime import date, timedelta

from sqlalchemy import text

from tests.api.test_billing import walk_in
from tests.api.test_checkout import pair_tablet, settle
from tests.api.test_room_service import idem, ready_order, zar

MARKER = "Piimarker"
GUEST_EMAIL = "piimarker.guest@example.com"
GUEST_PHONE = "+27 82 999 4321"


async def platform(factory, role: str = "platform_super_admin") -> dict[str, str]:
    user = await factory.platform_user(role)
    token, _ = await factory.token(None, user)
    return {"Authorization": f"Bearer {token}"}


def step_up(factory, headers: dict[str, str]) -> dict[str, str]:
    from app.core.jwt import STEP_UP_TTL_S

    claims = factory.state.jwt.verify(headers["Authorization"].split(" ", 1)[1], "access")
    token, _ = factory.state.jwt.sign("step_up", {"sub": claims["sub"], "sid": claims["sid"]}, STEP_UP_TTL_S)
    return {**headers, "X-Step-Up": token}


async def test_platform_reads_need_platform_permissions(client, factory):
    hotel = await factory.hotel(rooms=2)
    admin = await platform(factory)
    metrics = await client.get("/admin/metrics", headers=admin)
    assert metrics.status_code == 200, metrics.text
    assert metrics.json()["hotels"] >= 1 and isinstance(metrics.json()["mrr"], list)
    listing = (await client.get("/admin/hotels", headers=admin)).json()["data"]
    row = next(h for h in listing if h["id"] == str(hotel.id))
    assert row["counts"]["rooms"] == 2 and row["plan"] == "starter"
    health = (await client.get("/admin/health", headers=admin)).json()
    assert health["checks"]["database"]["status"] == "ok" and "queue" in health["checks"]

    support = await platform(factory, "platform_support")
    assert (await client.get("/admin/hotels", headers=support)).status_code == 200
    assert (await client.get("/admin/plans", headers=support)).json()["error"]["code"] == "PERMISSION_DENIED"
    gm = await factory.auth(hotel, "general_manager")
    for path in ("/admin/metrics", "/admin/hotels", "/admin/health", "/admin/plans", "/admin/feature-flags"):
        assert (await client.get(path, headers=gm)).json()["error"]["code"] == "PERMISSION_DENIED", path
    # A platform token cannot use hotel endpoints at all.
    assert (await client.get("/rooms", headers=admin)).status_code == 403


async def test_approve_suspend_reactivate(client, factory, owner_engine, mailbox):
    hotel = await factory.hotel(rooms=1, status="pending_approval")
    admin = await platform(factory)
    approved = await client.post(f"/admin/hotels/{hotel.id}/approve", headers={**admin, **idem()})
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "active"
    owner_email = hotel.users["hotel_owner"].email
    assert any(m.to == owner_email and "is live" in m.subject for m in mailbox.sent)
    again = await client.post(f"/admin/hotels/{hotel.id}/approve", headers={**admin, **idem()})
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"

    no_step_up = await client.post(
        f"/admin/hotels/{hotel.id}/suspend", json={"reason": "Unpaid invoices"}, headers={**admin, **idem()}
    )
    assert no_step_up.json()["error"]["code"] == "STEP_UP_REQUIRED"
    admin_s = step_up(factory, admin)
    suspended = await client.post(
        f"/admin/hotels/{hotel.id}/suspend", json={"reason": "Unpaid invoices"}, headers={**admin_s, **idem()}
    )
    assert suspended.json() | {"id": None, "name": None} == {
        "id": None,
        "name": None,
        "status": "suspended",
        "status_reason": "Unpaid invoices",
    }
    # Staff can still read but not write; tablets show the paused state.
    gm = await factory.auth(hotel, "general_manager")
    tablet_gm = await factory.auth(hotel, "general_manager")
    assert (await client.get("/rooms", headers=gm)).status_code == 200
    write = await client.post("/menu/categories", json={"name": "x"}, headers={**gm, **idem()})
    assert write.json()["error"]["code"] == "HOTEL_SUSPENDED"
    _ = tablet_gm

    back = await client.post(f"/admin/hotels/{hotel.id}/reactivate", headers={**admin, **idem()})
    assert back.json()["status"] == "active" and back.json()["status_reason"] is None
    async with owner_engine.connect() as conn:
        actions = (
            await conn.execute(
                text(
                    "SELECT action, actor_type FROM app.audit_logs WHERE hotel_id = :h "
                    "AND action LIKE 'hotel.%' ORDER BY created_at"
                ),
                {"h": hotel.id},
            )
        ).all()
        platform_events = (
            (
                await conn.execute(
                    text(
                        "SELECT type FROM app.event_outbox WHERE hotel_id = :h AND 'platform' = ANY(channels) "
                        "ORDER BY seq"
                    ),
                    {"h": hotel.id},
                )
            )
            .scalars()
            .all()
        )
    assert [tuple(a) for a in actions] == [
        ("hotel.approve", "platform"),
        ("hotel.suspend", "platform"),
        ("hotel.reactivate", "platform"),
    ]
    assert platform_events == ["TENANT_APPROVED", "TENANT_SUSPENDED", "TENANT_REACTIVATED"]
    missing = await client.post(f"/admin/hotels/{uuid.uuid4()}/approve", headers={**admin, **idem()})
    assert missing.status_code == 404


async def test_subscription_plans_and_limits(client, factory):
    hotel = await factory.hotel(rooms=1)
    admin = await platform(factory)
    created = await client.post(
        "/admin/plans",
        json={
            "code": f"tiny_{uuid.uuid4().hex[:6]}",
            "name": "Tiny",
            "monthly_price": zar(49900),
            "limits": {"rooms": 5, "devices": 5, "staff": 50, "api_keys": 1},
        },
        headers={**admin, **idem()},
    )
    assert created.status_code == 201, created.text
    plan = created.json()
    dup = await client.post(
        "/admin/plans",
        json={"code": plan["code"], "name": "Again", "monthly_price": zar(1)},
        headers={**admin, **idem()},
    )
    assert dup.json()["error"]["details"]["reason"] == "code_taken"
    assert plan["code"] in [
        p["code"] for p in (await client.get("/admin/plans", headers=admin)).json()["data"]
    ]

    sub = await client.put(
        f"/admin/hotels/{hotel.id}/subscription",
        json={
            "plan_id": plan["id"],
            "status": "active",
            "starts_on": str(date.today()),
            "renews_on": str(date.today() + timedelta(days=30)),
            "limit_overrides": {"rooms": 1},
        },
        headers=admin,
    )
    assert sub.status_code == 200, sub.text
    assert sub.json()["limits"]["rooms"] == 1 and sub.json()["plan"]["code"] == plan["code"]
    gm = await factory.auth(hotel, "general_manager")
    over = await client.post(
        "/rooms", json={"number": "999", "room_type_id": str(hotel.room_type_id)}, headers={**gm, **idem()}
    )
    assert over.json()["error"]["code"] == "PLAN_LIMIT_REACHED"
    assert over.json()["error"]["details"]["limit"] == 1

    # Changing only the status keeps the hotel's custom limits; {} clears them.
    renewed = await client.put(
        f"/admin/hotels/{hotel.id}/subscription",
        json={"plan_id": plan["id"], "status": "past_due", "starts_on": str(date.today())},
        headers=admin,
    )
    assert renewed.status_code == 200, renewed.text
    assert renewed.json()["limit_overrides"] == {"rooms": 1} and renewed.json()["limits"]["rooms"] == 1
    cleared = await client.put(
        f"/admin/hotels/{hotel.id}/subscription",
        json={
            "plan_id": plan["id"],
            "status": "active",
            "starts_on": str(date.today()),
            "limit_overrides": {},
        },
        headers=admin,
    )
    assert cleared.json()["limit_overrides"] == {}


async def test_feature_flags(client, factory):
    hotel = await factory.hotel(rooms=1)
    admin = await platform(factory)
    key = f"beta.{uuid.uuid4().hex[:8]}"
    r = await client.patch(
        "/admin/feature-flags",
        json={
            "changes": [
                {"key": key, "enabled": False},
                {"key": key, "hotel_id": str(hotel.id), "enabled": True},
            ]
        },
        headers=admin,
    )
    assert r.status_code == 200, r.text
    mine = {(f["hotel_id"], f["enabled"]) for f in r.json()["data"] if f["key"] == key}
    assert mine == {(None, False), (str(hotel.id), True)}
    unknown = await client.patch(
        "/admin/feature-flags",
        json={"changes": [{"key": key, "hotel_id": str(uuid.uuid4()), "enabled": True}]},
        headers=admin,
    )
    assert unknown.status_code == 404


async def test_support_access_is_read_only_ticketed_visible_and_revocable(
    client, factory, owner_engine, mailbox
):
    hotel = await factory.hotel(rooms=1)
    await walk_in(client, factory, hotel)
    support = await platform(factory, "platform_support")
    body = {"ticket_reference": "SUP-1042", "minutes": 30, "reason": "Tablet will not pair"}
    r = await client.post(
        f"/admin/hotels/{hotel.id}/support-access", json=body, headers={**support, **idem()}
    )
    assert r.json()["error"]["code"] == "STEP_UP_REQUIRED"
    granted = await client.post(
        f"/admin/hotels/{hotel.id}/support-access", json=body, headers={**step_up(factory, support), **idem()}
    )
    assert granted.status_code == 201, granted.text
    view = {"Authorization": f"Bearer {granted.json()['access_token']}"}
    over = await client.post(
        f"/admin/hotels/{hotel.id}/support-access",
        json={**body, "minutes": 61},
        headers={**support, **idem()},
    )
    assert over.status_code in (400, 403)

    assert (await client.get("/rooms", headers=view)).status_code == 200
    assert (await client.get("/devices", headers=view)).status_code == 200
    for path in ("/guests", "/stays", "/audit-logs"):
        r = await client.get(path, headers=view)
        assert r.status_code in (403, 404), (path, r.text)
    write = await client.post(
        "/rooms", json={"number": "500", "room_type_id": str(hotel.room_type_id)}, headers={**view, **idem()}
    )
    assert write.json()["error"]["code"] == "PERMISSION_DENIED"

    owner = hotel.users["hotel_owner"]
    assert any(m.to == owner.email and "SUP-1042" in m.body for m in mailbox.sent)
    own = await factory.auth(hotel, "hotel_owner")
    grants = (await client.get("/support-access", headers=own)).json()["data"]
    assert [(g["ticket_reference"], g["active"]) for g in grants] == [("SUP-1042", True)]
    revoked = await client.post(f"/support-access/{grants[0]['id']}/revoke", headers=own)
    assert revoked.json()["active"] is False
    ended = await client.get("/rooms", headers=view)
    assert ended.status_code == 401 and ended.json()["error"]["details"]["reason"] == "support_ended"
    async with owner_engine.connect() as conn:
        actions = (
            (
                await conn.execute(
                    text(
                        "SELECT action FROM app.audit_logs WHERE hotel_id = :h AND action LIKE 'support.%' "
                        "ORDER BY created_at"
                    ),
                    {"h": hotel.id},
                )
            )
            .scalars()
            .all()
        )
    assert actions == ["support.access_granted", "support.access_revoked"]

    other = await factory.hotel(rooms=1)
    other_owner = await factory.auth(other, "hotel_owner")
    assert (await client.get("/support-access", headers=other_owner)).json()["data"] == []
    assert (
        await client.post(f"/support-access/{grants[0]['id']}/revoke", headers=other_owner)
    ).status_code == 404


async def _guest_with_history(client, factory, owner_engine):
    """A hotel whose guest has personal data across stays, orders, payments and invoices."""
    hotel, gm, order, stay = await ready_order(client, factory, owner_engine)
    await factory.auth(hotel, "receptionist")
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.guests SET full_name = :n, email = :e, phone = :p WHERE hotel_id = :h"),
            {"n": f"Zanele {MARKER} Dlamini", "e": GUEST_EMAIL, "p": GUEST_PHONE, "h": hotel.id},
        )
    await pair_tablet(client, gm, hotel.room_ids[0])
    ss = await factory.auth(hotel, "room_service_staff")
    for step in ("claim", "picked-up", "delivered", "leave-on-room"):
        await client.post(f"/deliveries/{order['id']}/{step}", headers={**ss, **idem()})
    await settle(client, factory, hotel, stay["id"])
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    out = await client.post(f"/stays/{stay['id']}/checkout", json={}, headers={**gm_s, **idem()})
    assert out.status_code == 200, out.text
    assert MARKER in out.text  # the bill itself names the guest, for authorised hotel staff
    guest_id = (await client.get(f"/stays/{stay['id']}", headers=gm)).json()["guest"]["id"]
    return hotel, {
        "stay_id": stay["id"],
        "order_id": order["id"],
        "invoice_id": out.json()["invoice"]["id"],
        "guest_id": guest_id,
        "room_id": str(hotel.room_ids[0]),
        "hotel_id": str(hotel.id),
    }


def _fill(path: str, ids: dict[str, str]) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: ids.get(m.group(1), str(uuid.uuid4())), path)


def _leaks(body: str) -> list[str]:
    lowered = body.lower()
    return [s for s in (MARKER.lower(), GUEST_EMAIL, GUEST_PHONE) if s.lower() in lowered]


async def test_exit_admin_cannot_read_guest_pii_through_any_endpoint(client, factory, owner_engine, app):
    """Phase 7 exit criterion. Every GET route is called with a platform super admin token and
    with an active support-access token; no response may contain the guest's name, email or
    phone. The platform write endpoints' responses are checked too."""
    hotel, ids = await _guest_with_history(client, factory, owner_engine)
    admin = await platform(factory)
    granted = await client.post(
        f"/admin/hotels/{hotel.id}/support-access",
        json={"ticket_reference": "SUP-7", "minutes": 10},
        headers={**step_up(factory, admin), **idem()},
    )
    support_view = {"Authorization": f"Bearer {granted.json()['access_token']}"}
    assert not _leaks(granted.text)

    spec = app.openapi()
    paths = sorted(p.removeprefix("/api/v1") for p, ops in spec["paths"].items() if "get" in ops)
    assert len(paths) > 40
    checked = 0
    for path in paths:
        if "dev-storage" in path:
            continue
        url = _fill(path, ids)
        for headers in (admin, support_view):
            r = await client.get(url, headers=headers)
            assert not _leaks(r.text), f"{path} leaked guest data: {r.status_code} {r.text[:300]}"
            checked += 1
    assert checked > 80

    # Write endpoints a platform user can call return no guest data either.
    for r in (
        await client.post(
            f"/admin/hotels/{hotel.id}/suspend",
            json={"reason": "Check"},
            headers={**step_up(factory, admin), **idem()},
        ),
        await client.post(f"/admin/hotels/{hotel.id}/reactivate", headers={**admin, **idem()}),
        await client.get("/admin/hotels", headers=admin),
    ):
        assert r.status_code == 200 and not _leaks(r.text)

    # The guest data is really there: the hotel's own manager can read it.
    gm = await factory.auth(hotel, "general_manager")
    assert _leaks((await client.get(f"/guests/{ids['guest_id']}", headers=gm)).text)
