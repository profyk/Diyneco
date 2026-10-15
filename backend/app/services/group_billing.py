"""Owners paying for several properties at once (DECISIONS D89).

- Every property keeps its own tax invoice. The owner's statement lists the open invoices of
  every property they own; "Pay all" opens ONE checkout with the provider for the balance of
  every open invoice in a currency.
- The group (app.group_payments, control plane) owns that checkout. Each invoice's share is an
  ordinary payment attempt of its own hotel, linked to the group, created and settled under
  that hotel's context with the same code as a single payment (sub_payments.apply_status),
  so every hotel's invoice, payment, notices and audit trail look exactly as if it paid alone.
- When the provider confirms, the amount received is shared out oldest invoice first and
  never beyond an invoice's balance at that moment (another payment may have arrived since):
  anything left over is kept on the group as unallocated for a billing administrator to
  refund. A failed, cancelled or expired checkout fails every share.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert, select, text

from app.audit.writer import write_audit
from app.billing import providers
from app.billing.notices import BillingDeps
from app.billing.providers import ProviderStatus
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.tenancy import BillingSettings, GroupPayment, SubscriptionInvoice, SubscriptionPaymentAttempt
from app.services import properties, sub_invoices, sub_payments
from app.services.pricing import money


def _ctx(
    hotel_id: uuid.UUID, user_id: uuid.UUID | None, label: str, base: TenantContext | None
) -> TenantContext:
    return TenantContext(
        hotel_id=hotel_id,
        actor_type="user" if user_id else "system",
        actor_id=user_id,
        actor_label=label,
        ip=base.ip if base else None,
        request_id=base.request_id if base else None,
    )


def group_out(g: GroupPayment) -> dict[str, Any]:
    return {
        "id": g.id,
        "provider": g.provider,
        "test_mode": g.test_mode,
        "amount": money(g.amount_minor, g.currency),
        "paid": money(g.paid_minor, g.currency) if g.paid_minor is not None else None,
        "unallocated": money(g.unallocated_minor, g.currency),
        "status": g.status,
        "failure_reason": g.failure_reason,
        "checkout_url": g.checkout_url if g.status == "pending" else None,
        "created_at": g.created_at,
        "completed_at": g.completed_at,
    }


async def _open_invoices(uow: UnitOfWork, user_id: uuid.UUID, current: TenantContext) -> list[dict[str, Any]]:
    """Every open invoice with something due, across the hotels the user owns."""
    rows: list[dict[str, Any]] = []
    try:
        for m in await properties.owned(uow, user_id):
            await set_tenant(uow.session, m.hotel_id, user_id)
            invoices = (
                await uow.session.execute(
                    select(SubscriptionInvoice)
                    .where(
                        SubscriptionInvoice.hotel_id == m.hotel_id,
                        SubscriptionInvoice.kind == "invoice",
                        SubscriptionInvoice.number.is_not(None),
                        SubscriptionInvoice.status.in_(sub_invoices.OPEN),
                    )
                    .order_by(SubscriptionInvoice.due_on, SubscriptionInvoice.number)
                )
            ).scalars()
            for inv in invoices:
                balance = (await sub_invoices.amounts(uow, inv))["balance"]
                if balance > 0:
                    rows.append(
                        {
                            "hotel_id": m.hotel_id,
                            "hotel_name": m.hotel_name,
                            "invoice_id": inv.id,
                            "number": inv.number,
                            "status": inv.status,
                            "issued_at": inv.issued_at,
                            "due_on": inv.due_on,
                            "currency": inv.currency,
                            "total": money(inv.total_minor, inv.currency),
                            "balance": money(balance, inv.currency),
                            "balance_minor": balance,
                        }
                    )
    finally:
        await set_tenant(uow.session, current.hotel_id, user_id)
    return sorted(rows, key=lambda r: (r["due_on"] or datetime.max.date(), r["number"] or ""))


async def statement(
    deps: BillingDeps, uow: UnitOfWork, user_id: uuid.UUID, current: TenantContext
) -> dict[str, Any]:
    if not await properties.owned(uow, user_id):
        raise AppError("PERMISSION_DENIED", "Only a hotel owner sees the group statement.")
    invoices = await _open_invoices(uow, user_id, current)
    due: dict[str, int] = defaultdict(int)
    for r in invoices:
        due[r["currency"]] += r["balance_minor"]
    recent = (
        await uow.session.execute(
            select(GroupPayment)
            .where(GroupPayment.owner_user_id == user_id)
            .order_by(GroupPayment.created_at.desc())
            .limit(10)
        )
    ).scalars()
    s = (await uow.session.execute(select(BillingSettings))).scalar_one()
    return {
        "invoices": [{k: v for k, v in r.items() if k != "balance_minor"} for r in invoices],
        "due": [money(v, c) for c, v in sorted(due.items())],
        "payments": [group_out(g) for g in recent],
        "options": await sub_payments.options(deps, uow),
        "group_discount_bp": s.group_discount_bp,
        "group_discount_min_properties": s.group_discount_min_properties,
    }


async def start(
    deps: BillingDeps, uow: UnitOfWork, user_id: uuid.UUID, current: TenantContext, currency: str
) -> dict[str, Any]:
    """One checkout for the balance of every open invoice in `currency` across the owner's hotels."""
    invoices = [r for r in await _open_invoices(uow, user_id, current) if r["currency"] == currency]
    if not invoices:
        raise AppError("INVALID_TRANSITION", "Nothing is due in that currency.")
    total = sum(r["balance_minor"] for r in invoices)
    provider = providers.build(
        deps.settings, (await uow.session.execute(select(BillingSettings))).scalar_one().card_provider
    )
    if provider.name != "sandbox" and not deps.settings.merchant_app_url:
        raise AppError("SERVICE_UNAVAILABLE", "Online payment is not set up yet. Pay by bank transfer (EFT).")
    group = (
        await uow.session.execute(
            insert(GroupPayment)
            .values(
                owner_user_id=user_id,
                provider=provider.name,
                test_mode=provider.test_mode,
                currency=currency,
                amount_minor=total,
            )
            .returning(GroupPayment)
        )
    ).scalar_one()
    base = (deps.settings.merchant_app_url or "").rstrip("/")
    checkout = await provider.create_checkout(
        attempt_id=str(group.id),
        amount_minor=total,
        currency=currency,
        reference=f"GRP{group.id.hex[:12].upper()}",
        return_url=f"{base}/billing/return?group={group.id}",
    )
    group.provider_ref = checkout.provider_ref
    group.checkout_url = checkout.url
    await uow.session.flush()
    try:
        for r in invoices:
            await set_tenant(uow.session, r["hotel_id"], user_id)
            ctx = _ctx(r["hotel_id"], user_id, current.actor_label, current)
            attempt = (
                await uow.session.execute(
                    insert(SubscriptionPaymentAttempt)
                    .values(
                        hotel_id=r["hotel_id"],
                        invoice_id=r["invoice_id"],
                        provider=provider.name,
                        test_mode=provider.test_mode,
                        amount_minor=r["balance_minor"],
                        currency=currency,
                        created_by=user_id,
                        group_payment_id=group.id,
                    )
                    .returning(SubscriptionPaymentAttempt.id)
                )
            ).scalar_one()
            await write_audit(
                uow.session,
                ctx,
                "subscription_payment.group_checkout",
                "subscription_invoice",
                r["invoice_id"],
                new_value={
                    "group_payment_id": str(group.id),
                    "attempt_id": str(attempt),
                    "amount_minor": r["balance_minor"],
                },
            )
    finally:
        await set_tenant(uow.session, current.hotel_id, user_id)
    return {**group_out(group), "checkout_url": checkout.url, "invoices": len(invoices)}


