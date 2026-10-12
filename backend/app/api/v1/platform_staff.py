"""/admin/staff: Diyneco staff accounts (DECISIONS D71), and the public step that accepts a
platform invitation (/auth/platform-invitations/accept)."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission, state_of
from app.api.v1.auth import AuthLimited, _client
from app.schemas.platform_staff import (
    PlatformInviteAccept,
    PlatformRoleList,
    PlatformStaffInvite,
    PlatformStaffList,
    PlatformStaffOut,
    PlatformStaffRoles,
)
from app.services import platform_staff as svc

router = APIRouter(prefix="/admin/staff", tags=["admin"])
public_router = APIRouter(prefix="/auth", tags=["auth"])

StaffManage = Annotated[Principal, Depends(require_permission("platform.staff.manage"))]


def _out(row: dict[str, Any]) -> dict[str, Any]:
    return PlatformStaffOut.model_validate(row).model_dump(mode="json")


@router.get("", response_model=PlatformStaffList)
async def list_staff(uow: Uow, principal: StaffManage) -> dict[str, Any]:
    return {"data": await svc.staff(uow)}


@router.get("/roles", response_model=PlatformRoleList)
async def list_roles(uow: Uow, principal: StaffManage) -> dict[str, Any]:
    return {"data": await svc.roles(uow)}


@router.post("", status_code=201, response_model=PlatformStaffOut)
async def invite(
    idem: IdemUser, body: PlatformStaffInvite, request: Request, uow: Uow, principal: StaffManage, _s: StepUp
) -> Response:
    row = await svc.invite(
        state_of(request),
        uow,
        principal.platform_actor(request),
        email=body.email,
        name=body.name,
        role_codes=body.roles,
    )
    return await idem.complete(uow, 201, _out(row))


@router.post("/{user_id}/resend-invitation", response_model=PlatformStaffOut)
async def resend_invitation(
    idem: IdemUser, user_id: uuid.UUID, request: Request, uow: Uow, principal: StaffManage
) -> Response:
    row = await svc.resend_invite(state_of(request), uow, principal.platform_actor(request), user_id)
    return await idem.complete(uow, 200, _out(row))


@router.put("/{user_id}/roles", response_model=PlatformStaffOut)
async def change_roles(
    user_id: uuid.UUID,
    body: PlatformStaffRoles,
    request: Request,
    uow: Uow,
    principal: StaffManage,
    _s: StepUp,
) -> dict[str, Any]:
    return _out(await svc.change_roles(uow, principal.platform_actor(request), user_id, body.roles))


@router.post("/{user_id}/deactivate", response_model=PlatformStaffOut)
async def deactivate(
    idem: IdemUser, user_id: uuid.UUID, request: Request, uow: Uow, principal: StaffManage, _s: StepUp
) -> Response:
    row = await svc.deactivate(uow, principal.platform_actor(request), user_id)
    return await idem.complete(uow, 200, _out(row))


@router.post("/{user_id}/reactivate", response_model=PlatformStaffOut)
async def reactivate(
    idem: IdemUser, user_id: uuid.UUID, request: Request, uow: Uow, principal: StaffManage, _s: StepUp
) -> Response:
    row = await svc.reactivate(state_of(request), uow, principal.platform_actor(request), user_id)
    return await idem.complete(uow, 200, _out(row))


@public_router.post("/platform-invitations/accept", dependencies=AuthLimited, status_code=204)
async def accept_invitation(body: PlatformInviteAccept, request: Request, uow: Uow) -> Response:
    await svc.accept_invite(uow, body.token, body.password, _client(request))
    return Response(status_code=204)
