"""Kitchen stations and menu administration (API spec, Menu, stations, schedules and images).

Price changes affect new orders only (orders snapshot what they need). A price change needs
`menu.price.update`, a sensitive permission, so it also needs step-up (D19). Halaal and
kosher tags need `menu.certify`.
"""

from __future__ import annotations

import uuid
import zoneinfo
from datetime import UTC, datetime
from typing import Any

from app.audit.writer import write_audit
from app.core.errors import AppError
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork
from app.integrations.storage import hotel_key
from app.models.domain import (
    KitchenStation,
    MenuCategory,
    MenuItem,
    MenuModifier,
    MenuModifierGroup,
    MenuSchedule,
)
from app.realtime.outbox import emit, hotel_channel
from app.repositories.hotels import HotelRepository
from app.repositories.menu import MenuRepository
from app.services import images as images_svc
from app.services import schedules

CERTIFIED_TAGS = {"halaal", "kosher"}
IMAGE_TYPES = {"image/jpeg": "jpg", "image/webp": "webp"}
IMAGE_MAX_BYTES = 5 * 1024 * 1024


def money(amount_minor: int, currency: str) -> dict[str, Any]:
    return {"amount_minor": amount_minor, "currency": currency}


def _field_error(field: str, problem: str, code: str = "VALIDATION_FAILED") -> AppError:
    return AppError(
        code, problem, details={"fields": [{"field": field, "problem": problem, "type": "value_error"}]}
    )


async def _settings(uow: UnitOfWork, ctx: TenantContext) -> Any:
    st = await HotelRepository(uow.session, ctx).get_settings()
    if st is None:
        raise AppError("NOT_FOUND")
    return st


async def menu_changed(uow: UnitOfWork, ctx: TenantContext, repo: MenuRepository, reason: str) -> None:
    """MENU_UPDATED to every kitchen station and every room with a tablet (API spec channels)."""
    channels = [hotel_channel(ctx.hotel_id, f"kitchen:{s.id}") for s in await repo.stations(active_only=True)]
    channels += [hotel_channel(ctx.hotel_id, f"room:{r}") for r in await repo.guest_room_channels()]
    if channels:
        await emit(uow.session, ctx, "MENU_UPDATED", channels, {"reason": reason})


# --- Stations ------------------------------------------------------------------------------


def station_payload(s: KitchenStation) -> dict[str, Any]:
    return {"id": s.id, "name": s.name, "sort_order": s.sort_order, "is_active": s.is_active}


