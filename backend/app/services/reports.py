"""Hotel reports (API spec, Reports). Every money figure is computed from folio entries and
payments, so a report reconciles to the bills to the cent. Training stays are excluded.

Dates are hotel-local business dates. Payments and orders are placed on a business date by
their time in the hotel's time zone.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import insert, select, text, update

from app.audit.writer import write_audit
from app.billing.folio import business_date
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.domain import DailyClose
from app.repositories.hotels import HotelRepository
from app.services.pricing import money

MAX_RANGE_DAYS = 366


async def _settings(uow: UnitOfWork, ctx: TenantContext) -> Any:
    st = await HotelRepository(uow.session, ctx).get_settings()
    if st is None:
        raise AppError("NOT_FOUND")
    return st


def _range(date_from: date, date_to: date) -> None:
    if date_to < date_from:
        raise AppError("VALIDATION_FAILED", "`to` must not be before `from`.")
    if (date_to - date_from).days >= MAX_RANGE_DAYS:
        raise AppError("VALIDATION_FAILED", "A report covers at most 366 days.")


async def _rows(uow: UnitOfWork, sql: str, params: dict[str, Any]) -> list[Any]:
    return list((await uow.session.execute(text(sql), params)).mappings().all())


# --- Revenue ---------------------------------------------------------------------------------


REVENUE_SQL = """
SELECT fe.business_date AS day, c.revenue_group AS grp, fe.entry_type AS kind,
       sum(fe.amount_minor) AS amount, sum(fe.vat_minor) AS vat
FROM app.folio_entries fe
JOIN app.charge_categories c ON c.id = fe.category_id
JOIN app.folios f ON f.id = fe.folio_id
WHERE fe.hotel_id = :h AND fe.business_date BETWEEN :f AND :t
  AND NOT EXISTS (SELECT 1 FROM app.stays st WHERE st.id = f.stay_id AND st.is_training)
GROUP BY 1, 2, 3
"""


async def revenue(uow: UnitOfWork, ctx: TenantContext, date_from: date, date_to: date) -> dict[str, Any]:
    """Per business day: accommodation, F&B and other services net of discounts, reversals
    and adjustments (which are also shown on their own), VAT contained, payments, and tips,
    which are never revenue."""
    _range(date_from, date_to)
    currency = (await _settings(uow, ctx)).currency
    keys = (
        "accommodation",
        "fnb",
        "other",
        "discounts",
        "adjustments",
        "reversals",
        "vat",
        "tips",
        "payments",
    )
    days: dict[date, dict[str, int]] = {
        date_from + timedelta(days=i): dict.fromkeys(keys, 0) for i in range((date_to - date_from).days + 1)
    }
    for r in await _rows(uow, REVENUE_SQL, {"h": ctx.hotel_id, "f": date_from, "t": date_to}):
        d = days[r["day"]]
        amount, grp, kind = int(r["amount"]), r["grp"], r["kind"]
        if grp == "tip":
            d["tips"] += amount
        elif grp == "payment":
            d["payments"] += -amount
        else:
            d[grp] += amount
            d["vat"] += int(r["vat"])
            if kind == "discount":
                d["discounts"] += amount
            elif kind == "adjustment":
                d["adjustments"] += amount
            elif kind == "reversal":
                d["reversals"] += amount
    total = dict.fromkeys(keys, 0)
    out = []
    for day, d in days.items():
        for k in keys:
            total[k] += d[k]
        out.append(_revenue_row(day, d, currency))
    return {"from": date_from, "to": date_to, "days": out, "total": _revenue_row(None, total, currency)}


def _revenue_row(day: date | None, d: dict[str, int], c: str) -> dict[str, Any]:
    net = d["accommodation"] + d["fnb"] + d["other"]
    return {
        **({"date": day} if day else {}),
        "accommodation": money(d["accommodation"], c),
        "fnb": money(d["fnb"], c),
        "other": money(d["other"], c),
        "revenue": money(net, c),
        "vat_included": money(d["vat"], c),
        "revenue_excluding_vat": money(net - d["vat"], c),
        "discounts": money(d["discounts"], c),
        "adjustments": money(d["adjustments"], c),
        "reversals": money(d["reversals"], c),
        "payments": money(d["payments"], c),
        "tips": money(d["tips"], c),
    }


# --- Payments --------------------------------------------------------------------------------


PAYMENTS_SQL = """
SELECT p.method, p.recorded_by AS staff_id, coalesce(u.name, 'Device') AS staff_name,
       count(*) AS n, sum(p.amount_received_minor - p.tip_amount_minor) AS applied,
       sum(p.amount_received_minor) AS received, sum(p.tip_amount_minor) AS tips,
       count(*) FILTER (WHERE p.late_reason IS NOT NULL) AS late
