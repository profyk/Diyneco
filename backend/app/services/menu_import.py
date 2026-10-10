"""Menu upload from a spreadsheet (CSV), checked first and then imported all or nothing (D66).

Columns: category, name, description, price, type, station, dietary, allergens, ingredients,
options. Lists are separated by semicolons. A missing category is created; the station and
option groups must exist (by name, ignoring case); an empty station means the first active one.
Prices are in the hotel's currency, e.g. 185.00.
"""

from __future__ import annotations

import csv
import io
import re
import uuid
from typing import Any, get_args

from app.audit.writer import write_audit
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.repositories.menu import MenuRepository
from app.schemas.menu import Allergen, DietaryTag
from app.services.menu import CERTIFIED_TAGS, _settings, menu_changed

COLUMNS = (
    "category",
    "name",
    "description",
    "price",
    "type",
    "station",
    "dietary",
    "allergens",
    "ingredients",
    "options",
)
MAX_BYTES = 1_000_000
MAX_ROWS = 500
_PRICE = re.compile(r"^\d{1,7}(\.\d{1,2})?$")
DIETARY = set(get_args(DietaryTag))
ALLERGENS = set(get_args(Allergen))
TEMPLATE = (
    "category,name,description,price,type,station,dietary,allergens,ingredients,options\n"
    'Grill,Rump steak 300 g,Flame-grilled with chips,245.00,food,,,"",'
    '"beef;potato;salt;pepper","Steak temperature;Sauce"\n'
    'Drinks,Fresh orange juice,,45.00,beverage,Bar,vegan,,"orange",\n'
)


def _error(problem: str) -> AppError:
    return AppError(
        "VALIDATION_FAILED",
        problem,
        details={"fields": [{"field": "body", "problem": problem, "type": "file"}]},
    )


def _split(cell: str) -> list[str]:
    return [p.strip() for p in cell.split(";") if p.strip()]


def _rows(raw: bytes) -> list[tuple[int, list[str]]]:
    if len(raw) > MAX_BYTES:
        raise _error("The file is larger than 1 MB.")
    try:
        content = raw.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(content)))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise _error("The file must be a UTF-8 CSV file.") from exc
    if not rows or tuple(h.strip().lower() for h in rows[0]) != COLUMNS:
        raise _error(f"The first line must be: {','.join(COLUMNS)}")
    data = [(i + 2, r) for i, r in enumerate(rows[1:]) if any(c.strip() for c in r)]
    if not data:
        raise _error("The file has no menu items.")
    if len(data) > MAX_ROWS:
        raise _error(f"At most {MAX_ROWS} items per file.")
    return data


