"""/orders for staff: list, detail, phone orders, approve, decline, cancel."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission
from app.api.pagination import DEFAULT_LIMIT, Cursor, Limit, decode_cursor, page
from app.schemas.orders import (
    OrderList,
    OrderOut,
    OrderPlaced,
    OrderStatus,
    Quote,
    ReasonBody,
    StaffOrder,
    StaffQuote,
)
from app.services import orders as svc

router = APIRouter(prefix="/orders", tags=["orders"])

OrdersRead = Annotated[Principal, Depends(require_permission("orders.read"))]
OrdersCreate = Annotated[Principal, Depends(require_permission("orders.create"))]
OrdersApprove = Annotated[Principal, Depends(require_permission("orders.approve"))]
OrdersCancel = Annotated[Principal, Depends(require_permission("orders.cancel"))]


@router.get("", response_model=OrderList)
async def list_orders(
    request: Request,
    uow: Uow,
    principal: OrdersRead,
    status: Annotated[OrderStatus | None, Query()] = None,
    room_id: Annotated[uuid.UUID | None, Query()] = None,
    stay_id: Annotated[uuid.UUID | None, Query()] = None,
    from_: Annotated[datetime | None, Query(alias="from")] = None,
    to: Annotated[datetime | None, Query()] = None,
    limit: Limit = DEFAULT_LIMIT,
    cursor: Cursor = None,
) -> dict[str, Any]:
    rows = await svc.list_orders(
        uow,
        principal.tenant(request),
        status=status,
        room_id=room_id,
        stay_id=stay_id,
        created_from=from_,
        created_to=to,
        after=decode_cursor(cursor, 1),
        limit=limit,
    )
    data, next_cursor = page(rows, limit, lambda r: [r[0].number])
    return {"data": [p for _, p in data], "next_cursor": next_cursor}


@router.post("/quote", response_model=Quote)
async def staff_quote(
    body: StaffQuote, request: Request, uow: Uow, principal: OrdersCreate
) -> dict[str, Any]:
    """Prices a cart for a room so the phone order can be confirmed with the exact total."""
    return await svc.quote(uow, principal.tenant(request), body.room_id, body.model_dump()["lines"])


@router.post("", status_code=201, response_model=OrderPlaced)
async def staff_order(
    idem: IdemUser, body: StaffOrder, request: Request, uow: Uow, principal: OrdersCreate
) -> Response:
    """A phone or fallback order for a room: same pricing and approval rules as the tablet."""
    result = await svc.place(
        uow,
        principal.tenant(request),
        room_id=body.room_id,
        body=body.model_dump(),
        idempotency_key=idem.key,
        placed_by_user=principal.user_id,
    )
    return await idem.complete(uow, 201, OrderPlaced.model_validate(result).model_dump(mode="json"))


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: uuid.UUID, request: Request, uow: Uow, principal: OrdersRead) -> dict[str, Any]:
    return await svc.get_order(uow, principal.tenant(request), order_id)


@router.post("/{order_id}/approve", response_model=OrderOut)
async def approve(
    idem: IdemUser, order_id: uuid.UUID, request: Request, uow: Uow, principal: OrdersApprove, _s: StepUp
) -> Response:
    result = await svc.approve(uow, principal.tenant(request), order_id)
    return await idem.complete(uow, 200, OrderOut.model_validate(result).model_dump(mode="json"))


@router.post("/{order_id}/decline", response_model=OrderOut)
async def decline(
    idem: IdemUser,
    order_id: uuid.UUID,
    body: ReasonBody,
    request: Request,
    uow: Uow,
    principal: OrdersApprove,
) -> Response:
    result = await svc.decline(uow, principal.tenant(request), order_id, body.reason)
    return await idem.complete(uow, 200, OrderOut.model_validate(result).model_dump(mode="json"))


@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel(
    idem: IdemUser,
    order_id: uuid.UUID,
    body: ReasonBody,
    request: Request,
    uow: Uow,
    principal: OrdersCancel,
    _s: StepUp,
) -> Response:
    result = await svc.cancel(uow, principal.tenant(request), order_id, body.reason)
    return await idem.complete(uow, 200, OrderOut.model_validate(result).model_dump(mode="json"))


@router.post("/{order_id}/items/{item_id}/void", response_model=OrderOut)
async def void_item(
    idem: IdemUser,
    order_id: uuid.UUID,
    item_id: uuid.UUID,
    body: ReasonBody,
    request: Request,
    uow: Uow,
    principal: OrdersCancel,
    _s: StepUp,
) -> Response:
    """Cancels one line of an order with a reason; its bill charge is reversed (D67)."""
    result = await svc.void_item(uow, principal.tenant(request), order_id, item_id, body.reason)
    return await idem.complete(uow, 200, OrderOut.model_validate(result).model_dump(mode="json"))
