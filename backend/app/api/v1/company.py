"""/admin/company and /admin/tax-rates: Diyneco's own billing identity and tax rates
(DECISIONS D72). Every change needs step-up and a reason, and is audited."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission, state_of
from app.schemas.company import (
    CompanyLogoUpload,
    CompanySettingsOut,
    CompanySettingsPut,
    TaxRateCreate,
    TaxRateList,
)
from app.schemas.hotel import LogoUploadOut
from app.services import company as svc

router = APIRouter(prefix="/admin", tags=["admin"])

CompanyManage = Annotated[Principal, Depends(require_permission("platform.company.manage"))]


@router.get("/company", response_model=CompanySettingsOut)
async def get_company(request: Request, uow: Uow, principal: CompanyManage) -> dict[str, Any]:
    return await svc.view(state_of(request), uow)


@router.put("/company", response_model=CompanySettingsOut)
async def put_company(
    body: CompanySettingsPut, request: Request, uow: Uow, principal: CompanyManage, _s: StepUp
) -> dict[str, Any]:
    """Replaces the editable settings. `version` must match (else 412); `reason` is audited."""
    return await svc.update(state_of(request), uow, principal.platform_actor(request), body.model_dump())


@router.post("/company/logo", response_model=LogoUploadOut)
async def start_logo_upload(
    body: CompanyLogoUpload, request: Request, uow: Uow, principal: CompanyManage, _s: StepUp
) -> dict[str, Any]:
    """Returns a signed URL; PUT the PNG or JPEG there within its lifetime."""
    return await svc.start_logo_upload(
        state_of(request), uow, principal.platform_actor(request), body.content_type, body.size_bytes
    )


@router.get("/tax-rates", response_model=TaxRateList)
async def list_tax_rates(uow: Uow, principal: CompanyManage) -> dict[str, Any]:
    return {"data": await svc.tax_rates(uow)}


@router.post("/tax-rates", status_code=201, response_model=TaxRateList)
async def schedule_tax_rate(
    idem: IdemUser, body: TaxRateCreate, request: Request, uow: Uow, principal: CompanyManage, _s: StepUp
) -> Response:
    rows = await svc.schedule_rate(uow, principal.platform_actor(request), body.model_dump())
    return await idem.complete(uow, 201, TaxRateList.model_validate({"data": rows}).model_dump(mode="json"))


@router.delete("/tax-rates/{rate_id}", response_model=TaxRateList)
async def withdraw_tax_rate(
    rate_id: uuid.UUID, request: Request, uow: Uow, principal: CompanyManage, _s: StepUp
) -> dict[str, Any]:
    return {"data": await svc.withdraw_rate(uow, principal.platform_actor(request), rate_id)}
