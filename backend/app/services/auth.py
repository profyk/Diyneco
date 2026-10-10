"""Authentication and sessions (API spec "Authentication and sessions"; security spec
"Authentication design").

Sessions are rows in app.sessions. Every refresh creates a new row in the same family and
marks the previous one revoked with reason 'rotated'; presenting a rotated token again is
reuse, which revokes the whole family. Failure counters are written in their own committed
transaction, because the request that reports the failure rolls back.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.writer import write_audit, write_platform_audit
from app.core import crypto
from app.core.errors import AppError
from app.core.jwt import ACCESS_TTL_S, MFA_PENDING_TTL_S, STEP_UP_TTL_S
from app.core.logging import security_event
from app.core.passwords import check_password, check_pin
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.tenancy import (
    Hotel,
    HotelUser,
    MfaFactor,
    MfaRecoveryCode,
    OneTimeToken,
    Session,
    User,
)
from app.services import mfa

LOCKOUT_THRESHOLD = 5
LOCKOUT_WINDOW = timedelta(minutes=15)
LOCKOUT_DURATION = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=30)
WEB_IDLE = timedelta(hours=12)
MAX_ACTIVE_SESSIONS = 10
RESET_TOKEN_TTL = timedelta(minutes=30)
VERIFY_TOKEN_TTL = timedelta(hours=24)

# Hotel roles that must use MFA (security spec, MFA policy). Platform accounts always must.
MFA_REQUIRED_ROLES = frozenset({"hotel_owner", "hotel_admin", "general_manager", "finance_manager"})

INVALID_LOGIN = "Email or password is incorrect, or the account is temporarily locked."


@dataclass(frozen=True)
class ClientInfo:
    ip: str | None
    user_agent: str | None
    request_id: str | None
    web: bool  # request came from an allow-listed web origin (refresh cookie, idle limit)


@dataclass(frozen=True)
class Membership:
    hotel_id: uuid.UUID
    hotel_name: str
    hotel_status: str
    hotel_user_id: uuid.UUID
    perms_version: int
    role_codes: tuple[str, ...]


@dataclass(frozen=True)
class IssuedTokens:
    access_token: str
    expires_in: int
    refresh_token: str
    session_id: uuid.UUID
    mfa_pending: bool


def _now() -> datetime:
    return datetime.now(UTC)


async def memberships(session: AsyncSession, user_id: uuid.UUID) -> list[Membership]:
    rows = (await session.execute(text("SELECT * FROM app.user_memberships(:u)"), {"u": user_id})).all()
    return [
        Membership(
            r.hotel_id,
            r.hotel_name,
            r.hotel_status,
            r.hotel_user_id,
            r.perms_version,
            tuple(r.role_codes or ()),
        )
        for r in rows
    ]


def hotels_payload(ms: list[Membership]) -> list[dict[str, Any]]:
    return [
        {"id": m.hotel_id, "name": m.hotel_name, "status": m.hotel_status, "roles": list(m.role_codes)}
        for m in ms
    ]


def user_payload(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "email_verified": user.email_verified_at is not None,
    }


def mfa_required_for(user: User, membership: Membership | None) -> bool:
    if user.is_platform:
        return True
    return bool(membership and MFA_REQUIRED_ROLES.intersection(membership.role_codes))


# --- Failure bookkeeping (own transaction) -------------------------------------------------


async def _record_login_failure(st: AppState, user_id: uuid.UUID, client: ClientInfo, reason: str) -> None:
    async with st.db.sessionmaker() as s, s.begin():
        uow = UnitOfWork(s, st.db.sessionmaker)
        user = (await s.execute(select(User).where(User.id == user_id).with_for_update())).scalar_one()
        now = _now()
        if user.failed_window_start is None or user.failed_window_start < now - LOCKOUT_WINDOW:
            user.failed_window_start, user.failed_logins = now, 1
        else:
            user.failed_logins += 1
        locked_now = False
        if user.failed_logins >= LOCKOUT_THRESHOLD and not (user.locked_until and user.locked_until > now):
            user.locked_until = now + LOCKOUT_DURATION
            locked_now = True
        await write_platform_audit(
            s,
            actor_type="user",
            actor_id=user.id,
            actor_label=user.name,
            action="auth.login_failed",
            entity_type="user",
            entity_id=user.id,
            ip=client.ip,
            request_id=client.request_id,
            new_value={"reason": reason, "failed_logins": user.failed_logins, "locked": locked_now},
        )
        if locked_now:
            await st.mailer.queue(
                uow,
                hotel_id=None,
                template="account_locked",
                to=user.email,
                subject="Your Diyneco account was locked",
                body=(
                    "We locked your account for 15 minutes after 5 failed sign-in attempts. "
                    "If this was not you, reset your password."
                ),
            )
    if locked_now:
        security_event("auth.account_locked", user_id=str(user_id), ip=client.ip)
        await uow.run_after_commit()


async def _reset_login_failures(session: AsyncSession, user: User) -> None:
    user.failed_logins = 0
    user.failed_window_start = None
    user.locked_until = None


# --- Session issuing ------------------------------------------------------------------------


async def issue_session(
    st: AppState,
    session: AsyncSession,
    user: User,
    membership: Membership | None,
    amr: list[str],
    client: ClientInfo,
    *,
    family_id: uuid.UUID | None = None,
    mfa_pending: bool = False,
) -> IssuedTokens:
    now = _now()
    if family_id is None:
        family_id = uuid.uuid4()
        active_families = (
            await session.execute(
                select(Session.family_id, func.min(Session.created_at).label("started"))
                .where(Session.user_id == user.id, Session.revoked_at.is_(None), Session.expires_at > now)
                .group_by(Session.family_id)
                .order_by(text("started"))
            )
        ).all()
        excess = len(active_families) - (MAX_ACTIVE_SESSIONS - 1)
        if excess > 0:
            oldest = [f.family_id for f in active_families[:excess]]
            await session.execute(
                update(Session)
                .where(Session.family_id.in_(oldest), Session.revoked_at.is_(None))
                .values(revoked_at=now, revoked_reason="session_limit")
            )
    refresh = crypto.random_token("rt_")
    session_id = (
        await session.execute(
            insert(Session)
            .values(
                user_id=user.id,
                family_id=family_id,
                active_hotel_id=membership.hotel_id if membership else None,
                refresh_hash=crypto.sha256(refresh),
                user_agent=(client.user_agent or "")[:300] or None,
                ip=client.ip,
                amr=amr,
                expires_at=now + REFRESH_TTL,
            )
            .returning(Session.id)
        )
    ).scalar_one()
    claims: dict[str, Any] = {
        "sub": str(user.id),
        "kind": "platform" if user.is_platform else "staff",
        "sid": str(session_id),
        "amr": amr,
    }
    if membership is not None:
        claims["hid"] = str(membership.hotel_id)
        claims["perms_v"] = membership.perms_version
    if mfa_pending:
        claims["mfa_pending"] = True
    access, _ = st.jwt.sign("access", claims, ACCESS_TTL_S)
    return IssuedTokens(access, ACCESS_TTL_S, refresh, session_id, mfa_pending)


def _pick_membership(ms: list[Membership], hotel_id: uuid.UUID | None) -> Membership:
    if hotel_id is not None:
        for m in ms:
            if m.hotel_id == hotel_id:
                return m
        raise AppError("NOT_FOUND")
    if not ms:
        raise AppError("UNAUTHENTICATED", "Your account has no active hotel access.")
    return ms[0]


# --- Login and MFA --------------------------------------------------------------------------


@dataclass(frozen=True)
class LoginResult:
    user: User
    hotels: list[Membership]
    tokens: IssuedTokens | None = None
    mfa_token: str | None = None


async def login(
    st: AppState, uow: UnitOfWork, email: str, password: str, hotel_id: uuid.UUID | None, client: ClientInfo
) -> LoginResult:
    s = uow.session
    user = (await s.execute(select(User).where(User.email == email.strip()))).scalar_one_or_none()
    ok = crypto.verify_secret(user.password_hash if user else None, password)
    if user is None:
        security_event("auth.login_failed", reason="unknown_email", ip=client.ip)
        raise AppError("UNAUTHENTICATED", INVALID_LOGIN)
    now = _now()
    if user.locked_until and user.locked_until > now:
        security_event("auth.login_failed", reason="locked", user_id=str(user.id), ip=client.ip)
        raise AppError("UNAUTHENTICATED", INVALID_LOGIN)
    if not ok or user.status != "active":
        reason = "bad_password" if not ok else f"status_{user.status}"
        security_event("auth.login_failed", reason=reason, user_id=str(user.id), ip=client.ip)
        if not ok:
            await _record_login_failure(st, user.id, client, reason)
        raise AppError("UNAUTHENTICATED", INVALID_LOGIN)

    if user.password_hash and crypto.needs_rehash(user.password_hash):
        user.password_hash = crypto.hash_secret(password)
    await _reset_login_failures(s, user)

    ms = [] if user.is_platform else await memberships(s, user.id)
    membership = None if user.is_platform else _pick_membership(ms, hotel_id)

    factor = (
        await s.execute(
            select(MfaFactor.id).where(MfaFactor.user_id == user.id, MfaFactor.confirmed_at.is_not(None))
        )
    ).first()
    if factor is not None:
        mfa_claims: dict[str, Any] = {"sub": str(user.id)}
        if membership is not None:
            mfa_claims["hid"] = str(membership.hotel_id)
        mfa_token, _ = st.jwt.sign("mfa_pending", mfa_claims, MFA_PENDING_TTL_S)
        return LoginResult(user=user, hotels=ms, mfa_token=mfa_token)

    user.last_login_at = now
    pending = mfa_required_for(user, membership)
    tokens = await issue_session(st, s, user, membership, ["pwd"], client, mfa_pending=pending)
    return LoginResult(user=user, hotels=ms, tokens=tokens)


async def _verify_second_factor(
    st: AppState, s: AsyncSession, user: User, code: str | None, recovery_code: str | None, client: ClientInfo
) -> None:
    factor = (
        await s.execute(
            select(MfaFactor)
            .where(MfaFactor.user_id == user.id, MfaFactor.confirmed_at.is_not(None))
            .order_by(MfaFactor.created_at.desc())
            .limit(1)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if factor is None:
        raise AppError("UNAUTHENTICATED")
    if code:
        secret = (await st.keyring.decrypt("platform", factor.secret_enc, f"mfa:{user.id}")).decode()
        step = mfa.verify_code(secret, code, factor.last_used_step)
        if step is not None:
            factor.last_used_step = step
            return
    elif recovery_code:
        row = (
            await s.execute(
                select(MfaRecoveryCode)
                .where(
                    MfaRecoveryCode.user_id == user.id,
                    MfaRecoveryCode.code_hash == mfa.recovery_hash(recovery_code),
                    MfaRecoveryCode.used_at.is_(None),
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is not None:
            row.used_at = _now()
            security_event("auth.recovery_code_used", user_id=str(user.id))
            return
    security_event("auth.mfa_failed", user_id=str(user.id), ip=client.ip)
    await _record_login_failure(st, user.id, client, "bad_mfa_code")
    raise AppError("UNAUTHENTICATED", "That code is not valid.", details={"reason": "invalid_code"})


async def verify_mfa_login(
    st: AppState,
    uow: UnitOfWork,
    mfa_token: str,
    code: str | None,
    recovery_code: str | None,
    client: ClientInfo,
) -> LoginResult:
    claims = st.jwt.verify(mfa_token, "mfa_pending")
    s = uow.session
    user = (await s.execute(select(User).where(User.id == uuid.UUID(claims["sub"])))).scalar_one_or_none()
    if user is None or user.status != "active" or (user.locked_until and user.locked_until > _now()):
        raise AppError("UNAUTHENTICATED")
    await _verify_second_factor(st, s, user, code, recovery_code, client)
    ms = [] if user.is_platform else await memberships(s, user.id)
    membership = None
    if not user.is_platform:
        membership = _pick_membership(ms, uuid.UUID(claims["hid"]) if claims.get("hid") else None)
    user.last_login_at = _now()
    await _reset_login_failures(s, user)
    tokens = await issue_session(st, s, user, membership, ["pwd", "mfa"], client)
    return LoginResult(user=user, hotels=ms, tokens=tokens)


async def enroll_mfa(st: AppState, uow: UnitOfWork, user_id: uuid.UUID) -> dict[str, str]:
    s = uow.session
    user = (await s.execute(select(User).where(User.id == user_id))).scalar_one()
    confirmed = (
        await s.execute(
            select(MfaFactor.id).where(MfaFactor.user_id == user_id, MfaFactor.confirmed_at.is_not(None))
        )
    ).first()
    if confirmed is not None:
        raise AppError("INVALID_TRANSITION", "Two-step sign-in is already set up.")
    secret = mfa.new_secret()
    await s.execute(
        insert(MfaFactor).values(
            user_id=user_id,
            kind="totp",
            secret_enc=await st.keyring.encrypt("platform", secret.encode(), f"mfa:{user_id}"),
        )
    )
    return {"secret": secret, "otpauth_uri": mfa.provisioning_uri(secret, user.email)}


async def confirm_mfa(
    st: AppState, uow: UnitOfWork, user_id: uuid.UUID, session_id: uuid.UUID, code: str, client: ClientInfo
) -> tuple[LoginResult, list[str]]:
    """Confirm the newest unconfirmed factor with a code; rotate into a full-MFA session."""
    s = uow.session
    user = (await s.execute(select(User).where(User.id == user_id))).scalar_one()
    factor = (
        await s.execute(
            select(MfaFactor)
            .where(MfaFactor.user_id == user_id, MfaFactor.confirmed_at.is_(None))
            .order_by(MfaFactor.created_at.desc())
            .limit(1)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if factor is None:
        raise AppError("INVALID_TRANSITION", "Start two-step sign-in set-up first.")
    secret = (await st.keyring.decrypt("platform", factor.secret_enc, f"mfa:{user_id}")).decode()
    step = mfa.verify_code(secret, code, factor.last_used_step)
    if step is None:
        await _record_login_failure(st, user_id, client, "bad_mfa_enrol_code")
        raise AppError("UNAUTHENTICATED", "That code is not valid.", details={"reason": "invalid_code"})
    now = _now()
    factor.confirmed_at, factor.last_used_step = now, step
    codes = mfa.new_recovery_codes()
    await s.execute(
        insert(MfaRecoveryCode), [{"user_id": user_id, "code_hash": mfa.recovery_hash(c)} for c in codes]
    )

    current = (
        await s.execute(select(Session).where(Session.id == session_id).with_for_update())
    ).scalar_one()
    current.revoked_at, current.revoked_reason = now, "mfa_upgraded"
    ms = [] if user.is_platform else await memberships(s, user.id)
    membership = None if user.is_platform else _pick_membership(ms, current.active_hotel_id)
    tokens = await issue_session(st, s, user, membership, ["pwd", "mfa"], client, family_id=current.family_id)
    await write_platform_audit(
        s,
        actor_type="user",
        actor_id=user.id,
        actor_label=user.name,
        action="auth.mfa_enrolled",
        entity_type="user",
        entity_id=user.id,
        ip=client.ip,
        request_id=client.request_id,
    )
    return LoginResult(user=user, hotels=ms, tokens=tokens), codes


# --- Refresh, logout, sessions ---------------------------------------------------------------


async def _revoke_family(st: AppState, family_id: uuid.UUID, reason: str) -> None:
    async with st.db.sessionmaker() as s, s.begin():
        await s.execute(
            update(Session)
            .where(Session.family_id == family_id, Session.revoked_at.is_(None))
            .values(revoked_at=_now(), revoked_reason=reason)
        )


async def refresh(
    st: AppState, uow: UnitOfWork, refresh_token: str, hotel_id: uuid.UUID | None, client: ClientInfo
) -> LoginResult:
    s = uow.session
    row = (
        await s.execute(
            select(Session).where(Session.refresh_hash == crypto.sha256(refresh_token)).with_for_update()
        )
    ).scalar_one_or_none()
    now = _now()
    if row is None:
        raise AppError("UNAUTHENTICATED")
    if row.revoked_at is not None:
        if row.revoked_reason in ("rotated", "mfa_upgraded"):
            # A token that was already exchanged is being used again: assume theft.
            await _revoke_family(st, row.family_id, "refresh_reuse")
            security_event(
                "auth.refresh_reuse", user_id=str(row.user_id), family_id=str(row.family_id), ip=client.ip
            )
            await _notify_refresh_reuse(st, row.user_id)
        raise AppError("UNAUTHENTICATED")
    if row.expires_at <= now or (client.web and row.last_used_at < now - WEB_IDLE):
        raise AppError("UNAUTHENTICATED")

    user = (await s.execute(select(User).where(User.id == row.user_id))).scalar_one()
    if user.status != "active":
        raise AppError("UNAUTHENTICATED")
    ms = [] if user.is_platform else await memberships(s, user.id)
    membership = None if user.is_platform else _pick_membership(ms, hotel_id or row.active_hotel_id)

    amr = list(row.amr)
    pending = mfa_required_for(user, membership) and "mfa" not in amr
    row.revoked_at, row.revoked_reason = now, "rotated"
    tokens = await issue_session(
        st, s, user, membership, amr, client, family_id=row.family_id, mfa_pending=pending
    )
    return LoginResult(user=user, hotels=ms, tokens=tokens)


async def _notify_refresh_reuse(st: AppState, user_id: uuid.UUID) -> None:
    async with st.db.sessionmaker() as s, s.begin():
        uow = UnitOfWork(s, st.db.sessionmaker)
        user = (await s.execute(select(User).where(User.id == user_id))).scalar_one()
        await st.mailer.queue(
            uow,
            hotel_id=None,
            template="session_reuse",
            to=user.email,
            subject="We signed you out of Diyneco",
            body=(
                "A sign-in token for your account was used twice, which can mean it was copied. "
                "We signed that session out everywhere. If this was not you, change your password."
            ),
        )
    await uow.run_after_commit()


async def logout(uow: UnitOfWork, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
    await uow.session.execute(
        update(Session)
        .where(Session.id == session_id, Session.user_id == user_id, Session.revoked_at.is_(None))
        .values(revoked_at=_now(), revoked_reason="logout")
    )


async def list_sessions(uow: UnitOfWork, user_id: uuid.UUID, current: uuid.UUID) -> list[dict[str, Any]]:
    rows = (
        (
            await uow.session.execute(
                select(Session)
                .where(Session.user_id == user_id, Session.revoked_at.is_(None), Session.expires_at > _now())
                .order_by(Session.last_used_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": r.id,
            "user_agent": r.user_agent,
            "ip": str(r.ip) if r.ip else None,
            "created_at": r.created_at,
            "last_used_at": r.last_used_at,
            "current": r.id == current,
        }
        for r in rows
    ]


async def revoke_session(uow: UnitOfWork, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
    result = await uow.session.execute(
        update(Session)
        .where(Session.id == session_id, Session.user_id == user_id, Session.revoked_at.is_(None))
        .values(revoked_at=_now(), revoked_reason="user_revoked")
        .returning(Session.id)
    )
    if result.first() is None:
        raise AppError("NOT_FOUND")


async def revoke_all_sessions(session: AsyncSession, user_id: uuid.UUID, reason: str) -> None:
    await session.execute(
        update(Session)
        .where(Session.user_id == user_id, Session.revoked_at.is_(None))
        .values(revoked_at=_now(), revoked_reason=reason)
    )


# --- Step-up and PIN ----------------------------------------------------------------------


async def _record_pin_failure(
    st: AppState, hotel_id: uuid.UUID, hotel_user_id: uuid.UUID, user_id: uuid.UUID
) -> int:
    async with st.db.sessionmaker() as s, s.begin():
        await set_tenant(s, hotel_id, user_id)
        hu = (
            await s.execute(select(HotelUser).where(HotelUser.id == hotel_user_id).with_for_update())
        ).scalar_one()
        now = _now()
        if hu.pin_failed_window_start is None or hu.pin_failed_window_start < now - LOCKOUT_WINDOW:
            hu.pin_failed_window_start, hu.pin_failed = now, 1
        else:
            hu.pin_failed += 1
        if hu.pin_failed >= LOCKOUT_THRESHOLD:
            hu.pin_locked_until = now + LOCKOUT_DURATION
            security_event("auth.pin_locked", hotel_id=str(hotel_id), user_id=str(user_id))
        return max(0, LOCKOUT_THRESHOLD - hu.pin_failed)


async def check_member_pin(st: AppState, hotel_id: uuid.UUID, hu: HotelUser, pin: str) -> None:
    """Verify a member's PIN: 5 failures in 15 minutes lock it for 15 minutes. Failures are
    recorded in their own transaction so a rolled-back request still counts them."""
    now = _now()
    if hu.pin_locked_until and hu.pin_locked_until > now:
        raise AppError(
            "PIN_INVALID",
            "Your PIN is locked for 15 minutes.",
            details={"attempts_left": 0, "locked_until": hu.pin_locked_until.isoformat()},
        )
    if hu.pin_hash is None:
        raise AppError("PIN_INVALID", "Set a PIN first.", details={"reason": "pin_not_set"})
    if not crypto.verify_secret(hu.pin_hash, pin):
        left = await _record_pin_failure(st, hotel_id, hu.id, hu.user_id)
        raise AppError("PIN_INVALID", "That PIN is not correct.", details={"attempts_left": left})
    hu.pin_failed, hu.pin_failed_window_start, hu.pin_locked_until = 0, None, None


async def step_up(
    st: AppState,
    uow: UnitOfWork,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    hotel_id: uuid.UUID | None,
    hotel_user_id: uuid.UUID | None,
    pin: str | None,
    password: str | None,
    client: ClientInfo,
) -> tuple[str, int]:
    s = uow.session
    now = _now()
    if pin is not None:
        if hotel_user_id is None or hotel_id is None:
            raise AppError("PIN_INVALID", "Use your password to confirm.", details={"attempts_left": 0})
        hu = (await s.execute(select(HotelUser).where(HotelUser.id == hotel_user_id))).scalar_one()
        await check_member_pin(st, hotel_id, hu, pin)
    elif password is not None:
        user = (await s.execute(select(User).where(User.id == user_id))).scalar_one()
        if user.locked_until and user.locked_until > now:
            raise AppError(
                "PIN_INVALID", "Your account is locked for 15 minutes.", details={"attempts_left": 0}
            )
        if not crypto.verify_secret(user.password_hash, password):
            await _record_login_failure(st, user_id, client, "bad_step_up_password")
            raise AppError("PIN_INVALID", "That password is not correct.", details={"credential": "password"})
    else:
        raise AppError("VALIDATION_FAILED", "Send a pin or a password.")
    claims: dict[str, Any] = {"sub": str(user_id), "sid": str(session_id)}
    if hotel_id is not None:
        claims["hid"] = str(hotel_id)
    return st.jwt.sign("step_up", claims, STEP_UP_TTL_S)


async def set_pin(uow: UnitOfWork, ctx: TenantContext, hotel_user_id: uuid.UUID, pin: str) -> None:
    check_pin(pin)
    hu = (await uow.session.execute(select(HotelUser).where(HotelUser.id == hotel_user_id))).scalar_one()
    hu.pin_hash = crypto.hash_secret(pin)
    hu.pin_failed, hu.pin_failed_window_start, hu.pin_locked_until = 0, None, None
    await write_audit(uow.session, ctx, "staff.pin_set", "hotel_user", hotel_user_id)


# --- Password reset and email verification ------------------------------------------------


async def create_one_time_token(
    session: AsyncSession, user_id: uuid.UUID, purpose: str, ttl: timedelta
) -> str:
    token = crypto.random_token()
    await session.execute(
        insert(OneTimeToken).values(
            token_hash=crypto.sha256(token), user_id=user_id, purpose=purpose, expires_at=_now() + ttl
        )
    )
    return token


async def _consume_token(session: AsyncSession, token: str, purpose: str) -> OneTimeToken:
    row = (
        await session.execute(
            select(OneTimeToken)
            .where(OneTimeToken.token_hash == crypto.sha256(token), OneTimeToken.purpose == purpose)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if row is None or row.used_at is not None or row.expires_at <= _now():
        raise AppError(
            "VALIDATION_FAILED",
            "This link is invalid or has expired.",
            details={"fields": [{"field": "token", "problem": "Invalid or expired.", "type": "token"}]},
        )
    row.used_at = _now()
    return row


async def forgot_password(st: AppState, uow: UnitOfWork, email: str) -> None:
    user = (await uow.session.execute(select(User).where(User.email == email.strip()))).scalar_one_or_none()
    if user is None or user.status not in ("active", "locked") or user.password_hash is None:
        return  # same response either way
    token = await create_one_time_token(uow.session, user.id, "password_reset", RESET_TOKEN_TTL)
    await st.mailer.queue(
        uow,
        hotel_id=None,
        template="password_reset",
        to=user.email,
        subject="Reset your Diyneco password",
        body=f"Use this code within 30 minutes to choose a new password:\n\n{token}\n\n"
        "If you did not ask for this, ignore this email.",
    )


async def reset_password(
    st: AppState, uow: UnitOfWork, token: str, new_password: str, client: ClientInfo
) -> None:
    s = uow.session
    row = await _consume_token(s, token, "password_reset")
    user = (await s.execute(select(User).where(User.id == row.user_id).with_for_update())).scalar_one()
    check_password(new_password, email=user.email, field="new_password")
    user.password_hash = crypto.hash_secret(new_password)
    await _reset_login_failures(s, user)
    await revoke_all_sessions(s, user.id, "password_reset")
    await write_platform_audit(
        s,
        actor_type="user",
        actor_id=user.id,
        actor_label=user.name,
        action="auth.password_reset",
        entity_type="user",
        entity_id=user.id,
        ip=client.ip,
        request_id=client.request_id,
    )
    await st.mailer.queue(
        uow,
        hotel_id=None,
        template="password_changed",
        to=user.email,
        subject="Your Diyneco password was changed",
        body="Your password was changed and every session was signed out.",
    )


async def verify_email(uow: UnitOfWork, token: str) -> None:
    row = await _consume_token(uow.session, token, "email_verify")
    await uow.session.execute(
        update(User)
        .where(User.id == row.user_id, User.email_verified_at.is_(None))
        .values(email_verified_at=_now())
    )


async def send_verification_email(
    st: AppState, uow: UnitOfWork, user: User, hotel_id: uuid.UUID | None
) -> None:
    token = await create_one_time_token(uow.session, user.id, "email_verify", VERIFY_TOKEN_TTL)
    await st.mailer.queue(
        uow,
        hotel_id=hotel_id,
        template="email_verify",
        to=user.email,
        subject="Confirm your email for Diyneco",
        body=f"Use this code within 24 hours to confirm your email address:\n\n{token}\n",
    )


async def me(
    uow: UnitOfWork,
    *,
    kind: str,
    user_id: uuid.UUID | None,
    hotel_id: uuid.UUID | None,
    roles: tuple[str, ...],
    permissions: frozenset[str],
    amr: tuple[str, ...],
    mfa_pending: bool,
) -> dict[str, Any]:
    s = uow.session
    user = (await s.execute(select(User).where(User.id == user_id))).scalar_one_or_none() if user_id else None
    hotel = (
        (await s.execute(select(Hotel).where(Hotel.id == hotel_id))).scalar_one_or_none()
        if hotel_id
        else None
    )
    return {
        "kind": kind,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "email_verified": user.email_verified_at is not None,
        }
        if user
        else None,
        "hotel": {"id": hotel.id, "name": hotel.name, "status": hotel.status} if hotel else None,
        "roles": list(roles),
        "permissions": sorted(permissions),
        "mfa": "mfa" in amr,
        "mfa_pending": mfa_pending,
    }
