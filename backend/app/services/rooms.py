"""Room types and rooms: single, ranges and CSV import. Bulk calls create every row or none.

Occupancy (`occupied`) is set only by check-in and checkout, never here. A room type's rate
change applies to new stays only, because stays snapshot `nightly_rate_minor` at check-in.
"""

from __future__ import annotations

import csv
import io
import re
import uuid
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.audit.writer import write_audit
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.domain import Room, RoomType
from app.repositories.hotels import HotelRepository
from app.repositories.rooms import RoomRepository, RoomTypeRepository
from app.schemas.rooms import MAX_BULK_ROOMS
from app.services.plans import ensure_capacity

CSV_COLUMNS = ("room_number", "floor", "room_type", "rate", "capacity", "amenities")
MAX_CSV_BYTES = 1_000_000
_RATE = re.compile(r"^\d{1,9}(\.\d{1,2})?$")


def money(amount_minor: int, currency: str) -> dict[str, Any]:
    return {"amount_minor": amount_minor, "currency": currency}


def field_error(field: str, problem: str, code: str = "VALIDATION_FAILED", **extra: Any) -> AppError:
    fields = [{"field": field, "problem": problem, "type": "value_error"}]
    return AppError(code, problem, details={"fields": fields, **extra})


def room_type_payload(rt: RoomType, room_count: int) -> dict[str, Any]:
    return {
        "id": rt.id,
        "name": rt.name,
        "base_rate": money(rt.base_rate_minor, rt.currency),
        "capacity": rt.capacity,
        "amenities": list(rt.amenities),
        "room_count": room_count,
        "version": rt.version,
        "created_at": rt.created_at,
        "updated_at": rt.updated_at,
    }


def room_payload(room: Room, rt: RoomType) -> dict[str, Any]:
    return {
        "id": room.id,
        "number": room.number,
        "floor": room.floor,
        "room_type": {"id": rt.id, "name": rt.name},
        "rate": money(room.rate_minor, rt.currency) if room.rate_minor is not None else None,
        "effective_rate": money(
            room.rate_minor if room.rate_minor is not None else rt.base_rate_minor, rt.currency
        ),
        "capacity": room.capacity if room.capacity is not None else rt.capacity,
        "amenities": list(room.amenities),
        "status": room.status,
        "status_changed_at": room.status_changed_at,
        "version": room.version,
        "created_at": room.created_at,
        "updated_at": room.updated_at,
    }


async def _currency(uow: UnitOfWork, ctx: TenantContext) -> str:
    st = await HotelRepository(uow.session, ctx).get_settings()
    if st is None:
        raise AppError("NOT_FOUND")
    return st.currency


def _check_money(field: str, value: dict[str, Any] | None, currency: str) -> int | None:
    if value is None:
        return None
    if value["currency"] != currency:
        raise field_error(field, "Currency must match the hotel currency.", "AMOUNT_INVALID")
    return int(value["amount_minor"])


async def _room_types_by_id(uow: UnitOfWork, ctx: TenantContext) -> dict[uuid.UUID, RoomType]:
    return {rt.id: rt for rt in (await RoomTypeRepository(uow.session, ctx).by_lower_names()).values()}


def _clean_amenities(items: list[str]) -> list[str]:
    seen: dict[str, str] = {}
    for raw in items:
        a = raw.strip()
        if a and a.lower() not in seen:
            seen[a.lower()] = a
    return list(seen.values())


def _jsonable(v: Any) -> Any:
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, list):
        return list(v)
    return v


# --- Room types ----------------------------------------------------------------------------


def room_type_audit(rt: RoomType) -> dict[str, Any]:
    return {
        "name": rt.name,
        "base_rate_minor": rt.base_rate_minor,
        "capacity": rt.capacity,
        "amenities": list(rt.amenities),
    }


