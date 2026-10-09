"""Deliveries and payments."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints, model_validator

from app.schemas.common import Money, StrictModel

PaymentMethod = Literal["card_terminal", "cash", "eft"]
TerminalRef = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9-]{4,20}$")]


class AssignRequest(StrictModel):
    user_id: uuid.UUID


class DeliveryOut(BaseModel):
    order_id: uuid.UUID
    number: int
    status: str
    room: str
    special_instructions: str | None
    items: list[dict[str, object]]
    amount_due: Money
    paid: bool
    assigned_to: dict[str, object] | None
    ready_at: datetime | None
    assigned_at: datetime | None
    picked_up_at: datetime | None
    delivered_at: datetime | None


class DeliveryList(BaseModel):
    data: list[DeliveryOut]
    next_cursor: str | None = None


class _Target(StrictModel):
    order_id: uuid.UUID | None = None
    stay_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _one(self) -> _Target:
        if (self.order_id is None) == (self.stay_id is None):
            raise ValueError("Send either order_id or stay_id.")
        return self


class PaymentPreviewRequest(_Target):
    amount_received: Money


class PaymentPreview(BaseModel):
    amount_due: Money
    amount_received: Money
    difference: Money
    tip: Money
    shortfall: Money
    status: Literal["paid", "partial"]


class PaymentRequest(_Target):
    method: PaymentMethod
    amount_received: Money
    confirm_tip: bool = False
    terminal_reference: TerminalRef | None = None
    occurred_at: datetime | None = None
    late_reason: Annotated[str, StringConstraints(min_length=3, max_length=300)] | None = None

    @model_validator(mode="after")
    def _terminal(self) -> PaymentRequest:
        if self.method == "card_terminal" and self.terminal_reference is None:
            raise ValueError("A card terminal payment needs the terminal_reference.")
        return self


class PaymentOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID | None
    stay_id: uuid.UUID
    method: str
    status: str
    amount_due: Money
    amount_received: Money
    tip: Money
    terminal_reference: str | None
    recorded_by: dict[str, object] | None
    occurred_at: datetime
    late_reason: str | None
    created_at: datetime


class PaymentList(BaseModel):
    data: list[PaymentOut]
    next_cursor: str | None = None
