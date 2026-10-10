"""Platform admin and support access."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import Money, SignedMoney, StrictModel

FlagKey = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_.]{1,60}$")]


class Metrics(BaseModel):
    as_of: datetime
    hotels: int
    active_hotels: int
    pending_hotels: int
    suspended_hotels: int
    rooms: int
    connected_devices: int
    active_stays: int
    orders_today: int
    orders_this_month: int
    mrr: list[SignedMoney]
    active_subscriptions: int
    cancelled_this_month: int
    churn_bp: int


class HotelCounts(BaseModel):
    rooms: int
    devices: int
    connected_devices: int
    staff: int
    active_stays: int


class AdminHotel(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    status_reason: str | None
    created_at: datetime
    plan: str | None
    subscription_status: str | None
    renews_on: date | None
    counts: HotelCounts
    last_activity: datetime | None


class AdminHotelList(BaseModel):
    data: list[AdminHotel]
    next_cursor: str | None = None


class SuspendRequest(StrictModel):
    reason: Annotated[str, StringConstraints(min_length=3, max_length=500)]


class HotelStatusOut(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    status_reason: str | None


class PlanCreate(StrictModel):
    code: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,40}$")]
    name: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    monthly_price: Money
    limits: dict[Literal["rooms", "devices", "staff", "api_keys"], Annotated[int, Field(ge=0)]] = Field(
        default_factory=dict
    )
    features: dict[FlagKey, bool] = Field(default_factory=dict)


class PlanPatch(StrictModel):
    name: Annotated[str, StringConstraints(min_length=1, max_length=80)] | None = None
    monthly_price: Money | None = None
    limits: dict[Literal["rooms", "devices", "staff", "api_keys"], Annotated[int, Field(ge=0)]] | None = None
    features: dict[FlagKey, bool] | None = None
    is_active: bool | None = None


class PlanOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    monthly_price: SignedMoney
    limits: dict[str, Any]
    features: dict[str, Any]
    is_active: bool


class PlanList(BaseModel):
    data: list[PlanOut]
    next_cursor: str | None = None


class SubscriptionPut(StrictModel):
    plan_id: uuid.UUID
    status: Literal["trialing", "active", "past_due", "cancelled"]
    starts_on: date
    renews_on: date | None = None
    # Left out: the current overrides are kept. {} clears them.
    limit_overrides: (
        dict[Literal["rooms", "devices", "staff", "api_keys"], Annotated[int, Field(ge=0)]] | None
    ) = None


class SubscriptionOut(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    plan: PlanOut
    status: str
    starts_on: date
    renews_on: date | None
    cancelled_at: datetime | None
    limits: dict[str, Any]
    limit_overrides: dict[str, Any]


class FlagOut(BaseModel):
    key: str
    hotel_id: uuid.UUID | None
    enabled: bool
    updated_at: datetime
    updated_by: uuid.UUID | None


class FlagList(BaseModel):
    data: list[FlagOut]
    next_cursor: str | None = None


class FlagChange(StrictModel):
    key: FlagKey
    hotel_id: uuid.UUID | None = None
    enabled: bool


class FlagPatch(StrictModel):
    changes: Annotated[list[FlagChange], Field(min_length=1, max_length=50)]


class SupportRequest(StrictModel):
    ticket_reference: Annotated[str, StringConstraints(min_length=3, max_length=60)]
    minutes: Annotated[int, Field(ge=1, le=60, strict=True)] = 30
    reason: Annotated[str, StringConstraints(max_length=300)] | None = None


class SupportGrantOut(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    platform_user_id: uuid.UUID
    ticket_reference: str
    reason: str | None
    starts_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    active: bool


class SupportGrantList(BaseModel):
    data: list[SupportGrantOut]
    next_cursor: str | None = None


class SupportAccessOut(BaseModel):
    grant: SupportGrantOut
    access_token: str
    token_type: str


class HealthCheck(BaseModel):
    status: str
    model_config = {"extra": "allow"}


class Health(BaseModel):
    status: str
    checks: dict[str, HealthCheck]
    checked_at: datetime


class HotelOwner(BaseModel):
    name: str
    email: str


class PlatformAction(BaseModel):
    id: int
    action: str
    entity_type: str
    actor: str
    reason: str | None
    created_at: datetime


class AdminHotelDetail(BaseModel):
    """One hotel for the platform team: no guest data, only what running the account needs."""

    hotel: AdminHotel
    legal_name: str | None
    country: str
    currency: str
    timezone: str
    phone: str | None
    email: str | None
    owners: list[HotelOwner]
    subscription: SubscriptionOut | None
    support_grants: list[SupportGrantOut]
    platform_actions: list[PlatformAction]


class ActivityEvent(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID | None  # None for platform-wide events such as HEALTH_DEGRADED
    hotel_name: str | None
    type: str
    payload: dict[str, Any]
    created_at: datetime


class ActivityList(BaseModel):
    data: list[ActivityEvent]
    next_cursor: str | None = None
