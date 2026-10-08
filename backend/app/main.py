"""FastAPI app factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import reject_card_data, reject_unknown_query
from app.api.v1 import auth, health, hotel, rooms, staff
from app.core.config import Settings, get_settings
from app.core.crypto import LocalKms
from app.core.errors import install_error_handlers
from app.core.jwt import JwtKeys
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.ratelimit import build_rate_limiter
from app.core.state import AppState, Keyring
from app.db.session import Database
from app.notifications.email import ConsoleEmailProvider, EmailProvider, Mailer
from app.services.idempotency import IdempotentReplay, replay_response

API_PREFIX = "/api/v1"


def build_state(settings: Settings, email_provider: EmailProvider | None = None) -> AppState:
    db = Database(settings.database_url, "diyneco-api")
    if settings.kms_provider != "local":
        raise RuntimeError(f"KMS provider {settings.kms_provider!r} is not implemented yet")
    kms = LocalKms(settings.kms_local_master_key or "", settings.kms_master_key_id)
    if email_provider is None:
        if settings.email_provider != "console":
            raise RuntimeError(f"email provider {settings.email_provider!r} is not implemented yet")
        email_provider = ConsoleEmailProvider(echo=settings.is_development)
    return AppState(
        settings=settings,
        db=db,
        jwt=JwtKeys.from_config(
            settings.jwt_signing_keys_json, settings.jwt_active_kid, settings.api_base_url
        ),
        keyring=Keyring(kms=kms, db=db),
        limiter=build_rate_limiter(settings.redis_url),
        mailer=Mailer(provider=email_provider, sender=settings.email_from),
    )


def create_app(settings: Settings | None = None, state: AppState | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    app_state = state or build_state(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await app_state.db.dispose()

    app = FastAPI(
        title="Diyneco API",
        version="1.0.0",
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs" if settings.is_development else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.diyneco = app_state
    install_error_handlers(app)

    @app.exception_handler(IdempotentReplay)
    async def _replay(_: object, exc: IdempotentReplay):  # type: ignore[no-untyped-def]
        return replay_response(exc)

    api = APIRouter(
        prefix=API_PREFIX, dependencies=[Depends(reject_unknown_query), Depends(reject_card_data)]
    )
    api.include_router(health.router)
    api.include_router(auth.router)
    api.include_router(hotel.router)
    api.include_router(rooms.router)
    api.include_router(staff.router)
    app.include_router(api)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            "If-Match",
            "X-Step-Up",
            "X-Hotel-Id",
            "X-Request-Id",
        ],
        expose_headers=[
            "ETag",
            "X-Request-Id",
            "Idempotent-Replayed",
            "RateLimit-Limit",
            "RateLimit-Remaining",
            "RateLimit-Reset",
            "Retry-After",
        ],
    )
    app.add_middleware(RequestContextMiddleware, hsts=not settings.is_development)
    return app
