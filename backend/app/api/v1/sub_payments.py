"""Subscribing, plan changes, payments and the billing dashboard (DECISIONS D79).

- /subscription/...: a hotel subscribes, changes plan, pays its invoices and sees its payments.
- /billing/webhooks/stitch: Stitch's signed webhooks (no session; the signature is the check).
- /admin/hotels/{hotel_id}/payments: billing administrators record offline payments, refund
  and reconcile, in that hotel's context.
- /admin/billing/...: the cross-hotel Billing & Invoices dashboard, lists and CSV exports.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission, state_of
from app.core.errors import AppError
from app.schemas.sub_payments import (
    AdminInvoiceList,
    AdminPaymentList,
    AttemptList,
    AttemptOut,
    BillingSummary,
    CheckoutOut,
    ManualPayment,
    PaymentList,
    PaymentOptions,
    PaymentOut,
    PlanChangeOut,
    PlanChangeRequest,
    ProviderStatusOut,
    ReconcileRequest,
    RefundOut,
    RefundRequest,
    SandboxOutcome,
    SubscribeOut,
    SubscribeRequest,
    WebhookAck,
    WebhookEventList,
)
from app.services import billing_admin, billing_engine, company
from app.services import sub_payments as svc
from app.services.admin import _enter

router = APIRouter(prefix="/subscription", tags=["subscription"])
webhook_router = APIRouter(prefix="/billing/webhooks", tags=["billing"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])

SubscriptionRead = Annotated[Principal, Depends(require_permission("subscription.read"))]
SubscriptionManage = Annotated[Principal, Depends(require_permission("subscription.manage"))]
BillingManage = Annotated[Principal, Depends(require_permission("platform.billing.manage"))]


def _dump(model: Any, data: dict[str, Any]) -> dict[str, Any]:
    return dict(model.model_validate(data).model_dump(mode="json"))


# --- The hotel ------------------------------------------------------------------------------


@router.post("/subscribe", status_code=201, response_model=SubscribeOut)
async def subscribe(
    idem: IdemUser,
    body: SubscribeRequest,
    request: Request,
    uow: Uow,
    principal: SubscriptionManage,
    _s: StepUp,
) -> Response:
    """Subscribes to a published plan at the price the server computes, and issues the first
    invoice; the subscription is pending payment until that invoice is paid."""
    out = await billing_engine.subscribe(
        state_of(request), uow, principal.tenant(request), body.plan_code, body.interval
    )
    return await idem.complete(uow, 201, _dump(SubscribeOut, out))


@router.post("/change", response_model=PlanChangeOut)
async def change_plan(
    idem: IdemUser,
    body: PlanChangeRequest,
    request: Request,
    uow: Uow,
    principal: SubscriptionManage,
    _s: StepUp,
) -> Response:
    """Upgrades apply at once with a prorated invoice when proration is on; other changes
    wait for the next renewal. Choosing the current plan withdraws a scheduled change."""
    out = await billing_engine.change_plan(
        state_of(request), uow, principal.tenant(request), body.plan_code, body.interval
    )
    return await idem.complete(uow, 200, _dump(PlanChangeOut, out))


@router.get("/payment-options", response_model=PaymentOptions)
async def payment_options(request: Request, uow: Uow, principal: SubscriptionRead) -> dict[str, Any]:
    return await svc.options(state_of(request), uow)


@router.get("/payments", response_model=PaymentList)
async def my_payments(request: Request, uow: Uow, principal: SubscriptionRead) -> dict[str, Any]:
    return {"data": await svc.list_payments(uow, principal.tenant(request))}


@router.get("/payment-attempts", response_model=AttemptList)
async def my_attempts(request: Request, uow: Uow, principal: SubscriptionRead) -> dict[str, Any]:
    return {"data": await svc.list_attempts(uow, principal.tenant(request))}


@router.post("/invoices/{invoice_id}/pay", status_code=201, response_model=CheckoutOut)
async def pay_invoice(
    idem: IdemUser, invoice_id: uuid.UUID, request: Request, uow: Uow, principal: SubscriptionManage
) -> Response:
    """Opens a checkout for the invoice's balance with the configured provider; send the
    browser to `checkout_url`. Nothing is paid until the provider confirms it."""
    out = await svc.start_checkout(state_of(request), uow, principal.tenant(request), invoice_id)
    return await idem.complete(uow, 201, _dump(CheckoutOut, out))


@router.get("/payment-attempts/{attempt_id}", response_model=AttemptOut)
async def check_attempt(
    attempt_id: uuid.UUID, request: Request, uow: Uow, principal: SubscriptionRead
) -> dict[str, Any]:
    """The attempt's status as the provider reports it now (asked on the server)."""
    return await svc.check_attempt(state_of(request), uow, principal.tenant(request), attempt_id)


