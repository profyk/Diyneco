"""/guest: the guest tablet. Device token only; hotel, room and stay come from it, never from
the request, and every response is limited to the room's active stay."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Request, Response

from app.api.deps import DeviceAnyState, DevicePrincipal, IdemDevice, Principal, Uow, state_of
from app.core.errors import AppError
from app.models.domain import Device
from app.schemas.orders import (
    GuestFolio,
    GuestInfo,
    GuestMenu,
    GuestSession,
    OrderList,
    OrderOut,
    OrderPlaced,
    PlaceOrder,
    Quote,
    QuoteRequest,
)
from app.services import guest as svc
from app.services import orders as order_service

router = APIRouter(prefix="/guest", tags=["guest"])


def _tablet(request: Request) -> Device:
    device: Device = request.state.device
    if device.kind != "guest" or device.room_id is None:
        raise AppError("DEVICE_UNAUTHORISED")
    return device


def _ctx(request: Request, principal: Principal) -> Any:
    return principal.tenant(request)


@router.get("/session", response_model=GuestSession)
async def session(request: Request, uow: Uow, principal: DeviceAnyState) -> dict[str, Any]:
    """Works while locked, so the tablet can show its paused screen."""
    return await svc.session(state_of(request), uow, _ctx(request, principal), _tablet(request))


@router.get("/menu", response_model=GuestMenu)
async def menu(request: Request, uow: Uow, principal: DevicePrincipal) -> dict[str, Any]:
    _tablet(request)
    return await svc.menu(state_of(request), uow, _ctx(request, principal))


@router.post("/orders/quote", response_model=Quote)
async def quote(body: QuoteRequest, request: Request, uow: Uow, principal: DevicePrincipal) -> dict[str, Any]:
    device = _tablet(request)
    assert device.room_id is not None  # noqa: S101 - checked by _tablet
    return await order_service.quote(
        uow, _ctx(request, principal), device.room_id, body.model_dump()["lines"]
    )


@router.post("/orders", status_code=201, response_model=OrderPlaced)
async def place_order(
    idem: IdemDevice, body: PlaceOrder, request: Request, uow: Uow, principal: DevicePrincipal
) -> Response:
    device = _tablet(request)
    assert device.room_id is not None  # noqa: S101 - checked by _tablet
    result = await order_service.place(
        uow,
        _ctx(request, principal),
        room_id=device.room_id,
        body=body.model_dump(),
        idempotency_key=idem.key,
        placed_by_user=None,
    )
    return await idem.complete(uow, 201, OrderPlaced.model_validate(result).model_dump(mode="json"))


@router.get("/orders", response_model=OrderList)
async def my_orders(request: Request, uow: Uow, principal: DevicePrincipal) -> dict[str, Any]:
    device = _tablet(request)
    ctx = _ctx(request, principal)
    assert device.room_id is not None  # noqa: S101 - checked by _tablet
    stay = await svc.active_stay(uow, ctx, device.room_id)
    if stay is None:
        return {"data": [], "next_cursor": None}  # welcome state: no history
    rows = await order_service.list_orders(uow, ctx, stay_id=stay.id, limit=200)
    return {"data": [p for _, p in rows[:200]], "next_cursor": None}


@router.get("/orders/{order_id}", response_model=OrderOut)
async def my_order(
    order_id: uuid.UUID, request: Request, uow: Uow, principal: DevicePrincipal
) -> dict[str, Any]:
    ctx = _ctx(request, principal)
    stay = await svc.require_stay(uow, ctx, _tablet(request))
    return await order_service.get_order(uow, ctx, order_id, stay_id=stay.id)


@router.get("/folio", response_model=GuestFolio)
async def my_folio(request: Request, uow: Uow, principal: DevicePrincipal) -> dict[str, Any]:
    ctx = _ctx(request, principal)
    stay = await svc.require_stay(uow, ctx, _tablet(request))
    return await svc.folio(uow, ctx, stay)


@router.get("/info", response_model=GuestInfo)
async def info(request: Request, uow: Uow, principal: DeviceAnyState) -> dict[str, Any]:
    _tablet(request)
    return await svc.info(uow, _ctx(request, principal))
