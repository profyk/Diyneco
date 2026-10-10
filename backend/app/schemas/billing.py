"""Folios, discounts and adjustments."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, EmailStr, Field, StringConstraints, model_validator

from app.schemas.common import Money, SignedMoney, StrictModel
from app.schemas.hotel import Address

Reason = Annotated[str, StringConstraints(min_length=1, max_length=500)]


class ChargeRequest(StrictModel):
    charge_category_id: uuid.UUID
    description: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    amount: Money
    quantity: Annotated[int, Field(ge=1, le=1000, strict=True)] = 1


class DiscountRequest(StrictModel):
    kind: Literal["percent", "fixed"]
    percent_bp: Annotated[int, Field(ge=1, le=10000, strict=True)] | None = None
    amount: Money | None = None
    applies_to: Literal["accommodation", "fnb", "other", "all"]
    reason: Reason

    @model_validator(mode="after")
    def _shape(self) -> DiscountRequest:
        if self.kind == "percent" and (self.percent_bp is None or self.amount is not None):
            raise ValueError("A percent discount takes percent_bp only.")
        if self.kind == "fixed" and (self.amount is None or self.percent_bp is not None):
            raise ValueError("A fixed discount takes amount only.")
        if self.amount is not None and self.amount.amount_minor <= 0:
            raise ValueError("A discount must be above zero.")
        return self


class AdjustmentRequest(StrictModel):
    folio_entry_id: uuid.UUID | None = None
    order_id: uuid.UUID | None = None
    new_amount: Money
    reason: Annotated[str, StringConstraints(min_length=3, max_length=500)]

    @model_validator(mode="after")
    def _one(self) -> AdjustmentRequest:
        if (self.folio_entry_id is None) == (self.order_id is None):
            raise ValueError("Send either folio_entry_id or order_id.")
        return self


class RejectRequest(StrictModel):
    reason: Reason


class FolioEntryOut(BaseModel):
    id: uuid.UUID
    type: str
    category: str
    group: str
    description: str
    quantity: int
    unit_amount: SignedMoney
    amount: SignedMoney
    vat: SignedMoney
    business_date: date
    order_id: uuid.UUID | None
    payment_id: uuid.UUID | None
    reverses_entry_id: uuid.UUID | None
    created_at: datetime


class FolioTotals(BaseModel):
    accommodation: SignedMoney
    fnb: SignedMoney
    other: SignedMoney
    vat_included: SignedMoney
    tips: SignedMoney
    paid: SignedMoney
    balance: SignedMoney


class FolioOut(BaseModel):
    stay_id: uuid.UUID
    folio_id: uuid.UUID
    status: str
    entries: list[FolioEntryOut]
    totals: FolioTotals
    by_category: dict[str, SignedMoney]


class AdjustmentOut(BaseModel):
    id: uuid.UUID
    folio_id: uuid.UUID
    target_entry_id: uuid.UUID | None
    order_id: uuid.UUID | None
    original: SignedMoney
    new_amount: SignedMoney
    reason: str
    status: str
    requested_by: uuid.UUID
    requested_at: datetime
    decided_by: uuid.UUID | None
    decided_at: datetime | None
    decision_note: str | None


BillDelivery = Literal["pdf", "email"]


def _pdf_only() -> list[BillDelivery]:
    return ["pdf"]


class ChargeCategoryOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    group: str
    vat_rate_bp: int | None


class ChargeCategoryList(BaseModel):
    data: list[ChargeCategoryOut]
    next_cursor: str | None = None


class AdjustmentListItem(AdjustmentOut):
    stay_id: uuid.UUID
    room: str
    requested_by_name: str | None


class AdjustmentList(BaseModel):
    data: list[AdjustmentListItem]
    next_cursor: str | None = None


class CheckoutRequest(StrictModel):
    override: bool = False
    override_reason: Reason | None = None
    bill_delivery: list[BillDelivery] = Field(default_factory=_pdf_only, max_length=2)
    email_to: list[EmailStr] = Field(default_factory=list, max_length=5)
    recipient_address: Address | None = None
    confirm_long_stay_vat: bool = False


class OpenOrder(BaseModel):
    id: uuid.UUID
    number: int
    status: str


class CheckoutSummary(BaseModel):
    stay_id: uuid.UUID
    stay_status: str
    folio_status: str
    totals: FolioTotals
    by_category: dict[str, SignedMoney]
    open_orders: list[OpenOrder]
    can_check_out: bool
    override_allowed: bool
    invoice_kind: str
    flags: list[str]


class InvoiceTotals(BaseModel):
    accommodation: SignedMoney
    fnb: SignedMoney
    other: SignedMoney
    charges: SignedMoney
    vat_included: SignedMoney
    tips: SignedMoney
    paid: SignedMoney
    balance: SignedMoney


class InvoiceItemOut(BaseModel):
    line_no: int
    category: str
    description: str
    quantity: int
    amount: SignedMoney
    vat_rate_bp: int
    vat: SignedMoney


class InvoiceOut(BaseModel):
    id: uuid.UUID
    number: str
    kind: str
    title: str
    stay_id: uuid.UUID
    folio_id: uuid.UUID
    credits_invoice_id: uuid.UUID | None
    issued_at: datetime
    supplier: dict[str, Any]
    recipient: dict[str, Any]
    totals: InvoiceTotals
    by_category: dict[str, SignedMoney]
    flags: list[str]
    reason: str | None
    items: list[InvoiceItemOut]
    sha256: str | None


class InvoiceList(BaseModel):
    data: list[InvoiceOut]
    next_cursor: str | None = None


class CheckoutOut(BaseModel):
    stay_id: uuid.UUID
    status: str
    override_reason: str | None
    invoice: InvoiceOut
    emailed_to: list[str]


class InvoiceEmailRequest(StrictModel):
    to: Annotated[list[EmailStr], Field(min_length=1, max_length=5)]


class InvoiceEmailOut(BaseModel):
    invoice_id: uuid.UUID
    queued_to: list[str]


class SignedUrl(BaseModel):
    url: str
    expires_in: int


class CreditNoteRequest(StrictModel):
    reason: Annotated[str, StringConstraints(min_length=3, max_length=500)]
