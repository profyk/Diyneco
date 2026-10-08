"""Error envelope and exception handlers.

Every non-2xx body is {"error": {"code", "message", "request_id", "details"}} with a code
from the API spec's catalogue. Stack traces and SQL never reach the client.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import request_id_var, security_event

log = logging.getLogger("diyneco.errors")

# HTTP status for every code in the API spec's catalogue.
ERROR_STATUS: dict[str, int] = {
    "VALIDATION_FAILED": 400,
    "AMOUNT_INVALID": 400,
    "CARD_DATA_REJECTED": 400,
    "UNAUTHENTICATED": 401,
    "MFA_REQUIRED": 401,
    "DEVICE_UNAUTHORISED": 401,
    "PERMISSION_DENIED": 403,
    "STEP_UP_REQUIRED": 403,
    "PIN_INVALID": 403,
    "DEVICE_DISABLED": 403,
    "HOTEL_SUSPENDED": 403,
    "SELF_APPROVAL": 403,
    "NOT_FOUND": 404,
    "INVALID_TRANSITION": 409,
    "IDEMPOTENCY_CONFLICT": 409,
    "IDEMPOTENCY_IN_PROGRESS": 409,
    "ALREADY_CLAIMED": 409,
    "ALREADY_PAID": 409,
    "PRICE_CHANGED": 409,
    "TIP_CONFIRMATION_REQUIRED": 409,
    "OPEN_ORDERS": 409,
    "OUTSTANDING_BALANCE": 409,
    "ROOM_NOT_AVAILABLE": 409,
    "ROOM_OCCUPIED": 409,
    "PRECONDITION_FAILED": 412,
    "NO_ACTIVE_STAY": 422,
    "ROOM_CHARGE_DISABLED": 422,
    "STAY_BLOCKED": 422,
    "ITEM_UNAVAILABLE": 422,
    "ORDER_TOO_LARGE": 422,
    "OVERRIDE_NOT_ALLOWED": 422,
    "REASON_REQUIRED": 422,
    "PAIRING_INVALID": 422,
    "PLAN_LIMIT_REACHED": 422,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503,
}

DEFAULT_MESSAGES: dict[str, str] = {
    "VALIDATION_FAILED": "The request is not valid.",
    "UNAUTHENTICATED": "Please sign in again.",
    "MFA_REQUIRED": "A second sign-in factor is required.",
    "PERMISSION_DENIED": "You do not have permission to do this.",
    "STEP_UP_REQUIRED": "Confirm with your PIN or password to continue.",
    "NOT_FOUND": "Not found.",
    "RATE_LIMITED": "Too many requests. Try again shortly.",
    "INTERNAL_ERROR": "Something went wrong. Please try again.",
    "INVALID_TRANSITION": "That change is not allowed from the current state.",
    "PRECONDITION_FAILED": "This record changed since you loaded it. Reload and try again.",
    "CARD_DATA_REJECTED": "Card details must never be entered here.",
}


class AppError(Exception):
    """A failure the client is allowed to see. `code` must be in ERROR_STATUS."""

    def __init__(
        self,
        code: str,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        if code not in ERROR_STATUS:
            raise ValueError(f"unknown error code {code}")
        self.code = code
        self.status = ERROR_STATUS[code]
        self.message = message or DEFAULT_MESSAGES.get(code, code.replace("_", " ").capitalize() + ".")
        self.details = details or {}
        self.headers = headers
        super().__init__(f"{code}: {self.message}")


def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id_var.get(),
            "details": details or {},
        }
    }


def error_response(err: AppError) -> JSONResponse:
    return JSONResponse(
        error_body(err.code, err.message, err.details), status_code=err.status, headers=err.headers
    )


# SQLSTATEs raised by our own triggers (database spec). The API should have stopped these
# writes first, so each one is also a security event.
SQLSTATE_MAP: dict[str, tuple[str, str]] = {
    "P0001": ("INTERNAL_ERROR", "db.append_only_violation"),
    "P0002": ("INVALID_TRANSITION", "db.closed_folio_write"),
    "P0003": ("INTERNAL_ERROR", "db.locked_order_change"),
    "P0004": ("INVALID_TRANSITION", "db.invalid_order_transition"),
    "42501": ("INTERNAL_ERROR", "db.privilege_or_rls_violation"),
}


def sqlstate_of(exc: DBAPIError) -> str | None:
    orig = getattr(exc, "orig", None)
    for attr in ("sqlstate", "pgcode"):
        value = getattr(orig, attr, None)
        if isinstance(value, str):
            return value
    cause = getattr(orig, "__cause__", None)
    value = getattr(cause, "sqlstate", None)
    return value if isinstance(value, str) else None


def app_error_from_db(exc: DBAPIError) -> AppError:
    state = sqlstate_of(exc)
    if state in SQLSTATE_MAP:
        code, event = SQLSTATE_MAP[state]
        security_event(event, sqlstate=state)
        return AppError(code)
    log.error("database error", extra={"sqlstate": state, "error_type": type(exc.orig).__name__})
    return AppError("INTERNAL_ERROR")


def _validation_details(exc: RequestValidationError) -> dict[str, Any]:
    fields = []
    for e in exc.errors():
        loc = [str(p) for p in e.get("loc", ()) if p not in ("body",)]
        fields.append({"field": ".".join(loc), "problem": e.get("msg", "invalid"), "type": e.get("type")})
    return {"fields": fields}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return error_response(exc)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(AppError("VALIDATION_FAILED", details=_validation_details(exc)))

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return error_response(AppError("NOT_FOUND"))
        if exc.status_code == 405:
            return error_response(AppError("NOT_FOUND"))
        log.warning("unexpected http exception", extra={"status": exc.status_code})
        return error_response(AppError("INTERNAL_ERROR"))

    @app.exception_handler(DBAPIError)
    async def _db(_: Request, exc: DBAPIError) -> JSONResponse:
        return error_response(app_error_from_db(exc))

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error", exc_info=exc)
        return error_response(AppError("INTERNAL_ERROR"))
