"""/auth: sign-in, MFA, refresh, sessions, step-up, PIN, password reset, email verification,
invitation acceptance. Kitchen sign-in (/auth/kitchen/sign-in) arrives with the kitchen
display in Phase 4."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from app.api.deps import (
    CurrentPrincipal,
    IdemAnon,
    PendingPrincipal,
    StepUp,
    Uow,
    client_ip,
    get_principal_allow_mfa_pending,
    limit_auth_ip,
    state_of,
)
from app.core.errors import AppError
from app.core.logging import request_id_var
from app.schemas.auth import (
    AcceptedResponse,
    AcceptInvitationRequest,
    ForgotPasswordRequest,
    InvitationAcceptedResponse,
    LoginRequest,
    MfaChallengeResponse,
    MfaConfirmResponse,
    MfaEnrollResponse,
    MfaVerifyRequest,
    RefreshRequest,
    ResetPasswordRequest,
    SessionList,
    SetPinRequest,
    StepUpRequest,
    StepUpResponse,
    TokenResponse,
    VerifyEmailRequest,
)
from app.services import auth as auth_service
from app.services import invitations

router = APIRouter(prefix="/auth", tags=["auth"])
AuthLimited = [Depends(limit_auth_ip)]

REFRESH_COOKIE = "__Host-diyneco_rt"


def _client(request: Request) -> auth_service.ClientInfo:
    origin = request.headers.get("origin")
    web = bool(origin and origin in state_of(request).settings.cors_allowed_origins)
    return auth_service.ClientInfo(
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        request_id=request_id_var.get(),
        web=web,
    )


def _token_response(
    result: auth_service.LoginResult,
    client: auth_service.ClientInfo,
    extra: dict[str, Any] | None = None,
    status_code: int = 200,
) -> JSONResponse:
    t = result.tokens
    if t is None:
        raise AppError("INTERNAL_ERROR")
    body: dict[str, Any] = {
        "access_token": t.access_token,
        "token_type": "Bearer",
        "expires_in": t.expires_in,
        "refresh_token": None if client.web else t.refresh_token,
        "mfa_enrolment_required": t.mfa_pending,
        "user": auth_service.user_payload(result.user),
        "hotels": auth_service.hotels_payload(result.hotels),
        **(extra or {}),
    }
    model = MfaConfirmResponse if extra and "recovery_codes" in extra else TokenResponse
    response = JSONResponse(model.model_validate(body).model_dump(mode="json"), status_code=status_code)
    if client.web:
        response.set_cookie(
            REFRESH_COOKIE,
            t.refresh_token,
            max_age=int(auth_service.REFRESH_TTL.total_seconds()),
            path="/",
            secure=True,
            httponly=True,
            samesite="strict",
        )
    return response


@router.post(
    "/login", dependencies=AuthLimited, responses={200: {"model": TokenResponse | MfaChallengeResponse}}
)
async def login(body: LoginRequest, request: Request, uow: Uow) -> JSONResponse:
    client = _client(request)
    result = await auth_service.login(
        state_of(request), uow, body.email, body.password, body.hotel_id, client
    )
    if result.mfa_token is not None:
        return JSONResponse(MfaChallengeResponse(mfa_token=result.mfa_token).model_dump())
    return _token_response(result, client)


@router.post(
    "/mfa/verify", dependencies=AuthLimited, responses={200: {"model": TokenResponse | MfaConfirmResponse}}
)
async def mfa_verify(body: MfaVerifyRequest, request: Request, uow: Uow) -> JSONResponse:
    """With `mfa_token`: complete a sign-in. Without it, with a bearer token: confirm a new
    TOTP factor from /auth/mfa/enroll (returns new tokens and the recovery codes, once)."""
    st, client = state_of(request), _client(request)
    if body.mfa_token:
        result = await auth_service.verify_mfa_login(
            st, uow, body.mfa_token, body.code, body.recovery_code, client
        )
        return _token_response(result, client)
    if body.code is None:
        raise AppError("VALIDATION_FAILED", "Send the 6-digit code from your authenticator app.")
    principal = await get_principal_allow_mfa_pending(request, uow)
    result, codes = await auth_service.confirm_mfa(st, uow, principal.uid, principal.sid, body.code, client)
    return _token_response(result, client, extra={"recovery_codes": codes})


@router.post("/mfa/enroll", response_model=MfaEnrollResponse)
async def mfa_enroll(request: Request, uow: Uow, principal: PendingPrincipal) -> dict[str, str]:
    return await auth_service.enroll_mfa(state_of(request), uow, principal.uid)


@router.post("/refresh", dependencies=AuthLimited, response_model=TokenResponse)
async def refresh(body: RefreshRequest, request: Request, uow: Uow) -> JSONResponse:
    client = _client(request)
    token = body.refresh_token
    if token is None and client.web:
        token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise AppError("UNAUTHENTICATED")
    result = await auth_service.refresh(state_of(request), uow, token, body.hotel_id, client)
    return _token_response(result, client)


@router.post("/logout", status_code=204)
async def logout(uow: Uow, principal: PendingPrincipal) -> Response:
    await auth_service.logout(uow, principal.sid, principal.uid)
    response = Response(status_code=204)
    response.delete_cookie(REFRESH_COOKIE, path="/", secure=True, httponly=True, samesite="strict")
    return response


@router.get("/sessions", response_model=SessionList)
async def list_sessions(uow: Uow, principal: CurrentPrincipal) -> dict[str, Any]:
    return {
        "data": await auth_service.list_sessions(uow, principal.uid, principal.sid),
        "next_cursor": None,
    }


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke_session(session_id: uuid.UUID, uow: Uow, principal: CurrentPrincipal) -> Response:
    await auth_service.revoke_session(uow, principal.uid, session_id)
    return Response(status_code=204)


@router.post("/step-up", dependencies=AuthLimited, response_model=StepUpResponse)
async def step_up(
    body: StepUpRequest, request: Request, uow: Uow, principal: CurrentPrincipal
) -> dict[str, Any]:
    token, exp = await auth_service.step_up(
        state_of(request),
        uow,
        user_id=principal.uid,
        session_id=principal.sid,
        hotel_id=principal.hotel_id,
        hotel_user_id=principal.hotel_user_id,
        pin=body.pin,
        password=body.password,
        client=_client(request),
    )
    return {"step_up_token": token, "expires_at": datetime.fromtimestamp(exp, UTC)}


@router.put("/pin", status_code=204)
async def set_pin(body: SetPinRequest, request: Request, uow: Uow, principal: StepUp) -> Response:
    if principal.hotel_user_id is None:
        raise AppError("PERMISSION_DENIED")
    await auth_service.set_pin(uow, principal.tenant(request), principal.hotel_user_id, body.pin)
    return Response(status_code=204)


@router.post("/password/forgot", dependencies=AuthLimited, status_code=202, response_model=AcceptedResponse)
async def forgot_password(body: ForgotPasswordRequest, request: Request, uow: Uow) -> dict[str, str]:
    await auth_service.forgot_password(state_of(request), uow, body.email)
    return {"status": "accepted"}


@router.post("/password/reset", dependencies=AuthLimited, status_code=204)
async def reset_password(body: ResetPasswordRequest, request: Request, uow: Uow) -> Response:
    await auth_service.reset_password(state_of(request), uow, body.token, body.new_password, _client(request))
    return Response(status_code=204)


@router.post("/email/verify", dependencies=AuthLimited, status_code=204)
async def verify_email(body: VerifyEmailRequest, uow: Uow) -> Response:
    await auth_service.verify_email(uow, body.token)
    return Response(status_code=204)


@router.post(
    "/invitations/{token}/accept",
    dependencies=AuthLimited,
    status_code=201,
    response_model=InvitationAcceptedResponse,
)
async def accept_invitation(
    idem: IdemAnon,
    token: str,
    body: AcceptInvitationRequest,
    request: Request,
    uow: Uow,
) -> JSONResponse:
    result = await invitations.accept_invitation(
        uow, token, name=body.name, password=body.password, pin=body.pin, client=_client(request)
    )
    return await idem.complete(uow, 201, result)
