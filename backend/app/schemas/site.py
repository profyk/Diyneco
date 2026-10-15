"""The public website (DECISIONS D83): settings, pages and posts made of typed blocks, media,
redirects, leads and page-view analytics.

Content is validated here, so the website only ever renders known block types with bounded
text. Links are site paths (`/pricing`) or https addresses; images are site_media ids. Long
text (`body`) is Markdown, rendered on the website without raw HTML.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from app.schemas.common import StrictModel

Locale = Annotated[str, StringConstraints(pattern=r"^[a-z]{2}(-[A-Z]{2})?$")]
Slug = Annotated[
    str, StringConstraints(pattern=r"^$|^[a-z0-9]+(-[a-z0-9]+)*(/[a-z0-9]+(-[a-z0-9]+)*)*$", max_length=120)
]
Href = Annotated[
    str,
    StringConstraints(pattern=r"^(/[A-Za-z0-9/_.~%#?=&-]*|https://[^\s]+|mailto:[^\s]+)$", max_length=300),
]
Line = Annotated[str, StringConstraints(min_length=1, max_length=160)]
Para = Annotated[str, StringConstraints(max_length=1200)]
Markdown = Annotated[str, StringConstraints(max_length=100_000)]
Icon = Annotated[str, StringConstraints(pattern=r"^[a-z0-9-]{1,40}$")]


class Cta(StrictModel):
    label: Annotated[str, StringConstraints(min_length=1, max_length=60)]
    href: Href


# --- Blocks --------------------------------------------------------------------------------


class Hero(StrictModel):
    type: Literal["hero"]
    eyebrow: Annotated[str, StringConstraints(max_length=80)] | None = None
    heading: Line
    subheading: Para | None = None
    primary: Cta | None = None
    secondary: Cta | None = None
    image_id: uuid.UUID | None = None


class FeatureItem(StrictModel):
    icon: Icon | None = None
    title: Line
    body: Para
    image_id: uuid.UUID | None = None  # a photo on the card (D91)


class Features(StrictModel):
    type: Literal["features"]
    heading: Line | None = None
    intro: Para | None = None
    items: Annotated[list[FeatureItem], Field(min_length=1, max_length=12)]


class StepItem(StrictModel):
    title: Line
    body: Para


class Steps(StrictModel):
    type: Literal["steps"]
    heading: Line | None = None
    items: Annotated[list[StepItem], Field(min_length=1, max_length=8)]


class Split(StrictModel):
    type: Literal["split"]
    heading: Line
    body: Annotated[str, StringConstraints(max_length=4000)]
    image_id: uuid.UUID | None = None
    image_side: Literal["left", "right"] = "right"
    cta: Cta | None = None


class StatItem(StrictModel):
    value: Annotated[str, StringConstraints(min_length=1, max_length=20)]
    label: Line


class Stats(StrictModel):
    type: Literal["stats"]
    heading: Line | None = None
    items: Annotated[list[StatItem], Field(min_length=1, max_length=6)]


class Testimonial(StrictModel):
    quote: Annotated[str, StringConstraints(min_length=1, max_length=600)]
    name: Line
    role: Line | None = None
    hotel: Line | None = None


class Testimonials(StrictModel):
    type: Literal["testimonials"]
    heading: Line | None = None
    items: Annotated[list[Testimonial], Field(min_length=1, max_length=12)]


class FaqItem(StrictModel):
    question: Annotated[str, StringConstraints(min_length=1, max_length=300)]
    answer: Annotated[str, StringConstraints(min_length=1, max_length=3000)]


class Faq(StrictModel):
    type: Literal["faq"]
    heading: Line | None = None
    items: Annotated[list[FaqItem], Field(min_length=1, max_length=40)]


class CallToAction(StrictModel):
    type: Literal["cta"]
    heading: Line
    body: Para | None = None
    primary: Cta
    secondary: Cta | None = None


class LogoItem(StrictModel):
    image_id: uuid.UUID
    name: Line
    href: Href | None = None


class Logos(StrictModel):
    type: Literal["logos"]
    heading: Line | None = None
    items: Annotated[list[LogoItem], Field(min_length=1, max_length=24)]


class Pricing(StrictModel):
    """The live published plans from GET /plans, so prices on the site always match billing."""

    type: Literal["pricing"]
    heading: Line | None = None
    intro: Para | None = None


class RichText(StrictModel):
    type: Literal["rich_text"]
    body: Markdown


class LeadForm(StrictModel):
    type: Literal["lead_form"]
    kind: Literal["demo", "contact"]
    heading: Line | None = None
    intro: Para | None = None


GalleryCategory = Literal[
    "rooms", "reception", "kitchen", "restaurant", "outside", "pool", "spa", "conference", "events", "other"
]


class GalleryItem(StrictModel):
    image_id: uuid.UUID
    caption: Annotated[str, StringConstraints(max_length=160)] | None = None
    category: GalleryCategory = "other"


class Gallery(StrictModel):
    """Photos of hotels using Diyneco (kitchens, reception, rooms, outside...), with filters by
    area and a full-screen viewer (D91)."""

    type: Literal["gallery"]
    heading: Line | None = None
    intro: Para | None = None
    items: Annotated[list[GalleryItem], Field(min_length=1, max_length=60)]
    show_filters: bool = True


class PostList(StrictModel):
    """The latest blog posts in the page's language."""

    type: Literal["post_list"]
    heading: Line | None = None
    limit: Annotated[int, Field(ge=1, le=12)] = 3


