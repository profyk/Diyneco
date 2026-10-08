"""Role-based access rules that hold no matter which endpoint asks."""

from __future__ import annotations

from collections.abc import Iterable

from app.core.errors import AppError
from app.core.logging import security_event


def assert_can_grant(granter_permissions: Iterable[str], requested: Iterable[str]) -> None:
    """A user can never grant a permission they do not hold themselves (security spec, hard
    limits). Used by custom-role creation and editing and by role assignment (Phase 2)."""
    missing = sorted(set(requested) - set(granter_permissions))
    if missing:
        security_event("rbac.grant_denied", missing=missing)
        raise AppError(
            "PERMISSION_DENIED",
            "You cannot grant permissions you do not hold.",
            details={"missing_permissions": missing},
        )
