"""Guest service requests (D93)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

from app.schemas.common import StrictModel

RequestKind = Literal[
    "towels",
    "toiletries",
    "pillows",
    "cleaning",
    "turndown",
    "maintenance",
    "wake_up",
    "late_checkout",
    "luggage",
    "other",
]
RequestStatus = Literal["open", "acknowledged", "in_progress", "done", "cancelled"]
Note = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class GuestRequestCreate(StrictModel):
    kind: RequestKind
    note: Note | None = None
    # When it is wanted: required for a wake-up call, the asked-for time for a late checkout.
    due_at: datetime | None = None


class StaffRequestCreate(GuestRequestCreate):
    room_id: uuid.UUID


class CancelRequest(StrictModel):
    reason: Reason | None = None


class AssignRequestTo(StrictModel):
    user_id: uuid.UUID


class Person(BaseModel):
    id: uuid.UUID
    name: str


class GuestRequestOut(BaseModel):
    """What the room's tablet sees: no staff names, only progress."""

    id: uuid.UUID
    kind: RequestKind
    note: str | None
    due_at: datetime | None
    status: RequestStatus
    created_at: datetime
    acknowledged_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None


class GuestRequestList(BaseModel):
    data: list[GuestRequestOut]


class RequestOut(GuestRequestOut):
    room_id: uuid.UUID
    room: str
    stay_id: uuid.UUID | None
    source: Literal["guest", "staff"]
    created_by: Person | None
    assigned_to: Person | None
    started_at: datetime | None
    cancelled_by: Literal["guest", "staff"] | None
    cancel_reason: str | None
    waiting_minutes: int


class RequestSummary(BaseModel):
    open: int
    in_progress: int
    done_today: int
    # Median minutes from request to done over the last 7 days; None until something is done.
    median_minutes_to_done: int | None


class RequestList(BaseModel):
    data: list[RequestOut]
    summary: RequestSummary
    next_cursor: str | None = None
