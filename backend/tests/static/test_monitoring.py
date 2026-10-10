"""Monitoring never ships personal data or credentials."""

from __future__ import annotations

from app.core.monitoring import scrub


def test_scrub_removes_bodies_credentials_and_user_details():
    event = {
        "request": {
            "data": {"guest": {"name": "Zanele"}},
            "cookies": {"refresh": "secret"},
            "query_string": "email=a@b.c",
            "headers": {"Authorization": "Bearer x", "X-Api-Key": "dyk_live_x", "User-Agent": "ok"},
        },
        "user": {"id": "u1", "email": "a@b.c", "ip_address": "1.2.3.4"},
        "breadcrumbs": {"values": [{"category": "query", "message": "SELECT ..."}, {"category": "http"}]},
    }
    out = scrub(event)
    assert (
        "data" not in out["request"]
        and "cookies" not in out["request"]
        and "query_string" not in out["request"]
    )
    assert out["request"]["headers"] == {
        "Authorization": "[removed]",
        "X-Api-Key": "[removed]",
        "User-Agent": "ok",
    }
    assert out["user"] == {"id": "u1"}
    assert out["breadcrumbs"]["values"] == [{"category": "http"}]
