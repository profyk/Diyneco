"""/folios and /adjustments: the bill for staff, other charges, discounts and two-person
adjustments."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission
from app.schemas.billing import (
    AdjustmentOut,
    AdjustmentRequest,
    ChargeRequest,
    DiscountRequest,
    FolioOut,
    RejectRequest,
)
from app.services import billing as svc

router = APIRouter(tags=["billing"])

FolioRead = Annotated[Principal, Depends(require_permission("folio.read"))]
FolioCharge = Annotated[Principal, Depends(require_permission("folio.charge"))]
FolioDiscount = Annotated[Principal, Depends(require_permission("folio.discount"))]
AdjustRequest = Annotated[Principal, Depends(require_permission("folio.adjust.request"))]
AdjustApprove = Annotated[Principal, Depends(require_permission("folio.adjust.approve"))]


@router.get("/folios/{stay_id}", response_model=FolioOut)
async def get_folio(stay_id: uuid.UUID, request: Request, uow: Uow, principal: FolioRead) -> dict[str, Any]:
    return await svc.view(uow, principal.tenant(request), stay_id)


@router.post("/folios/{stay_id}/charges", status_code=201, response_model=FolioOut)
async def add_charge(
    idem: IdemUser,
    stay_id: uuid.UUID,
    body: ChargeRequest,
    request: Request,
    uow: Uow,
    principal: FolioCharge,
) -> Response:
    result = await svc.add_charge(uow, principal.tenant(request), stay_id, body.model_dump())
    return await idem.complete(uow, 201, FolioOut.model_validate(result).model_dump(mode="json"))


@router.post("/folios/{stay_id}/discounts", status_code=201, response_model=FolioOut)
async def add_discount(
    idem: IdemUser,
    stay_id: uuid.UUID,
    body: DiscountRequest,
    request: Request,
    uow: Uow,
    principal: FolioDiscount,
    _s: StepUp,
) -> Response:
    result = await svc.add_discount(uow, principal.tenant(request), stay_id, body.model_dump())
    return await idem.complete(uow, 201, FolioOut.model_validate(result).model_dump(mode="json"))


@router.post("/adjustments", status_code=201, response_model=AdjustmentOut)
async def request_adjustment(
    idem: IdemUser, body: AdjustmentRequest, request: Request, uow: Uow, principal: AdjustRequest
) -> Response:
    result = await svc.request_adjustment(uow, principal.tenant(request), body.model_dump())
    return await idem.complete(uow, 201, AdjustmentOut.model_validate(result).model_dump(mode="json"))


@router.post("/adjustments/{adjustment_id}/approve", response_model=AdjustmentOut)
async def approve_adjustment(
    idem: IdemUser,
    adjustment_id: uuid.UUID,
    request: Request,
    uow: Uow,
    principal: AdjustApprove,
    _s: StepUp,
) -> Response:
    result = await svc.approve_adjustment(uow, principal.tenant(request), adjustment_id)
    return await idem.complete(uow, 200, AdjustmentOut.model_validate(result).model_dump(mode="json"))


@router.post("/adjustments/{adjustment_id}/reject", response_model=AdjustmentOut)
async def reject_adjustment(
    idem: IdemUser,
    adjustment_id: uuid.UUID,
    body: RejectRequest,
    request: Request,
    uow: Uow,
    principal: AdjustApprove,
) -> Response:
    result = await svc.reject_adjustment(uow, principal.tenant(request), adjustment_id, body.reason)
    return await idem.complete(uow, 200, AdjustmentOut.model_validate(result).model_dump(mode="json"))
