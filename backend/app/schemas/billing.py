"""Folios, discounts and adjustments."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.schemas.common import Money, SignedMoney, StrictModel

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
