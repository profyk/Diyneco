"""Idempotency-Key rules (API spec, Conventions; DECISIONS G12, G13), exercised through
POST /signup, an anonymous Idem endpoint."""

from __future__ import annotations

import asyncio
import json
import uuid

import pytest
from sqlalchemy import text

from app.services import signup as signup_module
from app.services.idempotency import request_fingerprint
from tests.api.test_hotel_endpoints import signup_body

PATH = "/api/v1/signup"


async def hotels_named(owner_engine, name: str) -> int:
    async with owner_engine.connect() as conn:
        return (
            await conn.execute(text("SELECT count(*) FROM app.hotels WHERE name = :n"), {"n": name})
        ).scalar_one()


def unique_body() -> dict:
    body = signup_body()
    body["hotel"]["name"] = f"Idem Hotel {uuid.uuid4().hex[:8]}"
    return body


async def test_replay_returns_the_original_response_once(client, owner_engine):
    body, key = unique_body(), str(uuid.uuid4())
    first = await client.post("/signup", json=body, headers={"Idempotency-Key": key})
    second = await client.post("/signup", json=body, headers={"Idempotency-Key": key})
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    assert "Idempotent-Replayed" not in first.headers
    assert second.headers["Idempotent-Replayed"] == "true"
    assert await hotels_named(owner_engine, body["hotel"]["name"]) == 1


async def test_same_key_different_body_conflicts(client):
    key = str(uuid.uuid4())
    await client.post("/signup", json=unique_body(), headers={"Idempotency-Key": key})
    r = await client.post("/signup", json=unique_body(), headers={"Idempotency-Key": key})
    assert r.status_code == 409 and r.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


async def test_body_key_order_does_not_matter(client):
    body, key = unique_body(), str(uuid.uuid4())
    await client.post("/signup", json=body, headers={"Idempotency-Key": key})
    reordered = json.dumps({"hotel": body["hotel"], "owner": body["owner"]})
    r = await client.post(
        "/signup", content=reordered, headers={"Idempotency-Key": key, "Content-Type": "application/json"}
    )
    assert r.status_code == 201 and r.headers["Idempotent-Replayed"] == "true"


async def _claim_row(owner_engine, key: uuid.UUID, body: dict, age_s: int) -> None:
    fingerprint = request_fingerprint("POST", PATH, json.dumps(body).encode())
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO app.idempotency_keys (principal_key, key, method, path, request_hash, status, created_at) "
                "VALUES ('anon', :k, 'POST', :p, :h, 'in_progress', now() - make_interval(secs => :age))"
            ),
            {"k": key, "p": PATH, "h": fingerprint, "age": age_s},
        )


async def test_in_flight_request_returns_in_progress(client, owner_engine):
    body, key = unique_body(), uuid.uuid4()
    await _claim_row(owner_engine, key, body, age_s=1)
    r = await client.post("/signup", json=body, headers={"Idempotency-Key": str(key)})
    assert r.status_code == 409 and r.json()["error"]["code"] == "IDEMPOTENCY_IN_PROGRESS"


async def test_abandoned_claim_is_retaken(client, owner_engine):
    body, key = unique_body(), uuid.uuid4()
    await _claim_row(owner_engine, key, body, age_s=120)
    r = await client.post("/signup", json=body, headers={"Idempotency-Key": str(key)})
    assert r.status_code == 201
    assert await hotels_named(owner_engine, body["hotel"]["name"]) == 1


async def test_expired_key_is_treated_as_new(client, owner_engine):
    body, key = unique_body(), str(uuid.uuid4())
    await client.post("/signup", json=body, headers={"Idempotency-Key": key})
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.idempotency_keys SET expires_at = now() - interval '1 second' WHERE key = :k"),
            {"k": key},
        )
    other = unique_body()
    r = await client.post("/signup", json=other, headers={"Idempotency-Key": key})
    assert r.status_code == 201 and "Idempotent-Replayed" not in r.headers


@pytest.mark.parametrize("header", [None, "not-a-uuid"])
async def test_key_is_required_and_must_be_a_uuid(client, header):
    headers = {"Idempotency-Key": header} if header else {}
    r = await client.post("/signup", json=unique_body(), headers=headers)
    assert r.status_code == 400
    assert r.json()["error"]["details"]["fields"][0]["field"] == "Idempotency-Key"


async def test_client_errors_are_stored_and_replayed(client):
    body, key = unique_body(), str(uuid.uuid4())
    body["owner"]["password"] = "too-short"
    first = await client.post("/signup", json=body, headers={"Idempotency-Key": key})
    second = await client.post("/signup", json=body, headers={"Idempotency-Key": key})
    assert first.status_code == second.status_code == 400
    assert second.headers["Idempotent-Replayed"] == "true"
    assert first.json()["error"]["code"] == second.json()["error"]["code"] == "VALIDATION_FAILED"


async def test_server_errors_release_the_key_for_retry(client, owner_engine, monkeypatch):
    body, key = unique_body(), str(uuid.uuid4())
    real = signup_module.signup

    async def boom(*args, **kwargs):
        raise RuntimeError("simulated outage")

    monkeypatch.setattr("app.api.v1.hotel.signup_service", boom)
    failed = await client.post("/signup", json=body, headers={"Idempotency-Key": key})
    assert failed.status_code == 500
    assert "simulated" not in failed.text and "Traceback" not in failed.text
    assert await hotels_named(owner_engine, body["hotel"]["name"]) == 0

    monkeypatch.setattr("app.api.v1.hotel.signup_service", real)
    retry = await client.post("/signup", json=body, headers={"Idempotency-Key": key})
    assert retry.status_code == 201 and "Idempotent-Replayed" not in retry.headers
    assert await hotels_named(owner_engine, body["hotel"]["name"]) == 1


async def test_concurrent_requests_with_one_key_create_one_hotel(client, owner_engine):
    body, key = unique_body(), str(uuid.uuid4())
    results = await asyncio.gather(
        *[client.post("/signup", json=body, headers={"Idempotency-Key": key}) for _ in range(4)]
    )
    statuses = sorted(r.status_code for r in results)
    assert statuses.count(201) >= 1
    assert set(statuses) <= {201, 409}
    for r in results:
        if r.status_code == 409:
            assert r.json()["error"]["code"] == "IDEMPOTENCY_IN_PROGRESS"
    assert await hotels_named(owner_engine, body["hotel"]["name"]) == 1


async def test_keys_are_scoped_per_principal(app_state):
    """The same key from two principals is two different requests, never a replay or conflict."""
    from app.services.idempotency import claim

    key = uuid.uuid4()
    fp_a = request_fingerprint("POST", "/api/v1/x", b'{"a": 1}')
    fp_b = request_fingerprint("POST", "/api/v1/x", b'{"b": 2}')
    first = await claim(app_state.db.sessionmaker, f"user:{uuid.uuid4()}", key, "POST", "/api/v1/x", fp_a)
    second = await claim(app_state.db.sessionmaker, f"user:{uuid.uuid4()}", key, "POST", "/api/v1/x", fp_b)
    assert first.principal_key != second.principal_key
