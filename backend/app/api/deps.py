"""Request dependencies: transaction, principal, tenancy, permissions, step-up, rate limits.

Authorisation always checks a permission code, never a role name. The hotel always comes
from the token, never from the request; X-Hotel-Id, if sent, must equal the token's hotel.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from fastapi import Depends, Request
from fastapi.dependencies.models import Dependant
from sqlalchemy import select, text

from app.core.crypto import CARD_FIELD_NAMES, looks_like_card_number
from app.core.errors import AppError
from app.core.logging import request_id_var, security_event
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.tenancy import Hotel, HotelUser, Role, RolePermission, Session, User, UserRole
from app.services.devices import check_device
from app.services.idempotency import IdempotencyClaim, claim, parse_key, request_fingerprint

PrincipalKind = Literal["staff", "platform", "device", "kitchen_session", "api_key"]
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def state_of(request: Request) -> AppState:
    st: AppState = request.app.state.diyneco
    return st


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# --- Transaction ---------------------------------------------------------------------------


async def _uow(request: Request) -> AsyncIterator[UnitOfWork]:
    db = state_of(request).db
    async with db.sessionmaker() as session:
        uow = UnitOfWork(session, db.sessionmaker)
        await session.begin()
        try:
            yield uow
        except BaseException:
            await session.rollback()
            raise
        await session.commit()
    await uow.run_after_commit()


# scope="function": commit happens after the endpoint returns but before the response is
# sent, so a client never sees success for a transaction that failed to commit.
Uow = Annotated[UnitOfWork, Depends(_uow, scope="function")]


# --- Request hygiene -----------------------------------------------------------------------


def _query_names(dep: Dependant) -> set[str]:
    names = {p.alias for p in dep.query_params}
    for sub in dep.dependencies:
        names |= _query_names(sub)
    return names


async def reject_unknown_query(request: Request) -> None:
    """Only documented filters are accepted (API spec, Conventions)."""
    route = request.scope.get("route")
    dependant = getattr(route, "dependant", None)
    if dependant is None or not request.query_params:
        return
    unknown = sorted(set(request.query_params.keys()) - _query_names(dependant))
    if unknown:
        raise AppError(
            "VALIDATION_FAILED",
            "Unknown query parameter.",
            details={
                "fields": [
                    {"field": n, "problem": "Unknown query parameter.", "type": "extra_forbidden"}
                    for n in unknown
                ]
            },
        )


def _scan_for_card_data(value: Any, path: str = "") -> str | None:
    if isinstance(value, dict):
        for k, v in value.items():
            p = f"{path}.{k}" if path else str(k)
            if str(k).lower() in CARD_FIELD_NAMES:
                return p
            found = _scan_for_card_data(v, p)
            if found:
                return found
    elif isinstance(value, list):
        for i, v in enumerate(value):
            found = _scan_for_card_data(v, f"{path}[{i}]")
            if found:
                return found
    elif isinstance(value, str | int) and not isinstance(value, bool) and looks_like_card_number(str(value)):
        return path or "body"
    return None


async def reject_card_data(request: Request) -> None:
    """No card numbers, CVV, PIN-block or track data are accepted anywhere (PCI scope)."""
    if request.method in SAFE_METHODS:
        return
    if "application/json" not in request.headers.get("content-type", ""):
        return
    try:
        body = await request.json()
    except ValueError:
        return  # malformed JSON is reported by validation
    field = _scan_for_card_data(body)
    if field:
        security_event("payment.card_data_rejected", field=field, path=request.url.path)
        raise AppError("CARD_DATA_REJECTED", details={"field": field})


# --- Rate limits ---------------------------------------------------------------------------


async def _limit(request: Request, bucket: str, key: str) -> None:
    decision = await state_of(request).limiter.hit(bucket, key)
    request.state.rate_headers = {
        "RateLimit-Limit": str(decision.limit),
        "RateLimit-Remaining": str(decision.remaining),
        "RateLimit-Reset": str(decision.reset_s),
    }
    if not decision.allowed:
        raise AppError(
            "RATE_LIMITED", headers={**request.state.rate_headers, "Retry-After": str(decision.reset_s)}
        )


async def limit_auth_ip(request: Request) -> None:
    await _limit(request, "auth_ip", client_ip(request) or "unknown")


# --- Principals ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Principal:
    kind: PrincipalKind
    user_id: uuid.UUID | None
    session_id: uuid.UUID | None
    hotel_id: uuid.UUID | None
    hotel_user_id: uuid.UUID | None
    permissions: frozenset[str]
    amr: tuple[str, ...]
    name: str
    role_names: tuple[str, ...]
    device_id: uuid.UUID | None = None
    mfa_pending: bool = False

    @property
    def uid(self) -> uuid.UUID:
        if self.user_id is None:
            raise AppError("UNAUTHENTICATED")
        return self.user_id

    @property
    def sid(self) -> uuid.UUID:
        if self.session_id is None:
            raise AppError("UNAUTHENTICATED")
        return self.session_id

    @property
    def label(self) -> str:
        roles = ", ".join(self.role_names)
        return f"{self.name} ({roles})" if roles else self.name

    @property
    def idempotency_key(self) -> str:
        if self.kind in ("device",):
            return f"device:{self.device_id}"
        return f"user:{self.user_id}"

    def tenant(self, request: Request) -> TenantContext:
        if self.hotel_id is None:
            raise AppError("PERMISSION_DENIED")
        actor_type = {"platform": "platform", "device": "device"}.get(self.kind, "user")
        return TenantContext(
            hotel_id=self.hotel_id,
            actor_type=actor_type,
            actor_id=self.user_id,
            actor_label=self.label,
            device_id=self.device_id,
            ip=client_ip(request),
            request_id=request_id_var.get(),
        )


_BEARER = re.compile(r"^Bearer ([A-Za-z0-9_\-.]+)$")


def bearer_token(request: Request) -> str:
    match = _BEARER.match(request.headers.get("authorization", ""))
    if not match:
        raise AppError("UNAUTHENTICATED")
    return match.group(1)


async def _resolve_principal(request: Request, uow: UnitOfWork, *, allow_mfa_pending: bool) -> Principal:
    st = state_of(request)
    claims = st.jwt.verify(bearer_token(request), "access")
    kind = claims.get("kind")
    if kind not in ("staff", "platform"):
        # Device and kitchen-session principals have their own endpoints (Phases 3-4).
        raise AppError("UNAUTHENTICATED")
    try:
        user_id = uuid.UUID(str(claims["sub"]))
        session_id = uuid.UUID(str(claims["sid"]))
        hotel_id = uuid.UUID(str(claims["hid"])) if claims.get("hid") else None
    except (KeyError, ValueError) as exc:
        raise AppError("UNAUTHENTICATED") from exc
    amr = tuple(claims.get("amr") or ())
    mfa_pending = bool(claims.get("mfa_pending"))
    if mfa_pending and not allow_mfa_pending:
        raise AppError("MFA_REQUIRED", "Set up two-step sign-in to continue.", details={"next": "mfa_enroll"})

    if kind == "staff" and hotel_id is None:
        raise AppError("UNAUTHENTICATED")
    header_hotel = request.headers.get("x-hotel-id")
    if header_hotel and (hotel_id is None or header_hotel.lower() != str(hotel_id)):
        # The token is bound to one hotel; switching goes through /auth/refresh (G11).
        raise AppError("NOT_FOUND")

    s = uow.session
    await set_tenant(s, hotel_id, user_id)

    session_row = (
        await s.execute(
            select(Session.id).where(
                Session.id == session_id,
                Session.user_id == user_id,
                Session.revoked_at.is_(None),
                Session.expires_at > text("now()"),
            )
        )
    ).first()
    user = (await s.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if session_row is None or user is None or user.status not in ("active",):
        raise AppError("UNAUTHENTICATED")

    if kind == "platform":
        if not user.is_platform:
            raise AppError("UNAUTHENTICATED")
        if "mfa" not in amr and not mfa_pending:
            raise AppError("MFA_REQUIRED")
        rows = (
            await s.execute(
                text(
                    "SELECT r.name, rp.permission_code FROM app.platform_user_roles pur "
                    "JOIN app.roles r ON r.id = pur.role_id "
                    "JOIN app.role_permissions rp ON rp.role_id = r.id WHERE pur.user_id = :u"
                ),
                {"u": user_id},
            )
        ).all()
        principal = Principal(
            kind="platform",
            user_id=user_id,
            session_id=session_id,
            hotel_id=None,
            hotel_user_id=None,
            permissions=frozenset(r[1] for r in rows),
            amr=amr,
            name=user.name,
            role_names=tuple(sorted({r[0] for r in rows})),
            mfa_pending=mfa_pending,
        )
    else:
        membership = (
            await s.execute(
                select(HotelUser).where(HotelUser.user_id == user_id, HotelUser.status == "active")
            )
        ).scalar_one_or_none()  # RLS: only rows of the token's hotel are visible
        if membership is None or membership.hotel_id != hotel_id:
            raise AppError("UNAUTHENTICATED")
        if claims.get("perms_v") != membership.perms_version:
            raise AppError(
                "UNAUTHENTICATED",
                "Your access changed. Please refresh your session.",
                details={"reason": "perms_changed"},
            )
        hotel_status = (
            await s.execute(select(Hotel.status).where(Hotel.id == hotel_id))
        ).scalar_one_or_none()
        if hotel_status is None:
            raise AppError("UNAUTHENTICATED")
        if hotel_status in ("suspended", "closed") and request.method not in SAFE_METHODS:
            raise AppError("HOTEL_SUSPENDED", "This hotel's account is suspended. Data can still be viewed.")
        rows = (
            await s.execute(
                select(Role.name, RolePermission.permission_code)
                .select_from(UserRole)
                .join(Role, Role.id == UserRole.role_id)
                .outerjoin(RolePermission, RolePermission.role_id == Role.id)
                .where(UserRole.hotel_user_id == membership.id)
            )
        ).all()
        principal = Principal(
            kind="staff",
            user_id=user_id,
            session_id=session_id,
            hotel_id=hotel_id,
            hotel_user_id=membership.id,
            permissions=frozenset(r[1] for r in rows if r[1] is not None),
            amr=amr,
            name=user.name,
            role_names=tuple(sorted({r[0] for r in rows})),
            mfa_pending=mfa_pending,
        )

    await _limit(request, "staff", f"user:{user_id}")
    request.state.principal = principal
    return principal


async def get_principal(request: Request, uow: Uow) -> Principal:
    return await _resolve_principal(request, uow, allow_mfa_pending=False)


async def get_principal_allow_mfa_pending(request: Request, uow: Uow) -> Principal:
    """Only for the MFA enrolment endpoints and logout."""
    return await _resolve_principal(request, uow, allow_mfa_pending=True)


async def _resolve_device(request: Request, uow: UnitOfWork, *, allow_locked: bool) -> Principal:
    """Device token checks (API spec, Devices), in order: credential valid and not revoked,
    device enabled, hotel active, still bound to the token's room, room still exists."""
    claims = state_of(request).jwt.verify(bearer_token(request), "access", error_code="DEVICE_UNAUTHORISED")
    if claims.get("kind") != "device":
        raise AppError("DEVICE_UNAUTHORISED")
    try:
        device_id = uuid.UUID(str(claims["sub"]))
        hotel_id = uuid.UUID(str(claims["hid"]))
    except (KeyError, ValueError) as exc:
        raise AppError("DEVICE_UNAUTHORISED") from exc
    await set_tenant(uow.session, hotel_id, actor_device=device_id)
    device = await check_device(
        uow.session,
        hotel_id,
        device_id,
        room_claim=claims.get("rid") if claims.get("dk") == "guest" else None,
        allow_locked=allow_locked,
    )
    await _limit(request, "device", f"device:{device_id}")
    principal = Principal(
        kind="device",
        user_id=None,
        session_id=None,
        hotel_id=hotel_id,
        hotel_user_id=None,
        permissions=frozenset(),
        amr=(),
        name=device.label,
        role_names=(),
        device_id=device_id,
    )
    request.state.principal = principal
    request.state.device = device
    return principal


