"""Members, their roles, invitations and custom roles of one hotel. Every query filters by
the context's hotel_id (RLS enforces the same underneath)."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, exists, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import TenantContext
from app.models.tenancy import (
    HotelUser,
    Invitation,
    MfaFactor,
    Role,
    RolePermission,
    Session,
    User,
    UserRole,
)
from app.repositories.roles import PLATFORM_ROLE_PREFIX


class StaffRepository:
    def __init__(self, session: AsyncSession, ctx: TenantContext) -> None:
        self.s = session
        self.ctx = ctx

    # --- members -------------------------------------------------------------------------

    async def members(self) -> list[tuple[HotelUser, User, bool]]:
        mfa = (
            exists().where(MfaFactor.user_id == User.id, MfaFactor.confirmed_at.is_not(None)).correlate(User)
        )
        rows = (
            await self.s.execute(
                select(HotelUser, User, mfa)
                .join(User, User.id == HotelUser.user_id)
                .where(HotelUser.hotel_id == self.ctx.hotel_id)
                .order_by(HotelUser.status, func.lower(User.name), HotelUser.id)
            )
        ).all()
        return [(r[0], r[1], bool(r[2])) for r in rows]

    async def member(self, user_id: uuid.UUID, *, for_update: bool = False) -> tuple[HotelUser, User] | None:
        q = (
            select(HotelUser, User)
            .join(User, User.id == HotelUser.user_id)
            .where(HotelUser.hotel_id == self.ctx.hotel_id, HotelUser.user_id == user_id)
        )
        if for_update:
            q = q.with_for_update(of=HotelUser)
        row = (await self.s.execute(q)).first()
        return (row[0], row[1]) if row else None

    async def member_by_email(self, email: str) -> HotelUser | None:
        return (
            await self.s.execute(
                select(HotelUser)
                .join(User, User.id == HotelUser.user_id)
                .where(HotelUser.hotel_id == self.ctx.hotel_id, User.email == email)
            )
        ).scalar_one_or_none()

    async def roles_by_member(self, hotel_user_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[Role]]:
        out: dict[uuid.UUID, list[Role]] = defaultdict(list)
        if not hotel_user_ids:
            return out
        rows = (
            await self.s.execute(
                select(UserRole.hotel_user_id, Role)
                .join(Role, Role.id == UserRole.role_id)
                .where(UserRole.hotel_id == self.ctx.hotel_id, UserRole.hotel_user_id.in_(hotel_user_ids))
                .order_by(Role.name)
            )
        ).all()
        for hu_id, role in rows:
            out[hu_id].append(role)
        return out

    async def member_permissions(self, hotel_user_id: uuid.UUID) -> set[str]:
        rows = (
            await self.s.execute(
                select(RolePermission.permission_code)
                .join(UserRole, UserRole.role_id == RolePermission.role_id)
                .where(UserRole.hotel_id == self.ctx.hotel_id, UserRole.hotel_user_id == hotel_user_id)
            )
        ).scalars()
        return set(rows)

    async def replace_roles(
        self, hotel_user_id: uuid.UUID, role_ids: list[uuid.UUID], granted_by: uuid.UUID
    ) -> None:
        await self.s.execute(
            delete(UserRole).where(
                UserRole.hotel_id == self.ctx.hotel_id, UserRole.hotel_user_id == hotel_user_id
            )
        )
        await self.s.execute(
            insert(UserRole),
            [
                {
                    "hotel_id": self.ctx.hotel_id,
                    "hotel_user_id": hotel_user_id,
                    "role_id": r,
                    "granted_by": granted_by,
                }
                for r in role_ids
            ],
        )

    async def bump_perms(self, hotel_user_ids: list[uuid.UUID]) -> None:
        if hotel_user_ids:
            await self.s.execute(
                update(HotelUser)
                .where(HotelUser.hotel_id == self.ctx.hotel_id, HotelUser.id.in_(hotel_user_ids))
                .values(perms_version=HotelUser.perms_version + 1)
            )

    async def holders_of_role(self, role_id: uuid.UUID) -> list[uuid.UUID]:
        return list(
            (
                await self.s.execute(
                    select(UserRole.hotel_user_id).where(
                        UserRole.hotel_id == self.ctx.hotel_id, UserRole.role_id == role_id
                    )
                )
            ).scalars()
        )

    async def active_holders_of_system_role(self, code: str) -> list[uuid.UUID]:
        return list(
            (
                await self.s.execute(
                    select(HotelUser.id)
                    .join(UserRole, UserRole.hotel_user_id == HotelUser.id)
                    .join(Role, Role.id == UserRole.role_id)
                    .where(
                        HotelUser.hotel_id == self.ctx.hotel_id,
                        HotelUser.status == "active",
                        Role.hotel_id.is_(None),
                        Role.code == code,
                    )
                )
            ).scalars()
        )

    async def update_member(self, hotel_user_id: uuid.UUID, values: dict[str, Any]) -> None:
        await self.s.execute(
            update(HotelUser)
            .where(HotelUser.hotel_id == self.ctx.hotel_id, HotelUser.id == hotel_user_id)
            .values(**values)
        )

    async def revoke_sessions(self, user_id: uuid.UUID, reason: str) -> int:
        """Sessions of this user that are bound to this hotel (a token serves one hotel, G11)."""
        result = await self.s.execute(
            update(Session)
            .where(
                Session.user_id == user_id,
                Session.active_hotel_id == self.ctx.hotel_id,
                Session.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC), revoked_reason=reason)
            .returning(Session.id)
        )
        return len(result.all())

    # --- roles ---------------------------------------------------------------------------

    async def visible_roles(self, role_ids: list[uuid.UUID]) -> list[Role]:
        """System hotel roles and this hotel's own custom roles, never platform roles."""
        if not role_ids:
            return []
        return list(
            (
                await self.s.execute(
                    select(Role).where(
                        Role.id.in_(role_ids),
                        ((Role.hotel_id.is_(None)) & (~Role.code.startswith(PLATFORM_ROLE_PREFIX)))
                        | (Role.hotel_id == self.ctx.hotel_id),
                    )
                )
            ).scalars()
        )

    async def role_permissions(self, role_ids: list[uuid.UUID]) -> dict[uuid.UUID, set[str]]:
        out: dict[uuid.UUID, set[str]] = defaultdict(set)
        if role_ids:
            for role_id, code in (
                await self.s.execute(
                    select(RolePermission.role_id, RolePermission.permission_code).where(
                        RolePermission.role_id.in_(role_ids)
                    )
                )
            ).all():
                out[role_id].add(code)
        return out

    async def own_role(self, role_id: uuid.UUID, *, for_update: bool = False) -> Role | None:
        q = select(Role).where(Role.id == role_id, Role.hotel_id == self.ctx.hotel_id)
        if for_update:
            q = q.with_for_update()
        return (await self.s.execute(q)).scalar_one_or_none()

    async def role_name_taken(self, name: str, exclude: uuid.UUID | None = None) -> bool:
        q = select(Role.id).where(
            func.lower(Role.name) == name.lower(),
            ((Role.hotel_id.is_(None)) & (~Role.code.startswith(PLATFORM_ROLE_PREFIX)))
            | (Role.hotel_id == self.ctx.hotel_id),
        )
        if exclude is not None:
            q = q.where(Role.id != exclude)
        return (await self.s.execute(q)).first() is not None

    async def create_role(self, code: str, name: str, permissions: list[str]) -> Role:
        role = (
            await self.s.execute(
                insert(Role)
                .values(hotel_id=self.ctx.hotel_id, code=code, name=name, is_system=False)
                .returning(Role)
            )
        ).scalar_one()
        await self.set_role_permissions(role.id, permissions)
        return role

    async def set_role_permissions(self, role_id: uuid.UUID, permissions: list[str]) -> None:
        await self.s.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        await self.s.execute(
            insert(RolePermission),
            [{"role_id": role_id, "permission_code": p} for p in sorted(set(permissions))],
        )

    async def rename_role(self, role_id: uuid.UUID, name: str) -> None:
        await self.s.execute(
            update(Role).where(Role.id == role_id, Role.hotel_id == self.ctx.hotel_id).values(name=name)
        )

    # --- invitations ---------------------------------------------------------------------

    async def pending_invitations(self) -> list[tuple[Invitation, str | None]]:
        rows = (
            await self.s.execute(
                select(Invitation, User.name)
                .outerjoin(User, User.id == Invitation.invited_by)
                .where(
                    Invitation.hotel_id == self.ctx.hotel_id,
                    Invitation.accepted_at.is_(None),
                    Invitation.cancelled_at.is_(None),
                    Invitation.expires_at > func.now(),
                )
                .order_by(Invitation.created_at.desc())
            )
        ).all()
        return [(r[0], r[1]) for r in rows]

    async def pending_invitation_for(self, email: str) -> Invitation | None:
        return (
            await self.s.execute(
                select(Invitation).where(
                    Invitation.hotel_id == self.ctx.hotel_id,
                    Invitation.email == email,
                    Invitation.accepted_at.is_(None),
                    Invitation.cancelled_at.is_(None),
                    Invitation.expires_at > func.now(),
                )
            )
        ).scalar_one_or_none()

    async def create_invitation(self, values: dict[str, Any]) -> Invitation:
        return (
            await self.s.execute(
                insert(Invitation).values(hotel_id=self.ctx.hotel_id, **values).returning(Invitation)
            )
        ).scalar_one()

    async def invitation(self, invitation_id: uuid.UUID) -> Invitation | None:
        return (
            await self.s.execute(
                select(Invitation)
                .where(Invitation.hotel_id == self.ctx.hotel_id, Invitation.id == invitation_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
