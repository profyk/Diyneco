"""Checkout, invoices and credit notes (API spec, Folios, payments, checkout and invoices;
security spec, VAT, invoicing and record retention).

Checkout closes the folio, issues the bill and resets the room's tablet in one transaction.
The bill is numbered from a gap-free per-hotel, per-year sequence whose row is locked for the
rest of the transaction, so a rolled-back checkout never uses up a number. Supplier and
recipient details are copied into the invoice, and its PDF is rendered and stored before the
row is written, because invoices are append-only.

A credit note cancels a whole invoice and re-opens the folio for corrections; the next
checkout of that stay issues a new invoice (D44).
"""

from __future__ import annotations

import hashlib
import uuid
import zoneinfo
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert, select, text, update

from app.audit.writer import write_audit
from app.billing import invoice_pdf
from app.billing.folio import business_date
from app.core.errors import AppError
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork
from app.integrations.storage import hotel_key
from app.models.domain import (
    BillingProfile,
    Folio,
    Guest,
    Invoice,
    InvoiceItem,
    Order,
    Stay,
)
from app.realtime.outbox import emit, hotel_channel
from app.repositories.hotels import HotelRepository
from app.repositories.rooms import RoomRepository
from app.repositories.stays import StayRepository
from app.services import billing, devices
from app.services.pricing import money

FINISHED_ORDERS = ("CLOSED", "CANCELLED", "DECLINED")
LONG_STAY_NIGHTS = 28
REVENUE_TYPES = ("charge", "discount", "adjustment", "reversal")
KIND_TITLES = {
    "tax_invoice": "Tax Invoice",
    "abridged_tax_invoice": "Tax Invoice",
    "guest_statement": "Guest Statement",
    "credit_note": "Credit Note",
}


