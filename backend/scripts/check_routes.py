"""Fail if a hotel-scoped route accepts a hotel id as input (security spec, Tenant isolation:
"Static check fails CI if a router function takes hotel_id as input").

The hotel comes from the principal. The only exceptions are the two auth routes where a
signed-in user picks which of their own memberships to use (the server checks membership),
and the platform admin router (/admin), which only platform tokens can call and where a
hotel is the object being administered, not the caller's tenant.

    uv run python scripts/check_routes.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PLATFORM_PREFIX = "/api/v1/admin/"
FORBIDDEN = {"hotel_id", "hid", "hotelid", "hotel"}
ALLOWED = {
    ("POST", "/api/v1/auth/login"): {"hotel_id"},
    ("POST", "/api/v1/auth/refresh"): {"hotel_id"},
    ("POST", "/api/v1/signup"): {"hotel"},  # the hotel being created, not a reference
}


def _schema_props(spec: dict[str, Any], schema: dict[str, Any]) -> set[str]:
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[-1]
        schema = spec["components"]["schemas"][name]
    props = set(schema.get("properties", {}))
    for key in ("anyOf", "oneOf", "allOf"):
        for sub in schema.get(key, []):
            props |= _schema_props(spec, sub)
    return props


def check(spec: dict[str, Any]) -> list[str]:
    problems = []
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            names = {p["name"].lower() for p in op.get("parameters", [])}
            body = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
            if body:
                names |= {n.lower() for n in _schema_props(spec, body)}
            names |= {seg.strip("{}").lower() for seg in path.split("/") if seg.startswith("{")}
            if path.startswith(PLATFORM_PREFIX):
                continue
            bad = (names & FORBIDDEN) - ALLOWED.get((method.upper(), path), set())
            if bad:
                problems.append(f"{method.upper()} {path} accepts {sorted(bad)}")
    return problems


def main() -> int:
    os.environ.setdefault("APP_ENV", "development")
    from app.main import create_app

    problems = check(create_app().openapi())
    if problems:
        print("Route check FAILED:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("Route check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
