"""/signup, /hotel, /hotel/logo, /hotel/onboarding, /hotel/settings, /permissions, /roles.
The hotel is always the caller's token hotel; none of these routes accept a hotel id."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Path, Request
from fastapi.responses import JSONResponse, Response

from app.api.deps import (
    IdemAnon,
    Principal,
    StepUp,
    Uow,
    client_ip,
    limit_auth_ip,
    require_permission,
    state_of,
)
from app.core.countries import country as country_of
from app.core.countries import regions as regions_of
from app.core.currencies import CURRENCIES
from app.core.errors import AppError
from app.core.logging import request_id_var
from app.repositories.roles import RoleRepository
from app.schemas.hotel import (
    CountryList,
    CurrencyList,
    HotelOut,
    HotelPatch,
    LogoUploadOut,
    LogoUploadRequest,
    OnboardingOut,
    PermissionList,
    RegionList,
    RoleList,
    SettingsOut,
    SettingsPatch,
    SignupRequest,
    SignupResponse,
)
from app.services import countries as countries_service
from app.services import hotel as hotel_service
from app.services.auth import ClientInfo
from app.services.signup import signup as signup_service

router = APIRouter(tags=["hotel"])

HotelRead = Annotated[Principal, Depends(require_permission("hotel.read"))]
HotelUpdate = Annotated[Principal, Depends(require_permission("hotel.update"))]
SettingsRead = Annotated[Principal, Depends(require_permission("settings.read"))]
SettingsUpdate = Annotated[Principal, Depends(require_permission("settings.update"))]
StaffRead = Annotated[Principal, Depends(require_permission("staff.read"))]
IfMatch = Annotated[str | None, Header(alias="If-Match")]

NOT_NULL_HOTEL = {"name"}
NOT_NULL_SETTINGS = set(hotel_service.SETTINGS_FIELDS) - {"vat_number", "wifi_name"}


def _with_etag(body: dict[str, Any], version: int, model: type[Any]) -> Response:
    return JSONResponse(
        model.model_validate(body).model_dump(mode="json"), headers={"ETag": hotel_service.etag(version)}
    )


def _changes(patch: Any, not_null: set[str]) -> dict[str, Any]:
    changes: dict[str, Any] = patch.model_dump(exclude_unset=True, mode="json")
    nulls = sorted(k for k, v in changes.items() if v is None and k in not_null)
    if nulls:
        raise AppError(
            "VALIDATION_FAILED",
            details={"fields": [{"field": f, "problem": "Cannot be empty.", "type": "null"} for f in nulls]},
        )
    return changes


@router.post("/signup", status_code=201, dependencies=[Depends(limit_auth_ip)], response_model=SignupResponse)
async def signup(idem: IdemAnon, body: SignupRequest, request: Request, uow: Uow) -> Response:
    client = ClientInfo(
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        request_id=request_id_var.get(),
        web=False,
    )
    result = await signup_service(
        state_of(request),
        uow,
        owner_name=body.owner.name,
        email=str(body.owner.email),
        password=body.owner.password,
        hotel=body.hotel.model_dump(mode="json", exclude_none=True),
        client=client,
        accepted_documents=body.accepted_documents,
        owner_phone=body.owner.phone,
    )
    return await idem.complete(uow, 201, result)


@router.get("/hotel", response_model=HotelOut)
async def get_hotel(request: Request, uow: Uow, principal: HotelRead) -> Response:
    body, version = await hotel_service.get_hotel(state_of(request), uow, principal.tenant(request))
    return _with_etag(body, version, HotelOut)


@router.patch("/hotel", response_model=HotelOut)
async def patch_hotel(
    body: HotelPatch, request: Request, uow: Uow, principal: HotelUpdate, if_match: IfMatch = None
) -> Response:
    expected = hotel_service.parse_if_match(if_match)
    result, version = await hotel_service.patch_hotel(
        state_of(request), uow, principal.tenant(request), expected, _changes(body, NOT_NULL_HOTEL)
    )
    return _with_etag(result, version, HotelOut)


@router.post("/hotel/logo", response_model=LogoUploadOut)
async def start_logo_upload(
    body: LogoUploadRequest, request: Request, uow: Uow, principal: HotelUpdate
) -> dict[str, Any]:
    """Returns a signed URL; PUT the file there with the given headers within its lifetime."""
    return await hotel_service.start_logo_upload(
        state_of(request), uow, principal.tenant(request), body.content_type, body.size_bytes
    )


@router.get("/hotel/onboarding", response_model=OnboardingOut)
async def get_onboarding(request: Request, uow: Uow, principal: HotelRead) -> dict[str, Any]:
    return await hotel_service.onboarding(uow, principal.tenant(request))


@router.get("/hotel/settings", response_model=SettingsOut)
async def get_settings(request: Request, uow: Uow, principal: SettingsRead) -> Response:
    body, version = await hotel_service.get_settings(uow, principal.tenant(request))
    return _with_etag(body, version, SettingsOut)


@router.patch("/hotel/settings", response_model=SettingsOut)
async def patch_settings(
    body: SettingsPatch,
    request: Request,
    uow: Uow,
    principal: SettingsUpdate,
    _step_up: StepUp,
    if_match: IfMatch = None,
) -> Response:
    expected = hotel_service.parse_if_match(if_match)
    result, version = await hotel_service.patch_settings(
        uow, principal.tenant(request), expected, _changes(body, NOT_NULL_SETTINGS)
    )
    return _with_etag(result, version, SettingsOut)


@router.get("/currencies", response_model=CurrencyList)
async def currencies() -> dict[str, Any]:
    """Currencies a hotel or a plan may use (public: the signup form needs it)."""
    return {
        "data": [
            {"code": c.code, "name": c.name, "symbol": c.symbol, "decimals": c.decimals}
            for c in CURRENCIES.values()
        ]
    }


@router.get("/countries", response_model=CountryList)
async def countries(uow: Uow) -> dict[str, Any]:
    """Countries where new hotels can sign up, with the defaults each suggests (public: the
    signup form needs it). The platform chooses them (operational countries, D84)."""
    return {"data": await countries_service.public_list(uow)}


@router.get("/countries/{code}/regions", response_model=RegionList)
async def country_regions(code: Annotated[str, Path(pattern=r"^[A-Z]{2}$")]) -> dict[str, Any]:
    """A country's provinces, states or other first-level regions (ISO 3166-2, D85). Public:
    the signup form and hotel settings use it. An empty list means the region is free text."""
    if country_of(code) is None:
        raise AppError("NOT_FOUND")
    label, items = regions_of(code)
    return {"label": label, "data": [{"code": c, "name": n} for c, n in items]}


@router.get("/permissions", response_model=PermissionList)
async def list_permissions(request: Request, uow: Uow, principal: StaffRead) -> dict[str, Any]:
    perms = await RoleRepository(uow.session, principal.tenant(request)).hotel_permissions()
    return {
        "data": [{"code": p.code, "description": p.description, "sensitive": p.sensitive} for p in perms],
        "next_cursor": None,
    }


@router.get("/roles", response_model=RoleList)
async def list_roles(request: Request, uow: Uow, principal: StaffRead) -> dict[str, Any]:
    rows = await RoleRepository(uow.session, principal.tenant(request)).roles_with_permissions()
    return {
        "data": [
            {"id": r.id, "code": r.code, "name": r.name, "is_system": r.is_system, "permissions": perms}
            for r, perms in rows
        ],
        "next_cursor": None,
    }