Block = Annotated[
    Hero
    | Features
    | Steps
    | Split
    | Stats
    | Testimonials
    | Faq
    | CallToAction
    | Logos
    | Pricing
    | RichText
    | LeadForm
    | PostList
    | Gallery,
    Field(discriminator="type"),
]


class Seo(StrictModel):
    title: Annotated[str, StringConstraints(max_length=70)] | None = None
    description: Annotated[str, StringConstraints(max_length=170)] | None = None
    image_id: uuid.UUID | None = None
    noindex: bool = False


class EntryContent(StrictModel):
    """A page is blocks; a post is a body with an excerpt, a cover and tags."""

    title: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    seo: Seo = Field(default_factory=Seo)
    blocks: Annotated[list[Block], Field(max_length=40)] = Field(default_factory=list)
    excerpt: Annotated[str, StringConstraints(max_length=300)] | None = None
    body: Markdown | None = None
    cover_id: uuid.UUID | None = None
    author: Line | None = None
    tags: Annotated[
        list[Annotated[str, StringConstraints(min_length=1, max_length=40)]], Field(max_length=10)
    ] = Field(default_factory=list)


class EntryCreate(StrictModel):
    kind: Literal["page", "post"]
    locale: Locale
    slug: Slug
    content: EntryContent
    translation_of: uuid.UUID | None = None  # another entry this one translates

    @model_validator(mode="after")
    def _home_is_a_page(self) -> EntryCreate:
        if self.kind == "post" and not self.slug:
            raise ValueError("A post needs an address.")
        return self


class EntryPatch(StrictModel):
    slug: Slug | None = None
    content: EntryContent | None = None


class EntrySummary(BaseModel):
    id: uuid.UUID
    kind: str
    locale: str
    slug: str
    title: str
    translation_key: uuid.UUID
    status: Literal["draft", "published", "changed"]  # changed: published with unpublished edits
    version: int
    published_at: datetime | None
    updated_at: datetime


class EntryOut(EntrySummary):
    draft: dict[str, Any]
    published: dict[str, Any] | None
    translations: list[dict[str, Any]]


class EntryList(BaseModel):
    data: list[EntrySummary]
    next_cursor: str | None = None


class EntryVersion(BaseModel):
    version: int
    published_at: datetime
    published_by: str | None
    content: dict[str, Any]


class EntryVersionList(BaseModel):
    data: list[EntryVersion]
    next_cursor: str | None = None


class PreviewOut(BaseModel):
    url: str
    expires_in: int


# --- Settings ------------------------------------------------------------------------------


class NavLink(StrictModel):
    label: Annotated[str, StringConstraints(min_length=1, max_length=40)]
    href: Href


class FooterColumn(StrictModel):
    heading: Annotated[str, StringConstraints(min_length=1, max_length=40)]
    links: Annotated[list[NavLink], Field(max_length=10)]


