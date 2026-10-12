"""Legal documents (DECISIONS D70): versions are drafted and published by the platform, frozen
once published, served per country, accepted by merchants and kept as acceptances.

Documents are platform-wide rows shared by every test, so these tests publish only for New
Zealand (NZ), a country no other test signs up in."""

from __future__ import annotations

import secrets

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.api.test_admin import platform, step_up
from tests.api.test_checkout import pair_tablet
from tests.api.test_hotel_endpoints import signup_body
from tests.api.test_room_service import idem

NZ = "NZ"


async def publish(client, factory, kind: str, title: str, country: str = NZ) -> dict:
    admin = await platform(factory)
    draft = await client.post(
        "/admin/legal-documents",
        json={"kind": kind, "country": country, "title": title, "body": f"{title} text.", "summary": "New"},
        headers={**admin, **idem()},
    )
    assert draft.status_code == 201, draft.text
    assert draft.json()["status"] == "draft"
    out = await client.post(
        f"/admin/legal-documents/{draft.json()['id']}/publish",
        headers={**step_up(factory, admin), **idem()},
    )
    assert out.status_code == 200, out.text
    return out.json()


async def set_country(owner_engine, hotel, country: str) -> None:
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("UPDATE app.hotels SET country = :c WHERE id = :h"), {"c": country, "h": hotel.id}
        )


