"""Guests, billing profiles, reservations, check-in and walk-ins (API spec, Guests, stays and
check-in).

Check-in runs in one transaction: it opens the folio, posts every night's accommodation up
front (VAT per the hotel's settings), sets the stay active and the room occupied, and tells
the room's tablet that a guest arrived.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.audit.writer import write_audit
from app.billing.folio import FolioLedger, Line, business_date
from app.billing.vat import gross_and_vat
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.domain import Guest, Room, Stay
from app.realtime.outbox import emit, hotel_channel
from app.repositories.hotels import HotelRepository
from app.repositories.rooms import RoomRepository, RoomTypeRepository
from app.repositories.stays import LIVE, StayRepository

CHECK_IN_ROOM_STATUSES = ("available", "reserved")


def money(amount: int, currency: str) -> dict[str, Any]:
    return {"amount_minor": amount, "currency": currency}


def _field_error(field: str, problem: str, code: str = "VALIDATION_FAILED") -> AppError:
    return AppError(
        code, problem, details={"fields": [{"field": field, "problem": problem, "type": "value_error"}]}
    )


async def _settings(uow: UnitOfWork, ctx: TenantContext) -> Any:
    st = await HotelRepository(uow.session, ctx).get_settings()
    if st is None:
        raise AppError("NOT_FOUND")
    return st


# --- Guests --------------------------------------------------------------------------------


def guest_payload(g: Guest) -> dict[str, Any]:
    return {
        "id": g.id,
        "name": g.full_name,
        "email": g.email,
        "phone": g.phone,
        "nationality": g.nationality,
        "anonymised": g.anonymised_at is not None,
        "created_at": g.created_at,
    }


async def search_guests(
    uow: UnitOfWork, ctx: TenantContext, q: str | None, limit: int
) -> list[dict[str, Any]]:
    return [guest_payload(g) for g in await StayRepository(uow.session, ctx).search_guests(q, limit)]


async def create_guest(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> Guest:
    guest = await StayRepository(uow.session, ctx).create_guest(
        {
            "full_name": body["name"],
            "email": str(body["email"]).lower() if body.get("email") else None,
            "phone": body.get("phone"),
            "nationality": body.get("nationality"),
        }
    )
    # Personal data stays out of the audit log; the entry records that it happened.
    await write_audit(uow.session, ctx, "guest.create", "guest", guest.id)
    return guest


async def get_guest(uow: UnitOfWork, ctx: TenantContext, guest_id: uuid.UUID) -> dict[str, Any]:
    repo = StayRepository(uow.session, ctx)
    guest = await repo.guest(guest_id)
    if guest is None:
        raise AppError("NOT_FOUND")
    stays = await repo.stays_of_guest(guest_id)
    rooms = await repo.rooms([s.room_id for s in stays])
    return {
        **guest_payload(guest),
        "stays": [
            {
                "id": s.id,
                "status": s.status,
                "room": rooms[s.room_id].number if s.room_id in rooms else None,
                "arrival_date": s.arrival_date,
                "departure_date": s.departure_date,
            }
            for s in stays
        ],
    }


async def patch_guest(
    uow: UnitOfWork, ctx: TenantContext, guest_id: uuid.UUID, changes: dict[str, Any]
) -> dict[str, Any]:
    repo = StayRepository(uow.session, ctx)
    guest = await repo.guest(guest_id, for_update=True)
    if guest is None:
        raise AppError("NOT_FOUND")
    if guest.anonymised_at is not None:
        raise AppError("INVALID_TRANSITION", "This guest's personal data was removed.")
    columns = {"name": "full_name", "email": "email", "phone": "phone", "nationality": "nationality"}
    values = {columns[k]: (str(v).lower() if k == "email" and v else v) for k, v in changes.items()}
    if values:
        guest = await repo.update_guest(guest_id, values)
        await write_audit(
            uow.session, ctx, "guest.update", "guest", guest_id, new_value={"fields": sorted(changes)}
        )
    return guest_payload(guest)


# --- Billing profiles ----------------------------------------------------------------------


def profile_payload(p: Any) -> dict[str, Any]:
    return {
        "id": p.id,
        "company_name": p.company_name,
        "registration_number": p.registration_number,
        "vat_number": p.vat_number,
        "billing_address": p.billing_address,
        "billing_email": p.billing_email,
    }


async def search_profiles(
    uow: UnitOfWork, ctx: TenantContext, q: str | None, limit: int
) -> list[dict[str, Any]]:
    return [profile_payload(p) for p in await StayRepository(uow.session, ctx).search_profiles(q, limit)]


async def create_profile(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    values = {
        **body,
        "billing_email": str(body["billing_email"]).lower() if body.get("billing_email") else None,
    }
    profile = await StayRepository(uow.session, ctx).create_profile(values)
    await write_audit(
        uow.session,
        ctx,
        "billing_profile.create",
        "billing_profile",
        profile.id,
        new_value={"company": profile.company_name},
    )
    return profile_payload(profile)


# --- Stays ---------------------------------------------------------------------------------


async def stay_payload(uow: UnitOfWork, ctx: TenantContext, stays: list[Stay]) -> list[dict[str, Any]]:
    repo = StayRepository(uow.session, ctx)
    rooms = await repo.rooms(list({s.room_id for s in stays}))
    guests = await repo.guests(list({s.guest_id for s in stays}))
    ledger = FolioLedger(uow.session, ctx)
    out = []
    for s in stays:
        folio = await ledger.folio_for_stay(s.id)
        summary = None
        if folio is not None:
            b = await ledger.balance(folio.id)
            summary = {
                "folio_id": folio.id,
                "status": folio.status,
                **{
                    k: money(b[k], s.currency)
                    for k in ("accommodation", "fnb", "other", "tips", "paid", "balance")
                },
            }
        guest = guests.get(s.guest_id)
        out.append(
            {
                "id": s.id,
                "status": s.status,
                "room": {"id": s.room_id, "number": rooms[s.room_id].number},
                "guest": {"id": s.guest_id, "name": guest.full_name if guest else ""},
                "arrival_date": s.arrival_date,
                "departure_date": s.departure_date,
                "nights": (s.departure_date - s.arrival_date).days,
                "nightly_rate": money(s.nightly_rate_minor, s.currency),
                "billing_type": s.billing_type,
                "billing_profile_id": s.billing_profile_id,
                "purchase_order": s.purchase_order,
                "traveller_name": s.traveller_name,
                "charges_blocked": s.charges_blocked,
                "is_training": s.is_training,
                "checked_in_at": s.checked_in_at,
                "checked_out_at": s.checked_out_at,
                "folio": summary,
                "version": s.version,
            }
        )
    return out


async def list_stays(
    uow: UnitOfWork, ctx: TenantContext, **filters: Any
) -> list[tuple[Stay, dict[str, Any]]]:
    stays = await StayRepository(uow.session, ctx).list_stays(**filters)
    return list(zip(stays, await stay_payload(uow, ctx, stays), strict=True))


async def get_stay(uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID) -> dict[str, Any]:
    stay = await StayRepository(uow.session, ctx).stay(stay_id)
    if stay is None:
        raise AppError("NOT_FOUND")
    return (await stay_payload(uow, ctx, [stay]))[0]


async def _room_rate(uow: UnitOfWork, ctx: TenantContext, room: Room) -> int:
    if room.rate_minor is not None:
        return room.rate_minor
    rt = await RoomTypeRepository(uow.session, ctx).get(room.room_type_id)
    if rt is None:  # pragma: no cover - FK
        raise AppError("NOT_FOUND")
    return rt.base_rate_minor


async def _new_stay(
    uow: UnitOfWork,
    ctx: TenantContext,
    body: dict[str, Any],
    room: Room,
    arrival: date,
    departure: date,
    permissions: frozenset[str],
) -> Stay:
    repo = StayRepository(uow.session, ctx)
    settings = await _settings(uow, ctx)
    if departure <= arrival:
        raise _field_error("departure_date", "Departure must be after arrival.")
    if (departure - arrival).days > 90:
        raise _field_error("departure_date", "A stay is at most 90 nights.")
    if await repo.overlapping(room.id, arrival, departure, None):
        raise AppError("ROOM_NOT_AVAILABLE", "This room is already booked for some of these nights.")
    if body.get("guest_id"):
        guest = await repo.guest(body["guest_id"])
        if guest is None:
            raise AppError("NOT_FOUND", "Unknown guest.")
        if guest.anonymised_at is not None:
            raise AppError(
                "INVALID_TRANSITION", "This guest's personal data was removed; create a new guest."
            )
    else:
        guest = await create_guest(uow, ctx, body["guest"])
    billing = body.get("billing") or {"type": "personal"}
    if billing.get("billing_profile_id") and await repo.profile(billing["billing_profile_id"]) is None:
        raise AppError("NOT_FOUND", "Unknown billing profile.")
    standard = await _room_rate(uow, ctx, room)
    rate, reason = standard, None
    override = body.get("rate_override")
    if override is not None:
        if "stays.rate_override" not in permissions:
            raise AppError(
                "PERMISSION_DENIED",
                "You cannot override room rates.",
                details={"permission": "stays.rate_override"},
            )
        if override["currency"] != settings.currency:
            raise _field_error("rate_override", "Currency must match the hotel currency.", "AMOUNT_INVALID")
        if not (body.get("rate_override_reason") or "").strip():
            raise AppError("REASON_REQUIRED", "Give a reason for the rate override.")
        rate, reason = int(override["amount_minor"]), body["rate_override_reason"].strip()
    stay = await repo.create_stay(
        {
            "room_id": room.id,
            "guest_id": guest.id,
            "billing_type": billing.get("type", "personal"),
            "billing_profile_id": billing.get("billing_profile_id"),
            "purchase_order": billing.get("purchase_order"),
            "traveller_name": billing.get("traveller_name"),
            "arrival_date": arrival,
            "departure_date": departure,
            "nightly_rate_minor": rate,
            "rate_override_reason": reason,
            "currency": settings.currency,
            "is_training": bool(body.get("training")),
        }
    )
    await write_audit(
        uow.session,
        ctx,
        "stay.create",
        "stay",
        stay.id,
        new_value={
            "room": room.number,
            "arrival": str(arrival),
            "departure": str(departure),
            "nightly_rate_minor": rate,
            "standard_rate_minor": standard,
            "rate_override_reason": reason,
            "training": stay.is_training,
        },
    )
    return stay


async def create_reservation(
    uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any], permissions: frozenset[str]
) -> dict[str, Any]:
    room = await RoomRepository(uow.session, ctx).get(body["room_id"])
    if room is None:
        raise AppError("NOT_FOUND")
    stay = await _new_stay(uow, ctx, body, room, body["arrival_date"], body["departure_date"], permissions)
    return (await stay_payload(uow, ctx, [stay]))[0]


async def _check_in(uow: UnitOfWork, ctx: TenantContext, stay: Stay) -> Stay:
    repo = StayRepository(uow.session, ctx)
    rooms = RoomRepository(uow.session, ctx)
    settings = await _settings(uow, ctx)
    today = business_date(settings.timezone)
    if stay.status != "reserved":
        raise AppError("INVALID_TRANSITION", f"A {stay.status.replace('_', ' ')} stay cannot be checked in.")
    if stay.arrival_date > today:
        raise AppError("INVALID_TRANSITION", "This stay arrives on a later date.")
    if stay.departure_date <= today:
        raise AppError("INVALID_TRANSITION", "This stay's departure date has passed.")
    room = await rooms.get(stay.room_id, for_update=True)
    if room is None or room.status not in CHECK_IN_ROOM_STATUSES or await repo.live_stay_for_room(room.id):
        raise AppError("ROOM_NOT_AVAILABLE", "This room is not ready for a guest.")
    ledger = FolioLedger(uow.session, ctx)
    folio = await ledger.open_folio(stay.id, stay.currency)
    gross, vat = gross_and_vat(
        stay.nightly_rate_minor,
        settings.vat_rate_bp,
        includes_vat=settings.accommodation_rates_include_vat,
        registered=settings.vat_registered,
    )
    nights = (stay.departure_date - stay.arrival_date).days
    await ledger.post(
        folio,
        [
            Line(
                category="accommodation",
                description=f"Room {room.number}, night of {stay.arrival_date + timedelta(days=i)}",
                unit_amount_minor=gross,
                quantity=1,
                vat_rate_bp=settings.vat_rate_bp if settings.vat_registered else 0,
                vat_minor=vat,
                business_date=stay.arrival_date + timedelta(days=i),
            )
            for i in range(nights)
        ],
    )
    now = datetime.now(UTC)
    stay = await repo.update_stay(
        stay.id, {"status": "active", "checked_in_at": now, "checked_in_by": ctx.actor_id}
    )
    await rooms.update(room.id, None, {"status": "occupied", "status_changed_at": now})
    await write_audit(
        uow.session,
        ctx,
        "stay.check_in",
        "stay",
        stay.id,
        new_value={"room": room.number, "nights": nights, "accommodation_minor": gross * nights},
    )
    payload = {"stay_id": str(stay.id), "room_id": str(room.id), "room": room.number}
    await emit(
        uow.session,
        ctx,
        "STAY_CHECKED_IN",
        [hotel_channel(ctx.hotel_id, f"room:{room.id}"), hotel_channel(ctx.hotel_id, "ops")],
        payload,
    )
    return stay


async def check_in(uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID) -> dict[str, Any]:
    stay = await StayRepository(uow.session, ctx).stay(stay_id, for_update=True)
    if stay is None:
        raise AppError("NOT_FOUND")
    stay = await _check_in(uow, ctx, stay)
    return (await stay_payload(uow, ctx, [stay]))[0]


async def walk_in(
    uow: UnitOfWork, ctx: TenantContext, room_id: uuid.UUID, body: dict[str, Any], permissions: frozenset[str]
) -> dict[str, Any]:
    room = await RoomRepository(uow.session, ctx).get(room_id, for_update=True)
    if room is None:
        raise AppError("NOT_FOUND")
    if room.status not in CHECK_IN_ROOM_STATUSES:
        raise AppError("ROOM_NOT_AVAILABLE", "This room is not ready for a guest.")
    today = business_date((await _settings(uow, ctx)).timezone)
    stay = await _new_stay(uow, ctx, body, room, today, today + timedelta(days=body["nights"]), permissions)
    stay = await _check_in(uow, ctx, stay)
    return (await stay_payload(uow, ctx, [stay]))[0]


async def cancel(uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID) -> dict[str, Any]:
    repo = StayRepository(uow.session, ctx)
    stay = await repo.stay(stay_id, for_update=True)
    if stay is None:
        raise AppError("NOT_FOUND")
    if stay.status != "reserved":
        raise AppError("INVALID_TRANSITION", "Only a reservation can be cancelled.")
    stay = await repo.update_stay(stay_id, {"status": "cancelled"})
    await write_audit(uow.session, ctx, "stay.cancel", "stay", stay_id, old_value={"status": "reserved"})
    return (await stay_payload(uow, ctx, [stay]))[0]


async def set_charges_blocked(
    uow: UnitOfWork, ctx: TenantContext, stay_id: uuid.UUID, blocked: bool
) -> dict[str, Any]:
    repo = StayRepository(uow.session, ctx)
    stay = await repo.stay(stay_id, for_update=True)
    if stay is None:
        raise AppError("NOT_FOUND")
    if stay.status not in LIVE:
        raise AppError("INVALID_TRANSITION", "Only a checked-in stay can have charges blocked.")
    if stay.charges_blocked != blocked:
        stay = await repo.update_stay(stay_id, {"charges_blocked": blocked})
        await write_audit(
            uow.session,
            ctx,
            "stay.block_charges" if blocked else "stay.unblock_charges",
            "stay",
            stay_id,
            old_value={"charges_blocked": not blocked},
            new_value={"charges_blocked": blocked},
        )
    return (await stay_payload(uow, ctx, [stay]))[0]
