"""Legal documents (DECISIONS D70): public reading, staff acceptance, the guest tablet's
documents and platform drafting and publishing under /admin/legal-documents."""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import (
    CurrentPrincipal,
    DeviceAnyState,
    IdemUser,
    Principal,
    StepUp,
    Uow,
    require_permission,
)
from app.core.errors import AppError
from app.schemas.legal import (
    LegalAccept,
    LegalDocumentList,
    LegalDocumentOut,
    LegalDraftCreate,
    LegalDraftPatch,
)
from app.services import legal as svc

router = APIRouter(tags=["legal"])
admin_router = APIRouter(prefix="/admin/legal-documents", tags=["admin"])

LegalManage = Annotated[Principal, Depends(require_permission("platform.legal.manage"))]
AUDIENCES = {"merchant": svc.MERCHANT_REQUIRED, "guest": svc.GUEST_KINDS, "all": svc.KINDS}


def _person(principal: Principal) -> Principal:
    """Acceptance is personal: only a signed-in member of the hotel's staff can give it."""
    if principal.kind != "staff":
        raise AppError("PERMISSION_DENIED")
    return principal


@router.get("/legal/documents", response_model=LegalDocumentList)
async def documents(
    uow: Uow,
    country: Annotated[str | None, Query(pattern=r"^[A-Z]{2}$")] = None,
    audience: Literal["merchant", "guest", "all"] = "all",
) -> dict[str, Any]:
    """Current published version of each document for a country (public: signup shows them)."""
    return {"data": await svc.public_documents(uow, country, AUDIENCES[audience])}


@router.get("/legal/documents/{document_id}", response_model=LegalDocumentOut)
async def document(document_id: uuid.UUID, uow: Uow) -> dict[str, Any]:
    return await svc.public_document(uow, document_id)


@router.get("/legal/pending", response_model=LegalDocumentList)
async def pending(request: Request, uow: Uow, principal: CurrentPrincipal) -> dict[str, Any]:
    """Current merchant documents the caller has not accepted yet for this hotel."""
    ctx = _person(principal).tenant(request)
    return {"data": await svc.pending_for(uow, ctx)}


@router.post("/legal/accept", response_model=LegalDocumentList)
async def accept(
    idem: IdemUser, body: LegalAccept, request: Request, uow: Uow, principal: CurrentPrincipal
) -> Response:
    ctx = _person(principal).tenant(request)
    left = await svc.accept(uow, ctx, body.document_ids, user_agent=request.headers.get("user-agent"))
    return await idem.complete(
        uow, 200, LegalDocumentList.model_validate({"data": left}).model_dump(mode="json")
    )


@router.get("/guest/legal", response_model=LegalDocumentList)
async def guest_documents(request: Request, uow: Uow, principal: DeviceAnyState) -> dict[str, Any]:
    """Guest terms and privacy notice for the tablet's hotel country."""
    ctx = principal.tenant(request)
    return {"data": await svc.public_documents(uow, await svc.hotel_country(uow, ctx), svc.GUEST_KINDS)}


# --- Platform -----------------------------------------------------------------------------


@admin_router.get("", response_model=LegalDocumentList)
async def admin_list(uow: Uow, principal: LegalManage) -> dict[str, Any]:
    return {"data": await svc.admin_list(uow)}


@admin_router.post("", status_code=201, response_model=LegalDocumentOut)
async def create_draft(
    idem: IdemUser, body: LegalDraftCreate, request: Request, uow: Uow, principal: LegalManage
) -> Response:
    doc = await svc.create_draft(uow, principal.platform_actor(request), body.model_dump())
    return await idem.complete(uow, 201, LegalDocumentOut.model_validate(doc).model_dump(mode="json"))


@admin_router.patch("/{document_id}", response_model=LegalDocumentOut)
async def update_draft(
    document_id: uuid.UUID, body: LegalDraftPatch, uow: Uow, principal: LegalManage
) -> dict[str, Any]:
    changes = body.model_dump(exclude_unset=True)
    if not changes or any(changes.get(k) is None for k in ("title", "body") if k in changes):
        raise AppError("VALIDATION_FAILED", "Nothing to change, or a title or text was cleared.")
    return await svc.update_draft(uow, document_id, changes)


@admin_router.delete("/{document_id}", status_code=204)
async def delete_draft(document_id: uuid.UUID, uow: Uow, principal: LegalManage) -> Response:
    await svc.delete_draft(uow, document_id)
    return Response(status_code=204)


@admin_router.post("/{document_id}/publish", response_model=LegalDocumentOut)
async def publish(
    idem: IdemUser, document_id: uuid.UUID, request: Request, uow: Uow, principal: LegalManage, _s: StepUp
) -> Response:
    doc = await svc.publish(uow, principal.platform_actor(request), document_id)
    return await idem.complete(uow, 200, LegalDocumentOut.model_validate(doc).model_dump(mode="json"))
