"""Legal documents: the platform publishes versions, every app shows the current ones, and each
acceptance is recorded (DECISIONS D70).

The current version of a kind for a country is the newest published version for that country,
or the newest global one (country NULL) when the country has none of its own. Merchants must
accept the current terms, privacy notice and data processing agreement; the Merchant app asks
again whenever a newer version of any of them is published.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.audit.writer import write_audit, write_platform_audit
from app.core.errors import AppError
from app.db.session import TenantContext, UnitOfWork
from app.models.tenancy import Hotel, LegalAcceptance, LegalDocument

KINDS = ("terms", "privacy", "dpa", "acceptable_use", "guest_terms", "guest_privacy")
MERCHANT_REQUIRED = ("terms", "privacy", "dpa")
GUEST_KINDS = ("guest_terms", "guest_privacy")


def payload(d: LegalDocument, *, with_body: bool = True) -> dict[str, Any]:
    out = {
        "id": d.id,
        "kind": d.kind,
        "country": d.country,
        "version": d.version,
        "title": d.title,
        "summary": d.summary,
        "status": d.status,
        "effective_at": d.effective_at,
        "published_at": d.published_at,
    }
    if with_body:
        out["body"] = d.body
    return out


async def current(s: Any, kinds: tuple[str, ...], country: str | None) -> dict[str, LegalDocument]:
    """Current published version of each kind for the country (country-specific first)."""
    rows = (
        await s.execute(
            select(LegalDocument)
            .where(
                LegalDocument.kind.in_(kinds),
                LegalDocument.status == "published",
                (LegalDocument.country.is_(None)) | (LegalDocument.country == (country or "").upper()),
            )
            .order_by(LegalDocument.kind, LegalDocument.country.is_(None), LegalDocument.version.desc())
        )
    ).scalars()
    out: dict[str, LegalDocument] = {}
    for d in rows:
        out.setdefault(d.kind, d)  # first per kind: own country before global, newest first
    return out


async def public_documents(
    uow: UnitOfWork, country: str | None, kinds: tuple[str, ...] = KINDS
) -> list[dict[str, Any]]:
    docs = await current(uow.session, kinds, country)
    return [payload(docs[k]) for k in kinds if k in docs]


async def public_document(uow: UnitOfWork, document_id: uuid.UUID) -> dict[str, Any]:
    d = (
        await uow.session.execute(
            select(LegalDocument).where(LegalDocument.id == document_id, LegalDocument.status == "published")
        )
    ).scalar_one_or_none()
    if d is None:
        raise AppError("NOT_FOUND")
    return payload(d)


async def hotel_country(uow: UnitOfWork, ctx: TenantContext) -> str | None:
    return (
        await uow.session.execute(select(Hotel.country).where(Hotel.id == ctx.hotel_id))
    ).scalar_one_or_none()


async def pending_for(uow: UnitOfWork, ctx: TenantContext) -> list[dict[str, Any]]:
    """Current merchant documents this person has not accepted for this hotel."""
    if ctx.actor_id is None:
        return []
    docs = await current(uow.session, MERCHANT_REQUIRED, await hotel_country(uow, ctx))
    if not docs:
        return []
    accepted = set(
        (
            await uow.session.execute(
                select(LegalAcceptance.document_id).where(
                    LegalAcceptance.hotel_id == ctx.hotel_id,
                    LegalAcceptance.user_id == ctx.actor_id,
                    LegalAcceptance.document_id.in_([d.id for d in docs.values()]),
                )
            )
        ).scalars()
    )
    return [payload(d, with_body=False) for k, d in docs.items() if d.id not in accepted]


async def accept(
    uow: UnitOfWork,
    ctx: TenantContext,
    document_ids: list[uuid.UUID],
    *,
    user_agent: str | None,
    country: str | None = None,
) -> list[dict[str, Any]]:
    """Records acceptance of current documents; anything else (old or draft) is refused."""
    if ctx.actor_id is None:
        raise AppError("PERMISSION_DENIED")
    docs = await current(uow.session, KINDS, country or await hotel_country(uow, ctx))
    valid = {d.id for d in docs.values()}
    if not document_ids or not set(document_ids) <= valid:
        raise AppError(
            "VALIDATION_FAILED",
            "Accept the current version of each document; a newer one may have been published.",
            details={"fields": [{"field": "document_ids", "problem": "Not current.", "type": "value_error"}]},
        )
    for doc_id in dict.fromkeys(document_ids):
        await uow.session.execute(
            pg_insert(LegalAcceptance)
            .values(
                hotel_id=ctx.hotel_id,
                document_id=doc_id,
                user_id=ctx.actor_id,
                ip=ctx.ip,
                user_agent=(user_agent or "")[:500] or None,
            )
            .on_conflict_do_nothing()
        )
    await write_audit(
        uow.session,
        ctx,
        "legal.accept",
        "legal_document",
        None,
        new_value={"documents": [str(d) for d in document_ids]},
    )
    return await pending_for(uow, ctx)


async def signup_documents(
    uow: UnitOfWork, country: str, document_ids: list[uuid.UUID] | None
) -> list[uuid.UUID]:
    """The owner must accept every current merchant document (when any are published). Returns
    the ids to record once the hotel exists; refuses before anything is written."""
    docs = await current(uow.session, MERCHANT_REQUIRED, country)
    if not docs:
        return []
    if set(document_ids or []) != {d.id for d in docs.values()}:
        raise AppError(
            "VALIDATION_FAILED",
            "Accept the terms, privacy notice and data processing agreement to register.",
            details={
                "fields": [{"field": "accepted_documents", "problem": "Required.", "type": "value_error"}]
            },
        )
    return [d.id for d in docs.values()]


# --- Platform: drafting and publishing -----------------------------------------------------


async def admin_list(uow: UnitOfWork) -> list[dict[str, Any]]:
    rows = (
        await uow.session.execute(
            select(LegalDocument).order_by(
                LegalDocument.kind, LegalDocument.country, LegalDocument.version.desc()
            )
        )
    ).scalars()
    return [payload(d) for d in rows]


async def create_draft(uow: UnitOfWork, actor: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    s = uow.session
    country = body.get("country")
    latest = (
        await s.execute(
            select(func.max(LegalDocument.version)).where(
                LegalDocument.kind == body["kind"],
                LegalDocument.country.is_(None) if country is None else LegalDocument.country == country,
            )
        )
    ).scalar_one()
    doc = (
        await s.execute(
            insert(LegalDocument)
            .values(
                kind=body["kind"],
                country=country,
                version=(latest or 0) + 1,
                title=body["title"],
                body=body["body"],
                summary=body.get("summary"),
                effective_at=body.get("effective_at"),
                created_by=actor["actor_id"],
            )
            .returning(LegalDocument)
        )
    ).scalar_one()
    await write_platform_audit(
        s,
        **actor,
        action="legal.draft",
        entity_type="legal_document",
        entity_id=doc.id,
        new_value={"kind": doc.kind, "country": doc.country, "version": doc.version},
    )
    return payload(doc)


async def _draft(uow: UnitOfWork, document_id: uuid.UUID) -> LegalDocument:
    doc = (
        await uow.session.execute(select(LegalDocument).where(LegalDocument.id == document_id))
    ).scalar_one_or_none()
    if doc is None:
        raise AppError("NOT_FOUND")
    if doc.status != "draft":
        raise AppError("INVALID_TRANSITION", "Published versions are frozen. Create a new version instead.")
    return doc


async def update_draft(uow: UnitOfWork, document_id: uuid.UUID, changes: dict[str, Any]) -> dict[str, Any]:
    await _draft(uow, document_id)
    doc = (
        await uow.session.execute(
            update(LegalDocument)
            .where(LegalDocument.id == document_id)
            .values(**changes)
            .returning(LegalDocument)
        )
    ).scalar_one()
    return payload(doc)


async def delete_draft(uow: UnitOfWork, document_id: uuid.UUID) -> None:
    doc = await _draft(uow, document_id)
    await uow.session.delete(doc)


async def publish(uow: UnitOfWork, actor: dict[str, Any], document_id: uuid.UUID) -> dict[str, Any]:
    await _draft(uow, document_id)
    now = datetime.now(UTC)
    doc = (
        await uow.session.execute(
            update(LegalDocument)
            .where(LegalDocument.id == document_id)
            .values(
                status="published",
                published_at=now,
                published_by=actor["actor_id"],
                effective_at=func.coalesce(LegalDocument.effective_at, now),
            )
            .returning(LegalDocument)
        )
    ).scalar_one()
    await write_platform_audit(
        uow.session,
        **actor,
        action="legal.publish",
        entity_type="legal_document",
        entity_id=doc.id,
        new_value={"kind": doc.kind, "country": doc.country, "version": doc.version},
    )
    return payload(doc)
