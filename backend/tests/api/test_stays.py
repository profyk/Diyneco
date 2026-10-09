"""Guests, billing profiles, reservations, check-in (accommodation posting, VAT), walk-ins."""

from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import text

from app.billing.folio import business_date
from app.billing.vat import gross_and_vat, vat_included, vat_on_top


def idem() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


def zar(n: int) -> dict:
    return {"amount_minor": n, "currency": "ZAR"}


async def vat_registered(owner_engine, hotel, **extra) -> None:
    sets = ", ".join(f"{k} = :{k}" for k in extra)
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE app.hotel_settings SET vat_registered = true, vat_number = '4123456789'"
                + (f", {sets}" if sets else "")
                + " WHERE hotel_id = :h"
            ),
            {"h": hotel.id, **extra},
        )


def test_vat_arithmetic_matches_the_spec_examples():
    # API spec: R290 + R20 + R50 fee, VAT-inclusive at 15% -> R46.96 VAT.
    assert vat_included(29000, 1500) + vat_included(2000, 1500) + vat_included(5000, 1500) == 4696
    # Build spec: R1,500 a night excl. VAT -> R1,725.00, three nights R5,175.00.
    assert gross_and_vat(150000, 1500, includes_vat=False, registered=True) == (172500, 22500)
    assert gross_and_vat(150000, 1500, includes_vat=False, registered=False) == (150000, 0)
    assert vat_on_top(1, 1500) == 0 and vat_on_top(4, 1500) == 1  # 0.6 rounds up
    assert vat_included(-11500, 1500) == -1500


