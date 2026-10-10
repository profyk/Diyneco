"""/deliveries and /payments: the room-service app and payment recording."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import IdemUser, Principal, Uow, require_permission
from app.api.pagination import DEFAULT_LIMIT, Cursor, Limit, decode_cursor, page
from app.core.errors import AppError
from app.schemas.room_service import (
    AssignRequest,
    DeliveryList,
    DeliveryOut,
    PaymentList,
    PaymentMethod,
    PaymentOut,
    PaymentPreview,
    PaymentPreviewRequest,
    PaymentRequest,
)
from app.services import deliveries as dsvc
from app.services import payments as psvc

router = APIRouter(tags=["room-service"])

DeliveriesView = Annotated[Principal, Depends(require_permission("deliveries.view"))]
DeliveriesUpdate = Annotated[Principal, Depends(require_permission("deliveries.update"))]
DeliveriesManage = Annotated[Principal, Depends(require_permission("deliveries.manage"))]
PaymentsRecord = Annotated[Principal, Depends(require_permission("payments.record"))]
PaymentsRead = Annotated[Principal, Depends(require_permission("payments.read"))]


@router.get("/deliveries", response_model=DeliveryList)
async def list_deliveries(
    request: Request,
    uow: Uow,
    principal: DeliveriesView,
    scope: Annotated[Literal["ready", "mine", "all"], Query()] = "ready",
) -> dict[str, Any]:
    """`all` (everything ready or on its way) is the dispatcher's view and needs deliveries.manage."""
    if scope == "all" and "deliveries.manage" not in principal.permissions:
        raise AppError("PERMISSION_DENIED")
    return {"data": await dsvc.list_deliveries(uow, principal.tenant(request), scope), "next_cursor": None}


async def _done(idem: Any, uow: Uow, result: dict[str, Any]) -> Response:
    response: Response = await idem.complete(
        uow, 200, DeliveryOut.model_validate(result).model_dump(mode="json")
    )
    return response


@router.post("/deliveries/{order_id}/claim", response_model=DeliveryOut)
async def claim(
    idem: IdemUser, order_id: uuid.UUID, request: Request, uow: Uow, principal: DeliveriesUpdate
) -> Response:
    return await _done(idem, uow, await dsvc.claim(uow, principal.tenant(request), order_id))


@router.post("/deliveries/{order_id}/release", response_model=DeliveryOut)
async def release(
    idem: IdemUser, order_id: uuid.UUID, request: Request, uow: Uow, principal: DeliveriesUpdate
) -> Response:
    return await _done(idem, uow, await dsvc.release(uow, principal.tenant(request), order_id))


@router.post("/deliveries/{order_id}/assign", response_model=DeliveryOut)
async def assign(
    idem: IdemUser,
    order_id: uuid.UUID,
    body: AssignRequest,
    request: Request,
    uow: Uow,
    principal: DeliveriesManage,
) -> Response:
    return await _done(idem, uow, await dsvc.assign(uow, principal.tenant(request), order_id, body.user_id))


@router.post("/deliveries/{order_id}/picked-up", response_model=DeliveryOut)
async def picked_up(
    idem: IdemUser, order_id: uuid.UUID, request: Request, uow: Uow, principal: DeliveriesUpdate
) -> Response:
    return await _done(idem, uow, await dsvc.picked_up(uow, principal.tenant(request), order_id))


@router.post("/deliveries/{order_id}/delivered", response_model=DeliveryOut)
async def delivered(
    idem: IdemUser, order_id: uuid.UUID, request: Request, uow: Uow, principal: DeliveriesUpdate
) -> Response:
    return await _done(idem, uow, await dsvc.delivered(uow, principal.tenant(request), order_id))


@router.post("/deliveries/{order_id}/leave-on-room", response_model=DeliveryOut)
async def leave_on_room(
    idem: IdemUser, order_id: uuid.UUID, request: Request, uow: Uow, principal: DeliveriesUpdate
) -> Response:
    return await _done(idem, uow, await dsvc.leave_on_room(uow, principal.tenant(request), order_id))


@router.post("/payments/preview", response_model=PaymentPreview)
async def preview(
    body: PaymentPreviewRequest, request: Request, uow: Uow, principal: PaymentsRecord
) -> dict[str, Any]:
    return await psvc.preview(uow, principal.tenant(request), body.model_dump(), principal.permissions)


@router.post("/payments", status_code=201, response_model=PaymentOut)
async def record_payment(
    idem: IdemUser, body: PaymentRequest, request: Request, uow: Uow, principal: PaymentsRecord
) -> Response:
    result = await psvc.record(
        uow, principal.tenant(request), body.model_dump(), principal.permissions, idem.key
    )
    return await idem.complete(uow, 201, PaymentOut.model_validate(result).model_dump(mode="json"))


@router.get("/payments", response_model=PaymentList)
async def list_payments(
    request: Request,
    uow: Uow,
    principal: PaymentsRead,
    method: Annotated[PaymentMethod | None, Query()] = None,
    from_: Annotated[datetime | None, Query(alias="from")] = None,
    to: Annotated[datetime | None, Query()] = None,
    staff_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Limit = DEFAULT_LIMIT,
    cursor: Cursor = None,
) -> dict[str, Any]:
    rows = await psvc.list_payments(
        uow,
        principal.tenant(request),
        method=method,
        date_from=from_,
        date_to=to,
        staff_id=staff_id,
        after=decode_cursor(cursor, 1),
        limit=limit,
    )
    data, next_cursor = page(rows, limit, lambda r: [str(r[0].id)])
    return {"data": [p for _, p in data], "next_cursor": next_cursor}
