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
    monthly_price_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = _currency()
    limits: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class Hotel(Base):
    __tablename__ = "hotels"
    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str]
    legal_name: Mapped[str | None]
    slug: Mapped[str]
    status: Mapped[str] = mapped_column(server_default=text("'pending_approval'"))
    status_reason: Mapped[str | None]
    address: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    phone: Mapped[str | None]
    email: Mapped[str | None]
    logo_path: Mapped[str | None]
    country: Mapped[str] = mapped_column(CHAR(2), server_default=text("'ZA'"))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    version: Mapped[int] = _version()


class HotelSettings(Base):
    __tablename__ = "hotel_settings"
    hotel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    timezone: Mapped[str] = mapped_column(server_default=text("'Africa/Johannesburg'"))
    currency: Mapped[str] = _currency()
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
    __tablename__ = "subscriptions"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    plan_id: Mapped[uuid.UUID]
    status: Mapped[str]
    starts_on: Mapped[date]
    renews_on: Mapped[date | None]
    cancelled_at: Mapped[datetime | None]
    limit_overrides: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


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
