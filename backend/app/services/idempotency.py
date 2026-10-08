"""Idempotency-Key handling (API spec, Conventions; DECISIONS G12, G13).

- Same key + same request within 24 h: the stored status and body, with
  `Idempotent-Replayed: true`.
- Same key + different request: 409 IDEMPOTENCY_CONFLICT.
- Same key while the first request is still running: 409 IDEMPOTENCY_IN_PROGRESS.
- A claim older than 60 s that never completed is treated as abandoned and retaken.
- 2xx and 4xx outcomes are stored; 5xx releases the key so the client can retry it.

The claim is written and committed in its own short transaction, so concurrent requests see
it at once. Completion is written inside the request's own transaction, so the stored
response commits atomically with the change it describes.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import AppError, error_body
from app.db.session import UnitOfWork
from app.models.events import IdempotencyKey

ABANDONED_AFTER = timedelta(seconds=60)
REPLAY_HEADER = "Idempotent-Replayed"


class IdempotentReplay(Exception):
    """Raised to short-circuit a request with the stored response."""

    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self.body = body


def replay_response(exc: IdempotentReplay) -> JSONResponse:
    return JSONResponse(exc.body, status_code=exc.status_code, headers={REPLAY_HEADER: "true"})


def request_fingerprint(method: str, path: str, body: bytes) -> bytes:
    try:
        canonical = json.dumps(json.loads(body), sort_keys=True, separators=(",", ":")) if body else ""
    except ValueError:
        canonical = body.decode("utf-8", "replace")
    return hashlib.sha256(f"{method}\n{path}\n{canonical}".encode()).digest()


def parse_key(request: Request) -> uuid.UUID:
    raw = request.headers.get("idempotency-key")
    try:
        return uuid.UUID(raw or "")
    except ValueError as exc:
        raise AppError(
            "VALIDATION_FAILED",
            "Idempotency-Key header with a UUID is required.",
            details={
                "fields": [
                    {"field": "Idempotency-Key", "problem": "Required UUID header.", "type": "missing"}
                ]
            },
        ) from exc


@dataclass
class IdempotencyClaim:
    principal_key: str
    key: uuid.UUID
    sessionmaker: async_sessionmaker[AsyncSession]

    async def complete(self, uow: UnitOfWork, status_code: int, body: Any) -> JSONResponse:
        """Store the response in the request's transaction and return it."""
        encoded = jsonable_encoder(body)
        await uow.session.execute(
            update(IdempotencyKey)
            .where(IdempotencyKey.principal_key == self.principal_key, IdempotencyKey.key == self.key)
            .values(status="completed", response_code=status_code, response_body=encoded)
        )
        return JSONResponse(encoded, status_code=status_code)

    async def fail(self, err: BaseException) -> None:
        """After the request's transaction rolled back: keep a 4xx outcome, release on 5xx."""
        async with self.sessionmaker() as s, s.begin():
            where = (
                IdempotencyKey.principal_key == self.principal_key,
                IdempotencyKey.key == self.key,
                IdempotencyKey.status == "in_progress",
            )
            if isinstance(err, AppError) and err.status < 500:
                await s.execute(
                    update(IdempotencyKey)
                    .where(*where)
                    .values(
                        status="completed",
                        response_code=err.status,
                        response_body=error_body(err.code, err.message, err.details),
                    )
                )
            else:
                await s.execute(delete(IdempotencyKey).where(*where))


async def claim(
    sessionmaker: async_sessionmaker[AsyncSession],
    principal_key: str,
    key: uuid.UUID,
    method: str,
    path: str,
    fingerprint: bytes,
) -> IdempotencyClaim:
    now = datetime.now(UTC)
    async with sessionmaker() as s, s.begin():
        inserted = (
            await s.execute(
                pg_insert(IdempotencyKey)
                .values(
                    principal_key=principal_key,
                    key=key,
                    method=method,
                    path=path,
                    request_hash=fingerprint,
                    status="in_progress",
                )
                .on_conflict_do_nothing(index_elements=["principal_key", "key"])
                .returning(IdempotencyKey.key)
            )
        ).first()
        if inserted is None:
            row = (
                await s.execute(
                    select(IdempotencyKey)
                    .where(IdempotencyKey.principal_key == principal_key, IdempotencyKey.key == key)
                    .with_for_update()
                )
            ).scalar_one()
            expired = row.expires_at <= now
            abandoned = row.status == "in_progress" and row.created_at <= now - ABANDONED_AFTER
            if expired or abandoned:
                if not expired and (row.request_hash != fingerprint):
                    raise AppError(
                        "IDEMPOTENCY_CONFLICT", "This Idempotency-Key was used for a different request."
                    )
                await s.execute(
                    update(IdempotencyKey)
                    .where(IdempotencyKey.principal_key == principal_key, IdempotencyKey.key == key)
                    .values(
                        method=method,
                        path=path,
                        request_hash=fingerprint,
                        status="in_progress",
                        response_code=None,
                        response_body=None,
                        created_at=now,
                        expires_at=now + timedelta(hours=24),
                    )
                )
            elif row.request_hash != fingerprint:
                raise AppError(
                    "IDEMPOTENCY_CONFLICT", "This Idempotency-Key was used for a different request."
                )
            elif row.status == "completed":
                raise IdempotentReplay(int(row.response_code or 200), row.response_body)
            else:
                raise AppError("IDEMPOTENCY_IN_PROGRESS", "This request is still being processed.")
    return IdempotencyClaim(principal_key, key, sessionmaker)
