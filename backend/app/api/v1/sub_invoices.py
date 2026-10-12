"""Diyneco's invoices and credit notes to hotels (DECISIONS D78).

- /admin/hotels/{hotel_id}/invoices: billing administrators draft manual invoices, issue,
  void, credit and resend them; every write runs and is audited in that hotel's context.
- /subscription/invoices: a hotel lists and downloads its own issued documents only.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission, state_of
from app.schemas.sub_invoices import (
    CreditRequest,
    DraftCreate,
    PdfLink,
    SentOut,
    SubscriptionInvoiceList,
    SubscriptionInvoiceOut,
    VoidRequest,
)
from app.services import sub_invoices as svc
from app.services.admin import _enter

admin_router = APIRouter(prefix="/admin/hotels/{hotel_id}/invoices", tags=["admin"])
router = APIRouter(prefix="/subscription/invoices", tags=["subscription"])

BillingManage = Annotated[Principal, Depends(require_permission("platform.billing.manage"))]
SubscriptionRead = Annotated[Principal, Depends(require_permission("subscription.read"))]


def _out(data: dict[str, Any]) -> dict[str, Any]:
    return SubscriptionInvoiceOut.model_validate(data).model_dump(mode="json")


# --- Platform ------------------------------------------------------------------------------


@admin_router.get("", response_model=SubscriptionInvoiceList)
async def admin_list(
    hotel_id: uuid.UUID, request: Request, uow: Uow, principal: BillingManage
) -> dict[str, Any]:
    ctx = principal.for_hotel(request, hotel_id)
    await _enter(uow, ctx)
    return {"data": await svc.list_for_hotel(uow, ctx, include_drafts=True)}


@admin_router.post("", status_code=201, response_model=SubscriptionInvoiceOut)
async def draft(
    idem: IdemUser,
    hotel_id: uuid.UUID,
    body: DraftCreate,
    request: Request,
    uow: Uow,
    principal: BillingManage,
) -> Response:
    """A manual invoice for an approved charge, as a draft; the server works out tax and totals."""
    ctx = principal.for_hotel(request, hotel_id)
    await _enter(uow, ctx)
    data = body.model_dump()
    inv = await svc.create_draft(
        uow,
        ctx,
        lines=data["lines"],
        currency=data["currency"],
        prices_include_tax=data["prices_include_tax"],
        period_start=data["period_start"],
        period_end=data["period_end"],
        notes=data["notes"],
        reason=data["reason"],
    )
    return await idem.complete(uow, 201, _out(await svc.payload(uow, inv)))


@admin_router.post("/{invoice_id}/issue", response_model=SubscriptionInvoiceOut)
async def issue(
    idem: IdemUser,
    hotel_id: uuid.UUID,
    invoice_id: uuid.UUID,
    request: Request,
    uow: Uow,
    principal: BillingManage,
    _s: StepUp,
) -> Response:
    """Numbers, freezes, renders and emails the invoice."""
    ctx = principal.for_hotel(request, hotel_id)
    await _enter(uow, ctx)
    inv = await svc.issue(state_of(request), uow, ctx, invoice_id)
    return await idem.complete(uow, 200, _out(await svc.payload(uow, inv)))


@admin_router.post("/{invoice_id}/void", response_model=SubscriptionInvoiceOut)
async def void(
    idem: IdemUser,
    hotel_id: uuid.UUID,
    invoice_id: uuid.UUID,
    body: VoidRequest,
    request: Request,
    uow: Uow,
    principal: BillingManage,
    _s: StepUp,
) -> Response:
    ctx = principal.for_hotel(request, hotel_id)
    await _enter(uow, ctx)
    inv = await svc.void(uow, ctx, invoice_id, body.reason)
    return await idem.complete(uow, 200, _out(await svc.payload(uow, inv)))


@admin_router.post("/{invoice_id}/credit", status_code=201, response_model=SubscriptionInvoiceOut)
async def credit(
    idem: IdemUser,
    hotel_id: uuid.UUID,
    invoice_id: uuid.UUID,
    body: CreditRequest,
    request: Request,
    uow: Uow,
    principal: BillingManage,
    _s: StepUp,
) -> Response:
    """Issues a credit note for all or part of an issued invoice."""
    ctx = principal.for_hotel(request, hotel_id)
    await _enter(uow, ctx)
    note = await svc.credit(state_of(request), uow, ctx, invoice_id, body.reason, body.amount_minor)
    return await idem.complete(uow, 201, _out(await svc.payload(uow, note)))


@admin_router.post("/{invoice_id}/send", response_model=SentOut)
async def resend(
    idem: IdemUser,
    hotel_id: uuid.UUID,
    invoice_id: uuid.UUID,
    request: Request,
    uow: Uow,
    principal: BillingManage,
) -> Response:
    ctx = principal.for_hotel(request, hotel_id)
    await _enter(uow, ctx)
    inv = await svc.get(uow, ctx, invoice_id, include_drafts=False)
    sent = await svc.send(state_of(request), uow, ctx, inv)
    return await idem.complete(uow, 200, {"recipients": sent})


@admin_router.get("/{invoice_id}/pdf", response_model=PdfLink)
async def admin_pdf(
    hotel_id: uuid.UUID, invoice_id: uuid.UUID, request: Request, uow: Uow, principal: BillingManage
) -> dict[str, str]:
    ctx = principal.for_hotel(request, hotel_id)
    await _enter(uow, ctx)
    inv = await svc.get(uow, ctx, invoice_id, include_drafts=False)
    return {"url": await svc.pdf_url(state_of(request), inv)}


# --- The hotel ------------------------------------------------------------------------------


@router.get("", response_model=SubscriptionInvoiceList)
async def my_invoices(request: Request, uow: Uow, principal: SubscriptionRead) -> dict[str, Any]:
    return {"data": await svc.list_for_hotel(uow, principal.tenant(request), include_drafts=False)}


@router.get("/{invoice_id}", response_model=SubscriptionInvoiceOut)
async def my_invoice(
    invoice_id: uuid.UUID, request: Request, uow: Uow, principal: SubscriptionRead
) -> dict[str, Any]:
    ctx = principal.tenant(request)
    return await svc.payload(uow, await svc.get(uow, ctx, invoice_id, include_drafts=False))


@router.get("/{invoice_id}/pdf", response_model=PdfLink)
async def my_invoice_pdf(
    invoice_id: uuid.UUID, request: Request, uow: Uow, principal: SubscriptionRead
) -> dict[str, str]:
    """A signed address valid for 5 minutes; invoices are never at a public address."""
    inv = await svc.get(uow, principal.tenant(request), invoice_id, include_drafts=False)
    return {"url": await svc.pdf_url(state_of(request), inv)}
