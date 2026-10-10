"""/auth/kitchen/sign-in and /kitchen/*: the kitchen display.

The board can be read with the display's own device token, a kitchen session or a staff
token with `kitchen.view`. Actions need a person: a kitchen session or staff token with
`kitchen.update`. A kitchen session sees its display's stations; other staff see all.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, StringConstraints

from app.api.deps import (
    DevicePrincipal,
    IdemUser,
    Principal,
    Uow,
    get_device_active,
    get_principal,
    limit_auth_ip,
    require_permission,
    state_of,
)
from app.core.errors import AppError
from app.models.domain import Device
from app.schemas.common import StrictModel
from app.services import kitchen as svc
from app.services import menu as menu_svc

router = APIRouter(tags=["kitchen"])

KitchenUpdate = Annotated[Principal, Depends(require_permission("kitchen.update"))]
SoldOut = Annotated[Principal, Depends(require_permission("menu.availability"))]


class KitchenSignIn(StrictModel):
    user_id: uuid.UUID
    pin: Annotated[str, StringConstraints(pattern=r"^\d{4,6}$")]


class KitchenUser(BaseModel):
    id: uuid.UUID
    name: str


class KitchenSession(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: KitchenUser


class KitchenStaff(BaseModel):
    user_id: uuid.UUID
    name: str


class KitchenStaffList(BaseModel):
    data: list[KitchenStaff]
    next_cursor: str | None = None


class KitchenItem(BaseModel):
    id: uuid.UUID
    name: str
    quantity: int
    note: str | None
    modifiers: list[dict[str, str]]
    station: dict[str, Any]
    prep_status: str
    ready_at: datetime | None
    mine: bool


class KitchenOrder(BaseModel):
    id: uuid.UUID
    number: int
    status: str
    room: str
    special_instructions: str | None
    created_at: datetime
    accepted_at: datetime | None
    ready_at: datetime | None
    items: list[KitchenItem]


class KitchenBoard(BaseModel):
    data: list[KitchenOrder]
    next_cursor: str | None = None


def _kitchen_display(request: Request) -> Device:
    device: Device = request.state.device
    if device.kind != "kitchen":
        raise AppError("DEVICE_UNAUTHORISED")
    return device


@router.get("/kitchen/staff", response_model=KitchenStaffList)
async def sign_in_list(request: Request, uow: Uow, principal: DevicePrincipal) -> dict[str, Any]:
    _kitchen_display(request)
    return {"data": await svc.staff_for_sign_in(uow, principal.tenant(request)), "next_cursor": None}


@router.post("/auth/kitchen/sign-in", response_model=KitchenSession, dependencies=[Depends(limit_auth_ip)])
async def kitchen_sign_in(
    body: KitchenSignIn, request: Request, uow: Uow, principal: DevicePrincipal
) -> dict[str, Any]:
    device = _kitchen_display(request)
    return await svc.sign_in(
        state_of(request), uow, principal.tenant(request), device.id, body.user_id, body.pin
    )


async def _stations(request: Request, uow: Uow, principal: Principal) -> set[uuid.UUID]:
    ctx = principal.tenant(request)
    if principal.kind in ("kitchen_session", "device") and principal.device_id is not None:
        return await svc.device_stations(uow, ctx, principal.device_id)
    return await svc.all_stations(uow, ctx)


async def _board_viewer(request: Request, uow: Uow) -> Principal:
    claims = state_of(request).jwt.verify(
        request.headers.get("authorization", "").removeprefix("Bearer ").strip(), "access"
    )
    if claims.get("kind") == "device":
        principal = await get_device_active(request, uow)
        _kitchen_display(request)
        return principal
    principal = await get_principal(request, uow)
    if "kitchen.view" not in principal.permissions:
        raise AppError("PERMISSION_DENIED")
    return principal


BoardViewer = Annotated[Principal, Depends(_board_viewer)]


@router.get("/kitchen/orders", response_model=KitchenBoard)
async def kitchen_orders(request: Request, uow: Uow, principal: BoardViewer) -> dict[str, Any]:
    stations = await _stations(request, uow, principal)
    return {"data": await svc.board(uow, principal.tenant(request), stations), "next_cursor": None}


@router.post("/kitchen/orders/{order_id}/accept", response_model=KitchenOrder)
async def accept(
    idem: IdemUser, order_id: uuid.UUID, request: Request, uow: Uow, principal: KitchenUpdate
) -> Response:
    result = await svc.accept(
        uow, principal.tenant(request), order_id, await _stations(request, uow, principal)
    )
    return await idem.complete(uow, 200, KitchenOrder.model_validate(result).model_dump(mode="json"))


@router.post("/kitchen/orders/{order_id}/start", response_model=KitchenOrder)
async def start(
    idem: IdemUser, order_id: uuid.UUID, request: Request, uow: Uow, principal: KitchenUpdate
) -> Response:
    result = await svc.start(
        uow, principal.tenant(request), order_id, await _stations(request, uow, principal)
    )
    return await idem.complete(uow, 200, KitchenOrder.model_validate(result).model_dump(mode="json"))


@router.post("/kitchen/order-items/{item_id}/ready", response_model=KitchenOrder)
async def item_ready(
    idem: IdemUser, item_id: uuid.UUID, request: Request, uow: Uow, principal: KitchenUpdate
) -> Response:
    result = await svc.item_ready(
        uow, principal.tenant(request), item_id, await _stations(request, uow, principal)
    )
    return await idem.complete(uow, 200, KitchenOrder.model_validate(result).model_dump(mode="json"))


@router.post("/kitchen/order-items/{item_id}/unready", response_model=KitchenOrder)
async def item_unready(
    idem: IdemUser, item_id: uuid.UUID, request: Request, uow: Uow, principal: KitchenUpdate
) -> Response:
    result = await svc.item_unready(
        uow, principal.tenant(request), item_id, await _stations(request, uow, principal)
    )
    return await idem.complete(uow, 200, KitchenOrder.model_validate(result).model_dump(mode="json"))


class KitchenMenuItem(BaseModel):
    """A dish as the kitchen sees it: no prices (security spec)."""

    id: uuid.UUID
    name: str
    category: str
    station_id: uuid.UUID
    is_available: bool


class KitchenMenu(BaseModel):
    data: list[KitchenMenuItem]
    next_cursor: str | None = None


class SoldOutChange(StrictModel):
    available: bool


@router.get("/kitchen/menu", response_model=KitchenMenu)
async def kitchen_menu(request: Request, uow: Uow, principal: BoardViewer) -> dict[str, Any]:
    """Dishes of this display's stations, so a cook can mark one sold out (D67)."""
    stations = await _stations(request, uow, principal)
    return {
        "data": await svc.menu_for_stations(uow, principal.tenant(request), stations),
        "next_cursor": None,
    }


@router.post("/kitchen/menu-items/{item_id}/availability", response_model=KitchenMenuItem)
async def kitchen_sold_out(
    item_id: uuid.UUID, body: SoldOutChange, request: Request, uow: Uow, principal: SoldOut
) -> dict[str, Any]:
    """Sold out or back in stock; tablets stop offering the dish at once."""
    ctx = principal.tenant(request)
    await menu_svc.set_availability(state_of(request), uow, ctx, item_id, body.available)
    items = await svc.menu_for_stations(uow, ctx, None, item_id=item_id)
    if not items:
        raise AppError("NOT_FOUND")
    return items[0]
