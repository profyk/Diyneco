"""WebSocket gateway: handshake, channel permissions, replay since a seq, live events.

The gateway runs in Starlette's TestClient on its own thread and event loop, with its own
app instance, because the async engine of the shared test app is bound to the test loop.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import build_state, create_app


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


async def _tablet(client, factory, hotel):
    gm = await factory.auth(hotel, "general_manager")
    code = (
        await client.post(
            "/devices/pairings",
            json={"type": "guest", "room_id": str(hotel.room_ids[0])},
            headers={**gm, **idem()},
        )
    ).json()["code"]
    pair = (await client.post("/devices/pair", json={"code": code}, headers=idem())).json()
    token = (
        await client.post("/devices/token", json={"device_credential": pair["device_credential"]})
    ).json()
    return gm, pair["device_id"], token["access_token"]


def _run(settings, fn):
    def go():
        app = create_app(settings, state=build_state(settings))
        with TestClient(app, base_url="http://testserver") as tc:
            return fn(tc)

    return asyncio.to_thread(go)


async def test_must_authenticate_first(settings):
    def flow(tc):
        with tc.websocket_connect("/api/v1/ws") as ws:
            ws.send_json({"op": "subscribe", "channels": ["x"]})
            with pytest.raises(WebSocketDisconnect) as exc:
                ws.receive_json()
            return exc.value.code

    assert await _run(settings, flow) == 4401


async def test_tablet_sees_only_its_room_with_replay_and_live_events(client, factory, settings):
    hotel = await factory.hotel(rooms=2)
    gm, device_id, token = await _tablet(client, factory, hotel)
    rec = await factory.auth(hotel, "receptionist")
    await client.post(
        f"/rooms/{hotel.room_ids[0]}/walk-in",
        json={"guest": {"name": "G"}, "nights": 1},
        headers={**rec, **idem()},
    )
    own = f"hotel:{hotel.id}:room:{hotel.room_ids[0]}"

    def flow(tc):
        with tc.websocket_connect("/api/v1/ws") as ws:
            ws.send_json({"op": "auth", "token": token})
            ready = ws.receive_json()
            ws.send_json({"op": "subscribe", "channels": [own], "since_seq": 0})
            replayed = ws.receive_json()
            subscribed = ws.receive_json()
            r = tc.post(f"/api/v1/devices/{device_id}/reset", headers={**gm, **idem()})
            assert r.status_code == 200, r.text
            live = ws.receive_json()
        with tc.websocket_connect("/api/v1/ws") as ws:
            ws.send_json({"op": "auth", "token": token})
            ws.receive_json()
            ws.send_json({"op": "subscribe", "channels": [f"hotel:{hotel.id}:ops"]})
            with pytest.raises(WebSocketDisconnect) as exc:
                ws.receive_json()
        return ready, replayed, subscribed, live, exc.value.code

    ready, replayed, subscribed, live, denied = await _run(settings, flow)
    assert ready == {"op": "ready", "channels": [own]}
    assert replayed["type"] == "STAY_CHECKED_IN" and replayed["channel"] == own
    assert subscribed["op"] == "subscribed"
    assert live["type"] == "RESET_ROOM_SESSION" and live["seq"] > replayed["seq"]
    assert denied == 4403


async def test_kitchen_staff_get_new_orders_live(client, factory, settings, owner_engine):
    hotel = await factory.hotel(rooms=1)
    gm, _, tablet_token = await _tablet(client, factory, hotel)
    cat = (await client.post("/menu/categories", json={"name": "Mains"}, headers={**gm, **idem()})).json()
    item = (
        await client.post(
            "/menu/items",
            json={
                "name": "Toast",
                "price": {"amount_minor": 3000, "currency": "ZAR"},
                "station_id": str(hotel.station_id),
                "category_id": cat["id"],
            },
            headers={**gm, **idem()},
        )
    ).json()
    rec = await factory.auth(hotel, "receptionist")
    await client.post(
        f"/rooms/{hotel.room_ids[0]}/walk-in",
        json={"guest": {"name": "G"}, "nights": 1},
        headers={**rec, **idem()},
    )
    kitchen = (await factory.auth(hotel, "kitchen_staff"))["Authorization"].split(" ", 1)[1]
    channel = f"hotel:{hotel.id}:kitchen:{hotel.station_id}"
    tablet = {"Authorization": f"Bearer {tablet_token}"}

    def flow(tc):
        with tc.websocket_connect("/api/v1/ws") as ws:
            ws.send_json({"op": "auth", "token": kitchen})
            ready = ws.receive_json()
            ws.send_json({"op": "subscribe", "channels": [channel]})
            ws.receive_json()
            placed = tc.post(
                "/api/v1/guest/orders",
                json={
                    "lines": [{"menu_item_id": item["id"], "quantity": 1}],
                    "quoted_total": {"amount_minor": 3000, "currency": "ZAR"},
                },
                headers={**tablet, **idem()},
            )
            assert placed.status_code == 201, placed.text
            event = ws.receive_json()
        return ready, event, placed.json()

    ready, event, order = await _run(settings, flow)
    assert channel in ready["channels"] and f"hotel:{hotel.id}:ops" not in ready["channels"]
    assert event["type"] == "NEW_ORDER"
    assert event["data"]["order_id"] == order["id"]
    assert "total" not in str(event["data"])  # notifications carry ids, never amounts


async def test_revoked_device_cannot_connect(client, factory, settings):
    hotel = await factory.hotel(rooms=1)
    gm, device_id, token = await _tablet(client, factory, hotel)
    s = await factory.step_up(hotel, "general_manager", gm)
    await client.delete(f"/devices/{device_id}/pairing", headers={**s, **idem()})

    def flow(tc):
        with tc.websocket_connect("/api/v1/ws") as ws:
            ws.send_json({"op": "auth", "token": token})
            with pytest.raises(WebSocketDisconnect) as exc:
                ws.receive_json()
            return exc.value.code

    assert await _run(settings, flow) == 4409
