"""Subscribing, paying, refunds, the billing engine and the billing dashboard (DECISIONS D79).

Money only counts once the server has verified it: a sandbox checkout's explicit choice
(test money, never collected revenue), a provider status fetched on the server, or a payment a
billing administrator saw on the bank statement. Renewals, reminders and suspensions run in the
worker and are safe to repeat. Billing settings and company settings are shared rows: tests
that change them restore them."""

from __future__ import annotations

import json
import time
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.billing import providers
from app.billing.providers import Checkout, ProviderStatus
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.services import billing_engine
from tests.api.test_admin import platform, step_up
from tests.api.test_room_service import idem
from tests.api.test_subscriptions import _plan, _vat

TODAY = date.today()


async def _trial_hotel(factory, owner_engine, **kw):
    hotel = await factory.hotel(**kw)
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE app.subscriptions SET plan_id = NULL, status = 'trial', trial_ends_on = :t "
                "WHERE hotel_id = :h"
            ),
            {"h": hotel.id, "t": TODAY + timedelta(days=10)},
        )
    return hotel


async def _owner(factory, hotel) -> dict:
    return await factory.step_up(hotel, "hotel_owner", await factory.auth(hotel, "hotel_owner"))


async def _subscribe(client, factory, hotel, code: str, interval: str = "month") -> dict:
    out = await client.post(
        "/subscription/subscribe",
        json={"plan_code": code, "interval": interval, "accept_terms": True},
        headers={**await _owner(factory, hotel), **idem()},
    )
    assert out.status_code == 201, out.text
    return out.json()


async def _pay_sandbox(client, factory, hotel, invoice_id: str, outcome: str = "succeeded") -> dict:
    owner = await _owner(factory, hotel)
    checkout = await client.post(f"/subscription/invoices/{invoice_id}/pay", headers={**owner, **idem()})
    assert checkout.status_code == 201, checkout.text
    done = await client.post(
        f"/subscription/payment-attempts/{checkout.json()['id']}/sandbox",
        json={"outcome": outcome},
        headers={**owner, **idem()},
    )
    assert done.status_code == 200, done.text
    return done.json()


async def _process(worker_engine, app_state, hotel_id, today: date) -> None:
    """One billing-engine pass for one hotel, as the worker runs it (diyneco_worker)."""
    sm = async_sessionmaker(worker_engine, expire_on_commit=False, autoflush=False)  # as Database
    async with sm() as s:
        uow = UnitOfWork(session=s, sessionmaker=sm)
        async with s.begin():
            await set_tenant(s, hotel_id)
            ctx = TenantContext(hotel_id=hotel_id, actor_type="system", actor_id=None, actor_label="Billing")
            await billing_engine.process_hotel(app_state, uow, ctx, today)
        await uow.run_after_commit()


async def _one(owner_engine, sql: str, **params):
    async with owner_engine.connect() as conn:
        return (await conn.execute(text(sql), params)).one()


async def _active(client, factory, owner_engine, admin, **plan_fields):
    """A hotel with a paid, active monthly subscription to a fresh published plan."""
    plan = await _plan(client, factory, admin, **plan_fields)
    hotel = await _trial_hotel(factory, owner_engine)
    sub = await _subscribe(client, factory, hotel, plan["code"])
    await _pay_sandbox(client, factory, hotel, sub["invoice"]["id"])
    return plan, hotel, sub


def _sent(mailbox, template: str, after: int = 0) -> list:
    return [m for m in mailbox.sent[after:] if m.template == template]


