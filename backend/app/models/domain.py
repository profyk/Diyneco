"""Property and devices, guests and folios, menu, orders, payments and invoices."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Identity, text

from app.models.base import (
    ARRAY,
    CHAR,
    CITEXT,
    INET,
    JSONB,
    UUID,
    Base,
    BigInteger,
    LargeBinary,
    Mapped,
    SmallInteger,
    date,
    datetime,
    mapped_column,
    text_array,
    uuid,
)
from app.models.base import created_at as _created
from app.models.base import currency as _currency
from app.models.base import pk as _pk
from app.models.base import updated_at as _updated
from app.models.base import version as _version

# --- Property and devices ------------------------------------------------------------------


class RoomType(Base):
    __tablename__ = "room_types"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    name: Mapped[str]
    base_rate_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = _currency()
    capacity: Mapped[int] = mapped_column(SmallInteger, server_default=text("2"))
    amenities: Mapped[list[str]] = text_array()
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    deleted_at: Mapped[datetime | None]
    version: Mapped[int] = _version()


class Room(Base):
    __tablename__ = "rooms"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    room_type_id: Mapped[uuid.UUID]
    number: Mapped[str]
    floor: Mapped[str | None]
    rate_minor: Mapped[int | None] = mapped_column(BigInteger)
    capacity: Mapped[int | None] = mapped_column(SmallInteger)
    amenities: Mapped[list[str]] = text_array()
    status: Mapped[str] = mapped_column(server_default=text("'available'"))
    status_changed_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    deleted_at: Mapped[datetime | None]
    version: Mapped[int] = _version()


class KitchenStation(Base):
    __tablename__ = "kitchen_stations"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    name: Mapped[str]
    sort_order: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    label: Mapped[str]
    kind: Mapped[str]
    room_id: Mapped[uuid.UUID | None]
    credential_hash: Mapped[bytes | None] = mapped_column(LargeBinary)
    status: Mapped[str] = mapped_column(server_default=text("'active'"))
    os: Mapped[str | None]
    app_version: Mapped[str | None]
    last_seen_at: Mapped[datetime | None]
    last_ip: Mapped[str | None] = mapped_column(INET)
    paired_at: Mapped[datetime | None]
    revoked_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class DeviceStation(Base):
    __tablename__ = "device_stations"
    hotel_id: Mapped[uuid.UUID]
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    station_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)


class DevicePairing(Base):
    __tablename__ = "device_pairings"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    kind: Mapped[str]
    room_id: Mapped[uuid.UUID | None]
    station_ids: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID(as_uuid=True)))
    code_hash: Mapped[bytes] = mapped_column(LargeBinary)
    created_by: Mapped[uuid.UUID]
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]
    used_by_device: Mapped[uuid.UUID | None]
    attempts: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    created_at: Mapped[datetime] = _created()


# --- Guests, stays and folios --------------------------------------------------------------


class Guest(Base):
    __tablename__ = "guests"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    full_name: Mapped[str]
    email: Mapped[str | None] = mapped_column(CITEXT)
    phone: Mapped[str | None]
    id_number_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    nationality: Mapped[str | None] = mapped_column(CHAR(2))
    anonymised_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class BillingProfile(Base):
    __tablename__ = "billing_profiles"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    company_name: Mapped[str]
    registration_number: Mapped[str | None]
    vat_number: Mapped[str | None]
    billing_address: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    billing_email: Mapped[str | None] = mapped_column(CITEXT)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class Stay(Base):
    __tablename__ = "stays"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    room_id: Mapped[uuid.UUID]
    guest_id: Mapped[uuid.UUID]
    billing_type: Mapped[str] = mapped_column(server_default=text("'personal'"))
    billing_profile_id: Mapped[uuid.UUID | None]
    purchase_order: Mapped[str | None]
    traveller_name: Mapped[str | None]
    status: Mapped[str] = mapped_column(server_default=text("'reserved'"))
    arrival_date: Mapped[date]
    departure_date: Mapped[date]
    nightly_rate_minor: Mapped[int] = mapped_column(BigInteger)
    rate_override_reason: Mapped[str | None]
    currency: Mapped[str] = _currency()
    charges_blocked: Mapped[bool] = mapped_column(server_default=text("false"))
    is_training: Mapped[bool] = mapped_column(server_default=text("false"))
    checked_in_at: Mapped[datetime | None]
    checked_in_by: Mapped[uuid.UUID | None]
    checked_out_at: Mapped[datetime | None]
    checked_out_by: Mapped[uuid.UUID | None]
    checkout_override_reason: Mapped[str | None]
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    version: Mapped[int] = _version()


class Folio(Base):
    __tablename__ = "folios"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    stay_id: Mapped[uuid.UUID]
    status: Mapped[str] = mapped_column(server_default=text("'open'"))
    currency: Mapped[str] = _currency()
    closed_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = _created()


class ChargeCategory(Base):
    __tablename__ = "charge_categories"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID | None]
    code: Mapped[str]
    name: Mapped[str]
    revenue_group: Mapped[str]
    vat_rate_bp: Mapped[int | None]
    is_revenue: Mapped[bool]


class FolioEntry(Base):
    __tablename__ = "folio_entries"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    folio_id: Mapped[uuid.UUID]
    entry_type: Mapped[str]
    category_id: Mapped[uuid.UUID]
    description: Mapped[str]
    quantity: Mapped[int] = mapped_column(server_default=text("1"))
    unit_amount_minor: Mapped[int] = mapped_column(BigInteger)
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    vat_rate_bp: Mapped[int] = mapped_column(server_default=text("0"))
    vat_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    currency: Mapped[str] = _currency()
    business_date: Mapped[date]
    order_id: Mapped[uuid.UUID | None]
    payment_id: Mapped[uuid.UUID | None]
    reverses_entry_id: Mapped[uuid.UUID | None]
    adjustment_id: Mapped[uuid.UUID | None]
    created_by: Mapped[uuid.UUID | None]
    created_by_device: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = _created()


class Adjustment(Base):
    __tablename__ = "adjustments"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    folio_id: Mapped[uuid.UUID]
    target_entry_id: Mapped[uuid.UUID | None]
    order_id: Mapped[uuid.UUID | None]
    original_minor: Mapped[int] = mapped_column(BigInteger)
    new_minor: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[str]
    status: Mapped[str] = mapped_column(server_default=text("'pending'"))
    requested_by: Mapped[uuid.UUID]
    requested_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    decided_by: Mapped[uuid.UUID | None]
    decided_at: Mapped[datetime | None]
    decision_note: Mapped[str | None]


class Discount(Base):
    __tablename__ = "discounts"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    folio_id: Mapped[uuid.UUID]
    kind: Mapped[str]
    percent_bp: Mapped[int | None]
    amount_minor: Mapped[int | None] = mapped_column(BigInteger)
    applies_to: Mapped[str]
    reason: Mapped[str]
    created_by: Mapped[uuid.UUID]
    created_at: Mapped[datetime] = _created()


# --- Menu ----------------------------------------------------------------------------------


class MenuSchedule(Base):
    __tablename__ = "menu_schedules"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    name: Mapped[str]
    windows: Mapped[list[Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class MenuCategory(Base):
    __tablename__ = "menu_categories"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    name: Mapped[str]
    sort_order: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    schedule_id: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    deleted_at: Mapped[datetime | None]


class MenuItem(Base):
    __tablename__ = "menu_items"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    category_id: Mapped[uuid.UUID]
    station_id: Mapped[uuid.UUID]
    charge_category_code: Mapped[str] = mapped_column(server_default=text("'food'"))
    name: Mapped[str]
    description: Mapped[str | None]
    price_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = _currency()
    vat_rate_bp: Mapped[int | None]
    schedule_id: Mapped[uuid.UUID | None]
    is_available: Mapped[bool] = mapped_column(server_default=text("true"))
    dietary_tags: Mapped[list[str]] = text_array()
    allergens: Mapped[list[str]] = text_array()
    image_path: Mapped[str | None]
    image_variants: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    sort_order: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    deleted_at: Mapped[datetime | None]
    version: Mapped[int] = _version()


class MenuModifierGroup(Base):
    __tablename__ = "menu_modifier_groups"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    name: Mapped[str]
    min_select: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    max_select: Mapped[int] = mapped_column(SmallInteger, server_default=text("1"))
    created_at: Mapped[datetime] = _created()
    deleted_at: Mapped[datetime | None]


class MenuModifier(Base):
    __tablename__ = "menu_modifiers"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    group_id: Mapped[uuid.UUID]
    name: Mapped[str]
    price_delta_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    is_available: Mapped[bool] = mapped_column(server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    deleted_at: Mapped[datetime | None]


class MenuItemModifier(Base):
    __tablename__ = "menu_item_modifiers"
    hotel_id: Mapped[uuid.UUID]
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    sort_order: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))


# --- Orders and deliveries -----------------------------------------------------------------


class OrderNumberSequence(Base):
    __tablename__ = "order_number_sequences"
    hotel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    next_number: Mapped[int] = mapped_column(BigInteger, server_default=text("10001"))


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    number: Mapped[int] = mapped_column(BigInteger)
    stay_id: Mapped[uuid.UUID]
    room_id: Mapped[uuid.UUID]
    room_number: Mapped[str]
    device_id: Mapped[uuid.UUID | None]
    placed_by_user: Mapped[uuid.UUID | None]
    late_reason: Mapped[str | None]
    status: Mapped[str]
    payment_method: Mapped[str] = mapped_column(server_default=text("'room_charge'"))
    special_instructions: Mapped[str | None]
    subtotal_minor: Mapped[int] = mapped_column(BigInteger)
    fee_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    total_minor: Mapped[int] = mapped_column(BigInteger)
    vat_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    currency: Mapped[str] = _currency()
    needs_approval: Mapped[bool] = mapped_column(server_default=text("false"))
    approved_by: Mapped[uuid.UUID | None]
    approved_at: Mapped[datetime | None]
    decline_reason: Mapped[str | None]
    posted_to_folio: Mapped[bool] = mapped_column(server_default=text("false"))
    locked_at: Mapped[datetime | None]
    accepted_at: Mapped[datetime | None]
    ready_at: Mapped[datetime | None]
    closed_at: Mapped[datetime | None]
    idempotency_key: Mapped[uuid.UUID]
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    order_id: Mapped[uuid.UUID]
    menu_item_id: Mapped[uuid.UUID | None]
    station_id: Mapped[uuid.UUID]
    name: Mapped[str]
    description: Mapped[str | None]
    charge_category_code: Mapped[str]
    unit_price_minor: Mapped[int] = mapped_column(BigInteger)
    quantity: Mapped[int]
    line_total_minor: Mapped[int] = mapped_column(BigInteger)
    vat_rate_bp: Mapped[int]
    vat_minor: Mapped[int] = mapped_column(BigInteger)
    note: Mapped[str | None]
    prep_status: Mapped[str] = mapped_column(server_default=text("'PENDING'"))
    ready_at: Mapped[datetime | None]
    ready_by: Mapped[uuid.UUID | None]


class OrderItemModifier(Base):
    __tablename__ = "order_item_modifiers"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    order_item_id: Mapped[uuid.UUID]
    modifier_id: Mapped[uuid.UUID | None]
    group_name: Mapped[str]
    name: Mapped[str]
    price_delta_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    hotel_id: Mapped[uuid.UUID]
    order_id: Mapped[uuid.UUID]
    from_status: Mapped[str | None]
    to_status: Mapped[str]
    actor_user: Mapped[uuid.UUID | None]
    actor_device: Mapped[uuid.UUID | None]
    note: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(primary_key=True, server_default=text("now()"))


class Delivery(Base):
    __tablename__ = "deliveries"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    order_id: Mapped[uuid.UUID]
    assigned_to: Mapped[uuid.UUID | None]
    assigned_by: Mapped[uuid.UUID | None]
    assigned_at: Mapped[datetime | None]
    picked_up_at: Mapped[datetime | None]
    delivered_at: Mapped[datetime | None]
    released_count: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))


# --- Payments, tips and invoices -----------------------------------------------------------


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    folio_id: Mapped[uuid.UUID]
    order_id: Mapped[uuid.UUID | None]
    method: Mapped[str]
    status: Mapped[str]
    amount_due_minor: Mapped[int] = mapped_column(BigInteger)
    amount_received_minor: Mapped[int] = mapped_column(BigInteger)
    tip_amount_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    currency: Mapped[str] = _currency()
    provider: Mapped[str | None]
    provider_reference: Mapped[str | None]
    external_transaction_id: Mapped[str | None]
    recorded_by: Mapped[uuid.UUID | None]
    recorded_by_device: Mapped[uuid.UUID | None]
    occurred_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    late_reason: Mapped[str | None]
    idempotency_key: Mapped[uuid.UUID]
    created_at: Mapped[datetime] = _created()


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    payment_id: Mapped[uuid.UUID]
    folio_entry_id: Mapped[uuid.UUID]
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = _created()


class Tip(Base):
    __tablename__ = "tips"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    payment_id: Mapped[uuid.UUID]
    folio_entry_id: Mapped[uuid.UUID]
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    staff_user_id: Mapped[uuid.UUID | None]
    confirmed_by: Mapped[uuid.UUID]
    confirmed_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class InvoiceSequence(Base):
    __tablename__ = "invoice_sequences"
    hotel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    year: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    next_number: Mapped[int] = mapped_column(server_default=text("1"))


class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    folio_id: Mapped[uuid.UUID]
    number: Mapped[str]
    kind: Mapped[str]
    credits_invoice_id: Mapped[uuid.UUID | None]
    issued_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    supplier: Mapped[dict[str, Any]] = mapped_column(JSONB)
    recipient: Mapped[dict[str, Any]] = mapped_column(JSONB)
    totals: Mapped[dict[str, Any]] = mapped_column(JSONB)
    currency: Mapped[str] = _currency()
    pdf_path: Mapped[str | None]
    pdf_sha256: Mapped[bytes | None] = mapped_column(LargeBinary)
    created_by: Mapped[uuid.UUID | None]


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    invoice_id: Mapped[uuid.UUID]
    folio_entry_id: Mapped[uuid.UUID | None]
    line_no: Mapped[int] = mapped_column(SmallInteger)
    category: Mapped[str]
    description: Mapped[str]
    quantity: Mapped[int]
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    vat_rate_bp: Mapped[int]
    vat_minor: Mapped[int] = mapped_column(BigInteger)


class DailyClose(Base):
    __tablename__ = "daily_closes"
    hotel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    business_date: Mapped[date] = mapped_column(primary_key=True)
    terminal_batch_total_minor: Mapped[int | None] = mapped_column(BigInteger)
    cash_counted_minor: Mapped[int | None] = mapped_column(BigInteger)
    card_recorded_minor: Mapped[int | None] = mapped_column(BigInteger)
    cash_recorded_minor: Mapped[int | None] = mapped_column(BigInteger)
    flags: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'"))
    notes: Mapped[str | None]
    reviewed_by: Mapped[uuid.UUID | None]
    reviewed_at: Mapped[datetime | None]
