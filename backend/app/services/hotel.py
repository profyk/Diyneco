"""Hotel profile and settings. Writes are optimistic (ETag = version) and audited; settings
changes are audited one entry per field."""

from __future__ import annotations

import zoneinfo
from datetime import time
from typing import Any

from app.audit.writer import write_audit
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.tenancy import Hotel, HotelSettings
from app.realtime.outbox import emit, hotel_channel
from app.repositories.hotels import HotelRepository

# API field -> (column, kind). Money fields arrive as {"amount_minor", "currency"}.
SETTINGS_FIELDS: dict[str, tuple[str, str]] = {
    "timezone": ("timezone", "plain"),
    "currency": ("currency", "plain"),
    "vat_registered": ("vat_registered", "plain"),
    "vat_number": ("vat_number", "plain"),
    "vat_rate_bp": ("vat_rate_bp", "plain"),
    "accommodation_rates_include_vat": ("accommodation_rates_include_vat", "plain"),
    "menu_prices_include_vat": ("menu_prices_include_vat", "plain"),
    "room_charging_enabled": ("room_charging_enabled", "plain"),
    "room_charge_auto_approve_limit": ("room_charge_auto_limit_minor", "money"),
    "room_service_fee": ("room_service_fee_minor", "money"),
    "checkout_override_allowed": ("checkout_override_allowed", "plain"),
    "room_status_after_checkout": ("room_status_after_checkout", "plain"),
    "checkout_time": ("checkout_time", "time"),
    "wifi_name": ("wifi_name", "plain"),
    "invoice_prefix": ("invoice_prefix", "plain"),
    "abridged_invoice_max": ("abridged_invoice_max_minor", "money"),
    "guest_data_retention_days": ("guest_data_retention_days", "plain"),
}

HOTEL_FIELDS = ("name", "legal_name", "address", "phone", "email")


def parse_if_match(header: str | None) -> int:
    """PATCH requires If-Match; missing or malformed counts as stale (DECISIONS)."""
    if not header:
        raise AppError("PRECONDITION_FAILED", "Send If-Match with the ETag you loaded.")
    tag = header.strip()
    if tag.startswith("W/"):
        tag = tag[2:]
    tag = tag.strip('"')
    if not tag.isdigit():
        raise AppError("PRECONDITION_FAILED")
    return int(tag)


def etag(version: int) -> str:
    return f'"{version}"'


def money(amount_minor: int, currency: str) -> dict[str, Any]:
    return {"amount_minor": amount_minor, "currency": currency}


def settings_payload(st: HotelSettings) -> dict[str, Any]:
    return {
        "timezone": st.timezone,
        "currency": st.currency,
        "vat_registered": st.vat_registered,
        "vat_number": st.vat_number,
        "vat_rate_bp": st.vat_rate_bp,
        "accommodation_rates_include_vat": st.accommodation_rates_include_vat,
        "menu_prices_include_vat": st.menu_prices_include_vat,
        "room_charging_enabled": st.room_charging_enabled,
        "room_charge_auto_approve_limit": money(st.room_charge_auto_limit_minor, st.currency),
        "room_service_fee": money(st.room_service_fee_minor, st.currency),
        "checkout_override_allowed": st.checkout_override_allowed,
        "room_status_after_checkout": st.room_status_after_checkout,
        "checkout_time": st.checkout_time.strftime("%H:%M"),
        "wifi_name": st.wifi_name,
        "invoice_prefix": st.invoice_prefix,
        "abridged_invoice_max": money(st.abridged_invoice_max_minor, st.currency),
        "guest_data_retention_days": st.guest_data_retention_days,
    }


async def hotel_payload(repo: HotelRepository, hotel: Hotel) -> dict[str, Any]:
    plan = await repo.current_plan()
    return {
        "id": hotel.id,
        "name": hotel.name,
        "legal_name": hotel.legal_name,
        "slug": hotel.slug,
        "status": hotel.status,
        "address": hotel.address,
        "phone": hotel.phone,
        "email": hotel.email,
        "logo_url": None,  # logo upload arrives in Phase 2
        "country": hotel.country,
        "plan": {"code": plan[0].code, "name": plan[0].name, "subscription_status": plan[1].status}
        if plan
        else None,
        "created_at": hotel.created_at,
        "version": hotel.version,
    }


