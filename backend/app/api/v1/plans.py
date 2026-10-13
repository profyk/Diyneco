"""Plans & Pricing (DECISIONS D74): /admin/plans for billing administrators, /admin/billing-settings,
and the public pricing page (/plans)."""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission, state_of
from app.core.errors import AppError
from app.schemas.plans import (
    BillingSettingsOut,
    BillingSettingsPut,
    PlanCreate,
    PlanList,
    PlanOut,
    PlanPatch,
    PlanStatusChange,
    PriceCreate,
    PublicPlan,
    PublicPlanList,
)
from app.services import catalogue as svc

router = APIRouter(prefix="/admin", tags=["admin"])
public_router = APIRouter(tags=["plans"])

BillingManage = Annotated[Principal, Depends(require_permission("platform.billing.manage"))]


def _out(plan: dict[str, Any]) -> dict[str, Any]:
    return PlanOut.model_validate(plan).model_dump(mode="json")


@public_router.get("/plans", response_model=PublicPlanList)
async def public_plans(uow: Uow) -> dict[str, Any]:
    """Published plans with their prices in force (public: the pricing page and signup)."""
    return await svc.public_plans(uow)


@router.get("/plans", response_model=PlanList)
async def plans(uow: Uow, principal: BillingManage) -> dict[str, Any]:
    return {"data": await svc.list_plans(uow), "next_cursor": None}


@router.post("/plans", status_code=201, response_model=PlanOut)
async def create_plan(
    idem: IdemUser, body: PlanCreate, request: Request, uow: Uow, principal: BillingManage
) -> Response:
    """A new plan starts as a draft; price it, preview it, then publish it."""
    plan = await svc.create_plan(uow, principal.platform_actor(request), body.model_dump(exclude_unset=True))
    return await idem.complete(uow, 201, _out(plan))


@router.patch("/plans/{plan_id}", response_model=PlanOut)
async def update_plan(
    plan_id: uuid.UUID, body: PlanPatch, request: Request, uow: Uow, principal: BillingManage
) -> dict[str, Any]:
    """Details, limits and features. `version` must match (else 412); a published plan needs a
    `reason`. Prices change through /prices."""
    return await svc.update_plan(
        uow, principal.platform_actor(request), plan_id, body.model_dump(exclude_unset=True)
    )


@router.get("/plans/{plan_id}/preview", response_model=PublicPlan)
async def preview_plan(plan_id: uuid.UUID, uow: Uow, principal: BillingManage) -> dict[str, Any]:
    return await svc.preview(uow, plan_id)


@router.post("/plans/{plan_id}/prices", status_code=201, response_model=PlanOut)
async def add_price(
    idem: IdemUser,
    plan_id: uuid.UUID,
    body: PriceCreate,
    request: Request,
    uow: Uow,
    principal: BillingManage,
    _s: StepUp,
) -> Response:
    plan = await svc.add_price(uow, principal.platform_actor(request), plan_id, body.model_dump())
    return await idem.complete(uow, 201, _out(plan))


@router.delete("/plans/{plan_id}/prices/{price_id}", response_model=PlanOut)
async def withdraw_price(
    plan_id: uuid.UUID, price_id: uuid.UUID, request: Request, uow: Uow, principal: BillingManage, _s: StepUp
) -> dict[str, Any]:
    """Withdraws a scheduled price that is not yet in force."""
    return await svc.withdraw_price(uow, principal.platform_actor(request), plan_id, price_id)


async def _transition(
    action: Literal["publish", "archive", "restore"],
    idem: IdemUser,
    plan_id: uuid.UUID,
    body: PlanStatusChange,
    request: Request,
    uow: Uow,
    principal: Principal,
) -> Response:
    plan = await svc.set_status(uow, principal.platform_actor(request), plan_id, action, body.reason)
    return await idem.complete(uow, 200, _out(plan))


@router.post("/plans/{plan_id}/publish", response_model=PlanOut)
async def publish_plan(
    idem: IdemUser,
    plan_id: uuid.UUID,
    body: PlanStatusChange,
    request: Request,
    uow: Uow,
    principal: BillingManage,
    _s: StepUp,
) -> Response:
    """Puts the plan on sale. Needs a price in force; confirmed with step-up."""
    return await _transition("publish", idem, plan_id, body, request, uow, principal)


@router.post("/plans/{plan_id}/archive", response_model=PlanOut)
async def archive_plan(
    idem: IdemUser,
    plan_id: uuid.UUID,
    body: PlanStatusChange,
    request: Request,
    uow: Uow,
    principal: BillingManage,
    _s: StepUp,
) -> Response:
    """Takes the plan off sale; hotels already on it keep it."""
    return await _transition("archive", idem, plan_id, body, request, uow, principal)


@router.post("/plans/{plan_id}/restore", response_model=PlanOut)
async def restore_plan(
    idem: IdemUser,
    plan_id: uuid.UUID,
    body: PlanStatusChange,
    request: Request,
    uow: Uow,
    principal: BillingManage,
) -> Response:
    """Brings an archived plan back as a draft."""
    return await _transition("restore", idem, plan_id, body, request, uow, principal)


@router.get("/billing-settings", response_model=BillingSettingsOut)
async def get_billing_settings(uow: Uow, principal: BillingManage) -> dict[str, Any]:
    return await svc.billing_settings(uow)


@router.put("/billing-settings", response_model=BillingSettingsOut)
async def put_billing_settings(
    body: BillingSettingsPut, request: Request, uow: Uow, principal: BillingManage, _s: StepUp
) -> dict[str, Any]:
    settings = state_of(request).settings
    if body.card_provider == "stitch" and not settings.stitch_configured:
        raise AppError("INVALID_TRANSITION", "Stitch is not configured on this server (STITCH_* variables).")
    if body.card_provider == "sandbox" and settings.app_env == "production":
        raise AppError("INVALID_TRANSITION", "The sandbox cannot take payments in production.")
    return await svc.put_billing_settings(uow, principal.platform_actor(request), body.model_dump())
