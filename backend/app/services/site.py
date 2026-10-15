"""The public website (DECISIONS D83).

- Pages and posts per language. Editing changes the draft; publishing copies it to the live
  version and records it in site_entry_versions. Changing the address of a published entry
  adds a permanent redirect from the old address, so links and search rankings survive.
- Addresses: the default language has no prefix (`/pricing`, `/blog/<slug>`); others do
  (`/af/pricing`, `/af/blog/<slug>`). Entries sharing a translation_key are the same page in
  several languages and are announced to search engines as alternates (hreflang).
- Images are decoded and re-encoded on the server (JPEG, PNG or WebP in; WebP out, metadata
  dropped, several widths) and served from the API at addresses that never change.
- Leads: a filled honeypot or a form sent in under 3 seconds is accepted silently and
  dropped; 5 leads per address per hour. Each lead is emailed to the lead address. The
  sender gets no automatic email, so the form cannot be used to send mail to strangers.
- Page views are counted per day, path, language and referring site. A visitor is counted
  once a day by a hash of a daily random salt, the address and the browser, held only in
  memory and forgotten at midnight; nothing that identifies a person is stored.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import logging
import re
import secrets
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit

import httpx
from PIL import Image, ImageOps
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError

from app.audit.writer import write_platform_audit
from app.core.errors import AppError
from app.core.logging import security_event
from app.core.state import AppState
from app.db.session import UnitOfWork
from app.models.site import (
    SiteEntry,
    SiteEntryVersion,
    SiteLead,
    SiteMedia,
    SitePageView,
    SiteRedirect,
    SiteSettings,
)
from app.models.tenancy import User
from app.schemas.site import EntryContent

log = logging.getLogger("diyneco.site")

PREVIEW_TTL_S = 15 * 60
MEDIA_BUCKET_PREFIX = "site"
MEDIA_WIDTHS = (480, 960, 1600, 2400)
MEDIA_MAX_BYTES = 6 * 1024 * 1024
MEDIA_MAX_PIXELS = 40_000_000
LEAD_MIN_MS = 3000
LEAD_LIMIT = 5
ENTRY_LIMIT = 500
_BOT = re.compile(r"bot|crawl|spider|slurp|preview|monitor|headless|lighthouse|curl|wget|python", re.I)
_REF_KEYS = ("image_id", "cover_id", "default_image_id", "organization_logo_id")


def _field_error(field: str, problem: str) -> AppError:
    return AppError(
        "VALIDATION_FAILED",
        problem,
        details={"fields": [{"field": field, "problem": problem, "type": "value_error"}]},
    )


# --- Addresses and media references ------------------------------------------------------


def path_for(kind: str, locale: str, slug: str, default_locale: str) -> str:
    prefix = "" if locale == default_locale else f"/{locale}"
    if kind == "post":
        return f"{prefix}/blog/{slug}"
    return f"{prefix}/{slug}" if slug else (prefix or "/")


def media_refs(value: Any) -> set[uuid.UUID]:
    """Every image id the content or settings refer to."""
    found: set[uuid.UUID] = set()
    if isinstance(value, dict):
        for k, v in value.items():
            if k in _REF_KEYS and v:
                found.add(uuid.UUID(str(v)))
            else:
                found |= media_refs(v)
    elif isinstance(value, list):
        for v in value:
            found |= media_refs(v)
    return found


def media_payload(st: AppState, m: SiteMedia) -> dict[str, Any]:
    base = f"{st.settings.api_base_url.rstrip('/')}/api/v1/site/media/{m.id}"
    widths = sorted(m.widths)
    return {
        "id": m.id,
        "filename": m.filename,
        "alt": m.alt,
        "width": m.width,
        "height": m.height,
        "widths": widths,
        "src": {str(w): f"{base}/{w}.webp" for w in widths},
        "url": f"{base}/{widths[-1]}.webp",
        "created_at": m.created_at,
    }


async def _media(st: AppState, uow: UnitOfWork, ids: set[uuid.UUID]) -> dict[str, dict[str, Any]]:
    if not ids:
        return {}
    rows = (
        await uow.session.execute(
            select(SiteMedia).where(SiteMedia.id.in_(ids), SiteMedia.deleted_at.is_(None))
        )
    ).scalars()
    return {str(m.id): media_payload(st, m) for m in rows}


async def _check_media(st: AppState, uow: UnitOfWork, value: Any) -> None:
    wanted = media_refs(value)
    found = await _media(st, uow, wanted)
    missing = sorted(str(i) for i in wanted if str(i) not in found)
    if missing:
        raise _field_error("content", f"An image was removed or does not exist: {missing[0]}.")


# --- Settings ------------------------------------------------------------------------------


async def _settings(uow: UnitOfWork, *, for_update: bool = False) -> SiteSettings:
    q = select(SiteSettings).where(SiteSettings.id == 1)
    if for_update:
        q = q.with_for_update()
    return (await uow.session.execute(q)).scalar_one()


def _settings_payload(s: SiteSettings) -> dict[str, Any]:
    return {
        "site_name": s.site_name,
        "base_url": s.base_url,
        "default_locale": s.default_locale,
        "locales": list(s.locales),
        "navigation": s.navigation,
        "footer": s.footer,
        "contact": s.contact,
        "social": s.social,
        "seo": s.seo,
        "verification": s.verification,
        "analytics": s.analytics,
        "lead_email": s.lead_email,
        "updated_at": s.updated_at,
    }


async def get_settings(uow: UnitOfWork) -> dict[str, Any]:
    return _settings_payload(await _settings(uow))


async def put_settings(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], values: dict[str, Any]
) -> dict[str, Any]:
    s = await _settings(uow, for_update=True)
    await _check_media(st, uow, values["seo"])
    before = _settings_payload(s)
    removed = set(s.locales) - set(values["locales"])
    if removed:
        live = (
            await uow.session.execute(
                select(func.count())
                .select_from(SiteEntry)
                .where(
                    SiteEntry.locale.in_(removed),
                    SiteEntry.published.is_not(None),
                    SiteEntry.deleted_at.is_(None),
                )
            )
        ).scalar_one()
        if live:
            raise _field_error(
                "locales", "Unpublish the pages in a language before switching the language off."
            )
    for k, v in values.items():
        setattr(s, k, v)
    s.updated_at = datetime.now(UTC)
    s.updated_by = actor["actor_id"]
    changed = sorted(k for k in values if before.get(k) != values[k])
    await write_platform_audit(
        uow.session,
        **actor,
        action="site.settings",
        entity_type="site_settings",
        entity_id=None,
        new_value={"changed": changed},
    )
    _revalidate_after_commit(st, uow, ["/"], everything=True)
    return _settings_payload(s)


async def public_settings(st: AppState, uow: UnitOfWork) -> dict[str, Any]:
    s = await _settings(uow)
    out = _settings_payload(s)
    out.pop("lead_email")
    out.pop("updated_at")
    out["media"] = await _media(st, uow, media_refs(s.seo))
    return out


# --- Entries -------------------------------------------------------------------------------


def _status(e: SiteEntry) -> str:
    if e.published is None:
        return "draft"
    return "published" if e.published == e.draft else "changed"


def _summary(e: SiteEntry) -> dict[str, Any]:
    return {
        "id": e.id,
        "kind": e.kind,
        "locale": e.locale,
        "slug": e.slug,
        "title": e.draft.get("title", ""),
        "translation_key": e.translation_key,
        "status": _status(e),
        "version": e.version,
        "published_at": e.published_at,
        "updated_at": e.updated_at,
    }


async def _entry(uow: UnitOfWork, entry_id: uuid.UUID, *, for_update: bool = False) -> SiteEntry:
    q = select(SiteEntry).where(SiteEntry.id == entry_id, SiteEntry.deleted_at.is_(None))
    if for_update:
        q = q.with_for_update()
    e = (await uow.session.execute(q)).scalar_one_or_none()
    if e is None:
        raise AppError("NOT_FOUND")
    return e


async def _translations(uow: UnitOfWork, e: SiteEntry) -> list[SiteEntry]:
    return list(
        (
            await uow.session.execute(
                select(SiteEntry).where(
                    SiteEntry.translation_key == e.translation_key,
                    SiteEntry.deleted_at.is_(None),
                    SiteEntry.id != e.id,
                )
            )
        ).scalars()
    )


async def _entry_out(uow: UnitOfWork, e: SiteEntry) -> dict[str, Any]:
    return {
        **_summary(e),
        "draft": e.draft,
        "published": e.published,
        "translations": [
            {"id": t.id, "locale": t.locale, "slug": t.slug, "status": _status(t)}
            for t in await _translations(uow, e)
        ],
    }


async def list_entries(
    uow: UnitOfWork, kind: str | None, locale: str | None, q: str | None
) -> list[dict[str, Any]]:
    query = select(SiteEntry).where(SiteEntry.deleted_at.is_(None))
    if kind:
        query = query.where(SiteEntry.kind == kind)
    if locale:
        query = query.where(SiteEntry.locale == locale)
    if q:
        like = f"%{q.lower()}%"
        query = query.where(
            func.lower(SiteEntry.slug).like(like) | func.lower(SiteEntry.draft["title"].astext).like(like)
        )
    rows = (
        await uow.session.execute(
            query.order_by(SiteEntry.kind, SiteEntry.locale, SiteEntry.slug).limit(ENTRY_LIMIT)
        )
    ).scalars()
    return [_summary(e) for e in rows]


async def get_entry(uow: UnitOfWork, entry_id: uuid.UUID) -> dict[str, Any]:
    return await _entry_out(uow, await _entry(uow, entry_id))


async def _locale_enabled(uow: UnitOfWork, locale: str) -> SiteSettings:
    s = await _settings(uow)
    if locale not in s.locales:
        raise _field_error("locale", "Switch this language on in the website settings first.")
    return s


async def _insert(uow: UnitOfWork, values: dict[str, Any]) -> SiteEntry:
    try:
        async with uow.session.begin_nested():
            e = SiteEntry(**values)
            uow.session.add(e)
            await uow.session.flush()
    except IntegrityError as exc:
        if "site_entries_translation" in str(exc.orig):
            raise _field_error("locale", "This page already has a version in that language.") from exc
        raise _field_error(
            "slug", "Another page or post in this language already uses that address."
        ) from exc
    await uow.session.refresh(e)
    return e


async def create_entry(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], body: dict[str, Any]
) -> dict[str, Any]:
    await _locale_enabled(uow, body["locale"])
    await _check_media(st, uow, body["content"])
    values: dict[str, Any] = {
        "kind": body["kind"],
        "locale": body["locale"],
        "slug": body["slug"],
        "draft": body["content"],
        "created_by": actor["actor_id"],
        "updated_by": actor["actor_id"],
    }
    if body.get("translation_of"):
        source = await _entry(uow, body["translation_of"])
        if source.kind != body["kind"]:
            raise _field_error("translation_of", "A translation is the same kind of entry as its original.")
        values["translation_key"] = source.translation_key
    e = await _insert(uow, values)
    await write_platform_audit(
        uow.session,
        **actor,
        action="site.entry_create",
        entity_type="site_entry",
        entity_id=e.id,
        new_value={"kind": e.kind, "locale": e.locale, "slug": e.slug},
    )
    return await _entry_out(uow, e)


async def update_entry(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], entry_id: uuid.UUID, changes: dict[str, Any]
) -> dict[str, Any]:
    e = await _entry(uow, entry_id, for_update=True)
    s = await _settings(uow)
    old_path = path_for(e.kind, e.locale, e.slug, s.default_locale)
    if "content" in changes and changes["content"] is not None:
        await _check_media(st, uow, changes["content"])
        e.draft = changes["content"]
    moved = changes.get("slug") is not None and changes["slug"] != e.slug
    if moved:
        if e.kind == "post" and not changes["slug"]:
            raise _field_error("slug", "A post needs an address.")
        if e.kind == "page" and e.slug == "":
            raise _field_error("slug", "The home page's address cannot change.")
        e.slug = changes["slug"]
    e.updated_by = actor["actor_id"]
    e.updated_at = datetime.now(UTC)
    try:
        async with uow.session.begin_nested():
            await uow.session.flush()
    except IntegrityError as exc:
        raise _field_error(
            "slug", "Another page or post in this language already uses that address."
        ) from exc
    if moved and e.published is not None:
        new_path = path_for(e.kind, e.locale, e.slug, s.default_locale)
        await uow.session.execute(
            text("DELETE FROM app.site_redirects WHERE from_path = :p"), {"p": new_path}
        )
        await uow.session.execute(
            text(
                "INSERT INTO app.site_redirects (from_path, to_path, permanent, created_by) "
                "VALUES (:f, :t, true, :u) ON CONFLICT (from_path) DO UPDATE SET to_path = EXCLUDED.to_path"
            ),
            {"f": old_path, "t": new_path, "u": actor["actor_id"]},
        )
        # Older redirects that pointed at the old address now go straight to the new one.
        await uow.session.execute(
            update(SiteRedirect).where(SiteRedirect.to_path == old_path).values(to_path=new_path)
        )
        _revalidate_after_commit(st, uow, [old_path, new_path])
    await write_platform_audit(
        uow.session,
        **actor,
        action="site.entry_edit",
        entity_type="site_entry",
        entity_id=e.id,
        new_value={"slug": e.slug} if moved else None,
    )
    return await _entry_out(uow, e)


async def publish_entry(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], entry_id: uuid.UUID
) -> dict[str, Any]:
    e = await _entry(uow, entry_id, for_update=True)
    s = await _locale_enabled(uow, e.locale)
    EntryContent.model_validate(e.draft)  # still valid under today's rules
    await _check_media(st, uow, e.draft)
    now = datetime.now(UTC)
    e.version += 1
    e.published = e.draft
    e.published_at = e.published_at or now
    e.republished_at = now
    uow.session.add(
        SiteEntryVersion(entry_id=e.id, version=e.version, content=e.draft, published_by=actor["actor_id"])
    )
    await uow.session.flush()
    await write_platform_audit(
        uow.session,
        **actor,
        action="site.publish",
        entity_type="site_entry",
        entity_id=e.id,
        new_value={"version": e.version, "locale": e.locale, "slug": e.slug},
    )
    _revalidate_after_commit(st, uow, _affected_paths(e, s))
    return await _entry_out(uow, e)


async def unpublish_entry(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], entry_id: uuid.UUID
) -> dict[str, Any]:
    e = await _entry(uow, entry_id, for_update=True)
    if e.published is None:
        raise AppError("INVALID_TRANSITION", "This is not published.")
    if e.kind == "page" and e.slug == "" and e.locale == (await _settings(uow)).default_locale:
        raise AppError("INVALID_TRANSITION", "The home page in the default language must stay published.")
    e.published = None
    e.updated_at = datetime.now(UTC)
    await uow.session.flush()
    await write_platform_audit(
        uow.session, **actor, action="site.unpublish", entity_type="site_entry", entity_id=e.id
    )
    _revalidate_after_commit(st, uow, _affected_paths(e, await _settings(uow)))
    return await _entry_out(uow, e)


async def delete_entry(st: AppState, uow: UnitOfWork, actor: dict[str, Any], entry_id: uuid.UUID) -> None:
    e = await _entry(uow, entry_id, for_update=True)
    if e.published is not None:
        raise AppError("INVALID_TRANSITION", "Unpublish it first.")
    e.deleted_at = datetime.now(UTC)
    await write_platform_audit(
        uow.session,
        **actor,
        action="site.entry_delete",
        entity_type="site_entry",
        entity_id=e.id,
        new_value={"slug": e.slug, "locale": e.locale},
    )


async def versions(uow: UnitOfWork, entry_id: uuid.UUID) -> list[dict[str, Any]]:
    await _entry(uow, entry_id)
    rows = (
        await uow.session.execute(
            select(SiteEntryVersion, User.name)
            .join(User, User.id == SiteEntryVersion.published_by, isouter=True)
            .where(SiteEntryVersion.entry_id == entry_id)
            .order_by(SiteEntryVersion.version.desc())
            .limit(50)
        )
    ).all()
    return [
        {"version": v.version, "published_at": v.published_at, "published_by": name, "content": v.content}
        for v, name in rows
    ]


async def restore_version(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], entry_id: uuid.UUID, version: int
) -> dict[str, Any]:
    e = await _entry(uow, entry_id, for_update=True)
    v = (
        await uow.session.execute(
            select(SiteEntryVersion).where(
                SiteEntryVersion.entry_id == entry_id, SiteEntryVersion.version == version
            )
        )
    ).scalar_one_or_none()
    if v is None:
        raise AppError("NOT_FOUND")
    content = EntryContent.model_validate(v.content).model_dump(mode="json")
    await _check_media(st, uow, content)
    e.draft = content
    e.updated_at = datetime.now(UTC)
    e.updated_by = actor["actor_id"]
    await write_platform_audit(
        uow.session,
        **actor,
        action="site.restore",
        entity_type="site_entry",
        entity_id=e.id,
        new_value={"version": version},
    )
    return await _entry_out(uow, e)


def preview_link(st: AppState, base_url: str, entry_id: uuid.UUID) -> dict[str, Any]:
    token, _ = st.jwt.sign("site_preview", {"sub": str(entry_id)}, PREVIEW_TTL_S)
    # The website's /preview page (apps/website) renders the draft behind the token (D88).
    return {"url": f"{base_url.rstrip('/')}/preview?token={token}", "expires_in": PREVIEW_TTL_S}


async def preview(st: AppState, uow: UnitOfWork, entry_id: uuid.UUID) -> dict[str, Any]:
    await _entry(uow, entry_id)
    return preview_link(st, (await _settings(uow)).base_url, entry_id)


# --- Public reads --------------------------------------------------------------------------


async def _alternates(uow: UnitOfWork, e: SiteEntry, default_locale: str) -> list[dict[str, str]]:
    rows = (
        await uow.session.execute(
            select(SiteEntry).where(
                SiteEntry.translation_key == e.translation_key,
                SiteEntry.published.is_not(None),
                SiteEntry.deleted_at.is_(None),
            )
        )
    ).scalars()
    return [
        {"locale": t.locale, "path": path_for(t.kind, t.locale, t.slug, default_locale)}
        for t in sorted(rows, key=lambda t: t.locale)
    ]


def _card(
    st: AppState, e: SiteEntry, default_locale: str, media: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    c = e.published or {}
    cover = media.get(str(c.get("cover_id"))) if c.get("cover_id") else None
    return {
        "slug": e.slug,
        "path": path_for("post", e.locale, e.slug, default_locale),
        "title": c.get("title", ""),
        "excerpt": c.get("excerpt"),
        "cover": cover,
        "author": c.get("author"),
        "tags": c.get("tags", []),
        "published_at": e.published_at,
    }


async def _posts(
    st: AppState,
    uow: UnitOfWork,
    locale: str,
    default_locale: str,
    limit: int,
    before: datetime | None,
    tag: str | None,
) -> list[dict[str, Any]]:
    q = select(SiteEntry).where(
        SiteEntry.kind == "post",
        SiteEntry.locale == locale,
        SiteEntry.published.is_not(None),
        SiteEntry.deleted_at.is_(None),
    )
    if before is not None:
        q = q.where(SiteEntry.published_at < before)
    if tag:
        q = q.where(SiteEntry.published["tags"].contains([tag]))
    rows = list((await uow.session.execute(q.order_by(SiteEntry.published_at.desc()).limit(limit))).scalars())
    media = await _media(
        st,
        uow,
        {uuid.UUID(str(c)) for e in rows if (c := (e.published or {}).get("cover_id"))},
    )
    return [_card(st, e, default_locale, media) for e in rows]


async def _render(
    st: AppState, uow: UnitOfWork, e: SiteEntry, content: dict[str, Any], s: SiteSettings, *, preview: bool
) -> dict[str, Any]:
    posts: list[dict[str, Any]] = []
    wanted = [b for b in content.get("blocks", []) if b.get("type") == "post_list"]
    if wanted:
        posts = await _posts(
            st, uow, e.locale, s.default_locale, max(b.get("limit", 3) for b in wanted), None, None
        )
    return {
        "kind": e.kind,
        "locale": e.locale,
        "slug": e.slug,
        "path": path_for(e.kind, e.locale, e.slug, s.default_locale),
        "content": content,
        "published_at": e.published_at,
        "updated_at": e.republished_at,
        "alternates": await _alternates(uow, e, s.default_locale),
        "media": await _media(st, uow, media_refs(content)),
        "posts": posts,
        "preview": preview,
    }


async def public_entry(st: AppState, uow: UnitOfWork, kind: str, locale: str, slug: str) -> dict[str, Any]:
    s = await _settings(uow)
    if locale not in s.locales:
        raise AppError("NOT_FOUND")
    e = (
        await uow.session.execute(
            select(SiteEntry).where(
                SiteEntry.kind == kind,
                SiteEntry.locale == locale,
                SiteEntry.slug == slug,
                SiteEntry.published.is_not(None),
                SiteEntry.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if e is None or e.published is None:
        raise AppError("NOT_FOUND")
    return await _render(st, uow, e, e.published, s, preview=False)


async def preview_entry(st: AppState, uow: UnitOfWork, token: str) -> dict[str, Any]:
    claims = st.jwt.verify(token, "site_preview", error_code="NOT_FOUND")
    e = await _entry(uow, uuid.UUID(str(claims["sub"])))
    return await _render(st, uow, e, e.draft, await _settings(uow), preview=True)


async def public_posts(
    st: AppState, uow: UnitOfWork, locale: str, limit: int, before: datetime | None, tag: str | None
) -> dict[str, Any]:
    s = await _settings(uow)
    if locale not in s.locales:
        raise AppError("NOT_FOUND")
    cards = await _posts(st, uow, locale, s.default_locale, limit + 1, before, tag)
    more = len(cards) > limit
    cards = cards[:limit]
    return {"data": cards, "next_cursor": cards[-1]["published_at"].isoformat() if more and cards else None}


async def sitemap(uow: UnitOfWork) -> list[dict[str, Any]]:
    s = await _settings(uow)
    rows = list(
        (
            await uow.session.execute(
                select(SiteEntry).where(
                    SiteEntry.published.is_not(None),
                    SiteEntry.deleted_at.is_(None),
                    SiteEntry.locale.in_(s.locales),
                )
            )
        ).scalars()
    )
    groups: dict[uuid.UUID, list[SiteEntry]] = {}
    for e in rows:
        groups.setdefault(e.translation_key, []).append(e)
    out = []
    for e in rows:
        if (e.published or {}).get("seo", {}).get("noindex"):
            continue
        alternates = [
            {"locale": t.locale, "path": path_for(t.kind, t.locale, t.slug, s.default_locale)}
            for t in sorted(groups[e.translation_key], key=lambda t: t.locale)
        ]
        out.append(
            {
                "path": path_for(e.kind, e.locale, e.slug, s.default_locale),
                "locale": e.locale,
                "kind": e.kind,
                "updated_at": e.republished_at or e.updated_at,
                "alternates": alternates,
            }
        )
    return sorted(out, key=lambda r: r["path"])


# --- Redirects -----------------------------------------------------------------------------


def _redirect_payload(r: SiteRedirect) -> dict[str, Any]:
    return {
        "id": r.id,
        "from_path": r.from_path,
        "to_path": r.to_path,
        "permanent": r.permanent,
        "created_at": r.created_at,
    }


async def list_redirects(uow: UnitOfWork) -> list[dict[str, Any]]:
    rows = (
        await uow.session.execute(select(SiteRedirect).order_by(SiteRedirect.from_path).limit(2000))
    ).scalars()
    return [_redirect_payload(r) for r in rows]


async def create_redirect(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], body: dict[str, Any]
) -> dict[str, Any]:
    if body["from_path"].rstrip("/") == body["to_path"].rstrip("/"):
        raise _field_error("to_path", "A redirect cannot point at itself.")
    loop = (
        await uow.session.execute(select(SiteRedirect.id).where(SiteRedirect.from_path == body["to_path"]))
    ).first()
    if loop is not None:
        raise _field_error("to_path", "That address redirects too; point at its final address.")
    try:
        async with uow.session.begin_nested():
            r = SiteRedirect(**body, created_by=actor["actor_id"])
            uow.session.add(r)
            await uow.session.flush()
    except IntegrityError as exc:
        raise _field_error("from_path", "That address already redirects.") from exc
    await uow.session.refresh(r)
    await write_platform_audit(
        uow.session,
        **actor,
        action="site.redirect_create",
        entity_type="site_redirect",
        entity_id=r.id,
        new_value={"from": r.from_path, "to": r.to_path},
    )
    _revalidate_after_commit(st, uow, [], everything=True)
    return _redirect_payload(r)


async def delete_redirect(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], redirect_id: uuid.UUID
) -> None:
    r = (
        await uow.session.execute(select(SiteRedirect).where(SiteRedirect.id == redirect_id))
    ).scalar_one_or_none()
    if r is None:
        raise AppError("NOT_FOUND")
    await uow.session.delete(r)
    await write_platform_audit(
        uow.session,
        **actor,
        action="site.redirect_delete",
        entity_type="site_redirect",
        entity_id=redirect_id,
        new_value={"from": r.from_path},
    )
    _revalidate_after_commit(st, uow, [], everything=True)


# --- Media ---------------------------------------------------------------------------------


def _bucket(st: AppState) -> str:
    return st.settings.storage_bucket_assets


def encode_image(data: bytes) -> tuple[int, int, dict[int, bytes]]:
    """Width, height and WebP copies; raises AppError for anything that is not a usable image."""
    Image.MAX_IMAGE_PIXELS = MEDIA_MAX_PIXELS
    try:
        with Image.open(io.BytesIO(data)) as probe:
            if probe.format not in ("JPEG", "PNG", "WEBP"):
                raise _field_error("data_base64", "Upload a JPEG, PNG or WebP image.")
            probe.verify()
        with Image.open(io.BytesIO(data)) as opened:
            img = ImageOps.exif_transpose(opened)
            img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
            out: dict[int, bytes] = {}
            for width in MEDIA_WIDTHS:
                if width > img.width and out:
                    break
                copy = img.copy()
                if copy.width > width:
                    copy.thumbnail(
                        (width, round(width * copy.height / copy.width) or 1), Image.Resampling.LANCZOS
                    )
                buf = io.BytesIO()
                copy.save(buf, "WEBP", quality=84, method=4)  # no exif/icc: metadata dropped
                out[min(width, img.width)] = buf.getvalue()
            return img.width, img.height, out
    except AppError:
        raise
    except (Image.DecompressionBombError, OSError, ValueError, SyntaxError) as exc:
        raise _field_error("data_base64", "That file is not an image we can use.") from exc


async def upload_media(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], body: dict[str, Any]
) -> dict[str, Any]:
    try:
        data = base64.b64decode(body["data_base64"], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise _field_error("data_base64", "The file could not be read.") from exc
    if len(data) > MEDIA_MAX_BYTES:
        raise _field_error("data_base64", "Images must be 6 MB or smaller.")
    width, height, copies = encode_image(data)
    media_id = uuid.uuid4()
    key = f"{MEDIA_BUCKET_PREFIX}/{media_id}"
    for w, blob in copies.items():
        await st.storage.put(_bucket(st), f"{key}/{w}.webp", blob, "image/webp")
    m = SiteMedia(
        id=media_id,
        filename=body["filename"],
        alt=body.get("alt", ""),
        width=width,
        height=height,
        widths=sorted(copies),
        bytes=sum(len(b) for b in copies.values()),
        storage_key=key,
        uploaded_by=actor["actor_id"],
    )
    uow.session.add(m)
    await uow.session.flush()
    await uow.session.refresh(m)
    await write_platform_audit(
        uow.session,
        **actor,
        action="site.media_upload",
        entity_type="site_media",
        entity_id=m.id,
        new_value={"filename": m.filename, "width": width, "height": height},
    )
    return media_payload(st, m)


async def list_media(st: AppState, uow: UnitOfWork) -> list[dict[str, Any]]:
    rows = (
        await uow.session.execute(
            select(SiteMedia)
            .where(SiteMedia.deleted_at.is_(None))
            .order_by(SiteMedia.created_at.desc())
            .limit(500)
        )
    ).scalars()
    return [media_payload(st, m) for m in rows]


async def _live_media(uow: UnitOfWork, media_id: uuid.UUID) -> SiteMedia:
    m = (
        await uow.session.execute(
            select(SiteMedia).where(SiteMedia.id == media_id, SiteMedia.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if m is None:
        raise AppError("NOT_FOUND")
    return m


async def update_media(
    st: AppState, uow: UnitOfWork, actor: dict[str, Any], media_id: uuid.UUID, alt: str
) -> dict[str, Any]:
    m = await _live_media(uow, media_id)
    m.alt = alt
    await write_platform_audit(
        uow.session, **actor, action="site.media_alt", entity_type="site_media", entity_id=m.id
    )
    return media_payload(st, m)


async def delete_media(uow: UnitOfWork, actor: dict[str, Any], media_id: uuid.UUID) -> None:
    m = await _live_media(uow, media_id)
    used = (
        await uow.session.execute(
            text(
                "SELECT 1 FROM app.site_entries WHERE deleted_at IS NULL "
                "AND (draft::text LIKE :p OR coalesce(published::text, '') LIKE :p) "
                "UNION ALL SELECT 1 FROM app.site_settings WHERE seo::text LIKE :p LIMIT 1"
            ),
            {"p": f"%{media_id}%"},
        )
    ).first()
    if used is not None:
        raise AppError("INVALID_TRANSITION", "A page, post or the site settings still use this image.")
    m.deleted_at = datetime.now(UTC)
    await write_platform_audit(
        uow.session, **actor, action="site.media_delete", entity_type="site_media", entity_id=m.id
    )


async def media_bytes(st: AppState, uow: UnitOfWork, media_id: uuid.UUID, width: int) -> bytes:
    m = await _live_media(uow, media_id)
    if width not in m.widths:
        raise AppError("NOT_FOUND")
    return await st.storage.get(_bucket(st), f"{m.storage_key}/{width}.webp")


# --- Leads ---------------------------------------------------------------------------------


def _lead_payload(lead: SiteLead) -> dict[str, Any]:
    return {
        "id": lead.id,
        "kind": lead.kind,
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "company": lead.company,
        "rooms": lead.rooms,
        "country": lead.country,
        "message": lead.message,
        "locale": lead.locale,
        "source_path": lead.source_path,
        "consent_text": lead.consent_text,
        "status": lead.status,
        "notes": lead.notes,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
    }


async def create_lead(st: AppState, uow: UnitOfWork, body: dict[str, Any], ip: str | None) -> None:
    if body.get("website") or body["elapsed_ms"] < LEAD_MIN_MS:
        security_event("site.lead_dropped", reason="honeypot" if body.get("website") else "too_fast", ip=ip)
        return  # answered like a success, so a bot learns nothing
    decision = await st.limiter.hit("site_lead", ip or "unknown")
    if not decision.allowed:
        raise AppError("RATE_LIMITED", "Too many requests from this address. Try again later or email us.")
    s = await _settings(uow)
    lead = SiteLead(
        kind=body["kind"],
        name=body["name"],
        email=body["email"],
        phone=body.get("phone") or None,
        company=body.get("company") or None,
        rooms=body.get("rooms"),
        country=body.get("country"),
        message=body.get("message") or None,
        locale=body["locale"],
        source_path=body.get("source_path"),
        consent_text=body["consent_text"],
    )
    uow.session.add(lead)
    await uow.session.flush()
    lines = [
        f"{'Demo request' if lead.kind == 'demo' else 'Message'} from the website.",
        "",
        f"Name: {lead.name}",
        f"Email: {lead.email}",
        *([f"Phone: {lead.phone}"] if lead.phone else []),
        *([f"Hotel or company: {lead.company}"] if lead.company else []),
        *([f"Rooms: {lead.rooms}"] if lead.rooms else []),
        *([f"Country: {lead.country}"] if lead.country else []),
        f"Language: {lead.locale}",
        *([f"Page: {lead.source_path}"] if lead.source_path else []),
        "",
        lead.message or "(no message)",
        "",
        "Follow it up in the Admin panel under Website > Leads.",
    ]
    what = "demo request" if lead.kind == "demo" else "website message"
    await st.mailer.queue(
        uow,
        hotel_id=None,
        template="site_lead",
        to=s.lead_email,
        subject=f"New {what}: {lead.company or lead.name}",
        body="\n".join(lines),
        subject_ref={"site_lead": str(lead.id)},
    )


async def list_leads(
    uow: UnitOfWork, status: str | None, kind: str | None, before: datetime | None, limit: int
) -> dict[str, Any]:
    q = select(SiteLead)
    if status:
        q = q.where(SiteLead.status == status)
    if kind:
        q = q.where(SiteLead.kind == kind)
    if before is not None:
        q = q.where(SiteLead.created_at < before)
    rows = list(
        (await uow.session.execute(q.order_by(SiteLead.created_at.desc()).limit(limit + 1))).scalars()
    )
    more = len(rows) > limit
    rows = rows[:limit]
    return {
        "data": [_lead_payload(r) for r in rows],
        "next_cursor": rows[-1].created_at.isoformat() if more and rows else None,
    }


async def _lead(uow: UnitOfWork, lead_id: uuid.UUID) -> SiteLead:
    lead = (
        await uow.session.execute(select(SiteLead).where(SiteLead.id == lead_id).with_for_update())
    ).scalar_one_or_none()
    if lead is None:
        raise AppError("NOT_FOUND")
    return lead


async def update_lead(
    uow: UnitOfWork, actor: dict[str, Any], lead_id: uuid.UUID, changes: dict[str, Any]
) -> dict[str, Any]:
    lead = await _lead(uow, lead_id)
    if changes.get("status"):
        lead.status = changes["status"]
    if "notes" in changes:
        lead.notes = changes["notes"]
    lead.handled_by = actor["actor_id"]
    await uow.session.flush()
    await uow.session.refresh(lead)
    await write_platform_audit(
        uow.session,
        **actor,
        action="site.lead_update",
        entity_type="site_lead",
        entity_id=lead.id,
        new_value={"status": lead.status},
    )
    return _lead_payload(lead)


async def erase_lead(uow: UnitOfWork, actor: dict[str, Any], lead_id: uuid.UUID) -> None:
    """A person asked to be forgotten (POPIA): the lead is deleted; the audit keeps only that
    a lead was erased, never who it was."""
    lead = await _lead(uow, lead_id)
    await uow.session.delete(lead)
    await write_platform_audit(
        uow.session, **actor, action="site.lead_erase", entity_type="site_lead", entity_id=lead_id
    )


# --- Page views ----------------------------------------------------------------------------


class _Visitors:
    """Distinct visitors per day, in memory only. The salt is random each day and never stored,
    so yesterday's hashes cannot be recomputed. Several API instances each count separately,
    which can only over-count; the numbers are a trend, not an audit."""

    MAX = 200_000

    def __init__(self) -> None:
        self.day: date | None = None
        self.salt = b""
        self.seen: set[bytes] = set()

    def first_visit(self, today: date, *parts: str) -> bool:
        if today != self.day:
            self.day, self.salt, self.seen = today, secrets.token_bytes(32), set()
        key = hashlib.sha256(self.salt + "\x00".join(parts).encode()).digest()[:16]
        if key in self.seen:
            return False
        if len(self.seen) < self.MAX:
            self.seen.add(key)
        return True


_visitors = _Visitors()


def _referrer_host(referrer: str, own_host: str) -> str:
    host = (urlsplit(referrer).hostname or "").lower().removeprefix("www.") if referrer else ""
    return "" if not host or host == own_host else host[:200]


async def record_view(uow: UnitOfWork, body: dict[str, Any], ip: str | None, user_agent: str | None) -> None:
    if not user_agent or _BOT.search(user_agent):
        return
    s = await _settings(uow)
    if s.analytics.get("provider") != "builtin" or body["locale"] not in s.locales:
        return
    path = body["path"].split("?")[0].split("#")[0][:300] or "/"
    today = datetime.now(UTC).date()
    own = (urlsplit(s.base_url).hostname or "").lower().removeprefix("www.")
    new = _visitors.first_visit(today, ip or "", user_agent)
    await uow.session.execute(
        text(
            "INSERT INTO app.site_page_views (day, path, locale, referrer, views, visitors) "
            "VALUES (:d, :p, :l, :r, 1, :v) "
            "ON CONFLICT (day, path, locale, referrer) DO UPDATE SET "
            "views = app.site_page_views.views + 1, visitors = app.site_page_views.visitors + :v"
        ),
        {
            "d": today,
            "p": path,
            "l": body["locale"],
            "r": _referrer_host(body.get("referrer", ""), own),
            "v": int(new),
        },
    )


async def analytics(uow: UnitOfWork, since: date, until: date) -> dict[str, Any]:
    s = uow.session
    where = (SitePageView.day >= since, SitePageView.day <= until)

    async def top(column: Any) -> list[dict[str, Any]]:
        rows = (
            await s.execute(
                select(column, func.sum(SitePageView.views), func.sum(SitePageView.visitors))
                .where(*where)
                .group_by(column)
                .order_by(func.sum(SitePageView.views).desc())
                .limit(20)
            )
        ).all()
        return [{"key": k or "(direct)", "views": int(v), "visitors": int(u)} for k, v, u in rows]

    days = (
        await s.execute(
            select(SitePageView.day, func.sum(SitePageView.views), func.sum(SitePageView.visitors))
            .where(*where)
            .group_by(SitePageView.day)
            .order_by(SitePageView.day)
        )
    ).all()
    leads = (
        await s.execute(
            select(func.count())
            .select_from(SiteLead)
            .where(SiteLead.created_at >= since, SiteLead.created_at < until + timedelta(days=1))
        )
    ).scalar_one()
    return {
        "since": since,
        "until": until,
        "views": sum(int(v) for _, v, _ in days),
        "visitors": sum(int(u) for _, _, u in days),
        "days": [{"day": d, "views": int(v), "visitors": int(u)} for d, v, u in days],
        "pages": await top(SitePageView.path),
        "referrers": await top(SitePageView.referrer),
        "locales": await top(SitePageView.locale),
        "leads": int(leads),
    }


# --- Telling the website to refresh -------------------------------------------------------


def _affected_paths(e: SiteEntry, s: SiteSettings) -> list[str]:
    paths = [path_for(e.kind, e.locale, e.slug, s.default_locale)]
    if e.kind == "post":
        prefix = "" if e.locale == s.default_locale else f"/{e.locale}"
        paths += [f"{prefix}/blog", prefix or "/"]
    return paths


def _revalidate_after_commit(
    st: AppState, uow: UnitOfWork, paths: list[str], *, everything: bool = False
) -> None:
    url, secret = st.settings.website_url, st.settings.website_revalidate_secret
    if not url or not secret:
        return

    async def call() -> None:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(
                f"{url.rstrip('/')}/api/revalidate",
                json={"paths": sorted(set(paths)), "everything": everything},
                headers={"x-revalidate-secret": secret},
            )
            if r.status_code >= 400:
                log.warning("website refresh failed: %s", r.status_code)

    uow.after_commit(call)
