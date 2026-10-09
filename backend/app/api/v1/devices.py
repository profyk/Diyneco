"""/devices: registry, pairing, device tokens and heartbeat.

Every state-changing device operation takes an Idempotency-Key (CLAUDE.md rule; DECISIONS
D24), including lock, unlock, reset, disable, reassign and unpair.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from app.api.deps import (
    DeviceAnyState,
    IdemAnon,
    IdemUser,
    Principal,
    StepUp,
    Uow,
    client_ip,
    limit_auth_ip,
    require_permission,
    state_of,
)
from app.api.pagination import DEFAULT_LIMIT, Cursor, Limit, decode_cursor, page
from app.core.logging import request_id_var
from app.schemas.devices import (
    DeviceKind,
    DeviceList,
    DeviceOut,
    DeviceTokenRequest,
    DeviceTokenResponse,
    HeartbeatRequest,
    HeartbeatResponse,
    PairingCreate,
    PairingOut,
    PairRequest,
    PairResponse,
    ReassignRequest,
    StoredStatus,
)
from app.services import devices as svc
from app.services.idempotency import IdempotencyClaim

router = APIRouter(prefix="/devices", tags=["devices"])

DevicesRead = Annotated[Principal, Depends(require_permission("devices.read"))]
DevicesManage = Annotated[Principal, Depends(require_permission("devices.manage"))]


@router.get("", response_model=DeviceList)
async def list_devices(
    request: Request,
    uow: Uow,
    principal: DevicesRead,
    type: Annotated[DeviceKind | None, Query()] = None,
    status: Annotated[StoredStatus | None, Query()] = None,
    room_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Limit = DEFAULT_LIMIT,
    cursor: Cursor = None,
) -> dict[str, Any]:
    rows = await svc.list_devices(
        uow,
        principal.tenant(request),
        kind=type,
        status=status,
        room_id=room_id,
        after=decode_cursor(cursor, 1),
        limit=limit,
    )
    data, next_cursor = page(rows, limit, lambda d: [d["label"]])
    return {"data": data, "next_cursor": next_cursor}


@router.post("/pairings", status_code=201, response_model=PairingOut)
async def create_pairing(
    idem: IdemUser, body: PairingCreate, request: Request, uow: Uow, principal: DevicesManage
) -> Response:
    result = await svc.create_pairing(
        state_of(request), uow, principal.tenant(request), body.type, body.room_id, body.stations()
    )
    return await idem.complete(uow, 201, PairingOut.model_validate(result).model_dump(mode="json"))


@router.post("/pair", status_code=201, response_model=PairResponse, dependencies=[Depends(limit_auth_ip)])
async def pair_device(idem: IdemAnon, body: PairRequest, request: Request, uow: Uow) -> Response:
    """Redeems a pairing code. The credential is in this response only; a replay of the same
    request returns `device_credential: null` (DECISIONS D23)."""
    result = await svc.pair(
        state_of(request),
        uow,
        body.code,
        body.device_info.model_dump(),
        client_ip(request),
        request_id_var.get(),
    )
    out = PairResponse.model_validate(result).model_dump(mode="json")
    return await idem.complete(uow, 201, out, store={**out, "device_credential": None})


@router.post("/token", response_model=DeviceTokenResponse, dependencies=[Depends(limit_auth_ip)])
async def device_token(body: DeviceTokenRequest, request: Request, uow: Uow) -> dict[str, Any]:
    """Exchanges the device credential for a 1-hour device token (security spec, Credentials)."""
    return await svc.issue_token(state_of(request), uow, body.device_credential, client_ip(request))


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def heartbeat(
    body: HeartbeatRequest, request: Request, uow: Uow, _device: DeviceAnyState
) -> dict[str, Any]:
    return await svc.heartbeat(uow, request.state.device, body.model_dump(), client_ip(request))


@router.get("/{device_id}", response_model=DeviceOut)
async def get_device(
    device_id: uuid.UUID, request: Request, uow: Uow, principal: DevicesRead
) -> dict[str, Any]:
    return await svc.get_device(uow, principal.tenant(request), device_id)


async def _action(
    idem: IdempotencyClaim,
    request: Request,
    uow: Uow,
    principal: Principal,
    device_id: uuid.UUID,
    action: str,
) -> Response:
    result = await svc.change_state(uow, principal.tenant(request), device_id, action)
    return await idem.complete(uow, 200, DeviceOut.model_validate(result).model_dump(mode="json"))


@router.post("/{device_id}/lock", response_model=DeviceOut)
async def lock_device(
    idem: IdemUser, device_id: uuid.UUID, request: Request, uow: Uow, principal: DevicesManage
) -> Response:
    return await _action(idem, request, uow, principal, device_id, "lock")


@router.post("/{device_id}/unlock", response_model=DeviceOut)
async def unlock_device(
    idem: IdemUser, device_id: uuid.UUID, request: Request, uow: Uow, principal: DevicesManage
) -> Response:
    """Returns a locked or disabled device to active."""
    return await _action(idem, request, uow, principal, device_id, "unlock")


@router.post("/{device_id}/reset", response_model=DeviceOut)
async def reset_device(
    idem: IdemUser, device_id: uuid.UUID, request: Request, uow: Uow, principal: DevicesManage
) -> Response:
    return await _action(idem, request, uow, principal, device_id, "reset")


@router.post("/{device_id}/disable", response_model=DeviceOut)
async def disable_device(
    idem: IdemUser, device_id: uuid.UUID, request: Request, uow: Uow, principal: DevicesManage
) -> Response:
    return await _action(idem, request, uow, principal, device_id, "disable")


@router.post("/{device_id}/reassign", response_model=DeviceOut)
async def reassign_device(
    idem: IdemUser,
    device_id: uuid.UUID,
    body: ReassignRequest,
    request: Request,
    uow: Uow,
    principal: DevicesManage,
    _s: StepUp,
) -> Response:
    result = await svc.reassign(uow, principal.tenant(request), device_id, body.room_id)
    return await idem.complete(uow, 200, DeviceOut.model_validate(result).model_dump(mode="json"))


@router.delete("/{device_id}/pairing", status_code=204)
async def unpair_device(
    idem: IdemUser, device_id: uuid.UUID, request: Request, uow: Uow, principal: DevicesManage, _s: StepUp
) -> Response:
    await svc.revoke(uow, principal.tenant(request), device_id)
    return await idem.complete(uow, 204, None)
