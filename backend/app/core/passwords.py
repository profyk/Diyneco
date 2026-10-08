"""Password and PIN rules (security spec): passwords at least 12 characters and not on a
breached or common-password list, no composition rules; PINs 4 to 6 digits.

The list in data/common_passwords.txt holds the 12+ character entries of the NCSC top
100,000 list from SecLists (MIT licence), lower-cased (DECISIONS G16)."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from app.core.errors import AppError

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 256
_PIN = re.compile(r"^\d{4,6}$")


@lru_cache
def _common_passwords() -> frozenset[str]:
    path = Path(__file__).parent / "data" / "common_passwords.txt"
    return frozenset(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def check_password(password: str, *, email: str | None = None, field: str = "password") -> None:
    problem: str | None = None
    if len(password) < MIN_PASSWORD_LENGTH:
        problem = f"Use at least {MIN_PASSWORD_LENGTH} characters."
    elif len(password) > MAX_PASSWORD_LENGTH:
        problem = f"Use at most {MAX_PASSWORD_LENGTH} characters."
    elif password.lower() in _common_passwords():
        problem = "This password is too common. Choose another."
    elif email and password.lower() == email.lower():
        problem = "The password cannot be your email address."
    if problem:
        raise AppError(
            "VALIDATION_FAILED",
            "Choose a stronger password.",
            details={"fields": [{"field": field, "problem": problem, "type": "password_policy"}]},
        )


def check_pin(pin: str, field: str = "pin") -> None:
    if not _PIN.match(pin):
        raise AppError(
            "VALIDATION_FAILED",
            "A PIN is 4 to 6 digits.",
            details={"fields": [{"field": field, "problem": "Use 4 to 6 digits.", "type": "pin_policy"}]},
        )
