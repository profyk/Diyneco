"""Reports, daily close, audit log, subscription, API keys and webhooks."""

from __future__ import annotations

import uuid
from datetime import date as Day
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints

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


class HotelSubscription(BaseModel):
    plan: dict[str, Any] | None
    status: str | None
    starts_on: Day | None
    renews_on: Day | None
    limits: dict[str, Any]
    usage: dict[str, Usage]


class ChangeRequest(StrictModel):
    plan_code: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,40}$")]
    note: Annotated[str, StringConstraints(max_length=1000)] | None = None


class ChangeRequestOut(BaseModel):
    requested_plan: str
    status: Literal["received"]


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
