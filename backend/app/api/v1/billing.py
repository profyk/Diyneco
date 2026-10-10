"""/folios, /adjustments, checkout and /invoices: the bill for staff, other charges, discounts,
two-person adjustments, checkout, invoices and credit notes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission, state_of
from app.schemas.billing import (
    AdjustmentList,
    AdjustmentOut,
    AdjustmentRequest,
    ChargeCategoryList,
    ChargeRequest,
    CheckoutOut,
    CheckoutRequest,
    CheckoutSummary,
    CreditNoteRequest,
    DiscountRequest,
    FolioOut,
    InvoiceEmailOut,
    InvoiceEmailRequest,
    InvoiceList,
    InvoiceOut,
    RejectRequest,
    SignedUrl,
)
from app.services import billing as svc
from app.services import checkout

router = APIRouter(tags=["billing"])

FolioRead = Annotated[Principal, Depends(require_permission("folio.read"))]
FolioCharge = Annotated[Principal, Depends(require_permission("folio.charge"))]
FolioDiscount = Annotated[Principal, Depends(require_permission("folio.discount"))]
AdjustRequest = Annotated[Principal, Depends(require_permission("folio.adjust.request"))]
AdjustApprove = Annotated[Principal, Depends(require_permission("folio.adjust.approve"))]


@router.get("/charge-categories", response_model=ChargeCategoryList)
async def charge_categories(request: Request, uow: Uow, principal: FolioRead) -> dict[str, Any]:
    return {"data": await svc.chargeable_categories(uow, principal.tenant(request)), "next_cursor": None}


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


@router.get("/adjustments", response_model=AdjustmentList)
async def list_adjustments(
    request: Request,
    uow: Uow,
    principal: FolioRead,
    status: Annotated[Literal["pending", "approved", "rejected"] | None, Query()] = None,
) -> dict[str, Any]:
    return {"data": await svc.list_adjustments(uow, principal.tenant(request), status), "next_cursor": None}


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


# --- Checkout and invoices -------------------------------------------------------------------

CheckoutPerform = Annotated[Principal, Depends(require_permission("checkout.perform"))]
InvoicesRead = Annotated[Principal, Depends(require_permission("invoices.read"))]
InvoicesSend = Annotated[Principal, Depends(require_permission("invoices.send"))]
InvoicesCredit = Annotated[Principal, Depends(require_permission("invoices.credit"))]


@router.get("/stays/{stay_id}/checkout-summary", response_model=CheckoutSummary)
async def checkout_summary(
    stay_id: uuid.UUID, request: Request, uow: Uow, principal: CheckoutPerform
) -> dict[str, Any]:
    return await checkout.summary(uow, principal.tenant(request), stay_id)


@router.post("/stays/{stay_id}/checkout", response_model=CheckoutOut)
async def check_out(
    idem: IdemUser,
    stay_id: uuid.UUID,
    body: CheckoutRequest,
    request: Request,
    uow: Uow,
    principal: CheckoutPerform,
    _s: StepUp,
) -> Response:
    result = await checkout.check_out(
        state_of(request), uow, principal.tenant(request), stay_id, body.model_dump(), principal.permissions
    )
    return await idem.complete(uow, 200, CheckoutOut.model_validate(result).model_dump(mode="json"))


@router.get("/stays/{stay_id}/invoices", response_model=InvoiceList)
async def stay_invoices(
    stay_id: uuid.UUID, request: Request, uow: Uow, principal: InvoicesRead
) -> dict[str, Any]:
    return {
        "data": await checkout.list_invoices(uow, principal.tenant(request), stay_id),
        "next_cursor": None,
    }


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    invoice_id: uuid.UUID, request: Request, uow: Uow, principal: InvoicesRead
) -> dict[str, Any]:
    return await checkout.get_invoice(uow, principal.tenant(request), invoice_id)


@router.get("/invoices/{invoice_id}/pdf", response_model=SignedUrl)
async def invoice_pdf(
    invoice_id: uuid.UUID, request: Request, uow: Uow, principal: InvoicesRead
) -> dict[str, Any]:
    return await checkout.pdf_url(state_of(request), uow, principal.tenant(request), invoice_id)


@router.post("/invoices/{invoice_id}/email", response_model=InvoiceEmailOut)
async def email_invoice(
    idem: IdemUser,
    invoice_id: uuid.UUID,
    body: InvoiceEmailRequest,
    request: Request,
    uow: Uow,
    principal: InvoicesSend,
) -> Response:
    result = await checkout.email_invoice(
        state_of(request), uow, principal.tenant(request), invoice_id, [str(t) for t in body.to]
    )
    return await idem.complete(uow, 200, InvoiceEmailOut.model_validate(result).model_dump(mode="json"))


@router.post("/invoices/{invoice_id}/credit-note", status_code=201, response_model=InvoiceOut)
async def credit_note(
    idem: IdemUser,
    invoice_id: uuid.UUID,
    body: CreditNoteRequest,
    request: Request,
    uow: Uow,
    principal: InvoicesCredit,
    _s: StepUp,
) -> Response:
    result = await checkout.credit_note(
        state_of(request), uow, principal.tenant(request), invoice_id, body.reason
    )
    return await idem.complete(uow, 201, InvoiceOut.model_validate(result).model_dump(mode="json"))
