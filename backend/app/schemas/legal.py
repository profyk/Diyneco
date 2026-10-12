"""Legal documents and acceptances (DECISIONS D70)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import StrictModel

LegalKind = Literal["terms", "privacy", "dpa", "acceptable_use", "guest_terms", "guest_privacy"]
CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
Title = Annotated[str, StringConstraints(min_length=1, max_length=200, strip_whitespace=True)]
Body = Annotated[str, StringConstraints(min_length=1, max_length=200_000)]
Summary = Annotated[str, StringConstraints(max_length=2000)]


class LegalDocumentOut(BaseModel):
    id: uuid.UUID
    kind: LegalKind
    country: str | None  # None: applies wherever a country has no version of its own
    version: int
    title: str
    summary: str | None
    status: Literal["draft", "published"]
    effective_at: datetime | None
    published_at: datetime | None
    body: str | None = None  # left out of lists of documents waiting for acceptance


class LegalDocumentList(BaseModel):
    data: list[LegalDocumentOut]
    next_cursor: str | None = None


class LegalAccept(StrictModel):
    document_ids: list[uuid.UUID] = Field(min_length=1, max_length=10)


class LegalDraftCreate(StrictModel):
    kind: LegalKind
    country: CountryCode | None = None
    title: Title
    body: Body
    summary: Summary | None = None
    effective_at: datetime | None = None


class LegalDraftPatch(StrictModel):
    title: Title | None = None
    body: Body | None = None
    summary: Summary | None = None
    effective_at: datetime | None = None
