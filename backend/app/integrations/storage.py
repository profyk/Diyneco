"""Object storage behind one interface (security spec, Data protection and Tenant isolation).

Keys are always `hotels/{hotel_id}/...` and are built here from the tenant context, never
from client input. Buckets are private: clients upload and download through signed URLs
minted after a tenant check, valid for 5 minutes.

- `supabase`: Supabase Storage through its REST API with the service-role key, which lives
  only in the backend.
- `local`: development only. Files go under backend/.storage and the signed URLs point at
  the API's /dev-storage routes, signed with the API's own EdDSA keys.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol
from urllib.parse import quote

import httpx

from app.core.config import Settings
from app.core.errors import AppError
from app.core.jwt import JwtKeys

SIGNED_URL_TTL = timedelta(minutes=5)
LOCAL_ROOT = Path(__file__).resolve().parents[2] / ".storage"


@dataclass(frozen=True)
class SignedUpload:
    url: str
    method: str
    headers: dict[str, str]
    expires_at: datetime


class Storage(Protocol):
    async def signed_upload(
        self, bucket: str, key: str, content_type: str, max_bytes: int
    ) -> SignedUpload: ...
    async def signed_download(self, bucket: str, key: str) -> str: ...
    async def signed_downloads(self, bucket: str, keys: list[str]) -> dict[str, str]: ...
    async def put(self, bucket: str, key: str, data: bytes, content_type: str) -> None: ...
    async def get(self, bucket: str, key: str) -> bytes: ...


def hotel_key(hotel_id: uuid.UUID, *parts: str) -> str:
    for p in parts:
        if not p or "/" in p or p in (".", "..") or "\\" in p:
            raise ValueError("invalid storage key part")
    return "/".join(("hotels", str(hotel_id), *parts))


class SupabaseStorage:
    def __init__(self, url: str, service_key: str, client: httpx.AsyncClient | None = None) -> None:
        self.base = url.rstrip("/") + "/storage/v1"
        self.headers = {"Authorization": f"Bearer {service_key}", "apikey": service_key}
        self.client = client or httpx.AsyncClient(timeout=10)

    async def signed_upload(self, bucket: str, key: str, content_type: str, max_bytes: int) -> SignedUpload:
        r = await self.client.post(
            f"{self.base}/object/upload/sign/{bucket}/{quote(key)}", headers=self.headers, json={}
        )
        if r.status_code >= 300:
            raise AppError("SERVICE_UNAVAILABLE", "File storage is unavailable. Try again shortly.")
        return SignedUpload(
            url=f"{self.base}{r.json()['url']}",
            method="PUT",
            headers={"Content-Type": content_type, "x-upsert": "true"},
            expires_at=datetime.now(UTC) + timedelta(hours=2),  # Supabase's fixed upload-URL lifetime
        )

    async def signed_download(self, bucket: str, key: str) -> str:
        r = await self.client.post(
            f"{self.base}/object/sign/{bucket}/{quote(key)}",
            headers=self.headers,
            json={"expiresIn": int(SIGNED_URL_TTL.total_seconds())},
        )
        if r.status_code >= 300:
            raise AppError("SERVICE_UNAVAILABLE", "File storage is unavailable. Try again shortly.")
        return f"{self.base}{r.json()['signedURL']}"

    async def signed_downloads(self, bucket: str, keys: list[str]) -> dict[str, str]:
        if not keys:
            return {}
        r = await self.client.post(
            f"{self.base}/object/sign/{bucket}",
            headers=self.headers,
            json={"expiresIn": int(SIGNED_URL_TTL.total_seconds()), "paths": keys},
        )
        if r.status_code >= 300:
            raise AppError("SERVICE_UNAVAILABLE", "File storage is unavailable. Try again shortly.")
        return {row["path"]: f"{self.base}{row['signedURL']}" for row in r.json() if row.get("signedURL")}

    async def put(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        """Server-side upload of a document the API generated. Never overwrites."""
        r = await self.client.post(
            f"{self.base}/object/{bucket}/{quote(key)}",
            headers={**self.headers, "Content-Type": content_type, "x-upsert": "false"},
            content=data,
        )
        if r.status_code >= 300:
            raise AppError("SERVICE_UNAVAILABLE", "File storage is unavailable. Try again shortly.")

    async def get(self, bucket: str, key: str) -> bytes:
        r = await self.client.get(
            f"{self.base}/object/authenticated/{bucket}/{quote(key)}", headers=self.headers
        )
        if r.status_code >= 300:
            raise AppError("SERVICE_UNAVAILABLE", "File storage is unavailable. Try again shortly.")
        return r.content


class LocalStorage:
    """Development only (refused elsewhere by build_storage)."""

    def __init__(self, api_base_url: str, jwt: JwtKeys, root: Path = LOCAL_ROOT) -> None:
        self.base = api_base_url.rstrip("/") + "/api/v1/dev-storage"
        self.jwt = jwt
        self.root = root

    def _token(self, op: str, bucket: str, key: str, **extra: object) -> str:
        token, _ = self.jwt.sign(
            "storage", {"sub": f"{bucket}/{key}", "op": op, **extra}, int(SIGNED_URL_TTL.total_seconds())
        )
        return token

    async def signed_upload(self, bucket: str, key: str, content_type: str, max_bytes: int) -> SignedUpload:
        token = self._token("put", bucket, key, ct=content_type, max=max_bytes)
        return SignedUpload(
            url=f"{self.base}/{token}",
            method="PUT",
            headers={"Content-Type": content_type},
            expires_at=datetime.now(UTC) + SIGNED_URL_TTL,
        )

    async def signed_download(self, bucket: str, key: str) -> str:
        return f"{self.base}/{self._token('get', bucket, key)}"

    async def signed_downloads(self, bucket: str, keys: list[str]) -> dict[str, str]:
        return {k: await self.signed_download(bucket, k) for k in keys}

    async def put(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        path = self.path_for(f"{bucket}/{key}")
        if path.exists():
            raise RuntimeError("storage object already exists")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def get(self, bucket: str, key: str) -> bytes:
        path = self.path_for(f"{bucket}/{key}")
        if not path.is_file():
            raise AppError("NOT_FOUND")
        return path.read_bytes()

    def path_for(self, object_name: str) -> Path:
        path = (self.root / object_name).resolve()
        if self.root.resolve() not in path.parents:
            raise AppError("NOT_FOUND")
        return path


def build_storage(settings: Settings, jwt: JwtKeys) -> Storage:
    if (
        settings.supabase_url
        and settings.supabase_service_role_key
        and "YOUR-PROJECT" not in settings.supabase_url
    ):
        return SupabaseStorage(settings.supabase_url, settings.supabase_service_role_key)
    if not settings.is_development:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required outside development")
    return LocalStorage(settings.api_base_url, jwt)
