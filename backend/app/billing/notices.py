"""Billing emails and in-app notices to hotels (DECISIONS D79; owner's brief, section 11).

Each notice goes to the hotel's billing contact (or, without one, its owners) through the
existing mailer, which logs every delivery attempt in app.notifications and sends only after
the transaction commits; a failed email is logged as failed and never repeats an invoice or a
payment. An event on the hotel's ops channel tells signed-in staff at once.

A notice with a dedupe key is recorded in subscription_billing_events first; when the key was
used before, nothing is sent again (reminders and renewals run every few minutes).

Emails link to the signed-in Merchant app (Settings > Plan), never to a public invoice.
"""

from __future__ import annotations

import uuid
from typing import Any, Protocol

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import Settings
from app.core.currencies import format_minor
from app.db.session import TenantContext, UnitOfWork
from app.integrations.storage import Storage
from app.models.tenancy import CompanySettings, SubscriptionBillingContact, SubscriptionBillingEvent
from app.notifications.email import Mailer
from app.realtime.outbox import emit, hotel_channel
from app.services.admin import OWNER_EMAILS_SQL


class BillingDeps(Protocol):
    """What billing work needs from the application (AppState in the API, the worker's own)."""

    @property
    def settings(self) -> Settings: ...
    @property
    def storage(self) -> Storage: ...
    @property
    def mailer(self) -> Mailer: ...


# kind: (subject, body). Values are filled from the notice's own fields; every amount is
# already formatted with its currency.
TEMPLATES: dict[str, tuple[str, str]] = {
    "subscription_confirmed": (
        "Your {plan} subscription is active",
        "Thank you. Your {plan} subscription ({interval}) is active from {period_start}. "
        "It renews on {renews_on} for {amount}.",
    ),
    "upcoming_renewal": (
        "Your {plan} subscription renews on {renews_on}",
        "Your {plan} subscription renews on {renews_on} for {amount} ({interval}). "
        "The invoice for the next period follows by email.",
    ),
    "trial_ending": (
        "Your Diyneco trial ends on {trial_ends_on}",
        "Your free trial ends on {trial_ends_on}. Choose a plan in Settings > Plan to keep "
        "adding rooms, devices and staff. Your data stays in place either way.",
    ),
    "trial_ended": (
        "Your Diyneco trial has ended",
        "Your free trial ended on {trial_ends_on}. Your data is kept and can still be viewed. "
        "Choose a plan in Settings > Plan to carry on using Diyneco.",
    ),
    "payment_succeeded": (
        "Payment received for {invoice}",
        "We received {amount} for invoice {invoice} on {received_on}. Reference: {reference}. "
        "Balance still due on this invoice: {balance}.",
    ),
    "payment_failed": (
        "Payment for {invoice} did not go through",
        "The payment of {amount} for invoice {invoice} did not go through ({reason}). "
        "Nothing was charged. You can try again, or pay by bank transfer using the invoice "
        "number as the reference.",
    ),
    "payment_reminder": (
        "Reminder: invoice {invoice} is due on {due_on}",
        "Invoice {invoice} for {balance} is due on {due_on}. Pay by bank transfer using the "
        "invoice number as the reference, or pay online in Settings > Plan.",
    ),
    "invoice_overdue": (
        "Invoice {invoice} is overdue",
        "Invoice {invoice} was due on {due_on} and {balance} is still outstanding. "
        "Please pay by {grace_ends_on} to keep your subscription running without interruption.",
    ),
    "plan_upgraded": (
        "Your plan is now {plan}",
        "Your subscription moved to {plan} on {effective_on}. {detail}",
    ),
    "plan_change_scheduled": (
        "Your plan changes to {plan} on {effective_on}",
        "Your subscription moves to {plan} ({interval}) on {effective_on}, at {amount} per period. "
        "Until then nothing changes. {detail}",
    ),
    "subscription_cancelled": (
        "Your Diyneco subscription is cancelled",
        "Your subscription is cancelled and ends on {ends_on}. Your data and invoices are kept. "
        "Reason given: {reason}",
    ),
    "subscription_suspended": (
        "Your Diyneco subscription is suspended",
        "Invoice {invoice} ({balance}) is unpaid past the grace period, so your subscription is "
        "suspended. Your data is kept and can still be viewed, and billing stays open so you "
        "can pay. Access returns as soon as the payment is confirmed.",
    ),
    "subscription_reactivated": (
        "Your Diyneco subscription is active again",
        "Thank you, your payment is confirmed and your subscription is active again.",
    ),
    "refund_processed": (
        "Refund of {amount} for {invoice}",
        "We refunded {amount} against invoice {invoice} (credit note {credit_note}). {detail}",
    ),
}