async def test_subscribing_issues_the_first_invoice_and_a_verified_payment_starts_it(
    client, factory, owner_engine, mailbox
):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    plan = await _plan(client, factory, admin)
    hotel = await _trial_hotel(factory, owner_engine)
    owner = await _owner(factory, hotel)
    unaccepted = await client.post(
        "/subscription/subscribe",
        json={"plan_code": plan["code"], "interval": "month", "accept_terms": False},
        headers={**owner, **idem()},
    )
    assert unaccepted.json()["error"]["code"] == "VALIDATION_FAILED"
    sneaky = await client.post(
        "/subscription/subscribe",
        json={"plan_code": plan["code"], "interval": "month", "accept_terms": True, "total_minor": 1},
        headers={**owner, **idem()},
    )
    assert sneaky.json()["error"]["code"] == "VALIDATION_FAILED"  # prices come from the server

    mark = len(mailbox.sent)
    out = await _subscribe(client, factory, hotel, plan["code"])
    inv, sub = out["invoice"], out["subscription"]
    assert sub["status"] == "pending_payment" and sub["price"]["amount_minor"] == 49900
    assert inv["purpose"] == "initial" and inv["total"]["amount_minor"] == 49900 and inv["number"]
    assert sub["outstanding"][0]["balance"]["amount_minor"] == 49900
    assert _sent(mailbox, "subscription_invoice", mark)
    again = await client.post(
        "/subscription/subscribe",
        json={"plan_code": plan["code"], "interval": "month", "accept_terms": True},
        headers={**owner, **idem()},
    )
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"

    options = (await client.get("/subscription/payment-options", headers=owner)).json()
    assert options["online"] == {
        "available": True,
        "provider": "sandbox",
        "label": "Test payment (sandbox, no money moves)",
        "test_mode": True,
    }
    checkout = await client.post(f"/subscription/invoices/{inv['id']}/pay", headers={**owner, **idem()})
    attempt = checkout.json()
    assert attempt["status"] == "pending" and attempt["test_mode"] and "sandbox=1" in attempt["checkout_url"]
    # Reaching the return page proves nothing: the attempt stays pending.
    assert (await client.get(f"/subscription/payment-attempts/{attempt['id']}", headers=owner)).json()[
        "status"
    ] == "pending"
    assert (await client.get("/subscription", headers=owner)).json()["status"] == "pending_payment"

    other = await factory.hotel()
    other_owner = await _owner(factory, other)
    assert (
        await client.get(f"/subscription/payment-attempts/{attempt['id']}", headers=other_owner)
    ).status_code == 404
    assert (
        await client.post(f"/subscription/invoices/{inv['id']}/pay", headers={**other_owner, **idem()})
    ).status_code == 404
    gm = await factory.auth(hotel, "general_manager")
    assert (await client.post(f"/subscription/invoices/{inv['id']}/pay", headers={**gm, **idem()})).json()[
        "error"
    ]["code"] == "PERMISSION_DENIED"

    mark = len(mailbox.sent)
    done = await client.post(
        f"/subscription/payment-attempts/{attempt['id']}/sandbox",
        json={"outcome": "succeeded"},
        headers={**owner, **idem()},
    )
    assert done.json()["status"] == "succeeded"
    view = (await client.get("/subscription", headers=owner)).json()
    assert view["status"] == "active" and view["plan"]["code"] == plan["code"] and view["outstanding"] == []
    paid = (await client.get(f"/subscription/invoices/{inv['id']}", headers=owner)).json()
    assert paid["status"] == "paid" and paid["balance"]["amount_minor"] == 0
    payments = (await client.get("/subscription/payments", headers=owner)).json()["data"]
    assert [(p["method"], p["test_mode"], p["amount"]["amount_minor"]) for p in payments] == [
        ("sandbox", True, 49900)
    ]
    assert _sent(mailbox, "billing_payment_succeeded", mark) and _sent(
        mailbox, "billing_subscription_confirmed", mark
    )
    twice = await client.post(
        f"/subscription/payment-attempts/{attempt['id']}/sandbox",
        json={"outcome": "succeeded"},
        headers={**owner, **idem()},
    )
    assert twice.json()["error"]["code"] == "INVALID_TRANSITION"
    # Plan limits apply once paid for.
    assert view["limits"] == plan["limits"]


