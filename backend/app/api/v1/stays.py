"""/guests, /billing-profiles, /stays and /rooms/{id}/walk-in."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission
from app.api.http import IfMatch, parse_if_match, patch_changes, with_etag
from app.api.pagination import DEFAULT_LIMIT, Cursor, Limit, decode_cursor, page
from app.schemas.stays import (
    AnonymiseOut,
    AnonymiseRequest,
    BillingProfileCreate,
    BillingProfileList,
    BillingProfileOut,
    GuestCreate,
    GuestList,
    GuestOut,
    GuestPatch,
    StayCreate,
    StayDatesPatch,
    StayList,
    StayMove,
    StayOut,
    StayStatus,
    WalkIn,
)
from app.services import privacy
from app.services import stays as svc

router = APIRouter(tags=["stays"])

GuestsRead = Annotated[Principal, Depends(require_permission("guests.read"))]
GuestsManage = Annotated[Principal, Depends(require_permission("guests.manage"))]
PrivacyManage = Annotated[Principal, Depends(require_permission("privacy.manage"))]
BillingManage = Annotated[Principal, Depends(require_permission("billing.manage"))]
StaysRead = Annotated[Principal, Depends(require_permission("stays.read"))]
StaysManage = Annotated[Principal, Depends(require_permission("stays.manage"))]
Search = Annotated[str | None, Query(max_length=100)]


@router.get("/guests", response_model=GuestList)
async def search_guests(
    request: Request, uow: Uow, principal: GuestsRead, q: Search = None, limit: Limit = DEFAULT_LIMIT
) -> dict[str, Any]:
    return {"data": await svc.search_guests(uow, principal.tenant(request), q, limit), "next_cursor": None}


@router.post("/guests", status_code=201, response_model=GuestOut)
async def create_guest(
    idem: IdemUser, body: GuestCreate, request: Request, uow: Uow, principal: GuestsManage
) -> Response:
    guest = await svc.create_guest(uow, principal.tenant(request), body.model_dump())
    return await idem.complete(
        uow, 201, GuestOut.model_validate(svc.guest_payload(guest)).model_dump(mode="json")
    )


@router.get("/guests/{guest_id}")
async def get_guest(guest_id: uuid.UUID, request: Request, uow: Uow, principal: GuestsRead) -> dict[str, Any]:
    """Profile and stay history."""
    return await svc.get_guest(uow, principal.tenant(request), guest_id)


@router.get("/guests/{guest_id}/export")
async def export_guest(
    guest_id: uuid.UUID, request: Request, uow: Uow, principal: PrivacyManage, _s: StepUp
) -> dict[str, Any]:
    """POPIA access request: everything held about this guest."""
    return await privacy.export_guest(uow, principal.tenant(request), guest_id)


@router.post("/guests/{guest_id}/anonymise", response_model=AnonymiseOut)
async def anonymise_guest(
    idem: IdemUser,
    guest_id: uuid.UUID,
    body: AnonymiseRequest,
    request: Request,
    uow: Uow,
    principal: PrivacyManage,
    _s: StepUp,
) -> Response:
    result = await privacy.anonymise_guest(uow, principal.tenant(request), guest_id, reason=body.reason)
    return await idem.complete(uow, 200, AnonymiseOut.model_validate(result).model_dump(mode="json"))


@router.patch("/guests/{guest_id}", response_model=GuestOut)
async def patch_guest(
    guest_id: uuid.UUID, body: GuestPatch, request: Request, uow: Uow, principal: GuestsManage
) -> dict[str, Any]:
    return await svc.patch_guest(uow, principal.tenant(request), guest_id, patch_changes(body, {"name"}))


@router.get("/billing-profiles", response_model=BillingProfileList)
async def search_profiles(
    request: Request, uow: Uow, principal: GuestsRead, q: Search = None, limit: Limit = DEFAULT_LIMIT
) -> dict[str, Any]:
    return {"data": await svc.search_profiles(uow, principal.tenant(request), q, limit), "next_cursor": None}


@router.post("/billing-profiles", status_code=201, response_model=BillingProfileOut)
async def create_profile(
    idem: IdemUser, body: BillingProfileCreate, request: Request, uow: Uow, principal: BillingManage
) -> Response:
    result = await svc.create_profile(uow, principal.tenant(request), body.model_dump())
    return await idem.complete(uow, 201, BillingProfileOut.model_validate(result).model_dump(mode="json"))


@router.get("/stays", response_model=StayList)
async def list_stays(
    request: Request,
    uow: Uow,
    principal: StaysRead,
    status: Annotated[StayStatus | None, Query()] = None,
    room_id: Annotated[uuid.UUID | None, Query()] = None,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
    limit: Limit = DEFAULT_LIMIT,
    cursor: Cursor = None,
) -> dict[str, Any]:
    rows = await svc.list_stays(
        uow,
        principal.tenant(request),
        status=status,
        room_id=room_id,
        date_from=from_,
        date_to=to,
        after=decode_cursor(cursor, 1),
        limit=limit,
    )
    data, next_cursor = page(rows, limit, lambda r: [str(r[0].id)])
    return {"data": [p for _, p in data], "next_cursor": next_cursor}


@router.post("/stays", status_code=201, response_model=StayOut)
async def create_stay(
    idem: IdemUser, body: StayCreate, request: Request, uow: Uow, principal: StaysManage
) -> Response:
    result = await svc.create_reservation(
        uow, principal.tenant(request), body.model_dump(), principal.permissions
    )
    return await idem.complete(uow, 201, StayOut.model_validate(result).model_dump(mode="json"))


@router.get("/stays/{stay_id}", response_model=StayOut)
async def get_stay(stay_id: uuid.UUID, request: Request, uow: Uow, principal: StaysRead) -> Response:
    result = await svc.get_stay(uow, principal.tenant(request), stay_id)
    return with_etag(result, result["version"], StayOut)


@router.patch("/stays/{stay_id}", response_model=StayOut)
async def change_dates(
    stay_id: uuid.UUID,
    body: StayDatesPatch,
    request: Request,
    uow: Uow,
    principal: StaysManage,
    if_match: IfMatch = None,
) -> Response:
    expected = parse_if_match(if_match)
    changes = patch_changes(body, {"arrival_date", "departure_date"})
    result = await svc.change_dates(uow, principal.tenant(request), stay_id, expected, changes)
    return with_etag(result, result["version"], StayOut)


@router.post("/stays/{stay_id}/move", response_model=StayOut)
async def move_stay(
    idem: IdemUser,
    stay_id: uuid.UUID,
    body: StayMove,
    request: Request,
    uow: Uow,
    principal: StaysManage,
    _s: StepUp,
) -> Response:
    result = await svc.move(uow, principal.tenant(request), stay_id, body.room_id, body.reason)
    return await idem.complete(uow, 200, StayOut.model_validate(result).model_dump(mode="json"))


@router.post("/stays/{stay_id}/check-in", response_model=StayOut)
async def check_in(
    idem: IdemUser, stay_id: uuid.UUID, request: Request, uow: Uow, principal: StaysManage
) -> Response:
    result = await svc.check_in(uow, principal.tenant(request), stay_id)
    return await idem.complete(uow, 200, StayOut.model_validate(result).model_dump(mode="json"))


@router.post("/rooms/{room_id}/walk-in", status_code=201, response_model=StayOut)
async def walk_in(
    idem: IdemUser, room_id: uuid.UUID, body: WalkIn, request: Request, uow: Uow, principal: StaysManage
) -> Response:
    result = await svc.walk_in(
        uow, principal.tenant(request), room_id, body.model_dump(), principal.permissions
    )
    return await idem.complete(uow, 201, StayOut.model_validate(result).model_dump(mode="json"))


@router.post("/stays/{stay_id}/cancel", response_model=StayOut)
async def cancel_stay(
    idem: IdemUser, stay_id: uuid.UUID, request: Request, uow: Uow, principal: StaysManage
) -> Response:
    result = await svc.cancel(uow, principal.tenant(request), stay_id)
    return await idem.complete(uow, 200, StayOut.model_validate(result).model_dump(mode="json"))


@router.post("/stays/{stay_id}/block-charges", response_model=StayOut)
async def block_charges(
    stay_id: uuid.UUID, request: Request, uow: Uow, principal: StaysManage
) -> dict[str, Any]:
    return await svc.set_charges_blocked(uow, principal.tenant(request), stay_id, True)


@router.post("/stays/{stay_id}/unblock-charges", response_model=StayOut)
async def unblock_charges(
    stay_id: uuid.UUID, request: Request, uow: Uow, principal: StaysManage
) -> dict[str, Any]:
    return await svc.set_charges_blocked(uow, principal.tenant(request), stay_id, False)
