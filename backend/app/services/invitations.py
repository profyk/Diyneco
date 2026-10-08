"""Invitation acceptance. The emailed token is the only proof, so the hotel is found through
app.invitation_lookup (no tenant context exists yet), then the work runs under that hotel's
context. Returns no tokens (DECISIONS G12); the new member signs in afterwards.

Creating invitations is Phase 2 (POST /staff/invitations)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert, select, text

from app.audit.writer import write_audit
from app.core import crypto
from app.core.errors import AppError
from app.core.passwords import check_password, check_pin
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.tenancy import HotelUser, Invitation, User, UserRole
from app.services.auth import ClientInfo

INVALID = "This invitation is invalid, used or expired."


async def accept_invitation(
    uow: UnitOfWork, token: str, *, name: str, password: str, pin: str, client: ClientInfo
) -> dict[str, Any]:
    s = uow.session
    found = (
        await s.execute(text("SELECT * FROM app.invitation_lookup(:h)"), {"h": crypto.sha256(token)})
    ).first()
    if found is None:
        raise AppError("NOT_FOUND", INVALID)
    await set_tenant(s, found.hotel_id)
    inv = (
        await s.execute(select(Invitation).where(Invitation.id == found.invitation_id).with_for_update())
    ).scalar_one()
    if inv.accepted_at is not None or inv.cancelled_at is not None:
        raise AppError("NOT_FOUND", INVALID)
    check_pin(pin)

    now = datetime.now(UTC)
    user = (
        await s.execute(select(User).where(User.email == inv.email).with_for_update())
    ).scalar_one_or_none()
    if user is None:
        check_password(password, email=inv.email)
        user = (
            await s.execute(
                insert(User)
                .values(
                    email=inv.email,
                    name=name.strip(),
                    password_hash=crypto.hash_secret(password),
                    email_verified_at=now,
                )
                .returning(User)
            )
        ).scalar_one()
    else:
        # Existing account (member of another hotel): prove it is theirs with the current password.
        if user.status != "active" or not crypto.verify_secret(user.password_hash, password):
            raise AppError("UNAUTHENTICATED", "Sign in with your existing Diyneco password to accept.")
        if user.email_verified_at is None:
            user.email_verified_at = now

    await set_tenant(s, inv.hotel_id, user.id)
    already = (await s.execute(select(HotelUser.id).where(HotelUser.user_id == user.id))).first()
    if already is not None:
        raise AppError("INVALID_TRANSITION", "You are already a member of this hotel.")
    hotel_user_id = (
        await s.execute(
            insert(HotelUser)
            .values(
                hotel_id=inv.hotel_id,
                user_id=user.id,
                department=inv.department,
                pin_hash=crypto.hash_secret(pin),
            )
            .returning(HotelUser.id)
        )
    ).scalar_one()
    if inv.role_ids:
        await s.execute(
            insert(UserRole),
            [
                {
                    "hotel_id": inv.hotel_id,
                    "hotel_user_id": hotel_user_id,
                    "role_id": r,
                    "granted_by": inv.invited_by,
                }
                for r in inv.role_ids
            ],
        )
    inv.accepted_at = now
    ctx = TenantContext(
        hotel_id=inv.hotel_id,
        actor_type="user",
        actor_id=user.id,
        actor_label=user.name,
        ip=client.ip,
        request_id=client.request_id,
    )
    await write_audit(
        s,
        ctx,
        "staff.invitation_accepted",
        "invitation",
        inv.id,
        new_value={"user_id": str(user.id), "role_ids": [str(r) for r in inv.role_ids]},
    )
    return {"status": "accepted", "hotel_id": inv.hotel_id, "user_id": user.id}