async def test_failed_payments_and_bank_transfers_recorded_by_billing_administrators(
    client, factory, owner_engine, mailbox
):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    plan = await _plan(client, factory, admin)
    hotel = await _trial_hotel(factory, owner_engine)
    inv = (await _subscribe(client, factory, hotel, plan["code"]))["invoice"]
    mark = len(mailbox.sent)
    failed = await _pay_sandbox(client, factory, hotel, inv["id"], "failed")
    assert failed["status"] == "failed" and _sent(mailbox, "billing_payment_failed", mark)
    owner = await _owner(factory, hotel)
    assert (await client.get(f"/subscription/invoices/{inv['id']}", headers=owner)).json()[
        "status"
    ] == "issued"

    before = (await client.get("/admin/billing/summary", headers=admin)).json()
    url = f"/admin/hotels/{hotel.id}/payments"
    body = {
        "invoice_id": inv["id"],
        "amount_minor": 20000,
        "reference": "FNB 1234",
        "received_on": str(TODAY),
    }
    no_step_up = await client.post(url, json=body, headers={**admin, **idem()})
    assert no_step_up.json()["error"]["code"] == "STEP_UP_REQUIRED"
    support = await platform(factory, "platform_support")
    denied = await client.post(url, json=body, headers={**step_up(factory, support), **idem()})
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
    too_much = await client.post(
        url, json={**body, "amount_minor": 49901}, headers={**step_up(factory, admin), **idem()}
    )
    assert too_much.json()["error"]["code"] == "VALIDATION_FAILED"
    future = await client.post(
        url,
        json={**body, "received_on": str(TODAY + timedelta(days=2))},
        headers={**step_up(factory, admin), **idem()},
    )
    assert future.json()["error"]["code"] == "VALIDATION_FAILED"

    part = await client.post(url, json=body, headers={**step_up(factory, admin), **idem()})
    assert part.status_code == 201, part.text
    assert part.json()["reconciliation_status"] == "matched" and part.json()["test_mode"] is False
    dup = await client.post(url, json=body, headers={**step_up(factory, admin), **idem()})
    assert dup.json()["error"]["code"] == "INVALID_TRANSITION"
    partial = (await client.get(f"/subscription/invoices/{inv['id']}", headers=owner)).json()
    assert partial["status"] == "partially_paid" and partial["balance"]["amount_minor"] == 29900
    assert (await client.get("/subscription", headers=owner)).json()["status"] == "pending_payment"

    rest = await client.post(
        url,
        json={**body, "amount_minor": 29900, "reference": "FNB 1299"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert rest.status_code == 201
    assert (await client.get("/subscription", headers=owner)).json()["status"] == "active"
    after = (await client.get("/admin/billing/summary", headers=admin)).json()

    def zar(summary, key):
        return next(c for c in summary["currencies"] if c["currency"] == "ZAR")[key]["amount_minor"]

    assert zar(after, "collected") - zar(before, "collected") == 49900  # real money counts
    assert zar(after, "test_collected") == zar(before, "test_collected")
    audit = await _one(
        owner_engine,
        "SELECT count(*) AS n FROM app.audit_logs WHERE hotel_id = :h AND action = 'subscription_payment.received'",
        h=hotel.id,
    )
    assert audit.n == 2


async def test_refunds_come_with_a_credit_note_and_records_stay_permanent(
    client, factory, owner_engine, mailbox
):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    plan = await _plan(client, factory, admin)
    hotel = await _trial_hotel(factory, owner_engine)
    inv = (await _subscribe(client, factory, hotel, plan["code"]))["invoice"]
    paid = await client.post(
        f"/admin/hotels/{hotel.id}/payments",
        json={
            "invoice_id": inv["id"],
            "amount_minor": 49900,
            "reference": "EFT 77",
            "received_on": str(TODAY),
        },
        headers={**step_up(factory, admin), **idem()},
    )
    payment = paid.json()
    url = f"/admin/hotels/{hotel.id}/payments/{payment['id']}/refund"
    no_ref = await client.post(
        url, json={"amount_minor": 10000, "reason": "Goodwill"}, headers={**step_up(factory, admin), **idem()}
    )
    assert no_ref.json()["error"]["code"] == "VALIDATION_FAILED"  # a bank refund needs its reference
    mark = len(mailbox.sent)
    refund = await client.post(
        url,
        json={"amount_minor": 10000, "reason": "Goodwill", "reference": "EFT OUT 1"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert refund.status_code == 201, refund.text
    assert refund.json()["credit_note_number"].startswith("CN-") and refund.json()["method"] == "manual"
    assert _sent(mailbox, "billing_refund_processed", mark) and _sent(
        mailbox, "subscription_credit_note", mark
    )
    too_much = await client.post(
        url,
        json={"amount_minor": 40000, "reason": "More", "reference": "EFT OUT 2"},
        headers={**step_up(factory, admin), **idem()},
    )
    assert too_much.json()["error"]["code"] == "VALIDATION_FAILED"
    listed = (await client.get(f"/admin/hotels/{hotel.id}/payments", headers=admin)).json()["data"]
    assert listed[0]["refunded"]["amount_minor"] == 10000
    original = (await client.get(f"/admin/hotels/{hotel.id}/invoices", headers=admin)).json()["data"]
    assert next(i for i in original if i["id"] == inv["id"])["balance"]["amount_minor"] == 0

    for sql in (
        "UPDATE app.subscription_payments SET amount_minor = 1 WHERE id = :i",
        "DELETE FROM app.subscription_payments WHERE id = :i",
    ):
        with pytest.raises(DBAPIError, match=r"permanent record|never deleted"):
            async with owner_engine.begin() as conn:
                await conn.execute(text(sql), {"i": payment["id"]})
    with pytest.raises(DBAPIError):
        async with owner_engine.begin() as conn:
            await conn.execute(
                text("UPDATE app.subscription_refunds SET amount_minor = 1 WHERE payment_id = :i"),
                {"i": payment["id"]},
            )
    reconciled = await client.post(
        f"/admin/hotels/{hotel.id}/payments/{payment['id']}/reconcile",
        json={"status": "disputed", "note": "Not on statement"},
        headers={**admin, **idem()},
    )
    assert reconciled.json()["reconciliation_status"] == "disputed"


async def test_cancelling_a_subscription_that_never_started_voids_its_first_invoice(
    client, factory, owner_engine
):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    plan = await _plan(client, factory, admin)
    hotel = await _trial_hotel(factory, owner_engine)
    inv = (await _subscribe(client, factory, hotel, plan["code"]))["invoice"]
    owner = await _owner(factory, hotel)
    out = await client.post(
        "/subscription/cancel", json={"reason": "Changed our mind"}, headers={**owner, **idem()}
    )
    assert out.status_code == 200, out.text
    assert out.json()["status"] is None
    assert (await client.get(f"/subscription/invoices/{inv['id']}", headers=owner)).json()["status"] == "void"
    # Subscribing again starts a new subscription.
    again = await _subscribe(client, factory, hotel, plan["code"])
    assert again["subscription"]["status"] == "pending_payment"


async def test_renewals_are_invoiced_once_and_follow_the_billing_anchor(
    client, factory, owner_engine, worker_engine, app_state
):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    _plan_row, hotel, _sub = await _active(client, factory, owner_engine, admin)
    # Anchor 31: the period that ends on 28 Feb 2027 is followed by one ending on 31 Mar 2027.
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE app.subscriptions SET anchor_day = 31, current_period_start = '2027-01-31', "
                "renews_on = '2027-02-28' WHERE hotel_id = :h AND status = 'active'"
            ),
            {"h": hotel.id},
        )
    for _ in range(2):  # the worker repeats itself every few minutes
        await _process(worker_engine, app_state, hotel.id, date(2027, 2, 24))
    sql = (
        "SELECT count(*) AS n, min(period_start) AS ps, min(period_end) AS pe, min(due_on) AS due, "
        "min(total_minor) AS total FROM app.subscription_invoices WHERE hotel_id = :h AND purpose = 'renewal'"
    )
    renewal = await _one(owner_engine, sql, h=hotel.id)
    assert renewal.n == 1 and (renewal.ps, renewal.pe) == (date(2027, 2, 28), date(2027, 3, 31))
    assert renewal.due == date(2027, 2, 28) and renewal.total == 49900
    with pytest.raises(IntegrityError):  # the database refuses a second invoice for the period
        async with owner_engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO app.subscription_invoices (hotel_id, subscription_id, kind, purpose, currency, "
                    "period_start, period_end) SELECT hotel_id, subscription_id, 'invoice', 'renewal', currency, "
                    "period_start, period_end FROM app.subscription_invoices WHERE hotel_id = :h AND purpose = 'renewal'"
                ),
                {"h": hotel.id},
            )
    for _ in range(2):
        await _process(worker_engine, app_state, hotel.id, date(2027, 2, 28))
    moved = await _one(
        owner_engine,
        "SELECT current_period_start, renews_on FROM app.subscriptions WHERE hotel_id = :h AND status = 'active'",
        h=hotel.id,
    )
    assert (moved.current_period_start, moved.renews_on) == (date(2027, 2, 28), date(2027, 3, 31))
    renewed = await _one(
        owner_engine,
        "SELECT count(*) AS n FROM app.subscription_billing_events WHERE hotel_id = :h AND kind = 'subscription.renewed'",
        h=hotel.id,
    )
    assert renewed.n == 1


async def test_overdue_invoices_lead_to_suspension_and_payment_restores_access(
    client, factory, owner_engine, worker_engine, app_state, mailbox
):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    _plan_row, hotel, _sub = await _active(client, factory, owner_engine, admin)
    renews = TODAY + timedelta(days=2)
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE app.subscriptions SET anchor_day = :d, current_period_start = :s, renews_on = :r "
                "WHERE hotel_id = :h AND status = 'active'"
            ),
            {"h": hotel.id, "d": renews.day, "s": renews - timedelta(days=30), "r": renews},
        )
        settings = (await conn.execute(text("SELECT grace_days FROM app.billing_settings"))).one()
    mark = len(mailbox.sent)
    await _process(worker_engine, app_state, hotel.id, TODAY)
    owner = await _owner(factory, hotel)
    renewal = next(
        i
        for i in (await client.get("/subscription/invoices", headers=owner)).json()["data"]
        if i["purpose"] == "renewal"
    )
    assert _sent(mailbox, "billing_upcoming_renewal", mark)

    await _process(worker_engine, app_state, hotel.id, renews + timedelta(days=1))
    view = (await client.get("/subscription", headers=owner)).json()
    assert view["status"] == "past_due" and view["outstanding"][0]["status"] == "overdue"
    assert _sent(mailbox, "billing_payment_reminder", mark)  # on the due date

    await _process(worker_engine, app_state, hotel.id, renews + timedelta(days=settings.grace_days + 1))
    assert (await client.get("/subscription", headers=owner)).json()["status"] == "suspended"
    assert _sent(mailbox, "billing_subscription_suspended", mark) and _sent(
        mailbox, "billing_invoice_overdue", mark
    )
    room = {"number": f"S{time.time_ns() % 10000}", "room_type_id": str(hotel.room_type_id)}
    blocked = await client.post("/rooms", json=room, headers={**owner, **idem()})
    assert blocked.json()["error"]["code"] == "SUBSCRIPTION_SUSPENDED"
    assert (await client.get("/rooms", headers=owner)).status_code == 200  # data stays readable

    await _pay_sandbox(client, factory, hotel, renewal["id"])  # billing stays open while suspended
    assert (await client.get("/subscription", headers=owner)).json()["status"] == "active"
    assert _sent(mailbox, "billing_subscription_reactivated", mark)
    assert (await client.post("/rooms", json=room, headers={**owner, **idem()})).status_code == 201