async def settle(
    deps: BillingDeps,
    uow: UnitOfWork,
    group: GroupPayment,
    status: ProviderStatus,
    *,
    actor_label: str,
    restore: TenantContext | None = None,
) -> None:
    """Shares a verified provider result out over the group's invoices. Safe to call twice."""
    if group.status != "pending" or status.status == "pending":
        return
    paid = (
        (status.amount_minor if status.amount_minor is not None else group.amount_minor)
        if status.status == "succeeded"
        else 0
    )
    group.status = status.status
    group.completed_at = datetime.now(UTC)
    group.failure_reason = status.failure_reason
    group.paid_minor = paid if status.status == "succeeded" else None
    await uow.session.flush()
    shares = (
        await uow.session.execute(text("SELECT * FROM app.group_payment_shares(:g)"), {"g": group.id})
    ).all()
    remaining = paid
    try:
        for n, (hotel_id, attempt_id) in enumerate(shares, start=1):
            await set_tenant(uow.session, hotel_id)
            ctx = _ctx(hotel_id, None, actor_label, restore)
            attempt = await sub_payments._attempt(uow, ctx, attempt_id, lock=True)
            if attempt.status != "pending":
                continue
            if status.status != "succeeded":
                await sub_payments.apply_status(
                    deps,
                    uow,
                    ctx,
                    attempt,
                    ProviderStatus(status=status.status, failure_reason=status.failure_reason),
                )
                continue
            inv = (
                await uow.session.execute(
                    select(SubscriptionInvoice).where(SubscriptionInvoice.id == attempt.invoice_id)
                )
            ).scalar_one()
            balance = (
                (await sub_invoices.amounts(uow, inv))["balance"] if inv.status in sub_invoices.OPEN else 0
            )
            share = min(remaining, attempt.amount_minor, balance)
            if share > 0:
                await sub_payments.apply_status(
                    deps,
                    uow,
                    ctx,
                    attempt,
                    ProviderStatus(
                        status="succeeded",
                        provider_payment_id=f"{status.provider_payment_id or group.provider_ref}:{n}",
                        amount_minor=share,
                    ),
                )
                remaining -= share
            else:
                await sub_payments.apply_status(
                    deps,
                    uow,
                    ctx,
                    attempt,
                    ProviderStatus(
                        status="failed", failure_reason="Already paid, or not covered by the group payment"
                    ),
                )
    finally:
        await set_tenant(
            uow.session, restore.hotel_id if restore else None, restore.actor_id if restore else None
        )
    group.unallocated_minor = remaining
    await uow.session.flush()