async def get_hotel(uow: UnitOfWork, ctx: TenantContext) -> tuple[dict[str, Any], int]:
    repo = HotelRepository(uow.session, ctx)
    hotel = await repo.get()
    if hotel is None:
        raise AppError("NOT_FOUND")
    return await hotel_payload(repo, hotel), hotel.version


async def patch_hotel(
    uow: UnitOfWork, ctx: TenantContext, expected_version: int, changes: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    repo = HotelRepository(uow.session, ctx)
    before = await repo.get()
    if before is None:
        raise AppError("NOT_FOUND")
    old = {k: getattr(before, k) for k in changes}
    updated = await repo.update(expected_version, changes)
    if updated is None:
        raise AppError("PRECONDITION_FAILED")
    if changes:
        await write_audit(
            uow.session, ctx, "hotel.update", "hotel", ctx.hotel_id, old_value=old, new_value=changes
        )
        await emit(
            uow.session,
            ctx,
            "HOTEL_UPDATED",
            [hotel_channel(ctx.hotel_id, "ops")],
            {"hotel_id": str(ctx.hotel_id), "version": updated.version},
        )
    return await hotel_payload(repo, updated), updated.version


async def get_settings(uow: UnitOfWork, ctx: TenantContext) -> tuple[dict[str, Any], int]:
    st = await HotelRepository(uow.session, ctx).get_settings()
    if st is None:
        raise AppError("NOT_FOUND")
    return settings_payload(st), st.version


def _field_error(field: str, problem: str, code: str = "VALIDATION_FAILED") -> AppError:
    return AppError(
        code, problem, details={"fields": [{"field": field, "problem": problem, "type": "value_error"}]}
    )


def _to_column_values(current: HotelSettings, changes: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for api_field, raw in changes.items():
        column, kind = SETTINGS_FIELDS[api_field]
        if kind == "money":
            if raw["currency"] != current.currency:
                raise _field_error(api_field, "Currency must match the hotel currency.", "AMOUNT_INVALID")
            values[column] = raw["amount_minor"]
        elif kind == "time":
            values[column] = raw if isinstance(raw, time) else time.fromisoformat(raw)
        else:
            values[column] = raw
    if "currency" in values and values["currency"] != current.currency:
        raise _field_error("currency", "The hotel currency cannot be changed.")
    if "timezone" in values:
        try:
            zoneinfo.ZoneInfo(values["timezone"])
        except (zoneinfo.ZoneInfoNotFoundError, ValueError) as exc:
            raise _field_error("timezone", "Unknown time zone.") from exc
    vat_registered = values.get("vat_registered", current.vat_registered)
    vat_number = values.get("vat_number", current.vat_number)
    if vat_registered and not vat_number:
        raise _field_error("vat_number", "A VAT-registered hotel needs a VAT number.")
    return values


async def patch_settings(
    uow: UnitOfWork, ctx: TenantContext, expected_version: int, changes: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    repo = HotelRepository(uow.session, ctx)
    current = await repo.get_settings()
    if current is None:
        raise AppError("NOT_FOUND")
    if current.version != expected_version:
        raise AppError("PRECONDITION_FAILED")
    before = settings_payload(current)
    values = _to_column_values(current, changes)
    updated = await repo.update_settings(expected_version, values)
    if updated is None:
        raise AppError("PRECONDITION_FAILED")
    after = settings_payload(updated)
    changed = [f for f in changes if before[f] != after[f]]
    for f in changed:
        await write_audit(
            uow.session,
            ctx,
            "settings.update",
            "hotel_settings",
            ctx.hotel_id,
            old_value={f: before[f]},
            new_value={f: after[f]},
        )
    if changed:
        await emit(
            uow.session,
            ctx,
            "SETTINGS_UPDATED",
            [hotel_channel(ctx.hotel_id, "ops")],
            {"hotel_id": str(ctx.hotel_id), "fields": changed, "version": updated.version},
        )
    return after, updated.version