async def test_trials_expire_and_unpaid_first_invoices_end_the_subscription(
    client, factory, owner_engine, worker_engine, app_state, mailbox
):
    await _vat(owner_engine, on=False)
    hotel = await _trial_hotel(factory, owner_engine)
    mark = len(mailbox.sent)
    await _process(worker_engine, app_state, hotel.id, TODAY + timedelta(days=5))
    assert _sent(mailbox, "billing_trial_ending", mark)
    await _process(worker_engine, app_state, hotel.id, TODAY + timedelta(days=10))
    owner = await _owner(factory, hotel)
    assert (await client.get("/subscription", headers=owner)).json()["status"] is None
    assert _sent(mailbox, "billing_trial_ended", mark)

    admin = await platform(factory)
    plan = await _plan(client, factory, admin)
    out = await _subscribe(client, factory, hotel, plan["code"])
    due = date.fromisoformat(out["invoice"]["due_on"])
    grace = (await _one(owner_engine, "SELECT grace_days FROM app.billing_settings")).grace_days
    await _process(worker_engine, app_state, hotel.id, due + timedelta(days=grace + 1))
    assert (await client.get("/subscription", headers=owner)).json()["status"] is None
    inv = (await client.get(f"/subscription/invoices/{out['invoice']['id']}", headers=owner)).json()
    assert inv["status"] == "void"
    ended = await _one(
        owner_engine,
        "SELECT status FROM app.subscriptions WHERE hotel_id = :h ORDER BY created_at DESC LIMIT 1",
        h=hotel.id,
    )
    assert ended.status == "expired"