FROM app.payments p
JOIN app.hotel_settings hs ON hs.hotel_id = p.hotel_id
LEFT JOIN app.users u ON u.id = p.recorded_by
WHERE p.hotel_id = :h AND p.status IN ('paid', 'partial')
  AND (p.occurred_at AT TIME ZONE hs.timezone)::date BETWEEN :f AND :t
GROUP BY 1, 2, 3
ORDER BY 1, 3
"""


async def payments(uow: UnitOfWork, ctx: TenantContext, date_from: date, date_to: date) -> dict[str, Any]:
    _range(date_from, date_to)
    c = (await _settings(uow, ctx)).currency
    rows = await _rows(uow, PAYMENTS_SQL, {"h": ctx.hotel_id, "f": date_from, "t": date_to})
    by_method: dict[str, dict[str, int]] = defaultdict(
        lambda: {"count": 0, "amount": 0, "received": 0, "tips": 0}
    )
    by_staff: dict[Any, dict[str, Any]] = {}
    for r in rows:
        m = by_method[r["method"]]
        s = by_staff.setdefault(
            r["staff_id"],
            {"name": r["staff_name"], "count": 0, "amount": 0, "received": 0, "tips": 0, "late": 0},
        )
        for target in (m, s):
            target["count"] += int(r["n"])
            target["amount"] += int(r["applied"])
            target["received"] += int(r["received"])
            target["tips"] += int(r["tips"])
        s["late"] += int(r["late"])

    def fmt(v: dict[str, Any]) -> dict[str, Any]:
        return {
            **{k: v[k] for k in v if k not in ("amount", "received", "tips")},
            "amount": money(v["amount"], c),
            "received": money(v["received"], c),
            "tips": money(v["tips"], c),
        }

    totals = {
        "count": sum(v["count"] for v in by_method.values()),
        "amount": sum(v["amount"] for v in by_method.values()),
        "received": sum(v["received"] for v in by_method.values()),
        "tips": sum(v["tips"] for v in by_method.values()),
    }
    return {
        "from": date_from,
        "to": date_to,
        "by_method": [{"method": k, **fmt(v)} for k, v in sorted(by_method.items())],
        "by_staff": [{"staff_id": k, **fmt(v)} for k, v in by_staff.items()],
        "total": fmt(totals),
    }


# --- Orders, items, kitchen, room service ----------------------------------------------------


ORDER_WINDOW = """
FROM app.orders o
JOIN app.hotel_settings hs ON hs.hotel_id = o.hotel_id
WHERE o.hotel_id = :h AND (o.created_at AT TIME ZONE hs.timezone)::date BETWEEN :f AND :t
  AND NOT EXISTS (SELECT 1 FROM app.stays st WHERE st.id = o.stay_id AND st.is_training)