@router.post("/payment-attempts/{attempt_id}/sandbox", response_model=AttemptOut)
async def sandbox_outcome(
    idem: IdemUser,
    attempt_id: uuid.UUID,
    body: SandboxOutcome,
    request: Request,
    uow: Uow,
    principal: SubscriptionManage,
) -> Response:
    """Test mode only (never in production): finishes a sandbox checkout. No money moves and
    the payment is recorded as a test payment."""
    out = await svc.sandbox_complete(
        state_of(request), uow, principal.tenant(request), attempt_id, body.outcome
    )
    return await idem.complete(uow, 200, _dump(AttemptOut, out))


# --- Webhooks -------------------------------------------------------------------------------


@webhook_router.post("/stitch", response_model=WebhookAck)
async def stitch_webhook(request: Request, uow: Uow) -> dict[str, str]:
    """Stitch payment events, signed with Svix. A repeated event is acknowledged and not
    processed again; the payment's status is always fetched from Stitch."""
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    return await svc.stitch_webhook(state_of(request), uow, headers, body)


# --- Billing administrators: one hotel ------------------------------------------------------


@admin_router.get("/hotels/{hotel_id}/payments", response_model=PaymentList)
async def hotel_payments(
    hotel_id: uuid.UUID, request: Request, uow: Uow, principal: BillingManage
) -> dict[str, Any]:
    ctx = principal.for_hotel(request, hotel_id)
    await _enter(uow, ctx)
    return {"data": await svc.list_payments(uow, ctx, admin=True)}


@admin_router.post("/hotels/{hotel_id}/payments", status_code=201, response_model=PaymentOut)
async def record_payment(
    idem: IdemUser,
    hotel_id: uuid.UUID,
    body: ManualPayment,
    request: Request,
    uow: Uow,
    principal: BillingManage,
    _s: StepUp,
) -> Response:
    """Records a verified offline payment (EFT) with its bank reference."""
    ctx = principal.for_hotel(request, hotel_id)
    await _enter(uow, ctx)
    out = await svc.record_manual(
        state_of(request),
        uow,
        ctx,
        invoice_id=body.invoice_id,
        amount_minor=body.amount_minor,
        method=body.method,
        reference=body.reference,
        received_on=body.received_on,
        notes=body.notes,
    )
    return await idem.complete(uow, 201, _dump(PaymentOut, out))


@admin_router.post(
    "/hotels/{hotel_id}/payments/{payment_id}/refund", status_code=201, response_model=RefundOut
)
async def refund_payment(
    idem: IdemUser,
    hotel_id: uuid.UUID,
    payment_id: uuid.UUID,
    body: RefundRequest,
    request: Request,
    uow: Uow,
    principal: BillingManage,
    _s: StepUp,
) -> Response:
    """Refunds part or all of a payment, with a credit note for the same amount."""
    ctx = principal.for_hotel(request, hotel_id)
    await _enter(uow, ctx)
    out = await svc.refund(
        state_of(request),
        uow,
        ctx,
        payment_id,
        amount_minor=body.amount_minor,
        reason=body.reason,
        reference=body.reference,
    )
    return await idem.complete(uow, 201, _dump(RefundOut, out))


