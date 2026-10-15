"""Staff codes (DECISIONS D82): sign-in to the room-service app with the hotel's Hotel ID, the
member's own 8-digit staff code and their PIN.

- A manager with `staff.manage` issues the code; it is shown once and stored as SHA-256 with
  the hotel id and the server pepper, unique within the hotel. Issuing again replaces it.
- Roles that must use two-step sign-in (owner, admin, general manager, finance manager) and
  anyone who turned it on sign in with email, password and their authenticator instead.
- A wrong Hotel ID or code counts per IP (10 in 15 minutes, then refused); a wrong PIN counts
  against the member's PIN lockout (5 in 15 minutes).
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.audit.writer import write_audit
from app.core import crypto
from app.core.errors import AppError
from app.core.logging import security_event
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.tenancy import Hotel, HotelUser, MfaFactor, User
from app.repositories.staff import StaffRepository
from app.services import auth
from app.services.staff import _target

CODE_FAIL_LIMIT = 10
WRONG = "The Hotel ID, staff code or PIN is not correct."
USE_EMAIL = "Your account signs in with email, password and two-step sign-in."


def code_hash(st: AppState, hotel_id: uuid.UUID, code: str) -> bytes:
    return crypto.sha256(f"staff:{hotel_id}:{code}:{st.settings.pairing_code_pepper}")


async def _must_use_mfa(repo: StaffRepository, hu: HotelUser) -> bool:
    roles = (await repo.roles_by_member([hu.id])).get(hu.id, [])
    if auth.MFA_REQUIRED_ROLES.intersection(r.code for r in roles if r.hotel_id is None):
        return True
    factor = (
        await repo.s.execute(
            select(MfaFactor.id).where(MfaFactor.user_id == hu.user_id, MfaFactor.confirmed_at.is_not(None))
        )
    ).first()
    return factor is not None


async def issue(
    st: AppState, uow: UnitOfWork, ctx: TenantContext, user_id: uuid.UUID, caller_permissions: frozenset[str]
) -> dict[str, Any]:
    repo = StaffRepository(uow.session, ctx)
    hu, _ = await _target(repo, ctx, user_id, caller_permissions)
    if hu.status != "active":
        raise AppError("INVALID_TRANSITION", "This person no longer has access.")
    if await _must_use_mfa(repo, hu):
        raise AppError(
            "INVALID_TRANSITION", "This person signs in with email and two-step sign-in, not a staff code."
        )
    for _ in range(5):
        code = f"{secrets.randbelow(100_000_000):08d}"
        taken = (
            await uow.session.execute(
                select(HotelUser.id).where(
                    HotelUser.hotel_id == ctx.hotel_id,
                    HotelUser.staff_code_hash == code_hash(st, ctx.hotel_id, code),
                )
            )
        ).first()
        if taken is None:
            break
    else:  # pragma: no cover - a hundred million codes per hotel
        raise AppError("SERVICE_UNAVAILABLE")
    replaced = hu.staff_code_hash is not None
    await repo.update_member(
        hu.id, {"staff_code_hash": code_hash(st, ctx.hotel_id, code), "staff_code_set_at": datetime.now(UTC)}
    )
    await write_audit(
        uow.session, ctx, "staff.code_issued", "hotel_user", hu.id, new_value={"replaced": replaced}
    )
    hotel_code = (await uow.session.execute(select(Hotel.code).where(Hotel.id == ctx.hotel_id))).scalar_one()
    return {"staff_code": code, "hotel_code": hotel_code}


async def revoke(
    uow: UnitOfWork, ctx: TenantContext, user_id: uuid.UUID, caller_permissions: frozenset[str]
) -> None:
    repo = StaffRepository(uow.session, ctx)
    hu, _ = await _target(repo, ctx, user_id, caller_permissions)
    if hu.staff_code_hash is None:
        raise AppError("INVALID_TRANSITION", "This person has no staff code.")
    await repo.update_member(hu.id, {"staff_code_hash": None, "staff_code_set_at": None})
    await write_audit(uow.session, ctx, "staff.code_removed", "hotel_user", hu.id)


async def sign_in(
    st: AppState, uow: UnitOfWork, hotel_code: str, staff_code: str, pin: str, client: auth.ClientInfo
) -> auth.LoginResult:
    ip_key = client.ip or "unknown"
    if await st.limiter.peek("staff_code_fail", ip_key) >= CODE_FAIL_LIMIT:
        security_event("auth.staff_code_locked", ip=client.ip)
        raise AppError("RATE_LIMITED", "Too many wrong codes. Try again in 15 minutes.")

    async def wrong(reason: str) -> AppError:
        await st.limiter.hit("staff_code_fail", ip_key)
        security_event("auth.staff_code_failed", reason=reason, ip=client.ip)
        return AppError("UNAUTHENTICATED", WRONG)

    s = uow.session
    hotel = await auth.hotel_by_code(s, hotel_code)
    if hotel is None:
        raise await wrong("unknown_hotel")
    await set_tenant(s, hotel.id)
    hu = (
        await s.execute(
            select(HotelUser).where(
                HotelUser.hotel_id == hotel.id,
                HotelUser.staff_code_hash == code_hash(st, hotel.id, staff_code),
                HotelUser.status == "active",
            )
        )
    ).scalar_one_or_none()
    if hu is None:
        raise await wrong("bad_code")
    user = (await s.execute(select(User).where(User.id == hu.user_id))).scalar_one()
    now = datetime.now(UTC)
    if user.status != "active" or user.is_platform or (user.locked_until and user.locked_until > now):
        security_event(
            "auth.staff_code_failed", reason=f"user_{user.status}", user_id=str(user.id), ip=client.ip
        )
        raise AppError("UNAUTHENTICATED", WRONG)
    await auth.check_member_pin(st, hotel.id, hu, pin)
    ctx = TenantContext(hotel_id=hotel.id, actor_type="user", actor_id=user.id, actor_label=user.name)
    if await _must_use_mfa(StaffRepository(s, ctx), hu):
        raise AppError("UNAUTHENTICATED", USE_EMAIL, details={"reason": "use_email"})
    ms = await auth.memberships(s, user.id)
    membership = next((m for m in ms if m.hotel_id == hotel.id), None)
    if membership is None:
        raise AppError("UNAUTHENTICATED", WRONG)
    user.last_login_at = now
    tokens = await auth.issue_session(st, s, user, membership, ["code", "pin"], client)
    return auth.LoginResult(user=user, hotels=ms, tokens=tokens)
