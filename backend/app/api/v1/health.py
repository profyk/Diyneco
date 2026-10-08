"""Liveness and readiness for the load balancer. No principal, no tenant data."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.deps import state_of

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> JSONResponse:
    db_ok = await state_of(request).ping_db()
    return JSONResponse(
        {"status": "ok" if db_ok else "degraded", "database": "ok" if db_ok else "unavailable"},
        status_code=200 if db_ok else 503,
    )
