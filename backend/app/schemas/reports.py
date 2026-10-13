"""Reports, daily close, audit log, subscription, API keys and webhooks."""

from __future__ import annotations

import uuid
from datetime import date as Day
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from app.schemas.common import Money, SignedMoney, StrictModel


class RevenueRow(BaseModel):
    date: Day | None = None
    accommodation: SignedMoney
    fnb: SignedMoney
    other: SignedMoney
    revenue: SignedMoney
    vat_included: SignedMoney
    revenue_excluding_vat: SignedMoney
    discounts: SignedMoney
    adjustments: SignedMoney
    reversals: SignedMoney
    payments: SignedMoney
    tips: SignedMoney


class RevenueReport(BaseModel):
    from_: Day = Field(alias="from")
    to: Day
    days: list[RevenueRow]
    total: RevenueRow
    model_config = {"populate_by_name": True, "serialize_by_alias": True}


class PaymentLine(BaseModel):
    count: int
    amount: SignedMoney
    received: SignedMoney
    tips: SignedMoney


class PaymentByMethod(PaymentLine):
    method: str


class PaymentByStaff(PaymentLine):
    staff_id: uuid.UUID | None
    name: str
    late: int


class PaymentsReport(BaseModel):
    from_: Day = Field(alias="from")
    to: Day
    by_method: list[PaymentByMethod]
    by_staff: list[PaymentByStaff]
    total: PaymentLine
    model_config = {"populate_by_name": True, "serialize_by_alias": True}


class HourCount(BaseModel):
    hour: int
    orders: int


class OrdersReport(BaseModel):
    from_: Day = Field(alias="from")
    to: Day
    orders: int
    completed_or_open: int
    cancelled: int
    declined: int
    value: SignedMoney
    average_order_value: SignedMoney
    by_hour: list[HourCount]
    model_config = {"populate_by_name": True, "serialize_by_alias": True}


class ItemLine(BaseModel):
    menu_item_id: uuid.UUID | None
    name: str
    quantity: int
    revenue: SignedMoney


class ItemsReport(BaseModel):
    from_: Day = Field(alias="from")
    to: Day
    items: list[ItemLine]
    model_config = {"populate_by_name": True, "serialize_by_alias": True}


class StationTimes(BaseModel):
    station_id: uuid.UUID
    name: str
    items: int
    median_seconds: float
    p90_seconds: float


class KitchenReport(BaseModel):
    from_: Day = Field(alias="from")
    to: Day
    stations: list[StationTimes]
    model_config = {"populate_by_name": True, "serialize_by_alias": True}


class StaffTimes(BaseModel):
    staff_id: uuid.UUID | None
    name: str | None
    deliveries: int
    median_seconds: float


class RoomServiceReport(BaseModel):
    from_: Day = Field(alias="from")
    to: Day
    staff: list[StaffTimes]
    model_config = {"populate_by_name": True, "serialize_by_alias": True}


class OccupancyNight(BaseModel):
    date: Day
    rooms: int
    occupied: int
    out_of_service: int
    available: int
    occupancy_bp: int


class OccupancyTotal(BaseModel):
    rooms: int
    occupied: int
    out_of_service: int
    available: int
    occupancy_bp: int


class OccupancyReport(BaseModel):
    from_: Day = Field(alias="from")
    to: Day
    nights: list[OccupancyNight]
    total: OccupancyTotal
    model_config = {"populate_by_name": True, "serialize_by_alias": True}


class OpenBalance(BaseModel):
    stay_id: uuid.UUID
    room: str
    bill_to: str
    billing_type: str
    checked_out_at: datetime | None
    override_reason: str | None
    balance: SignedMoney


class OpenBalances(BaseModel):
    data: list[OpenBalance]
    total: SignedMoney


class DailyClosePut(StrictModel):
    terminal_batch_total: Money | None = None
    cash_counted: Money | None = None
    notes: Annotated[str, StringConstraints(max_length=2000)] | None = None
    mark_reviewed: bool = False


class CloseTips(BaseModel):
    staff_id: uuid.UUID | None
    name: str
    tips: SignedMoney


class ClosePayments(BaseModel):
    by_method: list[PaymentByMethod]
    by_staff: list[PaymentByStaff]
    total: PaymentLine


class CloseCard(BaseModel):
    recorded: SignedMoney
    terminal_batch_total: SignedMoney | None


class CloseCash(BaseModel):
    recorded: SignedMoney
    counted: SignedMoney | None


class CloseAdjustment(BaseModel):
    id: uuid.UUID
    original: SignedMoney
    new_amount: SignedMoney
    reason: str
    status: str
    requested_by: str | None
    decided_by: str | None


class CloseDiscount(BaseModel):
    id: uuid.UUID
    kind: str
    percent_bp: int | None
    amount: SignedMoney | None
    applies_to: str
    reason: str | None
    given_by: str | None


class CloseOverride(BaseModel):
    stay_id: uuid.UUID
    room: str
    reason: str


class CloseLateEntry(BaseModel):
    kind: Literal["payment", "order"]
    id: uuid.UUID
    reason: str
    occurred_at: datetime
    created_at: datetime


class DailyCloseReport(BaseModel):
    date: Day
    revenue: RevenueRow
    payments: ClosePayments
    tips_by_staff: list[CloseTips]
    card: CloseCard
    cash: CloseCash
    adjustments: list[CloseAdjustment]
    discounts: list[CloseDiscount]
    overrides: list[CloseOverride]
    late_entries: list[CloseLateEntry]
    flags: list[str]
    notes: str | None
    reviewed_at: datetime | None
    reviewed_by: uuid.UUID | None


