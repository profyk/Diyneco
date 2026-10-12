"""Diyneco's company billing settings and tax rates (DECISIONS D72)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from app.schemas.common import StrictModel

Line = Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
Prefix = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9]{1,10}$")]


class Address(StrictModel):
    line1: Line | None = None
    line2: Line | None = None
    city: Line | None = None
    province: Line | None = None
    postal_code: Annotated[str, StringConstraints(strip_whitespace=True, max_length=12)] | None = None
    country: Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")] | None = None


class BankDetails(StrictModel):
    bank_name: Line | None = None
    account_holder: Line | None = None
    account_number: Annotated[str, StringConstraints(pattern=r"^\d{6,16}$")] | None = None
    branch_code: Annotated[str, StringConstraints(pattern=r"^\d{4,8}$")] | None = None
    account_type: Literal["cheque", "current", "savings", "business"] | None = None
    swift_code: Annotated[str, StringConstraints(pattern=r"^[A-Z0-9]{8}([A-Z0-9]{3})?$")] | None = None


class CompanySettingsOut(BaseModel):
    legal_name: str
    trading_name: str
    registration_number: str | None
    country: str
    currency: str
    timezone: str
    registered_address: Address
    business_address: Address
    billing_email: str | None
    billing_phone: str | None
    logo_url: str | None
    vat_registered: bool
    vat_number: str | None
    vat_effective_date: date | None
    invoice_prefix: str
    credit_note_prefix: str
    number_padding: int
    number_reset: Literal["never", "yearly"]
    payment_terms_days: int
    bank_details: BankDetails
    payment_instructions: str | None
    version: int
    updated_at: datetime
    # What an invoice issued today carries: "Tax invoice" with VAT, or a plain invoice.
    invoice_example: str
    tax_today: TaxToday
    missing: list[str]


class TaxToday(BaseModel):
    charged: bool
    tax_name: str | None
    rate_bp: int | None


class CompanySettingsPut(StrictModel):
    version: int
    reason: Reason
    legal_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=200)]
    trading_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    registration_number: Annotated[str, StringConstraints(strip_whitespace=True, max_length=40)] | None = None
    registered_address: Address = Field(default_factory=Address)
    business_address: Address = Field(default_factory=Address)
    billing_email: EmailStr | None = None
    billing_phone: Annotated[str, StringConstraints(pattern=r"^\+?[0-9 ()-]{7,30}$")] | None = None
    vat_registered: bool = False
    vat_number: Annotated[str, StringConstraints(strip_whitespace=True, max_length=30)] | None = None
    vat_effective_date: date | None = None
    invoice_prefix: Prefix = "INV"
    credit_note_prefix: Prefix = "CN"
    number_padding: Annotated[int, Field(ge=4, le=10)] = 6
    number_reset: Literal["never", "yearly"] = "never"
    payment_terms_days: Annotated[int, Field(ge=0, le=90)] = 7
    bank_details: BankDetails = Field(default_factory=BankDetails)
    payment_instructions: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] | None = (
        None
    )


class CompanyLogoUpload(StrictModel):
    content_type: Literal["image/png", "image/jpeg"]
    size_bytes: Annotated[int, Field(ge=1, le=1024 * 1024, strict=True)]


class TaxRateOut(BaseModel):
    id: uuid.UUID
    country: str
    tax_name: str
    category: Literal["standard", "zero_rated", "exempt"]
    rate_bp: int
    effective_from: date
    reason: str
    created_at: datetime
    in_force: bool
    scheduled: bool


class TaxRateList(BaseModel):
    data: list[TaxRateOut]


class TaxRateCreate(StrictModel):
    country: Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
    tax_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=30)]
    rate_bp: Annotated[int, Field(ge=0, le=10000, strict=True)]
    effective_from: date
    reason: Reason


CompanySettingsOut.model_rebuild()