async def list_stations(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    return [station_payload(s) for s in await MenuRepository(uow.session, ctx).stations()]


async def create_station(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    if await repo.station_name_taken(body["name"]):
        raise _field_error("name", "A station with this name already exists.")
    station = await repo.create_station({"name": body["name"], "sort_order": body.get("sort_order", 0)})
    await write_audit(
        uow.session, ctx, "station.create", "kitchen_station", station.id, new_value={"name": station.name}
    )
    return station_payload(station)


async def patch_station(
    uow: UnitOfWork, ctx: TenantContext, station_id: uuid.UUID, changes: dict[str, Any]
) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    station = await repo.station(station_id, for_update=True)
    if station is None:
        raise AppError("NOT_FOUND")
    if changes.get("name") and await repo.station_name_taken(changes["name"], exclude=station_id):
        raise _field_error("name", "A station with this name already exists.")
    if changes.get("is_active") is False and await repo.live_items_at_station(station_id):
        raise AppError("INVALID_TRANSITION", "Move this station's menu items to another station first.")
    old = {k: getattr(station, k) for k in changes}
    station = await repo.update_station(station_id, changes)
    if changes:
        await write_audit(
            uow.session,
            ctx,
            "station.update",
            "kitchen_station",
            station_id,
            old_value=old,
            new_value=changes,
        )
    return station_payload(station)


async def delete_station(uow: UnitOfWork, ctx: TenantContext, station_id: uuid.UUID) -> None:
    """Deactivates the station. Past orders keep pointing at it, so the row stays (D31)."""
    repo = MenuRepository(uow.session, ctx)
    station = await repo.station(station_id, for_update=True)
    if station is None or not station.is_active:
        raise AppError("NOT_FOUND")
    if await repo.live_items_at_station(station_id):
        raise AppError("INVALID_TRANSITION", "Menu items still point at this station.")
    await repo.update_station(station_id, {"is_active": False})
    await write_audit(
        uow.session, ctx, "station.delete", "kitchen_station", station_id, old_value={"name": station.name}
    )


# --- Schedules -----------------------------------------------------------------------------


def schedule_payload(s: MenuSchedule) -> dict[str, Any]:
    return {"id": s.id, "name": s.name, "windows": s.windows}


async def list_schedules(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    return [schedule_payload(s) for s in await MenuRepository(uow.session, ctx).schedules()]


async def create_schedule(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    windows = [{"days": w["days"], "from": w["from"], "to": w["to"]} for w in body["windows"]]
    schedule = await MenuRepository(uow.session, ctx).create_schedule(body["name"], windows)
    await write_audit(
        uow.session,
        ctx,
        "menu.schedule_create",
        "menu_schedule",
        schedule.id,
        new_value={"name": schedule.name},
    )
    return schedule_payload(schedule)


async def _check_schedule(repo: MenuRepository, schedule_id: uuid.UUID | None) -> None:
    if schedule_id is not None and await repo.schedule(schedule_id) is None:
        raise AppError("NOT_FOUND", "Unknown schedule.")


# --- Categories ----------------------------------------------------------------------------


def category_payload(c: MenuCategory) -> dict[str, Any]:
    return {"id": c.id, "name": c.name, "sort_order": c.sort_order, "schedule_id": c.schedule_id}


async def list_categories(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    return [category_payload(c) for c in await MenuRepository(uow.session, ctx).categories()]


async def create_category(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    await _check_schedule(repo, body.get("schedule_id"))
    category = await repo.create_category(
        {
            "name": body["name"],
            "sort_order": body.get("sort_order", 0),
            "schedule_id": body.get("schedule_id"),
        }
    )
    await write_audit(
        uow.session,
        ctx,
        "menu.category_create",
        "menu_category",
        category.id,
        new_value={"name": category.name},
    )
    await menu_changed(uow, ctx, repo, "category")
    return category_payload(category)


async def patch_category(
    uow: UnitOfWork, ctx: TenantContext, category_id: uuid.UUID, changes: dict[str, Any]
) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    category = await repo.category(category_id)
    if category is None:
        raise AppError("NOT_FOUND")
    if "schedule_id" in changes:
        await _check_schedule(repo, changes["schedule_id"])
    old = {
        k: str(v) if isinstance(v, uuid.UUID) else v for k, v in ((k, getattr(category, k)) for k in changes)
    }
    category = await repo.update_category(category_id, changes)
    if changes:
        new = {k: str(v) if isinstance(v, uuid.UUID) else v for k, v in changes.items()}
        await write_audit(
            uow.session,
            ctx,
            "menu.category_update",
            "menu_category",
            category_id,
            old_value=old,
            new_value=new,
        )
        await menu_changed(uow, ctx, repo, "category")
    return category_payload(category)


async def delete_category(uow: UnitOfWork, ctx: TenantContext, category_id: uuid.UUID) -> None:
    repo = MenuRepository(uow.session, ctx)
    category = await repo.category(category_id)
    if category is None:
        raise AppError("NOT_FOUND")
    if await repo.live_items_in_category(category_id):
        raise AppError("INVALID_TRANSITION", "Move or delete this category's items first.")
    await repo.update_category(category_id, {"deleted_at": datetime.now(UTC)})
    await write_audit(
        uow.session,
        ctx,
        "menu.category_delete",
        "menu_category",
        category_id,
        old_value={"name": category.name},
    )
    await menu_changed(uow, ctx, repo, "category")


# --- Items ---------------------------------------------------------------------------------


def group_payload(g: MenuModifierGroup, options: list[MenuModifier], currency: str) -> dict[str, Any]:
    return {
        "id": g.id,
        "name": g.name,
        "min_select": g.min_select,
        "max_select": g.max_select,
        "options": [
            {
                "id": o.id,
                "name": o.name,
                "price_delta": money(o.price_delta_minor, currency),
                "is_available": o.is_available,
                "sort_order": o.sort_order,
            }
            for o in options
        ],
    }


async def item_payloads(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, items: list[MenuItem]
) -> list[dict[str, Any]]:
    """Items with their modifier groups, image URLs and `available_now` in hotel time."""
    repo = MenuRepository(uow.session, ctx)
    settings = await _settings(uow, ctx)
    local_now = datetime.now(zoneinfo.ZoneInfo(settings.timezone)).replace(tzinfo=None)
    schedules_by_id = {s.id: s.windows for s in await repo.schedules()}
    categories = {c.id: c for c in await repo.categories()}
    item_groups = await repo.item_groups([i.id for i in items])
    group_ids = list({g for gs in item_groups.values() for g in gs})
    groups = {g.id: g for g in await repo.groups(group_ids)}
    options = await repo.options(group_ids)
    served = {i.id: images_svc.served_path(i.image_path, i.image_variants) for i in items}
    images = await st.storage.signed_downloads(
        st.settings.storage_bucket_assets, [p for p in served.values() if p]
    )
    out = []
    for i in items:
        category = categories.get(i.category_id)
        schedule_id = i.schedule_id or (category.schedule_id if category else None)
        windows = schedules_by_id.get(schedule_id) if schedule_id else None
        out.append(
            {
                "id": i.id,
                "name": i.name,
                "description": i.description,
                "price": money(i.price_minor, i.currency),
                "vat_rate_bp": i.vat_rate_bp,
                "charge_category": i.charge_category_code,
                "station_id": i.station_id,
                "category_id": i.category_id,
                "schedule_id": i.schedule_id,
                "is_available": i.is_available,
                "available_now": i.is_available
                and category is not None
                and schedules.is_open(windows, local_now),
                "next_available_at": schedules.next_open(windows, local_now) if windows else None,
                "dietary_tags": list(i.dietary_tags),
                "allergens": list(i.allergens),
                "image_url": images.get(path) if (path := served[i.id]) else None,
                "sort_order": i.sort_order,
                "modifier_groups": [
                    group_payload(groups[g], options.get(g, []), i.currency)
                    for g in item_groups.get(i.id, [])
                    if g in groups
                ],
                "version": i.version,
                "updated_at": i.updated_at,
            }
        )
    return out


async def list_items(
    st: AppState,
    uow: UnitOfWork,
    ctx: TenantContext,
    *,
    category_id: uuid.UUID | None,
    station_id: uuid.UUID | None,
    available: bool | None,
) -> list[dict[str, Any]]:
    items = await MenuRepository(uow.session, ctx).items(category_id=category_id, station_id=station_id)
    payloads = await item_payloads(st, uow, ctx, items)
    if available is not None:
        payloads = [p for p in payloads if p["available_now"] == available]
    return payloads


async def get_item(st: AppState, uow: UnitOfWork, ctx: TenantContext, item_id: uuid.UUID) -> dict[str, Any]:
    item = await MenuRepository(uow.session, ctx).item(item_id)
    if item is None:
        raise AppError("NOT_FOUND")
    return (await item_payloads(st, uow, ctx, [item]))[0]


async def _check_refs(repo: MenuRepository, values: dict[str, Any]) -> None:
    if "station_id" in values:
        station = await repo.station(values["station_id"])
        if station is None or not station.is_active:
            raise AppError("NOT_FOUND", "Unknown station.")
    if "category_id" in values and await repo.category(values["category_id"]) is None:
        raise AppError("NOT_FOUND", "Unknown category.")
    if "schedule_id" in values:
        await _check_schedule(repo, values["schedule_id"])


def _check_tags(tags: list[str] | None, permissions: frozenset[str]) -> None:
    if tags and CERTIFIED_TAGS & set(tags) and "menu.certify" not in permissions:
        raise AppError(
            "PERMISSION_DENIED",
            "Only staff who can certify the menu may mark items halaal or kosher.",
            details={"permission": "menu.certify"},
        )


async def create_item(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any], permissions: frozenset[str]
) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    settings = await _settings(uow, ctx)
    if body["price"]["currency"] != settings.currency:
        raise _field_error("price", "Currency must match the hotel currency.", "AMOUNT_INVALID")
    _check_tags(body.get("dietary_tags"), permissions)
    values = {
        "name": body["name"],
        "description": body.get("description"),
        "price_minor": body["price"]["amount_minor"],
        "currency": settings.currency,
        "vat_rate_bp": body.get("vat_rate_bp"),
        "charge_category_code": body.get("charge_category", "food"),
        "station_id": body["station_id"],
        "category_id": body["category_id"],
        "schedule_id": body.get("schedule_id"),
        "dietary_tags": sorted(set(body.get("dietary_tags") or [])),
        "allergens": sorted(set(body.get("allergens") or [])),
        "sort_order": body.get("sort_order", 0),
    }
    await _check_refs(repo, values)
    item = await repo.create_item(values)
    await write_audit(
        uow.session,
        ctx,
        "menu.item_create",
        "menu_item",
        item.id,
        new_value={"name": item.name, "price_minor": item.price_minor},
    )
    await menu_changed(uow, ctx, repo, "item")
    return (await item_payloads(st, uow, ctx, [item]))[0]


def price_changes(changes: dict[str, Any], item: MenuItem) -> bool:
    price = changes.get("price")
    return (price is not None and price["amount_minor"] != item.price_minor) or (
        "vat_rate_bp" in changes and changes["vat_rate_bp"] != item.vat_rate_bp
    )


async def patch_item(
    st: AppState,
    uow: UnitOfWork,
    ctx: TenantContext,
    item_id: uuid.UUID,
    expected_version: int,
    changes: dict[str, Any],
    permissions: frozenset[str],
    *,
    stepped_up: bool,
) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    item = await repo.item(item_id, for_update=True)
    if item is None:
        raise AppError("NOT_FOUND")
    if item.version != expected_version:
        raise AppError("PRECONDITION_FAILED")
    if price_changes(changes, item):
        if "menu.price.update" not in permissions:
            raise AppError(
                "PERMISSION_DENIED", "You cannot change prices.", details={"permission": "menu.price.update"}
            )
        if not stepped_up:
            raise AppError("STEP_UP_REQUIRED", "Changing a price needs your PIN or password.")
    _check_tags(changes.get("dietary_tags"), permissions)
    values: dict[str, Any] = {}
    for api, column in (
        ("name", "name"),
        ("description", "description"),
        ("vat_rate_bp", "vat_rate_bp"),
        ("charge_category", "charge_category_code"),
        ("station_id", "station_id"),
        ("category_id", "category_id"),
        ("schedule_id", "schedule_id"),
        ("sort_order", "sort_order"),
    ):
        if api in changes:
            values[column] = changes[api]
    if "price" in changes:
        if changes["price"]["currency"] != item.currency:
            raise _field_error("price", "Currency must match the hotel currency.", "AMOUNT_INVALID")
        values["price_minor"] = changes["price"]["amount_minor"]
    for tags in ("dietary_tags", "allergens"):
        if tags in changes:
            values[tags] = sorted(set(changes[tags] or []))
    await _check_refs(repo, values)
    old = {k: _plain(getattr(item, k)) for k in values}
    updated = await repo.update_item(item_id, expected_version, values)
    if updated is None:
        raise AppError("PRECONDITION_FAILED")
    if values:
        action = (
            "menu.price_update" if "price_minor" in values or "vat_rate_bp" in values else "menu.item_update"
        )
        await write_audit(
            uow.session,
            ctx,
            action,
            "menu_item",
            item_id,
            old_value=old,
            new_value={k: _plain(v) for k, v in values.items()},
        )
        await menu_changed(uow, ctx, repo, "item")
    return (await item_payloads(st, uow, ctx, [updated]))[0]


def _plain(v: Any) -> Any:
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, list | tuple):
        return list(v)
    return v


async def set_availability(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, item_id: uuid.UUID, available: bool
) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    item = await repo.item(item_id, for_update=True)
    if item is None:
        raise AppError("NOT_FOUND")
    if item.is_available != available:
        item = await repo.update_item(item_id, None, {"is_available": available}) or item
        await write_audit(
            uow.session,
            ctx,
            "menu.availability",
            "menu_item",
            item_id,
            old_value={"is_available": not available},
            new_value={"is_available": available},
        )
        await menu_changed(uow, ctx, repo, "availability")
    return (await item_payloads(st, uow, ctx, [item]))[0]


async def delete_item(uow: UnitOfWork, ctx: TenantContext, item_id: uuid.UUID) -> None:
    repo = MenuRepository(uow.session, ctx)
    item = await repo.item(item_id, for_update=True)
    if item is None:
        raise AppError("NOT_FOUND")
    await repo.update_item(item_id, None, {"deleted_at": datetime.now(UTC)})
    await write_audit(
        uow.session, ctx, "menu.item_delete", "menu_item", item_id, old_value={"name": item.name}
    )
    await menu_changed(uow, ctx, repo, "item")


async def start_image_upload(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, item_id: uuid.UUID, content_type: str, size_bytes: int
) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    item = await repo.item(item_id, for_update=True)
    if item is None:
        raise AppError("NOT_FOUND")
    if content_type not in IMAGE_TYPES or size_bytes > IMAGE_MAX_BYTES:
        raise _field_error("content_type", "Upload a JPEG or WebP image of 5 MB or less.")
    key = hotel_key(ctx.hotel_id, "menu", str(item_id), f"{uuid.uuid4()}.{IMAGE_TYPES[content_type]}")
    upload = await st.storage.signed_upload(
        st.settings.storage_bucket_assets, key, content_type, IMAGE_MAX_BYTES
    )
    await repo.update_item(item_id, None, {"image_path": key})
    await write_audit(
        uow.session,
        ctx,
        "menu.item_image",
        "menu_item",
        item_id,
        old_value={"image_path": item.image_path},
        new_value={"image_path": key},
    )
    await menu_changed(uow, ctx, repo, "image")
    return {
        "upload_url": upload.url,
        "method": upload.method,
        "headers": upload.headers,
        "expires_at": upload.expires_at,
        "max_bytes": IMAGE_MAX_BYTES,
    }


# --- Modifiers -----------------------------------------------------------------------------


async def list_groups(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    repo = MenuRepository(uow.session, ctx)
    currency = (await _settings(uow, ctx)).currency
    groups = await repo.groups()
    options = await repo.options([g.id for g in groups])
    return [group_payload(g, options.get(g.id, []), currency) for g in groups]


async def create_group(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    if body["max_select"] < body["min_select"]:
        raise _field_error("max_select", "max_select must be at least min_select.")
    repo = MenuRepository(uow.session, ctx)
    group = await repo.create_group(body)
    await write_audit(
        uow.session, ctx, "menu.modifier_group_create", "menu_modifier_group", group.id, new_value=body
    )
    return group_payload(group, [], (await _settings(uow, ctx)).currency)


async def create_option(
    uow: UnitOfWork,
    ctx: TenantContext,
    group_id: uuid.UUID,
    body: dict[str, Any],
    permissions: frozenset[str],
) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    if not await repo.groups([group_id]):
        raise AppError("NOT_FOUND")
    currency = (await _settings(uow, ctx)).currency
    if body["price_delta"]["currency"] != currency:
        raise _field_error("price_delta", "Currency must match the hotel currency.", "AMOUNT_INVALID")
    if body["price_delta"]["amount_minor"] > 0 and "menu.price.update" not in permissions:
        raise AppError(
            "PERMISSION_DENIED", "You cannot set prices.", details={"permission": "menu.price.update"}
        )
    option = await repo.create_option(
        {
            "group_id": group_id,
            "name": body["name"],
            "price_delta_minor": body["price_delta"]["amount_minor"],
            "sort_order": body.get("sort_order", 0),
        }
    )
    await write_audit(
        uow.session,
        ctx,
        "menu.modifier_option_create",
        "menu_modifier",
        option.id,
        new_value={"name": option.name, "price_delta_minor": option.price_delta_minor},
    )
    await menu_changed(uow, ctx, repo, "modifiers")
    groups = await repo.groups([group_id])
    return group_payload(groups[0], (await repo.options([group_id])).get(group_id, []), currency)


async def set_item_groups(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, item_id: uuid.UUID, group_ids: list[uuid.UUID]
) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    item = await repo.item(item_id, for_update=True)
    if item is None:
        raise AppError("NOT_FOUND")
    group_ids = list(dict.fromkeys(group_ids))
    if len(await repo.groups(group_ids)) != len(group_ids):
        raise AppError("NOT_FOUND", "Unknown modifier group.")
    await repo.set_item_groups(item_id, group_ids)
    await repo.update_item(item_id, None, {})  # bump version: the item's offer changed
    await write_audit(
        uow.session,
        ctx,
        "menu.item_modifiers",
        "menu_item",
        item_id,
        new_value={"group_ids": [str(g) for g in group_ids]},
    )
    await menu_changed(uow, ctx, repo, "modifiers")
    return await get_item(st, uow, ctx, item_id)
