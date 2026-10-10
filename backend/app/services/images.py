"""Menu photo processing (API spec: "server makes 3 sizes"; DECISIONS D64).

Staff upload a photo straight to storage through a signed URL, so the API never sees the bytes.
The worker then fetches each new photo, decodes it with Pillow (refusing anything that is not a
real JPEG or WebP, and oversized "decompression bombs"), drops all metadata such as camera GPS
by re-encoding, and writes WebP copies 160, 480 and 1200 pixels wide (never enlarged). Menus
serve the 480 copy; until it exists they serve the original.
"""

from __future__ import annotations

import io
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import PurePosixPath
from typing import Any

from PIL import Image, ImageOps
from sqlalchemy import text

from app.db.session import set_tenant
from app.integrations.storage import Storage

log = logging.getLogger("diyneco.images")

WIDTHS = (160, 480, 1200)
SERVED_WIDTH = "480"
MAX_PIXELS = 40_000_000  # about 6300 x 6300; larger files are refused, not decoded
GIVE_UP_AFTER = timedelta(days=1)  # an upload URL that was never used
BATCH = 20

Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class InvalidImage(ValueError):
    pass


def make_variants(data: bytes) -> dict[int, bytes]:
    """WebP copies at each width; raises InvalidImage for anything that is not a usable photo."""
    try:
        with Image.open(io.BytesIO(data)) as probe:
            if probe.format not in ("JPEG", "WEBP"):
                raise InvalidImage(f"unsupported format {probe.format}")
            probe.verify()
        with Image.open(io.BytesIO(data)) as opened:
            # Keep the photo upright once EXIF is dropped.
            img: Image.Image = ImageOps.exif_transpose(opened).convert("RGB")
            out: dict[int, bytes] = {}
            for width in WIDTHS:
                copy = img.copy()
                if copy.width > width:
                    height = round(width * copy.height / copy.width) or 1
                    copy.thumbnail((width, height), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                copy.save(buf, "WEBP", quality=82, method=4)  # no exif/icc passed: metadata dropped
                out[width] = buf.getvalue()
            return out
    except InvalidImage:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise InvalidImage("image too large") from exc
    except Exception as exc:
        raise InvalidImage(str(exc)[:200]) from exc


def variant_key(source: str, width: int) -> str:
    p = PurePosixPath(source)
    return str(p.with_name(f"{p.stem}-{width}.webp"))


async def process_pending(sessionmaker: Any, storage: Storage, bucket: str) -> int:
    """One pass over every hotel; returns the number of photos processed."""
    async with sessionmaker() as s, s.begin():
        hotels = [r[0] for r in (await s.execute(text("SELECT hotel_id FROM app.hotels_for_jobs()"))).all()]
    done = 0
    for hotel_id in hotels:
        done += await _process_hotel(sessionmaker, storage, bucket, hotel_id)
    return done


async def _process_hotel(sessionmaker: Any, storage: Storage, bucket: str, hotel_id: uuid.UUID) -> int:
    async with sessionmaker() as s, s.begin():
        await set_tenant(s, hotel_id)
        rows = (
            await s.execute(
                text(
                    "SELECT id, image_path, updated_at FROM app.menu_items WHERE hotel_id = :h "
                    "AND image_path IS NOT NULL "
                    "AND (image_variants IS NULL OR image_variants->>'source' IS DISTINCT FROM image_path) "
                    "ORDER BY updated_at LIMIT :n"
                ),
                {"h": hotel_id, "n": BATCH},
            )
        ).all()
    done = 0
    for item_id, source, updated_at in rows:
        try:
            original = await storage.get(bucket, source)
        except Exception:
            if datetime.now(UTC) - updated_at > GIVE_UP_AFTER:
                await _record(sessionmaker, hotel_id, item_id, source, {"source": source, "error": "missing"})
            continue
        try:
            variants = make_variants(original)
        except InvalidImage as exc:
            log.warning("menu photo refused", extra={"item_id": str(item_id), "problem": str(exc)})
            await _record(sessionmaker, hotel_id, item_id, source, {"source": source, "error": "invalid"})
            continue
        keys: dict[str, str] = {"source": source}
        for width, data in variants.items():
            key = variant_key(source, width)
            try:
                await storage.put(bucket, key, data, "image/webp")
            except Exception:
                log.info("menu photo variant already stored", extra={"key": key})
            keys[str(width)] = key
        await _record(sessionmaker, hotel_id, item_id, source, keys)
        done += 1
    return done


async def _record(
    sessionmaker: Any, hotel_id: uuid.UUID, item_id: uuid.UUID, source: str, value: dict[str, str]
) -> None:
    """Stores the result unless staff replaced the photo meanwhile (then the new one is next)."""
    async with sessionmaker() as s, s.begin():
        await set_tenant(s, hotel_id)
        await s.execute(
            text(
                "UPDATE app.menu_items SET image_variants = CAST(:v AS jsonb) "
                "WHERE hotel_id = :h AND id = :i AND image_path = :p"
            ),
            {"v": json.dumps(value), "h": hotel_id, "i": item_id, "p": source},
        )


def served_path(image_path: str | None, variants: dict[str, str] | None) -> str | None:
    """What menus show: the 480 copy when made, nothing for a refused file, else the original."""
    if not image_path:
        return None
    if variants and variants.get("source") == image_path:
        if "error" in variants:
            return None
        return variants.get(SERVED_WIDTH, image_path)
    return image_path
