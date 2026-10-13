"""Payment provider helpers (DECISIONS D79): Svix webhook signatures and provider amounts."""

from __future__ import annotations

import base64

import pytest

from app.billing.providers import SandboxProvider, build, major, sign_svix, verify_svix
from app.core.config import Settings
from app.core.errors import AppError

SECRET = "whsec_" + base64.b64encode(b"a-test-signing-key").decode()
BODY = b'{"id": "pr_1"}'


def _headers(msg: str = "msg_1", ts: int = 1_000_000, sig: str | None = None) -> dict[str, str]:
    return {
        "svix-id": msg,
        "svix-timestamp": str(ts),
        "svix-signature": sig or sign_svix(SECRET, msg, ts, BODY),
    }


def test_a_signed_body_is_accepted_and_its_message_id_returned():
    assert verify_svix(SECRET, _headers(), BODY, now=1_000_100) == "msg_1"
    # Several signatures (key rotation): any valid v1 one is enough.
    both = f"v1,bm90LXRoaXM= {sign_svix(SECRET, 'msg_1', 1_000_000, BODY)}"
    assert verify_svix(SECRET, _headers(sig=both), BODY, now=1_000_000) == "msg_1"


@pytest.mark.parametrize(
    ("headers", "body", "now"),
    [
        (_headers(), b'{"id": "pr_2"}', 1_000_000),  # body changed
        (_headers(sig="v1,AAAA"), BODY, 1_000_000),  # wrong signature
        (_headers(sig=sign_svix(SECRET, "msg_1", 1_000_000, BODY).replace("v1", "v2")), BODY, 1_000_000),
        (_headers(), BODY, 1_000_000 + 301),  # too old: a replay
        (_headers(), BODY, 1_000_000 - 301),  # from the future
        ({"svix-id": "msg_1", "svix-timestamp": "x", "svix-signature": "v1,AAAA"}, BODY, 0),
        ({}, BODY, 0),
    ],
)
def test_anything_else_is_refused(headers, body, now):
    with pytest.raises(AppError) as err:
        verify_svix(SECRET, headers, body, now=now)
    assert err.value.code == "UNAUTHENTICATED"


def test_signatures_depend_on_the_secret():
    other = "whsec_" + base64.b64encode(b"another-key").decode()
    with pytest.raises(AppError):
        verify_svix(other, _headers(), BODY, now=1_000_000)


def test_amounts_are_sent_in_major_units_exactly():
    assert major(49900, "ZAR") == "499.00"
    assert major(5, "ZAR") == "0.05"
    assert major(1500, "JPY") == "1500"
    assert major(2125, "BHD") == "2.125"


def test_the_sandbox_never_runs_in_production(settings: Settings):
    assert isinstance(build(settings, "sandbox"), SandboxProvider)
    live = settings.model_copy(update={"app_env": "production"})
    with pytest.raises(AppError):
        build(live, "sandbox")
    with pytest.raises(AppError):
        build(settings, "stitch")  # not configured here
    with pytest.raises(AppError):
        build(settings, "none")
