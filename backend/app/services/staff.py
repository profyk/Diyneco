"""Staff members, invitations and custom roles.

Rules (security spec, Permission catalogue): authorisation checks permissions, never role
names; nobody grants a permission they do not hold; system roles are copied, never edited.
Added here (DECISIONS D20-D22): you cannot change the roles of, deactivate or reset the PIN
of someone who holds a permission you lack; you cannot do those things to yourself; a hotel
always keeps at least one active Hotel Owner.
"""

from __future__ import annotations

import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, text

from app.audit.writer import write_audit
from app.core import crypto
from app.core.errors import AppError
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork
from app.models.tenancy import Hotel, Permission, Role
from app.repositories.staff import StaffRepository
from app.services.plans import ensure_capacity

INVITATION_TTL = timedelta(days=7)
OWNER_ROLE = "hotel_owner"


def _role_ref(r: Role) -> dict[str, Any]:
    return {"id": r.id, "code": r.code, "name": r.name}


def _field_error(field: str, problem: str) -> AppError:
    return AppError(
        "VALIDATION_FAILED",
        problem,
        details={"fields": [{"field": field, "problem": problem, "type": "value_error"}]},
    )


# --- Members -------------------------------------------------------------------------------


async def list_staff(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    repo = StaffRepository(uow.session, ctx)
    members = await repo.members()
    roles = await repo.roles_by_member([hu.id for hu, _, _ in members])
    return [
        {
            "user_id": u.id,
            "name": u.name,
            "email": u.email,
            "department": hu.department,
            "status": hu.status,
            "roles": [_role_ref(r) for r in roles.get(hu.id, [])],
            "has_pin": hu.pin_hash is not None,
            "mfa_enabled": mfa,
            "last_sign_in_at": u.last_login_at,
            "joined_at": hu.created_at,
        }
        for hu, u, mfa in members
    ]


async def _target(
    repo: StaffRepository, ctx: TenantContext, user_id: uuid.UUID, caller_permissions: frozenset[str]
) -> Any:
    found = await repo.member(user_id, for_update=True)
    if found is None:
        raise AppError("NOT_FOUND")
    hu, user = found
    if user_id == ctx.actor_id:
        raise AppError("PERMISSION_DENIED", "You cannot change your own access.")
    if not (await repo.member_permissions(hu.id)) <= caller_permissions:
        raise AppError("PERMISSION_DENIED", "This person has access you do not have.")
    return hu, user


async def _keeps_an_owner(repo: StaffRepository, removing_hotel_user: uuid.UUID) -> None:
    owners = await repo.active_holders_of_system_role(OWNER_ROLE)
    if owners and set(owners) <= {removing_hotel_user}:
        raise AppError("INVALID_TRANSITION", "A hotel must keep at least one active Hotel Owner.")


async def patch_member(
    uow: UnitOfWork, ctx: TenantContext, user_id: uuid.UUID, changes: dict[str, Any]
) -> dict[str, Any]:
    repo = StaffRepository(uow.session, ctx)
    found = await repo.member(user_id, for_update=True)
    if found is None:
        raise AppError("NOT_FOUND")
    hu, user = found
    old: dict[str, Any] = {}
    new: dict[str, Any] = {}
    if "department" in changes and changes["department"] != hu.department:
        old["department"], new["department"] = hu.department, changes["department"]
        await repo.update_member(hu.id, {"department": changes["department"]})
    if changes.get("name") and changes["name"] != user.name:
        others = (
            await uow.session.execute(text("SELECT count(*) FROM app.user_memberships(:u)"), {"u": user_id})
        ).scalar_one()
        if int(others) > 1:
            raise _field_error(
                "name", "This person works at several hotels, so only they can change their name."
            )
        old["name"], new["name"] = user.name, changes["name"]
        user.name = changes["name"]
    if new:
        await write_audit(uow.session, ctx, "staff.update", "hotel_user", hu.id, old_value=old, new_value=new)
    return next(m for m in await list_staff(uow, ctx) if m["user_id"] == user_id)


async def _checked_roles(
    repo: StaffRepository, role_ids: list[uuid.UUID], caller_permissions: frozenset[str]
) -> list[Role]:
    role_ids = list(dict.fromkeys(role_ids))
    roles = await repo.visible_roles(role_ids)
    if len(roles) != len(role_ids):
        raise AppError("NOT_FOUND", "One of the roles does not exist.")
    granted: set[str] = set()
    for perms in (await repo.role_permissions(role_ids)).values():
        granted |= perms
    lacking = sorted(granted - caller_permissions)
    if lacking:
        raise AppError(
            "PERMISSION_DENIED",
            "You cannot give access you do not have yourself.",
            details={"permissions": lacking},
        )
    return roles


async def set_roles(
    uow: UnitOfWork,
    ctx: TenantContext,
    user_id: uuid.UUID,
    role_ids: list[uuid.UUID],
    caller_permissions: frozenset[str],
) -> dict[str, Any]:
    repo = StaffRepository(uow.session, ctx)
    hu, _ = await _target(repo, ctx, user_id, caller_permissions)
    roles = await _checked_roles(repo, role_ids, caller_permissions)
    before = (await repo.roles_by_member([hu.id])).get(hu.id, [])
    if OWNER_ROLE in {r.code for r in before if r.hotel_id is None} and OWNER_ROLE not in {
        r.code for r in roles if r.hotel_id is None
    }:
        await _keeps_an_owner(repo, hu.id)
    if ctx.actor_id is None:
        raise AppError("UNAUTHENTICATED")
    await repo.replace_roles(hu.id, [r.id for r in roles], ctx.actor_id)
    await repo.bump_perms([hu.id])
    await write_audit(
        uow.session,
        ctx,
        "staff.roles",
        "hotel_user",
        hu.id,
        old_value={"roles": sorted(r.code for r in before)},
        new_value={"roles": sorted(r.code for r in roles)},
    )
    return next(m for m in await list_staff(uow, ctx) if m["user_id"] == user_id)


async def deactivate(
    uow: UnitOfWork, ctx: TenantContext, user_id: uuid.UUID, caller_permissions: frozenset[str]
) -> dict[str, Any]:
    repo = StaffRepository(uow.session, ctx)
    hu, _ = await _target(repo, ctx, user_id, caller_permissions)
    if hu.status == "deactivated":
        raise AppError("INVALID_TRANSITION", "This person is already deactivated.")
    await _keeps_an_owner(repo, hu.id)
    await repo.update_member(
        hu.id,
        {"status": "deactivated", "deactivated_at": datetime.now(UTC), "perms_version": hu.perms_version + 1},
    )
    revoked = await repo.revoke_sessions(user_id, "deactivated")
    await write_audit(
        uow.session,
        ctx,
        "staff.deactivate",
        "hotel_user",
        hu.id,
        old_value={"status": "active"},
        new_value={"status": "deactivated", "sessions_revoked": revoked},
    )
    return next(m for m in await list_staff(uow, ctx) if m["user_id"] == user_id)


async def reset_pin(
    uow: UnitOfWork, ctx: TenantContext, user_id: uuid.UUID, caller_permissions: frozenset[str]
) -> None:
    repo = StaffRepository(uow.session, ctx)
    hu, _ = await _target(repo, ctx, user_id, caller_permissions)
    await repo.update_member(hu.id, {"pin_hash": None, "pin_failed": 0, "pin_locked_until": None})
    await write_audit(uow.session, ctx, "staff.pin_reset", "hotel_user", hu.id)


# --- Invitations ---------------------------------------------------------------------------


def _invitation_payload(inv: Any, roles: dict[uuid.UUID, Role], invited_by: str | None) -> dict[str, Any]:
    return {
        "id": inv.id,
        "name": inv.name,
        "email": inv.email,
        "department": inv.department,
        "roles": [_role_ref(roles[r]) for r in inv.role_ids if r in roles],
        "invited_by": invited_by,
        "expires_at": inv.expires_at,
        "created_at": inv.created_at,
    }


async def list_invitations(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    repo = StaffRepository(uow.session, ctx)
    rows = await repo.pending_invitations()
    role_ids = list({r for inv, _ in rows for r in inv.role_ids})
    roles = {r.id: r for r in await repo.visible_roles(role_ids)}
    return [_invitation_payload(inv, roles, by) for inv, by in rows]


async def invite(
    st: AppState,
    uow: UnitOfWork,
    ctx: TenantContext,
    body: dict[str, Any],
    caller_permissions: frozenset[str],
) -> dict[str, Any]:
    repo = StaffRepository(uow.session, ctx)
    email = str(body["email"]).strip().lower()
    roles = await _checked_roles(repo, body["role_ids"], caller_permissions)
    existing = await repo.member_by_email(email)
    if existing is not None:
        raise _field_error("email", "This person is already a member of this hotel.")
    if await repo.pending_invitation_for(email) is not None:
        raise _field_error("email", "This person already has a pending invitation.")
    await ensure_capacity(uow, ctx, "staff")
    if ctx.actor_id is None:
        raise AppError("UNAUTHENTICATED")
    token = crypto.random_token("inv_")
    inv = await repo.create_invitation(
        {
            "email": email,
            "name": body["name"],
            "department": body.get("department"),
            "role_ids": [r.id for r in roles],
            "token_hash": crypto.sha256(token),
            "invited_by": ctx.actor_id,
            "expires_at": datetime.now(UTC) + INVITATION_TTL,
        }
    )
    hotel_name = (await uow.session.execute(select(Hotel.name).where(Hotel.id == ctx.hotel_id))).scalar_one()
    await st.mailer.queue(
        uow,
        hotel_id=ctx.hotel_id,
        template="staff_invitation",
        to=email,
        subject=f"You are invited to join {hotel_name} on Diyneco",
        body=(
            f"{ctx.actor_label} invited you to join {hotel_name} on Diyneco as "
            f"{', '.join(r.name for r in roles)}.\n\n"
            f"Use this invitation code within 7 days to set up your account:\n\n{token}\n\n"
            "If you were not expecting this, ignore this email."
        ),
        subject_ref={"invitation_id": str(inv.id)},
    )
    await write_audit(
        uow.session,
        ctx,
        "staff.invite",
        "invitation",
        inv.id,
        new_value={
            "email": email,
            "roles": sorted(r.code for r in roles),
            "department": body.get("department"),
        },
    )
    return _invitation_payload(inv, {r.id: r for r in roles}, ctx.actor_label)


async def cancel_invitation(uow: UnitOfWork, ctx: TenantContext, invitation_id: uuid.UUID) -> None:
    repo = StaffRepository(uow.session, ctx)
    inv = await repo.invitation(invitation_id)
    if inv is None:
        raise AppError("NOT_FOUND")
    if inv.accepted_at is not None or inv.cancelled_at is not None:
        raise AppError("INVALID_TRANSITION", "This invitation was already accepted or cancelled.")
    inv.cancelled_at = datetime.now(UTC)
    await write_audit(
        uow.session, ctx, "staff.invitation_cancelled", "invitation", inv.id, old_value={"email": inv.email}
    )


# --- Custom roles --------------------------------------------------------------------------


def _role_code(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:40] or "role"
    return f"custom_{slug}_{secrets.token_hex(3)}"


async def _checked_permissions(
    uow: UnitOfWork, permissions: list[str], caller_permissions: frozenset[str]
) -> list[str]:
    wanted = sorted(set(permissions))
    known = set(
        (
            await uow.session.execute(
                select(Permission.code).where(Permission.code.in_(wanted), Permission.scope == "hotel")
            )
        ).scalars()
    )
    unknown = [p for p in wanted if p not in known]
    if unknown:
        raise _field_error("permissions", f"Unknown permissions: {', '.join(unknown)}")
    lacking = [p for p in wanted if p not in caller_permissions]
    if lacking:
        raise AppError(
            "PERMISSION_DENIED",
            "You cannot give access you do not have yourself.",
            details={"permissions": lacking},
        )
    return wanted


async def create_role(
    uow: UnitOfWork, ctx: TenantContext, body: dict[str, Any], caller_permissions: frozenset[str]
) -> dict[str, Any]:
    repo = StaffRepository(uow.session, ctx)
    permissions = await _checked_permissions(uow, body["permissions"], caller_permissions)
    if await repo.role_name_taken(body["name"]):
        raise _field_error("name", "A role with this name already exists.")
    role = await repo.create_role(_role_code(body["name"]), body["name"], permissions)
    await write_audit(
        uow.session,
        ctx,
        "role.create",
        "role",
        role.id,
        new_value={"name": role.name, "permissions": permissions},
    )
    return {
        "id": role.id,
        "code": role.code,
        "name": role.name,
        "is_system": False,
        "permissions": permissions,
    }


async def patch_role(
    uow: UnitOfWork,
    ctx: TenantContext,
    role_id: uuid.UUID,
    changes: dict[str, Any],
    caller_permissions: frozenset[str],
) -> dict[str, Any]:
    repo = StaffRepository(uow.session, ctx)
    visible = await repo.visible_roles([role_id])
    if not visible:
        raise AppError("NOT_FOUND")
    if visible[0].is_system:
        raise AppError("INVALID_TRANSITION", "System roles cannot be edited. Create a custom role instead.")
    role = await repo.own_role(role_id, for_update=True)
    if role is None:
        raise AppError("NOT_FOUND")
    current = sorted((await repo.role_permissions([role_id])).get(role_id, set()))
    if not set(current) <= caller_permissions:
        raise AppError("PERMISSION_DENIED", "This role has access you do not have.")
    old: dict[str, Any] = {}
    new: dict[str, Any] = {}
    if changes.get("name") and changes["name"] != role.name:
        if await repo.role_name_taken(changes["name"], exclude=role_id):
            raise _field_error("name", "A role with this name already exists.")
        await repo.rename_role(role_id, changes["name"])
        old["name"], new["name"] = role.name, changes["name"]
    permissions = current
    if changes.get("permissions") is not None:
        permissions = await _checked_permissions(uow, changes["permissions"], caller_permissions)
        if permissions != current:
            await repo.set_role_permissions(role_id, permissions)
            await repo.bump_perms(await repo.holders_of_role(role_id))
            old["permissions"], new["permissions"] = current, permissions
    if new:
        await write_audit(uow.session, ctx, "role.update", "role", role_id, old_value=old, new_value=new)
    return {
        "id": role.id,
        "code": role.code,
        "name": new.get("name", role.name),
        "is_system": False,
        "permissions": permissions,
    }