class AuditEntry(BaseModel):
    id: int
    actor_type: str
    actor_id: uuid.UUID | None
    actor_label: str | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    reason: str | None
    ip: str | None
    device_id: uuid.UUID | None
    created_at: datetime


class AuditList(BaseModel):
    data: list[AuditEntry]
    next_cursor: str | None = None


# --- Subscription ---------------------------------------------------------------------------


class Usage(BaseModel):
    used: int
    limit: int | None


class PendingChange(BaseModel):
    plan_code: str
    plan_name: str
    interval: Literal["month", "quarter", "year"] | None
    price: SignedMoney
    effective_on: Day | None


class OutstandingInvoice(BaseModel):
    invoice_id: uuid.UUID
    number: str | None
    status: str
    due_on: Day | None
    balance: SignedMoney


class HotelSubscription(BaseModel):
    plan: dict[str, Any] | None  # empty during a trial without a plan (D76)
    status: (
        Literal["trial", "pending_payment", "active", "past_due", "suspended", "cancellation_scheduled"]
        | None
    )
    starts_on: Day | None
    renews_on: Day | None
    trial_ends_on: Day | None
    interval: Literal["month", "quarter", "year"] | None
    # The price agreed when the plan was bought; later plan price changes do not alter it.
    price: SignedMoney | None
    current_period_start: Day | None
    cancel_at_period_end: bool
    # A plan change waiting for the next renewal (D79).
    pending_change: PendingChange | None
    past_due_since: Day | None
    suspended_at: datetime | None
    outstanding: list[OutstandingInvoice]
    limits: dict[str, Any]
    usage: dict[str, Usage]


class QuoteRequest(StrictModel):
    plan_code: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,40}$")]
    interval: Literal["month", "quarter", "year"]


class QuoteLine(BaseModel):
    code: str
    description: str
    amount_minor: int
    discount_minor: int
    tax_minor: int
    total_minor: int


class QuoteOut(BaseModel):
    plan_code: str
    plan_name: str
    interval: Literal["month", "quarter", "year"]
    currency: str
    lines: list[QuoteLine]
    subtotal_minor: int
    tax_minor: int
    total_minor: int
    tax_charged: bool
    tax_name: str | None
    tax_rate_bp: int | None
    prices_include_tax: bool
    period_start: Day
    period_end: Day
    renews_at_minor: int
    intro_periods: int | None
    trial_days: int


class CancelRequest(StrictModel):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]


class ContactAddress(StrictModel):
    line1: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    line2: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    city: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    province: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    postal_code: Annotated[str, StringConstraints(strip_whitespace=True, max_length=12)] | None = None
    country: Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")] | None = None


class BillingContactPut(StrictModel):
    version: int
    legal_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None
    vat_number: Annotated[str, StringConstraints(strip_whitespace=True, max_length=30)] | None = None
    billing_email: EmailStr | None = None
    phone: Annotated[str, StringConstraints(pattern=r"^\+?[0-9 ()-]{7,30}$")] | None = None
    contact_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    address: ContactAddress = Field(default_factory=ContactAddress)


class BillingContactOut(BaseModel):
    legal_name: str | None
    vat_number: str | None
    billing_email: str | None
    phone: str | None
    contact_name: str | None
    address: dict[str, Any]
    version: int


# --- API keys and webhooks ------------------------------------------------------------------


class ApiKeyCreate(StrictModel):
    name: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    environment: Literal["sandbox", "production"]
    scopes: Annotated[list[str], Field(min_length=1, max_length=40)]


class ApiKeyOut(BaseModel):
    id: uuid.UUID
    name: str
    environment: str
    prefix: str
    scopes: list[str]
    created_by: uuid.UUID
    created_at: datetime
    last_used_at: datetime | None
    usage_count: int
    status: str
    revoked_at: datetime | None


class ApiKeyCreated(ApiKeyOut):
    secret: str


class ApiKeyList(BaseModel):
    data: list[ApiKeyOut]
    next_cursor: str | None = None


HttpsUrl = Annotated[str, StringConstraints(pattern=r"^https://[^\s/?#]+[^\s]*$", max_length=500)]


class WebhookCreate(StrictModel):
    url: HttpsUrl
    events: Annotated[list[str], Field(min_length=1, max_length=40)]


class WebhookStatusChange(StrictModel):
    status: Literal["active", "disabled"]


class WebhookOut(BaseModel):
    id: uuid.UUID
    url: str
    events: list[str]
    status: str
    failure_count: int
    created_at: datetime


class WebhookCreated(WebhookOut):
    signing_secret: str


class WebhookList(BaseModel):
    data: list[WebhookOut]
    next_cursor: str | None = None


class WebhookTestOut(BaseModel):
    webhook_id: uuid.UUID
    queued: bool
    seq: int


class DeliveryOut(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    attempt: int
    status_code: int | None
    error: str | None
    next_attempt_at: datetime | None
    created_at: datetime
    state: str


class DeliveryList(BaseModel):
    data: list[DeliveryOut]
    next_cursor: str | None = None


class AnalyticsDay(BaseModel):
    day: Day
    orders: int
    new_hotels: int
    checkins: int


class Analytics(BaseModel):
    days: list[AnalyticsDay]
