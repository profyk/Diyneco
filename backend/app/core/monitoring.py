"""Error monitoring (build spec section 77; security spec, Logging).

Sentry is enabled only when SENTRY_DSN is set. No personal data leaves the process: request
bodies, cookies, query strings and credential headers are dropped, users are identified by
id only, and breadcrumbs from SQL are removed (they could carry parameters).
"""

from __future__ import annotations

from typing import Any

import sentry_sdk

from app.core.config import Settings

SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key", "x-step-up", "x-device-credential"}


def scrub(event: dict[str, Any], _hint: dict[str, Any] | None = None) -> dict[str, Any]:
    request = event.get("request") or {}
    request.pop("data", None)
    request.pop("cookies", None)
    request.pop("query_string", None)
    headers = request.get("headers") or {}
    for name in list(headers):
        if name.lower() in SENSITIVE_HEADERS:
            headers[name] = "[removed]"
    user = event.get("user") or {}
    event["user"] = {"id": user["id"]} if user.get("id") else {}
    crumbs = (event.get("breadcrumbs") or {}).get("values")
    if isinstance(crumbs, list):
        event["breadcrumbs"]["values"] = [c for c in crumbs if c.get("category") not in ("query", "sql")]
    return event


def init_monitoring(settings: Settings, component: str) -> bool:
    if not settings.sentry_dsn:
        return False
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        release=settings.release or None,
        server_name=component,
        send_default_pii=False,
        max_request_body_size="never",
        traces_sample_rate=settings.sentry_traces_sample_rate,
        before_send=scrub,  # type: ignore[arg-type]
        before_send_transaction=scrub,  # type: ignore[arg-type]
    )
    return True
