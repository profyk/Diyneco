"""Cross-cutting HTTP behaviour: error envelope, request id, security headers, CORS, unknown
query parameters, card data, configuration fail-fast, RBAC grant rule."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from app.core.config import Settings
from app.core.crypto import looks_like_card_number
from app.core.errors import AppError
from app.services.rbac import assert_can_grant


async def test_error_envelope_and_request_id(client):
    r = await client.get("/does-not-exist", headers={"X-Request-Id": "trace-12345678"})
    assert r.status_code == 404
    assert r.json() == {
        "error": {"code": "NOT_FOUND", "message": "Not found.", "request_id": "trace-12345678", "details": {}}
    }
    assert r.headers["X-Request-Id"] == "trace-12345678"
    bad = await client.get("/health", headers={"X-Request-Id": "<script>"})
    assert bad.headers["X-Request-Id"] != "<script>"


async def test_validation_errors_list_fields(client):
    r = await client.post("/auth/login", json={"email": "a@b.c"})
    assert r.status_code == 400
    err = r.json()["error"]
    assert err["code"] == "VALIDATION_FAILED"
    assert err["details"]["fields"][0]["field"] == "password"


async def test_security_headers(client):
    r = await client.get("/health")
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert r.headers["Cache-Control"] == "no-store"


async def test_cors_allow_list(client):
    allowed = await client.options(
        "/health", headers={"Origin": "http://localhost:3001", "Access-Control-Request-Method": "GET"}
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3001"
    denied = await client.options(
        "/health", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"}
    )
    assert "access-control-allow-origin" not in denied.headers


async def test_unknown_query_parameters_are_rejected(client, factory):
    hotel = await factory.hotel(roles=("general_manager",))
    headers = await factory.auth(hotel, "general_manager")
    r = await client.get("/hotel?hotel_id=x", headers=headers)
    assert r.status_code == 400
    assert r.json()["error"]["details"]["fields"][0]["field"] == "hotel_id"


@pytest.mark.parametrize(
    "body",
    [
        {"email": "a@b.c", "password": "4111 1111 1111 1111"},
        {"email": "a@b.c", "password": "x", "cvv": "123"},
        {"email": "4012888888881881", "password": "x"},
    ],
)
async def test_card_data_is_rejected_anywhere(client, body):
    r = await client.post("/auth/login", json=body)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "CARD_DATA_REJECTED"
    assert "4111" not in r.text and "123" not in r.json()["error"]["message"]


def test_card_number_detection():
    assert looks_like_card_number("4111111111111111")
    assert looks_like_card_number("pay with 5500-0000-0000-0004 please")
    assert not looks_like_card_number("4111111111111112")  # fails Luhn
    assert not looks_like_card_number("+27 82 123 4567")  # phone number
    assert not looks_like_card_number("1234")
    # Ids are never mistaken for cards (this once failed CI: about 1 in 400 UUIDs passed Luhn).
    ids = [str(uuid.uuid4()) for _ in range(5000)] + ["01923456-7890-7123-8456-789012345678"]
    assert not any(looks_like_card_number(i) for i in ids)
    assert looks_like_card_number(f"{ids[0]} 4111 1111 1111 1111")


def _settings(**overrides):
    base = {
        "app_env": "development",
        "api_base_url": "http://x",
        "database_url": "postgresql+asyncpg://u:p@h/d",
        "jwt_signing_keys_json": '{"keys":[{"kid":"k1","kty":"OKP","crv":"Ed25519","x":"a","d":"b"}]}',
        "jwt_active_kid": "k1",
        "pairing_code_pepper": "pepper",
        "kms_master_key_id": "id",
        "kms_local_master_key": "A" * 43 + "=",
    }
    return Settings(_env_file=None, **{**base, **overrides})  # type: ignore[call-arg]


def test_settings_fail_fast():
    _settings()  # valid
    for override, message in (
        ({"pairing_code_pepper": "CHANGE_ME"}, "PAIRING_CODE_PEPPER"),
        ({"jwt_active_kid": "other"}, "JWT_ACTIVE_KID"),
        ({"kms_local_master_key": "short"}, "KMS_LOCAL_MASTER_KEY"),
        ({"app_env": "production"}, "REDIS_URL"),
        ({"cors_allowed_origins": "*"}, "wildcard"),
    ):
        with pytest.raises(ValidationError) as err:
            _settings(**override)
        assert message in str(err.value)


async def test_receptionist_cannot_grant_permissions_they_lack(api_session, factory):
    hotel = await factory.hotel(roles=("receptionist", "hotel_admin"))
    from tests.conftest import as_hotel

    await as_hotel(api_session, hotel.id)
    held = set(
        (
            await api_session.execute(
                text(
                    "SELECT rp.permission_code FROM app.user_roles ur JOIN app.role_permissions rp ON rp.role_id = ur.role_id "
                    "WHERE ur.hotel_user_id = :hu"
                ),
                {"hu": hotel.users["receptionist"].hotel_user_id},
            )
        ).scalars()
    )
    assert "roles.manage" not in held and "folio.adjust.approve" not in held
    assert_can_grant(held, {"stays.read"})  # a subset of what they hold is fine
    with pytest.raises(AppError) as err:
        assert_can_grant(held, {"stays.read", "folio.adjust.approve"})
    assert err.value.code == "PERMISSION_DENIED"
    assert err.value.details == {"missing_permissions": ["folio.adjust.approve"]}
