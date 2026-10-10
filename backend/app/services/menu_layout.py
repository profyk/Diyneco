"""Menu structure: the standard layout and routing a category to a kitchen station (D68).

The standard layout is what most hotel kitchens use; it only adds what is missing (matched by
name, ignoring case), so it is safe to run again after hotels rename or add their own.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.audit.writer import write_audit
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.repositories.menu import MenuRepository
from app.services.menu import category_payload, menu_changed, station_payload

STATIONS = ("Main kitchen", "Cold kitchen", "Pastry", "Bar")

# (section, category, station)
CATEGORIES: tuple[tuple[str, str, str], ...] = (
    ("food", "Breakfast", "Main kitchen"),
    ("food", "Starters", "Cold kitchen"),
    ("food", "Salads", "Cold kitchen"),
    ("food", "Mains", "Main kitchen"),
    ("food", "Grill", "Main kitchen"),
    ("food", "Sides", "Main kitchen"),
    ("food", "Desserts", "Pastry"),
    ("food", "Kids", "Main kitchen"),
    ("drinks", "Coffees and teas", "Bar"),
    ("drinks", "Soft drinks and juices", "Bar"),
    ("drinks", "Wines", "Bar"),
    ("drinks", "MCC and sparkling", "Bar"),
    ("drinks", "Beers and ciders", "Bar"),
    ("drinks", "Spirits and liqueurs", "Bar"),
    ("drinks", "Cocktails", "Bar"),
)


async def apply_standard_layout(uow: UnitOfWork, ctx: TenantContext) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    stations = {s.name.lower(): s for s in await repo.stations()}
    created_stations: list[str] = []
    for name in STATIONS:
        existing = stations.get(name.lower())
        if existing is None:
            stations[name.lower()] = await repo.create_station({"name": name, "sort_order": len(stations)})
            created_stations.append(name)
        elif not existing.is_active:
            stations[name.lower()] = await repo.update_station(existing.id, {"is_active": True})
    categories = {c.name.lower(): c for c in await repo.categories()}
    created_categories: list[str] = []
    for n, (section, name, station) in enumerate(CATEGORIES):
        if name.lower() in categories:
            continue
        categories[name.lower()] = await repo.create_category(
            {
                "name": name,
                "section": section,
                "sort_order": 10 * (n + 1),
                "default_station_id": stations[station.lower()].id,
            }
        )
        created_categories.append(name)
    if created_stations or created_categories:
        await write_audit(
            uow.session,
            ctx,
            "menu.standard_layout",
            "menu_category",
            None,
            new_value={"stations": created_stations, "categories": created_categories},
        )
        await menu_changed(uow, ctx, repo, "layout")
    return {
        "created_stations": created_stations,
        "created_categories": created_categories,
        "stations": [station_payload(s) for s in await repo.stations()],
        "categories": [category_payload(c) for c in await repo.categories()],
    }


async def route_category(
    uow: UnitOfWork, ctx: TenantContext, category_id: uuid.UUID, station_id: uuid.UUID
) -> dict[str, Any]:
    """Prepares every dish of the category at the station, and new ones too."""
    repo = MenuRepository(uow.session, ctx)
    category = await repo.category(category_id)
    if category is None:
        raise AppError("NOT_FOUND")
    station = await repo.station(station_id)
    if station is None or not station.is_active:
        raise AppError("NOT_FOUND", "Unknown station.")
    items = await repo.items(category_id=category_id)
    for item in items:
        if item.station_id != station_id:
            await repo.update_item(item.id, None, {"station_id": station_id})
    category = await repo.update_category(category_id, {"default_station_id": station_id})
    await write_audit(
        uow.session,
        ctx,
        "menu.category_route",
        "menu_category",
        category_id,
        new_value={"station": station.name, "items": len(items)},
    )
    await menu_changed(uow, ctx, repo, "routing")
    return {**category_payload(category), "moved_items": len(items)}