async def list_room_types(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    rows = await RoomTypeRepository(uow.session, ctx).list_with_counts()
    return [room_type_payload(rt, n) for rt, n in rows]


async def get_room_type(uow: UnitOfWork, ctx: TenantContext, room_type_id: uuid.UUID) -> RoomType:
    rt = await RoomTypeRepository(uow.session, ctx).get(room_type_id)
    if rt is None:
        raise AppError("NOT_FOUND")
    return rt


async def create_room_type(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    repo = RoomTypeRepository(uow.session, ctx)
    currency = await _currency(uow, ctx)
    rate = _check_money("base_rate", body["base_rate"], currency)
    if await repo.name_taken(body["name"]):
        raise field_error("name", "A room type with this name already exists.")
    rt = await repo.create(
        {
            "name": body["name"],
            "base_rate_minor": rate,
            "currency": currency,
            "capacity": body.get("capacity", 2),
            "amenities": _clean_amenities(body.get("amenities") or []),
        }
    )
    await write_audit(uow.session, ctx, "room_type.create", "room_type", rt.id, new_value=room_type_audit(rt))
    return room_type_payload(rt, 0)


def rate_changes(changes: dict[str, Any], current: RoomType) -> bool:
    rate = changes.get("base_rate")
    return rate is not None and int(rate["amount_minor"]) != current.base_rate_minor


async def patch_room_type(
    uow: UnitOfWork,
    ctx: TenantContext,
    room_type_id: uuid.UUID,
    expected_version: int,
    changes: dict[str, Any],
    *,
    stepped_up: bool,
) -> dict[str, Any]:
    repo = RoomTypeRepository(uow.session, ctx)
    current = await repo.get(room_type_id, for_update=True)
    if current is None:
        raise AppError("NOT_FOUND")
    if current.version != expected_version:
        raise AppError("PRECONDITION_FAILED")
    if rate_changes(changes, current) and not stepped_up:
        raise AppError("STEP_UP_REQUIRED", "Changing a rate needs your PIN or password.")
    values: dict[str, Any] = {}
    if "name" in changes:
        if await repo.name_taken(changes["name"], exclude=room_type_id):
            raise field_error("name", "A room type with this name already exists.")
        values["name"] = changes["name"]
    if "base_rate" in changes:
        values["base_rate_minor"] = _check_money("base_rate", changes["base_rate"], current.currency)
    if "capacity" in changes:
        values["capacity"] = changes["capacity"]
    if "amenities" in changes:
        values["amenities"] = _clean_amenities(changes["amenities"])
    before = room_type_audit(current)
    updated = await repo.update(room_type_id, expected_version, values)
    if updated is None:
        raise AppError("PRECONDITION_FAILED")
    after = room_type_audit(updated)
    diff = {k: v for k, v in after.items() if before[k] != v}
    if diff:
        await write_audit(
            uow.session,
            ctx,
            "room_type.update",
            "room_type",
            room_type_id,
            old_value={k: before[k] for k in diff},
            new_value=diff,
        )
    return room_type_payload(updated, await repo.room_count(room_type_id))


# --- Rooms ---------------------------------------------------------------------------------


async def list_rooms(
    uow: UnitOfWork,
    ctx: TenantContext,
    *,
    status: str | None,
    floor: str | None,
    room_type_id: uuid.UUID | None,
    after: list[Any] | None,
    limit: int,
) -> list[tuple[Room, dict[str, Any]]]:
    rooms = await RoomRepository(uow.session, ctx).list_page(
        status=status, floor=floor, room_type_id=room_type_id, after=after, limit=limit
    )
    types = await _room_types_by_id(uow, ctx)
    return [(r, room_payload(r, types[r.room_type_id])) for r in rooms]


async def get_room(uow: UnitOfWork, ctx: TenantContext, room_id: uuid.UUID) -> dict[str, Any]:
    room = await RoomRepository(uow.session, ctx).get(room_id)
    if room is None:
        raise AppError("NOT_FOUND")
    types = await _room_types_by_id(uow, ctx)
    return room_payload(room, types[room.room_type_id])


def _room_values(body: dict[str, Any], rt: RoomType) -> dict[str, Any]:
    return {
        "number": body["number"],
        "floor": body.get("floor"),
        "room_type_id": rt.id,
        "rate_minor": _check_money("rate", body.get("rate"), rt.currency),
        "capacity": body.get("capacity"),
        "amenities": _clean_amenities(body.get("amenities") or []),
    }


async def _insert_rooms(
    uow: UnitOfWork, ctx: TenantContext, rows: list[dict[str, Any]], source: str
) -> list[Room]:
    """All-or-nothing: checks every number and the plan limit before writing anything."""
    repo = RoomRepository(uow.session, ctx)
    numbers = [r["number"] for r in rows]
    if len(set(numbers)) != len(numbers):
        dupes = sorted({n for n in numbers if numbers.count(n) > 1})
        raise field_error("number", "Room numbers repeat in this request.", duplicates=dupes[:50])
    taken = sorted(await repo.existing_numbers(numbers))
    if taken:
        raise field_error("number", "These room numbers already exist.", existing=taken[:50])
    await ensure_capacity(uow, ctx, "rooms", len(rows))
    created = await repo.create_many(rows)
    await write_audit(
        uow.session,
        ctx,
        "room.create",
        "room",
        created[0].id if len(created) == 1 else None,
        new_value={"source": source, "count": len(created), "numbers": numbers[:200]},
    )
    return created


async def create_room(uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any]) -> dict[str, Any]:
    rt = await get_room_type(uow, ctx, body["room_type_id"])
    room = (await _insert_rooms(uow, ctx, [_room_values(body, rt)], "single"))[0]
    return room_payload(room, rt)


def expand_ranges(ranges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rooms: list[dict[str, Any]] = []
    for i, r in enumerate(ranges):
        lo, hi = r["from_"], r["to"]
        if hi < lo:
            raise field_error(f"ranges[{i}].to", "`to` must be at least `from`.")
        if len(rooms) + (hi - lo + 1) > MAX_BULK_ROOMS:
            raise field_error("ranges", f"At most {MAX_BULK_ROOMS} rooms per call.")
        floor = r.get("floor")
        for n in range(lo, hi + 1):
            rooms.append(
                {
                    "number": f"{r.get('prefix') or ''}{n}",
                    "floor": str(floor) if floor is not None else None,
                    "room_type_id": r["room_type_id"],
                    "index": i,
                }
            )
    return rooms


async def bulk_create(
    uow: UnitOfWork, ctx: TenantContext, ranges: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    planned = expand_ranges(ranges)
    types = await _room_types_by_id(uow, ctx)
    rows: list[dict[str, Any]] = []
    for p in planned:
        rt = types.get(p["room_type_id"])
        if rt is None:
            raise field_error(f"ranges[{p['index']}].room_type_id", "Unknown room type.")
        rows.append(_room_values(p, rt))
    created = await _insert_rooms(uow, ctx, rows, "ranges")
    return [room_payload(r, types[r.room_type_id]) for r in created]


# --- CSV import ----------------------------------------------------------------------------


def parse_rate(raw: str) -> int | None:
    """Rands with up to 2 decimals to cents, exactly (no floats)."""
    raw = raw.strip().replace(" ", "")
    if raw.startswith("R"):
        raw = raw[1:]
    if not _RATE.match(raw):
        return None
    try:
        return int(Decimal(raw) * 100)
    except InvalidOperation:
        return None


def _read_csv(raw: bytes) -> list[tuple[int, list[str]]]:
    """(line number, cells) for every non-blank data line, after checking the header."""
    if len(raw) > MAX_CSV_BYTES:
        raise field_error("body", "The file is larger than 1 MB.")
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise field_error("body", "The file must be UTF-8 text.") from exc
    try:
        rows_in = list(csv.reader(io.StringIO(content)))
    except csv.Error as exc:
        raise field_error("body", "The file is not valid CSV.") from exc
    if not rows_in:
        raise field_error("body", "The file is empty.")
    if tuple(h.strip().lower() for h in rows_in[0]) != CSV_COLUMNS:
        raise field_error("header", f"The first line must be: {','.join(CSV_COLUMNS)}")
    data_rows = [(i + 2, r) for i, r in enumerate(rows_in[1:]) if any(c.strip() for c in r)]
    if not data_rows:
        raise field_error("body", "The file has no rooms.")
    if len(data_rows) > MAX_BULK_ROOMS:
        raise field_error("body", f"At most {MAX_BULK_ROOMS} rooms per file.")
    return data_rows


def _check_csv_row(
    cells: list[str], types: dict[str, RoomType], existing: set[str], seen: dict[str, int], line: int
) -> tuple[dict[str, Any] | None, list[tuple[str, str]]]:
    """One row: (room values, or None if invalid) and a list of (field, problem)."""
    if len(cells) != len(CSV_COLUMNS):
        return None, [("row", f"Expected {len(CSV_COLUMNS)} columns, found {len(cells)}.")]
    problems: list[tuple[str, str]] = []
    number, floor, type_name, rate_raw, cap_raw, amen_raw = (c.strip() for c in cells)
    if not number or len(number) > 40:
        problems.append(("room_number", "Room number is required (max 40 characters)."))
    elif number in seen:
        problems.append(("room_number", f"Duplicate of line {seen[number]}."))
    elif number in existing:
        problems.append(("room_number", "This room number already exists."))
    else:
        seen[number] = line
    rt = types.get(type_name.lower())
    if rt is None:
        problems.append(
            ("room_type", f"Unknown room type {type_name!r}." if type_name else "Room type is required.")
        )
    rate = parse_rate(rate_raw) if rate_raw else None
    if rate_raw and rate is None:
        problems.append(("rate", "Rate must be in rands with up to 2 decimals, e.g. 1500.00."))
    capacity = int(cap_raw) if cap_raw.isdigit() and 1 <= int(cap_raw) <= 20 else None
    if cap_raw and capacity is None:
        problems.append(("capacity", "Capacity must be a whole number from 1 to 20."))
    if len(floor) > 20:
        problems.append(("floor", "Floor is at most 20 characters."))
    amenities = [a.strip() for a in amen_raw.split("|") if a.strip()]
    if len(amenities) > 50 or any(len(a) > 60 for a in amenities):
        problems.append(("amenities", "At most 50 amenities of 60 characters each."))
    if problems or rt is None:
        return None, problems
    values = {
        "number": number,
        "floor": floor or None,
        "room_type_id": rt.id,
        "rate_minor": rate,
        "capacity": capacity,
        "amenities": _clean_amenities(amenities),
    }
    return values, problems


async def import_csv(uow: UnitOfWork, ctx: TenantContext, raw: bytes, *, commit: bool) -> dict[str, Any]:
    data_rows = _read_csv(raw)
    types = await RoomTypeRepository(uow.session, ctx).by_lower_names()
    existing = await RoomRepository(uow.session, ctx).existing_numbers(
        [r[0].strip() for _, r in data_rows if r and r[0].strip()]
    )
    seen: dict[str, int] = {}
    planned: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line, cells in data_rows:
        values, problems = _check_csv_row(cells, types, existing, seen, line)
        errors.extend({"line": line, "field": f, "problem": p} for f, p in problems)
        if values is not None:
            planned.append(values)

    report: dict[str, Any] = {
        "committed": False,
        "valid": not errors,
        "rows": len(data_rows),
        "errors": errors[:500],
        "created": 0,
    }
    if commit and errors:
        raise AppError(
            "VALIDATION_FAILED",
            "Fix the problems in the file; nothing was imported.",
            details={"report": report},
        )
    if commit:
        created = await _insert_rooms(uow, ctx, planned, "csv")
        report.update(committed=True, created=len(created))
    return report


# --- Single-room changes -------------------------------------------------------------------


async def patch_room(
    uow: UnitOfWork, ctx: TenantContext, room_id: uuid.UUID, expected_version: int, changes: dict[str, Any]
) -> dict[str, Any]:
    repo = RoomRepository(uow.session, ctx)
    room = await repo.get(room_id, for_update=True)
    if room is None:
        raise AppError("NOT_FOUND")
    if room.version != expected_version:
        raise AppError("PRECONDITION_FAILED")
    types = await _room_types_by_id(uow, ctx)
    rt = types[room.room_type_id]
    values: dict[str, Any] = {}
    if changes.get("room_type_id") is not None and changes["room_type_id"] != room.room_type_id:
        new_rt = types.get(changes["room_type_id"])
        if new_rt is None:
            raise field_error("room_type_id", "Unknown room type.")
        rt = new_rt
        values["room_type_id"] = rt.id
    if changes.get("number") is not None and changes["number"] != room.number:
        if await repo.existing_numbers([changes["number"]]):
            raise field_error("number", "This room number already exists.")
        values["number"] = changes["number"]
    if "floor" in changes:
        values["floor"] = changes["floor"]
    if "rate" in changes:
        values["rate_minor"] = _check_money("rate", changes["rate"], rt.currency)
    if "capacity" in changes:
        values["capacity"] = changes["capacity"]
    if "amenities" in changes:
        values["amenities"] = _clean_amenities(changes["amenities"] or [])
    old = {k: _jsonable(getattr(room, k)) for k in values}
    updated = await repo.update(room_id, expected_version, values)
    if updated is None:
        raise AppError("PRECONDITION_FAILED")
    if values:
        await write_audit(
            uow.session,
            ctx,
            "room.update",
            "room",
            room_id,
            old_value=old,
            new_value={k: _jsonable(v) for k, v in values.items()},
        )
    return room_payload(updated, rt)


async def set_status(uow: UnitOfWork, ctx: TenantContext, room_id: uuid.UUID, status: str) -> dict[str, Any]:
    repo = RoomRepository(uow.session, ctx)
    room = await repo.get(room_id, for_update=True)
    if room is None:
        raise AppError("NOT_FOUND")
    if room.status == "occupied" or await repo.has_live_stay(room_id):
        raise AppError("ROOM_OCCUPIED", "This room has a guest checked in.")
    types = await _room_types_by_id(uow, ctx)
    if room.status == status:
        return room_payload(room, types[room.room_type_id])
    updated = await repo.update(room_id, None, {"status": status, "status_changed_at": datetime.now(UTC)})
    if updated is None:
        raise AppError("NOT_FOUND")
    await write_audit(
        uow.session,
        ctx,
        "room.status",
        "room",
        room_id,
        old_value={"status": room.status},
        new_value={"status": status},
    )
    return room_payload(updated, types[room.room_type_id])


async def delete_room(uow: UnitOfWork, ctx: TenantContext, room_id: uuid.UUID) -> None:
    repo = RoomRepository(uow.session, ctx)
    room = await repo.get(room_id, for_update=True)
    if room is None:
        raise AppError("NOT_FOUND")
    if await repo.has_live_stay(room_id):
        raise AppError("ROOM_OCCUPIED", "This room has a guest checked in.")
    if await repo.has_any_stay(room_id):
        raise AppError(
            "INVALID_TRANSITION", "A room with guest history cannot be deleted; set it out of service."
        )
    if await repo.has_bound_device(room_id):
        raise AppError("INVALID_TRANSITION", "Unpair this room's tablet before deleting the room.")
    await repo.update(room_id, None, {"deleted_at": datetime.now(UTC)})
    await write_audit(
        uow.session,
        ctx,
        "room.delete",
        "room",
        room_id,
        old_value={"number": room.number, "floor": room.floor},
    )
