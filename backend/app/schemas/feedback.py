"""Guest feedback (D98)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.schemas.common import StrictModel

Subject = Literal["order", "request", "stay"]
Comment = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class FeedbackCreate(StrictModel):
    subject: Subject
    order_id: uuid.UUID | None = None
    request_id: uuid.UUID | None = None
    rating: Annotated[int, Field(ge=1, le=5)]
    comment: Comment | None = None

    @model_validator(mode="after")
    def _target(self) -> FeedbackCreate:
        if (self.subject == "order") != (self.order_id is not None):
            raise ValueError("An order rating names the order, and only an order rating does.")
        if (self.subject == "request") != (self.request_id is not None):
            raise ValueError("A request rating names the request, and only a request rating does.")
        return self


class FeedbackOut(BaseModel):
    id: uuid.UUID
    subject: Subject
    order_id: uuid.UUID | None
    request_id: uuid.UUID | None
    rating: int
    comment: str | None
    created_at: datetime


class FeedbackList(BaseModel):
    data: list[FeedbackOut]


class FeedbackComment(BaseModel):
    id: uuid.UUID
    room: str
    subject: Subject
    rating: int
    comment: str | None
    created_at: datetime


class SubjectScore(BaseModel):
    subject: Subject
    ratings: int
    average: float | None


class FeedbackReport(BaseModel):
    from_: date = Field(alias="from")
    to: date
    ratings: int
    average: float | None
    # Ratings by stars, index 0 = one star.
    distribution: list[int]
    by_subject: list[SubjectScore]
    recent: list[FeedbackComment]
    model_config = {"populate_by_name": True, "serialize_by_alias": True}
