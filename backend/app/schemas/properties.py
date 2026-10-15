"""Owners with several properties (D86)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import SignedMoney, StrictModel
from app.schemas.hotel import SignupHotel


class AddPropertyRequest(StrictModel):
    hotel: SignupHotel
    # The current legal documents for the new hotel's country, as at signup (D70).
    accepted_documents: list[uuid.UUID] = Field(default_factory=list, max_length=10)


class AddPropertyOut(BaseModel):
    hotel_id: uuid.UUID
    name: str
    code: str
    status: str
    subscription_status: str | None  # None: choose a plan in Settings > Plan (or ask for a trial)


class PortfolioHotel(BaseModel):
    hotel_id: uuid.UUID
    name: str
    code: str
    status: str
    property_type: str | None
    country: str
    city: str | None
    province: str | None
    currency: str
    business_date: date
    subscription_status: str | None
    plan_name: str | None
    trial_ends_on: date | None
    rooms: int
    occupied: int
    occupancy_bp: int
    in_house: int
    arrivals_today: int
    open_orders: int
    staff: int
    revenue_today: SignedMoney
    revenue_month: SignedMoney
    payments_month: SignedMoney


class CurrencyTotals(BaseModel):
    currency: str
    today: SignedMoney
    month: SignedMoney
    payments_month: SignedMoney


class PortfolioTotals(BaseModel):
    properties: int
    rooms: int
    occupied: int
    occupancy_bp: int
    in_house: int
    open_orders: int
    revenue: list[CurrencyTotals]  # one row per currency: amounts are never added across currencies


class PortfolioOut(BaseModel):
    data: list[PortfolioHotel]
    totals: PortfolioTotals


class TrialGrant(StrictModel):
    days: Annotated[int, Field(ge=1, le=90)]
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
