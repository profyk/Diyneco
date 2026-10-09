"""What a guest tablet may see. The device token fixes hotel and room; everything here is
limited to the room's active stay, so a new guest never sees a previous guest's data
(API spec, Guest tablet endpoints; security spec, Device and kiosk security)."""

from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import select

from app.billing.folio import FolioLedger
from app.billing.vat import vat_on_top
from app.core.errors import AppError
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork
from app.models.domain import ChargeCategory, Device, FolioEntry, Stay
from app.repositories.hotels import HotelRepository
from app.repositories.menu import MenuRepository
from app.repositories.rooms import RoomRepository
from app.repositories.stays import StayRepository
from app.services import menu as menu_service
from app.services.pricing import money


async def active_stay(uow: UnitOfWork, ctx: TenantContext, room_id: uuid.UUID) -> Stay | None:
    stay = await StayRepository(uow.session, ctx).live_stay_for_room(room_id)
    return stay if stay is not None and stay.status == "active" else None


async def require_stay(uow: UnitOfWork, ctx: TenantContext, device: Device) -> Stay:
    if device.room_id is None:
        raise AppError("DEVICE_UNAUTHORISED")
    stay = await active_stay(uow, ctx, device.room_id)
    if stay is None:
        raise AppError("NO_ACTIVE_STAY", "Welcome! Ordering opens once you are checked in.")
    return stay


async def session(st: AppState, uow: UnitOfWork, ctx: TenantContext, device: Device) -> dict[str, Any]:
    hotel_repo = HotelRepository(uow.session, ctx)
    hotel = await hotel_repo.get()
    settings = await hotel_repo.get_settings()
    room = await RoomRepository(uow.session, ctx).get(device.room_id) if device.room_id else None
    if hotel is None or settings is None or room is None:
        raise AppError("DEVICE_UNAUTHORISED")
    stay = await active_stay(uow, ctx, room.id)
    if hotel.status in ("suspended", "closed"):
        state = "suspended"
    elif device.status == "locked":
        state = "locked"
    else:
        state = "active" if stay else "idle"
    logo = (
        await st.storage.signed_download(st.settings.storage_bucket_assets, hotel.logo_path)
        if hotel.logo_path
        else None
    )
    return {
        "state": state,
        "ordering_enabled": state == "active"
        and hotel.status == "active"
        and settings.room_charging_enabled
        and stay is not None
        and not stay.charges_blocked,
        "hotel": {"id": str(hotel.id), "name": hotel.name, "logo_url": logo},
        "room": {"id": str(room.id), "number": room.number},
        # Only what the welcome screen needs: no guest name or contact details on a shared screen.
        "stay": {"id": str(stay.id), "departure_date": str(stay.departure_date)}
        if stay and state == "active"
        else None,
    }


async def menu(st: AppState, uow: UnitOfWork, ctx: TenantContext) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    items = await repo.items()
    payloads = await menu_service.item_payloads(st, uow, ctx, items)
    settings = await HotelRepository(uow.session, ctx).get_settings()
    if settings is None:
        raise AppError("NOT_FOUND")
    by_category: dict[uuid.UUID, list[dict[str, Any]]] = defaultdict(list)
    for p in payloads:
        if not p["is_available"]:
            continue  # sold out items are hidden from guests
        price = p["price"]["amount_minor"]
        if settings.vat_registered and not settings.menu_prices_include_vat:
            rate = p["vat_rate_bp"] if p["vat_rate_bp"] is not None else settings.vat_rate_bp
            price += vat_on_top(price, rate)
        by_category[p["category_id"]].append(
            {
                "id": p["id"],
                "name": p["name"],
                "description": p["description"],
                "price": money(price, p["price"]["currency"]),
                "image_url": p["image_url"],
                "dietary_tags": p["dietary_tags"],
                "allergens": p["allergens"],
                "available_now": p["available_now"],
                "next_available_at": p["next_available_at"],
                "modifier_groups": p["modifier_groups"],
            }
        )
    return {
        "categories": [
            {"id": c.id, "name": c.name, "items": by_category[c.id]}
            for c in await repo.categories()
            if by_category.get(c.id)
        ]
    }


async def folio(uow: UnitOfWork, ctx: TenantContext, stay: Stay) -> dict[str, Any]:
    ledger = FolioLedger(uow.session, ctx)
    f = await ledger.folio_for_stay(stay.id)
    if f is None:
        raise AppError("NO_ACTIVE_STAY")
    rows = (
        await uow.session.execute(
            select(FolioEntry, ChargeCategory.revenue_group)
            .join(ChargeCategory, ChargeCategory.id == FolioEntry.category_id)
            .where(FolioEntry.hotel_id == ctx.hotel_id, FolioEntry.folio_id == f.id)
            .order_by(FolioEntry.created_at, FolioEntry.id)
        )
    ).all()
    groups: dict[str, list[dict[str, Any]]] = {
        "accommodation": [],
        "food_and_beverage": [],
        "other": [],
        "payments": [],
        "tips": [],
    }
    key = {
        "accommodation": "accommodation",
        "fnb": "food_and_beverage",
        "other": "other",
        "payment": "payments",
        "tip": "tips",
    }
    for entry, group in rows:
        groups[key[group]].append(
            {
                "description": entry.description,
                "amount": money(
                    -entry.amount_minor if group == "payment" else entry.amount_minor, f.currency
                ),
                "date": entry.business_date,
            }
        )
    b = await ledger.balance(f.id)
    totals = {
        "accommodation": b["accommodation"],
        "food_and_beverage": b["fnb"],
        "other": b["other"],
        "paid": b["paid"],
        "tips": b["tips"],
        "balance": b["balance"],
    }
    return {**groups, "totals": {k: money(v, f.currency) for k, v in totals.items()}}


async def info(uow: UnitOfWork, ctx: TenantContext) -> dict[str, Any]:
    repo = HotelRepository(uow.session, ctx)
    hotel = await repo.get()
    settings = await repo.get_settings()
    if hotel is None or settings is None:
        raise AppError("NOT_FOUND")
    return {
        "hotel_name": hotel.name,
        "wifi_name": settings.wifi_name,
        "checkout_time": settings.checkout_time,
        "phone": hotel.phone,
        "email": hotel.email,
        "pages": [],  # hotel information pages: not in the v1 schema yet
    }
