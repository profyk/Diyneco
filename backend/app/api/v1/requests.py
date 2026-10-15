"""/requests: guest service requests for staff (D93). The room's tablet uses /guest/requests."""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import IdemUser, Principal, Uow, require_permission
from app.schemas.requests import (
    AssignRequestTo,
    CancelRequest,
    RequestKind,
    RequestList,
    RequestOut,
    StaffRequestCreate,
)
from app.services import requests as svc

router = APIRouter(prefix="/requests", tags=["requests"])

RequestsView = Annotated[Principal, Depends(require_permission("requests.view"))]
RequestsUpdate = Annotated[Principal, Depends(require_permission("requests.update"))]


@router.get("", response_model=RequestList)
async def list_requests(
    request: Request,
    uow: Uow,
    principal: RequestsView,
    scope: Annotated[Literal["open", "mine", "recent"], Query()] = "open",
    kind: Annotated[RequestKind | None, Query()] = None,
    room_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 200,
) -> dict[str, Any]:
    """`open`: waiting or under way, oldest first. `mine`: those assigned to me. `recent`: the
    last 7 days, newest first."""
    ctx = principal.tenant(request)
    rows = await svc.list_requests(uow, ctx, scope=scope, kind=kind, room_id=room_id, limit=limit)
    return {"data": rows, "summary": await svc.summary(uow, ctx), "next_cursor": None}


async def _done(idem: Any, uow: Uow, result: dict[str, Any], status: int = 200) -> Response:
    response: Response = await idem.complete(
        uow, status, RequestOut.model_validate(result).model_dump(mode="json")
    )
    return response


@router.post("", status_code=201, response_model=RequestOut)
async def log_request(
    idem: IdemUser, body: StaffRequestCreate, request: Request, uow: Uow, principal: RequestsUpdate
) -> Response:
    """A request taken by phone or at the desk, for any room (with or without a guest)."""
    result = await svc.create_by_staff(uow, principal.tenant(request), body.model_dump())
    return await _done(idem, uow, result, 201)


@router.post("/{request_id}/acknowledge", response_model=RequestOut)
async def acknowledge(
    idem: IdemUser, request_id: uuid.UUID, request: Request, uow: Uow, principal: RequestsUpdate
) -> Response:
    return await _done(idem, uow, await svc.acknowledge(uow, principal.tenant(request), request_id))


@router.post("/{request_id}/start", response_model=RequestOut)
async def start(
    idem: IdemUser, request_id: uuid.UUID, request: Request, uow: Uow, principal: RequestsUpdate
) -> Response:
    return await _done(idem, uow, await svc.start(uow, principal.tenant(request), request_id))


@router.post("/{request_id}/done", response_model=RequestOut)
async def done(
    idem: IdemUser, request_id: uuid.UUID, request: Request, uow: Uow, principal: RequestsUpdate
) -> Response:
    return await _done(idem, uow, await svc.complete(uow, principal.tenant(request), request_id))


@router.post("/{request_id}/assign", response_model=RequestOut)
async def assign(
    idem: IdemUser,
    request_id: uuid.UUID,
    body: AssignRequestTo,
    request: Request,
    uow: Uow,
    principal: RequestsUpdate,
) -> Response:
    return await _done(idem, uow, await svc.assign(uow, principal.tenant(request), request_id, body.user_id))


@router.post("/{request_id}/cancel", response_model=RequestOut)
async def cancel(
    idem: IdemUser,
    request_id: uuid.UUID,
    body: CancelRequest,
    request: Request,
    uow: Uow,
    principal: RequestsUpdate,
) -> Response:
    result = await svc.cancel_by_staff(uow, principal.tenant(request), request_id, body.reason)
    return await _done(idem, uow, result)
