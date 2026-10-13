"""The platform's Billing & Invoices dashboard (DECISIONS D79; owner's brief, section 12).

Platform requests carry no hotel, so RLS hides every hotel's billing rows from them; the
cross-hotel figures and lists come from the app.admin_billing_* definer functions, which
return billing records only (no guest data). Collected revenue is money actually received
(test payments shown apart and never counted), invoiced is issued invoices less credit notes,
outstanding is what open invoices still owe, and MRR/ARR are projections from the agreed
prices of current subscriptions; the four are never mixed.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from typing import Any

from sqlalchemy import select, text

from app.billing import providers
from app.core.config import Settings
from app.db.session import UnitOfWork
from app.models.tenancy import BillingSettings, CompanySettings
from app.services.pricing import money


async def summary(uow: UnitOfWork, start: date, end: date) -> dict[str, Any]:
    counts = (
        (
            await uow.session.execute(
                text("SELECT * FROM app.admin_billing_counts(:f, :t)"), {"f": start, "t": end}
            )
        )
        .mappings()
        .one()
    )
    rows = (
        (
            await uow.session.execute(
                text("SELECT * FROM app.admin_billing_summary(:f, :t)"), {"f": start, "t": end}
            )
        )
        .mappings()
        .all()
    )
    plans = (
        (
            await uow.session.execute(
                text("SELECT * FROM app.admin_billing_by_plan(:f, :t)"), {"f": start, "t": end}
            )
        )
        .mappings()
        .all()
    )
    currencies = []
    for r in rows:
        c = str(r["currency"]).strip()
        currencies.append(
            {
                "currency": c,
                "mrr": money(int(r["mrr_minor"]), c),
                "arr": money(int(r["mrr_minor"]) * 12, c),
                "invoiced": money(int(r["invoiced_minor"]), c),
                "credited": money(int(r["credited_minor"]), c),
                "collected": money(int(r["collected_minor"]), c),
                "refunded": money(int(r["refunded_minor"]), c),
                "net_collected": money(int(r["collected_minor"]) - int(r["refunded_minor"]), c),
                "test_collected": money(int(r["test_collected_minor"]), c),
                "outstanding": money(int(r["outstanding_minor"]), c),
                "overdue": money(int(r["overdue_minor"]), c),
                "overdue_invoices": int(r["overdue_invoices"]),
            }
        )
    return {
        "from_": start,
        "to": end,
        **{k: int(v) for k, v in counts.items()},
        "currencies": currencies,
        "by_plan": [
            {
                "plan_code": p["plan_code"],
                "plan_name": p["plan_name"],
                "subscriptions": int(p["subscriptions"]),
                "mrr": money(int(p["mrr_minor"]), str(p["currency"]).strip()),
                "collected": money(int(p["collected_minor"]), str(p["currency"]).strip()),
            }
            for p in plans
        ],
    }


def _blank(v: str | None) -> str | None:
    return v.strip() or None if v else None


async def invoices(
    uow: UnitOfWork,
    *,
    q: str | None,
    status: str | None,
    start: date | None,
    end: date | None,
    plan: str | None,
    payment: str | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    rows = (
        (
            await uow.session.execute(
                text("SELECT * FROM app.admin_billing_invoices(:q, :s, :f, :t, :p, :pay, :l, :o)"),
                {
                    "q": _blank(q),
                    "s": status,
                    "f": start,
                    "t": end,
                    "p": plan,
                    "pay": payment,
                    "l": limit,
                    "o": offset,
                },
            )
        )
        .mappings()
        .all()
    )
    data = []
    for r in rows:
        c = str(r["currency"]).strip()
        data.append(
            {
                **{
                    k: r[k]
                    for k in (
                        "id",
                        "hotel_id",
                        "hotel_name",
                        "kind",
                        "purpose",
                        "number",
                        "status",
                        "issued_at",
                        "due_on",
                        "period_start",
                        "period_end",
                        "plan_code",
                        "is_tax_invoice",
                    )
                },
                "currency": c,
                "total": money(int(r["total_minor"]), c),
                "tax": money(int(r["tax_minor"]), c),
                "paid": money(int(r["paid_minor"]), c),
                "credited": money(int(r["credited_minor"]), c),
                "balance": money(int(r["balance_minor"]), c),
            }
        )
    return {"data": data, "total": int(rows[0]["total_count"]) if rows else 0}


async def payments(
    uow: UnitOfWork,
    *,
    q: str | None,
    reconciliation: str | None,
    start: date | None,
    end: date | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    rows = (
        (
            await uow.session.execute(
                text("SELECT * FROM app.admin_billing_payments(:q, :r, :f, :t, :l, :o)"),
                {"q": _blank(q), "r": reconciliation, "f": start, "t": end, "l": limit, "o": offset},
            )
        )
        .mappings()
        .all()
    )
    data = []
    for r in rows:
        c = str(r["currency"]).strip()
        data.append(
            {
                **{
                    k: r[k]
                    for k in (
                        "id",
                        "hotel_id",
                        "hotel_name",
                        "invoice_id",
                        "invoice_number",
                        "method",
                        "provider",
                        "test_mode",
                        "reference",
                        "provider_payment_id",
                        "received_on",
                        "reconciliation_status",
                        "reconciliation_note",
                        "reconciled_at",
                        "created_at",
                    )
                },
                "amount": money(int(r["amount_minor"]), c),
                "refunded": money(int(r["refunded_minor"]), c),
            }
        )
    return {"data": data, "total": int(rows[0]["total_count"]) if rows else 0}


async def webhooks(uow: UnitOfWork, limit: int) -> list[dict[str, Any]]:
    rows = await uow.session.execute(text("SELECT * FROM app.admin_billing_webhooks(:l)"), {"l": limit})
    return [dict(r) for r in rows.mappings().all()]


async def provider_status(uow: UnitOfWork, settings: Settings) -> dict[str, Any]:
    s = (await uow.session.execute(select(BillingSettings))).scalar_one()
    bank = (await uow.session.execute(select(CompanySettings.bank_details))).scalar_one() or {}
    return {
        **providers.status_report(settings, s.card_provider),
        "eft_enabled": s.eft_enabled,
        "bank_details_set": any(bool(v) for v in bank.values()),
    }


def _amount(m: dict[str, Any]) -> str:
    """A CSV amount in major units with a plain dot, e.g. 1234.50 (spreadsheet friendly)."""
    return providers.major(int(m["amount_minor"]), str(m["currency"]))


def _safe(v: Any) -> str:
    """CSV cells never start with = + - @ (formula injection in spreadsheets)."""
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s


def invoices_csv(rows: list[dict[str, Any]]) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(
        [
            "number",
            "kind",
            "status",
            "hotel",
            "hotel_id",
            "plan",
            "issued_at",
            "due_on",
            "period_start",
            "period_end",
            "currency",
            "total",
            "tax",
            "paid",
            "credited",
            "balance",
            "tax_invoice",
        ]
    )
    for r in rows:
        w.writerow(
            [
                _safe(x)
                for x in (
                    r["number"],
                    r["kind"],
                    r["status"],
                    r["hotel_name"],
                    r["hotel_id"],
                    r["plan_code"],
                    r["issued_at"].isoformat() if r["issued_at"] else "",
                    r["due_on"] or "",
                    r["period_start"] or "",
                    r["period_end"] or "",
                    r["currency"],
                    _amount(r["total"]),
                    _amount(r["tax"]),
                    _amount(r["paid"]),
                    _amount(r["credited"]),
                    _amount(r["balance"]),
                    "yes" if r["is_tax_invoice"] else "no",
                )
            ]
        )
    return out.getvalue()


def payments_csv(rows: list[dict[str, Any]]) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(
        [
            "received_on",
            "hotel",
            "hotel_id",
            "invoice",
            "method",
            "provider",
            "test",
            "currency",
            "amount",
            "refunded",
            "reference",
            "provider_payment_id",
            "reconciliation",
            "reconciliation_note",
        ]
    )
    for r in rows:
        w.writerow(
            [
                _safe(x)
                for x in (
                    r["received_on"],
                    r["hotel_name"],
                    r["hotel_id"],
                    r["invoice_number"],
                    r["method"],
                    r["provider"],
                    "yes" if r["test_mode"] else "no",
                    r["amount"]["currency"],
                    _amount(r["amount"]),
                    _amount(r["refunded"]),
                    r["reference"],
                    r["provider_payment_id"],
                    r["reconciliation_status"],
                    r["reconciliation_note"],
                )
            ]
        )
    return out.getvalue()
