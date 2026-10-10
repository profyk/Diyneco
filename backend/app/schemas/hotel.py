"""Signup, hotel profile, settings, roles and permissions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from app.schemas.auth import Password
from app.schemas.common import Money, Name, StrictModel

Phone = Annotated[str, StringConstraints(max_length=40, pattern=r"^[0-9+() -]{6,40}$")]


class Address(StrictModel):
    line1: Annotated[str, StringConstraints(max_length=200)] | None = None
    line2: Annotated[str, StringConstraints(max_length=200)] | None = None
    city: Annotated[str, StringConstraints(max_length=100)] | None = None
    province: Annotated[str, StringConstraints(max_length=100)] | None = None
    postal_code: Annotated[str, StringConstraints(max_length=20)] | None = None
    country: Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")] | None = None


class SignupOwner(StrictModel):
    name: Name
    email: EmailStr
    password: Password


class CurrencyOut(BaseModel):
    code: str
    name: str
    symbol: str


class CurrencyList(BaseModel):
    data: list[CurrencyOut]


class SignupHotel(StrictModel):
    name: Name
    # The hotel's operating currency (ISO 4217), chosen at signup; no default (D57).
    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
    legal_name: Name | None = None
    phone: Phone | None = None
    email: EmailStr | None = None
    address: Address | None = None


class SignupRequest(StrictModel):
    owner: SignupOwner
    hotel: SignupHotel


class SignupResponse(BaseModel):
    status: str
    message: str


class PlanOut(BaseModel):
    code: str
    name: str
    subscription_status: str


class HotelOut(BaseModel):
    id: uuid.UUID
    name: str
    legal_name: str | None
    slug: str
    status: str
    address: dict[str, object]
    phone: str | None
    email: str | None
    logo_url: str | None
    country: str
    plan: PlanOut | None
    created_at: datetime
    version: int


class HotelPatch(StrictModel):
    name: Name | None = None
    legal_name: Name | None = None
    phone: Phone | None = None
    email: EmailStr | None = None
    address: Address | None = None


class SettingsOut(BaseModel):
    timezone: str
    currency: str
    vat_registered: bool
    vat_number: str | None
    vat_rate_bp: int
    accommodation_rates_include_vat: bool
    menu_prices_include_vat: bool
    room_charging_enabled: bool
    room_charge_auto_approve_limit: Money
    room_service_fee: Money
    checkout_override_allowed: bool
    room_status_after_checkout: Literal["cleaning", "available"]
    checkout_time: str
    wifi_name: str | None
    invoice_prefix: str
    abridged_invoice_max: Money
    guest_data_retention_days: int


class SettingsPatch(StrictModel):
    timezone: Annotated[str, StringConstraints(max_length=64)] | None = None
    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")] | None = None
    vat_registered: bool | None = None
    vat_number: Annotated[str, StringConstraints(pattern=r"^4\d{9}$")] | None = None
    vat_rate_bp: Annotated[int, Field(ge=0, le=10000)] | None = None
    accommodation_rates_include_vat: bool | None = None
    menu_prices_include_vat: bool | None = None
    room_charging_enabled: bool | None = None
    room_charge_auto_approve_limit: Money | None = None
    room_service_fee: Money | None = None
    checkout_override_allowed: bool | None = None
    room_status_after_checkout: Literal["cleaning", "available"] | None = None
    checkout_time: Annotated[str, StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")] | None = None
    wifi_name: Annotated[str, StringConstraints(max_length=64)] | None = None
    invoice_prefix: Annotated[str, StringConstraints(pattern=r"^[A-Z0-9]{2,8}$")] | None = None
    abridged_invoice_max: Money | None = None
    guest_data_retention_days: Annotated[int, Field(ge=365, le=3650)] | None = None


class PermissionOut(BaseModel):
    code: str
    description: str
    sensitive: bool


class PermissionList(BaseModel):
    data: list[PermissionOut]
    next_cursor: str | None = None


class RoleOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    is_system: bool
    permissions: list[str]


class RoleList(BaseModel):
    data: list[RoleOut]
    next_cursor: str | None = None


class LogoUploadRequest(StrictModel):
    content_type: Literal["image/png", "image/jpeg", "image/svg+xml"]
    size_bytes: Annotated[int, Field(ge=1, le=2 * 1024 * 1024, strict=True)]


class LogoUploadOut(BaseModel):
    upload_url: str
    method: str
    headers: dict[str, str]
    expires_at: datetime
    max_bytes: int


class OnboardingStep(BaseModel):
    key: str
    title: str
    done: bool


class OnboardingOut(BaseModel):
    steps: list[OnboardingStep]
    next_step: str | None
    completed: int
    total: int