@admin_router.post("/hotels/{hotel_id}/payments/{payment_id}/reconcile", response_model=PaymentOut)
async def reconcile_payment(
    idem: IdemUser,
    hotel_id: uuid.UUID,
    payment_id: uuid.UUID,
    body: ReconcileRequest,
    request: Request,
    uow: Uow,
    principal: BillingManage,
) -> Response:
    ctx = principal.for_hotel(request, hotel_id)
    await _enter(uow, ctx)
    out = await svc.reconcile(uow, ctx, payment_id, body.status, body.note)
    return await idem.complete(uow, 200, _dump(PaymentOut, out))


# --- Billing administrators: across hotels --------------------------------------------------


async def _range(uow: Uow, start: date | None, end: date | None) -> tuple[date, date]:
    today = company.today_in((await company.company_row(uow)).timezone)
    end = end or today
    start = start or end.replace(day=1)
    if start > end or (end - start) > timedelta(days=3660):
        raise AppError("VALIDATION_FAILED", "Choose a start on or before the end, at most ten years apart.")
    return start, end


@admin_router.get("/billing/summary", response_model=BillingSummary)
async def billing_summary(
    uow: Uow,
    principal: BillingManage,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
) -> Response:
    f, t = await _range(uow, start, end)
    data = BillingSummary.model_validate(await billing_admin.summary(uow, f, t))
    return Response(data.model_dump_json(by_alias=True), media_type="application/json")


Format = Literal["json", "csv"]


@admin_router.get("/billing/invoices", response_model=AdminInvoiceList)
async def billing_invoices(
    uow: Uow,
    principal: BillingManage,
    q: Annotated[str | None, Query(max_length=100)] = None,
    status: Literal["issued", "partially_paid", "paid", "overdue", "void", "credited"] | None = None,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
    plan: Annotated[str | None, Query(pattern=r"^[a-z][a-z0-9_]{1,40}$")] = None,
    payment: Literal["paid", "unpaid", "partial", "overdue"] | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    format: Format = "json",
) -> Response:
    """Invoices and credit notes across hotels; `format=csv` exports up to 5,000 rows."""
    csv_out = format == "csv"
    out = await billing_admin.invoices(
        uow,
        q=q,
        status=status,
        start=start,
        end=end,
        plan=plan,
        payment=payment,
        limit=5000 if csv_out else limit,
        offset=0 if csv_out else offset,
    )
    if csv_out:
        return Response(
            billing_admin.invoices_csv(out["data"]),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="diyneco-invoices.csv"'},
        )
    return Response(AdminInvoiceList.model_validate(out).model_dump_json(), media_type="application/json")


@admin_router.get("/billing/payments", response_model=AdminPaymentList)
async def billing_payments(
    uow: Uow,
    principal: BillingManage,
    q: Annotated[str | None, Query(max_length=100)] = None,
    reconciliation: Literal["unreconciled", "matched", "disputed"] | None = None,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    format: Format = "json",
) -> Response:
    """Payments across hotels for reconciliation; `format=csv` exports up to 5,000 rows."""
    csv_out = format == "csv"
    out = await billing_admin.payments(
        uow,
        q=q,
        reconciliation=reconciliation,
        start=start,
        end=end,
        limit=5000 if csv_out else limit,
        offset=0 if csv_out else offset,
    )
    if csv_out:
        return Response(
            billing_admin.payments_csv(out["data"]),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="diyneco-payments.csv"'},
        )
    return Response(AdminPaymentList.model_validate(out).model_dump_json(), media_type="application/json")


@admin_router.get("/billing/webhooks", response_model=WebhookEventList)
async def billing_webhooks(
    uow: Uow, principal: BillingManage, limit: Annotated[int, Query(ge=1, le=500)] = 50
) -> dict[str, Any]:
    return {"data": await billing_admin.webhooks(uow, limit)}


@admin_router.get("/billing/provider", response_model=ProviderStatusOut)
async def billing_provider(request: Request, uow: Uow, principal: BillingManage) -> dict[str, Any]:
    """Which payment provider is selected and whether it is ready here; never a secret."""
    return await billing_admin.provider_status(uow, state_of(request).settings)
