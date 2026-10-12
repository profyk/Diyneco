"""Diyneco's invoices and credit notes to hotels (DECISIONS D78)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import SignedMoney, StrictModel

Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
Amount = Annotated[int, Field(ge=0, le=10**12, strict=True)]


class InvoiceLineOut(BaseModel):
    position: int
    code: str
    description: str
    quantity: int
    unit_amount_minor: int
    discount_minor: int
    tax_minor: int
    total_minor: int


class SubscriptionInvoiceOut(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    kind: Literal["invoice", "credit_note"]
    number: str | None
    status: Literal["draft", "issued", "partially_paid", "paid", "overdue", "void", "credited"]
    is_tax_invoice: bool
    currency: str
    subtotal: SignedMoney
    tax: SignedMoney
    total: SignedMoney
    paid: SignedMoney
    credited: SignedMoney
    balance: SignedMoney
    tax_name: str | None
    tax_rate_bp: int | None
    period_start: date | None
    period_end: date | None
    issued_at: datetime | None
    due_on: date | None
    credits_invoice_id: uuid.UUID | None
    credits_number: str | None
    seller: dict[str, Any]
    buyer: dict[str, Any]
    notes: str | None
    has_pdf: bool
    lines: list[InvoiceLineOut]


class SubscriptionInvoiceList(BaseModel):
    data: list[SubscriptionInvoiceOut]


class DraftLine(StrictModel):
    code: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,39}$")] = "charge"
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    quantity: Annotated[int, Field(ge=1, le=10000, strict=True)] = 1
    unit_amount_minor: Amount
    discount_minor: Amount = 0


class DraftCreate(StrictModel):
    """A manual invoice for an approved charge. Amounts are minor units of `currency`."""

    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
    prices_include_tax: bool = False
    lines: Annotated[list[DraftLine], Field(min_length=1, max_length=50)]
    period_start: date | None = None
    period_end: date | None = None
    notes: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] | None = None
    reason: Reason


class VoidRequest(StrictModel):
    reason: Reason


class CreditRequest(StrictModel):
    reason: Reason
    # Left out: the whole amount still creditable. Includes tax.
    amount_minor: Annotated[int, Field(ge=1, le=10**12, strict=True)] | None = None


class PdfLink(BaseModel):
    url: str


class SentOut(BaseModel):
    recipients: int