async def test_plan_changes_wait_for_renewal_unless_an_upgrade_is_prorated(
    client, factory, owner_engine, worker_engine, app_state
):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    plan, hotel, _sub = await _active(client, factory, owner_engine, admin)
    big = await _plan(client, factory, admin)
    from tests.api.test_plans import price

    assert (await price(client, factory, admin, big["id"], "month", 99900)).status_code == 201
    owner = await _owner(factory, hotel)
    down = await client.post(
        "/subscription/change",
        json={"plan_code": big["code"], "interval": "year"},
        headers={**owner, **idem()},
    )
    # 4,990.00 a year is less a month than 499.00 monthly: a downgrade, at renewal.
    assert down.json()["effective"] == "renewal"
    assert down.json()["subscription"]["pending_change"]["plan_code"] == big["code"]
    withdrawn = await client.post(
        "/subscription/change",
        json={"plan_code": plan["code"], "interval": "month"},
        headers={**owner, **idem()},
    )
    assert (
        withdrawn.json()["effective"] == "withdrawn"
        and withdrawn.json()["subscription"]["pending_change"] is None
    )

    async with owner_engine.begin() as conn:
        await conn.execute(text("UPDATE app.billing_settings SET proration_enabled = true"))
        await conn.execute(
            text(
                "UPDATE app.subscriptions SET current_period_start = :s, renews_on = :r, anchor_day = :d "
                "WHERE hotel_id = :h AND status = 'active'"
            ),
            {"h": hotel.id, "s": TODAY - timedelta(days=10), "r": TODAY + timedelta(days=20), "d": TODAY.day},
        )
    try:
        up = await client.post(
            "/subscription/change",
            json={"plan_code": big["code"], "interval": "month"},
            headers={**owner, **idem()},
        )
        assert up.status_code == 200, up.text
        assert up.json()["effective"] == "now"
        # (999.00 - 499.00) x 20 of 30 days = 333.33
        assert up.json()["invoice"]["purpose"] == "proration"
        assert up.json()["invoice"]["total"]["amount_minor"] == 33333
        assert up.json()["subscription"]["plan"]["code"] == big["code"]
    finally:
        async with owner_engine.begin() as conn:
            await conn.execute(text("UPDATE app.billing_settings SET proration_enabled = false"))


