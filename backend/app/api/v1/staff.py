"""/staff, /staff/invitations and custom roles (POST/PATCH /roles; GET /roles lives in hotel.py).

`staff.manage` and `roles.manage` are sensitive permissions (security spec †), so every
endpoint that uses them needs step-up, including the ones the API table leaves unmarked
(DECISIONS D19).
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission, state_of
from app.api.http import patch_changes
from app.schemas.hotel import RoleOut
from app.schemas.staff import (
    InvitationCreate,
    InvitationList,
    InvitationOut,
    RoleCreate,
    RolePatch,
    StaffList,
    StaffMember,
    StaffPatch,
    StaffRoles,
)
from app.services import staff as svc

router = APIRouter(tags=["staff"])

StaffRead = Annotated[Principal, Depends(require_permission("staff.read"))]
StaffManage = Annotated[Principal, Depends(require_permission("staff.manage"))]
RolesManage = Annotated[Principal, Depends(require_permission("roles.manage"))]


@router.get("/staff", response_model=StaffList)
async def list_staff(request: Request, uow: Uow, principal: StaffRead) -> dict[str, Any]:
    return {"data": await svc.list_staff(uow, principal.tenant(request)), "next_cursor": None}


@router.patch("/staff/{user_id}", response_model=StaffMember)
async def patch_staff(
    user_id: uuid.UUID, body: StaffPatch, request: Request, uow: Uow, principal: StaffManage, _s: StepUp
) -> dict[str, Any]:
    return await svc.patch_member(uow, principal.tenant(request), user_id, patch_changes(body, {"name"}))


@router.put("/staff/{user_id}/roles", response_model=StaffMember)
async def set_staff_roles(
    user_id: uuid.UUID, body: StaffRoles, request: Request, uow: Uow, principal: StaffManage, _s: StepUp
) -> dict[str, Any]:
    return await svc.set_roles(uow, principal.tenant(request), user_id, body.role_ids, principal.permissions)


@router.post("/staff/{user_id}/deactivate", response_model=StaffMember)
async def deactivate_staff(
    user_id: uuid.UUID, request: Request, uow: Uow, principal: StaffManage, _s: StepUp
) -> dict[str, Any]:
    return await svc.deactivate(uow, principal.tenant(request), user_id, principal.permissions)


@router.post("/staff/{user_id}/pin/reset", status_code=204)
async def reset_staff_pin(
    user_id: uuid.UUID, request: Request, uow: Uow, principal: StaffManage, _s: StepUp
) -> Response:
    await svc.reset_pin(uow, principal.tenant(request), user_id, principal.permissions)
    return Response(status_code=204)


@router.get("/staff/invitations", response_model=InvitationList)
async def list_invitations(request: Request, uow: Uow, principal: StaffRead) -> dict[str, Any]:
    return {"data": await svc.list_invitations(uow, principal.tenant(request)), "next_cursor": None}


@router.post("/staff/invitations", status_code=201, response_model=InvitationOut)
async def invite_staff(
    idem: IdemUser,
    body: InvitationCreate,
    request: Request,
    uow: Uow,
    principal: StaffManage,
    _s: StepUp,
) -> JSONResponse:
    result = await svc.invite(
        state_of(request), uow, principal.tenant(request), body.model_dump(), principal.permissions
    )
    return await idem.complete(uow, 201, InvitationOut.model_validate(result).model_dump(mode="json"))


@router.delete("/staff/invitations/{invitation_id}", status_code=204)
async def cancel_invitation(
    invitation_id: uuid.UUID, request: Request, uow: Uow, principal: StaffManage, _s: StepUp
) -> Response:
    await svc.cancel_invitation(uow, principal.tenant(request), invitation_id)
    return Response(status_code=204)


@router.post("/roles", status_code=201, response_model=RoleOut)
async def create_role(
    idem: IdemUser, body: RoleCreate, request: Request, uow: Uow, principal: RolesManage, _s: StepUp
) -> JSONResponse:
    result = await svc.create_role(uow, principal.tenant(request), body.model_dump(), principal.permissions)
    return await idem.complete(uow, 201, RoleOut.model_validate(result).model_dump(mode="json"))


@router.patch("/roles/{role_id}", response_model=RoleOut)
async def patch_role(
    role_id: uuid.UUID, body: RolePatch, request: Request, uow: Uow, principal: RolesManage, _s: StepUp
) -> dict[str, Any]:
    return await svc.patch_role(
        uow,
        principal.tenant(request),
        role_id,
        patch_changes(body, {"name", "permissions"}),
        principal.permissions,
    )
