"""Diyneco staff accounts (DECISIONS D71)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from app.schemas.auth import Password, Token
from app.schemas.common import StrictModel

RoleCode = Annotated[str, StringConstraints(pattern=r"^platform_[a-z_]{1,40}$")]
RoleCodes = Annotated[list[RoleCode], Field(min_length=1, max_length=10)]


class PlatformRole(BaseModel):
    code: str
    name: str
    permissions: list[str]


class PlatformRoleList(BaseModel):
    data: list[PlatformRole]


class PlatformStaffOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    status: Literal["invited", "active", "locked", "deactivated"]
    roles: list[str]
    mfa_enrolled: bool
    last_login_at: datetime | None
    created_at: datetime


class PlatformStaffList(BaseModel):
    data: list[PlatformStaffOut]


class PlatformStaffInvite(StrictModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    email: EmailStr
    roles: RoleCodes


class PlatformStaffRoles(StrictModel):
    roles: RoleCodes


class PlatformInviteAccept(StrictModel):
    token: Token
    password: Password
