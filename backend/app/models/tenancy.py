"""Platform and tenancy; identity and access."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from app.models.base import (
    ARRAY,
    CHAR,
    CITEXT,
    INET,
    JSONB,
    UUID,
    Base,
    BigInteger,
    Integer,
    LargeBinary,
    Mapped,
    SmallInteger,
    Text,
    date,
    datetime,
    mapped_column,
    time,
    uuid,
)
from app.models.base import created_at as _created
from app.models.base import currency as _currency
from app.models.base import pk as _pk
from app.models.base import updated_at as _updated
from app.models.base import version as _version


class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[uuid.UUID] = _pk()
    code: Mapped[str]
    name: Mapped[str]
    currency: Mapped[str] = _currency()
    short_description: Mapped[str | None]
    description: Mapped[str | None]
    highlights: Mapped[list[str]] = mapped_column(JSONB, server_default=text("'[]'"))
    status: Mapped[str] = mapped_column(server_default=text("'draft'"))
    display_order: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    recommended: Mapped[bool] = mapped_column(server_default=text("false"))
    setup_fee_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    trial_days: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    tax_treatment: Mapped[str] = mapped_column(server_default=text("'exclusive'"))
    support_level: Mapped[str | None]
    overage_policy: Mapped[str | None]
    can_upgrade: Mapped[bool] = mapped_column(server_default=text("true"))
    can_downgrade: Mapped[bool] = mapped_column(server_default=text("true"))
    promo_discount_bp: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    promo_ends_on: Mapped[date | None]
    limits: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    published_at: Mapped[datetime | None]
    archived_at: Mapped[datetime | None]
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class PlanPrice(Base):
    """A plan's price for one billing interval from a moment on (append-only, D74)."""

    __tablename__ = "plan_prices"
    id: Mapped[uuid.UUID] = _pk()
    plan_id: Mapped[uuid.UUID]
    interval: Mapped[str]
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(CHAR(3))
    intro_amount_minor: Mapped[int | None] = mapped_column(BigInteger)
    intro_periods: Mapped[int | None] = mapped_column(Integer)
    effective_from: Mapped[datetime]
    existing_policy: Mapped[str]
    notice_days: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[str]
    created_by: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = _created()
    withdrawn_at: Mapped[datetime | None]


class BillingSettings(Base):
    """Platform billing policies (one row, D74; later slices add trial, grace and reminders)."""

    __tablename__ = "billing_settings"
    id: Mapped[bool] = mapped_column(primary_key=True, server_default=text("true"))
    price_change_notice_days: Mapped[int] = mapped_column(Integer)
    trial_days: Mapped[int] = mapped_column(Integer)
    trial_limits: Mapped[dict[str, Any]] = mapped_column(JSONB)
    reminder_offsets: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    grace_days: Mapped[int] = mapped_column(Integer)
    renewal_lead_days: Mapped[int] = mapped_column(Integer)
    suspend_after_grace: Mapped[bool]
    read_only_when_suspended: Mapped[bool]
    proration_enabled: Mapped[bool]
    card_provider: Mapped[str]
    eft_enabled: Mapped[bool]
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    updated_at: Mapped[datetime] = _updated()
    updated_by: Mapped[uuid.UUID | None]


class Hotel(Base):
    __tablename__ = "hotels"
    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str]
    legal_name: Mapped[str | None]
    slug: Mapped[str]
    code: Mapped[str] = mapped_column(server_default=text("app.new_hotel_code()"))  # Hotel ID (D82)
    status: Mapped[str] = mapped_column(server_default=text("'pending_approval'"))
    status_reason: Mapped[str | None]
    address: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    phone: Mapped[str | None]
    email: Mapped[str | None]
    logo_path: Mapped[str | None]
    country: Mapped[str] = mapped_column(CHAR(2))
    data_region: Mapped[str]
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    version: Mapped[int] = _version()