async def test_price_changes_reach_existing_subscribers_only_at_renewal_after_notice(
    client, factory, owner_engine, worker_engine, app_state
):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    plan, hotel, _sub = await _active(client, factory, owner_engine, admin)
    from tests.api.test_plans import price

    raised = await price(client, factory, admin, plan["id"], "month", 59900, existing_policy="next_renewal")
    assert raised.status_code == 201, raised.text
    notice = (await _one(owner_engine, "SELECT price_change_notice_days AS d FROM app.billing_settings")).d

    async def renew_on(day: date) -> int:
        async with owner_engine.begin() as conn:
            await conn.execute(
                text(
                    "UPDATE app.subscriptions SET renews_on = :r, anchor_day = :a, current_period_start = :s "
                    "WHERE hotel_id = :h AND status = 'active'"
                ),
                {"h": hotel.id, "r": day, "a": day.day, "s": day - timedelta(days=28)},
            )
        await _process(worker_engine, app_state, hotel.id, day - timedelta(days=1))
        row = await _one(
            owner_engine,
            "SELECT total_minor FROM app.subscription_invoices WHERE hotel_id = :h AND purpose = 'renewal' "
            "AND period_start = :r",
            h=hotel.id,
            r=day,
        )
        return int(row.total_minor)

    assert await renew_on(TODAY + timedelta(days=max(1, notice - 5))) == 49900  # notice not yet given
    assert await renew_on(TODAY + timedelta(days=notice + 40)) == 59900