async def get_device_any_state(request: Request, uow: Uow) -> Principal:
    """Heartbeat: a locked device must still reach the server to learn it was unlocked."""
    return await _resolve_device(request, uow, allow_locked=True)


async def get_device_active(request: Request, uow: Uow) -> Principal:
    return await _resolve_device(request, uow, allow_locked=False)


CurrentPrincipal = Annotated[Principal, Depends(get_principal)]
DeviceAnyState = Annotated[Principal, Depends(get_device_any_state)]
DevicePrincipal = Annotated[Principal, Depends(get_device_active)]
PendingPrincipal = Annotated[Principal, Depends(get_principal_allow_mfa_pending)]


def require_permission(code: str) -> Callable[..., Coroutine[Any, Any, Principal]]:
    async def _check(request: Request, principal: CurrentPrincipal) -> Principal:
        if code not in principal.permissions:
            security_event(
                "rbac.permission_denied",
                permission=code,
                user_id=str(principal.user_id),
                path=request.url.path,
            )
            raise AppError("PERMISSION_DENIED")
        return principal

    _check.__name__ = f"require_{code.replace('.', '_')}"
    return _check


async def require_step_up(request: Request, principal: CurrentPrincipal) -> Principal:
    """X-Step-Up token from POST /auth/step-up: 5 minutes, bound to this user and session."""
    if not has_step_up(request, principal):
        raise AppError("STEP_UP_REQUIRED")
    return principal


