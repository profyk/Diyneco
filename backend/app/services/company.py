"""Diyneco's company billing settings and tax rates (DECISIONS D72).

The company is the seller on every subscription invoice. Its details start mostly empty and
are filled in only with verified information; every change needs a reason and is audited
with the previous and new values. VAT is charged only while the company is VAT-registered,
from its registration date, at the standard rate in force on the invoice date. Tax rates are
effective-dated rows: a change is a new row, a rate already in force is never altered, and a
scheduled rate can be withdrawn before it starts. Issued invoices keep their own copy of all of
this (later slices), so nothing here changes them.
"""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import delete, insert, select

from app.audit.writer import write_platform_audit
from app.core.countries import country as country_info
from app.core.countries import tax_id_ok
from app.core.errors import AppError
from app.core.state import AppState
from app.db.session import UnitOfWork
from app.integrations.storage import platform_key
from app.models.tenancy import CompanySettings, TaxRate

LOGO_TYPES = {"image/png": "png", "image/jpeg": "jpg"}
LOGO_MAX_BYTES = 1024 * 1024
# CIPC company registration numbers: 2026/123456/07.
ZA_REGISTRATION = re.compile(r"^\d{4}/\d{6}/\d{2}$")
EDITABLE = (
    "legal_name",
    "trading_name",
    "registration_number",
    "registered_address",
    "business_address",
    "billing_email",
    "billing_phone",
    "vat_registered",
    "vat_number",
    "vat_effective_date",
    "invoice_prefix",
    "credit_note_prefix",
    "number_padding",
    "number_reset",
    "payment_terms_days",
    "bank_details",
    "payment_instructions",
)


def _field(field: str, problem: str) -> AppError:
    return AppError(
        "VALIDATION_FAILED",
        problem,
        details={"fields": [{"field": field, "problem": problem, "type": "value_error"}]},
    )


def today_in(tz: str) -> date:
    return datetime.now(ZoneInfo(tz)).date()


async def _settings(uow: UnitOfWork, lock: bool = False) -> CompanySettings:
    q = select(CompanySettings)
    return (await uow.session.execute(q.with_for_update() if lock else q)).scalar_one()


async def company_row(uow: UnitOfWork) -> CompanySettings:
    return await _settings(uow)