async def test_stitch_webhooks_are_signed_verified_and_processed_once(
    client, factory, owner_engine, app_state, monkeypatch
):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    plan = await _plan(client, factory, admin)
    hotel = await _trial_hotel(factory, owner_engine)
    inv = (await _subscribe(client, factory, hotel, plan["code"]))["invoice"]
    secret = "whsec_" + "dGVzdC1zZWNyZXQtZm9yLXN0aXRjaA=="
    s = app_state.settings
    monkeypatch.setattr(s, "stitch_client_id", "test-client")
    monkeypatch.setattr(s, "stitch_client_secret", "test-secret")
    monkeypatch.setattr(s, "stitch_webhook_secret", secret)
    monkeypatch.setattr(s, "merchant_app_url", "https://merchant.example")
    # Not a long digit run: the card-number guard would (rightly) refuse one that passes Luhn.
    ref = f"pr_{uuid.uuid4()}"
    calls: list[str] = []

    async def create_checkout(self, **kw):
        assert kw["return_url"].startswith("https://merchant.example/billing/return?attempt=")
        return Checkout(provider_ref=ref, url="https://stitch.example/pay")

    async def fetch_status(self, provider_ref, currency):
        calls.append(provider_ref)
        return ProviderStatus(status="succeeded", provider_payment_id=provider_ref, amount_minor=49900)

    monkeypatch.setattr(providers.StitchProvider, "create_checkout", create_checkout)
    monkeypatch.setattr(providers.StitchProvider, "fetch_status", fetch_status)
    async with owner_engine.begin() as conn:
        await conn.execute(text("UPDATE app.billing_settings SET card_provider = 'stitch'"))
    try:
        owner = await _owner(factory, hotel)
        checkout = await client.post(f"/subscription/invoices/{inv['id']}/pay", headers={**owner, **idem()})
        assert checkout.status_code == 201, checkout.text
        assert checkout.json()["provider"] == "stitch" and checkout.json()["test_mode"] is True

        body = json.dumps({"data": {"client": {"paymentInitiationRequests": {"node": {"id": ref}}}}}).encode()
        stamp = int(time.time())

        def headers(msg: str, ts: int = stamp, sig: str | None = None) -> dict:
            return {
                "svix-id": msg,
                "svix-timestamp": str(ts),
                "svix-signature": sig or providers.sign_svix(secret, msg, ts, body),
                "content-type": "application/json",
            }

        forged = await client.post(
            "/billing/webhooks/stitch", content=body, headers=headers("msg_1", sig="v1,AAAA")
        )
        assert forged.status_code == 401
        stale = await client.post(
            "/billing/webhooks/stitch", content=body, headers=headers("msg_1", ts=stamp - 3600)
        )
        assert stale.status_code == 401
        assert calls == []

        ok = await client.post("/billing/webhooks/stitch", content=body, headers=headers("msg_1"))
        assert ok.status_code == 200 and ok.json()["status"] == "succeeded"
        again = await client.post("/billing/webhooks/stitch", content=body, headers=headers("msg_1"))
        assert again.json()["status"] == "duplicate"
        other = await client.post("/billing/webhooks/stitch", content=body, headers=headers("msg_2"))
        assert other.status_code == 200
        payments = (await client.get("/subscription/payments", headers=owner)).json()["data"]
        assert len(payments) == 1 and payments[0]["method"] == "pay_by_bank"
        assert (await client.get("/subscription", headers=owner)).json()["status"] == "active"
        assert calls == [ref]  # verified with the provider once; the duplicate was not re-processed
        events = (await client.get("/admin/billing/webhooks", headers=admin)).json()["data"]
        assert {"msg_1", "msg_2"} <= {e["event_id"] for e in events}
        status = await client.get("/admin/billing/provider", headers=admin)
        assert (
            status.json()["stitch"]["ready"] is True
            and "whsec" not in status.text
            and "test-secret" not in status.text
        )
    finally:
        async with owner_engine.begin() as conn:
            await conn.execute(text("UPDATE app.billing_settings SET card_provider = 'sandbox'"))