async def _open_orders(uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = (
        await uow.session.execute(
            select(Order.id, Order.number, Order.status)
            .where(
                Order.hotel_id == ctx.hotel_id, Order.stay_id == stay_id, Order.status.not_in(FINISHED_ORDERS)
            )
            .order_by(Order.number)
        )
    ).all()
    return [{"id": str(r.id), "number": r.number, "status": r.status} for r in rows]


def _charges_total(totals: dict[str, Any]) -> int:
    return sum(int(totals[k]["amount_minor"]) for k in ("accommodation", "fnb", "other"))


def _kind(settings: Any, charges_minor: int) -> str:
    if not settings.vat_registered:
        return "guest_statement"
    return "abridged_tax_invoice" if charges_minor <= settings.abridged_invoice_max_minor else "tax_invoice"


def _flags(stay: Stay) -> list[str]:
    nights = (stay.departure_date - stay.arrival_date).days
    # Security spec: VAT on commercial accommodation over 28 days differs; the hotel confirms it.
    return ["long_stay"] if nights > LONG_STAY_NIGHTS else []


async def summary(uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID) -> dict[str, Any]:
    stay, folio = await billing.stay_and_folio(uow, ctx, stay_id)
    view = await billing.view(uow, ctx, stay_id)
    settings = await billing._settings(uow, ctx)
    open_orders = await _open_orders(uow, ctx, stay.id)
    balance = int(view["totals"]["balance"]["amount_minor"])
    return {
        "stay_id": stay.id,
        "stay_status": stay.status,
        "folio_status": folio.status,
        "totals": view["totals"],
        "by_category": view["by_category"],
        "open_orders": open_orders,
        "can_check_out": folio.status == "open" and not open_orders and balance <= 0,
        "override_allowed": settings.checkout_override_allowed,
        "invoice_kind": _kind(settings, _charges_total(view["totals"])),
        "flags": _flags(stay),
    }


# --- Invoices -------------------------------------------------------------------------------


async def _next_number(uow: UnitOfWork, ctx: TenantContext, prefix: str, year: int) -> str:
    s = uow.session
    await s.execute(
        text(
            "INSERT INTO app.invoice_sequences (hotel_id, year, next_number) VALUES (:h, :y, 1) "
            "ON CONFLICT DO NOTHING"
        ),
        {"h": ctx.hotel_id, "y": year},
    )
    n = (
        await s.execute(
            text(
                "SELECT next_number FROM app.invoice_sequences WHERE hotel_id = :h AND year = :y FOR UPDATE"
            ),
            {"h": ctx.hotel_id, "y": year},
        )
    ).scalar_one()
    await s.execute(
        text(
            "UPDATE app.invoice_sequences SET next_number = next_number + 1 WHERE hotel_id = :h AND year = :y"
        ),
        {"h": ctx.hotel_id, "y": year},
    )
    return f"{prefix}-{year}-{int(n):06d}"


def _address(value: dict[str, Any] | None) -> dict[str, Any]:
    return {k: v for k, v in (value or {}).items() if v}


async def _supplier(uow: UnitOfWork, ctx: TenantContext, settings: Any) -> dict[str, Any]:
    hotel = await HotelRepository(uow.session, ctx).get()
    if hotel is None:
        raise AppError("NOT_FOUND")
    return {
        "name": hotel.legal_name or hotel.name,
        "trading_name": hotel.name,
        "address": _address(hotel.address),
        "vat_number": settings.vat_number if settings.vat_registered else None,
        "phone": hotel.phone,
        "email": hotel.email,
    }


async def _recipient(
    uow: UnitOfWork, ctx: TenantContext, stay: Stay, kind: str, address: dict[str, Any] | None
) -> dict[str, Any]:
    s = uow.session
    guest = (
        await s.execute(select(Guest).where(Guest.hotel_id == ctx.hotel_id, Guest.id == stay.guest_id))
    ).scalar_one()
    if stay.billing_type == "company" and stay.billing_profile_id is not None:
        profile = (
            await s.execute(
                select(BillingProfile).where(
                    BillingProfile.hotel_id == ctx.hotel_id, BillingProfile.id == stay.billing_profile_id
                )
            )
        ).scalar_one()
        recipient: dict[str, Any] = {
            "type": "company",
            "name": profile.company_name,
            "registration_number": profile.registration_number,
            "vat_number": profile.vat_number,
            "address": _address(address) or _address(profile.billing_address),
            "email": profile.billing_email,
            "purchase_order": stay.purchase_order,
            "traveller": stay.traveller_name or guest.full_name,
        }
    else:
        recipient = {"type": "personal", "name": guest.full_name, "address": _address(address)}
    # A full tax invoice needs the recipient's address (security spec, VAT); it is asked at
    # checkout and copied into the invoice only (D43).
    if kind == "tax_invoice" and not recipient["address"].get("line1"):
        raise AppError(
            "VALIDATION_FAILED",
            "A full tax invoice needs the recipient's address. Add it to the checkout.",
            details={"reason": "recipient_address_required"},
        )
    return recipient


async def _items(uow: UnitOfWork, ctx: TenantContext, folio_id: uuid.UUID) -> list[dict[str, Any]]:
    """Revenue lines of the bill. A charge that was reversed and its reversal cancel out and are
    left off; tips and payments appear in the totals, not as supplies."""
    rows = await billing.entries_with_groups(uow, ctx, folio_id)
    reversed_ids = {e.reverses_entry_id for e, _ in rows if e.reverses_entry_id is not None}
    items = []
    for e, cat in rows:
        if cat.revenue_group in ("tip", "payment") or e.entry_type not in REVENUE_TYPES:
            continue
        if e.entry_type == "reversal" or e.id in reversed_ids:
            continue
        items.append(
            {
                "folio_entry_id": e.id,
                "category": cat.code,
                "description": e.description,
                "quantity": e.quantity,
                "amount_minor": e.amount_minor,
                "vat_rate_bp": e.vat_rate_bp,
                "vat_minor": e.vat_minor,
            }
        )
    return items


def _totals(view: dict[str, Any], flags: list[str]) -> dict[str, Any]:
    t = {k: int(v["amount_minor"]) for k, v in view["totals"].items()}
    return {
        "accommodation_minor": t["accommodation"],
        "fnb_minor": t["fnb"],
        "other_minor": t["other"],
        "charges_minor": t["accommodation"] + t["fnb"] + t["other"],
        "vat_minor": t["vat_included"],
        "tips_minor": t["tips"],
        "paid_minor": t["paid"],
        "balance_minor": t["balance"],
        "by_category": {k: int(v["amount_minor"]) for k, v in view["by_category"].items()},
        "flags": flags,
    }


async def _issue(
    st: AppState,
    uow: UnitOfWork,
    ctx: TenantContext,
    *,
    folio: Folio,
    kind: str,
    supplier: dict[str, Any],
    recipient: dict[str, Any],
    totals: dict[str, Any],
    items: list[dict[str, Any]],
    credits: Invoice | None = None,
    reason: str | None = None,
) -> Invoice:
    settings = await billing._settings(uow, ctx)
    now = datetime.now(UTC)
    number = await _next_number(uow, ctx, settings.invoice_prefix, business_date(settings.timezone, now).year)
    invoice_id = (await uow.session.execute(text("SELECT app.uuid_v7()"))).scalar_one()
    document = {
        "title": KIND_TITLES[kind],
        "kind": kind,
        "number": number,
        "issued_at": now.astimezone(zoneinfo.ZoneInfo(settings.timezone)).strftime("%Y-%m-%d %H:%M"),
        "currency": folio.currency,
        "supplier": supplier,
        "recipient": recipient,
        "totals": totals,
        "items": items,
        "vat_registered": settings.vat_registered,
        "vat_rate_bp": settings.vat_rate_bp,
        "credits_number": credits.number if credits else None,
        "reason": reason,
    }
    pdf = invoice_pdf.render(document)
    key = hotel_key(ctx.hotel_id, "invoices", f"{invoice_id}.pdf")
    await st.storage.put(st.settings.storage_bucket_invoices, key, pdf, "application/pdf")
    invoice = (
        await uow.session.execute(
            insert(Invoice)
            .values(
                id=invoice_id,
                hotel_id=ctx.hotel_id,
                folio_id=folio.id,
                number=number,
                kind=kind,
                credits_invoice_id=credits.id if credits else None,
                issued_at=now,
                supplier=supplier,
                recipient=recipient,
                totals={**totals, **({"reason": reason} if reason else {})},
                currency=folio.currency,
                pdf_path=key,
                pdf_sha256=hashlib.sha256(pdf).digest(),
                created_by=ctx.actor_id,
            )
            .returning(Invoice)
        )
    ).scalar_one()
    if items:
        await uow.session.execute(
            insert(InvoiceItem),
            [
                {"hotel_id": ctx.hotel_id, "invoice_id": invoice.id, "line_no": i + 1, **it}
                for i, it in enumerate(items)
            ],
        )
    await write_audit(
        uow.session,
        ctx,
        "invoice.issue",
        "invoice",
        invoice.id,
        new_value={"number": number, "kind": kind, "charges_minor": totals["charges_minor"]},
        reason=reason,
    )
    return invoice


async def invoice_payload(uow: UnitOfWork, ctx: TenantContext, invoice: Invoice) -> dict[str, Any]:
    items = (
        await uow.session.execute(
            select(InvoiceItem)
            .where(InvoiceItem.hotel_id == ctx.hotel_id, InvoiceItem.invoice_id == invoice.id)
            .order_by(InvoiceItem.line_no)
        )
    ).scalars()
    stay_id = (
        await uow.session.execute(
            select(Folio.stay_id).where(Folio.hotel_id == ctx.hotel_id, Folio.id == invoice.folio_id)
        )
    ).scalar_one()
    c = invoice.currency
    t = invoice.totals
    return {
        "id": invoice.id,
        "number": invoice.number,
        "kind": invoice.kind,
        "title": KIND_TITLES[invoice.kind],
        "stay_id": stay_id,
        "folio_id": invoice.folio_id,
        "credits_invoice_id": invoice.credits_invoice_id,
        "issued_at": invoice.issued_at,
        "supplier": invoice.supplier,
        "recipient": invoice.recipient,
        "totals": {
            "accommodation": money(t["accommodation_minor"], c),
            "fnb": money(t["fnb_minor"], c),
            "other": money(t["other_minor"], c),
            "charges": money(t["charges_minor"], c),
            "vat_included": money(t["vat_minor"], c),
            "tips": money(t["tips_minor"], c),
            "paid": money(t["paid_minor"], c),
            "balance": money(t["balance_minor"], c),
        },
        "by_category": {k: money(v, c) for k, v in t["by_category"].items()},
        "flags": t.get("flags", []),
        "reason": t.get("reason"),
        "items": [
            {
                "line_no": i.line_no,
                "category": i.category,
                "description": i.description,
                "quantity": i.quantity,
                "amount": money(i.amount_minor, c),
                "vat_rate_bp": i.vat_rate_bp,
                "vat": money(i.vat_minor, c),
            }
            for i in items
        ],
        "sha256": invoice.pdf_sha256.hex() if invoice.pdf_sha256 else None,
    }


async def _invoice(uow: UnitOfWork, ctx: TenantContext, invoice_id: uuid.UUID) -> Invoice:
    invoice = (
        await uow.session.execute(
            select(Invoice).where(Invoice.hotel_id == ctx.hotel_id, Invoice.id == invoice_id)
        )
    ).scalar_one_or_none()
    if invoice is None:
        raise AppError("NOT_FOUND")
    return invoice


async def get_invoice(uow: UnitOfWork, ctx: TenantContext, invoice_id: uuid.UUID) -> dict[str, Any]:
    return await invoice_payload(uow, ctx, await _invoice(uow, ctx, invoice_id))


async def list_invoices(uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID) -> list[dict[str, Any]]:
    _, folio = await billing.stay_and_folio(uow, ctx, stay_id)
    invoices = (
        await uow.session.execute(
            select(Invoice)
            .where(Invoice.hotel_id == ctx.hotel_id, Invoice.folio_id == folio.id)
            .order_by(Invoice.issued_at, Invoice.id)
        )
    ).scalars()
    return [await invoice_payload(uow, ctx, i) for i in invoices]


async def pdf_url(st: AppState, uow: UnitOfWork, ctx: TenantContext, invoice_id: uuid.UUID) -> dict[str, Any]:
    invoice = await _invoice(uow, ctx, invoice_id)
    if invoice.pdf_path is None:
        raise AppError("NOT_FOUND", "This document has no PDF.")
    url = await st.storage.signed_download(st.settings.storage_bucket_invoices, invoice.pdf_path)
    await write_audit(uow.session, ctx, "invoice.download", "invoice", invoice.id)
    return {"url": url, "expires_in": 300}


async def _send(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, invoice: Invoice, to: list[str]
) -> list[str]:
    if invoice.pdf_path is None:
        raise AppError("NOT_FOUND", "This document has no PDF.")
    pdf = await st.storage.get(st.settings.storage_bucket_invoices, invoice.pdf_path)
    supplier_name = invoice.supplier.get("trading_name") or invoice.supplier.get("name")
    title = KIND_TITLES[invoice.kind]
    for address in to:
        await st.mailer.queue(
            uow,
            hotel_id=ctx.hotel_id,
            template="invoice",
            to=address,
            subject=f"{supplier_name}: {title} {invoice.number}",
            body=(
                f"Please find attached {title.lower()} {invoice.number} from {supplier_name}.\n\n"
                "If anything on it looks wrong, reply to the hotel directly."
            ),
            subject_ref={"invoice_id": str(invoice.id)},
            attachments=[(f"{invoice.number}.pdf", pdf, "application/pdf")],
        )
    await write_audit(
        uow.session, ctx, "invoice.email", "invoice", invoice.id, new_value={"recipients": len(to)}
    )
    return to


async def email_invoice(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, invoice_id: uuid.UUID, to: list[str]
) -> dict[str, Any]:
    invoice = await _invoice(uow, ctx, invoice_id)
    sent = await _send(st, uow, ctx, invoice, to)
    return {"invoice_id": invoice.id, "queued_to": sent}


# --- Checkout -------------------------------------------------------------------------------


async def check_out(
    st: AppState,
    uow: UnitOfWork,
    ctx: TenantContext,
    stay_id: uuid.UUID,
    body: dict[str, Any],
    permissions: frozenset[str],
) -> dict[str, Any]:
    s = uow.session
    stay, folio = await billing.stay_and_folio(uow, ctx, stay_id, lock=True)
    folio = (await s.execute(select(Folio).where(Folio.id == folio.id).with_for_update())).scalar_one()
    reissue = stay.status == "checked_out"
    if folio.status != "open" or stay.status not in ("active", "checkout_pending", "checked_out"):
        raise AppError(
            "INVALID_TRANSITION",
            "This stay is already checked out."
            if stay.status == "checked_out"
            else f"A {stay.status.replace('_', ' ')} stay cannot be checked out.",
        )
    open_orders = await _open_orders(uow, ctx, stay.id)
    if open_orders:
        raise AppError(
            "OPEN_ORDERS",
            "Finish, cancel or leave every order on the bill before checkout.",
            details={"orders": open_orders},
        )
    settings = await billing._settings(uow, ctx)
    view = await billing.view(uow, ctx, stay.id)
    balance = int(view["totals"]["balance"]["amount_minor"])
    override_reason = None
    if balance > 0:
        if not body.get("override"):
            raise AppError(
                "OUTSTANDING_BALANCE",
                "The bill still has a balance. Take payment first.",
                details={"balance": money(balance, folio.currency)},
            )
        if not settings.checkout_override_allowed:
            raise AppError("OVERRIDE_NOT_ALLOWED", "This hotel does not allow checkout with a balance.")
        if "checkout.override" not in permissions:
            raise AppError("PERMISSION_DENIED")
        override_reason = (body.get("override_reason") or "").strip()
        if not override_reason:
            raise AppError("REASON_REQUIRED", "Give a reason for checking out with a balance.")

    flags = _flags(stay)
    if "long_stay" in flags and not body.get("confirm_long_stay_vat"):
        raise AppError(
            "VALIDATION_FAILED",
            "This stay is longer than 28 days, so VAT on accommodation may differ. Confirm the "
            "accommodation charges are correct before checkout.",
            details={"reason": "long_stay_confirmation_required"},
        )
    totals = _totals(view, flags)
    kind = _kind(settings, totals["charges_minor"])
    recipient = await _recipient(uow, ctx, stay, kind, body.get("recipient_address"))
    email_to = list(dict.fromkeys(body.get("email_to") or []))
    if "email" in (body.get("bill_delivery") or []) and not email_to:
        default = recipient.get("email") if recipient["type"] == "company" else None
        if default is None:
            default = (
                await s.execute(
                    select(Guest.email).where(Guest.hotel_id == ctx.hotel_id, Guest.id == stay.guest_id)
                )
            ).scalar_one()
        if not default:
            raise AppError(
                "VALIDATION_FAILED",
                "Give an email address for the bill.",
                details={"reason": "email_to_required"},
            )
        email_to = [default]
    invoice = await _issue(
        st,
        uow,
        ctx,
        folio=folio,
        kind=kind,
        supplier=await _supplier(uow, ctx, settings),
        recipient=recipient,
        totals=totals,
        items=await _items(uow, ctx, folio.id),
    )
    now = datetime.now(UTC)
    await s.execute(update(Folio).where(Folio.id == folio.id).values(status="closed", closed_at=now))
    if not reissue:
        stay = await StayRepository(s, ctx).update_stay(
            stay.id,
            {
                "status": "checked_out",
                "checked_out_at": now,
                "checked_out_by": ctx.actor_id,
                "checkout_override_reason": override_reason,
            },
        )
        await RoomRepository(s, ctx).update(
            stay.room_id, None, {"status": settings.room_status_after_checkout, "status_changed_at": now}
        )
        await devices.reset_room_tablet(uow, ctx, stay.room_id, "checked_out")
    await write_audit(
        s,
        ctx,
        "stay.check_out" if not reissue else "stay.reissue_bill",
        "stay",
        stay.id,
        old_value={"balance_minor": balance},
        new_value={"invoice": invoice.number, "override": override_reason is not None, "flags": flags},
        reason=override_reason,
    )
    await emit(
        s,
        ctx,
        "STAY_CHECKED_OUT",
        [hotel_channel(ctx.hotel_id, "ops")],
        {"stay_id": str(stay.id), "room_id": str(stay.room_id), "invoice_id": str(invoice.id)},
    )
    if email_to:
        await _send(st, uow, ctx, invoice, email_to)
    return {
        "stay_id": stay.id,
        "status": "checked_out",
        "override_reason": override_reason,
        "invoice": await invoice_payload(uow, ctx, invoice),
        "emailed_to": email_to,
    }


# --- Credit notes ---------------------------------------------------------------------------


async def credit_note(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, invoice_id: uuid.UUID, reason: str
) -> dict[str, Any]:
    """Cancels a whole invoice: a credit note with the negated lines and totals, then the folio
    re-opens so the bill can be corrected and issued again (D44)."""
    reason = reason.strip()
    if not reason:
        raise AppError("REASON_REQUIRED")
    s = uow.session
    original = await _invoice(uow, ctx, invoice_id)
    if original.kind == "credit_note":
        raise AppError("INVALID_TRANSITION", "A credit note cannot be credited.")
    # Invoices are append-only (no row locks on them); the folio row serialises credit notes.
    folio = (
        await s.execute(
            select(Folio)
            .where(Folio.hotel_id == ctx.hotel_id, Folio.id == original.folio_id)
            .with_for_update()
        )
    ).scalar_one()
    already = (
        await s.execute(
            select(Invoice.number).where(
                Invoice.hotel_id == ctx.hotel_id, Invoice.credits_invoice_id == original.id
            )
        )
    ).scalar_one_or_none()
    if already is not None:
        raise AppError(
            "INVALID_TRANSITION", f"Already credited by {already}.", details={"credit_note": already}
        )
    if folio.status != "closed":
        raise AppError("INVALID_TRANSITION", "This bill is open for corrections; check out again first.")
    items = (
        await s.execute(
            select(InvoiceItem)
            .where(InvoiceItem.hotel_id == ctx.hotel_id, InvoiceItem.invoice_id == original.id)
            .order_by(InvoiceItem.line_no)
        )
    ).scalars()
    t = original.totals
    money_keys = ("accommodation_minor", "fnb_minor", "other_minor", "charges_minor", "vat_minor")
    totals = {
        **{k: -int(t[k]) for k in money_keys},
        "tips_minor": 0,
        "paid_minor": 0,
        "balance_minor": -int(t["charges_minor"]),
        "by_category": {k: -int(v) for k, v in t["by_category"].items()},
        "flags": [],
    }
    note = await _issue(
        st,
        uow,
        ctx,
        folio=folio,
        kind="credit_note",
        supplier=original.supplier,
        recipient=original.recipient,
        totals=totals,
        items=[
            {
                "folio_entry_id": i.folio_entry_id,
                "category": i.category,
                "description": i.description,
                "quantity": i.quantity,
                "amount_minor": -i.amount_minor,
                "vat_rate_bp": i.vat_rate_bp,
                "vat_minor": -i.vat_minor,
            }
            for i in items
        ],
        credits=original,
        reason=reason,
    )
    await s.execute(update(Folio).where(Folio.id == folio.id).values(status="open", closed_at=None))
    await write_audit(
        s,
        ctx,
        "invoice.credit",
        "invoice",
        original.id,
        new_value={"credit_note": note.number, "folio": "reopened"},
        reason=reason,
    )
    stay_id = (await s.execute(select(Stay.id).where(Stay.id == folio.stay_id))).scalar_one()
    await emit(
        s,
        ctx,
        "FOLIO_UPDATED",
        [hotel_channel(ctx.hotel_id, "ops")],
        {"stay_id": str(stay_id), "credit_note_id": str(note.id)},
    )
    return await invoice_payload(uow, ctx, note)
