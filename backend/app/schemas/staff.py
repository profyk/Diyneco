"""Staff, invitations and custom roles."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from app.schemas.common import Name, StrictModel

Department = Annotated[str, StringConstraints(min_length=1, max_length=80)]
PermissionCode = Annotated[str, StringConstraints(pattern=r"^[a-z_]+(\.[a-z_]+){1,3}$", max_length=60)]
RoleIds = Annotated[list[uuid.UUID], Field(min_length=1, max_length=20)]


class RoleRef(BaseModel):
    id: uuid.UUID
    code: str
    name: str


class StaffMember(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    department: str | None
    status: Literal["active", "deactivated"]
    roles: list[RoleRef]
    has_pin: bool
    mfa_enabled: bool
    last_sign_in_at: datetime | None
    joined_at: datetime


class StaffList(BaseModel):
    data: list[StaffMember]
    next_cursor: str | None = None


class StaffPatch(StrictModel):
    name: Name | None = None
    department: Department | None = None


class StaffRoles(StrictModel):
    role_ids: RoleIds


class InvitationCreate(StrictModel):
    name: Name
    email: EmailStr
    department: Department | None = None
    role_ids: RoleIds


class InvitationOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    department: str | None
    roles: list[RoleRef]
    invited_by: str | None
    expires_at: datetime
    created_at: datetime


class InvitationList(BaseModel):
    data: list[InvitationOut]
    next_cursor: str | None = None


class RoleCreate(StrictModel):
    name: Name
    permissions: Annotated[list[PermissionCode], Field(min_length=1, max_length=100)]


class RolePatch(StrictModel):
    name: Name | None = None
    permissions: Annotated[list[PermissionCode], Field(min_length=1, max_length=100)] | None = None
