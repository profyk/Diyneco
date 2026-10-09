"""/dev-storage: the local stand-in for Supabase Storage signed URLs. Mounted only when the
app runs with LocalStorage, which build_storage allows in development only.

A URL carries a 5-minute EdDSA-signed token naming one object and one operation; nothing
else is accepted, so these routes cannot list or reach another hotel's files.
"""

from __future__ import annotations

import mimetypes

from fastapi import APIRouter, Request, Response

from app.api.deps import state_of
from app.core.errors import AppError
from app.integrations.storage import LocalStorage

router = APIRouter(prefix="/dev-storage", tags=["dev-storage"], include_in_schema=False)


def _local(request: Request) -> LocalStorage:
    storage = state_of(request).storage
    if not isinstance(storage, LocalStorage):  # pragma: no cover - not mounted otherwise
        raise AppError("NOT_FOUND")
    return storage


@router.put("/{token}", status_code=204)
async def upload(token: str, request: Request) -> Response:
    storage = _local(request)
    claims = storage.jwt.verify(token, "storage", error_code="NOT_FOUND")
    if claims.get("op") != "put":
        raise AppError("NOT_FOUND")
    if request.headers.get("content-type", "").split(";")[0].strip() != claims.get("ct"):
        raise AppError("VALIDATION_FAILED", "The file type does not match the upload request.")
    body = await request.body()
    if len(body) > int(claims.get("max", 0)):
        raise AppError("VALIDATION_FAILED", "The file is too large.")
    path = storage.path_for(str(claims["sub"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return Response(status_code=204)


@router.get("/{token}")
async def download(token: str, request: Request) -> Response:
    storage = _local(request)
    claims = storage.jwt.verify(token, "storage", error_code="NOT_FOUND")
    if claims.get("op") != "get":
        raise AppError("NOT_FOUND")
    path = storage.path_for(str(claims["sub"]))
    if not path.is_file():
        raise AppError("NOT_FOUND")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return Response(
        path.read_bytes(),
        media_type=media_type,
        headers={
            "Cache-Control": "private, max-age=300",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
        },
    )
