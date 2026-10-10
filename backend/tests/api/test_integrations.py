"""API keys, webhooks (signing, retries, disabling, private-address refusal) and the hotel's
subscription view."""

from __future__ import annotations

import json

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.realtime.bus import EventBus
from app.services import integrations
from app.services.webhook_delivery import (
    MAX_ATTEMPTS,
    UnsafeDestination,
    check_destination,
    deliver_due,
    verify,
)
from app.worker import drain_once
from tests.api.test_billing import walk_in
from tests.api.test_room_service import idem


async def owner(factory, hotel) -> dict[str, str]:
    return await factory.step_up(hotel, "hotel_owner", await factory.auth(hotel, "hotel_owner"))


async def set_plan(owner_engine, hotel, code: str) -> None:
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE app.subscriptions SET plan_id = (SELECT id FROM app.plans WHERE code = :c) "
                "WHERE hotel_id = :h"
            ),
            {"c": code, "h": hotel.id},
        )


async def test_api_keys_scopes_plans_and_use(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    own = await owner(factory, hotel)
    body = {"name": "PMS sync", "environment": "sandbox", "scopes": ["rooms.read", "orders.read"]}
    no_step_up = await client.post(
        "/api-keys", json=body, headers={**(await factory.auth(hotel, "hotel_owner")), **idem()}
    )
    assert no_step_up.json()["error"]["code"] == "STEP_UP_REQUIRED"
    created = await client.post("/api-keys", json=body, headers={**own, **idem()})
    assert created.status_code == 201, created.text
    secret = created.json()["secret"]
    assert secret.startswith("dyk_test_") and created.json()["prefix"] == secret[:16]
    listed = (await client.get("/api-keys", headers=own)).json()["data"]
    assert "secret" not in listed[0] and secret not in json.dumps(listed)

    for bad, reason in (
        ({**body, "scopes": ["staff.manage"]}, "scope_not_allowed"),
        ({**body, "scopes": ["rooms.status"]}, "sandbox_read_only"),
    ):
        r = await client.post("/api-keys", json=bad, headers={**own, **idem()})
        assert r.json()["error"]["details"]["reason"] == reason
    prod = {**body, "environment": "production", "scopes": ["rooms.read", "rooms.status"]}
    r = await client.post("/api-keys", json=prod, headers={**own, **idem()})
    assert r.json()["error"]["code"] == "PLAN_LIMIT_REACHED"  # starter has no production keys
    await set_plan(owner_engine, hotel, "professional")
    live = await client.post("/api-keys", json=prod, headers={**own, **idem()})
    assert live.status_code == 201 and live.json()["secret"].startswith("dyk_live_")

    key = {"X-Api-Key": secret}
    assert (await client.get("/rooms", headers=key)).status_code == 200
    assert (await client.get("/staff", headers=key)).json()["error"]["code"] == "PERMISSION_DENIED"
    live_key = {"X-Api-Key": live.json()["secret"]}
    changed = await client.post(
        f"/rooms/{hotel.room_ids[0]}/status", json={"status": "cleaning"}, headers=live_key
    )
    assert changed.status_code == 200, changed.text
    async with owner_engine.connect() as conn:
        audit = (
            await conn.execute(
                text(
                    "SELECT actor_type, actor_id FROM app.audit_logs WHERE hotel_id = :h "
                    "AND actor_type = 'api_key' ORDER BY created_at DESC LIMIT 1"
                ),
                {"h": hotel.id},
            )
        ).one()
        usage = (
            await conn.execute(
                text("SELECT usage_count FROM app.api_keys WHERE id = :k"), {"k": created.json()["id"]}
            )
        ).scalar_one()
    assert str(audit.actor_id) == live.json()["id"] and usage == 1  # a refused call rolls back

    other = await factory.hotel(rooms=1)
    assert (await client.get(f"/rooms/{other.room_ids[0]}", headers=key)).status_code == 404
    assert (await client.get("/rooms", headers={"X-Api-Key": "dyk_test_" + "A" * 43})).status_code == 401
    assert (await client.delete(f"/api-keys/{created.json()['id']}", headers=own)).status_code == 204
    revoked = await client.get("/rooms", headers=key)
    assert revoked.status_code == 401
    third = await client.post("/api-keys", json=body, headers={**own, **idem()})
    assert third.status_code == 201  # the revoked key frees its seat
    assert (
        await client.get("/api-keys", headers=await factory.auth(hotel, "general_manager"))
    ).status_code == 403


class Receiver:
    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(self.status)


async def _no_guard(url: str) -> None:
    return None


async def test_webhooks_are_signed_retried_and_disabled(
    client, factory, owner_engine, worker_engine, app_state
):
    hotel = await factory.hotel(rooms=2)
    own = await owner(factory, hotel)
    bad = await client.post(
        "/webhooks",
        json={"url": "http://example.com/hook", "events": ["STAY_CHECKED_IN"]},
        headers={**own, **idem()},
    )
    assert bad.json()["error"]["code"] == "VALIDATION_FAILED"
    unknown = await client.post(
        "/webhooks", json={"url": "https://example.com/hook", "events": ["NOPE"]}, headers={**own, **idem()}
    )
    assert unknown.json()["error"]["details"]["reason"] == "unknown_events"
    created = await client.post(
        "/webhooks",
        json={"url": "https://pms.example.com/diyneco", "events": ["STAY_CHECKED_IN"]},
        headers={**own, **idem()},
    )
    assert created.status_code == 201, created.text
    secret = created.json()["signing_secret"]
    hook_id = created.json()["id"]
    assert "signing_secret" not in (await client.get("/webhooks", headers=own)).json()["data"][0]

    maker = async_sessionmaker(worker_engine, expire_on_commit=False)

    async def decrypt(hotel_id, webhook_id, enc):
        return (
            await app_state.keyring.decrypt(str(hotel_id), enc, integrations.secret_context(webhook_id))
        ).decode()

    async def drain():
        while await drain_once(maker, EventBus(), batch=500) > 0:
            pass

    # A check-in is delivered, signed, with ids only.
    await walk_in(client, factory, hotel)
    await drain()
    ok = Receiver()
    async with httpx.AsyncClient(transport=httpx.MockTransport(ok)) as http:
        assert await deliver_due(maker, http, decrypt, guard=_no_guard) >= 1
    sent = [r for r in ok.requests if str(r.url) == "https://pms.example.com/diyneco"]
    assert len(sent) == 1
    body = sent[0].content
    assert verify(secret, body, sent[0].headers["Diyneco-Signature"])
    assert not verify(secret, body + b" ", sent[0].headers["Diyneco-Signature"])
    payload = json.loads(body)
    assert payload["type"] == "STAY_CHECKED_IN" and payload["hotel_id"] == str(hotel.id)
    assert "Folio Guest" not in body.decode()
    assert (await client.get(f"/webhooks/{hook_id}/deliveries", headers=own)).json()["data"][0][
        "state"
    ] == "delivered"

    # A ping goes to this webhook only.
    assert (await client.post(f"/webhooks/{hook_id}/test", headers=own)).status_code == 202
    await drain()
    async with httpx.AsyncClient(transport=httpx.MockTransport(ok)) as http:
        await deliver_due(maker, http, decrypt, guard=_no_guard)
    assert json.loads(ok.requests[-1].content)["type"] == "ping"

    # Failures back off, then the webhook is disabled and the owners are told.
    rec = await factory.auth(hotel, "receptionist")
    await client.post(
        f"/rooms/{hotel.room_ids[1]}/walk-in",
        json={"guest": {"name": "Two"}, "nights": 1},
        headers={**rec, **idem()},
    )
    await drain()
    failing = Receiver(status=500)
    disabled: list[str] = []

    async def notify(hotel_id, hook):
        disabled.append(str(hook.id))

    async with httpx.AsyncClient(transport=httpx.MockTransport(failing)) as http:
        for _ in range(MAX_ATTEMPTS):
            await deliver_due(maker, http, decrypt, guard=_no_guard, notify_disabled=notify)
            async with owner_engine.begin() as conn:  # skip the wait before the next retry
                await conn.execute(
                    text(
                        "UPDATE app.webhook_deliveries SET next_attempt_at = now() - interval '1 second' "
                        "WHERE webhook_id = :w AND next_attempt_at IS NOT NULL"
                    ),
                    {"w": hook_id},
                )
    assert len(failing.requests) == MAX_ATTEMPTS
    assert disabled == [hook_id]
    hook = next(w for w in (await client.get("/webhooks", headers=own)).json()["data"] if w["id"] == hook_id)
    assert hook["status"] == "disabled" and hook["failure_count"] == MAX_ATTEMPTS
    attempts = (await client.get(f"/webhooks/{hook_id}/deliveries", headers=own)).json()["data"]
    assert max(a["attempt"] for a in attempts) == MAX_ATTEMPTS
    enabled = await client.post(f"/webhooks/{hook_id}/status", json={"status": "active"}, headers=own)
    assert enabled.json() | {"created_at": None} == {
        **hook,
        "status": "active",
        "failure_count": 0,
        "created_at": None,
    }

    other = await factory.hotel(rooms=1)
    other_owner = await owner(factory, other)
    assert (await client.get(f"/webhooks/{hook_id}/deliveries", headers=other_owner)).status_code == 404


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/hook",
        "https://127.0.0.1/hook",
        "https://10.1.2.3/hook",
        "https://169.254.169.254/latest/meta-data",
        "https://[::1]/hook",
        "https://localhost/hook",
    ],
)
async def test_webhooks_never_reach_internal_addresses(url):
    with pytest.raises(UnsafeDestination):
        await check_destination(url)


async def test_subscription_view_and_change_request(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=2)
    own = await factory.auth(hotel, "hotel_owner")
    sub = (await client.get("/subscription", headers=own)).json()
    assert sub["plan"]["code"] == "starter" and sub["usage"]["rooms"] == {"used": 2, "limit": 50}
    r = await client.post(
        "/subscription/change-request", json={"plan_code": "professional"}, headers={**own, **idem()}
    )
    assert r.status_code == 202 and r.json()["requested_plan"] == "professional"
    same = await client.post(
        "/subscription/change-request", json={"plan_code": "starter"}, headers={**own, **idem()}
    )
    assert same.json()["error"]["code"] == "INVALID_TRANSITION"
    gm = await factory.auth(hotel, "general_manager")
    denied = await client.post(
        "/subscription/change-request", json={"plan_code": "professional"}, headers={**gm, **idem()}
    )
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
    async with owner_engine.connect() as conn:
        events = (
            await conn.execute(
                text(
                    "SELECT type FROM app.event_outbox WHERE hotel_id = :h AND 'platform' = ANY(channels) "
                    "AND type = 'SUBSCRIPTION_CHANGE_REQUESTED'"
                ),
                {"h": hotel.id},
            )
        ).all()
    assert len(events) == 1
