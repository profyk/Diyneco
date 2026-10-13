"""Plans & Pricing (DECISIONS D74): plans are drafts until published, priced per interval
(month, quarter, year) entirely through the admin API, with a price history that is never
rewritten, and only published plans reach the public pricing page."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.api.test_admin import platform, step_up
from tests.api.test_room_service import idem


def _money(amount: int, currency: str = "ZAR") -> dict:
    return {"amount_minor": amount, "currency": currency}


async def draft_plan(client, admin, currency: str = "ZAR", **fields) -> dict:
    out = await client.post(
        "/admin/plans",
        json={"code": f"t_{uuid.uuid4().hex[:8]}", "name": "Test plan", "currency": currency, **fields},
        headers={**admin, **idem()},
    )
    assert out.status_code == 201, out.text
    return out.json()


async def price(
    client, factory, admin, plan_id: str, interval: str, amount: int, currency: str = "ZAR", **more
):
    return await client.post(
        f"/admin/plans/{plan_id}/prices",
        json={"interval": interval, "amount": _money(amount, currency), "reason": "Test price", **more},
        headers={**step_up(factory, admin), **idem()},
    )


async def published_plan(
    client, factory, admin, amount: int = 49900, currency: str = "ZAR", limits=None
) -> dict:
    plan = await draft_plan(client, admin, currency, limits=limits or {})
    priced = await price(client, factory, admin, plan["id"], "month", amount, currency)
    assert priced.status_code == 201, priced.text
    out = await client.post(
        f"/admin/plans/{plan['id']}/publish",
        json={"reason": "Test"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert out.status_code == 200, out.text
    return out.json()


async def test_a_plan_is_drafted_priced_previewed_and_published(client, factory):
    admin = await platform(factory)
    plan = await draft_plan(
        client,
        admin,
        short_description="For small guest houses",
        highlights=["Guest tablet ordering", "Kitchen display"],
        setup_fee_minor=150000,
        trial_days=14,
        limits={"rooms": 20},
    )
    assert plan["status"] == "draft" and plan["prices"] == {} and plan["setup_fee"] == _money(150000)

    early = await client.post(
        f"/admin/plans/{plan['id']}/publish",
        json={"reason": "Go live"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert early.json()["error"]["code"] == "INVALID_TRANSITION"  # no price yet

    monthly = await price(client, factory, admin, plan["id"], "month", 49900)
    assert monthly.status_code == 201, monthly.text
    annual = await price(
        client, factory, admin, plan["id"], "year", 499000, intro_amount=_money(399000), intro_periods=1
    )
    assert annual.status_code == 201, annual.text
    prices = annual.json()["prices"]
    assert prices["month"]["amount"] == _money(49900) and prices["year"]["amount"] == _money(499000)
    assert prices["year"]["per_month"] == _money(41583)  # 4,990.00 / 12, rounded half up
    assert "quarter" not in prices

    # Drafts are invisible to hotels and the public, but previewable.
    public = (await client.get("/plans")).json()
    assert plan["code"] not in [p["code"] for p in public["data"]]
    preview = (await client.get(f"/admin/plans/{plan['id']}/preview", headers=admin)).json()
    year = next(p for p in preview["prices"] if p["interval"] == "year")
    assert year["saving_bp"] == 1666  # 12 x 499 = 5,988; paying 4,990 saves 16.66%
    assert preview["highlights"] == ["Guest tablet ordering", "Kitchen display"]

    no_step_up = await client.post(
        f"/admin/plans/{plan['id']}/publish", json={"reason": "Go live"}, headers={**admin, **idem()}
    )
    assert no_step_up.json()["error"]["code"] == "STEP_UP_REQUIRED"
    live = await client.post(
        f"/admin/plans/{plan['id']}/publish",
        json={"reason": "Go live"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert live.json()["status"] == "published" and live.json()["published_at"]
    listed = next(p for p in (await client.get("/plans")).json()["data"] if p["code"] == plan["code"])
    assert [p["interval"] for p in listed["prices"]] == ["month", "year"]
    assert listed["trial_days"] == 14 and listed["limits"] == {"rooms": 20}

    archived = await client.post(
        f"/admin/plans/{plan['id']}/archive",
        json={"reason": "Retire"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert archived.json()["status"] == "archived"
    assert plan["code"] not in [p["code"] for p in (await client.get("/plans")).json()["data"]]
    edit = await client.patch(
        f"/admin/plans/{plan['id']}", json={"version": archived.json()["version"], "name": "X"}, headers=admin
    )
    assert edit.json()["error"]["code"] == "INVALID_TRANSITION"
    restored = await client.post(
        f"/admin/plans/{plan['id']}/restore", json={"reason": "Back"}, headers={**admin, **idem()}
    )
    assert restored.json()["status"] == "draft"


async def test_only_billing_administrators_manage_plans(client, factory):
    admin = await platform(factory)
    support = await platform(factory, "platform_support")
    hotel = await factory.hotel()
    owner = await factory.auth(hotel, "hotel_owner")
    body = {"code": "nope_plan", "name": "Nope", "currency": "ZAR"}
    assert (await client.post("/admin/plans", json=body, headers={**support, **idem()})).json()["error"][
        "code"
    ] == ("PERMISSION_DENIED")
    assert (await client.post("/admin/plans", json=body, headers={**owner, **idem()})).status_code in (
        401,
        403,
    )
    plan = await draft_plan(client, admin)
    sneaky = await client.post(
        f"/admin/plans/{plan['id']}/prices",
        json={"interval": "month", "amount": _money(1), "reason": "Cheap"},
        headers={**owner, **idem()},
    )
    assert sneaky.status_code in (401, 403)
    # The public list needs no sign-in and never shows internal fields.
    public = await client.get("/plans")
    assert public.status_code == 200
    assert all("status" not in p and "id" not in p for p in public.json()["data"])


async def test_prices_are_validated_on_the_server(client, factory):
    admin = await platform(factory)
    plan = await draft_plan(client, admin)
    wrong_currency = await price(client, factory, admin, plan["id"], "month", 1000, "USD")
    assert wrong_currency.json()["error"]["details"]["fields"][0]["field"] == "amount"
    negative = await client.post(
        f"/admin/plans/{plan['id']}/prices",
        json={"interval": "month", "amount": _money(-1), "reason": "Bad"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert negative.json()["error"]["code"] == "VALIDATION_FAILED"
    fractional = await client.post(
        f"/admin/plans/{plan['id']}/prices",
        json={"interval": "month", "amount": {"amount_minor": 499.5, "currency": "ZAR"}, "reason": "Bad"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert fractional.json()["error"]["code"] == "VALIDATION_FAILED"
    intro_too_high = await price(
        client, factory, admin, plan["id"], "month", 1000, intro_amount=_money(2000), intro_periods=2
    )
    assert intro_too_high.json()["error"]["details"]["fields"][0]["field"] == "intro_amount"
    intro_alone = await price(client, factory, admin, plan["id"], "month", 1000, intro_amount=_money(500))
    assert intro_alone.json()["error"]["details"]["fields"][0]["field"] == "intro_periods"
    scheduled_draft = await price(
        client,
        factory,
        admin,
        plan["id"],
        "month",
        1000,
        effective_from=(datetime.now(UTC) + timedelta(days=5)).isoformat(),
    )
    assert scheduled_draft.json()["error"]["details"]["fields"][0]["field"] == "effective_from"
    no_reason = await client.post(
        f"/admin/plans/{plan['id']}/prices",
        json={"interval": "month", "amount": _money(1000), "reason": ""},
        headers={**step_up(factory, admin), **idem()},
    )
    assert no_reason.json()["error"]["code"] == "VALIDATION_FAILED"
    promo = await client.patch(
        f"/admin/plans/{plan['id']}",
        json={"version": plan["version"], "promo_discount_bp": 1000},
        headers=admin,
    )
    assert promo.json()["error"]["details"]["fields"][0]["field"] == "promo_ends_on"


async def test_price_changes_never_rewrite_history(client, factory, owner_engine):
    admin = await platform(factory)
    plan = await published_plan(client, factory, admin, amount=99900)
    same = await price(client, factory, admin, plan["id"], "month", 99900)
    assert same.json()["error"]["code"] == "VALIDATION_FAILED"
    past = await price(
        client, factory, admin, plan["id"], "month", 109900, effective_from="2020-01-01T00:00:00Z"
    )
    assert past.json()["error"]["details"]["fields"][0]["field"] == "effective_from"

    later = (datetime.now(UTC) + timedelta(days=45)).replace(microsecond=0)
    scheduled = await price(
        client,
        factory,
        admin,
        plan["id"],
        "month",
        109900,
        effective_from=later.isoformat(),
        existing_policy="next_renewal",
    )
    assert scheduled.status_code == 201, scheduled.text
    s = scheduled.json()
    assert s["prices"]["month"]["amount"] == _money(99900)  # still in force today
    assert s["scheduled"][0]["amount"] == _money(109900)
    assert s["scheduled"][0]["existing_policy"] == "next_renewal" and s["scheduled"][0]["notice_days"] == 30

    # A change at once goes to new subscribers only and moves the old price to history.
    now_change = await price(client, factory, admin, plan["id"], "month", 89900)
    assert now_change.json()["prices"]["month"]["amount"] == _money(89900)
    assert now_change.json()["history"][0]["amount"] == _money(99900)

    withdrawn = await client.delete(
        f"/admin/plans/{plan['id']}/prices/{s['scheduled'][0]['id']}", headers=step_up(factory, admin)
    )
    assert withdrawn.status_code == 200 and withdrawn.json()["scheduled"] == []
    in_force = now_change.json()["prices"]["month"]["id"]
    refused = await client.delete(
        f"/admin/plans/{plan['id']}/prices/{in_force}", headers=step_up(factory, admin)
    )
    assert refused.json()["error"]["code"] == "INVALID_TRANSITION"

    with pytest.raises(DBAPIError, match="append-only"):
        async with owner_engine.begin() as conn:
            await conn.execute(
                text("UPDATE app.plan_prices SET amount_minor = 1 WHERE id = :i"), {"i": in_force}
            )
    with pytest.raises(DBAPIError, match="append-only"):
        async with owner_engine.begin() as conn:
            await conn.execute(text("DELETE FROM app.plan_prices WHERE id = :i"), {"i": in_force})

    async with owner_engine.connect() as conn:
        entry = (
            await conn.execute(
                text(
                    "SELECT actor_id, new_value FROM app.audit_logs WHERE action = 'plan.price_changed' "
                    "AND entity_id = :i"
                ),
                {"i": in_force},
            )
        ).one()
    assert entry.new_value["from"] == 99900 and entry.new_value["to"] == 89900
    assert entry.new_value["reason"] == "Test price" and entry.actor_id is not None


async def test_published_plan_edits_need_a_reason_and_the_current_version(client, factory):
    admin = await platform(factory)
    plan = await published_plan(client, factory, admin)
    no_reason = await client.patch(
        f"/admin/plans/{plan['id']}", json={"version": plan["version"], "name": "Renamed"}, headers=admin
    )
    assert no_reason.json()["error"]["details"]["fields"][0]["field"] == "reason"
    ok = await client.patch(
        f"/admin/plans/{plan['id']}",
        json={"version": plan["version"], "name": "Renamed", "recommended": True, "reason": "Rebrand"},
        headers=admin,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["name"] == "Renamed" and ok.json()["recommended"] is True
    stale = await client.patch(
        f"/admin/plans/{plan['id']}",
        json={"version": plan["version"], "name": "Again", "reason": "x" * 3},
        headers=admin,
    )
    assert stale.json()["error"]["code"] == "PRECONDITION_FAILED"


def _settings_body(s: dict) -> dict:
    return {k: s[k] for k in ("version", "price_change_notice_days", "trial_days", "trial_limits")}


async def test_notice_period_is_configured_in_the_admin_panel(client, factory):
    admin = await platform(factory)
    s = (await client.get("/admin/billing-settings", headers=admin)).json()
    try:
        out = await client.put(
            "/admin/billing-settings",
            json={**_settings_body(s), "price_change_notice_days": 60, "reason": "Longer notice"},
            headers=step_up(factory, admin),
        )
        assert out.status_code == 200, out.text
        assert out.json()["price_change_notice_days"] == 60
        plan = await published_plan(client, factory, admin)
        later = (datetime.now(UTC) + timedelta(days=90)).isoformat()
        p = await price(
            client,
            factory,
            admin,
            plan["id"],
            "month",
            59900,
            effective_from=later,
            existing_policy="next_renewal",
        )
        assert p.json()["scheduled"][0]["notice_days"] == 60
    finally:
        now = (await client.get("/admin/billing-settings", headers=admin)).json()
        await client.put(
            "/admin/billing-settings",
            json={
                **_settings_body(now),
                "price_change_notice_days": s["price_change_notice_days"],
                "reason": "Reset",
            },
            headers=step_up(factory, admin),
        )


async def test_hotels_can_only_ask_for_published_plans(client, factory):
    admin = await platform(factory)
    hotel = await factory.hotel()
    owner = await factory.auth(hotel, "hotel_owner")
    draft = await draft_plan(client, admin)
    refused = await client.post(
        "/subscription/quote", json={"plan_code": draft["code"], "interval": "month"}, headers=owner
    )
    assert refused.json()["error"]["code"] == "NOT_FOUND"
    live = await published_plan(client, factory, admin)
    ok = await client.post(
        "/subscription/quote", json={"plan_code": live["code"], "interval": "month"}, headers=owner
    )
    assert ok.status_code == 200, ok.text
