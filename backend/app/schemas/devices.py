"""Devices: pairing, device tokens, heartbeat and the registry."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.schemas.common import StrictModel

DeviceKind = Literal["guest", "kitchen"]
StoredStatus = Literal["active", "locked", "disabled", "reset_required", "revoked"]
Connection = Literal["online", "offline", "needs_pairing"]
Command = Literal["RESET", "LOCK"]
ShortStr = Annotated[str, StringConstraints(max_length=80)]


class PairingCreate(StrictModel):
    type: DeviceKind
    room_id: uuid.UUID | None = None
    station_id: uuid.UUID | None = None
    station_ids: Annotated[list[uuid.UUID], Field(max_length=20)] | None = None

    @model_validator(mode="after")
    def _target(self) -> PairingCreate:
        stations = [*(self.station_ids or []), *([self.station_id] if self.station_id else [])]
        if self.type == "guest" and (self.room_id is None or stations):
            raise ValueError("A guest tablet pairs to one room_id.")
        if self.type == "kitchen" and (self.room_id is not None or not stations):
            raise ValueError("A kitchen display pairs to one or more stations.")
        return self

    def stations(self) -> list[uuid.UUID]:
        return list(
            dict.fromkeys([*(self.station_ids or []), *([self.station_id] if self.station_id else [])])
        )


class PairingOut(BaseModel):
    code: str
    qr_payload: str
    expires_at: datetime


class DeviceInfo(StrictModel):
    model: ShortStr | None = None
    os: ShortStr | None = None
    app_version: Annotated[str, StringConstraints(max_length=40)] | None = None


class PairRequest(StrictModel):
    code: Annotated[str, StringConstraints(pattern=r"^\d{6}$")]
    device_info: DeviceInfo = Field(default_factory=DeviceInfo)


class Ref(BaseModel):
    id: uuid.UUID
    name: str


class RoomRef(BaseModel):
    id: uuid.UUID
    number: str


class PairResponse(BaseModel):
    device_id: uuid.UUID
    device_credential: str | None = Field(
        description="Shown once. A replay of this request returns null; pair again with a new code."
    )
    label: str
    kind: DeviceKind
    hotel: Ref
    room: RoomRef | None
    stations: list[Ref]


class DeviceTokenRequest(StrictModel):
    device_credential: Annotated[str, StringConstraints(min_length=10, max_length=200)]


class DeviceTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int
    device_id: uuid.UUID


class HeartbeatRequest(StrictModel):
    app_version: Annotated[str, StringConstraints(max_length=40)] | None = None
    battery: Annotated[int, Field(ge=0, le=100)] | None = None
    network: Annotated[str, StringConstraints(max_length=40)] | None = None
    completed_commands: Annotated[list[Command], Field(max_length=4)] = Field(default_factory=list)


class HeartbeatResponse(BaseModel):
    status: StoredStatus
    commands: list[Command]
    server_time: datetime


class DeviceOut(BaseModel):
    id: uuid.UUID
    label: str
    kind: DeviceKind
    status: StoredStatus
    connection: Connection
    room: RoomRef | None
    stations: list[Ref]
    os: str | None
    app_version: str | None
    last_seen_at: datetime | None
    paired_at: datetime | None
    created_at: datetime


class DeviceList(BaseModel):
    data: list[DeviceOut]
    next_cursor: str | None = None


class ReassignRequest(StrictModel):
    room_id: uuid.UUID
