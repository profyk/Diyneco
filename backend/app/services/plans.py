"""Plan limits (rooms, devices, staff, api_keys). Limits are data on app.plans, never code.

Counts: rooms not deleted; devices not revoked; staff = active members plus pending,
unexpired invitations (an invitation reserves a seat, so accepting one never breaks a limit).
"""

from __future__ import annotations

from typing import Literal

from sqlalchemy import text

from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.repositories.hotels import HotelRepository

Resource = Literal["rooms", "devices", "staff", "api_keys"]

_COUNT_SQL: dict[str, str] = {
    "rooms": "SELECT count(*) FROM app.rooms WHERE hotel_id = :h AND deleted_at IS NULL",
    "devices": "SELECT count(*) FROM app.devices WHERE hotel_id = :h AND status <> 'revoked'",
    "staff": (
        "SELECT (SELECT count(*) FROM app.hotel_users WHERE hotel_id = :h AND status = 'active')"
        " + (SELECT count(*) FROM app.invitations WHERE hotel_id = :h AND accepted_at IS NULL"
        "    AND cancelled_at IS NULL AND expires_at > now())"
    ),
    "api_keys": "SELECT count(*) FROM app.api_keys WHERE hotel_id = :h AND revoked_at IS NULL",
}


async def ensure_capacity(uow: UnitOfWork, ctx: TenantContext, resource: Resource, adding: int = 1) -> None:
    plan = await HotelRepository(uow.session, ctx).current_plan()
    if plan is None:
        raise AppError("PLAN_LIMIT_REACHED", "This hotel has no active plan.", details={"resource": resource})
    limit = plan[0].limits.get(resource)
    if limit is None:
        return  # no limit configured for this resource
    current = int((await uow.session.execute(text(_COUNT_SQL[resource]), {"h": ctx.hotel_id})).scalar_one())
    if current + adding > int(limit):
        raise AppError(
            "PLAN_LIMIT_REACHED",
            f"Your plan allows {limit} {resource.replace('_', ' ')}.",
            details={"resource": resource, "limit": int(limit), "current": current, "requested": adding},
        )
