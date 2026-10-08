"""Small helpers shared by routers: ETag responses, If-Match, PATCH change sets."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.errors import AppError

IfMatch = Annotated[str | None, Header(alias="If-Match")]


def etag(version: int) -> str:
    return f'"{version}"'


def parse_if_match(header: str | None) -> int:
    """PATCH requires If-Match; missing or malformed counts as stale (DECISIONS D6)."""
    if not header:
        raise AppError("PRECONDITION_FAILED", "Send If-Match with the ETag you loaded.")
    tag = header.strip()
    if tag.startswith("W/"):
        tag = tag[2:]
    tag = tag.strip('"')
    if not tag.isdigit():
        raise AppError("PRECONDITION_FAILED")
    return int(tag)


def with_etag(
    body: dict[str, Any], version: int, model: type[BaseModel], status_code: int = 200
) -> JSONResponse:
    return JSONResponse(
        model.model_validate(body).model_dump(mode="json"),
        status_code=status_code,
        headers={"ETag": etag(version)},
    )


def patch_changes(patch: BaseModel, not_null: set[str]) -> dict[str, Any]:
    """Fields the client sent. Explicit null is refused for fields that cannot be empty."""
    changes: dict[str, Any] = patch.model_dump(exclude_unset=True)
    nulls = sorted(k for k, v in changes.items() if v is None and k in not_null)
    if nulls:
        raise AppError(
            "VALIDATION_FAILED",
            details={"fields": [{"field": f, "problem": "Cannot be empty.", "type": "null"} for f in nulls]},
        )
    return changes