class Footer(StrictModel):
    columns: Annotated[list[FooterColumn], Field(max_length=5)] = Field(default_factory=list)
    note: Annotated[str, StringConstraints(max_length=300)] | None = None


class Contact(StrictModel):
    email: Annotated[str, StringConstraints(max_length=200)] | None = None
    phone: Annotated[str, StringConstraints(max_length=40)] | None = None
    address: Annotated[str, StringConstraints(max_length=300)] | None = None


class SocialLink(StrictModel):
    network: Literal["linkedin", "facebook", "instagram", "x", "youtube", "tiktok"]
    url: Annotated[str, StringConstraints(pattern=r"^https://", max_length=300)]


class SiteSeo(StrictModel):
    title_template: Annotated[str, StringConstraints(max_length=80)] = "%s | Diyneco"
    default_title: Annotated[str, StringConstraints(max_length=70)] | None = None
    default_description: Annotated[str, StringConstraints(max_length=170)] | None = None
    default_image_id: uuid.UUID | None = None
    organization_logo_id: uuid.UUID | None = None

    @field_validator("title_template")
    @classmethod
    def _has_slot(cls, v: str) -> str:
        if "%s" not in v:
            raise ValueError("The title template needs %s where the page title goes.")
        return v


class Verification(StrictModel):
    google: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{0,100}$")] | None = None
    bing: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{0,100}$")] | None = None


class Analytics(StrictModel):
    """`builtin`: Diyneco's own cookieless counts. `plausible`: a Plausible-compatible script
    (also cookieless). `none`: nothing is counted."""

    provider: Literal["builtin", "plausible", "none"] = "builtin"
    plausible_domain: Annotated[str, StringConstraints(max_length=200)] | None = None
    plausible_script: Annotated[str, StringConstraints(pattern=r"^https://", max_length=300)] | None = None


class SettingsIn(StrictModel):
    site_name: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    base_url: Annotated[str, StringConstraints(pattern=r"^https?://[^/\s]+$", max_length=200)]
    default_locale: Locale
    locales: Annotated[list[Locale], Field(min_length=1, max_length=20)]
    navigation: Annotated[list[NavLink], Field(max_length=10)]
    footer: Footer
    contact: Contact
    social: Annotated[list[SocialLink], Field(max_length=8)]
    seo: SiteSeo
    verification: Verification
    analytics: Analytics
    lead_email: Annotated[str, StringConstraints(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)]

    @model_validator(mode="after")
    def _default_enabled(self) -> SettingsIn:
        if self.default_locale not in self.locales:
            raise ValueError("The default language must be one of the enabled languages.")
        if len(set(self.locales)) != len(self.locales):
            raise ValueError("A language is listed twice.")
        return self


class SettingsOut(BaseModel):
    site_name: str
    base_url: str
    default_locale: str
    locales: list[str]
    navigation: list[dict[str, Any]]
    footer: dict[str, Any]
    contact: dict[str, Any]
    social: list[dict[str, Any]]
    seo: dict[str, Any]
    verification: dict[str, Any]
    analytics: dict[str, Any]
    lead_email: str
    updated_at: datetime


class PublicSettings(BaseModel):
    """What the website renders with. The lead address is never public."""

    site_name: str
    base_url: str
    default_locale: str
    locales: list[str]
    navigation: list[dict[str, Any]]
    footer: dict[str, Any]
    contact: dict[str, Any]
    social: list[dict[str, Any]]
    seo: dict[str, Any]
    verification: dict[str, Any]
    analytics: dict[str, Any]
    media: dict[str, dict[str, Any]]  # images the settings refer to, by id


# --- Public reads --------------------------------------------------------------------------


class Alternate(BaseModel):
    locale: str
    path: str


class PublicEntry(BaseModel):
    kind: str
    locale: str
    slug: str
    path: str
    content: dict[str, Any]
    published_at: datetime | None
    updated_at: datetime | None
    alternates: list[Alternate]
    media: dict[str, dict[str, Any]]  # every image the content refers to, by id
    posts: list[dict[str, Any]] = Field(default_factory=list)  # for post_list blocks
    preview: bool = False


