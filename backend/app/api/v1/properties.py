"""/hotels (add a property) and /portfolio (every property the caller owns), DECISIONS D86."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, Response

from app.api.deps import CurrentPrincipal, IdemUser, StepUp, Uow, client_ip, state_of
from app.core.errors import AppError
from app.core.logging import request_id_var
from app.schemas.properties import AddPropertyOut, AddPropertyRequest, PortfolioOut
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


@router.get("/portfolio", response_model=PortfolioOut)
async def portfolio(request: Request, uow: Uow, principal: CurrentPrincipal) -> dict[str, Any]:
    """Every property the caller owns side by side: occupancy, stays, open orders and revenue
    today and this month, with totals per currency."""
    return await svc.portfolio(uow, _user(principal), principal.tenant(request))