async def test_walk_in_posts_every_night_with_vat_and_occupies_the_room(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    await vat_registered(owner_engine, hotel)
    rec = await factory.auth(hotel, "receptionist")
    r = await client.post(
        f"/rooms/{hotel.room_ids[0]}/walk-in",
        json={"guest": {"name": "John Smith", "email": "John@Example.com"}, "nights": 3},
        headers={**rec, **idem()},
    )
    assert r.status_code == 201, r.text
    stay = r.json()
    assert stay["status"] == "active" and stay["nights"] == 3
    assert stay["folio"]["accommodation"] == zar(517500)
    assert stay["folio"]["balance"] == zar(517500)
    room = (await client.get(f"/rooms/{hotel.room_ids[0]}", headers=rec)).json()
    assert room["status"] == "occupied"
    async with owner_engine.connect() as conn:
        nights = (
            await conn.execute(
                text(
                    "SELECT business_date, amount_minor, vat_minor FROM app.folio_entries "
                    "WHERE folio_id = :f ORDER BY business_date"
                ),
                {"f": stay["folio"]["folio_id"]},
            )
        ).all()
        events = (
            await conn.execute(
                text(
                    "SELECT channels FROM app.event_outbox WHERE hotel_id = :h AND type = 'STAY_CHECKED_IN'"
                ),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert [(n.amount_minor, n.vat_minor) for n in nights] == [(172500, 22500)] * 3
    assert [n.business_date - nights[0].business_date for n in nights] == [
        timedelta(days=i) for i in range(3)
    ]
    assert f"hotel:{hotel.id}:room:{hotel.room_ids[0]}" in events
    again = await client.post(
        f"/rooms/{hotel.room_ids[0]}/walk-in",
        json={"guest": {"name": "Second"}, "nights": 1},
        headers={**rec, **idem()},
    )
    assert again.json()["error"]["code"] == "ROOM_NOT_AVAILABLE"


async def test_reservation_then_check_in_and_cancel_rules(client, factory):
    hotel = await factory.hotel(rooms=2)
    rec = await factory.auth(hotel, "receptionist")
    today = business_date("Africa/Johannesburg")
    body = {
        "room_id": str(hotel.room_ids[0]),
        "guest": {"name": "Ann Lee"},
        "arrival_date": str(today),
        "departure_date": str(today + timedelta(days=2)),
    }
    reserved = await client.post("/stays", json=body, headers={**rec, **idem()})
    assert reserved.status_code == 201, reserved.text
    assert reserved.json()["status"] == "reserved" and reserved.json()["folio"] is None
    overlap = await client.post("/stays", json=body, headers={**rec, **idem()})
    assert overlap.json()["error"]["code"] == "ROOM_NOT_AVAILABLE"
    sid = reserved.json()["id"]
    checked = await client.post(f"/stays/{sid}/check-in", headers={**rec, **idem()})
    assert checked.status_code == 200, checked.text
    assert checked.json()["folio"]["accommodation"] == zar(300000)  # not VAT-registered
    twice = await client.post(f"/stays/{sid}/check-in", headers={**rec, **idem()})
    assert twice.json()["error"]["code"] == "INVALID_TRANSITION"
    assert (await client.post(f"/stays/{sid}/cancel", headers={**rec, **idem()})).json()["error"]["code"] == (
        "INVALID_TRANSITION"
    )
    future = await client.post(
        "/stays",
        json={
            **body,
            "room_id": str(hotel.room_ids[1]),
            "arrival_date": str(today + timedelta(days=5)),
            "departure_date": str(today + timedelta(days=6)),
        },
        headers={**rec, **idem()},
    )
    early = await client.post(f"/stays/{future.json()['id']}/check-in", headers={**rec, **idem()})
    assert early.json()["error"]["code"] == "INVALID_TRANSITION"
    cancelled = await client.post(f"/stays/{future.json()['id']}/cancel", headers={**rec, **idem()})
    assert cancelled.json()["status"] == "cancelled"


async def test_rate_override_needs_permission_and_reason(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1)
    rec = await factory.auth(hotel, "receptionist")
    rm = await factory.auth(hotel, "reception_manager")
    body = {"guest": {"name": "Corp Guest"}, "nights": 1, "rate_override": zar(99900)}
    denied = await client.post(f"/rooms/{hotel.room_ids[0]}/walk-in", json=body, headers={**rec, **idem()})
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"
    no_reason = await client.post(f"/rooms/{hotel.room_ids[0]}/walk-in", json=body, headers={**rm, **idem()})
    assert no_reason.json()["error"]["code"] == "REASON_REQUIRED"
    ok = await client.post(
        f"/rooms/{hotel.room_ids[0]}/walk-in",
        json={**body, "rate_override_reason": "Corporate rate ABC Tech"},
        headers={**rm, **idem()},
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["nightly_rate"] == zar(99900)
    async with owner_engine.connect() as conn:
        audit = (
            await conn.execute(
                text("SELECT new_value FROM app.audit_logs WHERE hotel_id = :h AND action = 'stay.create'"),
                {"h": hotel.id},
            )
        ).scalar_one()
    assert audit["standard_rate_minor"] == 150000 and audit["nightly_rate_minor"] == 99900


async def test_company_billing_and_profiles(client, factory):
    hotel = await factory.hotel(rooms=1)
    rec = await factory.auth(hotel, "receptionist")
    profile = await client.post(
        "/billing-profiles",
        json={"company_name": "ABC Tech", "vat_number": "4987654321", "billing_email": "Travel@ABC.example"},
        headers={**rec, **idem()},
    )
    assert profile.status_code == 201, profile.text
    found = (await client.get("/billing-profiles", params={"q": "abc"}, headers=rec)).json()["data"]
    assert [p["company_name"] for p in found] == ["ABC Tech"]
    no_profile = await client.post(
        f"/rooms/{hotel.room_ids[0]}/walk-in",
        json={"guest": {"name": "J"}, "nights": 1, "billing": {"type": "company"}},
        headers={**rec, **idem()},
    )
    assert no_profile.status_code == 400
    ok = await client.post(
        f"/rooms/{hotel.room_ids[0]}/walk-in",
        json={
            "guest": {"name": "John Smith"},
            "nights": 1,
            "billing": {
                "type": "company",
                "billing_profile_id": profile.json()["id"],
                "purchase_order": "TRAVEL-10482",
                "traveller_name": "John Smith",
            },
        },
        headers={**rec, **idem()},
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["billing_type"] == "company" and ok.json()["purchase_order"] == "TRAVEL-10482"


async def test_guest_search_and_history(client, factory):
    hotel = await factory.hotel(rooms=1)
    rec = await factory.auth(hotel, "receptionist")
    g = await client.post(
        "/guests", json={"name": "Thabo Nkosi", "phone": "+27 82 555 0101"}, headers={**rec, **idem()}
    )
    assert g.status_code == 201
    assert [
        x["name"] for x in (await client.get("/guests", params={"q": "thabo"}, headers=rec)).json()["data"]
    ] == ["Thabo Nkosi"]
    walked = await client.post(
        f"/rooms/{hotel.room_ids[0]}/walk-in",
        json={"guest_id": g.json()["id"], "nights": 1},
        headers={**rec, **idem()},
    )
    assert walked.status_code == 201, walked.text
    profile = (await client.get(f"/guests/{g.json()['id']}", headers=rec)).json()
    assert [s["room"] for s in profile["stays"]] == ["101"]


async def test_block_charges_and_permissions(client, factory):
    hotel = await factory.hotel(rooms=1)
    rec = await factory.auth(hotel, "receptionist")
    stay = (
        await client.post(
            f"/rooms/{hotel.room_ids[0]}/walk-in",
            json={"guest": {"name": "B"}, "nights": 1},
            headers={**rec, **idem()},
        )
    ).json()
    blocked = await client.post(f"/stays/{stay['id']}/block-charges", headers=rec)
    assert blocked.json()["charges_blocked"] is True
    ks = await factory.auth(hotel, "kitchen_staff")
    assert (await client.get("/stays", headers=ks)).json()["error"]["code"] == "PERMISSION_DENIED"
    fin = await factory.auth(hotel, "finance_manager")
    assert (await client.get("/stays", headers=fin)).status_code == 200
    denied = await client.post(f"/stays/{stay['id']}/unblock-charges", headers=fin)
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"


async def test_stays_cross_tenant(client, factory):
    a = await factory.hotel(rooms=1)
    b = await factory.hotel(rooms=1)
    ra = await factory.auth(a, "receptionist")
    rb = await factory.auth(b, "receptionist")
    stay = (
        await client.post(
            f"/rooms/{a.room_ids[0]}/walk-in",
            json={"guest": {"name": "A"}, "nights": 1},
            headers={**ra, **idem()},
        )
    ).json()
    assert (await client.get(f"/stays/{stay['id']}", headers=rb)).status_code == 404
    assert (await client.get(f"/guests/{stay['guest']['id']}", headers=rb)).status_code == 404
    assert (
        await client.post(
            f"/rooms/{a.room_ids[0]}/walk-in",
            json={"guest": {"name": "X"}, "nights": 1},
            headers={**rb, **idem()},
        )
    ).status_code == 404
    assert (await client.get("/stays", headers=rb)).json()["data"] == []
