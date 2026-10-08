"""No hotel-scoped route takes a hotel id as input."""

from __future__ import annotations

import copy

from scripts.check_routes import check


def test_no_route_accepts_a_hotel_id(app):
    assert check(app.openapi()) == []


def test_check_catches_a_hotel_id_parameter(app):
    spec = copy.deepcopy(app.openapi())
    spec["paths"]["/api/v1/hotel"]["get"].setdefault("parameters", []).append(
        {"name": "hotel_id", "in": "query", "schema": {"type": "string"}}
    )
    assert check(spec) == ["GET /api/v1/hotel accepts ['hotel_id']"]
