"""Room types and rooms."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import Money, Name, StrictModel

Amenity = Annotated[str, StringConstraints(min_length=1, max_length=60)]
Amenities = Annotated[list[Amenity], Field(max_length=50)]
Capacity = Annotated[int, Field(ge=1, le=20, strict=True)]
RoomNumber = Annotated[str, StringConstraints(min_length=1, max_length=40)]
Floor = Annotated[str, StringConstraints(min_length=1, max_length=20)]
ManualStatus = Literal["available", "reserved", "cleaning", "maintenance", "out_of_service"]
RoomStatus = Literal["available", "occupied", "reserved", "cleaning", "maintenance", "out_of_service"]

MAX_BULK_ROOMS = 2000


class RoomTypeCreate(StrictModel):
    name: Name
    base_rate: Money
    capacity: Capacity = 2
    amenities: Amenities = Field(default_factory=list)


class RoomTypePatch(StrictModel):
    name: Name | None = None
    base_rate: Money | None = None
    capacity: Capacity | None = None
    amenities: Amenities | None = None


class RoomTypeOut(BaseModel):
    id: uuid.UUID
    name: str
    base_rate: Money
    capacity: int
    amenities: list[str]
    room_count: int
    version: int
    created_at: datetime
    updated_at: datetime


class RoomTypeList(BaseModel):
    data: list[RoomTypeOut]
    next_cursor: str | None = None


class RoomCreate(StrictModel):
    number: RoomNumber
    floor: Floor | None = None
    room_type_id: uuid.UUID
    rate: Money | None = None  # None: the room type's base rate applies
    capacity: Capacity | None = None
    amenities: Amenities = Field(default_factory=list)


class RoomPatch(StrictModel):
    number: RoomNumber | None = None
    floor: Floor | None = None
    room_type_id: uuid.UUID | None = None
    rate: Money | None = None
    capacity: Capacity | None = None
    amenities: Amenities | None = None


class RoomRange(StrictModel):
    from_: Annotated[int, Field(alias="from", ge=0, le=999_999, strict=True)]
    to: Annotated[int, Field(ge=0, le=999_999, strict=True)]
    floor: Annotated[int | str, Field(union_mode="left_to_right")] | None = None
    room_type_id: uuid.UUID
    prefix: Annotated[str, StringConstraints(max_length=10)] = ""


class RoomBulkCreate(StrictModel):
    ranges: Annotated[list[RoomRange], Field(min_length=1, max_length=100)]


class RoomStatusChange(StrictModel):
    status: ManualStatus


class RoomTypeRef(BaseModel):
    id: uuid.UUID
    name: str


class RoomOut(BaseModel):
    id: uuid.UUID
    number: str
    floor: str | None
    room_type: RoomTypeRef
    rate: Money | None
    effective_rate: Money
    capacity: int
    amenities: list[str]
    status: RoomStatus
    status_changed_at: datetime
    version: int
    created_at: datetime
    updated_at: datetime


class RoomList(BaseModel):
    data: list[RoomOut]
    next_cursor: str | None = None


class BulkResult(BaseModel):
    created: int
    data: list[RoomOut]


class ImportProblem(BaseModel):
    line: int
    field: str
    problem: str


class ImportReport(BaseModel):
    committed: bool
    valid: bool
    rows: int
    errors: list[ImportProblem]
    created: int
