"""Diyneco staff accounts and hotel accounts never mix (DECISIONS D75): each signs in only
through its own sign-in, holds only its own kind of permission on every route, and the
database refuses to turn one into the other or to put a Diyneco staff account in a hotel."""

from __future__ import annotations

import re
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.main import API_PREFIX
from tests.api.test_admin import platform, step_up
from tests.api.test_room_service import idem

# Routes anyone may call, signed in or not, or that act on the caller's own account.
OPEN_TO_EVERY_ACCOUNT = (
    "/auth/",
    "/health",
    "/plans",
    "/legal/documents",
    "/countries",
    "/currencies",
    "/signup",
    "/dev-storage",
    "/site/",  # the public website's reads, leads and page views (D83)
)


def _routes(app) -> list[tuple[str, str]]:
    """Every HTTP route the API serves, from its OpenAPI document, with ids filled in."""
    out = []
    for path, ops in app.openapi()["paths"].items():
        rel = path[len(API_PREFIX) :] if path.startswith(API_PREFIX) else path
        concrete = re.sub(r"\{[^}]+\}", str(uuid.uuid4()), rel)
        out.extend((m.upper(), concrete) for m in ops if m in ("get", "post", "put", "patch", "delete"))
    assert len(out) > 150  # the walk found the API, not an empty list
    return out


async def _call(client, method: str, path: str, headers: dict) -> int:
    kwargs = {"headers": {**headers, **idem()}}
    if method in ("POST", "PUT", "PATCH"):
        kwargs["json"] = {}
    return (await client.request(method, path, **kwargs)).status_code


async def test_each_account_signs_in_only_through_its_own_sign_in(client, factory):
    admin = await factory.platform_user()
    hotel = await factory.hotel(roles=("general_manager",))
    gm = hotel.users["general_manager"]

    wrong = await client.post("/auth/login", json={"email": admin.email, "password": admin.password})
    assert wrong.status_code == 401
    unknown = await client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "Whatever-123"}
    )
    assert wrong.json()["error"]["message"] == unknown.json()["error"]["message"]  # reveals nothing
    right = await client.post("/auth/platform/login", json={"email": admin.email, "password": admin.password})
    assert right.status_code == 200 and right.json()["mfa_required"] is True

    wrong = await client.post("/auth/platform/login", json={"email": gm.email, "password": gm.password})
    assert wrong.status_code == 401 and wrong.json()["error"]["code"] == "UNAUTHENTICATED"
    right = await client.post("/auth/login", json={"email": gm.email, "password": gm.password})
    assert right.status_code == 200


async def test_a_platform_token_opens_no_hotel_route(client, factory, app):
    admin = await platform(factory)
    headers = step_up(factory, admin)
    opened = []
    for method, path in _routes(app):
        if path.startswith("/admin") or path.startswith(OPEN_TO_EVERY_ACCOUNT):
            continue
        status = await _call(client, method, path, headers)
        assert status != 500, f"{method} {path}"
        if 200 <= status < 300:
            opened.append(f"{method} {path}")
    assert opened == []


async def test_a_hotel_token_opens_no_admin_route(client, factory, app):
    hotel = await factory.hotel(roles=("hotel_owner",))
    owner = await factory.auth(hotel, "hotel_owner")
    headers = await factory.step_up(hotel, "hotel_owner", owner)
    checked = 0
    for method, path in _routes(app):
        if not path.startswith("/admin"):
            continue
        status = await _call(client, method, path, headers)
        assert status in (401, 403), f"{method} {path} answered {status}"
        checked += 1
    assert checked > 30


async def test_the_database_keeps_the_two_kinds_apart(factory, owner_engine):
    admin = await factory.platform_user()
    hotel = await factory.hotel(roles=("general_manager",))
    gm = hotel.users["general_manager"]
    with pytest.raises(DBAPIError, match="cannot be a member of a hotel"):
        async with owner_engine.begin() as conn:
            await conn.execute(
                text("INSERT INTO app.hotel_users (hotel_id, user_id) VALUES (:h, :u)"),
                {"h": hotel.id, "u": admin.user_id},
            )
    for user in (admin, gm):
        with pytest.raises(DBAPIError, match="cannot change between"):
            async with owner_engine.begin() as conn:
                await conn.execute(
                    text("UPDATE app.users SET is_platform = NOT is_platform WHERE id = :u"),
                    {"u": user.user_id},
                )