class PostCard(BaseModel):
    slug: str
    path: str
    title: str
    excerpt: str | None
    cover: dict[str, Any] | None
    author: str | None
    tags: list[str]
    published_at: datetime


class PostCardList(BaseModel):
    data: list[PostCard]
    next_cursor: str | None = None


class SitemapEntry(BaseModel):
    path: str
    locale: str
    updated_at: datetime
    alternates: list[Alternate]
    kind: str


class Sitemap(BaseModel):
    data: list[SitemapEntry]


class RedirectOut(BaseModel):
    id: uuid.UUID
    from_path: str
    to_path: str
    permanent: bool
    created_at: datetime


class RedirectList(BaseModel):
    data: list[RedirectOut]
    next_cursor: str | None = None


class RedirectIn(StrictModel):
    from_path: Annotated[str, StringConstraints(pattern=r"^/[A-Za-z0-9/_.~%-]+$", max_length=300)]
    to_path: Annotated[str, StringConstraints(pattern=r"^(/[A-Za-z0-9/_.~%-]*|https://\S+)$", max_length=300)]
    permanent: bool = True


# --- Media ---------------------------------------------------------------------------------


class MediaUpload(StrictModel):
    filename: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    alt: Annotated[str, StringConstraints(max_length=300)] = ""
    data_base64: Annotated[str, StringConstraints(min_length=4, max_length=8_000_000)]  # about 6 MB


class MediaPatch(StrictModel):
    alt: Annotated[str, StringConstraints(max_length=300)]


class MediaOut(BaseModel):
    id: uuid.UUID
    filename: str
    alt: str
    width: int
    height: int
    widths: list[int]
    url: str  # the largest copy
    created_at: datetime


class MediaList(BaseModel):
    data: list[MediaOut]
    next_cursor: str | None = None


# --- Leads and analytics -------------------------------------------------------------------


class LeadIn(StrictModel):
    kind: Literal["demo", "contact"]
    name: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    email: Annotated[str, StringConstraints(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)]
    phone: Annotated[str, StringConstraints(pattern=r"^[0-9 +()-]{0,40}$")] | None = None
    company: Annotated[str, StringConstraints(max_length=160)] | None = None
    rooms: Annotated[int, Field(ge=1, le=100_000)] | None = None
    country: Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")] | None = None
    message: Annotated[str, StringConstraints(max_length=4000)] | None = None
    locale: Locale
    source_path: Annotated[str, StringConstraints(max_length=300)] | None = None
    consent: Literal[True]  # the form cannot be sent without ticking it
    consent_text: Annotated[str, StringConstraints(min_length=1, max_length=1000)]
    website: Annotated[str, StringConstraints(max_length=200)] = ""  # honeypot: people leave it empty
    elapsed_ms: Annotated[int, Field(ge=0, le=86_400_000)]  # time the form was open


class LeadOut(BaseModel):
    id: uuid.UUID
    kind: str
    name: str
    email: str
    phone: str | None
    company: str | None
    rooms: int | None
    country: str | None
    message: str | None
    locale: str
    source_path: str | None
    consent_text: str
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class LeadList(BaseModel):
    data: list[LeadOut]
    next_cursor: str | None = None


class LeadPatch(StrictModel):
    status: Literal["new", "contacted", "qualified", "closed", "spam"] | None = None
    notes: Annotated[str, StringConstraints(max_length=4000)] | None = None


class PageViewIn(StrictModel):
    path: Annotated[str, StringConstraints(pattern=r"^/", max_length=300)]
    locale: Locale
    referrer: Annotated[str, StringConstraints(max_length=500)] = ""


class AnalyticsRow(BaseModel):
    key: str
    views: int
    visitors: int


class AnalyticsDay(BaseModel):
    day: date
    views: int
    visitors: int


class AnalyticsOut(BaseModel):
    since: date
    until: date
    views: int
    visitors: int  # sum of daily distinct visitors
    days: list[AnalyticsDay]
    pages: list[AnalyticsRow]
    referrers: list[AnalyticsRow]
    locales: list[AnalyticsRow]
    leads: int
