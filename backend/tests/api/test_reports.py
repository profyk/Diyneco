"""Hotel reports, daily close and audit log; Phase 8 exit criterion: report totals reconcile
to folio entries to the cent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.billing.folio import business_date
from app.services.daily_close_job import send_daily_closes
from tests.api.test_billing import laundry
from tests.api.test_checkout import settle
from tests.api.test_ordering import set_settings
from tests.api.test_room_service import idem, ready_order, zar

TZ = "Africa/Johannesburg"


async def busy_hotel(client, factory, owner_engine):
    """A VAT-registered hotel with accommodation, a delivered order paid with a tip, an other
    charge, a discount, an approved adjustment, a cancelled order and a training stay."""
    hotel = await factory.hotel(rooms=3)
    await set_settings(owner_engine, hotel, vat_registered=True, vat_number="4123456789")
    hotel, gm, order, stay = await ready_order(client, factory, owner_engine, price=300000, hotel=hotel)
    ss = await factory.auth(hotel, "room_service_staff")
    for step in ("claim", "picked-up", "delivered"):
        await client.post(f"/deliveries/{order['id']}/{step}", headers={**ss, **idem()})
    paid = await client.post(
        "/payments",
        json={
            "order_id": order["id"],
            "method": "card_terminal",
            "amount_received": zar(order_total(order) + 50000),
            "terminal_reference": "AB1234",
            "confirm_tip": True,
        },
        headers={**ss, **idem()},
    )
    assert paid.status_code == 201, paid.text
    rec = await factory.auth(hotel, "receptionist")
    folio = (await laundry(client, rec, stay["id"], owner_engine, amount=4500, quantity=3)).json()
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    disc = await client.post(
        f"/folios/{stay['id']}/discounts",
        json={"kind": "percent", "percent_bp": 1250, "applies_to": "all", "reason": "Returning guest"},
        headers={**gm_s, **idem()},
    )
    assert disc.status_code == 201, disc.text
    entry = next(e for e in folio["entries"] if e["category"] == "laundry")
    rm = await factory.auth(hotel, "reception_manager")
    adj = (
        await client.post(
            "/adjustments",
            json={"folio_entry_id": entry["id"], "new_amount": zar(9001), "reason": "One shirt free"},
            headers={**rm, **idem()},
        )
    ).json()
    assert (
        await client.post(f"/adjustments/{adj['id']}/approve", headers={**gm_s, **idem()})
    ).status_code == 200
    # A cancelled phone order: posted, then reversed.
    async with owner_engine.connect() as conn:
        item_id = (
            await conn.execute(text("SELECT id FROM app.menu_items WHERE hotel_id = :h"), {"h": hotel.id})
        ).scalar_one()
    second = (
        await client.post(
            "/orders",
            json={
                "room_id": str(hotel.room_ids[0]),
                "lines": [{"menu_item_id": str(item_id), "quantity": 1}],
                "quoted_total": zar(order_total(order)),
            },
            headers={**rec, **idem()},
        )
    ).json()
    cancelled = await client.post(
        f"/orders/{second['id']}/cancel", json={"reason": "Guest changed mind"}, headers={**gm_s, **idem()}
    )
    assert cancelled.status_code == 200, cancelled.text
    await settle(client, factory, hotel, stay["id"])
    # A training stay must not count.
    training = await client.post(
        f"/rooms/{hotel.room_ids[1]}/walk-in",
        json={"guest": {"name": "Trainee"}, "nights": 1, "training": True},
        headers={**rec, **idem()},
    )
    assert training.status_code == 201, training.text
    return hotel, gm, stay


def order_total(order: dict) -> int:
    return 300000  # ready_order's platter, VAT inclusive, no fee


async def folio_truth(owner_engine, hotel_id, day_from, day_to) -> dict[str, int]:
    """The same figures straight from the ledger."""
    async with owner_engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT c.revenue_group AS g, coalesce(sum(fe.amount_minor), 0) AS a, "
                    "coalesce(sum(fe.vat_minor), 0) AS v "
                    "FROM app.folio_entries fe JOIN app.charge_categories c ON c.id = fe.category_id "
                    "JOIN app.folios f ON f.id = fe.folio_id JOIN app.stays s ON s.id = f.stay_id "
                    "WHERE fe.hotel_id = :h AND NOT s.is_training AND fe.business_date BETWEEN :f AND :t "
                    "GROUP BY 1"
                ),
                {"h": hotel_id, "f": day_from, "t": day_to},
            )
        ).all()
    by = {r.g: (int(r.a), int(r.v)) for r in rows}
    groups = ("accommodation", "fnb", "other")
    return {
        **{g: by.get(g, (0, 0))[0] for g in groups},
        "vat": sum(by.get(g, (0, 0))[1] for g in groups),
        "tips": by.get("tip", (0, 0))[0],
        "payments": -by.get("payment", (0, 0))[0],
    }


async def test_exit_revenue_report_reconciles_to_the_folio_to_the_cent(client, factory, owner_engine):
    hotel, _gm, stay = await busy_hotel(client, factory, owner_engine)
    fin = await factory.auth(hotel, "finance_manager")
    day_from = business_date(TZ) - timedelta(days=2)
    day_to = business_date(TZ) + timedelta(days=3)
    report = await client.get(
        "/reports/revenue", params={"from": str(day_from), "to": str(day_to)}, headers=fin
    )
    assert report.status_code == 200, report.text
    total = report.json()["total"]
    truth = await folio_truth(owner_engine, hotel.id, day_from, day_to)
    assert total["accommodation"]["amount_minor"] == truth["accommodation"]
    assert total["fnb"]["amount_minor"] == truth["fnb"]
    assert total["other"]["amount_minor"] == truth["other"]
    assert total["vat_included"]["amount_minor"] == truth["vat"]
    assert total["tips"]["amount_minor"] == truth["tips"] == 50000
    assert total["payments"]["amount_minor"] == truth["payments"]
    assert total["revenue"]["amount_minor"] == truth["accommodation"] + truth["fnb"] + truth["other"]
    # Days add up to the total, and each day matches the ledger for that day.
    for key in (
        "accommodation",
        "fnb",
        "other",
        "vat_included",
        "tips",
        "payments",
        "discounts",
        "adjustments",
    ):
        assert sum(d[key]["amount_minor"] for d in report.json()["days"]) == total[key]["amount_minor"], key
    for d in report.json()["days"]:
        day = datetime.fromisoformat(d["date"]).date()
        t = await folio_truth(owner_engine, hotel.id, day, day)
        assert (d["accommodation"]["amount_minor"], d["fnb"]["amount_minor"], d["other"]["amount_minor"]) == (
            t["accommodation"],
            t["fnb"],
            t["other"],
        )
    # Discounts, adjustments and the cancelled order's reversal show on their own.
    assert total["discounts"]["amount_minor"] < 0
    assert total["adjustments"]["amount_minor"] == 9001 - 13500
    assert total["reversals"]["amount_minor"] < 0
    # The folio's own balance view agrees with the report.
    async with owner_engine.connect() as conn:
        bal = (
            await conn.execute(
                text(
                    "SELECT accommodation_minor, fnb_minor, other_minor, tips_minor, paid_minor, balance_minor "
                    "FROM app.folio_balances WHERE stay_id = :s"
                ),
                {"s": stay["id"]},
            )
        ).one()
    assert (bal.accommodation_minor, bal.fnb_minor, bal.other_minor) == (
        truth["accommodation"],
        truth["fnb"],
        truth["other"],
    )
    assert bal.balance_minor == 0 and bal.paid_minor == truth["payments"]

    # The payments report agrees with the ledger's payment entries and tips.
    pay = (
        await client.get("/reports/payments", params={"from": str(day_from), "to": str(day_to)}, headers=fin)
    ).json()
    assert pay["total"]["amount"]["amount_minor"] == truth["payments"]
    assert pay["total"]["tips"]["amount_minor"] == truth["tips"]
    methods = {m["method"]: m for m in pay["by_method"]}
    assert set(methods) == {"card_terminal", "cash"} and methods["card_terminal"]["tips"] == zar(50000)


async def test_operational_reports_and_permissions(client, factory, owner_engine):
    hotel, _gm, _stay = await busy_hotel(client, factory, owner_engine)
    today = business_date(TZ)
    params = {"from": str(today - timedelta(days=1)), "to": str(today + timedelta(days=1))}
    km = await factory.auth(hotel, "kitchen_manager")
    orders = (await client.get("/reports/orders", params=params, headers=km)).json()
    assert (orders["orders"], orders["cancelled"]) == (2, 1)
    assert sum(h["orders"] for h in orders["by_hour"]) == 2
    items = (await client.get("/reports/items", params=params, headers=km)).json()["items"]
    assert items[0]["name"] == "Seafood platter" and items[0]["quantity"] == 1
    kitchen = (await client.get("/reports/kitchen", params=params, headers=km)).json()["stations"]
    assert kitchen[0]["items"] == 1 and kitchen[0]["median_seconds"] >= 0
    rs = (await client.get("/reports/room-service", params=params, headers=km)).json()["staff"]
    assert rs[0]["deliveries"] == 1
    occ = (await client.get("/reports/occupancy", params=params, headers=km)).json()
    tonight = next(n for n in occ["nights"] if n["date"] == str(today))
    assert (tonight["rooms"], tonight["occupied"]) == (3, 1)  # the training stay is not counted

    # Money needs reports.finance; the kitchen manager has reports.read only.
    for path in ("/reports/revenue", "/reports/payments", "/reports/daily-close", "/reports/open-balances"):
        r = await client.get(
            path, params=params if "daily" not in path and "open" not in path else None, headers=km
        )
        assert r.json()["error"]["code"] == "PERMISSION_DENIED", path
    rec = await factory.auth(hotel, "receptionist")
    assert (await client.get("/reports/orders", params=params, headers=rec)).status_code == 403
    bad = await client.get(
        "/reports/orders", params={"from": str(today), "to": str(today - timedelta(days=1))}, headers=km
    )
    assert bad.json()["error"]["code"] == "VALIDATION_FAILED"

    other = await factory.hotel(rooms=1)
    fin_b = await factory.auth(other, "finance_manager")
    revenue_b = (await client.get("/reports/revenue", params=params, headers=fin_b)).json()
    assert revenue_b["total"]["revenue"] == zar(0)


async def test_daily_close_review_flags_and_email(
    client, factory, owner_engine, app_state, worker_engine, mailbox
):
    hotel, _gm, _stay = await busy_hotel(client, factory, owner_engine)
    fin = await factory.auth(hotel, "finance_manager")
    today = business_date(TZ)
    report = (await client.get("/reports/daily-close", params={"date": str(today)}, headers=fin)).json()
    card = report["card"]["recorded"]["amount_minor"]
    assert card > 0 and report["card"]["terminal_batch_total"] is None
    assert len(report["discounts"]) == 1 and len(report["adjustments"]) == 1
    put = await client.put(
        f"/reports/daily-close/{today}",
        json={
            "terminal_batch_total": zar(card - 100),
            "cash_counted": report["cash"]["recorded"],
            "mark_reviewed": True,
        },
        headers=fin,
    )
    assert put.status_code == 200, put.text
    assert put.json()["flags"] == ["card_total_mismatch"] and put.json()["reviewed_at"]
    # Saving notes alone keeps the batch total and cash count entered before.
    notes = await client.put(f"/reports/daily-close/{today}", json={"notes": "Checked"}, headers=fin)
    assert notes.json()["card"]["terminal_batch_total"] == zar(card - 100)
    assert notes.json()["cash"]["counted"] == report["cash"]["recorded"]
    assert notes.json()["notes"] == "Checked" and notes.json()["flags"] == ["card_total_mismatch"]
    future = await client.put(f"/reports/daily-close/{today + timedelta(days=2)}", json={}, headers=fin)
    assert future.json()["error"]["code"] == "VALIDATION_FAILED"

    # The 06:00 email goes once to the GM and the Finance Manager for yesterday.
    maker = async_sessionmaker(worker_engine, expire_on_commit=False)
    seven_am_tomorrow = datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(
        tzinfo=__import__("zoneinfo").ZoneInfo(TZ)
    ) + timedelta(hours=7)
    before = len(mailbox.sent)
    sent = await send_daily_closes(maker, app_state.mailer, now=seven_am_tomorrow.astimezone(UTC))
    assert sent >= 2
    mine = [m for m in mailbox.sent[before:] if hotel.name in m.subject]
    assert {m.to for m in mine} == {
        hotel.users["general_manager"].email,
        hotel.users["finance_manager"].email,
    }
    assert "card total mismatch" in mine[0].body
    again = len(mailbox.sent)
    await send_daily_closes(maker, app_state.mailer, now=seven_am_tomorrow.astimezone(UTC))
    assert not [m for m in mailbox.sent[again:] if hotel.name in m.subject]


async def test_open_balances_and_audit_log(client, factory, owner_engine):
    hotel, gm, order, stay = await ready_order(client, factory, owner_engine)
    ss = await factory.auth(hotel, "room_service_staff")
    for step in ("claim", "picked-up", "delivered", "leave-on-room"):
        await client.post(f"/deliveries/{order['id']}/{step}", headers={**ss, **idem()})
    await set_settings(owner_engine, hotel, checkout_override_allowed=True)
    gm_s = await factory.step_up(hotel, "general_manager", gm)
    out = await client.post(
        f"/stays/{stay['id']}/checkout",
        json={"override": True, "override_reason": "Company pays on account"},
        headers={**gm_s, **idem()},
    )
    assert out.status_code == 200, out.text
    fin = await factory.auth(hotel, "finance_manager")
    ar = (await client.get("/reports/open-balances", headers=fin)).json()
    assert [(r["stay_id"], r["override_reason"]) for r in ar["data"]] == [
        (stay["id"], "Company pays on account")
    ]
    assert ar["total"] == ar["data"][0]["balance"]

    page1 = (await client.get("/audit-logs", params={"limit": 2}, headers=fin)).json()
    assert len(page1["data"]) == 2 and page1["next_cursor"]
    page2 = (
        await client.get("/audit-logs", params={"limit": 2, "cursor": page1["next_cursor"]}, headers=fin)
    ).json()
    assert {e["id"] for e in page1["data"]}.isdisjoint({e["id"] for e in page2["data"]})
    checkouts = (await client.get("/audit-logs", params={"action": "stay.check_out"}, headers=fin)).json()[
        "data"
    ]
    assert len(checkouts) == 1 and checkouts[0]["reason"] == "Company pays on account"
    assert (
        await client.get("/audit-logs", headers=await factory.auth(hotel, "receptionist"))
    ).status_code == 403
