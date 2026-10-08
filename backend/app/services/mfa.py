"""TOTP (RFC 6238): 160-bit secret, 30-second step, ±1 step drift, last used step stored
to block replay; 10 one-time recovery codes stored as SHA-256 hashes."""

from __future__ import annotations

import hmac
import secrets
import time

import pyotp

from app.core.crypto import sha256

STEP_S = 30
DRIFT_STEPS = 1
RECOVERY_CODE_COUNT = 10
_RECOVERY_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"


def new_secret() -> str:
    return pyotp.random_base32(length=32)  # 32 base32 chars = 160 bits


def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret, interval=STEP_S).provisioning_uri(name=email, issuer_name="Diyneco")


def current_step(at: float | None = None) -> int:
    return int((at if at is not None else time.time()) // STEP_S)


def code_at_step(secret: str, step: int) -> str:
    return str(pyotp.TOTP(secret, interval=STEP_S).generate_otp(step))


def verify_code(secret: str, code: str, last_used_step: int | None, at: float | None = None) -> int | None:
    """Return the matched step, or None. A step at or before last_used_step never matches,
    so a code cannot be used twice."""
    code = code.strip().replace(" ", "")
    if not (len(code) == 6 and code.isdigit()):
        return None
    now = current_step(at)
    for step in range(now - DRIFT_STEPS, now + DRIFT_STEPS + 1):
        if last_used_step is not None and step <= last_used_step:
            continue
        if hmac.compare_digest(code_at_step(secret, step), code):
            return step
    return None


def new_recovery_codes() -> list[str]:
    codes = []
    for _ in range(RECOVERY_CODE_COUNT):
        raw = "".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(10))
        codes.append(f"{raw[:5]}-{raw[5:]}")
    return codes


def recovery_hash(code: str) -> bytes:
    return sha256("recovery:" + code.strip().lower().replace(" ", ""))
