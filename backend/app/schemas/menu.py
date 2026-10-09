"""Kitchen stations, menu schedules, categories, items and modifiers."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.schemas.common import Money, Name, StrictModel

Allergen = Literal[
    "gluten",
    "crustaceans",
    "egg",
    "fish",
    "peanuts",
    "soy",
    "dairy",
    "tree_nuts",
    "celery",
    "mustard",
    "sesame",
    "sulphites",
    "lupin",
    "molluscs",
]
DietaryTag = Literal["vegetarian", "vegan", "halaal", "kosher", "gluten_free"]
ChargeCategory = Literal["food", "beverage"]
SortOrder = Annotated[int, Field(ge=-1000, le=1000, strict=True)]
Description = Annotated[str, StringConstraints(max_length=1000)]
HHMM = Annotated[str, StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]
VatRate = Annotated[int, Field(ge=0, le=10000, strict=True)]


# --- Stations ------------------------------------------------------------------------------


class StationCreate(StrictModel):
    name: Name
    sort_order: SortOrder = 0


class StationPatch(StrictModel):
    name: Name | None = None
    sort_order: SortOrder | None = None
    is_active: bool | None = None


class StationOut(BaseModel):
    id: uuid.UUID
    name: str
    sort_order: int
    is_active: bool


class StationList(BaseModel):
    data: list[StationOut]
    next_cursor: str | None = None


# --- Schedules -----------------------------------------------------------------------------


class Window(StrictModel):
    days: Annotated[list[Annotated[int, Field(ge=1, le=7)]], Field(min_length=1, max_length=7)]
    from_: Annotated[HHMM, Field(alias="from")]
    to: HHMM

    @field_validator("days")
    @classmethod
    def _unique(cls, v: list[int]) -> list[int]:
        return sorted(set(v))


class ScheduleCreate(StrictModel):
    name: Name
    windows: Annotated[list[Window], Field(min_length=1, max_length=21)]


class ScheduleOut(BaseModel):
    id: uuid.UUID
    name: str
    windows: list[dict[str, object]]


class ScheduleList(BaseModel):
    data: list[ScheduleOut]
    next_cursor: str | None = None


# --- Categories ----------------------------------------------------------------------------


class CategoryCreate(StrictModel):
    name: Name
    sort_order: SortOrder = 0
    schedule_id: uuid.UUID | None = None


class CategoryPatch(StrictModel):
    name: Name | None = None
    sort_order: SortOrder | None = None
    schedule_id: uuid.UUID | None = None


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    sort_order: int
    schedule_id: uuid.UUID | None


class CategoryList(BaseModel):
    data: list[CategoryOut]
    next_cursor: str | None = None


# --- Items ---------------------------------------------------------------------------------


class ItemCreate(StrictModel):
    name: Name
    description: Description | None = None
    price: Money
    vat_rate_bp: VatRate | None = None  # None: the hotel's VAT rate
    charge_category: ChargeCategory = "food"
    station_id: uuid.UUID
    category_id: uuid.UUID
    schedule_id: uuid.UUID | None = None
    dietary_tags: Annotated[list[DietaryTag], Field(max_length=5)] = Field(default_factory=list)
    allergens: Annotated[list[Allergen], Field(max_length=14)] = Field(default_factory=list)
    sort_order: SortOrder = 0


class ItemPatch(StrictModel):
    name: Name | None = None
    description: Description | None = None
    price: Money | None = None
    vat_rate_bp: VatRate | None = None
    charge_category: ChargeCategory | None = None
    station_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    schedule_id: uuid.UUID | None = None
    dietary_tags: Annotated[list[DietaryTag], Field(max_length=5)] | None = None
    allergens: Annotated[list[Allergen], Field(max_length=14)] | None = None
    sort_order: SortOrder | None = None


class AvailabilityChange(StrictModel):
    available: bool


class ImageUploadRequest(StrictModel):
    content_type: Literal["image/jpeg", "image/webp"]
    size_bytes: Annotated[int, Field(ge=1, le=5 * 1024 * 1024, strict=True)]


class ModifierOptionOut(BaseModel):
    id: uuid.UUID
    name: str
    price_delta: Money
    is_available: bool
    sort_order: int


class ModifierGroupOut(BaseModel):
    id: uuid.UUID
    name: str
    min_select: int
    max_select: int
    options: list[ModifierOptionOut]


class ItemOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    price: Money
    vat_rate_bp: int | None
    charge_category: ChargeCategory
    station_id: uuid.UUID
    category_id: uuid.UUID
    schedule_id: uuid.UUID | None
    is_available: bool
    available_now: bool
    next_available_at: datetime | None = None
    dietary_tags: list[str]
    allergens: list[str]
    image_url: str | None
    sort_order: int
    modifier_groups: list[ModifierGroupOut]
    version: int
    updated_at: datetime


class ItemList(BaseModel):
    data: list[ItemOut]
    next_cursor: str | None = None


# --- Modifiers -----------------------------------------------------------------------------


class ModifierGroupCreate(StrictModel):
    name: Name
    min_select: Annotated[int, Field(ge=0, le=20, strict=True)] = 0
    max_select: Annotated[int, Field(ge=1, le=20, strict=True)] = 1


class ModifierOptionCreate(StrictModel):
    name: Name
    price_delta: Money
    sort_order: SortOrder = 0


class ModifierGroupList(BaseModel):
    data: list[ModifierGroupOut]
    next_cursor: str | None = None


class ItemModifierGroups(StrictModel):
    group_ids: Annotated[list[uuid.UUID], Field(max_length=10)]


class ImageUploadOut(BaseModel):
    upload_url: str
    method: str
    headers: dict[str, str]
    expires_at: datetime
    max_bytes: int
