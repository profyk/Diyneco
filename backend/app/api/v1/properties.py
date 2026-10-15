"""/hotels (add a property) and /portfolio (every property the caller owns), DECISIONS D86."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Request, Response

from app.api.deps import CurrentPrincipal, IdemUser, StepUp, Uow, client_ip, state_of
from app.core.errors import AppError
from app.core.logging import request_id_var
from app.schemas.properties import (
    AddPropertyOut,
    AddPropertyRequest,
    GroupCheckoutOut,
    GroupPaymentOut,
    GroupPayRequest,
    GroupStatement,
    PortfolioOut,
)
from app.schemas.sub_payments import SandboxOutcome
from app.services import group_billing
from app.services import properties as svc
from app.services.auth import ClientInfo

router = APIRouter(tags=["properties"])


def _user(principal: Any) -> Any:
    if principal.kind != "staff" or principal.user_id is None:
        raise AppError("PERMISSION_DENIED", "Sign in as a hotel owner.")
    return principal.user_id


@router.post("/hotels", status_code=201, response_model=AddPropertyOut)
async def add_property(
    idem: IdemUser, body: AddPropertyRequest, request: Request, uow: Uow, principal: StepUp
) -> Response:
    """A Hotel Owner adds another property with the signup form's hotel details. It starts
    with no subscription (the free trial is once per owner); switch to it with
    POST /auth/refresh {hotel_id}."""
    result = await svc.add_property(
        state_of(request),
        uow,
        user_id=_user(principal),
        hotel=body.hotel.model_dump(mode="json", exclude_none=True),
        client=ClientInfo(
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_id=request_id_var.get(),
            web=False,
        ),
        accepted_documents=body.accepted_documents,
    )
    return await idem.complete(uow, 201, AddPropertyOut.model_validate(result).model_dump(mode="json"))


@router.get("/portfolio/billing", response_model=GroupStatement)
async def group_statement(request: Request, uow: Uow, principal: CurrentPrincipal) -> dict[str, Any]:
    """Every open invoice across the caller's properties and what is due per currency (D89)."""
    return await group_billing.statement(state_of(request), uow, _user(principal), principal.tenant(request))


@router.post("/portfolio/payments", status_code=201, response_model=GroupCheckoutOut)
async def pay_all(
    idem: IdemUser, body: GroupPayRequest, request: Request, uow: Uow, principal: CurrentPrincipal
) -> Response:
    """One checkout for the balance of every open invoice in a currency across the caller's
    properties. Each property keeps its own invoice and receives its own share."""
    out = await group_billing.start(
        state_of(request), uow, _user(principal), principal.tenant(request), body.currency
    )
    return await idem.complete(uow, 201, GroupCheckoutOut.model_validate(out).model_dump(mode="json"))


@router.get("/portfolio/payments/{group_id}", response_model=GroupPaymentOut)
async def check_group_payment(
    group_id: uuid.UUID, request: Request, uow: Uow, principal: CurrentPrincipal
) -> dict[str, Any]:
    """The group payment as the provider reports it now (asked on the server)."""
    return await group_billing.check(
        state_of(request), uow, _user(principal), principal.tenant(request), group_id
    )


@router.post("/portfolio/payments/{group_id}/sandbox", response_model=GroupPaymentOut)
async def group_sandbox(
    idem: IdemUser,
    group_id: uuid.UUID,
    body: SandboxOutcome,
    request: Request,
    uow: Uow,
    principal: CurrentPrincipal,
) -> Response:
    """Test mode only (never in production): finishes a sandbox group checkout; no money moves."""
    out = await group_billing.sandbox_complete(
        state_of(request), uow, _user(principal), principal.tenant(request), group_id, body.outcome
    )
    return await idem.complete(uow, 200, GroupPaymentOut.model_validate(out).model_dump(mode="json"))


@router.get("/portfolio", response_model=PortfolioOut)
async def portfolio(request: Request, uow: Uow, principal: CurrentPrincipal) -> dict[str, Any]:
    """Every property the caller owns side by side: occupancy, stays, open orders and revenue
    today and this month, with totals per currency."""
    return await svc.portfolio(uow, _user(principal), principal.tenant(request))