async def test_a_failed_email_never_repeats_a_payment(client, factory, owner_engine, mailbox, monkeypatch):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    plan = await _plan(client, factory, admin)
    hotel = await _trial_hotel(factory, owner_engine)
    inv = (await _subscribe(client, factory, hotel, plan["code"]))["invoice"]

    async def broken(message):
        raise ConnectionError("smtp down")

    monkeypatch.setattr(mailbox, "send", broken)
    await _pay_sandbox(client, factory, hotel, inv["id"])
    monkeypatch.undo()
    owner = await _owner(factory, hotel)
    assert len((await client.get("/subscription/payments", headers=owner)).json()["data"]) == 1
    failed = await _one(
        owner_engine,
        "SELECT count(*) AS n FROM app.notifications WHERE hotel_id = :h AND template = 'billing_payment_succeeded' "
        "AND status = 'failed'",
        h=hotel.id,
    )
    assert failed.n >= 1


async def test_the_billing_dashboard_lists_filters_and_exports(client, factory, owner_engine):
    await _vat(owner_engine, on=False)
    admin = await platform(factory)
    plan, hotel, _sub = await _active(client, factory, owner_engine, admin)
    name = (await _one(owner_engine, "SELECT name FROM app.hotels WHERE id = :h", h=hotel.id)).name
    summary = await client.get("/admin/billing/summary", headers=admin)
    assert summary.status_code == 200 and "from" in summary.json()
    by_plan = next(p for p in summary.json()["by_plan"] if p["plan_code"] == plan["code"])
    assert by_plan["subscriptions"] == 1 and by_plan["mrr"]["amount_minor"] == 49900
    assert by_plan["collected"]["amount_minor"] == 0  # a sandbox payment is not collected revenue

    found = (await client.get("/admin/billing/invoices", params={"q": name}, headers=admin)).json()
    assert (
        found["total"] == 1
        and found["data"][0]["status"] == "paid"
        and found["data"][0]["plan_code"] == plan["code"]
    )
    paid = (
        await client.get("/admin/billing/invoices", params={"q": name, "payment": "unpaid"}, headers=admin)
    ).json()
    assert paid["total"] == 0
    csv_out = await client.get("/admin/billing/invoices", params={"q": name, "format": "csv"}, headers=admin)
    assert csv_out.headers["content-type"].startswith("text/csv")
    assert csv_out.text.splitlines()[0].startswith("number,kind,status,hotel")
    assert "499.00" in csv_out.text
    pays = await client.get("/admin/billing/payments", params={"q": name, "format": "csv"}, headers=admin)
    assert len(pays.text.strip().splitlines()) == 2 and ",yes," in pays.text  # test payment marked

    owner = await factory.auth(hotel, "hotel_owner")
    assert (await client.get("/admin/billing/summary", headers=owner)).status_code in (401, 403)
    support = await platform(factory, "platform_support")
    assert (await client.get("/admin/billing/invoices", headers=support)).json()["error"][
        "code"
    ] == "PERMISSION_DENIED"


def test_csv_cells_cannot_become_formulas():
    from app.services.billing_admin import _safe

    assert _safe("=HYPERLINK(1)") == "'=HYPERLINK(1)" and _safe("Hotel") == "Hotel" and _safe(None) == ""
