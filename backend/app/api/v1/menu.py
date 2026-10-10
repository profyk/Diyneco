"""/kitchen-stations and /menu/*. The hotel is always the caller's token hotel."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import IdemUser, Principal, Uow, has_step_up, require_permission, state_of
from app.api.http import IfMatch, parse_if_match, patch_changes, with_etag
from app.core.errors import AppError
from app.schemas.menu import (
    AvailabilityChange,
    CategoryCreate,
    CategoryList,
    CategoryOut,
    CategoryPatch,
    ImageUploadOut,
    ImageUploadRequest,
    ItemCreate,
    ItemList,
    ItemModifierGroups,
    ItemOut,
    ItemPatch,
    MenuImportReport,
    ModifierGroupCreate,
    ModifierGroupList,
    ModifierGroupOut,
    ModifierOptionCreate,
    ScheduleCreate,
    ScheduleList,
    ScheduleOut,
    StationCreate,
    StationList,
    StationOut,
    StationPatch,
)
from app.services import menu as svc
from app.services import menu_import

router = APIRouter(tags=["menu"])

MenuRead = Annotated[Principal, Depends(require_permission("menu.read"))]
MenuManage = Annotated[Principal, Depends(require_permission("menu.manage"))]
MenuAvailability = Annotated[Principal, Depends(require_permission("menu.availability"))]
KitchenManage = Annotated[Principal, Depends(require_permission("kitchen.manage"))]


# --- Stations ------------------------------------------------------------------------------


@router.get("/kitchen-stations", response_model=StationList)
async def list_stations(request: Request, uow: Uow, principal: MenuRead) -> dict[str, Any]:
    return {"data": await svc.list_stations(uow, principal.tenant(request)), "next_cursor": None}


@router.post("/kitchen-stations", status_code=201, response_model=StationOut)
async def create_station(
    idem: IdemUser, body: StationCreate, request: Request, uow: Uow, principal: KitchenManage
) -> Response:
    result = await svc.create_station(uow, principal.tenant(request), body.model_dump())
    return await idem.complete(uow, 201, StationOut.model_validate(result).model_dump(mode="json"))


@router.patch("/kitchen-stations/{station_id}", response_model=StationOut)
async def patch_station(
    station_id: uuid.UUID, body: StationPatch, request: Request, uow: Uow, principal: KitchenManage
) -> dict[str, Any]:
    changes = patch_changes(body, {"name", "sort_order", "is_active"})
    return await svc.patch_station(uow, principal.tenant(request), station_id, changes)


@router.delete("/kitchen-stations/{station_id}", status_code=204)
async def delete_station(
    station_id: uuid.UUID, request: Request, uow: Uow, principal: KitchenManage
) -> Response:
    await svc.delete_station(uow, principal.tenant(request), station_id)
    return Response(status_code=204)


# --- Schedules and categories --------------------------------------------------------------


@router.get("/menu/schedules", response_model=ScheduleList)
async def list_schedules(request: Request, uow: Uow, principal: MenuRead) -> dict[str, Any]:
    return {"data": await svc.list_schedules(uow, principal.tenant(request)), "next_cursor": None}


@router.post("/menu/schedules", status_code=201, response_model=ScheduleOut)
async def create_schedule(
    idem: IdemUser, body: ScheduleCreate, request: Request, uow: Uow, principal: MenuManage
) -> Response:
    result = await svc.create_schedule(uow, principal.tenant(request), body.model_dump())
    return await idem.complete(uow, 201, ScheduleOut.model_validate(result).model_dump(mode="json"))


@router.get("/menu/categories", response_model=CategoryList)
async def list_categories(request: Request, uow: Uow, principal: MenuRead) -> dict[str, Any]:
    return {"data": await svc.list_categories(uow, principal.tenant(request)), "next_cursor": None}


@router.post("/menu/categories", status_code=201, response_model=CategoryOut)
async def create_category(
    idem: IdemUser, body: CategoryCreate, request: Request, uow: Uow, principal: MenuManage
) -> Response:
    result = await svc.create_category(uow, principal.tenant(request), body.model_dump())
    return await idem.complete(uow, 201, CategoryOut.model_validate(result).model_dump(mode="json"))


@router.patch("/menu/categories/{category_id}", response_model=CategoryOut)
async def patch_category(
    category_id: uuid.UUID, body: CategoryPatch, request: Request, uow: Uow, principal: MenuManage
) -> dict[str, Any]:
    changes = patch_changes(body, {"name", "sort_order"})
    return await svc.patch_category(uow, principal.tenant(request), category_id, changes)


@router.delete("/menu/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: uuid.UUID,
    request: Request,
    uow: Uow,
    principal: MenuManage,
    with_items: Annotated[bool, Query()] = False,
) -> Response:
    """`?with_items=true` removes the category and all its items, and needs step-up."""
    if with_items and not has_step_up(request, principal):
        raise AppError("STEP_UP_REQUIRED", "Deleting a category with its items needs your PIN or password.")
    await svc.delete_category(uow, principal.tenant(request), category_id, with_items=with_items)
    return Response(status_code=204)


@router.post(
    "/menu/items/import",
    response_model=MenuImportReport,
    openapi_extra={
        "requestBody": {"required": True, "content": {"text/csv": {"schema": {"type": "string"}}}}
    },
)
async def import_items(
    idem: IdemUser,
    request: Request,
    uow: Uow,
    principal: MenuManage,
    commit: Annotated[bool, Query()] = False,
) -> Response:
    """Dry run by default: a per-line report. `?commit=true` imports every row or none."""
    if not request.headers.get("content-type", "").startswith("text/csv"):
        raise AppError("VALIDATION_FAILED", "Send the file as text/csv.")
    report = await menu_import.import_csv(
        uow, principal.tenant(request), await request.body(), principal.permissions, commit=commit
    )
    status = 201 if report["committed"] else 200
    return await idem.complete(uow, status, MenuImportReport.model_validate(report).model_dump(mode="json"))


# --- Items ---------------------------------------------------------------------------------


@router.get("/menu/items", response_model=ItemList)
async def list_items(
    request: Request,
    uow: Uow,
    principal: MenuRead,
    category_id: Annotated[uuid.UUID | None, Query()] = None,
    station_id: Annotated[uuid.UUID | None, Query()] = None,
    available: Annotated[bool | None, Query()] = None,
) -> dict[str, Any]:
    data = await svc.list_items(
        state_of(request),
        uow,
        principal.tenant(request),
        category_id=category_id,
        station_id=station_id,
        available=available,
    )
    return {"data": data, "next_cursor": None}


@router.get("/menu/items/{item_id}", response_model=ItemOut)
async def get_item(item_id: uuid.UUID, request: Request, uow: Uow, principal: MenuRead) -> Response:
    result = await svc.get_item(state_of(request), uow, principal.tenant(request), item_id)
    return with_etag(result, result["version"], ItemOut)


@router.post("/menu/items", status_code=201, response_model=ItemOut)
async def create_item(
    idem: IdemUser, body: ItemCreate, request: Request, uow: Uow, principal: MenuManage
) -> Response:
    result = await svc.create_item(
        state_of(request), uow, principal.tenant(request), body.model_dump(), principal.permissions
    )
    return await idem.complete(uow, 201, ItemOut.model_validate(result).model_dump(mode="json"))


@router.patch("/menu/items/{item_id}", response_model=ItemOut)
async def patch_item(
    item_id: uuid.UUID,
    body: ItemPatch,
    request: Request,
    uow: Uow,
    principal: MenuManage,
    if_match: IfMatch = None,
) -> Response:
    expected = parse_if_match(if_match)
    changes = patch_changes(
        body,
        {
            "name",
            "price",
            "charge_category",
            "station_id",
            "category_id",
            "dietary_tags",
            "allergens",
            "sort_order",
        },
    )
    result = await svc.patch_item(
        state_of(request),
        uow,
        principal.tenant(request),
        item_id,
        expected,
        changes,
        principal.permissions,
        stepped_up=has_step_up(request, principal),
    )
    return with_etag(result, result["version"], ItemOut)


@router.delete("/menu/items/{item_id}", status_code=204)
async def delete_item(item_id: uuid.UUID, request: Request, uow: Uow, principal: MenuManage) -> Response:
    await svc.delete_item(uow, principal.tenant(request), item_id)
    return Response(status_code=204)


@router.post("/menu/items/{item_id}/availability", response_model=ItemOut)
async def set_availability(
    item_id: uuid.UUID, body: AvailabilityChange, request: Request, uow: Uow, principal: MenuAvailability
) -> dict[str, Any]:
    return await svc.set_availability(
        state_of(request), uow, principal.tenant(request), item_id, body.available
    )


@router.post("/menu/items/{item_id}/image", response_model=ImageUploadOut)
async def start_image_upload(
    item_id: uuid.UUID, body: ImageUploadRequest, request: Request, uow: Uow, principal: MenuManage
) -> dict[str, Any]:
    return await svc.start_image_upload(
        state_of(request), uow, principal.tenant(request), item_id, body.content_type, body.size_bytes
    )


@router.put("/menu/items/{item_id}/modifier-groups", response_model=ItemOut)
async def set_item_groups(
    item_id: uuid.UUID, body: ItemModifierGroups, request: Request, uow: Uow, principal: MenuManage
) -> dict[str, Any]:
    return await svc.set_item_groups(
        state_of(request), uow, principal.tenant(request), item_id, body.group_ids
    )


# --- Modifier groups -----------------------------------------------------------------------


@router.get("/menu/modifier-groups", response_model=ModifierGroupList)
async def list_groups(request: Request, uow: Uow, principal: MenuRead) -> dict[str, Any]:
    return {"data": await svc.list_groups(uow, principal.tenant(request)), "next_cursor": None}


@router.post("/menu/modifier-groups", status_code=201, response_model=ModifierGroupOut)
async def create_group(
    idem: IdemUser, body: ModifierGroupCreate, request: Request, uow: Uow, principal: MenuManage
) -> Response:
    result = await svc.create_group(uow, principal.tenant(request), body.model_dump())
    return await idem.complete(uow, 201, ModifierGroupOut.model_validate(result).model_dump(mode="json"))


@router.post("/menu/modifier-groups/{group_id}/options", status_code=201, response_model=ModifierGroupOut)
async def create_option(
    idem: IdemUser,
    group_id: uuid.UUID,
    body: ModifierOptionCreate,
    request: Request,
    uow: Uow,
    principal: MenuManage,
) -> Response:
    result = await svc.create_option(
        uow, principal.tenant(request), group_id, body.model_dump(), principal.permissions
    )
    return await idem.complete(uow, 201, ModifierGroupOut.model_validate(result).model_dump(mode="json"))