class HotelSettings(Base):
    __tablename__ = "hotel_settings"
    hotel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    timezone: Mapped[str] = mapped_column(server_default=text("'Africa/Johannesburg'"))
    currency: Mapped[str] = _currency()
    locale: Mapped[str]
    tax_label: Mapped[str]
    vat_registered: Mapped[bool] = mapped_column(server_default=text("false"))
    vat_number: Mapped[str | None]
    vat_rate_bp: Mapped[int] = mapped_column(server_default=text("1500"))
    accommodation_rates_include_vat: Mapped[bool] = mapped_column(server_default=text("false"))
    menu_prices_include_vat: Mapped[bool] = mapped_column(server_default=text("true"))
    room_charging_enabled: Mapped[bool] = mapped_column(server_default=text("true"))
    room_charge_auto_limit_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("50000"))
    room_service_fee_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    checkout_override_allowed: Mapped[bool] = mapped_column(server_default=text("false"))
    room_status_after_checkout: Mapped[str] = mapped_column(server_default=text("'cleaning'"))
    checkout_time: Mapped[time] = mapped_column(server_default=text("'10:00'"))
    wifi_name: Mapped[str | None]
    info_pages: Mapped[list[dict[str, str]]] = mapped_column(JSONB, server_default=text("'[]'"))
    invoice_prefix: Mapped[str]
    abridged_invoice_max_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("500000"))
    guest_id_number_enabled: Mapped[bool] = mapped_column(server_default=text("false"))
    guest_data_retention_days: Mapped[int] = mapped_column(server_default=text("1825"))
    updated_at: Mapped[datetime] = _updated()
    version: Mapped[int] = _version()


class Subscription(Base):
    """A hotel's subscription (D76). A trial may have no plan; a sold subscription keeps the
    price agreed when it was sold, whatever the plan's price does later."""

    __tablename__ = "subscriptions"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    plan_id: Mapped[uuid.UUID | None]
    status: Mapped[str]
    starts_on: Mapped[date]
    renews_on: Mapped[date | None]
    cancelled_at: Mapped[datetime | None]
    limit_overrides: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    interval: Mapped[str | None]
    plan_price_id: Mapped[uuid.UUID | None]
    amount_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str | None] = mapped_column(CHAR(3))
    intro_amount_minor: Mapped[int | None] = mapped_column(BigInteger)
    intro_periods_left: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    tax_treatment: Mapped[str | None]
    anchor_day: Mapped[int | None] = mapped_column(SmallInteger)
    current_period_start: Mapped[date | None]
    trial_ends_on: Mapped[date | None]
    cancel_reason: Mapped[str | None]
    ended_on: Mapped[date | None]
    pending_plan_id: Mapped[uuid.UUID | None]
    pending_plan_price_id: Mapped[uuid.UUID | None]
    pending_interval: Mapped[str | None]
    past_due_since: Mapped[date | None]
    suspended_at: Mapped[datetime | None]
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class SubscriptionBillingContact(Base):
    """Who Diyneco bills for a hotel's subscription (D76); invoices copy it when issued."""

    __tablename__ = "subscription_billing_contacts"
    hotel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    legal_name: Mapped[str | None]
    vat_number: Mapped[str | None]
    billing_email: Mapped[str | None] = mapped_column(CITEXT)
    phone: Mapped[str | None]
    contact_name: Mapped[str | None]
    address: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    updated_at: Mapped[datetime] = _updated()
    updated_by: Mapped[uuid.UUID | None]


class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    # No primary key in the schema; (key, hotel_id) is unique NULLS NOT DISTINCT.
    key: Mapped[str] = mapped_column(primary_key=True)
    hotel_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=True)
    enabled: Mapped[bool]
    updated_at: Mapped[datetime] = _updated()
    updated_by: Mapped[uuid.UUID | None]


