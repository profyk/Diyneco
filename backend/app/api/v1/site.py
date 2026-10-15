"""/site (public) and /admin/site (Diyneco staff): the public website (DECISIONS D83).

Public routes need no sign-in: the website server reads settings, pages, posts, the sitemap
and redirects; visitors send leads and cookieless page views. Images are served here at
addresses that never change. Staff edit with platform.website.manage and follow up leads
with platform.leads.read; every change is audited."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import Principal, Uow, client_ip, require_permission, state_of
from app.core.errors import AppError
from app.schemas.site import (
    AnalyticsOut,
    EntryCreate,
    EntryList,
    EntryOut,
    EntryPatch,
    EntryVersionList,
    LeadIn,
    LeadList,
    LeadOut,
    LeadPatch,
    Locale,
    MediaList,
    MediaOut,
    MediaPatch,
    MediaUpload,
    PageViewIn,
    PostCardList,
    PreviewOut,
    PublicEntry,
    PublicSettings,
    RedirectIn,
    RedirectList,
    RedirectOut,
    SettingsIn,
    SettingsOut,
    Sitemap,
    Slug,
)
from app.services import site as svc

public_router = APIRouter(prefix="/site", tags=["site"])
admin_router = APIRouter(prefix="/admin/site", tags=["admin"])

WebsiteManage = Annotated[Principal, Depends(require_permission("platform.website.manage"))]
LeadsRead = Annotated[Principal, Depends(require_permission("platform.leads.read"))]

# The website caches public reads itself and asks for a refresh on publish (D83).
PUBLIC_CACHE = "public, max-age=60, stale-while-revalidate=300"


# --- Public ------------------------------------------------------------------------------


@public_router.get("/settings", response_model=PublicSettings)
async def public_settings(request: Request, uow: Uow, response: Response) -> dict[str, Any]:
    response.headers["Cache-Control"] = PUBLIC_CACHE
    return await svc.public_settings(state_of(request), uow)


@public_router.get("/entry", response_model=PublicEntry)
async def public_entry(
    request: Request,
    uow: Uow,
    response: Response,
    kind: Literal["page", "post"],
    locale: Locale,
    slug: Annotated[Slug, Query()] = "",
) -> dict[str, Any]:
    """A published page or post; the home page is the page with an empty slug."""
    response.headers["Cache-Control"] = PUBLIC_CACHE
    return await svc.public_entry(state_of(request), uow, kind, locale, slug)


@public_router.get("/preview", response_model=PublicEntry)
async def preview_entry(request: Request, uow: Uow, response: Response, token: str) -> dict[str, Any]:
    """The draft behind a 15-minute preview link made in the admin panel."""
    response.headers["Cache-Control"] = "no-store"
    return await svc.preview_entry(state_of(request), uow, token)


@public_router.get("/posts", response_model=PostCardList)
async def public_posts(
    request: Request,
    uow: Uow,
    response: Response,
    locale: Locale,
    limit: Annotated[int, Query(ge=1, le=50)] = 12,
    before: datetime | None = None,
    tag: Annotated[str | None, Query(max_length=40)] = None,
) -> dict[str, Any]:
    response.headers["Cache-Control"] = PUBLIC_CACHE
    return await svc.public_posts(state_of(request), uow, locale, limit, before, tag)


@public_router.get("/sitemap", response_model=Sitemap)
async def sitemap(uow: Uow, response: Response) -> dict[str, Any]:
    response.headers["Cache-Control"] = PUBLIC_CACHE
    return {"data": await svc.sitemap(uow)}


@public_router.get("/redirects", response_model=RedirectList)
async def public_redirects(uow: Uow, response: Response) -> dict[str, Any]:
    """Old addresses and where they now live, for the website to answer with 301 or 302."""
    response.headers["Cache-Control"] = PUBLIC_CACHE
    return {"data": await svc.list_redirects(uow)}


@public_router.get("/media/{media_id}/{width}.webp")
async def media(media_id: uuid.UUID, width: int, request: Request, uow: Uow) -> Response:
    data = await svc.media_bytes(state_of(request), uow, media_id, width)
    return Response(
        content=data,
        media_type="image/webp",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@public_router.post("/leads", status_code=202)
async def create_lead(body: LeadIn, request: Request, uow: Uow) -> dict[str, str]:
    """A demo request or contact message. Spam is accepted silently and dropped."""
    await svc.create_lead(state_of(request), uow, body.model_dump(), client_ip(request))
    return {"status": "accepted"}


@public_router.post("/views", status_code=204)
async def record_view(body: PageViewIn, request: Request, uow: Uow) -> Response:
    """A cookieless page view; nothing that identifies the visitor is stored."""
    await svc.record_view(uow, body.model_dump(), client_ip(request), request.headers.get("user-agent"))
    return Response(status_code=204)


# --- Admin: settings and entries ---------------------------------------------------------


@admin_router.get("/settings", response_model=SettingsOut)
async def get_settings(uow: Uow, principal: WebsiteManage) -> dict[str, Any]:
    return await svc.get_settings(uow)


@admin_router.put("/settings", response_model=SettingsOut)
async def put_settings(
    body: SettingsIn, request: Request, uow: Uow, principal: WebsiteManage
) -> dict[str, Any]:
    return await svc.put_settings(
        state_of(request), uow, principal.platform_actor(request), body.model_dump(mode="json")
    )


@admin_router.get("/entries", response_model=EntryList)
async def list_entries(
    uow: Uow,
    principal: WebsiteManage,
    kind: Literal["page", "post"] | None = None,
    locale: Locale | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> dict[str, Any]:
    return {"data": await svc.list_entries(uow, kind, locale, q)}


@admin_router.post("/entries", status_code=201, response_model=EntryOut)
async def create_entry(
    body: EntryCreate, request: Request, uow: Uow, principal: WebsiteManage
) -> dict[str, Any]:
    return await svc.create_entry(
        state_of(request), uow, principal.platform_actor(request), body.model_dump(mode="json")
    )


@admin_router.get("/entries/{entry_id}", response_model=EntryOut)
async def get_entry(entry_id: uuid.UUID, uow: Uow, principal: WebsiteManage) -> dict[str, Any]:
    return await svc.get_entry(uow, entry_id)


@admin_router.patch("/entries/{entry_id}", response_model=EntryOut)
async def update_entry(
    entry_id: uuid.UUID, body: EntryPatch, request: Request, uow: Uow, principal: WebsiteManage
) -> dict[str, Any]:
    return await svc.update_entry(
        state_of(request),
        uow,
        principal.platform_actor(request),
        entry_id,
        body.model_dump(mode="json", exclude_unset=True),
    )


@admin_router.delete("/entries/{entry_id}", status_code=204)
async def delete_entry(entry_id: uuid.UUID, request: Request, uow: Uow, principal: WebsiteManage) -> Response:
    await svc.delete_entry(state_of(request), uow, principal.platform_actor(request), entry_id)
    return Response(status_code=204)


@admin_router.post("/entries/{entry_id}/publish", response_model=EntryOut)
async def publish_entry(
    entry_id: uuid.UUID, request: Request, uow: Uow, principal: WebsiteManage
) -> dict[str, Any]:
    return await svc.publish_entry(state_of(request), uow, principal.platform_actor(request), entry_id)


@admin_router.post("/entries/{entry_id}/unpublish", response_model=EntryOut)
async def unpublish_entry(
    entry_id: uuid.UUID, request: Request, uow: Uow, principal: WebsiteManage
) -> dict[str, Any]:
    return await svc.unpublish_entry(state_of(request), uow, principal.platform_actor(request), entry_id)


@admin_router.get("/entries/{entry_id}/versions", response_model=EntryVersionList)
async def versions(entry_id: uuid.UUID, uow: Uow, principal: WebsiteManage) -> dict[str, Any]:
    return {"data": await svc.versions(uow, entry_id)}


@admin_router.post("/entries/{entry_id}/versions/{version}/restore", response_model=EntryOut)
async def restore_version(
    entry_id: uuid.UUID, version: int, request: Request, uow: Uow, principal: WebsiteManage
) -> dict[str, Any]:
    """Copies a published version back into the draft; publish to make it live again."""
    return await svc.restore_version(
        state_of(request), uow, principal.platform_actor(request), entry_id, version
    )


@admin_router.post("/entries/{entry_id}/preview", response_model=PreviewOut)
async def preview_link(
    entry_id: uuid.UUID, request: Request, uow: Uow, principal: WebsiteManage
) -> dict[str, Any]:
    return await svc.preview(state_of(request), uow, entry_id)


# --- Admin: redirects and media ----------------------------------------------------------


@admin_router.get("/redirects", response_model=RedirectList)
async def list_redirects(uow: Uow, principal: WebsiteManage) -> dict[str, Any]:
    return {"data": await svc.list_redirects(uow)}


@admin_router.post("/redirects", status_code=201, response_model=RedirectOut)
async def create_redirect(
    body: RedirectIn, request: Request, uow: Uow, principal: WebsiteManage
) -> dict[str, Any]:
    return await svc.create_redirect(
        state_of(request), uow, principal.platform_actor(request), body.model_dump()
    )


@admin_router.delete("/redirects/{redirect_id}", status_code=204)
async def delete_redirect(
    redirect_id: uuid.UUID, request: Request, uow: Uow, principal: WebsiteManage
) -> Response:
    await svc.delete_redirect(state_of(request), uow, principal.platform_actor(request), redirect_id)
    return Response(status_code=204)


@admin_router.get("/media", response_model=MediaList)
async def list_media(request: Request, uow: Uow, principal: WebsiteManage) -> dict[str, Any]:
    return {"data": await svc.list_media(state_of(request), uow)}


@admin_router.post("/media", status_code=201, response_model=MediaOut)
async def upload_media(
    body: MediaUpload, request: Request, uow: Uow, principal: WebsiteManage
) -> dict[str, Any]:
    """JPEG, PNG or WebP up to 6 MB; re-encoded as WebP in several widths, metadata dropped."""
    return await svc.upload_media(
        state_of(request), uow, principal.platform_actor(request), body.model_dump()
    )


@admin_router.patch("/media/{media_id}", response_model=MediaOut)
async def update_media(
    media_id: uuid.UUID, body: MediaPatch, request: Request, uow: Uow, principal: WebsiteManage
) -> dict[str, Any]:
    return await svc.update_media(
        state_of(request), uow, principal.platform_actor(request), media_id, body.alt
    )


@admin_router.delete("/media/{media_id}", status_code=204)
async def delete_media(media_id: uuid.UUID, request: Request, uow: Uow, principal: WebsiteManage) -> Response:
    await svc.delete_media(uow, principal.platform_actor(request), media_id)
    return Response(status_code=204)


# --- Admin: leads and analytics ----------------------------------------------------------


@admin_router.get("/leads", response_model=LeadList)
async def list_leads(
    uow: Uow,
    principal: LeadsRead,
    status: Literal["new", "contacted", "qualified", "closed", "spam"] | None = None,
    kind: Literal["demo", "contact"] | None = None,
    before: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, Any]:
    return await svc.list_leads(uow, status, kind, before, limit)


@admin_router.patch("/leads/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: uuid.UUID, body: LeadPatch, request: Request, uow: Uow, principal: LeadsRead
) -> dict[str, Any]:
    return await svc.update_lead(
        uow, principal.platform_actor(request), lead_id, body.model_dump(exclude_unset=True)
    )


@admin_router.delete("/leads/{lead_id}", status_code=204)
async def erase_lead(lead_id: uuid.UUID, request: Request, uow: Uow, principal: LeadsRead) -> Response:
    """Erases a lead on the person's request (POPIA); the audit keeps only that it happened."""
    await svc.erase_lead(uow, principal.platform_actor(request), lead_id)
    return Response(status_code=204)


@admin_router.get("/analytics", response_model=AnalyticsOut)
async def analytics(
    uow: Uow, principal: WebsiteManage, since: date | None = None, until: date | None = None
) -> dict[str, Any]:
    end = until or datetime.now(UTC).date()
    start = since or end - timedelta(days=29)
    if start > end or (end - start).days > 366:
        raise AppError("VALIDATION_FAILED", "Choose a period of at most a year, oldest date first.")
    return await svc.analytics(uow, start, end)
