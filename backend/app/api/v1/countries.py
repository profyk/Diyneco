"""/admin/countries: the countries where new hotels can sign up (operational countries, D84).
Switching a country needs step-up and a reason, and is audited."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from app.api.deps import Principal, StepUp, Uow, require_permission
from app.schemas.countries import AdminCountryList, AdminCountryOut, CountryCode, CountryPut
from app.services import countries as svc

router = APIRouter(prefix="/admin", tags=["admin"])

CountriesManage = Annotated[Principal, Depends(require_permission("platform.countries.manage"))]


@router.get("/countries", response_model=AdminCountryList)
async def list_countries(uow: Uow, principal: CountriesManage) -> dict[str, Any]:
    """Every country Diyneco knows, whether it takes signups, and how many hotels it has."""
    return {"data": await svc.admin_list(uow)}


@router.put("/countries/{code}", response_model=AdminCountryOut)
async def put_country(
    code: CountryCode, body: CountryPut, request: Request, uow: Uow, principal: CountriesManage, _s: StepUp
) -> dict[str, Any]:
    """Switches signups on or off for a country. Existing hotels are never affected."""
    return await svc.set_operational(
        uow, principal.platform_actor(request), code, body.operational, body.reason
    )
