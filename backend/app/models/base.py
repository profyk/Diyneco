"""Declarative base and column helpers.

The migrations are the schema's source of truth; these models mirror them for typed queries.
tests/db/test_model_drift.py fails if a model and the migrated table disagree on columns,
types or nullability. Defaults live in the database (server_default), so the ORM never
invents ids, timestamps or money values.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Any

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Integer,
    LargeBinary,
    MetaData,
    SmallInteger,
    String,
    Text,
    Time,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, CITEXT, INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__ = [
    "ARRAY",
    "CHAR",
    "CITEXT",
    "INET",
    "JSONB",
    "UUID",
    "Base",
    "BigInteger",
    "Boolean",
    "Date",
    "DateTime",
    "Integer",
    "LargeBinary",
    "Mapped",
    "SmallInteger",
    "String",
    "Text",
    "Time",
    "date",
    "datetime",
    "mapped_column",
    "time",
    "uuid",
]


class Base(DeclarativeBase):
    metadata = MetaData(schema="app")
    type_annotation_map: dict[Any, Any] = {  # noqa: RUF012
        uuid.UUID: UUID(as_uuid=True),
        datetime: DateTime(timezone=True),
        date: Date,
        time: Time,
        str: Text,
        int: Integer,
        bool: Boolean,
        bytes: LargeBinary,
        dict[str, Any]: JSONB,
        list[Any]: JSONB,
    }


def pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("app.uuid_v7()"))


def created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=text("now()"))


def updated_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=text("now()"))


def money() -> Mapped[int]:
    return mapped_column(BigInteger)


def currency() -> Mapped[str]:
    return mapped_column(CHAR(3), server_default=text("'ZAR'"))


def version() -> Mapped[int]:
    return mapped_column(Integer, server_default=text("1"))


def text_array() -> Mapped[list[str]]:
    return mapped_column(ARRAY(Text), server_default=text("'{}'"))
