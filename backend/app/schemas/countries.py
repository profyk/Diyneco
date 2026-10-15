"""Operational countries in the admin panel (D84)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.schemas.common import StrictModel
from app.schemas.company import Reason
from app.schemas.hotel import CountryOut

CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]


class AdminCountryOut(CountryOut):
    operational: bool  # new hotels can sign up there
    enabled_at: datetime | None
    hotels: int
    active_hotels: int


class AdminCountryList(BaseModel):
    data: list[AdminCountryOut]


class CountryPut(StrictModel):
    operational: bool
    reason: Reason