class _Values(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return ""


def render(kind: str, values: dict[str, Any], seller: str, merchant_url: str | None) -> tuple[str, str]:
    subject, body = TEMPLATES[kind]
    v = _Values(values)
    link = (
        f"\n\nView your subscription and invoices: {merchant_url.rstrip('/')}/settings?tab=plan"
        if merchant_url
        else "\n\nSee your subscription and invoices in the Diyneco Merchant app, Settings > Plan."
    )
    return f"{seller}: {subject.format_map(v)}", body.format_map(v) + link + f"\n\n{seller}"


def money_text(amount_minor: int, currency: str) -> str:
    return format_minor(amount_minor, currency)


async def recipients(uow: UnitOfWork, hotel_id: uuid.UUID) -> list[str]:
    contact = (
        await uow.session.execute(
            select(SubscriptionBillingContact.billing_email).where(
                SubscriptionBillingContact.hotel_id == hotel_id
            )
        )
    ).scalar_one_or_none()
    if contact:
        return [str(contact)]
    return [str(e) for e in (await uow.session.execute(OWNER_EMAILS_SQL, {"h": hotel_id})).scalars()]


async def record(
    uow: UnitOfWork,
    ctx: TenantContext,
    kind: str,
    *,
    dedupe: str | None = None,
    subscription_id: uuid.UUID | None = None,
    invoice_id: uuid.UUID | None = None,
    detail: dict[str, Any] | None = None,
) -> bool:
    """Records a billing event; False when its dedupe key was used before."""
    stmt = pg_insert(SubscriptionBillingEvent).values(
        hotel_id=ctx.hotel_id,
        subscription_id=subscription_id,
        invoice_id=invoice_id,
        kind=kind,
        dedupe_key=dedupe,
        detail=detail or {},
    )
    if dedupe is not None:
        stmt = stmt.on_conflict_do_nothing(index_elements=["hotel_id", "dedupe_key"])
    done = await uow.session.execute(stmt.returning(SubscriptionBillingEvent.id))
    return done.first() is not None


async def notify(
    deps: BillingDeps,
    uow: UnitOfWork,
    ctx: TenantContext,
    kind: str,
    values: dict[str, Any],
    *,
    dedupe: str | None = None,
    subscription_id: uuid.UUID | None = None,
    invoice_id: uuid.UUID | None = None,
) -> bool:
    """Sends one notice (email to each recipient, plus an in-app event). False: already sent."""
    if not await record(
        uow,
        ctx,
        f"notice.{kind}",
        dedupe=dedupe,
        subscription_id=subscription_id,
        invoice_id=invoice_id,
        detail={k: str(v) for k, v in values.items()},
    ):
        return False
    company = (await uow.session.execute(select(CompanySettings))).scalar_one()
    seller = company.trading_name or company.legal_name
    subject, body = render(kind, values, seller, deps.settings.merchant_app_url)
    for address in await recipients(uow, ctx.hotel_id):
        await deps.mailer.queue(
            uow,
            hotel_id=ctx.hotel_id,
            template=f"billing_{kind}",
            to=address,
            subject=subject,
            body=body,
            subject_ref={
                k: str(v)
                for k, v in (("subscription_id", subscription_id), ("subscription_invoice_id", invoice_id))
                if v is not None
            },
        )
    await emit(
        uow.session,
        ctx,
        "BILLING_NOTICE",
        [hotel_channel(ctx.hotel_id, "ops")],
        {"kind": kind, "invoice_id": str(invoice_id) if invoice_id else None},
    )
    return True


async def already(uow: UnitOfWork, ctx: TenantContext, dedupe: str) -> bool:
    return (
        await uow.session.execute(
            text("SELECT 1 FROM app.subscription_billing_events WHERE hotel_id = :h AND dedupe_key = :k"),
            {"h": ctx.hotel_id, "k": dedupe},
        )
    ).first() is not None
