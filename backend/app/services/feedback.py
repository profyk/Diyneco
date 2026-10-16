"""Guest feedback (D98): stars and a comment for a delivered order, a finished request or the
stay, from the room's tablet during the stay. One rating per thing; a low rating (1 or 2
stars) reaches managers at once through the ops channel. Comments never enter events, audit
entries or webhooks, and are redacted when the guest is anonymised."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.domain import GuestFeedback, Order, Room, ServiceRequest, Stay
from app.realtime.outbox import emit, hotel_channel

RATEABLE_ORDER = ("DELIVERED", "CLOSED")
LOW = 2


def view(f: GuestFeedback) -> dict[str, Any]:
    return {
        "id": f.id,
        "subject": f.subject,
        "order_id": f.order_id,
        "request_id": f.request_id,
        "rating": f.rating,
        "comment": f.comment,
        "created_at": f.created_at,
    }


async def for_stay(uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = await uow.session.execute(
        select(GuestFeedback)
        .where(GuestFeedback.hotel_id == ctx.hotel_id, GuestFeedback.stay_id == stay_id)
        .order_by(GuestFeedback.created_at)
    )
    return [view(f) for f in rows.scalars()]


async def give(uow: UnitOfWork, ctx: TenantContext, stay: Stay, body: dict[str, Any]) -> dict[str, Any]:
    s = uow.session
    room_number = (
        await s.execute(select(Room.number).where(Room.hotel_id == ctx.hotel_id, Room.id == stay.room_id))
    ).scalar_one()
    if body["subject"] == "order":
        order = (
            await s.execute(select(Order).where(Order.hotel_id == ctx.hotel_id, Order.id == body["order_id"]))
        ).scalar_one_or_none()
        if order is None or order.stay_id != stay.id:
            raise AppError("NOT_FOUND")
        if order.status not in RATEABLE_ORDER:
            raise AppError("INVALID_TRANSITION", "You can rate an order once it has been delivered.")
    elif body["subject"] == "request":
        req = (
            await s.execute(
                select(ServiceRequest).where(
                    ServiceRequest.hotel_id == ctx.hotel_id, ServiceRequest.id == body["request_id"]
                )
            )
        ).scalar_one_or_none()
        if req is None or req.stay_id != stay.id:
            raise AppError("NOT_FOUND")
        if req.status != "done":
            raise AppError("INVALID_TRANSITION", "You can rate a request once it is done.")
    f = GuestFeedback(
        hotel_id=ctx.hotel_id,
        stay_id=stay.id,
        room_id=stay.room_id,
        room_number=room_number,
        subject=body["subject"],
        order_id=body.get("order_id"),
        request_id=body.get("request_id"),
        rating=body["rating"],
        comment=body.get("comment"),
    )
    try:
        async with s.begin_nested():
            s.add(f)
            await s.flush()
    except IntegrityError as exc:
        raise AppError("INVALID_TRANSITION", "Thank you, you have already rated this.") from exc
    await s.refresh(f)
    await emit(
        s,
        ctx,
        "FEEDBACK_RECEIVED",
        [hotel_channel(ctx.hotel_id, "ops")],
        {
            "feedback_id": str(f.id),
            "room": room_number,
            "subject": f.subject,
            "rating": f.rating,
            "low": f.rating <= LOW,
        },
    )
    return view(f)


async def report(uow: UnitOfWork, ctx: TenantContext, date_from: date, date_to: date) -> dict[str, Any]:
    if date_to < date_from or (date_to - date_from).days > 366:
        raise AppError("VALIDATION_FAILED", "Choose a range of up to a year.")
    p = {"h": ctx.hotel_id, "f": date_from, "t": date_to}
    window = (
        "FROM app.guest_feedback g JOIN app.hotel_settings hs ON hs.hotel_id = g.hotel_id "
        "WHERE g.hotel_id = :h AND (g.created_at AT TIME ZONE hs.timezone)::date BETWEEN :f AND :t "
    )
    s = uow.session
    stars = {
        int(r.rating): int(r.n)
        for r in await s.execute(text(f"SELECT g.rating, count(*) AS n {window}GROUP BY 1"), p)
    }
    subjects = (
        await s.execute(text(f"SELECT g.subject, count(*) AS n, avg(g.rating) AS a {window}GROUP BY 1"), p)
    ).all()
    recent = (
        await s.execute(
            text(
                f"SELECT g.id, g.room_number, g.subject, g.rating, g.comment, g.created_at {window}"
                "ORDER BY (g.comment IS NULL), g.created_at DESC LIMIT 50"
            ),
            p,
        )
    ).all()
    total = sum(stars.values())
    return {
        "from": date_from,
        "to": date_to,
        "ratings": total,
        "average": round(sum(k * v for k, v in stars.items()) / total, 2) if total else None,
        "distribution": [stars.get(i, 0) for i in range(1, 6)],
        "by_subject": [
            {
                "subject": r.subject,
                "ratings": int(r.n),
                "average": round(float(r.a), 2) if r.a is not None else None,
            }
            for r in subjects
        ],
        "recent": [
            {
                "id": r.id,
                "room": r.room_number,
                "subject": r.subject,
                "rating": int(r.rating),
                "comment": r.comment,
                "created_at": r.created_at,
            }
            for r in recent
        ],
    }
