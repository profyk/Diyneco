"""The daily close email (security spec: "emailed to Finance and the GM at 06:00 hotel time").

Run by the worker. For each active hotel whose local time is past 06:00, yesterday's daily
close is computed from folio entries and payments and emailed once to the hotel's active
Finance Managers and General Managers. The notification log is the record that it was sent.
"""

from __future__ import annotations

import logging
import zoneinfo
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.notifications.email import Mailer
from app.services import reports

log = logging.getLogger("diyneco.jobs")

SEND_FROM_HOUR = 6
RECIPIENTS_SQL = text(
    "SELECT DISTINCT u.email FROM app.hotel_users hu JOIN app.users u ON u.id = hu.user_id "
    "JOIN app.user_roles ur ON ur.hotel_user_id = hu.id JOIN app.roles r ON r.id = ur.role_id "
    "WHERE hu.hotel_id = :h AND hu.status = 'active' AND u.status = 'active' "
    "AND r.hotel_id IS NULL AND r.code IN ('finance_manager', 'general_manager')"
)


def _amount(m: dict[str, Any]) -> str:
    minor = int(m["amount_minor"])
    sign = "-" if minor < 0 else ""
    whole, cents = divmod(abs(minor), 100)
    return (
        f"{sign}R {whole:,}.{cents:02d}"
        if m["currency"] == "ZAR"
        else f"{sign}{m['currency']} {whole:,}.{cents:02d}"
    )


def render(name: str, report: dict[str, Any]) -> str:
    rev, pay = report["revenue"], report["payments"]
    lines = [
        f"Daily close for {name}, {report['date']:%A %d %B %Y}",
        "",
        f"Revenue (VAT inclusive): {_amount(rev['revenue'])}",
        f"  Accommodation {_amount(rev['accommodation'])}, food and beverage {_amount(rev['fnb'])}, "
        f"other {_amount(rev['other'])}",
        f"  Discounts {_amount(rev['discounts'])}, adjustments {_amount(rev['adjustments'])}",
        f"Tips (not revenue): {_amount(rev['tips'])}",
        "",
        "Payments:",
        *[
            f"  {m['method'].replace('_', ' ')}: {m['count']} for {_amount(m['amount'])}"
            for m in pay["by_method"]
        ],
        f"Card payments recorded: {_amount(report['card']['recorded'])} "
        "(enter the terminal batch total in Reports > Daily close)",
        f"Cash recorded: {_amount(report['cash']['recorded'])}",
        "",
        f"Adjustments: {len(report['adjustments'])}, discounts: {len(report['discounts'])}, "
        f"checkout overrides: {len(report['overrides'])}, late entries: {len(report['late_entries'])}",
    ]
    if report["flags"]:
        lines += ["", "Needs attention: " + ", ".join(f.replace("_", " ") for f in report["flags"])]
    return "\n".join(lines) + "\n"


async def send_daily_closes(
    sessionmaker: async_sessionmaker[AsyncSession], mailer: Mailer, now: datetime | None = None
) -> int:
    now = now or datetime.now(UTC)
    async with sessionmaker() as s, s.begin():
        hotels = (await s.execute(text("SELECT * FROM app.hotels_for_jobs()"))).all()
    sent = 0
    for hotel_id, timezone in hotels:
        local = now.astimezone(zoneinfo.ZoneInfo(timezone))
        if local.hour < SEND_FROM_HOUR:
            continue
        day = local.date() - timedelta(days=1)
        try:
            sent += await _send_one(sessionmaker, mailer, hotel_id, day)
        except Exception:
            log.exception("daily close email failed", extra={"hotel_id": str(hotel_id)})
    return sent


async def _send_one(
    sessionmaker: async_sessionmaker[AsyncSession], mailer: Mailer, hotel_id: Any, day: Any
) -> int:
    async with sessionmaker() as s:
        uow = UnitOfWork(session=s, sessionmaker=sessionmaker)
        async with s.begin():
            await set_tenant(s, hotel_id)
            done = (
                await s.execute(
                    text(
                        "SELECT 1 FROM app.notifications WHERE hotel_id = :h AND template = 'daily_close' "
                        "AND subject_ref->>'date' = :d LIMIT 1"
                    ),
                    {"h": hotel_id, "d": str(day)},
                )
            ).first()
            if done is not None:
                return 0
            recipients = [str(e) for e in (await s.execute(RECIPIENTS_SQL, {"h": hotel_id})).scalars()]
            if not recipients:
                return 0
            ctx = TenantContext(
                hotel_id=hotel_id, actor_type="system", actor_id=None, actor_label="Daily close"
            )
            report = await reports.daily_close(uow, ctx, day)
            name = (
                await s.execute(text("SELECT name FROM app.hotels WHERE id = :h"), {"h": hotel_id})
            ).scalar_one()
            body = render(name, report)
            for email in recipients:
                await mailer.queue(
                    uow,
                    hotel_id=hotel_id,
                    template="daily_close",
                    to=email,
                    subject=f"{name}: daily close for {day:%d %b %Y}",
                    body=body,
                    subject_ref={"date": str(day)},
                )
        await uow.run_after_commit()
    return len(recipients)
