"""/signup, /hotel, /hotel/settings, /permissions, /roles. The hotel is always the caller's
token hotel; none of these routes accept a hotel id."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse

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
from app.core.errors import AppError
from app.core.logging import request_id_var
from app.repositories.roles import RoleRepository
from app.schemas.hotel import (
    HotelOut,
    HotelPatch,
    PermissionList,
    RoleList,
    SettingsOut,
    SettingsPatch,
    SignupRequest,
    SignupResponse,
)
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


def _with_etag(body: dict[str, Any], version: int, model: type[Any]) -> JSONResponse:
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
async def signup(idem: IdemAnon, body: SignupRequest, request: Request, uow: Uow) -> JSONResponse:
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
    )
    return await idem.complete(uow, 201, result)


@router.get("/hotel", response_model=HotelOut)
async def get_hotel(request: Request, uow: Uow, principal: HotelRead) -> JSONResponse:
    body, version = await hotel_service.get_hotel(uow, principal.tenant(request))
    return _with_etag(body, version, HotelOut)


@router.patch("/hotel", response_model=HotelOut)
async def patch_hotel(
    body: HotelPatch, request: Request, uow: Uow, principal: HotelUpdate, if_match: IfMatch = None
) -> JSONResponse:
    expected = hotel_service.parse_if_match(if_match)
    result, version = await hotel_service.patch_hotel(
        uow, principal.tenant(request), expected, _changes(body, NOT_NULL_HOTEL)
    )
    return _with_etag(result, version, HotelOut)


@router.get("/hotel/settings", response_model=SettingsOut)
async def get_settings(request: Request, uow: Uow, principal: SettingsRead) -> JSONResponse:
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
) -> JSONResponse:
    expected = hotel_service.parse_if_match(if_match)
    result, version = await hotel_service.patch_settings(
        uow, principal.tenant(request), expected, _changes(body, NOT_NULL_SETTINGS)
    )
    return _with_etag(result, version, SettingsOut)


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