class SupportGrant(Base):
    """Time-boxed (max 60 minutes), ticketed read access for platform support; visible to the
    hotel and audited (DECISIONS D48)."""

    __tablename__ = "support_grants"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    platform_user_id: Mapped[uuid.UUID]
    ticket_reference: Mapped[str]
    reason: Mapped[str | None]
    starts_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    revoked_by: Mapped[uuid.UUID | None]


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _pk()
    email: Mapped[str] = mapped_column(CITEXT)
    name: Mapped[str]
    password_hash: Mapped[str | None]
    email_verified_at: Mapped[datetime | None]
    is_platform: Mapped[bool] = mapped_column(server_default=text("false"))
    status: Mapped[str] = mapped_column(server_default=text("'active'"))
    failed_logins: Mapped[int] = mapped_column(server_default=text("0"))
    failed_window_start: Mapped[datetime | None]
    locked_until: Mapped[datetime | None]
    last_login_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class MfaFactor(Base):
    __tablename__ = "mfa_factors"
    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID]
    kind: Mapped[str]
    secret_enc: Mapped[bytes] = mapped_column(LargeBinary)
    confirmed_at: Mapped[datetime | None]
    last_used_step: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = _created()


class MfaRecoveryCode(Base):
    __tablename__ = "mfa_recovery_codes"
    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID]
    code_hash: Mapped[bytes] = mapped_column(LargeBinary)
    used_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = _created()


class DataKey(Base):
    __tablename__ = "data_keys"
    scope: Mapped[str] = mapped_column(primary_key=True)
    wrapped_key: Mapped[bytes] = mapped_column(LargeBinary)
    kms_key_id: Mapped[str]
    created_at: Mapped[datetime] = _created()


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID]
    family_id: Mapped[uuid.UUID]
    active_hotel_id: Mapped[uuid.UUID | None]
    refresh_hash: Mapped[bytes] = mapped_column(LargeBinary)
    device_id: Mapped[uuid.UUID | None]
    user_agent: Mapped[str | None]
    ip: Mapped[str | None] = mapped_column(INET)
    amr: Mapped[list[str]] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = _created()
    last_used_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    revoked_reason: Mapped[str | None]


class Permission(Base):
    __tablename__ = "permissions"
    code: Mapped[str] = mapped_column(primary_key=True)
    scope: Mapped[str]
    description: Mapped[str]
    sensitive: Mapped[bool] = mapped_column(server_default=text("false"))


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID | None]
    code: Mapped[str]
    name: Mapped[str]
    is_system: Mapped[bool] = mapped_column(server_default=text("false"))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    permission_code: Mapped[str] = mapped_column(Text, primary_key=True)


class HotelUser(Base):
    __tablename__ = "hotel_users"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID]
    department: Mapped[str | None]
    pin_hash: Mapped[str | None]
    pin_failed: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    pin_failed_window_start: Mapped[datetime | None]
    pin_locked_until: Mapped[datetime | None]
    staff_code_hash: Mapped[bytes | None] = mapped_column(LargeBinary)
    staff_code_set_at: Mapped[datetime | None]
    perms_version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    status: Mapped[str] = mapped_column(server_default=text("'active'"))
    created_at: Mapped[datetime] = _created()
    deactivated_at: Mapped[datetime | None]


class UserRole(Base):
    __tablename__ = "user_roles"
    hotel_id: Mapped[uuid.UUID]
    hotel_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    granted_by: Mapped[uuid.UUID | None]
    granted_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class PlatformUserRole(Base):
    __tablename__ = "platform_user_roles"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)


class Invitation(Base):
    __tablename__ = "invitations"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    email: Mapped[str] = mapped_column(CITEXT)
    name: Mapped[str]
    department: Mapped[str | None]
    role_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    token_hash: Mapped[bytes] = mapped_column(LargeBinary)
    invited_by: Mapped[uuid.UUID]
    expires_at: Mapped[datetime]
    accepted_at: Mapped[datetime | None]
    cancelled_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = _created()


class OneTimeToken(Base):
    __tablename__ = "one_time_tokens"
    token_hash: Mapped[bytes] = mapped_column(LargeBinary, primary_key=True)
    user_id: Mapped[uuid.UUID]
    purpose: Mapped[str]
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]


