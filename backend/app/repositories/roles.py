"""Roles and permissions visible to one hotel: system hotel roles plus its own custom roles."""

from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import TenantContext
from app.models.tenancy import Permission, Role, RolePermission

PLATFORM_ROLE_PREFIX = "platform_"


class RoleRepository:
    def __init__(self, session: AsyncSession, ctx: TenantContext) -> None:
        self.s = session
        self.ctx = ctx

    async def hotel_permissions(self) -> list[Permission]:
        return list(
            (
                await self.s.execute(
                    select(Permission).where(Permission.scope == "hotel").order_by(Permission.code)
                )
            )
            .scalars()
            .all()
        )

    async def roles_with_permissions(self) -> list[tuple[Role, list[str]]]:
        roles = (
            (
                await self.s.execute(
                    select(Role)
                    .where(
                        ((Role.hotel_id.is_(None)) & (~Role.code.startswith(PLATFORM_ROLE_PREFIX)))
                        | (Role.hotel_id == self.ctx.hotel_id)
                    )
                    .order_by(Role.is_system.desc(), Role.created_at)
                )
            )
            .scalars()
            .all()
        )
        perms: dict[uuid.UUID, list[str]] = defaultdict(list)
        if roles:
            for role_id, code in (
                await self.s.execute(
                    select(RolePermission.role_id, RolePermission.permission_code)
                    .where(RolePermission.role_id.in_([r.id for r in roles]))
                    .order_by(RolePermission.permission_code)
                )
            ).all():
                perms[role_id].append(code)
        return [(r, perms[r.id]) for r in roles]

    async def system_role_id(self, code: str) -> uuid.UUID:
        return (
            await self.s.execute(select(Role.id).where(Role.hotel_id.is_(None), Role.code == code))
        ).scalar_one()
