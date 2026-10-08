"""Opaque keyset cursors (API spec, Conventions: `?limit=50&cursor=<opaque>`, max 200).

A cursor is the sort key of the last row returned, base64url-encoded JSON. It carries no
hotel id and grants nothing: the next page is still filtered by the caller's tenant.
"""

from __future__ import annotations

import base64
import json
from typing import Annotated, Any

from fastapi import Query

from app.core.errors import AppError

DEFAULT_LIMIT = 50
MAX_LIMIT = 200

Limit = Annotated[int, Query(ge=1, le=MAX_LIMIT)]
Cursor = Annotated[str | None, Query(max_length=512)]


def encode_cursor(values: list[Any]) -> str:
    raw = json.dumps(values, separators=(",", ":"), default=str).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str | None, size: int) -> list[Any] | None:
    if cursor is None:
        return None
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        values = json.loads(base64.urlsafe_b64decode(padded.encode()))
    except (ValueError, TypeError) as exc:
        raise _bad() from exc
    if not isinstance(values, list) or len(values) != size:
        raise _bad()
    return values


def _bad() -> AppError:
    return AppError(
        "VALIDATION_FAILED",
        "Invalid cursor.",
        details={"fields": [{"field": "cursor", "problem": "Invalid cursor.", "type": "value_error"}]},
    )


def page(rows: list[Any], limit: int, key: Any) -> tuple[list[Any], str | None]:
    """`rows` was fetched with limit + 1; returns the page and the next cursor."""
    if len(rows) <= limit:
        return rows, None
    rows = rows[:limit]
    return rows, encode_cursor(key(rows[-1]))