class LegalDocument(Base):
    """A version of a legal document (control plane, no hotel). Published versions are frozen."""

    __tablename__ = "legal_documents"
    id: Mapped[uuid.UUID] = _pk()
    kind: Mapped[str]
    country: Mapped[str | None] = mapped_column(CHAR(2))
    version: Mapped[int]
    title: Mapped[str]
    body: Mapped[str]
    summary: Mapped[str | None]
    status: Mapped[str] = mapped_column(server_default=text("'draft'"))
    effective_at: Mapped[datetime | None]
    published_at: Mapped[datetime | None]
    published_by: Mapped[uuid.UUID | None]
    created_by: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class LegalAcceptance(Base):
    """One person accepting one document version for one hotel (append-only)."""

    __tablename__ = "legal_acceptances"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    document_id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID]
    accepted_at: Mapped[datetime] = _created()
    ip: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None]


class CompanySettings(Base):
    """Diyneco's own identity as the seller of subscriptions (one row, control plane, D72)."""

    __tablename__ = "company_settings"
    id: Mapped[bool] = mapped_column(primary_key=True, server_default=text("true"))
    legal_name: Mapped[str]
    trading_name: Mapped[str]
    registration_number: Mapped[str | None]
    country: Mapped[str] = mapped_column(CHAR(2))
    currency: Mapped[str] = mapped_column(CHAR(3))
    timezone: Mapped[str]
    registered_address: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    business_address: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    billing_email: Mapped[str | None] = mapped_column(CITEXT)
    billing_phone: Mapped[str | None]
    logo_path: Mapped[str | None]
    vat_registered: Mapped[bool] = mapped_column(server_default=text("false"))
    vat_number: Mapped[str | None]
    vat_effective_date: Mapped[date | None]
    invoice_prefix: Mapped[str]
    credit_note_prefix: Mapped[str]
    number_padding: Mapped[int] = mapped_column(Integer)
    number_reset: Mapped[str]
    payment_terms_days: Mapped[int] = mapped_column(Integer)
    bank_details: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    payment_instructions: Mapped[str | None]
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    updated_at: Mapped[datetime] = _updated()
    updated_by: Mapped[uuid.UUID | None]


class TaxRate(Base):
    """A tax rate in force from a date (append-only; the latest row on or before a day applies)."""

    __tablename__ = "tax_rates"
    id: Mapped[uuid.UUID] = _pk()
    country: Mapped[str] = mapped_column(CHAR(2))
    tax_name: Mapped[str]
    category: Mapped[str]
    rate_bp: Mapped[int] = mapped_column(Integer)
    effective_from: Mapped[date]
    reason: Mapped[str]
    created_by: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = _created()


class SubscriptionInvoice(Base):
    """Diyneco's invoice or credit note to a hotel (D78). Frozen once issued."""

    __tablename__ = "subscription_invoices"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    subscription_id: Mapped[uuid.UUID | None]
    kind: Mapped[str]
    credits_invoice_id: Mapped[uuid.UUID | None]
    number: Mapped[str | None]
    status: Mapped[str] = mapped_column(server_default=text("'draft'"))
    is_tax_invoice: Mapped[bool] = mapped_column(server_default=text("false"))
    currency: Mapped[str] = mapped_column(CHAR(3))
    subtotal_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    tax_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    total_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    tax_name: Mapped[str | None]
    tax_rate_bp: Mapped[int | None] = mapped_column(Integer)
    period_start: Mapped[date | None]
    period_end: Mapped[date | None]
    issued_at: Mapped[datetime | None]
    due_on: Mapped[date | None]
    seller: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    buyer: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    payment_instructions: Mapped[str | None]
    notes: Mapped[str | None]
    pdf_path: Mapped[str | None]
    purpose: Mapped[str] = mapped_column(server_default=text("'manual'"))
    plan_id: Mapped[uuid.UUID | None]
    created_by: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class SubscriptionInvoiceLine(Base):
    __tablename__ = "subscription_invoice_lines"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    invoice_id: Mapped[uuid.UUID]
    position: Mapped[int] = mapped_column(Integer)
    code: Mapped[str]
    description: Mapped[str]
    quantity: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    unit_amount_minor: Mapped[int] = mapped_column(BigInteger)
    discount_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    tax_minor: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    total_minor: Mapped[int] = mapped_column(BigInteger)


