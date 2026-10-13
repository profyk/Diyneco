"""Diyneco's invoices and credit notes to hotels (DECISIONS D78).

A draft holds lines whose tax was worked out from Diyneco's tax position when it was drafted.
Issuing checks that position still holds, takes the next number for the kind, prefix and
year, copies the seller (company settings), the buyer (billing contact and hotel) and the
payment instructions into the invoice, renders and stores the PDF and emails it. From then on
the row is frozen by the database; corrections are credit notes, never edits.

A draft may be discarded (void). An issued plain invoice with nothing paid may be voided with a
reason; an issued tax invoice is only ever corrected by a credit note, as tax invoices must be.
All of this runs in the hotel's tenant context, so each hotel's own audit trail shows it.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, insert, select, text

from app.audit.writer import write_audit
from app.billing import subscription_pdf
from app.billing.notices import BillingDeps
from app.billing.vat import gross_and_vat, vat_included
from app.core.currencies import format_minor, is_supported
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.integrations.storage import hotel_key
from app.models.tenancy import (
    Hotel,
    SubscriptionBillingContact,
    SubscriptionInvoice,
    SubscriptionInvoiceEvent,
    SubscriptionInvoiceLine,
    SubscriptionPayment,
    SubscriptionRefund,
)
from app.services import company
from app.services.admin import OWNER_EMAILS_SQL
from app.services.pricing import money

OPEN = ("issued", "partially_paid", "overdue")


def _field(field: str, problem: str) -> AppError:
    return AppError(
        "VALIDATION_FAILED",
        problem,
        details={"fields": [{"field": field, "problem": problem, "type": "value_error"}]},
    )


# --- Reading -------------------------------------------------------------------------------


async def _lines(uow: UnitOfWork, invoice_id: uuid.UUID) -> list[SubscriptionInvoiceLine]:
    return list(
        (
            await uow.session.execute(
                select(SubscriptionInvoiceLine)
                .where(SubscriptionInvoiceLine.invoice_id == invoice_id)
                .order_by(SubscriptionInvoiceLine.position)
            )
        )
        .scalars()
        .all()
    )


async def _credited(uow: UnitOfWork, invoice_id: uuid.UUID) -> int:
    return int(
        (
            await uow.session.execute(
                select(func.coalesce(func.sum(SubscriptionInvoice.total_minor), 0)).where(
                    SubscriptionInvoice.credits_invoice_id == invoice_id,
                    SubscriptionInvoice.status != "void",
                )
            )
        ).scalar_one()
    )


async def paid_total(uow: UnitOfWork, invoice_id: uuid.UUID) -> int:
    """Money received for the invoice less money refunded from those payments."""
    received = (
        await uow.session.execute(
            select(func.coalesce(func.sum(SubscriptionPayment.amount_minor), 0)).where(
                SubscriptionPayment.invoice_id == invoice_id
            )
        )
    ).scalar_one()
    refunded = (
        await uow.session.execute(
            select(func.coalesce(func.sum(SubscriptionRefund.amount_minor), 0))
            .join(SubscriptionPayment, SubscriptionPayment.id == SubscriptionRefund.payment_id)
            .where(SubscriptionPayment.invoice_id == invoice_id)
        )
    ).scalar_one()
    return int(received) - int(refunded)


async def amounts(uow: UnitOfWork, inv: SubscriptionInvoice) -> dict[str, int]:
    """Paid, credited and the balance still due (never negative; credit notes owe nothing)."""
    if inv.kind != "invoice":
        return {"paid": 0, "credited": 0, "balance": 0}
    paid = await paid_total(uow, inv.id)
    credited = await _credited(uow, inv.id)
    return {"paid": paid, "credited": credited, "balance": max(0, inv.total_minor - paid - credited)}


def _line_out(line: SubscriptionInvoiceLine) -> dict[str, Any]:
    return {
        c: getattr(line, c)
        for c in (
            "position",
            "code",
            "description",
            "quantity",
            "unit_amount_minor",
            "discount_minor",
            "tax_minor",
            "total_minor",
        )
    }


async def payload(uow: UnitOfWork, inv: SubscriptionInvoice, *, with_lines: bool = True) -> dict[str, Any]:
    credits_number = None
    if inv.credits_invoice_id:
        credits_number = (
            await uow.session.execute(
                select(SubscriptionInvoice.number).where(SubscriptionInvoice.id == inv.credits_invoice_id)
            )
        ).scalar_one_or_none()
    figures = await amounts(uow, inv)
    return {
        "id": inv.id,
        "hotel_id": inv.hotel_id,
        "kind": inv.kind,
        "number": inv.number,
        "status": inv.status,
        "is_tax_invoice": inv.is_tax_invoice,
        "currency": inv.currency,
        "subtotal": money(inv.subtotal_minor, inv.currency),
        "tax": money(inv.tax_minor, inv.currency),
        "total": money(inv.total_minor, inv.currency),
        "paid": money(figures["paid"], inv.currency),
        "credited": money(figures["credited"], inv.currency),
        "balance": money(figures["balance"], inv.currency),
        "purpose": inv.purpose,
        "tax_name": inv.tax_name,
        "tax_rate_bp": inv.tax_rate_bp,
        "period_start": inv.period_start,
        "period_end": inv.period_end,
        "issued_at": inv.issued_at,
        "due_on": inv.due_on,
        "credits_invoice_id": inv.credits_invoice_id,
        "credits_number": credits_number,
        "seller": inv.seller,
        "buyer": inv.buyer,
        "notes": inv.notes,
        "has_pdf": inv.pdf_path is not None,
        "lines": [_line_out(line) for line in await _lines(uow, inv.id)] if with_lines else [],
    }


async def list_for_hotel(
    uow: UnitOfWork, ctx: TenantContext, *, include_drafts: bool
) -> list[dict[str, Any]]:
    q = select(SubscriptionInvoice).where(SubscriptionInvoice.hotel_id == ctx.hotel_id)
    if not include_drafts:
        # Hotels see what was issued to them, never Diyneco's drafts or discarded drafts.
        q = q.where(SubscriptionInvoice.number.is_not(None))
    rows = (await uow.session.execute(q.order_by(SubscriptionInvoice.created_at.desc()))).scalars().all()
    return [await payload(uow, r, with_lines=False) for r in rows]


async def get(
    uow: UnitOfWork, ctx: TenantContext, invoice_id: uuid.UUID, *, include_drafts: bool
) -> SubscriptionInvoice:
    inv = (
        await uow.session.execute(
            select(SubscriptionInvoice).where(
                SubscriptionInvoice.id == invoice_id, SubscriptionInvoice.hotel_id == ctx.hotel_id
            )
        )
    ).scalar_one_or_none()
    if inv is None or (not include_drafts and inv.number is None):
        raise AppError("NOT_FOUND")
    return inv


async def pdf_url(st: BillingDeps, inv: SubscriptionInvoice) -> str:
    """A signed address valid for 5 minutes, minted only after the tenant check."""
    if inv.pdf_path is None:
        raise AppError("NOT_FOUND", "This invoice has no PDF yet.")
    return await st.storage.signed_download(st.settings.storage_bucket_invoices, inv.pdf_path)


# --- Drafting ------------------------------------------------------------------------------


async def create_draft(
    uow: UnitOfWork,
    ctx: TenantContext,
    *,
    lines: list[dict[str, Any]],
    currency: str,
    prices_include_tax: bool,
    period_start: date | None = None,
    period_end: date | None = None,
    notes: str | None = None,
    subscription_id: uuid.UUID | None = None,
    reason: str | None = None,
    purpose: str = "manual",
    plan_id: uuid.UUID | None = None,
) -> SubscriptionInvoice:
    if not is_supported(currency):
        raise _field("currency", "That currency is not supported.")
    if not lines:
        raise _field("lines", "An invoice needs at least one line.")
    if (period_start is None) != (period_end is None) or (
        period_start and period_end and period_end <= period_start
    ):
        raise _field("period_end", "Give both period dates, the end after the start.")
    settings = await company.company_row(uow)
    tax = await company.tax_on(uow, company.today_in(settings.timezone), settings)
    rate = tax["rate_bp"] or 0
    computed = []
    for i, line in enumerate(lines, start=1):
        gross_before = line["quantity"] * line["unit_amount_minor"]
        if line.get("discount_minor", 0) > gross_before:
            raise _field(f"lines[{i - 1}].discount_minor", "A discount cannot exceed the line.")
        net = gross_before - line.get("discount_minor", 0)
        total, vat = gross_and_vat(net, rate, includes_vat=prices_include_tax, registered=tax["charged"])
        computed.append({**line, "position": i, "tax_minor": vat, "total_minor": total})
    total = sum(c["total_minor"] for c in computed)
    tax_total = sum(c["tax_minor"] for c in computed)
    inv = (
        await uow.session.execute(
            insert(SubscriptionInvoice)
            .values(
                hotel_id=ctx.hotel_id,
                subscription_id=subscription_id,
                purpose=purpose,
                plan_id=plan_id,
                kind="invoice",
                currency=currency,
                subtotal_minor=total - tax_total,
                tax_minor=tax_total,
                total_minor=total,
                is_tax_invoice=tax["charged"],
                tax_name=tax["tax_name"],
                tax_rate_bp=tax["rate_bp"],
                period_start=period_start,
                period_end=period_end,
                notes=notes,
                created_by=ctx.actor_id,
            )
            .returning(SubscriptionInvoice)
        )
    ).scalar_one()
    for c in computed:
        await uow.session.execute(
            insert(SubscriptionInvoiceLine).values(
                hotel_id=ctx.hotel_id,
                invoice_id=inv.id,
                position=c["position"],
                code=c.get("code") or "charge",
                description=c["description"],
                quantity=c["quantity"],
                unit_amount_minor=c["unit_amount_minor"],
                discount_minor=c.get("discount_minor", 0),
                tax_minor=c["tax_minor"],
                total_minor=c["total_minor"],
            )
        )
    await _event(uow, ctx, inv.id, None, "draft", None)
    await write_audit(
        uow.session,
        ctx,
        "subscription_invoice.draft",
        "subscription_invoice",
        inv.id,
        new_value={"total_minor": total, "currency": currency, "lines": len(computed)},
        reason=reason,
    )
    return inv


async def _event(
    uow: UnitOfWork,
    ctx: TenantContext,
    invoice_id: uuid.UUID,
    before: str | None,
    after: str,
    reason: str | None,
) -> None:
    await uow.session.execute(
        insert(SubscriptionInvoiceEvent).values(
            hotel_id=ctx.hotel_id,
            invoice_id=invoice_id,
            status_from=before,
            status_to=after,
            reason=reason,
            actor_type=ctx.actor_type,
            actor_id=ctx.actor_id,
        )
    )


# --- Issuing -------------------------------------------------------------------------------


def _seller(s: Any) -> dict[str, Any]:
    out = {
        "legal_name": s.legal_name,
        "trading_name": s.trading_name,
        "registration_number": s.registration_number,
        "registered_address": s.registered_address,
        "business_address": s.business_address,
        "billing_email": s.billing_email,
        "billing_phone": s.billing_phone,
        "country": s.country,
        "logo_path": s.logo_path,
        "vat_number": s.vat_number if s.vat_registered else None,
    }
    bank = {k: v for k, v in (s.bank_details or {}).items() if v}
    if bank:
        out["bank"] = bank
    return out


async def _buyer(uow: UnitOfWork, ctx: TenantContext) -> dict[str, Any]:
    hotel = (await uow.session.execute(select(Hotel).where(Hotel.id == ctx.hotel_id))).scalar_one()
    contact = (
        await uow.session.execute(
            select(SubscriptionBillingContact).where(SubscriptionBillingContact.hotel_id == ctx.hotel_id)
        )
    ).scalar_one_or_none()
    return {
        "hotel_name": hotel.name,
        "legal_name": (contact.legal_name if contact else None) or hotel.legal_name,
        "vat_number": contact.vat_number if contact else None,
        "billing_email": (contact.billing_email if contact else None) or hotel.email,
        "contact_name": contact.contact_name if contact else None,
        "phone": (contact.phone if contact else None) or hotel.phone,
        "address": (contact.address if contact and contact.address else None) or hotel.address,
    }


async def _locked(uow: UnitOfWork, ctx: TenantContext, invoice_id: uuid.UUID) -> SubscriptionInvoice:
    inv = (
        await uow.session.execute(
            select(SubscriptionInvoice)
            .where(SubscriptionInvoice.id == invoice_id, SubscriptionInvoice.hotel_id == ctx.hotel_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if inv is None:
        raise AppError("NOT_FOUND")
    return inv


async def _number(uow: UnitOfWork, kind: str, settings: Any, on: date) -> str:
    prefix = settings.invoice_prefix if kind == "invoice" else settings.credit_note_prefix
    year = on.year if settings.number_reset == "yearly" else 0
    n = (
        await uow.session.execute(
            text("SELECT app.next_subscription_invoice_number(:k, :p, :y)"),
            {"k": kind, "p": prefix, "y": year},
        )
    ).scalar_one()
    digits = str(n).zfill(settings.number_padding)
    return f"{prefix}-{year}-{digits}" if year else f"{prefix}-{digits}"


async def _render_and_store(
    st: BillingDeps, uow: UnitOfWork, ctx: TenantContext, inv: SubscriptionInvoice
) -> bytes:
    data = await payload(uow, inv)
    settings = await company.company_row(uow)
    logo = None
    if inv.seller.get("logo_path"):
        try:
            logo = await st.storage.get(st.settings.storage_bucket_assets, inv.seller["logo_path"])
        except Exception:
            logo = None
    tz_day = inv.issued_at.astimezone(ZoneInfo(settings.timezone)).date() if inv.issued_at else None
    doc = {
        **data,
        "issued_on": tz_day.isoformat() if tz_day else "",
        "payment_instructions": inv.payment_instructions,
        "paid_minor": data["paid"]["amount_minor"],
        "subtotal_minor": inv.subtotal_minor,
        "tax_minor": inv.tax_minor,
        "total_minor": inv.total_minor,
    }
    pdf = subscription_pdf.render(doc, data["lines"], logo)
    key = hotel_key(ctx.hotel_id, "subscription-invoices", f"{inv.id}.pdf")
    await st.storage.put(st.settings.storage_bucket_invoices, key, pdf, "application/pdf")
    inv.pdf_path = key
    await uow.session.flush()
    return pdf


async def _recipients(uow: UnitOfWork, ctx: TenantContext, buyer: dict[str, Any]) -> list[str]:
    if buyer.get("billing_email"):
        return [str(buyer["billing_email"])]
    return [str(e) for e in (await uow.session.execute(OWNER_EMAILS_SQL, {"h": ctx.hotel_id})).scalars()]


async def send(
    st: BillingDeps, uow: UnitOfWork, ctx: TenantContext, inv: SubscriptionInvoice, pdf: bytes | None = None
) -> int:
    """Emails the PDF to the billing contact (or the owners). The email links to the signed-in
    Merchant app, never to a public copy of the invoice."""
    if inv.number is None or inv.pdf_path is None:
        raise AppError("INVALID_TRANSITION", "Only an issued invoice can be sent.")
    pdf = pdf or await st.storage.get(st.settings.storage_bucket_invoices, inv.pdf_path)
    title = {"invoice": "Tax invoice" if inv.is_tax_invoice else "Invoice", "credit_note": "Credit note"}[
        inv.kind
    ]
    to = await _recipients(uow, ctx, inv.buyer)
    seller = inv.seller.get("trading_name") or inv.seller.get("legal_name") or "Diyneco"
    for address in to:
        await st.mailer.queue(
            uow,
            hotel_id=ctx.hotel_id,
            template="subscription_invoice" if inv.kind == "invoice" else "subscription_credit_note",
            to=address,
            subject=f"{seller}: {title} {inv.number}",
            body=(
                f"{title} {inv.number} for {format_minor(inv.total_minor, inv.currency)} is attached."
                + (f" It is due on {inv.due_on.isoformat()}." if inv.kind == "invoice" and inv.due_on else "")
                + "\n\nYou can also download it in the Diyneco Merchant app under Settings > Plan."
            ),
            subject_ref={"subscription_invoice_id": str(inv.id)},
            attachments=[(f"{inv.number}.pdf", pdf, "application/pdf")],
        )
    await write_audit(
        uow.session,
        ctx,
        "subscription_invoice.sent",
        "subscription_invoice",
        inv.id,
        new_value={"recipients": len(to)},
    )
    return len(to)


async def issue(
    st: BillingDeps,
    uow: UnitOfWork,
    ctx: TenantContext,
    invoice_id: uuid.UUID,
    *,
    due_on: date | None = None,
) -> SubscriptionInvoice:
    """Numbers, freezes, renders and emails a draft. Due after the payment terms, or on
    `due_on` (a renewal is due when its period starts)."""
    inv = await _locked(uow, ctx, invoice_id)
    if inv.status != "draft":
        raise AppError("INVALID_TRANSITION", "Only a draft can be issued.")
    if inv.kind == "invoice" and inv.total_minor <= 0:
        raise AppError("INVALID_TRANSITION", "An invoice must be for more than nothing.")
    settings = await company.company_row(uow)
    today = company.today_in(settings.timezone)
    tax = await company.tax_on(uow, today, settings)
    if (tax["charged"], tax["rate_bp"]) != (
        inv.is_tax_invoice,
        inv.tax_rate_bp if inv.is_tax_invoice else None,
    ):
        raise AppError(
            "INVALID_TRANSITION",
            "Diyneco's VAT position changed since this draft was made. Discard it and draft it again.",
        )
    # Everything that queries comes first: an autoflushing session must never write a half-issued
    # invoice (the freeze trigger would then refuse the rest).
    number = await _number(uow, inv.kind, settings, today)
    buyer = await _buyer(uow, ctx)
    inv.number = number
    inv.status = "issued"
    inv.issued_at = datetime.now(UTC)
    inv.due_on = (
        (due_on or today + timedelta(days=settings.payment_terms_days)) if inv.kind == "invoice" else None
    )
    inv.seller = _seller(settings)
    inv.buyer = buyer
    inv.payment_instructions = settings.payment_instructions if inv.kind == "invoice" else None
    await uow.session.flush()
    pdf = await _render_and_store(st, uow, ctx, inv)
    await _event(uow, ctx, inv.id, "draft", "issued", None)
    await write_audit(
        uow.session,
        ctx,
        "subscription_invoice.issued",
        "subscription_invoice",
        inv.id,
        new_value={"number": inv.number, "total_minor": inv.total_minor, "currency": inv.currency},
    )
    await send(st, uow, ctx, inv, pdf)
    return inv


# --- Corrections ---------------------------------------------------------------------------


async def void(
    uow: UnitOfWork, ctx: TenantContext, invoice_id: uuid.UUID, reason: str
) -> SubscriptionInvoice:
    inv = await _locked(uow, ctx, invoice_id)
    if inv.status == "draft":
        pass  # discarding a draft that was never issued
    elif inv.kind != "invoice" or inv.status not in ("issued", "overdue"):
        raise AppError("INVALID_TRANSITION", "Only a draft or an unpaid invoice can be voided.")
    elif inv.is_tax_invoice:
        raise AppError("INVALID_TRANSITION", "A tax invoice is corrected with a credit note, never voided.")
    elif await _credited(uow, inv.id):
        raise AppError("INVALID_TRANSITION", "This invoice has credit notes; credit the rest instead.")
    elif await paid_total(uow, inv.id):
        raise AppError("INVALID_TRANSITION", "Money was received for this invoice; credit it instead.")
    before = inv.status
    inv.status = "void"
    await uow.session.flush()
    await _event(uow, ctx, inv.id, before, "void", reason)
    await write_audit(
        uow.session,
        ctx,
        "subscription_invoice.void",
        "subscription_invoice",
        inv.id,
        old_value={"status": before},
        new_value={"status": "void"},
        reason=reason,
    )
    return inv


async def credit(
    st: BillingDeps,
    uow: UnitOfWork,
    ctx: TenantContext,
    invoice_id: uuid.UUID,
    reason: str,
    amount_minor: int | None,
) -> SubscriptionInvoice:
    """Issues a credit note against an issued invoice: the whole remaining amount, or part of
    it (amount including tax). The tax credited is the part of the amount the original rate
    contained, so the original and its credit notes always reconcile."""
    original = await _locked(uow, ctx, invoice_id)
    if original.kind != "invoice" or original.status not in ("issued", "overdue", "partially_paid", "paid"):
        raise AppError("INVALID_TRANSITION", "Only an issued invoice can be credited.")
    remaining = original.total_minor - await _credited(uow, original.id)
    amount = remaining if amount_minor is None else amount_minor
    if amount <= 0 or amount > remaining:
        raise _field("amount_minor", f"Credit between 0.01 and the {remaining} still creditable.")
    vat = vat_included(amount, original.tax_rate_bp or 0) if original.is_tax_invoice else 0
    note = (
        await uow.session.execute(
            insert(SubscriptionInvoice)
            .values(
                hotel_id=ctx.hotel_id,
                subscription_id=original.subscription_id,
                purpose="credit",
                plan_id=original.plan_id,
                kind="credit_note",
                credits_invoice_id=original.id,
                currency=original.currency,
                subtotal_minor=amount - vat,
                tax_minor=vat,
                total_minor=amount,
                is_tax_invoice=original.is_tax_invoice,
                tax_name=original.tax_name,
                tax_rate_bp=original.tax_rate_bp,
                period_start=original.period_start,
                period_end=original.period_end,
                notes=reason,
                created_by=ctx.actor_id,
            )
            .returning(SubscriptionInvoice)
        )
    ).scalar_one()
    await uow.session.execute(
        insert(SubscriptionInvoiceLine).values(
            hotel_id=ctx.hotel_id,
            invoice_id=note.id,
            position=1,
            code="credit",
            description=f"Credit against {original.number}: {reason}"[:300],
            quantity=1,
            unit_amount_minor=amount,
            tax_minor=vat,
            total_minor=amount,
        )
    )
    settings = await company.company_row(uow)
    today = company.today_in(settings.timezone)
    note.number = await _number(uow, "credit_note", settings, today)
    note.status = "issued"
    note.issued_at = datetime.now(UTC)
    note.seller = original.seller  # the parties of the invoice being corrected
    note.buyer = original.buyer
    await uow.session.flush()
    pdf = await _render_and_store(st, uow, ctx, note)
    await _event(uow, ctx, note.id, None, "issued", reason)
    if amount == remaining:
        before = original.status
        original.status = "credited"
        await uow.session.flush()
        await _event(uow, ctx, original.id, before, "credited", reason)
    await write_audit(
        uow.session,
        ctx,
        "subscription_invoice.credited",
        "subscription_invoice",
        original.id,
        new_value={"credit_note": note.number, "amount_minor": amount, "fully_credited": amount == remaining},
        reason=reason,
    )
    await send(st, uow, ctx, note, pdf)
    return note


async def settle(uow: UnitOfWork, ctx: TenantContext, inv: SubscriptionInvoice, reason: str) -> str:
    """Moves an invoice to paid or partially paid after money arrived; returns its status."""
    figures = await amounts(uow, inv)
    before = inv.status
    if before not in OPEN:
        return before
    if figures["balance"] == 0 and figures["paid"] > 0:
        target = "paid"
    elif figures["paid"] > 0 and before in ("issued", "overdue"):
        target = "partially_paid"
    else:
        return before
    if target != before:
        inv.status = target
        await uow.session.flush()
        await _event(uow, ctx, inv.id, before, target, reason)
    return target
