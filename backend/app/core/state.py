"""Process-wide services, built once in the app factory and stored on app.state.diyneco."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import Settings
from app.core.crypto import LocalKms, decrypt_field, encrypt_field, new_data_key
from app.core.jwt import JwtKeys
from app.core.ratelimit import RateLimiter
from app.db.session import Database
from app.models.tenancy import DataKey
from app.notifications.email import Mailer


@dataclass
class Keyring:
    """Per-scope data keys ('platform' for user MFA secrets, a hotel id for guest data),
    wrapped by the KMS master key and stored in app.data_keys. A new key is committed in its
    own short transaction before first use, so a key is never cached that the database
    does not hold."""

    kms: LocalKms
    db: Database
    _cache: dict[str, bytes] = field(default_factory=dict)

    async def data_key(self, scope: str) -> bytes:
        if scope in self._cache:
            return self._cache[scope]
        async with self.db.sessionmaker() as s, s.begin():
            await s.execute(
                pg_insert(DataKey)
                .values(
                    scope=scope, wrapped_key=self.kms.wrap(new_data_key(), scope), kms_key_id=self.kms.key_id
                )
                .on_conflict_do_nothing(index_elements=["scope"])
            )
            wrapped = (
                await s.execute(select(DataKey.wrapped_key).where(DataKey.scope == scope))
            ).scalar_one()
        key = self.kms.unwrap(wrapped, scope)
        self._cache[scope] = key
        return key

    async def encrypt(self, scope: str, plaintext: bytes, context: str) -> bytes:
        return encrypt_field(await self.data_key(scope), plaintext, context)

    async def decrypt(self, scope: str, ciphertext: bytes, context: str) -> bytes:
        return decrypt_field(await self.data_key(scope), ciphertext, context)


@dataclass
class AppState:
    settings: Settings
    db: Database
    jwt: JwtKeys
    keyring: Keyring
    limiter: RateLimiter
    mailer: Mailer

    async def ping_db(self) -> bool:
        try:
            async with self.db.sessionmaker() as s:
                await s.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