class SubscriptionInvoiceEvent(Base):
    __tablename__ = "subscription_invoice_events"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    invoice_id: Mapped[uuid.UUID]
    status_from: Mapped[str | None]
    status_to: Mapped[str]
    reason: Mapped[str | None]
    actor_type: Mapped[str]
    actor_id: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = _created()


class SubscriptionInvoiceSequence(Base):
    """Counter per kind, prefix and year (0: running), advanced only through
    app.next_subscription_invoice_number (D78)."""

    __tablename__ = "subscription_invoice_sequences"
    kind: Mapped[str] = mapped_column(primary_key=True)
    prefix: Mapped[str] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    next_number: Mapped[int] = mapped_column(BigInteger)


class SubscriptionPaymentAttempt(Base):
    """A checkout with a payment provider for an invoice (D79): pending until its status is
    verified on the server, then final."""

    __tablename__ = "subscription_payment_attempts"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    invoice_id: Mapped[uuid.UUID]
    provider: Mapped[str]
    test_mode: Mapped[bool]
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(CHAR(3))
    provider_ref: Mapped[str | None]
    checkout_url: Mapped[str | None]
    status: Mapped[str] = mapped_column(server_default=text("'pending'"))
    failure_reason: Mapped[str | None]
    created_by: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    completed_at: Mapped[datetime | None]


class SubscriptionPayment(Base):
    """Money received for a subscription invoice (D79). Only reconciliation changes."""

    __tablename__ = "subscription_payments"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    invoice_id: Mapped[uuid.UUID]
    attempt_id: Mapped[uuid.UUID | None]
    method: Mapped[str]
    provider: Mapped[str]
    test_mode: Mapped[bool] = mapped_column(server_default=text("false"))
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(CHAR(3))
    reference: Mapped[str | None]
    provider_payment_id: Mapped[str | None]
    received_on: Mapped[date]
    notes: Mapped[str | None]
    reconciliation_status: Mapped[str] = mapped_column(server_default=text("'unreconciled'"))
    reconciled_at: Mapped[datetime | None]
    reconciled_by: Mapped[uuid.UUID | None]
    reconciliation_note: Mapped[str | None]
    recorded_by: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class SubscriptionRefund(Base):
    """Money given back against a credit note (append-only, D79)."""

    __tablename__ = "subscription_refunds"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    payment_id: Mapped[uuid.UUID]
    credit_note_id: Mapped[uuid.UUID]
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(CHAR(3))
    method: Mapped[str]
    provider_refund_id: Mapped[str | None]
    reference: Mapped[str | None]
    test_mode: Mapped[bool] = mapped_column(server_default=text("false"))
    reason: Mapped[str]
    created_by: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = _created()


class SubscriptionBillingEvent(Base):
    """A billing lifecycle step (renewal, reminder, suspension, ...); the dedupe key makes
    each one happen once (append-only, D79)."""

    __tablename__ = "subscription_billing_events"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    subscription_id: Mapped[uuid.UUID | None]
    invoice_id: Mapped[uuid.UUID | None]
    kind: Mapped[str]
    dedupe_key: Mapped[str | None]
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    created_at: Mapped[datetime] = _created()


class BillingWebhookEvent(Base):
    """A payment provider's webhook, stored once per provider and event id (control plane,
    written only through app.billing_webhook_record and app.billing_webhook_done)."""

    __tablename__ = "billing_webhook_events"
    id: Mapped[uuid.UUID] = _pk()
    provider: Mapped[str]
    event_id: Mapped[str]
    event_type: Mapped[str | None]
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    received_at: Mapped[datetime] = _created()
    processed_at: Mapped[datetime | None]
    outcome: Mapped[str | None]
    error: Mapped[str | None]
