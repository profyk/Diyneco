"""Diyneco staff accounts (DECISIONS D71): Super Admins invite platform staff, change their
roles, and deactivate or reactivate them from the admin panel.

A platform account is never a hotel account: its email must not already be in use. A new
account starts as 'invited' without a password; the invitation link sets the password, and
two-step sign-in is set up at the first sign-in like for every platform account. Roles change
only through app.admin_set_platform_roles (platform roles, platform accounts), and the
database refuses to commit a change that leaves no active Super Admin; the service checks the
same rule first under the same lock to answer with a clear error.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import insert, select, text, update

from app.audit.writer import write_platform_audit
from app.core import crypto
from app.core.errors import AppError
from app.core.passwords import check_password
from app.core.state import AppState
from app.db.session import UnitOfWork
from app.models.tenancy import OneTimeToken, User
from app.services.auth import ClientInfo, _consume_token, create_one_time_token, revoke_all_sessions

INVITE_TTL = timedelta(hours=72)
SUPER_ADMIN = "platform_super_admin"
LOCK_SQL = text("SELECT pg_advisory_xact_lock(hashtext('app.platform_super_admins'))")
ROLES_SQL = text(
    "SELECT r.code, r.name, coalesce(array_agg(rp.permission_code ORDER BY rp.permission_code) "
    "FILTER (WHERE rp.permission_code IS NOT NULL), '{}') AS permissions "
    "FROM app.roles r LEFT JOIN app.role_permissions rp ON rp.role_id = r.id "
    "WHERE r.hotel_id IS NULL AND r.code LIKE 'platform\\_%' GROUP BY r.code, r.name ORDER BY r.name"
)
STAFF_SQL = text(
    "SELECT u.id, u.email, u.name, u.status, u.last_login_at, u.created_at, "
    "coalesce(array_agg(r.code ORDER BY r.code) FILTER (WHERE r.code IS NOT NULL), '{}') AS roles, "
    "EXISTS (SELECT 1 FROM app.mfa_factors f WHERE f.user_id = u.id AND f.confirmed_at IS NOT NULL) "
    "AS mfa_enrolled "
    "FROM app.users u LEFT JOIN app.platform_user_roles pur ON pur.user_id = u.id "
    "LEFT JOIN app.roles r ON r.id = pur.role_id "
    "WHERE u.is_platform AND (CAST(:id AS uuid) IS NULL OR u.id = CAST(:id AS uuid)) "
    "GROUP BY u.id ORDER BY u.name, u.email"
)
OTHER_SUPER_ADMINS_SQL = text(
    "SELECT count(DISTINCT u.id) FROM app.users u "
    "JOIN app.platform_user_roles pur ON pur.user_id = u.id JOIN app.roles r ON r.id = pur.role_id "
    "WHERE u.is_platform AND u.status = 'active' AND r.hotel_id IS NULL "
    "AND r.code = 'platform_super_admin' AND u.id <> :u"
)


async def roles(uow: UnitOfWork) -> list[dict[str, Any]]:
    rows = (await uow.session.execute(ROLES_SQL)).mappings().all()
    return [{"code": r["code"], "name": r["name"], "permissions": list(r["permissions"])} for r in rows]


async def staff(uow: UnitOfWork, user_id: uuid.UUID | None = None) -> list[dict[str, Any]]:
    rows = (await uow.session.execute(STAFF_SQL, {"id": user_id})).mappings().all()
    return [{**r, "roles": list(r["roles"])} for r in rows]


async def _one(uow: UnitOfWork, user_id: uuid.UUID) -> dict[str, Any]:
    await uow.session.flush()  # the read below is plain SQL
    found = await staff(uow, user_id)
    if not found:
        raise AppError("NOT_FOUND")
    return found[0]


async def _locked_account(uow: UnitOfWork, user_id: uuid.UUID) -> User:
    user = (
        await uow.session.execute(
            select(User).where(User.id == user_id, User.is_platform.is_(True)).with_for_update()
        )
    ).scalar_one_or_none()
    if user is None:
        raise AppError("NOT_FOUND")
    return user


def _not_self(actor: dict[str, Any], user_id: uuid.UUID, what: str) -> None:
    if actor["actor_id"] == user_id:
        raise AppError("PERMISSION_DENIED", f"Another Super Admin must {what} your own account.")


async def _keeps_a_super_admin(uow: UnitOfWork, user_id: uuid.UUID) -> None:
    """Refuses a change that would remove the last active Super Admin (the database checks
    again at commit; this answers with a clear error)."""
    await uow.session.execute(LOCK_SQL)
    left = (await uow.session.execute(OTHER_SUPER_ADMINS_SQL, {"u": user_id})).scalar_one()
    if left == 0:
        raise AppError("INVALID_TRANSITION", "The platform must keep at least one active Super Admin.")


async def _set_roles(uow: UnitOfWork, user_id: uuid.UUID, codes: list[str]) -> None:
    known = {r["code"] for r in await roles(uow)}
    unknown = sorted(set(codes) - known)
    if unknown:
        raise AppError(
            "VALIDATION_FAILED",
            details={
                "fields": [
                    {
                        "field": "roles",
                        "problem": f"Unknown role: {', '.join(unknown)}.",
                        "type": "value_error",
                    }
                ]
            },
        )
    await uow.session.execute(
        text("SELECT app.admin_set_platform_roles(:u, CAST(:r AS text[]))"),
        {"u": user_id, "r": sorted(set(codes))},
    )


async def _send_invite(st: AppState, uow: UnitOfWork, user: User, inviter: str) -> None:
    # A new link replaces every earlier one.
    await uow.session.execute(
        update(OneTimeToken)
        .where(
            OneTimeToken.user_id == user.id,
            OneTimeToken.purpose == "platform_invite",
            OneTimeToken.used_at.is_(None),
        )
        .values(used_at=datetime.now(UTC))
    )
    token = await create_one_time_token(uow.session, user.id, "platform_invite", INVITE_TTL)
    await st.mailer.queue(
        uow,
        hotel_id=None,
        template="platform_invitation",
        to=user.email,
        subject="You have been invited to the Diyneco admin panel",
        body=f"{inviter} invited you to the Diyneco admin panel.\n\n"
        + st.settings.admin_link("/accept-invite", token)
        + f" this code within 72 hours to choose your password:\n\n{token}\n\n"
        "You will set up two-step sign-in the first time you sign in.",
    )


async def invite(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], *, email: str, name: str, role_codes: list[str]
) -> dict[str, Any]:
    s = uow.session
    email = email.strip()
    if (await s.execute(select(User.id).where(User.email == email))).first() is not None:
        raise AppError(
            "INVALID_TRANSITION",
            "This email already has a Diyneco account. Platform staff need an address of their own.",
        )
    user = (
        await s.execute(
            insert(User)
            .values(email=email, name=name.strip(), is_platform=True, status="invited")
            .returning(User.id)
        )
    ).scalar_one()
    account = await _locked_account(uow, user)
    await _set_roles(uow, account.id, role_codes)
    await _send_invite(st, uow, account, actor["actor_label"])
    await write_platform_audit(
        s,
        **actor,
        action="platform.staff_invited",
        entity_type="user",
        entity_id=account.id,
        new_value={"email": email, "roles": sorted(set(role_codes))},
    )
    return await _one(uow, account.id)


async def resend_invite(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], user_id: uuid.UUID
) -> dict[str, Any]:
    account = await _locked_account(uow, user_id)
    if account.status != "invited":
        raise AppError(
            "INVALID_TRANSITION", "Only an invitation that has not been accepted can be sent again."
        )
    await _send_invite(st, uow, account, actor["actor_label"])
    await write_platform_audit(
        uow.session, **actor, action="platform.staff_invite_resent", entity_type="user", entity_id=user_id
    )
    return await _one(uow, user_id)


async def change_roles(
    uow: UnitOfWork, actor: dict[str, Any], user_id: uuid.UUID, role_codes: list[str]
) -> dict[str, Any]:
    _not_self(actor, user_id, "change the roles of")
    before = await _one(uow, user_id)
    await _locked_account(uow, user_id)
    if SUPER_ADMIN in before["roles"] and SUPER_ADMIN not in role_codes:
        await _keeps_a_super_admin(uow, user_id)
    await _set_roles(uow, user_id, role_codes)
    after = await _one(uow, user_id)
    await write_platform_audit(
        uow.session,
        **actor,
        action="platform.staff_roles_changed",
        entity_type="user",
        entity_id=user_id,
        new_value={"from": before["roles"], "to": after["roles"]},
    )
    return after


async def deactivate(uow: UnitOfWork, actor: dict[str, Any], user_id: uuid.UUID) -> dict[str, Any]:
    _not_self(actor, user_id, "deactivate")
    account = await _locked_account(uow, user_id)
    if account.status == "deactivated":
        raise AppError("INVALID_TRANSITION", "This account is already deactivated.")
    if account.status == "active":
        await _keeps_a_super_admin(uow, user_id)
    before = account.status
    account.status = "deactivated"
    await revoke_all_sessions(uow.session, user_id, "deactivated")
    await uow.session.execute(
        update(OneTimeToken)
        .where(OneTimeToken.user_id == user_id, OneTimeToken.used_at.is_(None))
        .values(used_at=datetime.now(UTC))
    )
    await write_platform_audit(
        uow.session,
        **actor,
        action="platform.staff_deactivated",
        entity_type="user",
        entity_id=user_id,
        new_value={"from": before, "to": "deactivated"},
    )
    return await _one(uow, user_id)


async def reactivate(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], user_id: uuid.UUID
) -> dict[str, Any]:
    account = await _locked_account(uow, user_id)
    if account.status != "deactivated":
        raise AppError("INVALID_TRANSITION", "Only a deactivated account can be reactivated.")
    # An account that never chose a password goes back to the invitation step.
    account.status = "active" if account.password_hash else "invited"
    if account.status == "invited":
        await _send_invite(st, uow, account, actor["actor_label"])
    await write_platform_audit(
        uow.session,
        **actor,
        action="platform.staff_reactivated",
        entity_type="user",
        entity_id=user_id,
        new_value={"from": "deactivated", "to": account.status},
    )
    return await _one(uow, user_id)


async def accept_invite(uow: UnitOfWork, token: str, password: str, client: ClientInfo) -> None:
    """Sets the password of an invited platform account; it signs in normally afterwards."""
    s = uow.session
    row = await _consume_token(s, token, "platform_invite")
    user = (await s.execute(select(User).where(User.id == row.user_id).with_for_update())).scalar_one()
    if not user.is_platform or user.status != "invited":
        raise AppError(
            "VALIDATION_FAILED",
            "This link is invalid or has expired.",
            details={"fields": [{"field": "token", "problem": "Invalid or expired.", "type": "token"}]},
        )
    check_password(password, email=user.email)
    user.password_hash = crypto.hash_secret(password)
    user.status = "active"
    user.email_verified_at = datetime.now(UTC)
    await write_platform_audit(
        s,
        actor_type="user",
        actor_id=user.id,
        actor_label=user.name,
        action="platform.staff_invite_accepted",
        entity_type="user",
        entity_id=user.id,
        ip=client.ip,
        request_id=client.request_id,
    )
