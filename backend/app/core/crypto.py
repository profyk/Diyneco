"""Hashing, random tokens and envelope encryption.

Passwords and PINs: Argon2id, 64 MiB, 3 iterations, parallelism 1, 16-byte salt (security
spec). Tokens, device credentials, pairing codes and API keys: SHA-256, because they are
already high-entropy or protected by expiry and lockout.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import os
import re
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ARGON2_PARAMS: dict[str, int] = {
    "time_cost": 3,
    "memory_cost": 64 * 1024,
    "parallelism": 1,
    "salt_len": 16,
    "hash_len": 32,
}


def _build_hasher(p: dict[str, int]) -> PasswordHasher:
    return PasswordHasher(
        time_cost=p["time_cost"],
        memory_cost=p["memory_cost"],
        parallelism=p["parallelism"],
        salt_len=p["salt_len"],
        hash_len=p["hash_len"],
    )


_hasher = _build_hasher(ARGON2_PARAMS)
# A fixed hash verified when an account does not exist, so response time does not reveal it.
_dummy_hash: str | None = None


def set_hash_params(**params: int) -> None:
    """Tests lower the cost to keep the suite fast. Never called by application code."""
    global _hasher, _dummy_hash  # noqa: PLW0603 - test-only switch
    _hasher = _build_hasher({**ARGON2_PARAMS, **params})
    _dummy_hash = None


def hash_secret(secret: str) -> str:
    return _hasher.hash(secret)


def verify_secret(stored_hash: str | None, secret: str) -> bool:
    """Constant-work check. A missing hash still costs one Argon2 verification."""
    global _dummy_hash  # noqa: PLW0603 - lazily built constant
    if stored_hash is None:
        if _dummy_hash is None:
            _dummy_hash = _hasher.hash(secrets.token_urlsafe(16))
        stored_hash = _dummy_hash
        with contextlib.suppress(VerificationError, InvalidHashError):
            _hasher.verify(stored_hash, secret)
        return False
    try:
        return _hasher.verify(stored_hash, secret)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    return _hasher.check_needs_rehash(stored_hash)


def sha256(value: str | bytes) -> bytes:
    data = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(data).digest()


def random_token(prefix: str = "", nbytes: int = 32) -> str:
    """256-bit random token, URL-safe."""
    return prefix + secrets.token_urlsafe(nbytes)


def constant_time_equal(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)


# --- Card data (PCI scope) -----------------------------------------------------------------

_CARD_CANDIDATE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
CARD_FIELD_NAMES = {
    "cvv",
    "cvc",
    "cvv2",
    "card_number",
    "cardnumber",
    "pan",
    "track",
    "track_data",
    "track1",
    "track2",
    "card_pin",
}


def luhn_valid(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def looks_like_card_number(text: str) -> bool:
    for match in _CARD_CANDIDATE.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if 13 <= len(digits) <= 19 and luhn_valid(digits):
            return True
    return False


# --- Envelope encryption -------------------------------------------------------------------

_FORMAT_V1 = b"\x01"


class LocalKms:
    """Wraps data keys with a master key held in configuration. Development and CI only;
    production uses a cloud KMS behind the same two methods (DECISIONS G9)."""

    def __init__(self, master_key_b64: str, key_id: str) -> None:
        self._master = AESGCM(base64.b64decode(master_key_b64))
        self.key_id = key_id

    def wrap(self, data_key: bytes, scope: str) -> bytes:
        nonce = os.urandom(12)
        return _FORMAT_V1 + nonce + self._master.encrypt(nonce, data_key, scope.encode())

    def unwrap(self, wrapped: bytes, scope: str) -> bytes:
        if wrapped[:1] != _FORMAT_V1:
            raise ValueError("unknown wrapped key format")
        return self._master.decrypt(wrapped[1:13], wrapped[13:], scope.encode())


def new_data_key() -> bytes:
    return AESGCM.generate_key(bit_length=256)


def encrypt_field(data_key: bytes, plaintext: bytes, context: str) -> bytes:
    """AES-256-GCM. `context` (e.g. 'mfa:<user_id>') is bound as associated data so a
    ciphertext copied to another row fails to decrypt."""
    nonce = os.urandom(12)
    return _FORMAT_V1 + nonce + AESGCM(data_key).encrypt(nonce, plaintext, context.encode())


def decrypt_field(data_key: bytes, ciphertext: bytes, context: str) -> bytes:
    if ciphertext[:1] != _FORMAT_V1:
        raise ValueError("unknown ciphertext format")
    return AESGCM(data_key).decrypt(ciphertext[1:13], ciphertext[13:], context.encode())