def _check_row(
    cells: list[str],
    stations: dict[str, Any],
    default_station: Any,
    groups: dict[str, Any],
    permissions: frozenset[str],
) -> tuple[dict[str, Any] | None, list[tuple[str, str]]]:
    """One line: (planned item, or None) and its problems as (column, message)."""
    if len(cells) != len(COLUMNS):
        return None, [("row", f"Expected {len(COLUMNS)} columns, found {len(cells)}.")]
    v = dict(zip(COLUMNS, (c.strip() for c in cells), strict=True))
    problems: list[tuple[str, str]] = []
    if not v["category"] or len(v["category"]) > 120:
        problems.append(("category", "Give a category name (up to 120 characters)."))
    if not v["name"] or len(v["name"]) > 120:
        problems.append(("name", "Give the item a name (up to 120 characters)."))
    if len(v["description"]) > 1000:
        problems.append(("description", "At most 1000 characters."))
    if not _PRICE.match(v["price"]):
        problems.append(("price", "Write the price like 185.00, without a currency symbol."))
    kind = (v["type"] or "food").lower()
    if kind not in ("food", "beverage"):
        problems.append(("type", "Use food or beverage."))
    station = stations.get(v["station"].lower()) if v["station"] else default_station
    if station is None:
        where = "No kitchen station with that name." if v["station"] else "Add a kitchen station first."
        problems.append(("station", where))
    dietary = [d.lower().replace(" ", "_") for d in _split(v["dietary"])]
    if bad := [d for d in dietary if d not in DIETARY]:
        problems.append(("dietary", f"Unknown: {', '.join(bad)}. Use {', '.join(sorted(DIETARY))}."))
    elif CERTIFIED_TAGS & set(dietary) and "menu.certify" not in permissions:
        problems.append(("dietary", "Only staff who can certify the menu may mark items halaal or kosher."))
    allergens = [a.lower().replace(" ", "_") for a in _split(v["allergens"])]
    if bad := [a for a in allergens if a not in ALLERGENS]:
        problems.append(("allergens", f"Unknown: {', '.join(bad)}."))
    ingredients = _split(v["ingredients"])
    if len(ingredients) > 40 or any(len(i) > 60 for i in ingredients):
        problems.append(("ingredients", "At most 40 ingredients of up to 60 characters."))
    option_names = _split(v["options"])
    if missing := [o for o in option_names if o.lower() not in groups]:
        problems.append(("options", f"No option group named {', '.join(missing)}; add it under Options."))
    if problems or station is None:
        return None, problems
    whole, _, cents = v["price"].partition(".")
    return {
        "category": v["category"],
        "values": {
            "name": v["name"],
            "description": v["description"] or None,
            "price_minor": int(whole) * 100 + int((cents + "00")[:2]),
            "charge_category_code": kind,
            "station_id": station.id,
            "dietary_tags": sorted(set(dietary)),
            "allergens": sorted(set(allergens)),
            "ingredients": ingredients,
        },
        "groups": [groups[o.lower()].id for o in option_names],
    }, []


async def import_csv(
    uow: UnitOfWork, ctx: TenantContext, raw: bytes, permissions: frozenset[str], *, commit: bool
) -> dict[str, Any]:
    repo = MenuRepository(uow.session, ctx)
    settings = await _settings(uow, ctx)
    stations = {s.name.lower(): s for s in await repo.stations(active_only=True)}
    default_station = next(iter(sorted(stations.values(), key=lambda s: (s.sort_order, s.name))), None)
    categories = {c.name.lower(): c for c in await repo.categories()}
    groups = {g.name.lower(): g for g in await repo.groups()}
    errors: list[dict[str, Any]] = []
    planned: list[dict[str, Any]] = []
    new_categories: list[str] = []

    for line, cells in _rows(raw):
        row, problems = _check_row(cells, stations, default_station, groups, permissions)
        if row is None:
            errors.extend({"line": line, "field": f, "problem": p} for f, p in problems)
            continue
        known = set(categories) | {n.lower() for n in new_categories}
        if row["category"].lower() not in known:
            new_categories.append(row["category"])
        row["values"]["currency"] = settings.currency
        planned.append(row)

    report: dict[str, Any] = {
        "committed": False,
        "valid": not errors,
        "rows": len(planned) + len({e["line"] for e in errors}),
        "errors": errors[:500],
        "created": 0,
        "new_categories": new_categories,
    }
    if commit and errors:
        raise AppError(
            "VALIDATION_FAILED",
            "Fix the problems in the file; nothing was imported.",
            details={"report": report},
        )
    if not commit:
        return report

    for name in new_categories:
        categories[name.lower()] = await repo.create_category({"name": name, "sort_order": len(categories)})
    created: list[uuid.UUID] = []
    for n, row in enumerate(planned):
        item = await repo.create_item(
            {**row["values"], "category_id": categories[row["category"].lower()].id, "sort_order": n}
        )
        if row["groups"]:
            await repo.set_item_groups(item.id, row["groups"])
        created.append(item.id)
    await write_audit(
        uow.session,
        ctx,
        "menu.import",
        "menu_item",
        None,
        new_value={"items": len(created), "new_categories": new_categories},
    )
    await menu_changed(uow, ctx, repo, "import")
    report.update(committed=True, created=len(created))
    return report
