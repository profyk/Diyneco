"""Orders, quotes and the guest tablet's views."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import Money, SignedMoney, StrictModel
from app.schemas.hotel import InfoPage

OrderStatus = Literal[
    "PENDING_APPROVAL",
    "NEW",
    "ACCEPTED",
    "PREPARING",
    "READY",
    "ASSIGNED",
    "PICKED_UP",
    "DELIVERED",
    "CLOSED",
    "DECLINED",
    "CANCELLED",
]
PaymentMethod = Literal["room_charge", "card_terminal", "cash"]
Note = Annotated[str, StringConstraints(max_length=200)]
Reason = Annotated[str, StringConstraints(max_length=300)]


class CartLine(StrictModel):
    menu_item_id: uuid.UUID
    # Bounds are checked by the service so that oversize carts get ORDER_TOO_LARGE.
    quantity: Annotated[int, Field(ge=1, le=10_000, strict=True)]
    modifier_option_ids: Annotated[list[uuid.UUID], Field(max_length=30)] = Field(default_factory=list)
    note: Note | None = None


class QuoteRequest(StrictModel):
    lines: Annotated[list[CartLine], Field(min_length=1, max_length=500)]


class PlaceOrder(QuoteRequest):
    special_instructions: Annotated[str, StringConstraints(max_length=500)] | None = None
    payment_method: Literal["room_charge"] = "room_charge"
    quoted_total: Money


class StaffQuote(QuoteRequest):
    """Price a cart for a room before a staff phone order (same server pricing as the tablet)."""

    room_id: uuid.UUID


class StaffOrder(QuoteRequest):
    room_id: uuid.UUID
    special_instructions: Annotated[str, StringConstraints(max_length=500)] | None = None
    payment_method: PaymentMethod = "room_charge"
    quoted_total: Money
    late_reason: Reason | None = None


class QuoteModifier(BaseModel):
    id: uuid.UUID
    group: str
    name: str
    price_delta: Money


class QuoteLine(BaseModel):
    menu_item_id: uuid.UUID
    name: str
    quantity: int
    unit_price: Money
    line_total: Money
    modifiers: list[QuoteModifier]
    note: str | None


class Quote(BaseModel):
    lines: list[QuoteLine]
    subtotal: Money
    fee: Money
    total: Money
    vat_included: Money
    needs_approval: bool


class ReasonBody(StrictModel):
    reason: Reason


class OrderPlaced(BaseModel):
    id: uuid.UUID
    number: int
    status: OrderStatus
    room: str
    subtotal: Money
    fee: Money
    total: Money
    vat_included: Money
    created_at: datetime


class OrderItemOut(BaseModel):
    id: uuid.UUID
    name: str
    quantity: int
    unit_price: Money
    line_total: Money
    station_id: uuid.UUID
    prep_status: str
    note: str | None
    modifiers: list[dict[str, object]]


class HistoryOut(BaseModel):
    from_status: str | None
    to_status: str
    at: datetime


class OrderOut(BaseModel):
    id: uuid.UUID
    number: int
    status: OrderStatus
    room: str
    room_id: uuid.UUID
    stay_id: uuid.UUID
    payment_method: PaymentMethod
    special_instructions: str | None
    subtotal: Money
    fee: Money
    total: Money
    vat_included: Money
    needs_approval: bool
    decline_reason: str | None
    placed_by: Literal["guest", "staff"]
    items: list[OrderItemOut]
    history: list[HistoryOut]
    created_at: datetime


class OrderList(BaseModel):
    data: list[OrderOut]
    next_cursor: str | None = None


# --- Guest tablet --------------------------------------------------------------------------


class GuestSession(BaseModel):
    state: Literal["active", "idle", "locked", "suspended"]
    ordering_enabled: bool
    hotel: dict[str, object]
    room: dict[str, object]
    stay: dict[str, object] | None


class GuestMenuItem(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    price: Money
    image_url: str | None
    dietary_tags: list[str]
    allergens: list[str]
    ingredients: list[str]
    available_now: bool
    next_available_at: datetime | None
    modifier_groups: list[dict[str, object]]


class GuestMenuCategory(BaseModel):
    id: uuid.UUID
    name: str
    items: list[GuestMenuItem]


class GuestMenu(BaseModel):
    categories: list[GuestMenuCategory]


class FolioLineOut(BaseModel):
    description: str
    amount: SignedMoney
    date: date


class GuestFolio(BaseModel):
    accommodation: list[FolioLineOut]
    food_and_beverage: list[FolioLineOut]
    other: list[FolioLineOut]
    payments: list[FolioLineOut]
    tips: list[FolioLineOut]
    totals: dict[str, SignedMoney]


class GuestInfo(BaseModel):
    hotel_name: str
    wifi_name: str | None
    checkout_time: time
    phone: str | None
    email: str | None
    pages: list[InfoPage]