StepUp = Annotated[Principal, Depends(require_step_up)]


def has_step_up(request: Request, principal: Principal) -> bool:
    """For endpoints where only some changes need step-up (e.g. a rate change): False when
    no X-Step-Up header was sent, True when a valid one was, and STEP_UP_REQUIRED when the
    header is present but invalid or expired."""
    if not request.headers.get("x-step-up"):
        return False
    token = request.headers["x-step-up"]
    claims = state_of(request).jwt.verify(token, "step_up", error_code="STEP_UP_REQUIRED")
    if claims.get("sub") != str(principal.user_id) or claims.get("sid") != str(principal.session_id):
        raise AppError("STEP_UP_REQUIRED")
    if principal.hotel_id is not None and claims.get("hid") != str(principal.hotel_id):
        raise AppError("STEP_UP_REQUIRED")
    return True


# --- Idempotency ---------------------------------------------------------------------------
# Declare these FIRST in an endpoint's parameters. They do not touch the request's
# transaction, so they are set up before it and torn down after it: on failure, the
# request has already rolled back when the outcome is stored or the key released.


async def _claim(request: Request, principal_key: str) -> IdempotencyClaim:
    body = await request.body()
    return await claim(
        state_of(request).db.sessionmaker,
        principal_key,
        parse_key(request),
        request.method,
        request.url.path,
        request_fingerprint(request.method, request.url.path, body),
    )


# Each dependency yields directly (no nested generator), so an exception raised by the
# endpoint reaches the `except` below and the outcome is stored or the key released.


async def _idempotency_anon(request: Request) -> AsyncIterator[IdempotencyClaim]:
    claim_ = await _claim(request, "anon")
    try:
        yield claim_
    except BaseException as exc:
        await claim_.fail(exc)
        raise


async def _idempotency_user(request: Request) -> AsyncIterator[IdempotencyClaim]:
    claims = state_of(request).jwt.verify(bearer_token(request), "access")
    claim_ = await _claim(request, f"user:{claims['sub']}")
    try:
        yield claim_
    except BaseException as exc:
        await claim_.fail(exc)
        raise


IdemAnon = Annotated[IdempotencyClaim, Depends(_idempotency_anon, scope="function")]
IdemUser = Annotated[IdempotencyClaim, Depends(_idempotency_user, scope="function")]
