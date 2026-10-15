"""The public website's API (DECISIONS D83): drafts stay private until published, moved pages
redirect, leads drop spam silently, staff need the website permissions, and nothing private
(the lead address) is ever public."""

from __future__ import annotations

import base64
import io
import secrets
import uuid

from PIL import Image
from sqlalchemy import text

from tests.api.test_admin import platform

PAGE = {
    "kind": "page",
    "locale": "en",
    "slug": "",
    "content": {
        "title": "Run your hotel from one place",
        "seo": {"description": "Guest tablets, kitchen displays and billing."},
        "blocks": [
            {
                "type": "hero",
                "heading": "Run your hotel from one place",
                "primary": {"label": "Start", "href": "/signup"},
            },
            {"type": "faq", "items": [{"question": "Is there a trial?", "answer": "Yes."}]},
        ],
    },
}


def _png() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (600, 400), (30, 127, 216)).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


async def _editor(factory) -> dict[str, str]:
    return await platform(factory, "platform_website_editor")


async def test_public_settings_never_show_the_lead_address(client):
    r = await client.get("/site/settings")
    assert r.status_code == 200
    body = r.json()
    assert "lead_email" not in body and body["default_locale"] == "en"
    assert r.headers["cache-control"].startswith("public")


async def test_only_website_staff_edit(client, factory):
    support = await platform(factory, "platform_support")
    assert (await client.get("/admin/site/entries", headers=support)).status_code == 403
    hotel = await factory.hotel(roles=("hotel_owner",))
    owner = await factory.auth(hotel, "hotel_owner")
    assert (await client.post("/admin/site/entries", json=PAGE, headers=owner)).status_code == 403


async def test_a_page_is_private_until_published_and_moves_with_a_redirect(client, factory, owner_engine):
    editor = await _editor(factory)
    slug = f"pricing-{secrets.token_hex(3)}"
    created = await client.post("/admin/site/entries", json={**PAGE, "slug": slug}, headers=editor)
    assert created.status_code == 201, created.text
    entry = created.json()
    assert entry["status"] == "draft"
    public = {"kind": "page", "locale": "en", "slug": slug}
    assert (await client.get("/site/entry", params=public)).status_code == 404

    preview = (await client.post(f"/admin/site/entries/{entry['id']}/preview", headers=editor)).json()
    token = preview["url"].split("token=", 1)[1]
    draft = await client.get("/site/preview", params={"token": token})
    assert draft.status_code == 200 and draft.json()["preview"] is True

    published = await client.post(f"/admin/site/entries/{entry['id']}/publish", headers=editor)
    assert published.status_code == 200, published.text
    live = await client.get("/site/entry", params=public)
    assert live.status_code == 200 and live.json()["content"]["title"] == PAGE["content"]["title"]
    assert any(e["path"] == f"/{slug}" for e in (await client.get("/site/sitemap")).json()["data"])

    moved = f"{slug}-new"
    patch = await client.patch(f"/admin/site/entries/{entry['id']}", json={"slug": moved}, headers=editor)
    assert patch.status_code == 200, patch.text
    redirects = (await client.get("/site/redirects")).json()["data"]
    assert any(r["from_path"] == f"/{slug}" and r["to_path"] == f"/{moved}" for r in redirects)

    versions = (await client.get(f"/admin/site/entries/{entry['id']}/versions", headers=editor)).json()[
        "data"
    ]
    assert versions and versions[0]["version"] >= 1

    # A published entry is unpublished before it can be deleted.
    assert (await client.delete(f"/admin/site/entries/{entry['id']}", headers=editor)).status_code == 409
    off = await client.post(f"/admin/site/entries/{entry['id']}/unpublish", headers=editor)
    assert off.status_code == 200 and off.json()["status"] == "draft", off.text
    assert (await client.delete(f"/admin/site/entries/{entry['id']}", headers=editor)).status_code == 204


