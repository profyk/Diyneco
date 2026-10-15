"""Guest service requests (D93): towels, cleaning, a repair, a wake-up call.

A room's tablet asks during the active stay; staff can also log one for a room (a phone call
or a request at the desk). open -> acknowledged -> in_progress -> done, or cancelled before
done; a trigger enforces the moves. The guest may cancel only while nobody has taken it yet.
Events carry ids and the room number only; the note stays in the database.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select, text, update

from app.audit.writer import write_audit
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.domain import Room, ServiceRequest, Stay
from app.models.tenancy import HotelUser, RolePermission, User, UserRole
from app.realtime.outbox import emit, hotel_channel
from app.repositories.stays import StayRepository

LIVE = ("open", "acknowledged", "in_progress")
MAX_OPEN_PER_ROOM = 10
DUE_PAST_GRACE = timedelta(minutes=5)
DUE_HORIZON = timedelta(days=14)


def _check_due(kind: str, due_at: datetime | None) -> None:
    if kind == "wake_up" and due_at is None:
        raise AppError(
            "VALIDATION_FAILED", "Choose a time for the wake-up call.", details={"field": "due_at"}
        )
    if due_at is None:
        return
    if due_at.tzinfo is None:
        raise AppError("VALIDATION_FAILED", "Send the time with its time zone.", details={"field": "due_at"})
    now = datetime.now(UTC)
    if due_at < now - DUE_PAST_GRACE or due_at > now + DUE_HORIZON:
        raise AppError(
            "VALIDATION_FAILED", "Choose a time within the next two weeks.", details={"field": "due_at"}
        )


async def _names(uow: UnitOfWork, ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
    if not ids:
        return {}
    rows = await uow.session.execute(select(User.id, User.name).where(User.id.in_(ids)))
    return {i: n for i, n in rows.all()}


def guest_view(r: ServiceRequest) -> dict[str, Any]:
    return {
        "id": r.id,
        "kind": r.kind,
        "note": r.note,
        "due_at": r.due_at,
        "status": r.status,
        "created_at": r.created_at,
        "acknowledged_at": r.acknowledged_at,
        "completed_at": r.completed_at,
        "cancelled_at": r.cancelled_at,
    }


async def staff_view(uow: UnitOfWork, rows: list[ServiceRequest]) -> list[dict[str, Any]]:
    names = await _names(uow, {i for r in rows for i in (r.created_by, r.assigned_to) if i})
    now = datetime.now(UTC)
    out = []
    for r in rows:
        end = r.completed_at or r.cancelled_at or now
        out.append(
            {
                **guest_view(r),
                "room_id": r.room_id,
                "room": r.room_number,
                "stay_id": r.stay_id,
                "source": r.source,
                "created_by": {"id": r.created_by, "name": names.get(r.created_by, "")}
                if r.created_by
                else None,
                "assigned_to": {"id": r.assigned_to, "name": names.get(r.assigned_to, "")}
                if r.assigned_to
                else None,
                "started_at": r.started_at,
                "cancelled_by": r.cancelled_by,
                "cancel_reason": r.cancel_reason,
                "waiting_minutes": max(0, int((end - r.created_at).total_seconds() // 60)),
            }
        )
    return out


async def _event(uow: UnitOfWork, ctx: TenantContext, r: ServiceRequest, event: str) -> None:
    await emit(
        uow.session,
        ctx,
        event,
        [hotel_channel(ctx.hotel_id, "requests"), hotel_channel(ctx.hotel_id, f"room:{r.room_id}")],
        {"request_id": str(r.id), "room": r.room_number, "kind": r.kind, "status": r.status},
    )


async def _open_for_room(uow: UnitOfWork, ctx: TenantContext, room_id: uuid.UUID) -> int:
    return int(
        (
            await uow.session.execute(
                select(func.count())
                .select_from(ServiceRequest)
                .where(
                    ServiceRequest.hotel_id == ctx.hotel_id,
                    ServiceRequest.room_id == room_id,
                    ServiceRequest.status.in_(LIVE),
                )
            )
        ).scalar_one()
    )


async def _create(
    uow: UnitOfWork,
    ctx: TenantContext,
    room: Room,
    stay: Stay | None,
    body: dict[str, Any],
    *,
    source: str,
    device_id: uuid.UUID | None,
) -> ServiceRequest:
    _check_due(body["kind"], body.get("due_at"))
    if await _open_for_room(uow, ctx, room.id) >= MAX_OPEN_PER_ROOM:
        raise AppError(
            "VALIDATION_FAILED",
            "This room already has 10 requests waiting. Please wait for the team to finish some.",
        )
    r = ServiceRequest(
        hotel_id=ctx.hotel_id,
        room_id=room.id,
        room_number=room.number,
        stay_id=stay.id if stay else None,
        kind=body["kind"],
        note=body.get("note"),
        due_at=body.get("due_at"),
        source=source,
        created_by=ctx.actor_id if source == "staff" else None,
        device_id=device_id,
    )
    uow.session.add(r)
    await uow.session.flush()
    await uow.session.refresh(r)
    await write_audit(
        uow.session,
        ctx,
        "request.create",
        "service_request",
        r.id,
        new_value={"kind": r.kind, "source": source},
    )
    await _event(uow, ctx, r, "REQUEST_CREATED")
    return r


async def create_from_room(
    uow: UnitOfWork,
    ctx: TenantContext,
    room_id: uuid.UUID,
    stay: Stay,
    device_id: uuid.UUID,
    body: dict[str, Any],
) -> dict[str, Any]:
    room = await _room(uow, ctx, room_id)
    return guest_view(await _create(uow, ctx, room, stay, body, source="guest", device_id=device_id))


async def create_by_staff(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    room = await _room(uow, ctx, body["room_id"])
    stay = await StayRepository(uow.session, ctx).live_stay_for_room(room.id)
    r = await _create(
        uow,
        ctx,
        room,
        stay if stay is not None and stay.status == "active" else None,
        body,
        source="staff",
        device_id=None,
    )
    return (await staff_view(uow, [r]))[0]


async def _room(uow: UnitOfWork, ctx: TenantContext, room_id: uuid.UUID) -> Room:
    room = (
        await uow.session.execute(
            select(Room).where(Room.hotel_id == ctx.hotel_id, Room.id == room_id, Room.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if room is None:
        raise AppError("NOT_FOUND")
    return room


async def for_stay(uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = (
        await uow.session.execute(
            select(ServiceRequest)
            .where(ServiceRequest.hotel_id == ctx.hotel_id, ServiceRequest.stay_id == stay_id)
            .order_by(ServiceRequest.created_at.desc())
            .limit(100)
        )
    ).scalars()
    return [guest_view(r) for r in rows]


async def _locked(uow: UnitOfWork, ctx: TenantContext, request_id: uuid.UUID) -> ServiceRequest:
    r = (
        await uow.session.execute(
            select(ServiceRequest)
            .where(ServiceRequest.hotel_id == ctx.hotel_id, ServiceRequest.id == request_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if r is None:
        raise AppError("NOT_FOUND")
    return r


async def _move(
    uow: UnitOfWork, ctx: TenantContext, r: ServiceRequest, values: dict[str, Any], action: str
) -> ServiceRequest:
    old = r.status
    await uow.session.execute(update(ServiceRequest).where(ServiceRequest.id == r.id).values(**values))
    await uow.session.refresh(r)
    await write_audit(
        uow.session,
        ctx,
        action,
        "service_request",
        r.id,
        old_value={"status": old},
        new_value={k: str(v) for k, v in values.items() if k in ("status", "assigned_to")},
    )
    await _event(uow, ctx, r, "REQUEST_UPDATED")
    return r


def _not_from(r: ServiceRequest, *allowed: str) -> None:
    if r.status not in allowed:
        raise AppError("INVALID_TRANSITION", details={"status": r.status})


async def acknowledge(uow: UnitOfWork, ctx: TenantContext, request_id: uuid.UUID) -> dict[str, Any]:
    r = await _locked(uow, ctx, request_id)
    _not_from(r, "open")
    r = await _move(
        uow,
        ctx,
        r,
        {
            "status": "acknowledged",
            "acknowledged_at": datetime.now(UTC),
            "assigned_to": r.assigned_to or ctx.actor_id,
        },
        "request.acknowledge",
    )
    return (await staff_view(uow, [r]))[0]


async def start(uow: UnitOfWork, ctx: TenantContext, request_id: uuid.UUID) -> dict[str, Any]:
    r = await _locked(uow, ctx, request_id)
    _not_from(r, "open", "acknowledged")
    now = datetime.now(UTC)
    r = await _move(
        uow,
        ctx,
        r,
        {
            "status": "in_progress",
            "started_at": now,
            "acknowledged_at": r.acknowledged_at or now,
            "assigned_to": ctx.actor_id,
        },
        "request.start",
    )
    return (await staff_view(uow, [r]))[0]


async def complete(uow: UnitOfWork, ctx: TenantContext, request_id: uuid.UUID) -> dict[str, Any]:
    r = await _locked(uow, ctx, request_id)
    _not_from(r, *LIVE)
    now = datetime.now(UTC)
    r = await _move(
        uow,
        ctx,
        r,
        {
            "status": "done",
            "completed_at": now,
            "acknowledged_at": r.acknowledged_at or now,
            "assigned_to": r.assigned_to or ctx.actor_id,
        },
        "request.done",
    )
    return (await staff_view(uow, [r]))[0]


async def assign(
    uow: UnitOfWork, ctx: TenantContext, request_id: uuid.UUID, user_id: uuid.UUID
) -> dict[str, Any]:
    target = (
        await uow.session.execute(
            select(HotelUser.id)
            .join(UserRole, UserRole.hotel_user_id == HotelUser.id)
            .join(RolePermission, RolePermission.role_id == UserRole.role_id)
            .where(
                HotelUser.hotel_id == ctx.hotel_id,
                HotelUser.user_id == user_id,
                HotelUser.status == "active",
                RolePermission.permission_code == "requests.update",
            )
        )
    ).first()
    if target is None:
        raise AppError("NOT_FOUND", "That person cannot handle requests.")
    r = await _locked(uow, ctx, request_id)
    _not_from(r, *LIVE)
    values: dict[str, Any] = {"assigned_to": user_id}
    if r.status == "open":
        values |= {"status": "acknowledged", "acknowledged_at": datetime.now(UTC)}
    r = await _move(uow, ctx, r, values, "request.assign")
    return (await staff_view(uow, [r]))[0]


async def cancel_by_staff(
    uow: UnitOfWork, ctx: TenantContext, request_id: uuid.UUID, reason: str | None
) -> dict[str, Any]:
    r = await _locked(uow, ctx, request_id)
    _not_from(r, *LIVE)
    r = await _move(
        uow,
        ctx,
        r,
        {
            "status": "cancelled",
            "cancelled_at": datetime.now(UTC),
            "cancelled_by": "staff",
            "cancel_reason": reason,
        },
        "request.cancel",
    )
    return (await staff_view(uow, [r]))[0]


async def cancel_by_guest(
    uow: UnitOfWork, ctx: TenantContext, request_id: uuid.UUID, stay_id: uuid.UUID
) -> dict[str, Any]:
    r = await _locked(uow, ctx, request_id)
    if r.stay_id != stay_id:
        raise AppError("NOT_FOUND")  # another stay's request does not exist for this guest
    if r.status != "open":
        raise AppError(
            "INVALID_TRANSITION",
            "The team is already on it. Call reception to change it.",
            details={"status": r.status},
        )
    r = await _move(
        uow,
        ctx,
        r,
        {"status": "cancelled", "cancelled_at": datetime.now(UTC), "cancelled_by": "guest"},
        "request.cancel",
    )
    return guest_view(r)


async def list_requests(
    uow: UnitOfWork,
    ctx: TenantContext,
    *,
    scope: str,
    kind: str | None,
    room_id: uuid.UUID | None,
    limit: int,
) -> list[dict[str, Any]]:
    q = select(ServiceRequest).where(ServiceRequest.hotel_id == ctx.hotel_id)
    if scope == "open":
        q = q.where(ServiceRequest.status.in_(LIVE)).order_by(ServiceRequest.created_at)
    elif scope == "mine":
        q = q.where(ServiceRequest.status.in_(LIVE), ServiceRequest.assigned_to == ctx.actor_id).order_by(
            ServiceRequest.created_at
        )
    else:  # recent: the last 7 days, newest first
        q = q.where(ServiceRequest.created_at >= datetime.now(UTC) - timedelta(days=7)).order_by(
            ServiceRequest.created_at.desc()
        )
    if kind:
        q = q.where(ServiceRequest.kind == kind)
    if room_id:
        q = q.where(ServiceRequest.room_id == room_id)
    rows = list((await uow.session.execute(q.limit(limit))).scalars())
    return await staff_view(uow, rows)


async def summary(uow: UnitOfWork, ctx: TenantContext) -> dict[str, Any]:
    row = (
        await uow.session.execute(
            text(
                """
                SELECT
                  count(*) FILTER (WHERE r.status IN ('open', 'acknowledged')) AS open,
                  count(*) FILTER (WHERE r.status = 'in_progress') AS in_progress,
                  count(*) FILTER (WHERE r.status = 'done'
                    AND (r.completed_at AT TIME ZONE s.timezone)::date
                      = (now() AT TIME ZONE s.timezone)::date) AS done_today,
                  percentile_cont(0.5) WITHIN GROUP (
                    ORDER BY extract(epoch FROM r.completed_at - r.created_at) / 60
                  ) FILTER (WHERE r.status = 'done' AND r.completed_at > now() - interval '7 days') AS median
                FROM app.service_requests r
                JOIN app.hotel_settings s ON s.hotel_id = r.hotel_id
                WHERE r.hotel_id = :h AND (r.status IN ('open', 'acknowledged', 'in_progress')
                  OR r.created_at > now() - interval '8 days')
                """
            ),
            {"h": ctx.hotel_id},
        )
    ).one()
    return {
        "open": int(row.open or 0),
        "in_progress": int(row.in_progress or 0),
        "done_today": int(row.done_today or 0),
        "median_minutes_to_done": round(row.median) if row.median is not None else None,
    }
