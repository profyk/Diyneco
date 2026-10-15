"""Owners with several properties (D86)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

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


class StatementInvoice(BaseModel):
    hotel_id: uuid.UUID
    hotel_name: str
    invoice_id: uuid.UUID
    number: str | None
    status: str
    issued_at: datetime | None
    due_on: date | None
    currency: str
    total: SignedMoney
    balance: SignedMoney


class GroupPaymentOut(BaseModel):
    id: uuid.UUID
    provider: str
    test_mode: bool
    amount: SignedMoney
    paid: SignedMoney | None
    unallocated: SignedMoney  # received beyond what the invoices still owed; refunded by Diyneco
    status: Literal["pending", "succeeded", "failed", "cancelled", "expired"]
    failure_reason: str | None
    checkout_url: str | None
    created_at: datetime
    completed_at: datetime | None


class GroupCheckoutOut(GroupPaymentOut):
    invoices: int


class GroupStatement(BaseModel):
    """Every open invoice of the owner's properties, what is due per currency (D89)."""

    invoices: list[StatementInvoice]
    due: list[SignedMoney]
    payments: list[GroupPaymentOut]
    options: dict[str, Any]
    group_discount_bp: int
    group_discount_min_properties: int


class GroupPayRequest(StrictModel):
    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


HotelRole = Literal[
    "hotel_owner",
    "hotel_admin",
    "general_manager",
    "reception_manager",
    "receptionist",
    "finance_manager",
    "kitchen_manager",
    "kitchen_staff",
    "room_service_manager",
    "room_service_staff",
]


class PropertyAssignment(StrictModel):
    hotel_id: uuid.UUID
    role_codes: Annotated[list[HotelRole], Field(min_length=1, max_length=5)]


class MultiInvite(StrictModel):
    """One person invited to several of the owner's properties, with a role at each (D90)."""

    name: Annotated[str, StringConstraints(min_length=1, max_length=120, strip_whitespace=True)]
    email: Annotated[str, StringConstraints(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)]
    department: Annotated[str, StringConstraints(max_length=80)] | None = None
    assignments: Annotated[list[PropertyAssignment], Field(min_length=1, max_length=50)]


class MultiInviteResult(BaseModel):
    hotel_id: uuid.UUID
    hotel_name: str
    id: uuid.UUID
    email: str
    roles: list[dict[str, Any]]
    expires_at: datetime


class MultiInviteList(BaseModel):
    data: list[MultiInviteResult]


class TrialGrant(StrictModel):
    days: Annotated[int, Field(ge=1, le=90)]
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