"""


async def orders(uow: UnitOfWork, ctx: TenantContext, date_from: date, date_to: date) -> dict[str, Any]:
    _range(date_from, date_to)
    c = (await _settings(uow, ctx)).currency
    p = {"h": ctx.hotel_id, "f": date_from, "t": date_to}
    summary = (
        await _rows(
            uow,
            "SELECT count(*) AS n, "
            "count(*) FILTER (WHERE o.status = 'CANCELLED') AS cancelled, "
            "count(*) FILTER (WHERE o.status = 'DECLINED') AS declined, "
            "coalesce(sum(o.total_minor) FILTER (WHERE o.status NOT IN ('CANCELLED','DECLINED')), 0) "
            "AS value, "
            "count(*) FILTER (WHERE o.status NOT IN ('CANCELLED','DECLINED')) AS kept " + ORDER_WINDOW,
            p,
        )
    )[0]
    hours = await _rows(
        uow,
        "SELECT extract(hour FROM o.created_at AT TIME ZONE hs.timezone)::int AS hour, count(*) AS n "  # noqa: S608 - constant fragments; values are bound
        + ORDER_WINDOW
        + " GROUP BY 1 ORDER BY 1",
        p,
    )
    kept = int(summary["kept"])
    return {
        "from": date_from,
        "to": date_to,
        "orders": int(summary["n"]),
        "completed_or_open": kept,
        "cancelled": int(summary["cancelled"]),
        "declined": int(summary["declined"]),
        "value": money(int(summary["value"]), c),
        "average_order_value": money((int(summary["value"]) // kept) if kept else 0, c),
        "by_hour": [{"hour": int(r["hour"]), "orders": int(r["n"])} for r in hours],
    }


async def items(
    uow: UnitOfWork, ctx: TenantContext, date_from: date, date_to: date, limit: int = 20
) -> dict[str, Any]:
    _range(date_from, date_to)
    c = (await _settings(uow, ctx)).currency
    rows = await _rows(
        uow,
        "SELECT oi.menu_item_id, min(oi.name) AS name, sum(oi.quantity) AS qty, "
        "sum(oi.line_total_minor) AS revenue "
        "FROM app.order_items oi JOIN app.orders o ON o.id = oi.order_id "
        "JOIN app.hotel_settings hs ON hs.hotel_id = o.hotel_id "
        "WHERE oi.hotel_id = :h AND o.status NOT IN ('CANCELLED','DECLINED') "
        "AND (o.created_at AT TIME ZONE hs.timezone)::date BETWEEN :f AND :t "
        "AND NOT EXISTS (SELECT 1 FROM app.stays st WHERE st.id = o.stay_id AND st.is_training) "
        "GROUP BY 1 ORDER BY qty DESC, revenue DESC LIMIT :n",
        {"h": ctx.hotel_id, "f": date_from, "t": date_to, "n": limit},
    )
    return {
        "from": date_from,
        "to": date_to,
        "items": [
            {
                "menu_item_id": r["menu_item_id"],
                "name": r["name"],
                "quantity": int(r["qty"]),
                "revenue": money(int(r["revenue"]), c),
            }
            for r in rows
        ],
    }


async def kitchen(uow: UnitOfWork, ctx: TenantContext, date_from: date, date_to: date) -> dict[str, Any]:
    """Median and 90th percentile seconds from the order's acceptance to each item being ready."""
    _range(date_from, date_to)
    rows = await _rows(
        uow,
        "SELECT oi.station_id, ks.name, count(*) AS n, "
        "percentile_cont(0.5) WITHIN GROUP "
        "(ORDER BY extract(epoch FROM oi.ready_at - o.accepted_at)) AS p50, "
        "percentile_cont(0.9) WITHIN GROUP (ORDER BY extract(epoch FROM oi.ready_at - o.accepted_at)) AS p90 "
        "FROM app.order_items oi JOIN app.orders o ON o.id = oi.order_id "
        "JOIN app.kitchen_stations ks ON ks.id = oi.station_id "
        "JOIN app.hotel_settings hs ON hs.hotel_id = o.hotel_id "
        "WHERE oi.hotel_id = :h AND oi.ready_at IS NOT NULL AND o.accepted_at IS NOT NULL "
        "AND (o.created_at AT TIME ZONE hs.timezone)::date BETWEEN :f AND :t "
        "GROUP BY 1, 2 ORDER BY 2",
        {"h": ctx.hotel_id, "f": date_from, "t": date_to},
    )
    return {
        "from": date_from,
        "to": date_to,
        "stations": [
            {
                "station_id": r["station_id"],
                "name": r["name"],
                "items": int(r["n"]),
                "median_seconds": round(float(r["p50"]), 1),
                "p90_seconds": round(float(r["p90"]), 1),
            }
            for r in rows
        ],
    }


