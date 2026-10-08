"""Audit writer. Every sensitive action records actor, hotel, action, entity, old and new
value, time, and device or IP, in the same transaction as the change itself."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import TenantContext
from app.models.events import AuditLog


async def write_audit(
    session: AsyncSession,
    ctx: TenantContext,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    *,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    reason: str | None = None,
) -> None:
    await session.execute(
        insert(AuditLog).values(
            hotel_id=ctx.hotel_id,
            actor_type=ctx.actor_type,
            actor_id=ctx.actor_id,
            actor_label=ctx.actor_label,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            ip=ctx.ip,
            device_id=ctx.device_id,
            request_id=ctx.request_id,
        )
    )


async def write_platform_audit(
    session: AsyncSession,
    *,
    actor_type: str,
    actor_id: uuid.UUID | None,
    actor_label: str,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    ip: str | None,
    request_id: str | None,
    new_value: dict[str, Any] | None = None,
) -> None:
    """Platform-level entries (hotel_id NULL), e.g. login security events. The app roles can
    write these but never read them back (RLS)."""
    await session.execute(
        insert(AuditLog).values(
            hotel_id=None,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            new_value=new_value,
            ip=ip,
            request_id=request_id,
        )
    )
