"""Plans & Pricing (DECISIONS D74): the plan catalogue, its price history and the public
pricing page."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import Money, SignedMoney, StrictModel

FlagKey = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_.]{1,60}$")]
Interval = Literal["month", "quarter", "year"]
LimitKey = Literal["rooms", "devices", "staff", "api_keys"]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
Text200 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
Highlight = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Amount = Annotated[int, Field(ge=0, le=10**12, strict=True)]


class PriceOut(BaseModel):
    id: uuid.UUID
    interval: Interval
    amount: SignedMoney
    intro_amount: SignedMoney | None
    intro_periods: int | None
    # The price spread over months, for comparing intervals (rounded half up).
    per_month: SignedMoney
    effective_from: datetime
    existing_policy: Literal["new_only", "next_renewal"]
    notice_days: int | None
    reason: str
    in_force: bool


class PlanOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    currency: str
    short_description: str | None
    description: str | None
    highlights: list[str]
    status: Literal["draft", "published", "archived"]
    display_order: int
    recommended: bool
    setup_fee: SignedMoney
    trial_days: int
    tax_treatment: Literal["exclusive", "inclusive"]
    support_level: str | None
    overage_policy: str | None
    can_upgrade: bool
    can_downgrade: bool
    promo_discount_bp: int
    promo_ends_on: date | None
    limits: dict[str, int]
    features: dict[str, bool]
    published_at: datetime | None
    archived_at: datetime | None
    version: int
    # Price in force per interval (absent: not offered on that interval).
    prices: dict[str, PriceOut]
    # Changes not yet in force, and earlier prices, newest first.
    scheduled: list[PriceOut]
    history: list[PriceOut]


class PlanList(BaseModel):
    data: list[PlanOut]
    next_cursor: str | None = None


class _PlanFields(StrictModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)] | None = None
    short_description: Text200 | None = None
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)] | None = None
    highlights: Annotated[list[Highlight], Field(max_length=20)] | None = None
    display_order: Annotated[int, Field(ge=0, le=1000)] | None = None
    recommended: bool | None = None
    setup_fee_minor: Amount | None = None
    trial_days: Annotated[int, Field(ge=0, le=365)] | None = None
    tax_treatment: Literal["exclusive", "inclusive"] | None = None
    support_level: Text200 | None = None
    overage_policy: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None
    can_upgrade: bool | None = None
    can_downgrade: bool | None = None
    promo_discount_bp: Annotated[int, Field(ge=0, le=10000)] | None = None
    promo_ends_on: date | None = None
    limits: dict[LimitKey, Annotated[int, Field(ge=0)]] | None = None
    features: dict[FlagKey, bool] | None = None


class PlanCreate(_PlanFields):
    code: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{1,40}$")]
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class PlanPatch(_PlanFields):
    version: int
    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")] | None = None
    # Required once the plan is published: kept in the audit log.
    reason: Reason | None = None


class PriceCreate(StrictModel):
    interval: Interval
    amount: Money
    intro_amount: Money | None = None
    intro_periods: Annotated[int, Field(ge=1, le=36)] | None = None
    # Left out: in force at once. A published plan may schedule a later start.
    effective_from: datetime | None = None
    existing_policy: Literal["new_only", "next_renewal"] = "new_only"
    reason: Reason


class PlanStatusChange(StrictModel):
    reason: Reason


class BillingSettingsOut(BaseModel):
    price_change_notice_days: int
    version: int
    updated_at: datetime


class BillingSettingsPut(StrictModel):
    version: int
    reason: Reason
    price_change_notice_days: Annotated[int, Field(ge=0, le=365)]


class PublicPrice(BaseModel):
    interval: Interval
    amount: SignedMoney
    per_month: SignedMoney
    intro_amount: SignedMoney | None
    intro_periods: int | None
    # Saving against paying monthly for the same time, in basis points (null: no monthly price).
    saving_bp: int | None


class PublicPlan(BaseModel):
    code: str
    name: str
    short_description: str | None
    description: str | None
    highlights: list[str]
    recommended: bool
    currency: str
    tax_treatment: Literal["exclusive", "inclusive"]
    setup_fee: SignedMoney
    trial_days: int
    support_level: str | None
    overage_policy: str | None
    promo_discount_bp: int
    promo_ends_on: date | None
    limits: dict[str, int]
    prices: list[PublicPrice]


class PublicPlanList(BaseModel):
    data: list[PublicPlan]
    # Whether published prices include VAT and whether the seller charges it today.
    tax_charged: bool
    tax_name: str | None
    tax_rate_bp: int | None
