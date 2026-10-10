"""Menu photos: the worker makes three WebP sizes, drops metadata and refuses non-images (D64)."""

from __future__ import annotations

import io

import pytest
from PIL import Image
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.services import images
from tests.api.test_menu import _category, _item
from tests.api.test_onboarding import _path


def photo(width: int = 2000, height: int = 1000, fmt: str = "JPEG", gps: bool = True) -> bytes:
    img = Image.new("RGB", (width, height), (200, 80, 40))
    buf = io.BytesIO()
    exif = Image.Exif()
    if gps:
        exif[0x8825] = {1: "S", 2: (33.0, 55.0, 0.0)}  # GPSInfo: a camera location
    img.save(buf, fmt, exif=exif.tobytes() if fmt == "JPEG" else b"")
    return buf.getvalue()


def test_variants_are_webp_at_three_widths_without_metadata():
    out = images.make_variants(photo())
    assert sorted(out) == [160, 480, 1200]
    for width, data in out.items():
        with Image.open(io.BytesIO(data)) as img:
            assert img.format == "WEBP" and img.width == width and img.height == width // 2
            assert not img.getexif() and "exif" not in img.info


def test_small_photos_are_not_enlarged():
    out = images.make_variants(photo(300, 200, gps=False))
    with Image.open(io.BytesIO(out[1200])) as img:
        assert img.width == 300


@pytest.mark.parametrize(
    "data",
    [b"not an image", b"<svg onload=alert(1)>", photo(50, 50, fmt="PNG", gps=False), photo(40, 40)[:200]],
)
def test_non_photos_are_refused(data):
    with pytest.raises(images.InvalidImage):
        images.make_variants(data)


def test_served_path():
    assert images.served_path(None, None) is None
    assert images.served_path("a/b.jpg", None) == "a/b.jpg"
    assert images.served_path("a/b.jpg", {"source": "a/old.jpg", "480": "x"}) == "a/b.jpg"
    assert images.served_path("a/b.jpg", {"source": "a/b.jpg", "480": "a/b-480.webp"}) == "a/b-480.webp"
    assert images.served_path("a/b.jpg", {"source": "a/b.jpg", "error": "invalid"}) is None


async def test_worker_resizes_an_uploaded_photo(client, factory, worker_engine, app_state, owner_engine):
    hotel = await factory.hotel(rooms=0)
    gm = await factory.auth(hotel, "general_manager")
    cat = await _category(client, gm)
    item = await _item(client, gm, hotel, cat["id"])
    data = photo()
    start = await client.post(
        f"/menu/items/{item['id']}/image",
        json={"content_type": "image/jpeg", "size_bytes": len(data)},
        headers=gm,
    )
    assert start.status_code == 200, start.text
    up = start.json()
    assert (await client.put(_path(up["upload_url"]), content=data, headers=up["headers"])).status_code == 204

    maker = async_sessionmaker(worker_engine, expire_on_commit=False)
    assert (
        await images.process_pending(maker, app_state.storage, app_state.settings.storage_bucket_assets) >= 1
    )
    url = (await client.get(f"/menu/items/{item['id']}", headers=gm)).json()["image_url"]
    served = await client.get(_path(url))
    with Image.open(io.BytesIO(served.content)) as img:
        assert img.format == "WEBP" and img.width == 480

    # A file that is not a photo is never shown to guests.
    start = await client.post(
        f"/menu/items/{item['id']}/image", json={"content_type": "image/jpeg", "size_bytes": 20}, headers=gm
    )
    up = start.json()
    await client.put(_path(up["upload_url"]), content=b"<html>not a photo</html>", headers=up["headers"])
    await images.process_pending(maker, app_state.storage, app_state.settings.storage_bucket_assets)
    assert (await client.get(f"/menu/items/{item['id']}", headers=gm)).json()["image_url"] is None
    async with owner_engine.connect() as conn:
        variants = (
            await conn.execute(
                text("SELECT image_variants FROM app.menu_items WHERE id = :i"), {"i": item["id"]}
            )
        ).scalar_one()
    assert variants["error"] == "invalid"