async def test_leads_drop_spam_silently_and_keep_real_requests(client, factory, owner_engine, mailbox):
    lead = {
        "kind": "demo",
        "name": "Ayanda",
        "email": f"ayanda.{secrets.token_hex(3)}@example.com",
        "company": "Coastline Lodge",
        "rooms": 18,
        "country": "ZA",
        "locale": "en",
        "consent": True,
        "consent_text": "You may contact me about Diyneco.",
        "elapsed_ms": 9000,
    }
    for spam in ({**lead, "website": "http://spam"}, {**lead, "elapsed_ms": 500}):
        assert (await client.post("/site/leads", json=spam)).status_code == 202
    assert (await client.post("/site/leads", json=lead)).status_code == 202
    async with owner_engine.connect() as conn:
        n = (
            await conn.execute(
                text("SELECT count(*) FROM app.site_leads WHERE email = :e"), {"e": lead["email"]}
            )
        ).scalar_one()
    assert n == 1  # the two spam sends were accepted and dropped
    assert any(m.template == "site_lead" for m in mailbox.sent)

    sales = await platform(factory, "platform_website_editor")
    listed = (await client.get("/admin/site/leads", headers=sales)).json()["data"]
    mine = next(x for x in listed if x["email"] == lead["email"])
    done = await client.patch(f"/admin/site/leads/{mine['id']}", json={"status": "contacted"}, headers=sales)
    assert done.json()["status"] == "contacted"
    assert (await client.delete(f"/admin/site/leads/{mine['id']}", headers=sales)).status_code == 204


async def test_images_are_re_encoded_and_served_at_fixed_addresses(client, factory):
    editor = await _editor(factory)
    up = await client.post(
        "/admin/site/media",
        json={"filename": "lobby.png", "alt": "The lobby", "data_base64": _png()},
        headers=editor,
    )
    assert up.status_code == 201, up.text
    media = up.json()
    assert media["width"] == 600 and 480 in media["widths"]
    r = await client.get(f"/site/media/{media['id']}/480.webp")
    assert r.status_code == 200 and r.headers["content-type"] == "image/webp"
    assert "immutable" in r.headers["cache-control"]
    assert (await client.get(f"/site/media/{media['id']}/123.webp")).status_code == 404


async def test_a_photo_gallery_shows_hotels_by_area_and_keeps_its_photos(client, factory):
    editor = await _editor(factory)
    up = await client.post(
        "/admin/site/media",
        json={"filename": "kitchen.png", "alt": "A kitchen display in use", "data_base64": _png()},
        headers=editor,
    )
    photo = up.json()["id"]
    slug = f"gallery-{secrets.token_hex(3)}"
    gallery = {
        "type": "gallery",
        "heading": "Diyneco in hotels",
        "items": [
            {"image_id": photo, "caption": "Orders on the kitchen display", "category": "kitchen"},
        ],
    }
    page = {**PAGE, "slug": slug, "content": {**PAGE["content"], "blocks": [gallery]}}
    missing = {
        **page,
        "content": {**page["content"], "blocks": [{**gallery, "items": [{"image_id": str(uuid.uuid4())}]}]},
    }
    assert (await client.post("/admin/site/entries", json=missing, headers=editor)).status_code == 400
    wrong_area = {
        **page,
        "content": {
            **page["content"],
            "blocks": [{**gallery, "items": [{"image_id": photo, "category": "garage"}]}],
        },
    }
    assert (await client.post("/admin/site/entries", json=wrong_area, headers=editor)).status_code == 400

    created = (await client.post("/admin/site/entries", json=page, headers=editor)).json()
    await client.post(f"/admin/site/entries/{created['id']}/publish", headers=editor)
    live = (await client.get("/site/entry", params={"kind": "page", "locale": "en", "slug": slug})).json()
    assert live["content"]["blocks"][0]["items"][0]["category"] == "kitchen"
    assert photo in live["media"] and live["media"][photo]["alt"] == "A kitchen display in use"
    # A photo a page uses cannot be deleted.
    assert (await client.delete(f"/admin/site/media/{photo}", headers=editor)).status_code == 409


async def test_page_views_are_counted_without_identifying_anyone(client, factory, owner_engine):
    browser = {"user-agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/130"}
    path = f"/views-{secrets.token_hex(3)}"
    for _ in range(2):
        assert (
            await client.post("/site/views", json={"path": path, "locale": "en"}, headers=browser)
        ).status_code == 204
    bot = {"user-agent": "Googlebot/2.1"}
    await client.post("/site/views", json={"path": path, "locale": "en"}, headers=bot)
    async with owner_engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT sum(views), sum(visitors) FROM app.site_page_views WHERE path = :p"), {"p": path}
            )
        ).one()
    assert tuple(row) == (2, 1)  # one visitor, two views; the bot is not counted
    stats = (await client.get("/admin/site/analytics", headers=await _editor(factory))).json()
    assert stats["views"] >= 2
