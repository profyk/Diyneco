"""/room-types and /rooms. The hotel is always the caller's token hotel."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse

from app.api.deps import IdemUser, Principal, StepUp, Uow, has_step_up, require_permission
from app.api.http import IfMatch, parse_if_match, patch_changes, with_etag
from app.api.pagination import DEFAULT_LIMIT, Cursor, Limit, decode_cursor, page
from app.core.errors import AppError
from app.repositories.rooms import room_sort_key
from app.schemas.rooms import (
    BulkResult,
    ImportReport,
    RoomBulkCreate,
    RoomCreate,
    RoomList,
    RoomOut,
    RoomPatch,
    RoomStatus,
    RoomStatusChange,
    RoomTypeCreate,
    RoomTypeList,
    RoomTypeOut,
    RoomTypePatch,
)
from app.services import rooms as svc

router = APIRouter(tags=["rooms"])

RoomsRead = Annotated[Principal, Depends(require_permission("rooms.read"))]
RoomsManage = Annotated[Principal, Depends(require_permission("rooms.manage"))]
RoomsStatus = Annotated[Principal, Depends(require_permission("rooms.status"))]

ROOM_TYPE_NOT_NULL = {"name", "base_rate", "capacity", "amenities"}
ROOM_NOT_NULL = {"number", "room_type_id", "amenities"}


# --- Room types ----------------------------------------------------------------------------


@router.get("/room-types", response_model=RoomTypeList)
async def list_room_types(request: Request, uow: Uow, principal: RoomsRead) -> dict[str, Any]:
    return {"data": await svc.list_room_types(uow, principal.tenant(request)), "next_cursor": None}


@router.post("/room-types", status_code=201, response_model=RoomTypeOut)
async def create_room_type(
    idem: IdemUser, body: RoomTypeCreate, request: Request, uow: Uow, principal: RoomsManage
) -> JSONResponse:
    result = await svc.create_room_type(uow, principal.tenant(request), body.model_dump())
    return await idem.complete(uow, 201, RoomTypeOut.model_validate(result).model_dump(mode="json"))


@router.patch("/room-types/{room_type_id}", response_model=RoomTypeOut)
async def patch_room_type(
    room_type_id: uuid.UUID,
    body: RoomTypePatch,
    request: Request,
    uow: Uow,
    principal: RoomsManage,
    if_match: IfMatch = None,
) -> JSONResponse:
    expected = parse_if_match(if_match)
    result = await svc.patch_room_type(
        uow,
        principal.tenant(request),
        room_type_id,
        expected,
        patch_changes(body, ROOM_TYPE_NOT_NULL),
        stepped_up=has_step_up(request, principal),
    )
    return with_etag(result, result["version"], RoomTypeOut)


# --- Rooms ---------------------------------------------------------------------------------


@router.get("/rooms", response_model=RoomList)
async def list_rooms(
    request: Request,
    uow: Uow,
    principal: RoomsRead,
    status: Annotated[RoomStatus | None, Query()] = None,
    floor: Annotated[str | None, Query(max_length=20)] = None,
    room_type_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Limit = DEFAULT_LIMIT,
    cursor: Cursor = None,
) -> dict[str, Any]:
    rows = await svc.list_rooms(
        uow,
        principal.tenant(request),
        status=status,
        floor=floor,
        room_type_id=room_type_id,
        after=decode_cursor(cursor, 3),
        limit=limit,
    )
    data, next_cursor = page(rows, limit, lambda r: room_sort_key(r[0]))
    return {"data": [payload for _, payload in data], "next_cursor": next_cursor}


@router.get("/rooms/{room_id}", response_model=RoomOut)
async def get_room(room_id: uuid.UUID, request: Request, uow: Uow, principal: RoomsRead) -> JSONResponse:
    result = await svc.get_room(uow, principal.tenant(request), room_id)
    return with_etag(result, result["version"], RoomOut)


@router.post("/rooms", status_code=201, response_model=RoomOut)
async def create_room(
    idem: IdemUser, body: RoomCreate, request: Request, uow: Uow, principal: RoomsManage
) -> JSONResponse:
    result = await svc.create_room(uow, principal.tenant(request), body.model_dump())
    return await idem.complete(uow, 201, RoomOut.model_validate(result).model_dump(mode="json"))


@router.post("/rooms/bulk", status_code=201, response_model=BulkResult)
async def bulk_create_rooms(
    idem: IdemUser, body: RoomBulkCreate, request: Request, uow: Uow, principal: RoomsManage
) -> JSONResponse:
    created = await svc.bulk_create(uow, principal.tenant(request), [r.model_dump() for r in body.ranges])
    result = BulkResult.model_validate({"created": len(created), "data": created})
    return await idem.complete(uow, 201, result.model_dump(mode="json"))


@router.post(
    "/rooms/import",
    response_model=ImportReport,
    openapi_extra={
        "requestBody": {"required": True, "content": {"text/csv": {"schema": {"type": "string"}}}}
    },
)
async def import_rooms(
    idem: IdemUser,
    request: Request,
    uow: Uow,
    principal: RoomsManage,
    commit: Annotated[bool, Query()] = False,
) -> JSONResponse:
    """Dry run by default: returns a per-line report. `?commit=true` writes all rows or none."""
    if not request.headers.get("content-type", "").startswith("text/csv"):
        raise AppError("VALIDATION_FAILED", "Send the file as text/csv.")
    report = await svc.import_csv(uow, principal.tenant(request), await request.body(), commit=commit)
    status = 201 if report["committed"] else 200
    return await idem.complete(uow, status, ImportReport.model_validate(report).model_dump(mode="json"))


@router.patch("/rooms/{room_id}", response_model=RoomOut)
async def patch_room(
    room_id: uuid.UUID,
    body: RoomPatch,
    request: Request,
    uow: Uow,
    principal: RoomsManage,
    if_match: IfMatch = None,
) -> JSONResponse:
    expected = parse_if_match(if_match)
    result = await svc.patch_room(
        uow, principal.tenant(request), room_id, expected, patch_changes(body, ROOM_NOT_NULL)
    )
    return with_etag(result, result["version"], RoomOut)


@router.post("/rooms/{room_id}/status", response_model=RoomOut)
async def set_room_status(
    room_id: uuid.UUID, body: RoomStatusChange, request: Request, uow: Uow, principal: RoomsStatus
) -> JSONResponse:
    result = await svc.set_status(uow, principal.tenant(request), room_id, body.status)
    return with_etag(result, result["version"], RoomOut)


@router.delete("/rooms/{room_id}", status_code=204)
async def delete_room(
    room_id: uuid.UUID, request: Request, uow: Uow, principal: RoomsManage, _step_up: StepUp
) -> Response:
    await svc.delete_room(uow, principal.tenant(request), room_id)
    return Response(status_code=204)