async def test_platform_drafts_publishes_and_freezes(client, factory, owner_engine):
    admin = await platform(factory)
    support = await platform(factory, "platform_support")
    body = {"kind": "acceptable_use", "country": NZ, "title": "Acceptable use", "body": "Be kind."}
    refused = await client.post("/admin/legal-documents", json=body, headers={**support, **idem()})
    assert refused.json()["error"]["code"] == "PERMISSION_DENIED"

    draft = (await client.post("/admin/legal-documents", json=body, headers={**admin, **idem()})).json()
    edited = await client.patch(
        f"/admin/legal-documents/{draft['id']}", json={"body": "Be very kind."}, headers=admin
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["body"] == "Be very kind."
    assert (await client.get(f"/legal/documents/{draft['id']}")).status_code == 404  # drafts are private

    no_step_up = await client.post(
        f"/admin/legal-documents/{draft['id']}/publish", headers={**admin, **idem()}
    )
    assert no_step_up.json()["error"]["code"] == "STEP_UP_REQUIRED"
    published = (
        await client.post(
            f"/admin/legal-documents/{draft['id']}/publish", headers={**step_up(factory, admin), **idem()}
        )
    ).json()
    assert published["status"] == "published" and published["published_at"]
    assert (await client.get(f"/legal/documents/{draft['id']}")).json()["body"] == "Be very kind."

    frozen = await client.patch(f"/admin/legal-documents/{draft['id']}", json={"body": "x"}, headers=admin)
    assert frozen.json()["error"]["code"] == "INVALID_TRANSITION"
    gone = await client.delete(f"/admin/legal-documents/{draft['id']}", headers=admin)
    assert gone.json()["error"]["code"] == "INVALID_TRANSITION"
    # The database refuses changes to a published version even from the owner role.
    with pytest.raises(DBAPIError, match="frozen"):
        async with owner_engine.begin() as conn:
            await conn.execute(
                text("UPDATE app.legal_documents SET body = 'changed' WHERE id = :id"), {"id": draft["id"]}
            )

    second = (await client.post("/admin/legal-documents", json=body, headers={**admin, **idem()})).json()
    assert second["version"] == published["version"] + 1
    assert (await client.delete(f"/admin/legal-documents/{second['id']}", headers=admin)).status_code == 204
    listed = (await client.get("/admin/legal-documents", headers=admin)).json()["data"]
    assert draft["id"] in {d["id"] for d in listed} and second["id"] not in {d["id"] for d in listed}


async def test_signup_requires_current_documents_and_records_them(client, factory, owner_engine):
    terms = await publish(client, factory, "terms", "Terms of service")
    privacy = await publish(client, factory, "privacy", "Privacy notice")
    dpa = await publish(client, factory, "dpa", "Data processing agreement")
    current = {terms["id"], privacy["id"], dpa["id"]}

    listed = (await client.get("/legal/documents", params={"country": NZ, "audience": "merchant"})).json()
    assert {d["id"] for d in listed["data"]} == current
    assert all(d["body"] for d in listed["data"])
    # Another country without versions of its own is not given New Zealand's.
    other = (await client.get("/legal/documents", params={"country": "IS", "audience": "merchant"})).json()
    assert all(d["country"] is None for d in other["data"])

    body = signup_body(f"kiwi.{secrets.token_hex(3)}@example.com")
    body["hotel"] = {"name": "Kiwi Lodge", "country": NZ}
    missing = await client.post("/signup", json=body, headers=idem())
    assert missing.json()["error"]["details"]["fields"][0]["field"] == "accepted_documents"
    partial = await client.post("/signup", json={**body, "accepted_documents": [terms["id"]]}, headers=idem())
    assert partial.json()["error"]["details"]["fields"][0]["field"] == "accepted_documents"

    done = await client.post("/signup", json={**body, "accepted_documents": sorted(current)}, headers=idem())
    assert done.status_code == 201, done.text
    # The same email again without acceptance gets the same refusal as a new one: no enumeration.
    again = await client.post("/signup", json=body, headers=idem())
    assert again.json()["error"]["details"]["fields"][0]["field"] == "accepted_documents"

    async with owner_engine.connect() as conn:
        accepted = (
            (
                await conn.execute(
                    text(
                        "SELECT a.document_id::text FROM app.legal_acceptances a "
                        "JOIN app.users u ON u.id = a.user_id WHERE u.email = :e"
                    ),
                    {"e": body["owner"]["email"]},
                )
            )
            .scalars()
            .all()
        )
        assert set(accepted) == current
        hotel = (
            await conn.execute(
                text(
                    "SELECT h.country, h.data_region, s.currency, s.tax_label, s.timezone FROM app.hotels h "
                    "JOIN app.hotel_settings s ON s.hotel_id = h.id "
                    "JOIN app.legal_acceptances a ON a.hotel_id = h.id "
                    "JOIN app.users u ON u.id = a.user_id WHERE u.email = :e LIMIT 1"
                ),
                {"e": body["owner"]["email"]},
            )
        ).one()
        assert tuple(hotel) == ("NZ", "ap-southeast", "NZD", "GST", "Pacific/Auckland")


async def test_staff_accept_new_versions_and_acceptances_are_append_only(
    client, factory, owner_engine, api_engine
):
    hotel = await factory.hotel(roles=("general_manager", "receptionist"))
    await set_country(owner_engine, hotel, NZ)
    terms = await publish(client, factory, "terms", "Terms, next version")
    gm = await factory.auth(hotel, "general_manager")
    pending = (await client.get("/legal/pending", headers=gm)).json()["data"]
    assert terms["id"] in {d["id"] for d in pending}
    assert all(d.get("body") is None for d in pending)

    stale = await client.post(
        "/legal/accept", json={"document_ids": [str(hotel.id)]}, headers={**gm, **idem()}
    )
    assert stale.json()["error"]["code"] == "VALIDATION_FAILED"
    left = await client.post(
        "/legal/accept", json={"document_ids": [d["id"] for d in pending]}, headers={**gm, **idem()}
    )
    assert left.status_code == 200, left.text
    assert left.json()["data"] == []
    # Acceptance is personal: the receptionist still has to accept.
    rec = await factory.auth(hotel, "receptionist")
    assert (await client.get("/legal/pending", headers=rec)).json()["data"]

    newer = await publish(client, factory, "terms", "Terms, newer version")
    assert [d["id"] for d in (await client.get("/legal/pending", headers=gm)).json()["data"]] == [newer["id"]]

    async with owner_engine.connect() as conn:
        audited = (
            await conn.execute(
                text("SELECT count(*) FROM app.audit_logs WHERE hotel_id = :h AND action = 'legal.accept'"),
                {"h": hotel.id},
            )
        ).scalar_one()
        assert audited == 1
    with pytest.raises(DBAPIError):  # the API role cannot rewrite who accepted what
        async with api_engine.begin() as conn:
            await conn.execute(text("SELECT set_config('app.hotel_id', :h, true)"), {"h": str(hotel.id)})
            await conn.execute(text("DELETE FROM app.legal_acceptances WHERE hotel_id = :h"), {"h": hotel.id})


async def test_guest_tablet_reads_guest_documents_for_its_country(client, factory, owner_engine):
    hotel = await factory.hotel(rooms=1, roles=("general_manager",))
    await set_country(owner_engine, hotel, NZ)
    guest_terms = await publish(client, factory, "guest_terms", "Guest terms")
    gm = await factory.auth(hotel, "general_manager")
    tablet = await pair_tablet(client, gm, hotel.room_ids[0])
    docs = (await client.get("/guest/legal", headers=tablet)).json()["data"]
    assert [d["id"] for d in docs if d["kind"] == "guest_terms"] == [guest_terms["id"]]
    assert all(d["kind"] in ("guest_terms", "guest_privacy") for d in docs)
    # A tablet cannot accept on anyone's behalf.
    refused = await client.post(
        "/legal/accept", json={"document_ids": [guest_terms["id"]]}, headers={**tablet, **idem()}
    )
    assert refused.status_code in (401, 403)