async def _mine(uow: UnitOfWork, user_id: uuid.UUID, group_id: uuid.UUID) -> GroupPayment:
    g = (
        await uow.session.execute(
            select(GroupPayment)
            .where(GroupPayment.id == group_id, GroupPayment.owner_user_id == user_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if g is None:
        raise AppError("NOT_FOUND")
    return g


async def check(
    deps: BillingDeps, uow: UnitOfWork, user_id: uuid.UUID, current: TenantContext, group_id: uuid.UUID
) -> dict[str, Any]:
    """The group as the provider reports it now (asked on the server, with Diyneco's keys)."""
    g = await _mine(uow, user_id, group_id)
    if g.status == "pending" and g.provider != "sandbox" and g.provider_ref:
        provider = providers.build(deps.settings, g.provider)
        await settle(
            deps,
            uow,
            g,
            await provider.fetch_status(g.provider_ref, g.currency),
            actor_label=current.actor_label,
            restore=current,
        )
    return group_out(g)


async def sandbox_complete(
    deps: BillingDeps,
    uow: UnitOfWork,
    user_id: uuid.UUID,
    current: TenantContext,
    group_id: uuid.UUID,
    outcome: str,
) -> dict[str, Any]:
    if deps.settings.app_env == "production":
        raise AppError("NOT_FOUND")
    g = await _mine(uow, user_id, group_id)
    if g.provider != "sandbox":
        raise AppError("NOT_FOUND")
    if g.status != "pending":
        raise AppError("INVALID_TRANSITION", "This test payment is already finished.")
    result = ProviderStatus(
        status="succeeded" if outcome == "succeeded" else "failed",
        provider_payment_id=f"sbx_grp_{g.id}" if outcome == "succeeded" else None,
        amount_minor=g.amount_minor,
        failure_reason=None if outcome == "succeeded" else "Declined in the sandbox",
    )
    await settle(deps, uow, g, result, actor_label=current.actor_label, restore=current)
    return group_out(g)


async def from_webhook(deps: BillingDeps, uow: UnitOfWork, provider_ref: str) -> str | None:
    """A Stitch webhook about a group checkout: the status is fetched from Stitch, never trusted
    from the webhook body. None when the reference is not a group's."""
    g = (
        await uow.session.execute(
            select(GroupPayment)
            .where(GroupPayment.provider == "stitch", GroupPayment.provider_ref == provider_ref)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if g is None:
        return None
    if g.status == "pending":
        provider = providers.build(deps.settings, "stitch")
        await settle(
            deps, uow, g, await provider.fetch_status(provider_ref, g.currency), actor_label="Stitch webhook"
        )
    return g.status