async def rate_on(uow: UnitOfWork, country: str, on: date) -> TaxRate | None:
    """The standard rate in force in a country on a day."""
    return (
        await uow.session.execute(
            select(TaxRate)
            .where(TaxRate.country == country, TaxRate.category == "standard", TaxRate.effective_from <= on)
            .order_by(TaxRate.effective_from.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def tax_on(uow: UnitOfWork, on: date, settings: CompanySettings | None = None) -> dict[str, Any]:
    """Whether an invoice dated `on` carries tax, and at what rate. Not registered (or before
    the registration date) means no tax and a plain invoice, never a tax invoice."""
    s = settings or await _settings(uow)
    if not s.vat_registered or s.vat_effective_date is None or on < s.vat_effective_date:
        return {"charged": False, "tax_name": None, "rate_bp": None}
    rate = await rate_on(uow, s.country, on)
    if rate is None:
        return {"charged": False, "tax_name": None, "rate_bp": None}
    return {"charged": True, "tax_name": rate.tax_name, "rate_bp": rate.rate_bp}


def _missing(s: CompanySettings) -> list[str]:
    """What an invoice would lack: shown in the admin panel, never filled in for them."""
    out = []
    if not s.registration_number:
        out.append("registration_number")
    if not (s.registered_address or {}).get("line1"):
        out.append("registered_address")
    if not s.billing_email:
        out.append("billing_email")
    if not (s.bank_details or {}).get("account_number") and not s.payment_instructions:
        out.append("payment_instructions")
    return out


async def view(st: AppState, uow: UnitOfWork) -> dict[str, Any]:
    s = await _settings(uow)
    tax = await tax_on(uow, today_in(s.timezone), s)
    logo_url = (
        await st.storage.signed_download(st.settings.storage_bucket_assets, s.logo_path)
        if s.logo_path
        else None
    )
    example = f"{s.invoice_prefix}-{'1'.zfill(s.number_padding)}"
    if s.number_reset == "yearly":
        example = f"{s.invoice_prefix}-{today_in(s.timezone).year}-{'1'.zfill(s.number_padding)}"
    return {
        **{k: getattr(s, k) for k in EDITABLE},
        "country": s.country,
        "currency": s.currency,
        "timezone": s.timezone,
        "logo_url": logo_url,
        "version": s.version,
        "updated_at": s.updated_at,
        "invoice_example": ("Tax invoice " if tax["charged"] else "Invoice ") + example,
        "tax_today": tax,
        "missing": _missing(s),
    }


def _mask(values: dict[str, Any]) -> dict[str, Any]:
    """Audit entries keep bank account numbers to their last four digits."""
    bank = values.get("bank_details")
    if isinstance(bank, dict) and bank.get("account_number"):
        values = {
            **values,
            "bank_details": {**bank, "account_number": "…" + str(bank["account_number"])[-4:]},
        }
    return values


async def update(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], body: dict[str, Any]
) -> dict[str, Any]:
    s = await _settings(uow, lock=True)
    if body["version"] != s.version:
        raise AppError("PRECONDITION_FAILED")
    new = {k: body.get(k) for k in EDITABLE}
    new["registered_address"] = {k: v for k, v in (new["registered_address"] or {}).items() if v}
    new["business_address"] = {k: v for k, v in (new["business_address"] or {}).items() if v}
    new["bank_details"] = {k: v for k, v in (new["bank_details"] or {}).items() if v}
    for k in ("registration_number", "vat_number", "billing_phone", "payment_instructions"):
        new[k] = new[k] or None
    new["billing_email"] = str(new["billing_email"]) if new["billing_email"] else None

    if (
        new["registration_number"]
        and s.country == "ZA"
        and not ZA_REGISTRATION.match(new["registration_number"])
    ):
        raise _field("registration_number", "Use the CIPC format, for example 2026/123456/07.")
    if new["invoice_prefix"] == new["credit_note_prefix"]:
        raise _field("credit_note_prefix", "Credit notes need a prefix different from invoices.")
    if new["vat_number"] and not tax_id_ok(s.country, new["vat_number"]):
        place = country_info(s.country)
        label = place.tax_id_label if place else "VAT number"
        raise _field("vat_number", f"This is not a valid {label}.")
    if new["vat_registered"]:
        # A registered company must be able to issue valid tax invoices from its effective date.
        if not new["vat_number"]:
            raise _field("vat_number", "A VAT-registered company needs its VAT number.")
        if new["vat_effective_date"] is None:
            raise _field("vat_effective_date", "Enter the date the VAT registration takes effect.")
        if not new["registration_number"] or not (new["registered_address"] or {}).get("line1"):
            raise _field("vat_registered", "Enter the registration number and registered address first.")
        if await rate_on(uow, s.country, new["vat_effective_date"]) is None:
            raise _field("vat_effective_date", "No standard tax rate is in force on that date.")

    before = {k: getattr(s, k) for k in EDITABLE}
    changed = [k for k in EDITABLE if before[k] != new[k]]
    if not changed:
        raise AppError("VALIDATION_FAILED", "Nothing changed.")
    for k in changed:
        setattr(s, k, new[k])
    s.version += 1
    s.updated_by = actor["actor_id"]
    sensitive = {"vat_registered", "vat_number", "vat_effective_date", "legal_name", "registration_number"}
    await write_platform_audit(
        uow.session,
        **actor,
        action="platform.company_tax_changed" if sensitive & set(changed) else "platform.company_changed",
        entity_type="company_settings",
        entity_id=None,
        new_value={
            "reason": body["reason"],
            "from": _mask({k: _plain(before[k]) for k in changed}),
            "to": _mask({k: _plain(new[k]) for k in changed}),
        },
    )
    await uow.session.flush()
    return await view(st, uow)


def _plain(v: Any) -> Any:
    return v.isoformat() if isinstance(v, date) else v


async def start_logo_upload(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], content_type: str, size_bytes: int
) -> dict[str, Any]:
    if content_type not in LOGO_TYPES:
        raise _field("content_type", "Upload a PNG or JPEG file (invoices print it).")
    if size_bytes > LOGO_MAX_BYTES:
        raise _field("size_bytes", "The logo must be 1 MB or smaller.")
    s = await _settings(uow, lock=True)
    key = platform_key("company", "logo", f"{uuid.uuid4()}.{LOGO_TYPES[content_type]}")
    upload = await st.storage.signed_upload(
        st.settings.storage_bucket_assets, key, content_type, LOGO_MAX_BYTES
    )
    before = s.logo_path
    s.logo_path = key
    s.version += 1
    s.updated_by = actor["actor_id"]
    await write_platform_audit(
        uow.session,
        **actor,
        action="platform.company_logo",
        entity_type="company_settings",
        entity_id=None,
        new_value={"from": before, "to": key},
    )
    return {
        "upload_url": upload.url,
        "method": upload.method,
        "headers": upload.headers,
        "expires_at": upload.expires_at,
        "max_bytes": LOGO_MAX_BYTES,
    }


# --- Tax rates -----------------------------------------------------------------------------


async def tax_rates(uow: UnitOfWork) -> list[dict[str, Any]]:
    s = await _settings(uow)
    today = today_in(s.timezone)
    rows = (
        (
            await uow.session.execute(
                select(TaxRate).order_by(TaxRate.country, TaxRate.category, TaxRate.effective_from)
            )
        )
        .scalars()
        .all()
    )
    in_force: dict[tuple[str, str], uuid.UUID] = {}
    for r in rows:
        if r.effective_from <= today:
            in_force[(r.country, r.category)] = r.id
    return [
        {
            **{
                c: getattr(r, c)
                for c in (
                    "id",
                    "country",
                    "tax_name",
                    "category",
                    "rate_bp",
                    "effective_from",
                    "reason",
                    "created_at",
                )
            },
            "in_force": in_force.get((r.country, r.category)) == r.id,
            "scheduled": r.effective_from > today,
        }
        for r in rows
    ]


async def schedule_rate(uow: UnitOfWork, actor: dict[str, Any], body: dict[str, Any]) -> list[dict[str, Any]]:
    """A new standard rate from a date. Only future dates: a rate already in force (and the
    invoices issued under it) is never rewritten."""
    s = await _settings(uow)
    if body["effective_from"] <= today_in(s.timezone):
        raise _field("effective_from", "A new rate can start tomorrow at the earliest.")
    if country_info(body["country"]) is None:
        raise _field("country", "Unknown country.")
    exists = (
        await uow.session.execute(
            select(TaxRate.id).where(
                TaxRate.country == body["country"],
                TaxRate.category == "standard",
                TaxRate.effective_from == body["effective_from"],
            )
        )
    ).first()
    if exists is not None:
        raise AppError("INVALID_TRANSITION", "A rate already starts on that date. Withdraw it first.")
    rate_id = (
        await uow.session.execute(
            insert(TaxRate)
            .values(
                country=body["country"],
                tax_name=body["tax_name"],
                category="standard",
                rate_bp=body["rate_bp"],
                effective_from=body["effective_from"],
                reason=body["reason"],
                created_by=actor["actor_id"],
            )
            .returning(TaxRate.id)
        )
    ).scalar_one()
    await write_platform_audit(
        uow.session,
        **actor,
        action="platform.tax_rate_scheduled",
        entity_type="tax_rate",
        entity_id=rate_id,
        new_value={
            "country": body["country"],
            "rate_bp": body["rate_bp"],
            "effective_from": body["effective_from"].isoformat(),
            "reason": body["reason"],
        },
    )
    return await tax_rates(uow)


async def withdraw_rate(uow: UnitOfWork, actor: dict[str, Any], rate_id: uuid.UUID) -> list[dict[str, Any]]:
    s = await _settings(uow)
    row = (await uow.session.execute(select(TaxRate).where(TaxRate.id == rate_id))).scalar_one_or_none()
    if row is None:
        raise AppError("NOT_FOUND")
    if row.effective_from <= today_in(s.timezone):
        raise AppError(
            "INVALID_TRANSITION", "A rate already in force cannot be withdrawn; schedule a new one."
        )
    await uow.session.execute(delete(TaxRate).where(TaxRate.id == rate_id))
    await write_platform_audit(
        uow.session,
        **actor,
        action="platform.tax_rate_withdrawn",
        entity_type="tax_rate",
        entity_id=rate_id,
        new_value={
            "country": row.country,
            "rate_bp": row.rate_bp,
            "effective_from": row.effective_from.isoformat(),
        },
    )
    return await tax_rates(uow)
