"""Hotels paying Diyneco's invoices (DECISIONS D79; owner's brief, section 9).

- A hotel opens a checkout for an open invoice with the configured provider (Stitch, or the
  clearly labelled sandbox outside production). The attempt stays pending until its status is
  verified on the server: by asking the provider when the hotel returns or when a signed
  webhook arrives, never because a browser reached a success page.
- Bank transfers (EFT) and other offline payments are recorded by a billing administrator with
  the bank reference, after checking the statement (step-up, audited).
- Refunds are made by a billing administrator against a payment and always come with a credit
  note for the same amount, so the invoice, its payments and its credits always reconcile.
- Every payment starts unreconciled (a provider's) or matched (an administrator's own check of
  the statement); the platform's reconciliation view marks provider payments matched or
  disputed against the settlement report.

When an invoice of a subscription is paid, the subscription follows: a pending subscription
starts, a past-due or suspended one is active again once nothing is overdue.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import func, insert, select, text

from app.audit.writer import write_audit
from app.billing import notices, providers
from app.billing.notices import BillingDeps, money_text
from app.billing.providers import ProviderStatus
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.tenancy import (
    BillingSettings,
    CompanySettings,
    SubscriptionInvoice,
    SubscriptionPayment,
    SubscriptionPaymentAttempt,
    SubscriptionRefund,
)
from app.services import billing_engine, company, sub_invoices
from app.services.pricing import money

LABELS = {"sandbox": "Test payment (sandbox, no money moves)", "stitch": "Pay by bank (Stitch)"}


def _field(field: str, problem: str) -> AppError:
    return AppError(
        "VALIDATION_FAILED",
        problem,
        details={"fields": [{"field": field, "problem": problem, "type": "value_error"}]},
    )


async def _settings(uow: UnitOfWork) -> BillingSettings:
    return (await uow.session.execute(select(BillingSettings))).scalar_one()


async def _today(uow: UnitOfWork) -> date:
    return company.today_in((await company.company_row(uow)).timezone)


# --- Reading -------------------------------------------------------------------------------


def attempt_out(a: SubscriptionPaymentAttempt) -> dict[str, Any]:
    return {
        "id": a.id,
        "invoice_id": a.invoice_id,
        "provider": a.provider,
        "provider_label": LABELS.get(a.provider, a.provider),
        "test_mode": a.test_mode,
        "amount": money(a.amount_minor, a.currency),
        "status": a.status,
        "failure_reason": a.failure_reason,
        "created_at": a.created_at,
        "completed_at": a.completed_at,
    }


async def _refunded(uow: UnitOfWork, payment_id: uuid.UUID) -> int:
    return int(
        (
            await uow.session.execute(
                select(func.coalesce(func.sum(SubscriptionRefund.amount_minor), 0)).where(
                    SubscriptionRefund.payment_id == payment_id
                )
            )
        ).scalar_one()
    )


async def payment_out(uow: UnitOfWork, p: SubscriptionPayment, *, admin: bool = False) -> dict[str, Any]:
    number = (
        await uow.session.execute(
            select(SubscriptionInvoice.number).where(SubscriptionInvoice.id == p.invoice_id)
        )
    ).scalar_one()
    out = {
        "id": p.id,
        "invoice_id": p.invoice_id,
        "invoice_number": number,
        "method": p.method,
        "provider": p.provider,
        "test_mode": p.test_mode,
        "amount": money(p.amount_minor, p.currency),
        "refunded": money(await _refunded(uow, p.id), p.currency),
        "reference": p.reference,
        "received_on": p.received_on,
        "created_at": p.created_at,
    }
    if admin:
        out |= {
            "provider_payment_id": p.provider_payment_id,
            "notes": p.notes,
            "reconciliation_status": p.reconciliation_status,
            "reconciliation_note": p.reconciliation_note,
            "reconciled_at": p.reconciled_at,
        }
    return out


async def list_payments(uow: UnitOfWork, ctx: TenantContext, *, admin: bool = False) -> list[dict[str, Any]]:
    rows = (
        (
            await uow.session.execute(
                select(SubscriptionPayment)
                .where(SubscriptionPayment.hotel_id == ctx.hotel_id)
                .order_by(SubscriptionPayment.received_on.desc(), SubscriptionPayment.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [await payment_out(uow, p, admin=admin) for p in rows]


async def list_attempts(uow: UnitOfWork, ctx: TenantContext, limit: int = 50) -> list[dict[str, Any]]:
    rows = (
        (
            await uow.session.execute(
                select(SubscriptionPaymentAttempt)
                .where(SubscriptionPaymentAttempt.hotel_id == ctx.hotel_id)
                .order_by(SubscriptionPaymentAttempt.created_at.desc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return [attempt_out(a) for a in rows]


async def options(deps: BillingDeps, uow: UnitOfWork) -> dict[str, Any]:
    """How a hotel can pay: online (when a provider can run here) and by bank transfer."""
    s = await _settings(uow)
    online: dict[str, Any] = {"available": False, "provider": None, "label": None, "test_mode": False}
    try:
        p = providers.build(deps.settings, s.card_provider)
        online = {"available": True, "provider": p.name, "label": LABELS[p.name], "test_mode": p.test_mode}
    except AppError:
        pass
    c = (await uow.session.execute(select(CompanySettings))).scalar_one()
    bank = {k: v for k, v in (c.bank_details or {}).items() if v}
    return {
        "online": online,
        "eft": {
            "available": s.eft_enabled and bool(bank),
            "bank": bank,
            "instructions": c.payment_instructions,
            "reference_hint": "Use the invoice number as the payment reference.",
        },
    }


# --- Checkout ------------------------------------------------------------------------------


async def _open_invoice(uow: UnitOfWork, ctx: TenantContext, invoice_id: uuid.UUID) -> SubscriptionInvoice:
    inv = (
        await uow.session.execute(
            select(SubscriptionInvoice)
            .where(SubscriptionInvoice.id == invoice_id, SubscriptionInvoice.hotel_id == ctx.hotel_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if inv is None or inv.number is None:
        raise AppError("NOT_FOUND")
    if inv.kind != "invoice" or inv.status not in sub_invoices.OPEN:
        raise AppError("INVALID_TRANSITION", "This invoice has nothing left to pay.")
    return inv


def _return_url(deps: BillingDeps, attempt_id: uuid.UUID) -> str:
    base = (deps.settings.merchant_app_url or "").rstrip("/")
    return f"{base}/billing/return?attempt={attempt_id}"


async def start_checkout(
    deps: BillingDeps, uow: UnitOfWork, ctx: TenantContext, invoice_id: uuid.UUID
) -> dict[str, Any]:
    """Opens a checkout for the whole balance of an invoice; the amount comes from the server."""
    inv = await _open_invoice(uow, ctx, invoice_id)
    balance = (await sub_invoices.amounts(uow, inv))["balance"]
    if balance <= 0:
        raise AppError("INVALID_TRANSITION", "This invoice has nothing left to pay.")
    provider = providers.build(deps.settings, (await _settings(uow)).card_provider)
    if provider.name != "sandbox" and not deps.settings.merchant_app_url:
        raise AppError("SERVICE_UNAVAILABLE", "Online payment is not set up yet. Pay by bank transfer (EFT).")
    attempt = (
        await uow.session.execute(
            insert(SubscriptionPaymentAttempt)
            .values(
                hotel_id=ctx.hotel_id,
                invoice_id=inv.id,
                provider=provider.name,
                test_mode=provider.test_mode,
                amount_minor=balance,
                currency=inv.currency,
                created_by=ctx.actor_id,
            )
            .returning(SubscriptionPaymentAttempt)
        )
    ).scalar_one()
    checkout = await provider.create_checkout(
        attempt_id=str(attempt.id),
        amount_minor=balance,
        currency=inv.currency,
        reference=inv.number or "",
        return_url=_return_url(deps, attempt.id),
    )
    attempt.provider_ref = checkout.provider_ref
    attempt.checkout_url = checkout.url
    await uow.session.flush()
    await write_audit(
        uow.session,
        ctx,
        "subscription_payment.checkout",
        "subscription_invoice",
        inv.id,
        new_value={"attempt_id": str(attempt.id), "provider": provider.name, "amount_minor": balance},
    )
    return {**attempt_out(attempt), "checkout_url": checkout.url}


async def _attempt(
    uow: UnitOfWork, ctx: TenantContext, attempt_id: uuid.UUID, *, lock: bool = False
) -> SubscriptionPaymentAttempt:
    q = select(SubscriptionPaymentAttempt).where(
        SubscriptionPaymentAttempt.id == attempt_id, SubscriptionPaymentAttempt.hotel_id == ctx.hotel_id
    )
    a = (await uow.session.execute(q.with_for_update() if lock else q)).scalar_one_or_none()
    if a is None:
        raise AppError("NOT_FOUND")
    return a


async def check_attempt(
    deps: BillingDeps, uow: UnitOfWork, ctx: TenantContext, attempt_id: uuid.UUID
) -> dict[str, Any]:
    """The attempt as the provider reports it now (asked on the server, with Diyneco's keys)."""
    a = await _attempt(uow, ctx, attempt_id, lock=True)
    if a.status == "pending" and a.provider != "sandbox" and a.provider_ref:
        provider = providers.build(deps.settings, a.provider)
        await apply_status(deps, uow, ctx, a, await provider.fetch_status(a.provider_ref, a.currency))
    return attempt_out(a)


async def sandbox_complete(
    deps: BillingDeps, uow: UnitOfWork, ctx: TenantContext, attempt_id: uuid.UUID, outcome: str
) -> dict[str, Any]:
    """The sandbox page's choice. Only for sandbox attempts and never in production; the
    payment it records is test money and is never counted as collected."""
    if deps.settings.app_env == "production":
        raise AppError("NOT_FOUND")
    a = await _attempt(uow, ctx, attempt_id, lock=True)
    if a.provider != "sandbox":
        raise AppError("NOT_FOUND")
    if a.status != "pending":
        raise AppError("INVALID_TRANSITION", "This test payment is already finished.")
    status = ProviderStatus(
        status="succeeded" if outcome == "succeeded" else "failed",
        provider_payment_id=f"sbx_pay_{a.id}" if outcome == "succeeded" else None,
        amount_minor=a.amount_minor,
        failure_reason=None if outcome == "succeeded" else "Declined in the sandbox",
    )
    await apply_status(deps, uow, ctx, a, status)
    return attempt_out(a)


async def apply_status(
    deps: BillingDeps,
    uow: UnitOfWork,
    ctx: TenantContext,
    attempt: SubscriptionPaymentAttempt,
    status: ProviderStatus,
) -> None:
    """Settles a pending attempt from a verified provider status. Safe to call twice: a
    finished attempt is left alone and a provider payment id is recorded once."""
    if attempt.status != "pending" or status.status == "pending":
        return
    now = datetime.now(UTC)
    attempt.status = status.status
    attempt.completed_at = now
    attempt.failure_reason = status.failure_reason
    await uow.session.flush()
    inv = (
        await uow.session.execute(
            select(SubscriptionInvoice).where(SubscriptionInvoice.id == attempt.invoice_id).with_for_update()
        )
    ).scalar_one()
    if status.status != "succeeded":
        await write_audit(
            uow.session,
            ctx,
            f"subscription_payment.{status.status}",
            "subscription_invoice",
            inv.id,
            new_value={
                "attempt_id": str(attempt.id),
                "provider": attempt.provider,
                "reason": status.failure_reason,
            },
        )
        if status.status == "failed":
            await notices.notify(
                deps,
                uow,
                ctx,
                "payment_failed",
                {
                    "invoice": inv.number,
                    "amount": money_text(attempt.amount_minor, attempt.currency),
                    "reason": status.failure_reason or "declined",
                },
                dedupe=f"payment_failed:{attempt.id}",
                subscription_id=inv.subscription_id,
                invoice_id=inv.id,
            )
        return
    amount = status.amount_minor if status.amount_minor is not None else attempt.amount_minor
    payment = (
        await uow.session.execute(
            insert(SubscriptionPayment)
            .values(
                hotel_id=ctx.hotel_id,
                invoice_id=inv.id,
                attempt_id=attempt.id,
                method={"stitch": "pay_by_bank"}.get(attempt.provider, "sandbox"),
                provider=attempt.provider,
                test_mode=attempt.provider == "sandbox",
                amount_minor=amount,
                currency=attempt.currency,
                provider_payment_id=status.provider_payment_id or attempt.provider_ref,
                received_on=await _today(uow),
                notes=None
                if amount == attempt.amount_minor
                else f"Provider reported {amount}, asked {attempt.amount_minor}",
            )
            .returning(SubscriptionPayment)
        )
    ).scalar_one()
    await _after_money(deps, uow, ctx, inv, payment)


async def _after_money(
    deps: BillingDeps,
    uow: UnitOfWork,
    ctx: TenantContext,
    inv: SubscriptionInvoice,
    payment: SubscriptionPayment,
) -> None:
    status = await sub_invoices.settle(
        uow, ctx, inv, f"Payment {payment.reference or payment.provider_payment_id}"
    )
    await write_audit(
        uow.session,
        ctx,
        "subscription_payment.received",
        "subscription_invoice",
        inv.id,
        new_value={
            "payment_id": str(payment.id),
            "amount_minor": payment.amount_minor,
            "currency": payment.currency,
            "method": payment.method,
            "provider": payment.provider,
            "test_mode": payment.test_mode,
            "invoice_status": status,
        },
    )
    balance = (await sub_invoices.amounts(uow, inv))["balance"]
    await notices.notify(
        deps,
        uow,
        ctx,
        "payment_succeeded",
        {
            "invoice": inv.number,
            "amount": money_text(payment.amount_minor, payment.currency)
            + (" (test payment, no money moved)" if payment.test_mode else ""),
            "received_on": payment.received_on.isoformat(),
            "reference": payment.reference or payment.provider_payment_id or "",
            "balance": money_text(balance, inv.currency),
        },
        dedupe=f"payment_succeeded:{payment.id}",
        subscription_id=inv.subscription_id,
        invoice_id=inv.id,
    )
    if inv.subscription_id is not None:
        await billing_engine.review(deps, uow, ctx, inv.subscription_id)


# --- Billing administrators ----------------------------------------------------------------


async def record_manual(
    deps: BillingDeps,
    uow: UnitOfWork,
    ctx: TenantContext,
    *,
    invoice_id: uuid.UUID,
    amount_minor: int,
    method: str,
    reference: str,
    received_on: date,
    notes: str | None,
) -> dict[str, Any]:
    """A verified offline payment (EFT, ...) seen on Diyneco's bank statement."""
    inv = await _open_invoice(uow, ctx, invoice_id)
    balance = (await sub_invoices.amounts(uow, inv))["balance"]
    if amount_minor > balance:
        raise _field("amount_minor", f"The balance due is {money_text(balance, inv.currency)}.")
    if received_on > await _today(uow):
        raise _field("received_on", "A payment cannot be received in the future.")
    taken = (
        await uow.session.execute(
            select(SubscriptionPayment.id).where(
                SubscriptionPayment.provider == "manual",
                SubscriptionPayment.reference == reference,
                SubscriptionPayment.invoice_id == inv.id,
            )
        )
    ).first()
    if taken is not None:
        raise AppError(
            "INVALID_TRANSITION", "A payment with that reference is already recorded for this invoice."
        )
    payment = (
        await uow.session.execute(
            insert(SubscriptionPayment)
            .values(
                hotel_id=ctx.hotel_id,
                invoice_id=inv.id,
                method=method,
                provider="manual",
                amount_minor=amount_minor,
                currency=inv.currency,
                reference=reference,
                received_on=received_on,
                notes=notes,
                reconciliation_status="matched",
                reconciled_at=datetime.now(UTC),
                reconciled_by=ctx.actor_id,
                reconciliation_note="Recorded from the bank statement",
                recorded_by=ctx.actor_id,
            )
            .returning(SubscriptionPayment)
        )
    ).scalar_one()
    await _after_money(deps, uow, ctx, inv, payment)
    return await payment_out(uow, payment, admin=True)


async def _payment(uow: UnitOfWork, ctx: TenantContext, payment_id: uuid.UUID) -> SubscriptionPayment:
    p = (
        await uow.session.execute(
            select(SubscriptionPayment)
            .where(SubscriptionPayment.id == payment_id, SubscriptionPayment.hotel_id == ctx.hotel_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if p is None:
        raise AppError("NOT_FOUND")
    return p


async def refund(
    deps: BillingDeps,
    uow: UnitOfWork,
    ctx: TenantContext,
    payment_id: uuid.UUID,
    *,
    amount_minor: int,
    reason: str,
    reference: str | None,
) -> dict[str, Any]:
    """Gives money back from a payment, with a credit note for the same amount.

    Sandbox payments are refunded in the sandbox. Stitch Pay by Bank refunds are not made
    through the API until verified with Stitch, and EFT refunds are bank transfers: the
    administrator makes the transfer and records its reference here."""
    p = await _payment(uow, ctx, payment_id)
    left = p.amount_minor - await _refunded(uow, p.id)
    if amount_minor > left:
        raise _field(
            "amount_minor", f"At most {money_text(left, p.currency)} of this payment can be refunded."
        )
    method = "provider" if p.provider == "sandbox" else "manual"
    if method == "manual" and not reference:
        raise _field("reference", "Give the reference of the refund transfer you made.")
    note = await sub_invoices.credit(deps, uow, ctx, p.invoice_id, f"Refund: {reason}", amount_minor)
    row = (
        await uow.session.execute(
            insert(SubscriptionRefund)
            .values(
                hotel_id=ctx.hotel_id,
                payment_id=p.id,
                credit_note_id=note.id,
                amount_minor=amount_minor,
                currency=p.currency,
                method=method,
                provider_refund_id=f"sbx_ref_{uuid.uuid4().hex[:12]}" if p.provider == "sandbox" else None,
                reference=reference,
                test_mode=p.test_mode,
                reason=reason,
                created_by=ctx.actor_id,
            )
            .returning(SubscriptionRefund)
        )
    ).scalar_one()
    inv_number = (
        await uow.session.execute(
            select(SubscriptionInvoice.number).where(SubscriptionInvoice.id == p.invoice_id)
        )
    ).scalar_one()
    await write_audit(
        uow.session,
        ctx,
        "subscription_payment.refunded",
        "subscription_payment",
        p.id,
        new_value={
            "refund_id": str(row.id),
            "amount_minor": amount_minor,
            "currency": p.currency,
            "credit_note": note.number,
            "method": method,
            "reference": reference,
        },
        reason=reason,
    )
    await notices.notify(
        deps,
        uow,
        ctx,
        "refund_processed",
        {
            "amount": money_text(amount_minor, p.currency),
            "invoice": inv_number,
            "credit_note": note.number,
            "detail": "This was a test refund; no money moved."
            if p.test_mode
            else f"Reference: {reference}.",
        },
        dedupe=f"refund:{row.id}",
        invoice_id=p.invoice_id,
    )
    return {
        "id": row.id,
        "payment_id": p.id,
        "amount": money(amount_minor, p.currency),
        "credit_note_id": note.id,
        "credit_note_number": note.number,
        "method": method,
        "reference": reference,
        "test_mode": p.test_mode,
    }


async def reconcile(
    uow: UnitOfWork, ctx: TenantContext, payment_id: uuid.UUID, status: str, note: str | None
) -> dict[str, Any]:
    p = await _payment(uow, ctx, payment_id)
    before = p.reconciliation_status
    p.reconciliation_status = status
    p.reconciliation_note = note
    p.reconciled_at = datetime.now(UTC) if status != "unreconciled" else None
    p.reconciled_by = ctx.actor_id if status != "unreconciled" else None
    await uow.session.flush()
    await write_audit(
        uow.session,
        ctx,
        "subscription_payment.reconciled",
        "subscription_payment",
        p.id,
        old_value={"status": before},
        new_value={"status": status},
        reason=note,
    )
    return await payment_out(uow, p, admin=True)


# --- Webhooks ------------------------------------------------------------------------------


def _payment_request_id(payload: dict[str, Any]) -> str | None:
    """The Stitch payment request a webhook is about (data.client.paymentInitiationRequests.node.id,
    or a flatter shape). Only an id is taken: the status is always fetched from Stitch."""
    node: Any = payload
    for key in ("data", "client", "paymentInitiationRequests", "node"):
        if isinstance(node, dict) and key in node:
            node = node[key]
    for candidate in (node, payload.get("data") if isinstance(payload.get("data"), dict) else None, payload):
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str):
            return str(candidate["id"])
    return None


async def stitch_webhook(
    deps: BillingDeps, uow: UnitOfWork, headers: dict[str, str], body: bytes
) -> dict[str, str]:
    secret = deps.settings.stitch_webhook_secret
    if not secret:
        raise AppError("NOT_FOUND")
    event_id = providers.verify_svix(secret, headers, body)
    try:
        payload = json.loads(body)
    except ValueError as exc:
        raise AppError("VALIDATION_FAILED", "The webhook body is not JSON.") from exc
    if not isinstance(payload, dict):
        raise AppError("VALIDATION_FAILED", "The webhook body is not a JSON object.")
    event_type = str(payload.get("type") or payload.get("eventType") or "")[:200] or None
    rec = (
        await uow.session.execute(
            text("SELECT * FROM app.billing_webhook_record('stitch', :e, :t, CAST(:p AS jsonb))"),
            {"e": event_id, "t": event_type, "p": json.dumps(payload)},
        )
    ).one()
    if rec.duplicate and rec.processed:
        return {"status": "duplicate"}
    ref = _payment_request_id(payload)
    hotel_id = (
        (
            await uow.session.execute(text("SELECT app.billing_attempt_hotel('stitch', :r)"), {"r": ref})
        ).scalar_one()
        if ref
        else None
    )
    if hotel_id is None:
        # Perhaps one checkout for several invoices of an owner (D89).
        from app.services import group_billing  # noqa: PLC0415 - group_billing imports this module

        group_status = await group_billing.from_webhook(deps, uow, ref) if ref else None
        outcome = f"group {group_status}" if group_status else "ignored: no matching payment"
        await uow.session.execute(
            text("SELECT app.billing_webhook_done(:i, :o, NULL)"), {"i": rec.id, "o": outcome}
        )
        return {"status": group_status or "ignored"}
    await set_tenant(uow.session, hotel_id)
    ctx = TenantContext(hotel_id=hotel_id, actor_type="system", actor_id=None, actor_label="Stitch webhook")
    attempt = (
        await uow.session.execute(
            select(SubscriptionPaymentAttempt)
            .where(
                SubscriptionPaymentAttempt.provider == "stitch",
                SubscriptionPaymentAttempt.provider_ref == ref,
            )
            .with_for_update()
        )
    ).scalar_one()
    if attempt.status == "pending":
        provider = providers.build(deps.settings, "stitch")
        await apply_status(deps, uow, ctx, attempt, await provider.fetch_status(ref or "", attempt.currency))
    await uow.session.execute(
        text("SELECT app.billing_webhook_done(:i, :o, NULL)"), {"i": rec.id, "o": f"attempt {attempt.status}"}
    )
    return {"status": attempt.status}
