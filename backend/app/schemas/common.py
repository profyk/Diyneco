"""Shared schema pieces. Request models forbid unknown fields, so a client cannot slip in a
price, total or hotel id that the server would ignore silently."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Money(StrictModel):
    amount_minor: Annotated[int, Field(ge=0, le=10**12, strict=True)]
    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None
    details: dict[str, object]


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


Name = Annotated[str, StringConstraints(min_length=1, max_length=120)]
ShortText = Annotated[str, StringConstraints(max_length=200)]
