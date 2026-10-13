"""Subscribing, plan changes, payments, refunds and the billing dashboard (DECISIONS D79)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import SignedMoney, StrictModel
from app.schemas.reports import HotelSubscription
from app.schemas.sub_invoices import SubscriptionInvoiceOut

PlanCode = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,40}$")]
Interval = Literal["month", "quarter", "year"]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
Reference = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


# --- Hotel ---------------------------------------------------------------------------------


class SubscribeRequest(StrictModel):
    """Prices are computed on the server; the hotel only chooses and accepts the terms."""

    plan_code: PlanCode
    interval: Interval
    accept_terms: Literal[True]


class SubscribeOut(BaseModel):
    subscription: HotelSubscription
    invoice: SubscriptionInvoiceOut


class PlanChangeRequest(StrictModel):
    plan_code: PlanCode
    interval: Interval


class PlanChangeOut(BaseModel):
    subscription: HotelSubscription
    invoice: SubscriptionInvoiceOut | None
    effective: Literal["now", "renewal", "withdrawn"]


class AttemptOut(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    provider: str
    provider_label: str
    test_mode: bool
    amount: SignedMoney
    status: Literal["pending", "succeeded", "failed", "cancelled", "expired"]
    failure_reason: str | None
    created_at: datetime
    completed_at: datetime | None


class CheckoutOut(AttemptOut):
    checkout_url: str


class AttemptList(BaseModel):
    data: list[AttemptOut]


class SandboxOutcome(StrictModel):
    outcome: Literal["succeeded", "failed"]


class PaymentOut(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    invoice_number: str | None
    method: str
    provider: str
    test_mode: bool
    amount: SignedMoney
    refunded: SignedMoney
    reference: str | None
    received_on: date
    created_at: datetime
    provider_payment_id: str | None = None
    notes: str | None = None
    reconciliation_status: Literal["unreconciled", "matched", "disputed"] | None = None
    reconciliation_note: str | None = None
    reconciled_at: datetime | None = None


class PaymentList(BaseModel):
    data: list[PaymentOut]


class PaymentOptions(BaseModel):
    online: dict[str, Any]
    eft: dict[str, Any]


class WebhookAck(BaseModel):
    status: str


# --- Billing administrators ----------------------------------------------------------------


class ManualPayment(StrictModel):
    """A payment seen on Diyneco's bank statement, recorded after checking it."""

    invoice_id: uuid.UUID
    amount_minor: Annotated[int, Field(ge=1, le=10**12, strict=True)]
    method: Literal["eft", "other"] = "eft"
    reference: Reference
    received_on: date
    notes: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None


class RefundRequest(StrictModel):
    amount_minor: Annotated[int, Field(ge=1, le=10**12, strict=True)]
    reason: Reason
    # The bank or provider reference of the refund made (needed unless the sandbox makes it).
    reference: Reference | None = None


class RefundOut(BaseModel):
    id: uuid.UUID
    payment_id: uuid.UUID
    amount: SignedMoney
    credit_note_id: uuid.UUID
    credit_note_number: str | None
    method: Literal["provider", "manual"]
    reference: str | None
    test_mode: bool


class ReconcileRequest(StrictModel):
    status: Literal["unreconciled", "matched", "disputed"]
    note: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None


class SummaryCurrency(BaseModel):
    currency: str
    mrr: SignedMoney
    arr: SignedMoney
    invoiced: SignedMoney
    credited: SignedMoney
    collected: SignedMoney
    refunded: SignedMoney
    net_collected: SignedMoney
    test_collected: SignedMoney
    outstanding: SignedMoney
    overdue: SignedMoney
    overdue_invoices: int


class PlanRevenue(BaseModel):
    plan_code: str
    plan_name: str
    subscriptions: int
    mrr: SignedMoney
    collected: SignedMoney


class BillingSummary(BaseModel):
    from_: date = Field(serialization_alias="from")
    to: date
    active_subscriptions: int
    trials: int
    past_due: int
    suspended: int
    new_subscriptions: int
    cancelled_subscriptions: int
    failed_payments: int
    currencies: list[SummaryCurrency]
    by_plan: list[PlanRevenue]


class AdminInvoiceRow(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    hotel_name: str
    kind: str
    purpose: str
    number: str | None
    status: str
    currency: str
    total: SignedMoney
    tax: SignedMoney
    paid: SignedMoney
    credited: SignedMoney
    balance: SignedMoney
    issued_at: datetime | None
    due_on: date | None
    period_start: date | None
    period_end: date | None
    plan_code: str | None
    is_tax_invoice: bool


class AdminInvoiceList(BaseModel):
    data: list[AdminInvoiceRow]
    total: int


class AdminPaymentRow(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    hotel_name: str
    invoice_id: uuid.UUID
    invoice_number: str | None
    method: str
    provider: str
    test_mode: bool
    amount: SignedMoney
    refunded: SignedMoney
    reference: str | None
    provider_payment_id: str | None
    received_on: date
    reconciliation_status: str
    reconciliation_note: str | None
    reconciled_at: datetime | None
    created_at: datetime


class AdminPaymentList(BaseModel):
    data: list[AdminPaymentRow]
    total: int


class WebhookEventRow(BaseModel):
    id: uuid.UUID
    provider: str
    event_id: str
    event_type: str | None
    received_at: datetime
    processed_at: datetime | None
    outcome: str | None
    error: str | None


class WebhookEventList(BaseModel):
    data: list[WebhookEventRow]


class ProviderStatusOut(BaseModel):
    selected: Literal["none", "sandbox", "stitch"]
    environment: str
    sandbox_allowed: bool
    stitch: dict[str, Any]
    eft_enabled: bool
    bank_details_set: bool
