"""Authentication request and response bodies."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, StringConstraints, model_validator

from app.schemas.common import Name, StrictModel

Password = Annotated[str, StringConstraints(min_length=1, max_length=256, strip_whitespace=False)]
Code = Annotated[str, StringConstraints(min_length=6, max_length=8)]
Pin = Annotated[str, StringConstraints(min_length=4, max_length=6, pattern=r"^\d+$")]
Token = Annotated[str, StringConstraints(min_length=16, max_length=200)]


class LoginRequest(StrictModel):
    email: EmailStr
    password: Password
    hotel_id: uuid.UUID | None = None  # pick one of the caller's hotels (DECISIONS G11)


class MfaVerifyRequest(StrictModel):
    mfa_token: str | None = None
    code: Code | None = None
    recovery_code: Annotated[str, StringConstraints(max_length=20)] | None = None

    @model_validator(mode="after")
    def _one_factor(self) -> MfaVerifyRequest:
        if (self.code is None) == (self.recovery_code is None):
            raise ValueError("send exactly one of code or recovery_code")
        return self


class RefreshRequest(StrictModel):
    refresh_token: str | None = None  # mobile; web sends the cookie instead
    hotel_id: uuid.UUID | None = None  # switch active hotel (DECISIONS G11)


class StepUpRequest(StrictModel):
    pin: Pin | None = None
    password: Password | None = None

    @model_validator(mode="after")
    def _one_credential(self) -> StepUpRequest:
        if (self.pin is None) == (self.password is None):
            raise ValueError("send exactly one of pin or password")
        return self


class SetPinRequest(StrictModel):
    pin: Pin


class ForgotPasswordRequest(StrictModel):
    email: EmailStr


class ResetPasswordRequest(StrictModel):
    token: Token
    new_password: Password


class VerifyEmailRequest(StrictModel):
    token: Token


class AcceptInvitationRequest(StrictModel):
    name: Name
    password: Password
    pin: Pin


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    email_verified: bool


class HotelMembershipOut(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    roles: list[str]


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int
    refresh_token: str | None = None  # omitted for web clients, which get an httpOnly cookie
    mfa_enrolment_required: bool = False
    user: UserOut
    hotels: list[HotelMembershipOut]


class MfaChallengeResponse(BaseModel):
    mfa_required: Literal[True] = True
    mfa_token: str


class MfaEnrollResponse(BaseModel):
    secret: str
    otpauth_uri: str


class MfaConfirmResponse(TokenResponse):
    recovery_codes: list[str]


class StepUpResponse(BaseModel):
    step_up_token: str
    expires_at: datetime


class SessionOut(BaseModel):
    id: uuid.UUID
    user_agent: str | None
    ip: str | None
    created_at: datetime
    last_used_at: datetime
    current: bool


class SessionList(BaseModel):
    data: list[SessionOut]
    next_cursor: str | None = None


class AcceptedResponse(BaseModel):
    status: str


class InvitationAcceptedResponse(BaseModel):
    status: str
    hotel_id: uuid.UUID
    user_id: uuid.UUID
