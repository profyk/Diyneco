"""/admin: the platform admin panel (platform token with MFA), plus the hotel's own view of
support access (/support-access)."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission, state_of
from app.schemas.admin import (
    ActivityList,
    AdminHotelDetail,
    AdminHotelList,
    FlagList,
    FlagPatch,
    Health,
    HotelStatusOut,
    Metrics,
    PlanCreate,
    PlanList,
    PlanOut,
    PlanPatch,
    SubscriptionOut,
    SubscriptionPut,
    SupportAccessOut,
    SupportGrantList,
    SupportGrantOut,
    SupportRequest,
    SuspendRequest,
)
from app.services import admin as svc

router = APIRouter(prefix="/admin", tags=["admin"])
hotel_router = APIRouter(tags=["support-access"])

PlatformMetrics = Annotated[Principal, Depends(require_permission("platform.metrics"))]
TenantsRead = Annotated[Principal, Depends(require_permission("platform.tenants.read"))]
TenantsManage = Annotated[Principal, Depends(require_permission("platform.tenants.manage"))]
BillingManage = Annotated[Principal, Depends(require_permission("platform.billing.manage"))]
FlagsManage = Annotated[Principal, Depends(require_permission("platform.flags.manage"))]
Support = Annotated[Principal, Depends(require_permission("platform.support"))]
AuditRead = Annotated[Principal, Depends(require_permission("audit.read"))]
HotelUpdate = Annotated[Principal, Depends(require_permission("hotel.update"))]


@router.get("/metrics", response_model=Metrics)
async def metrics(uow: Uow, principal: PlatformMetrics) -> dict[str, Any]:
    return await svc.metrics(uow)


@router.get("/health", response_model=Health)
async def health(request: Request, uow: Uow, principal: PlatformMetrics) -> dict[str, Any]:
    return await svc.health(state_of(request), uow, getattr(request.app.state, "realtime_hub", None))


@router.get("/hotels", response_model=AdminHotelList)
async def hotels(uow: Uow, principal: TenantsRead) -> dict[str, Any]:
    return {"data": await svc.hotels(uow), "next_cursor": None}


@router.get("/hotels/{hotel_id}", response_model=AdminHotelDetail)
async def hotel_detail(
    hotel_id: uuid.UUID, request: Request, uow: Uow, principal: TenantsRead
) -> dict[str, Any]:
    """One hotel: contacts, subscription, usage, support access and platform actions taken."""
    return await svc.hotel_detail(uow, principal.for_hotel(request, hotel_id))


@router.get("/activity", response_model=ActivityList)
async def activity(
    uow: Uow, principal: PlatformMetrics, hours: Annotated[int, Query(ge=1, le=24)] = 24
) -> dict[str, Any]:
    return {"data": await svc.activity(uow, hours), "next_cursor": None}


async def _status(
    request: Request,
    uow: Uow,
    principal: Principal,
    idem: Any,
    hotel_id: uuid.UUID,
    action: str,
    reason: str | None,
) -> Response:
    result = await svc.set_status(
        state_of(request), uow, principal.for_hotel(request, hotel_id), action, reason
    )
    response: Response = await idem.complete(
        uow, 200, HotelStatusOut.model_validate(result).model_dump(mode="json")
    )
    return response


@router.post("/hotels/{hotel_id}/approve", response_model=HotelStatusOut)
async def approve(
    idem: IdemUser, hotel_id: uuid.UUID, request: Request, uow: Uow, principal: TenantsManage
) -> Response:
    return await _status(request, uow, principal, idem, hotel_id, "approve", None)


@router.post("/hotels/{hotel_id}/suspend", response_model=HotelStatusOut)
async def suspend(
    idem: IdemUser,
    hotel_id: uuid.UUID,
    body: SuspendRequest,
    request: Request,
    uow: Uow,
    principal: TenantsManage,
    _s: StepUp,
) -> Response:
    return await _status(request, uow, principal, idem, hotel_id, "suspend", body.reason)


@router.post("/hotels/{hotel_id}/reactivate", response_model=HotelStatusOut)
async def reactivate(
    idem: IdemUser, hotel_id: uuid.UUID, request: Request, uow: Uow, principal: TenantsManage
) -> Response:
    return await _status(request, uow, principal, idem, hotel_id, "reactivate", None)


@router.put("/hotels/{hotel_id}/subscription", response_model=SubscriptionOut)
async def put_subscription(
    hotel_id: uuid.UUID, body: SubscriptionPut, request: Request, uow: Uow, principal: BillingManage
) -> dict[str, Any]:
    return await svc.put_subscription(uow, principal.for_hotel(request, hotel_id), body.model_dump())


@router.get("/plans", response_model=PlanList)
async def plans(uow: Uow, principal: BillingManage) -> dict[str, Any]:
    return {"data": await svc.list_plans(uow), "next_cursor": None}


@router.post("/plans", status_code=201, response_model=PlanOut)
async def create_plan(
    idem: IdemUser, body: PlanCreate, request: Request, uow: Uow, principal: BillingManage
) -> Response:
    result = await svc.create_plan(uow, principal.platform_actor(request), body.model_dump())
    return await idem.complete(uow, 201, PlanOut.model_validate(result).model_dump(mode="json"))


@router.patch("/plans/{plan_id}", response_model=PlanOut)
async def update_plan(
    plan_id: uuid.UUID, body: PlanPatch, request: Request, uow: Uow, principal: BillingManage
) -> dict[str, Any]:
    return await svc.update_plan(
        uow, principal.platform_actor(request), plan_id, body.model_dump(exclude_unset=True)
    )


@router.get("/feature-flags", response_model=FlagList)
async def flags(uow: Uow, principal: FlagsManage) -> dict[str, Any]:
    return {"data": await svc.list_flags(uow), "next_cursor": None}


@router.patch("/feature-flags", response_model=FlagList)
async def set_flags(body: FlagPatch, request: Request, uow: Uow, principal: FlagsManage) -> dict[str, Any]:
    changes = [c.model_dump() for c in body.changes]
    return {"data": await svc.set_flags(uow, principal.platform_actor(request), changes), "next_cursor": None}


@router.post("/hotels/{hotel_id}/support-access", status_code=201, response_model=SupportAccessOut)
async def support_access(
    idem: IdemUser,
    hotel_id: uuid.UUID,
    body: SupportRequest,
    request: Request,
    uow: Uow,
    principal: Support,
    _s: StepUp,
) -> Response:
    result = await svc.grant_support(
        state_of(request),
        uow,
        principal.for_hotel(request, hotel_id),
        body.model_dump(),
        session_id=principal.sid,
        amr=principal.amr,
    )
    return await idem.complete(uow, 201, SupportAccessOut.model_validate(result).model_dump(mode="json"))


# --- The hotel's view ----------------------------------------------------------------------


@hotel_router.get("/support-access", response_model=SupportGrantList)
async def hotel_grants(request: Request, uow: Uow, principal: AuditRead) -> dict[str, Any]:
    return {"data": await svc.list_grants(uow, principal.tenant(request)), "next_cursor": None}


@hotel_router.post("/support-access/{grant_id}/revoke", response_model=SupportGrantOut)
async def revoke_grant(
    grant_id: uuid.UUID, request: Request, uow: Uow, principal: HotelUpdate
) -> dict[str, Any]:
    return await svc.revoke_grant(uow, principal.tenant(request), grant_id)
