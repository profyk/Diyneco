"""Platform insights and owners for the admin panel (D87). Aggregates only; money per currency."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import SignedMoney


class InsightTotals(BaseModel):
    hotels: int
    active: int
    pending_approval: int
    suspended: int
    activated: int  # a room, a set-up device and a first order
    in_use_30d: int  # an order in the last 30 days
    paying: int
    trials: int
    no_plan: int
    rooms: int
    owners: int
    multi_property_owners: int
    mrr: list[SignedMoney]
    gmv_30d: list[SignedMoney]  # money processed through hotels' bills in 30 days


class InsightPeriod(BaseModel):
    signups: int
    activation_bp: int
    trials_ended: int
    trials_converted: int
    trial_conversion_bp: int
    paying_at_start: int
    churned: int
    churn_bp: int
    new_mrr: list[SignedMoney]
    churned_mrr: list[SignedMoney]


class SignupDay(BaseModel):
    day: date
    signups: int


class FunnelStep(BaseModel):
    step: str
    label: str
    hotels: int


class Cohort(BaseModel):
    month: str  # YYYY-MM of signup
    signups: int
    activated: int
    in_use_30d: int
    paying: int
    closed: int


class Breakdown(BaseModel):
    key: str
    label: str
    hotels: int
    active: int
    activated: int
    paying: int
    trials: int
    rooms: int
    orders_30d: int
    mrr: list[SignedMoney]
    gmv_30d: list[SignedMoney]


class RoleActivity(BaseModel):
    role: str
    members: int
    active_7d: int
    active_30d: int


class InsightsOut(BaseModel):
    since: date
    until: date
    totals: InsightTotals
    period: InsightPeriod
    days: list[SignupDay]
    funnel: list[FunnelStep]
    cohorts: list[Cohort]
    by_country: list[Breakdown]
    by_region: list[Breakdown]
    by_property_type: list[Breakdown]
    users: list[RoleActivity]


class OwnerHotel(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    status: str
    country: str
    city: str | None
    province: str | None
    property_type: str | None
    rooms: int
    subscription_status: str | None
    plan_name: str | None


class OwnerOut(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    phone: str | None
    created_at: datetime
    last_login_at: datetime | None
    email_verified: bool
    countries: list[str]
    rooms: int
    paying: int
    mrr: list[SignedMoney]
    gmv_30d: list[SignedMoney]
    hotels: list[OwnerHotel]


class OwnerList(BaseModel):
    data: list[OwnerOut]
    next_cursor: str | None = None