async def room_service(uow: UnitOfWork, ctx: TenantContext, date_from: date, date_to: date) -> dict[str, Any]:
    """Median seconds from the order being ready to it being delivered, by staff member."""
    _range(date_from, date_to)
    rows = await _rows(
        uow,
        "SELECT d.assigned_to AS staff_id, u.name, count(*) AS n, "
        "percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM d.delivered_at - o.ready_at)) AS p50 "
        "FROM app.deliveries d JOIN app.orders o ON o.id = d.order_id "
        "LEFT JOIN app.users u ON u.id = d.assigned_to "
        "JOIN app.hotel_settings hs ON hs.hotel_id = o.hotel_id "
        "WHERE d.hotel_id = :h AND d.delivered_at IS NOT NULL AND o.ready_at IS NOT NULL "
        "AND (o.created_at AT TIME ZONE hs.timezone)::date BETWEEN :f AND :t "
        "GROUP BY 1, 2 ORDER BY 2",
        {"h": ctx.hotel_id, "f": date_from, "t": date_to},
    )
    return {
        "from": date_from,
        "to": date_to,
        "staff": [
            {
                "staff_id": r["staff_id"],
                "name": r["name"],
                "deliveries": int(r["n"]),
                "median_seconds": round(float(r["p50"]), 1),
            }
            for r in rows
        ],
    }


