"""Integrations, events, idempotency and audit."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Identity, text

from app.models.base import (
    ARRAY,
    INET,
    JSONB,
    UUID,
    Base,
    BigInteger,
    LargeBinary,
    Mapped,
    SmallInteger,
    Text,
    datetime,
    mapped_column,
    uuid,
)
from app.models.base import created_at as _created
from app.models.base import pk as _pk


class ApiKey(Base):
    __tablename__ = "api_keys"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    name: Mapped[str]
    environment: Mapped[str]
    prefix: Mapped[str]
    secret_hash: Mapped[bytes] = mapped_column(LargeBinary)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(Text))
    created_by: Mapped[uuid.UUID]
    created_at: Mapped[datetime] = _created()
    last_used_at: Mapped[datetime | None]
    usage_count: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    revoked_at: Mapped[datetime | None]


class Webhook(Base):
    __tablename__ = "webhooks"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    url: Mapped[str]
    events: Mapped[list[str]] = mapped_column(ARRAY(Text))
    secret_enc: Mapped[bytes] = mapped_column(LargeBinary)
    status: Mapped[str] = mapped_column(server_default=text("'active'"))
    failure_count: Mapped[int] = mapped_column(server_default=text("0"))
    created_at: Mapped[datetime] = _created()


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID]
    webhook_id: Mapped[uuid.UUID]
    event_id: Mapped[uuid.UUID]
    attempt: Mapped[int] = mapped_column(SmallInteger)
    status_code: Mapped[int | None] = mapped_column(SmallInteger)
    error: Mapped[str | None]
    next_attempt_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = _created()


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID | None]
    channel: Mapped[str]
    template: Mapped[str]
    recipient: Mapped[str]
    subject_ref: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    status: Mapped[str] = mapped_column(server_default=text("'queued'"))
    provider_message_id: Mapped[str | None]
    error: Mapped[str | None]
    created_at: Mapped[datetime] = _created()
    sent_at: Mapped[datetime | None]


class EventSeq(Base):
    __tablename__ = "event_seq"
    hotel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    last_seq: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))


class EventOutbox(Base):
    __tablename__ = "event_outbox"
    id: Mapped[uuid.UUID] = _pk()
    hotel_id: Mapped[uuid.UUID | None]
    seq: Mapped[int | None] = mapped_column(BigInteger)
    type: Mapped[str]
    channels: Mapped[list[str]] = mapped_column(ARRAY(Text))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _created()
    published_at: Mapped[datetime | None]
    attempts: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    principal_key: Mapped[str] = mapped_column(primary_key=True)
    key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    method: Mapped[str]
    path: Mapped[str]
    request_hash: Mapped[bytes] = mapped_column(LargeBinary)
    status: Mapped[str]
    response_code: Mapped[int | None] = mapped_column(SmallInteger)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _created()
    expires_at: Mapped[datetime] = mapped_column(server_default=text("now() + interval '24 hours'"))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    hotel_id: Mapped[uuid.UUID | None]
    actor_type: Mapped[str]
    actor_id: Mapped[uuid.UUID | None]
    actor_label: Mapped[str]
    action: Mapped[str]
    entity_type: Mapped[str]
    entity_id: Mapped[uuid.UUID | None]
    old_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    reason: Mapped[str | None]
    ip: Mapped[str | None] = mapped_column(INET)
    device_id: Mapped[uuid.UUID | None]
    request_id: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(primary_key=True, server_default=text("now()"))


class PiiColumn(Base):
    __tablename__ = "pii_columns"
    table_name: Mapped[str] = mapped_column(primary_key=True)
    column_name: Mapped[str] = mapped_column(primary_key=True)
    category: Mapped[str]
    anonymise_to: Mapped[str]
