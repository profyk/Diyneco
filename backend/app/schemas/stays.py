"""Guests, billing profiles and stays."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, StringConstraints, model_validator

from app.schemas.common import Money, Name, StrictModel

Phone = Annotated[str, StringConstraints(max_length=40, pattern=r"^[0-9+() -]{6,40}$")]
Country = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
Reason = Annotated[str, StringConstraints(max_length=300)]
StayStatus = Literal["reserved", "checked_in", "active", "checkout_pending", "checked_out", "cancelled"]


class GuestCreate(StrictModel):
    name: Name
    email: EmailStr | None = None
    phone: Phone | None = None
    nationality: Country | None = None


class GuestPatch(StrictModel):
    name: Name | None = None
    email: EmailStr | None = None
    phone: Phone | None = None
    nationality: Country | None = None


class GuestOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str | None
    phone: str | None
    nationality: str | None
    anonymised: bool
    created_at: datetime


class GuestList(BaseModel):
    data: list[GuestOut]
    next_cursor: str | None = None


class BillingProfileCreate(StrictModel):
    company_name: Name
    registration_number: Annotated[str, StringConstraints(max_length=40)] | None = None
    vat_number: Annotated[str, StringConstraints(pattern=r"^4\d{9}$")] | None = None
    billing_address: dict[str, str] = Field(default_factory=dict, max_length=8)
    billing_email: EmailStr | None = None


class BillingProfileOut(BaseModel):
    id: uuid.UUID
    company_name: str
    registration_number: str | None
    vat_number: str | None
    billing_address: dict[str, str]
    billing_email: str | None


class BillingProfileList(BaseModel):
    data: list[BillingProfileOut]
    next_cursor: str | None = None


class Billing(StrictModel):
    type: Literal["personal", "company"] = "personal"
    billing_profile_id: uuid.UUID | None = None
    purchase_order: Annotated[str, StringConstraints(max_length=60)] | None = None
    traveller_name: Name | None = None

    @model_validator(mode="after")
    def _company(self) -> Billing:
        if self.type == "company" and self.billing_profile_id is None:
            raise ValueError("Company billing needs a billing_profile_id.")
        if self.type == "personal" and self.billing_profile_id is not None:
            raise ValueError("Personal billing takes no billing profile.")
        return self


class _GuestRef(StrictModel):
    guest_id: uuid.UUID | None = None
    guest: GuestCreate | None = None
    rate_override: Money | None = None
    rate_override_reason: Reason | None = None
    billing: Billing = Field(default_factory=Billing)
    training: bool = False

    @model_validator(mode="after")
    def _one_guest(self) -> _GuestRef:
        if (self.guest_id is None) == (self.guest is None):
            raise ValueError("Send either guest_id or guest.")
        return self


class StayCreate(_GuestRef):
    room_id: uuid.UUID
    arrival_date: date
    departure_date: date


class WalkIn(_GuestRef):
    nights: Annotated[int, Field(ge=1, le=90, strict=True)]


class RoomRef(BaseModel):
    id: uuid.UUID
    number: str


class GuestRef(BaseModel):
    id: uuid.UUID
    name: str


class FolioSummary(BaseModel):
    folio_id: uuid.UUID
    status: str
    accommodation: Money
    fnb: Money
    other: Money
    tips: Money
    paid: Money
    balance: Money


class StayOut(BaseModel):
    id: uuid.UUID
    status: StayStatus
    room: RoomRef
    guest: GuestRef
    arrival_date: date
    departure_date: date
    nights: int
    nightly_rate: Money
    billing_type: str
    billing_profile_id: uuid.UUID | None
    purchase_order: str | None
    traveller_name: str | None
    charges_blocked: bool
    is_training: bool
    checked_in_at: datetime | None
    checked_out_at: datetime | None
    folio: FolioSummary | None
    version: int


class StayList(BaseModel):
    data: list[StayOut]
    next_cursor: str | None = None
