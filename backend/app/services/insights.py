"""Platform insights for the admin panel (DECISIONS D87): adoption, activation, conversion,
churn, cohorts, where hotels are and what they are, owners, and staff activity.

Built from the aggregate-only functions of migration 0035 (never guest data). Money is kept
per currency and never added across currencies. A hotel is "activated" once it has a room,
a set-up device and a first order: the point where Diyneco is in daily use.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import text

from app.core.countries import country as country_of
from app.db.session import UnitOfWork
from app.services.pricing import money

PAYING = ("active", "past_due", "cancellation_scheduled")
MONTHS = {"month": 1, "quarter": 3, "year": 12}


def monthly_minor(amount_minor: int | None, interval: str | None) -> int:
    """The monthly equivalent of a price (MRR): a year's price over 12, a quarter's over 3."""
    if not amount_minor or not interval:
        return 0
    return int(amount_minor) // MONTHS.get(interval, 1)


_QUERIES = {
    fn: text(f"SELECT * FROM app.{fn}")  # noqa: S608 - fixed function names, no input
    for fn in (
        "admin_hotel_facts()",
        "admin_owner_facts()",
        "admin_subscription_history()",
        "admin_user_activity()",
    )
}


async def _rows(uow: UnitOfWork, fn: str) -> list[dict[str, Any]]:
    return [dict(r) for r in (await uow.session.execute(_QUERIES[fn])).mappings()]


def _country_name(code: str) -> str:
    c = country_of(code)
    return c.name if c else code


async def hotel_facts(uow: UnitOfWork) -> list[dict[str, Any]]:
    out = []
    for r in await _rows(uow, "admin_hotel_facts()"):
        country = str(r["country"]).strip()
        currency = str(r["currency"]).strip()
        sub_currency = str(r["sub_currency"]).strip() if r["sub_currency"] else None
        paying = r["sub_status"] in PAYING and r["plan_code"] is not None
        activated = int(r["rooms"]) > 0 and int(r["devices"]) > 0 and r["first_order_at"] is not None
        out.append(
            {
                **r,
                "country": country,
                "currency": currency,
                "sub_currency": sub_currency,
                "paying": paying,
                "activated": activated,
                "mrr_minor": monthly_minor(r["sub_amount_minor"], r["sub_interval"]) if paying else 0,
                "rooms": int(r["rooms"]),
                "staff": int(r["staff"]),
                "devices": int(r["devices"]),
                "orders_30d": int(r["orders_30d"]),
                "gmv_30d_minor": int(r["gmv_30d_minor"]),
            }
        )
    return out


def _money_by_currency(rows: list[dict[str, Any]], amount: str, currency: str) -> list[dict[str, Any]]:
    totals: dict[str, int] = defaultdict(int)
    for r in rows:
        if r[currency] and r[amount]:
            totals[r[currency]] += int(r[amount])
    return [money(v, c) for c, v in sorted(totals.items())]


def _group(rows: list[dict[str, Any]], key: Any, label: Any) -> list[dict[str, Any]]:
    groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)
    out = []
    for k, items in groups.items():
        out.append(
            {
                "key": k,
                "label": label(k, items),
                "hotels": len(items),
                "active": sum(1 for r in items if r["status"] == "active"),
                "activated": sum(1 for r in items if r["activated"]),
                "paying": sum(1 for r in items if r["paying"]),
                "trials": sum(1 for r in items if r["sub_status"] == "trial"),
                "rooms": sum(r["rooms"] for r in items),
                "orders_30d": sum(r["orders_30d"] for r in items),
                "mrr": _money_by_currency(items, "mrr_minor", "sub_currency"),
                "gmv_30d": _money_by_currency(items, "gmv_30d_minor", "currency"),
            }
        )
    return sorted(out, key=lambda g: (-g["hotels"], str(g["label"])))


def _pct_bp(part: int, whole: int) -> int:
    return part * 10000 // whole if whole else 0


async def overview(uow: UnitOfWork, since: date, until: date) -> dict[str, Any]:
    facts = await hotel_facts(uow)
    subs = await _rows(uow, "admin_subscription_history()")
    owners = await _rows(uow, "admin_owner_facts()")
    activity = await _rows(uow, "admin_user_activity()")

    def signed(r: dict[str, Any]) -> date:
        day: date = r["created_at"].astimezone(UTC).date()
        return day

    new = [r for r in facts if since <= signed(r) <= until]

    # Signups per day over the period.
    per_day: dict[date, int] = defaultdict(int)
    for r in new:
        per_day[signed(r)] += 1
    days = [
        {"day": since + timedelta(days=i), "signups": per_day.get(since + timedelta(days=i), 0)}
        for i in range((until - since).days + 1)
    ]

    # Activation funnel for the period's signups.
    funnel = [
        {"step": "signed_up", "label": "Signed up", "hotels": len(new)},
        {
            "step": "email_confirmed",
            "label": "Owner confirmed email",
            "hotels": sum(r["owner_verified"] for r in new),
        },
        {"step": "approved", "label": "Approved", "hotels": sum(r["status"] == "active" for r in new)},
        {"step": "rooms", "label": "Added rooms", "hotels": sum(r["rooms"] > 0 for r in new)},
        {"step": "devices", "label": "Set up a device", "hotels": sum(r["devices"] > 0 for r in new)},
        {
            "step": "first_order",
            "label": "Took a first order",
            "hotels": sum(r["first_order_at"] is not None for r in new),
        },
        {"step": "paying", "label": "Paying", "hotels": sum(r["paying"] for r in new)},
    ]

    # Subscriptions: conversion, churn, new and lost MRR in the period.
    by_hotel: dict[uuid.UUID, list[dict[str, Any]]] = defaultdict(list)
    for s in subs:
        by_hotel[s["hotel_id"]].append(s)
    trials_ended = converted = 0
    for items in by_hotel.values():
        for t in (s for s in items if not s["paid"] and s["trial_ends_on"]):
            if since <= t["trial_ends_on"] <= until or (t["ended_on"] and since <= t["ended_on"] <= until):
                trials_ended += 1
                if any(s["paid"] and s["starts_on"] >= t["starts_on"] for s in items):
                    converted += 1
    paid = [s for s in subs if s["paid"]]
    paying_at_start = [
        s for s in paid if s["starts_on"] <= since and (s["ended_on"] is None or s["ended_on"] > since)
    ]
    churned = [
        s
        for s in paid
        if s["status"] in ("cancelled", "expired") and s["ended_on"] and since <= s["ended_on"] <= until
    ]
    started = [s for s in paid if since <= s["starts_on"] <= until]

    def mrr_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return _money_by_currency(
            [
                {
                    "m": monthly_minor(s["amount_minor"], s["sub_interval"]),
                    "c": (s["currency"] or "").strip() or None,
                }
                for s in rows
            ],
            "m",
            "c",
        )

    # Cohorts: hotels by signup month (last 12 months), and where they are now.
    cohorts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    y, m = until.year, until.month - 11
    if m <= 0:
        y, m = y - 1, m + 12
    first_month = date(y, m, 1)
    for r in facts:
        d = signed(r)
        if d >= first_month:
            cohorts[f"{d.year}-{d.month:02d}"].append(r)
    cohort_rows = [
        {
            "month": m,
            "signups": len(items),
            "activated": sum(r["activated"] for r in items),
            "in_use_30d": sum(r["orders_30d"] > 0 for r in items),
            "paying": sum(r["paying"] for r in items),
            "closed": sum(r["status"] == "closed" for r in items),
        }
        for m, items in sorted(cohorts.items())
    ]

    multi = [o for o in owners if len(o["hotel_ids"] or []) > 1]
    return {
        "since": since,
        "until": until,
        "totals": {
            "hotels": len(facts),
            "active": sum(r["status"] == "active" for r in facts),
            "pending_approval": sum(r["status"] == "pending_approval" for r in facts),
            "suspended": sum(r["status"] == "suspended" for r in facts),
            "activated": sum(r["activated"] for r in facts),
            "in_use_30d": sum(r["orders_30d"] > 0 for r in facts),
            "paying": sum(r["paying"] for r in facts),
            "trials": sum(r["sub_status"] == "trial" for r in facts),
            "no_plan": sum(r["sub_status"] is None for r in facts),
            "rooms": sum(r["rooms"] for r in facts),
            "owners": len(owners),
            "multi_property_owners": len(multi),
            "mrr": _money_by_currency(facts, "mrr_minor", "sub_currency"),
            "gmv_30d": _money_by_currency(facts, "gmv_30d_minor", "currency"),
        },
        "period": {
            "signups": len(new),
            "activation_bp": _pct_bp(sum(r["activated"] for r in new), len(new)),
            "trials_ended": trials_ended,
            "trials_converted": converted,
            "trial_conversion_bp": _pct_bp(converted, trials_ended),
            "paying_at_start": len(paying_at_start),
            "churned": len(churned),
            "churn_bp": _pct_bp(len(churned), len(paying_at_start)),
            "new_mrr": mrr_rows(started),
            "churned_mrr": mrr_rows(churned),
        },
        "days": days,
        "funnel": funnel,
        "cohorts": cohort_rows,
        "by_country": _group(facts, lambda r: r["country"], lambda k, _: _country_name(k)),
        "by_region": _group(
            facts,
            lambda r: f"{r['country']}|{r['province_code'] or r['province'] or ''}",
            lambda k, items: f"{items[0]['province'] or 'Region not set'}, {items[0]['country']}",
        ),
        "by_property_type": _group(facts, lambda r: r["property_type"] or "unknown", lambda k, _: k),
        "users": sorted(
            (
                {
                    "role": r["role_code"],
                    "members": int(r["members"]),
                    "active_7d": int(r["active_7d"]),
                    "active_30d": int(r["active_30d"]),
                }
                for r in activity
            ),
            key=lambda r: -r["members"],
        ),
    }


async def owners(uow: UnitOfWork) -> list[dict[str, Any]]:
    """Every Hotel Owner with their properties, rooms, MRR and money processed."""
    facts = {r["id"]: r for r in await hotel_facts(uow)}
    out = []
    for o in await _rows(uow, "admin_owner_facts()"):
        hotels = [facts[h] for h in (o["hotel_ids"] or []) if h in facts]
        out.append(
            {
                "user_id": o["user_id"],
                "name": o["name"],
                "email": o["email"],
                "phone": o["phone"],
                "created_at": o["created_at"],
                "last_login_at": o["last_login_at"],
                "email_verified": o["email_verified"],
                "countries": sorted({h["country"] for h in hotels}),
                "rooms": sum(h["rooms"] for h in hotels),
                "paying": sum(h["paying"] for h in hotels),
                "mrr": _money_by_currency(hotels, "mrr_minor", "sub_currency"),
                "gmv_30d": _money_by_currency(hotels, "gmv_30d_minor", "currency"),
                "hotels": [
                    {
                        "id": h["id"],
                        "name": h["name"],
                        "code": h["code"],
                        "status": h["status"],
                        "country": h["country"],
                        "city": h["city"],
                        "province": h["province"],
                        "property_type": h["property_type"],
                        "rooms": h["rooms"],
                        "subscription_status": h["sub_status"],
                        "plan_name": h["plan_name"],
                    }
                    for h in hotels
                ],
            }
        )
    return sorted(out, key=lambda o: (-len(o["hotels"]), o["name"].lower()))


def default_period(since: date | None, until: date | None) -> tuple[date, date]:
    end = until or datetime.now(UTC).date()
    return since or end - timedelta(days=29), end
