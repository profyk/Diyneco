"""The public website (DECISIONS D83): settings, pages and posts, media, redirects, leads and
aggregated page views. Control plane: no hotel, written only by Diyneco staff."""

from __future__ import annotations

from typing import Any

from app.models.base import (
    ARRAY,
    CHAR,
    CITEXT,
    JSONB,
    UUID,
    Base,
    Integer,
    Mapped,
    SmallInteger,
    Text,
    created_at,
    date,
    datetime,
    mapped_column,
    pk,
    updated_at,
    uuid,
)
from sqlalchemy import text


class SiteSettings(Base):
    __tablename__ = "site_settings"
    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, server_default=text("1"))
    site_name: Mapped[str] = mapped_column(server_default=text("'Diyneco'"))
    base_url: Mapped[str] = mapped_column(server_default=text("'https://www.diyneco.com'"))
    default_locale: Mapped[str] = mapped_column(server_default=text("'en'"))
    locales: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{en}'"))
    navigation: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'"))
    footer: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    contact: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    social: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'"))
    seo: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    verification: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    analytics: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("""'{"provider": "builtin"}'"""))
    lead_email: Mapped[str] = mapped_column(server_default=text("'sales@diyneco.com'"))
    updated_at: Mapped[datetime] = updated_at()
    updated_by: Mapped[uuid.UUID | None]


class SiteMedia(Base):
    __tablename__ = "site_media"
    id: Mapped[uuid.UUID] = pk()
    filename: Mapped[str]
    alt: Mapped[str] = mapped_column(server_default=text("''"))
    width: Mapped[int]
    height: Mapped[int]
    widths: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    bytes: Mapped[int]
    storage_key: Mapped[str]
    uploaded_by: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = created_at()
    deleted_at: Mapped[datetime | None]


class SiteEntry(Base):
    __tablename__ = "site_entries"
    id: Mapped[uuid.UUID] = pk()
    kind: Mapped[str]
    locale: Mapped[str]
    slug: Mapped[str]
    translation_key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), server_default=text("app.uuid_v7()"))
    draft: Mapped[dict[str, Any]]
    published: Mapped[dict[str, Any] | None]
    version: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    published_at: Mapped[datetime | None]
    republished_at: Mapped[datetime | None]
    created_by: Mapped[uuid.UUID | None]
    updated_by: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()
    deleted_at: Mapped[datetime | None]


class SiteEntryVersion(Base):
    __tablename__ = "site_entry_versions"
    id: Mapped[uuid.UUID] = pk()
    entry_id: Mapped[uuid.UUID]
    version: Mapped[int]
    content: Mapped[dict[str, Any]]
    published_by: Mapped[uuid.UUID | None]
    published_at: Mapped[datetime] = created_at()


class SiteRedirect(Base):
    __tablename__ = "site_redirects"
    id: Mapped[uuid.UUID] = pk()
    from_path: Mapped[str]
    to_path: Mapped[str]
    permanent: Mapped[bool] = mapped_column(server_default=text("true"))
    created_by: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = created_at()


class SiteLead(Base):
    __tablename__ = "site_leads"
    id: Mapped[uuid.UUID] = pk()
    kind: Mapped[str]
    name: Mapped[str]
    email: Mapped[str] = mapped_column(CITEXT)
    phone: Mapped[str | None]
    company: Mapped[str | None]
    rooms: Mapped[int | None]
    country: Mapped[str | None] = mapped_column(CHAR(2))
    message: Mapped[str | None]
    locale: Mapped[str]
    source_path: Mapped[str | None]
    consent_text: Mapped[str]
    status: Mapped[str] = mapped_column(server_default=text("'new'"))
    notes: Mapped[str | None]
    handled_by: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()


class SitePageView(Base):
    __tablename__ = "site_page_views"
    day: Mapped[date] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(primary_key=True)
    locale: Mapped[str] = mapped_column(primary_key=True)
    referrer: Mapped[str] = mapped_column(primary_key=True, server_default=text("''"))
    views: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    visitors: Mapped[int] = mapped_column(Integer, server_default=text("0"))