async def occupancy(uow: UnitOfWork, ctx: TenantContext, date_from: date, date_to: date) -> dict[str, Any]:
    """Room-nights per night: occupied (a checked-in stay covers the night), out of service
    (rooms currently out of service; room status history is not kept), and available."""
    _range(date_from, date_to)
    rows = await _rows(
        uow,
        "WITH nights AS (SELECT generate_series(CAST(:f AS date), CAST(:t AS date), interval '1 day')::date "
        "AS d) "
        "SELECT n.d AS night, "
        "(SELECT count(*) FROM app.rooms r WHERE r.hotel_id = :h AND r.deleted_at IS NULL "
        "   AND r.created_at::date <= n.d) AS rooms, "
        "(SELECT count(*) FROM app.rooms r WHERE r.hotel_id = :h AND r.deleted_at IS NULL "
        "   AND r.status = 'out_of_service') AS oos, "
        "(SELECT count(*) FROM app.stays s WHERE s.hotel_id = :h AND s.checked_in_at IS NOT NULL "
        "   AND NOT s.is_training AND s.status IN ('active','checkout_pending','checked_out') "
        "   AND s.arrival_date <= n.d AND s.departure_date > n.d) AS occupied "
        "FROM nights n ORDER BY 1",
        {"h": ctx.hotel_id, "f": date_from, "t": date_to},
    )
    nights = []
    total = {"rooms": 0, "occupied": 0, "out_of_service": 0, "available": 0}
    for r in rows:
        rooms, occ, oos = int(r["rooms"]), int(r["occupied"]), int(r["oos"])
        row = {"rooms": rooms, "occupied": occ, "out_of_service": oos, "available": max(0, rooms - occ - oos)}
        for k in total:
            total[k] += row[k]
        nights.append({"date": r["night"], **row, "occupancy_bp": (occ * 10000 // rooms) if rooms else 0})
    sellable = total["rooms"] - total["out_of_service"]
    return {
        "from": date_from,
        "to": date_to,
        "nights": nights,
        "total": {**total, "occupancy_bp": (total["occupied"] * 10000 // sellable) if sellable > 0 else 0},
    }


async def open_balances(uow: UnitOfWork, ctx: TenantContext) -> dict[str, Any]:
    """Accounts receivable: checked-out stays whose bill still has a balance (D45)."""
    c = (await _settings(uow, ctx)).currency
    rows = await _rows(
        uow,
        "SELECT s.id AS stay_id, r.number AS room, coalesce(bp.company_name, g.full_name) AS bill_to, "
        "s.billing_type, s.checked_out_at, s.checkout_override_reason, b.balance_minor "
        "FROM app.stays s JOIN app.folio_balances b ON b.stay_id = s.id "
        "JOIN app.rooms r ON r.id = s.room_id JOIN app.guests g ON g.id = s.guest_id "
        "LEFT JOIN app.billing_profiles bp ON bp.id = s.billing_profile_id "
        "WHERE s.hotel_id = :h AND s.status = 'checked_out' AND b.balance_minor > 0 AND NOT s.is_training "
        "ORDER BY s.checked_out_at",
        {"h": ctx.hotel_id},
    )
    return {
        "data": [
            {
                "stay_id": r["stay_id"],
                "room": r["room"],
                "bill_to": r["bill_to"],
                "billing_type": r["billing_type"],
                "checked_out_at": r["checked_out_at"],
                "override_reason": r["checkout_override_reason"],
                "balance": money(int(r["balance_minor"]), c),
            }
            for r in rows
        ],
        "total": money(sum(int(r["balance_minor"]) for r in rows), c),
    }


# --- Daily close ----------------------------------------------------------------------------


async def _recorded(uow: UnitOfWork, ctx: TenantContext, day: date) -> dict[str, int]:
    rows = await _rows(
        uow,
        "SELECT p.method, coalesce(sum(p.amount_received_minor), 0) AS received FROM app.payments p "
        "JOIN app.hotel_settings hs ON hs.hotel_id = p.hotel_id "
        "WHERE p.hotel_id = :h AND p.status IN ('paid','partial') "
        "AND (p.occurred_at AT TIME ZONE hs.timezone)::date = :d GROUP BY 1",
        {"h": ctx.hotel_id, "d": day},
    )
    got = {r["method"]: int(r["received"]) for r in rows}
    return {"card": got.get("card_terminal", 0), "cash": got.get("cash", 0)}


async def daily_close(uow: UnitOfWork, ctx: TenantContext, day: date) -> dict[str, Any]:
    c = (await _settings(uow, ctx)).currency
    p = {"h": ctx.hotel_id, "d": day}
    rev = await revenue(uow, ctx, day, day)
    pay = await payments(uow, ctx, day, day)
    recorded = await _recorded(uow, ctx, day)
    adjustments = await _rows(
        uow,
        "SELECT a.id, a.original_minor, a.new_minor, a.reason, a.status, ru.name AS requested_by, "
        "du.name AS decided_by FROM app.adjustments a "
        "JOIN app.hotel_settings hs ON hs.hotel_id = a.hotel_id "
        "LEFT JOIN app.users ru ON ru.id = a.requested_by LEFT JOIN app.users du ON du.id = a.decided_by "
        "WHERE a.hotel_id = :h AND (a.requested_at AT TIME ZONE hs.timezone)::date = :d "
        "ORDER BY a.requested_at",
        p,
    )
    discounts = await _rows(
        uow,
        "SELECT d.id, d.kind, d.percent_bp, d.amount_minor, d.applies_to, d.reason, u.name AS given_by "
        "FROM app.discounts d JOIN app.hotel_settings hs ON hs.hotel_id = d.hotel_id "
        "LEFT JOIN app.users u ON u.id = d.created_by "
        "WHERE d.hotel_id = :h AND (d.created_at AT TIME ZONE hs.timezone)::date = :d ORDER BY d.created_at",
        p,
    )
    overrides = await _rows(
        uow,
        "SELECT s.id AS stay_id, r.number AS room, s.checkout_override_reason AS reason "
        "FROM app.stays s JOIN app.rooms r ON r.id = s.room_id "
        "JOIN app.hotel_settings hs ON hs.hotel_id = s.hotel_id "
        "WHERE s.hotel_id = :h AND s.checkout_override_reason IS NOT NULL "
        "AND (s.checked_out_at AT TIME ZONE hs.timezone)::date = :d",
        p,
    )
    late = await _rows(
        uow,
        "SELECT 'payment' AS kind, p.id, p.late_reason AS reason, p.occurred_at, p.created_at "
        "FROM app.payments p JOIN app.hotel_settings hs ON hs.hotel_id = p.hotel_id "
        "WHERE p.hotel_id = :h AND p.late_reason IS NOT NULL "
        "AND (p.occurred_at AT TIME ZONE hs.timezone)::date = :d "
        "UNION ALL SELECT 'order', o.id, o.late_reason, o.created_at, o.created_at "
        "FROM app.orders o JOIN app.hotel_settings hs ON hs.hotel_id = o.hotel_id "
        "WHERE o.hotel_id = :h AND o.late_reason IS NOT NULL "
        "AND (o.created_at AT TIME ZONE hs.timezone)::date = :d",
        p,
    )
    row = (
        await uow.session.execute(
            select(DailyClose).where(DailyClose.hotel_id == ctx.hotel_id, DailyClose.business_date == day)
        )
    ).scalar_one_or_none()
    flags = _flags(row, recorded, overrides, late)
    return {
        "date": day,
        "revenue": rev["total"],
        "payments": {"by_method": pay["by_method"], "by_staff": pay["by_staff"], "total": pay["total"]},
        "tips_by_staff": [
            {"staff_id": s["staff_id"], "name": s["name"], "tips": s["tips"]} for s in pay["by_staff"]
        ],
        "card": {
            "recorded": money(recorded["card"], c),
            "terminal_batch_total": money(row.terminal_batch_total_minor, c)
            if row and row.terminal_batch_total_minor is not None
            else None,
        },
        "cash": {
            "recorded": money(recorded["cash"], c),
            "counted": money(row.cash_counted_minor, c)
            if row and row.cash_counted_minor is not None
            else None,
        },
        "adjustments": [
            {
                "id": a["id"],
                "original": money(int(a["original_minor"]), c),
                "new_amount": money(int(a["new_minor"]), c),
                "reason": a["reason"],
                "status": a["status"],
                "requested_by": a["requested_by"],
                "decided_by": a["decided_by"],
            }
            for a in adjustments
        ],
        "discounts": [
            {
                "id": d["id"],
                "kind": d["kind"],
                "percent_bp": d["percent_bp"],
                "amount": money(int(d["amount_minor"]), c) if d["amount_minor"] is not None else None,
                "applies_to": d["applies_to"],
                "reason": d["reason"],
                "given_by": d["given_by"],
            }
            for d in discounts
        ],
        "overrides": [dict(o) for o in overrides],
        "late_entries": [dict(x) for x in late],
        "flags": flags,
        "notes": row.notes if row else None,
        "reviewed_at": row.reviewed_at if row else None,
        "reviewed_by": row.reviewed_by if row else None,
    }


def _flags(
    row: DailyClose | None, recorded: dict[str, int], overrides: list[Any], late: list[Any]
) -> list[str]:
    flags = []
    if (
        row is not None
        and row.terminal_batch_total_minor is not None
        and row.terminal_batch_total_minor != recorded["card"]
    ):
        flags.append("card_total_mismatch")
    if row is not None and row.cash_counted_minor is not None and row.cash_counted_minor != recorded["cash"]:
        flags.append("cash_count_mismatch")
    if overrides:
        flags.append("checkout_overrides")
    if late:
        flags.append("late_entries")
    return flags


async def put_daily_close(
    uow: UnitOfWork, ctx: TenantContext, day: date, body: dict[str, Any]
) -> dict[str, Any]:
    settings = await _settings(uow, ctx)
    if day > business_date(settings.timezone):
        raise AppError("VALIDATION_FAILED", "A day can only be closed once it has started.")
    s = uow.session
    recorded = await _recorded(uow, ctx, day)
    existing = (
        await s.execute(
            select(DailyClose)
            .where(DailyClose.hotel_id == ctx.hotel_id, DailyClose.business_date == day)
            .with_for_update()
        )
    ).scalar_one_or_none()
    values: dict[str, Any] = {
        "terminal_batch_total_minor": _minor(body.get("terminal_batch_total"), settings.currency),
        "cash_counted_minor": _minor(body.get("cash_counted"), settings.currency),
        "notes": body.get("notes"),
        "card_recorded_minor": recorded["card"],
        "cash_recorded_minor": recorded["cash"],
    }
    if body.get("mark_reviewed"):
        values |= {"reviewed_by": ctx.actor_id, "reviewed_at": datetime.now(UTC)}
    if existing is None:
        await s.execute(insert(DailyClose).values(hotel_id=ctx.hotel_id, business_date=day, **values))
    else:
        await s.execute(
            update(DailyClose)
            .where(DailyClose.hotel_id == ctx.hotel_id, DailyClose.business_date == day)
            .values(**values)
        )
    report = await daily_close(uow, ctx, day)
    await s.execute(
        update(DailyClose)
        .where(DailyClose.hotel_id == ctx.hotel_id, DailyClose.business_date == day)
        .values(flags=report["flags"])
    )
    await write_audit(
        s,
        ctx,
        "daily_close.review" if body.get("mark_reviewed") else "daily_close.update",
        "daily_close",
        None,
        old_value={"terminal_batch_total_minor": existing.terminal_batch_total_minor} if existing else None,
        new_value={
            "date": str(day),
            "terminal_batch_total_minor": values["terminal_batch_total_minor"],
            "cash_counted_minor": values["cash_counted_minor"],
            "flags": report["flags"],
        },
    )
    return report


def _minor(value: dict[str, Any] | None, currency: str) -> int | None:
    if value is None:
        return None
    if value["currency"] != currency:
        raise AppError("AMOUNT_INVALID", "Currency must match the hotel's currency.")
    return int(value["amount_minor"])


# --- Audit log ------------------------------------------------------------------------------


async def audit_logs(
    uow: UnitOfWork,
    ctx: TenantContext,
    *,
    actor_id: uuid.UUID | None,
    action: str | None,
    entity_type: str | None,
    date_from: date | None,
    date_to: date | None,
    after: list[str] | None,
    limit: int,
) -> list[dict[str, Any]]:
    conds = ["a.hotel_id = :h"]
    params: dict[str, Any] = {"h": ctx.hotel_id, "n": limit + 1}
    if actor_id:
        conds.append("a.actor_id = :actor")
        params["actor"] = actor_id
    if action:
        conds.append("a.action = :action")
        params["action"] = action
    if entity_type:
        conds.append("a.entity_type = :et")
        params["et"] = entity_type
    if date_from:
        conds.append("(a.created_at AT TIME ZONE hs.timezone)::date >= :f")
        params["f"] = date_from
    if date_to:
        conds.append("(a.created_at AT TIME ZONE hs.timezone)::date <= :t")
        params["t"] = date_to
    if after:
        conds.append("a.id < :ai")
        params["ai"] = int(after[0])
    rows = await _rows(
        uow,
        "SELECT a.id, a.actor_type, a.actor_id, a.actor_label, a.action, a.entity_type, a.entity_id, "  # noqa: S608 - conditions are fixed strings; values are bound
        "a.old_value, a.new_value, a.reason, host(a.ip) AS ip, a.device_id, a.created_at "
        "FROM app.audit_logs a JOIN app.hotel_settings hs ON hs.hotel_id = a.hotel_id "
        f"WHERE {' AND '.join(conds)} ORDER BY a.id DESC LIMIT :n",
        params,
    )
    return [dict(r) for r in rows]
