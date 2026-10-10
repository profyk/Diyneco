"""/reports, /audit-logs, /subscription, /api-keys and /webhooks, plus /admin/analytics."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import IdemUser, Principal, StepUp, Uow, require_permission, state_of
from app.api.pagination import DEFAULT_LIMIT, Cursor, Limit, decode_cursor, page
from app.billing.folio import business_date
from app.repositories.hotels import HotelRepository
from app.schemas.reports import (
    Analytics,
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyList,
    AuditList,
    ChangeRequest,
    ChangeRequestOut,
    DailyClosePut,
    DailyCloseReport,
    DeliveryList,
    HotelSubscription,
    ItemsReport,
    KitchenReport,
    OccupancyReport,
    OpenBalances,
    OrdersReport,
    PaymentsReport,
    RevenueReport,
    RoomServiceReport,
    WebhookCreate,
    WebhookCreated,
    WebhookList,
    WebhookOut,
    WebhookStatusChange,
    WebhookTestOut,
)
from app.services import admin, integrations, reports, subscription

router = APIRouter(tags=["reports"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])

ReportsRead = Annotated[Principal, Depends(require_permission("reports.read"))]
ReportsFinance = Annotated[Principal, Depends(require_permission("reports.finance"))]
AuditRead = Annotated[Principal, Depends(require_permission("audit.read"))]
SubscriptionRead = Annotated[Principal, Depends(require_permission("subscription.read"))]
SubscriptionManage = Annotated[Principal, Depends(require_permission("subscription.manage"))]
Integrations = Annotated[Principal, Depends(require_permission("integrations.manage"))]
PlatformMetrics = Annotated[Principal, Depends(require_permission("platform.metrics"))]
From = Annotated[date, Query(alias="from")]
To = Annotated[date, Query()]


@router.get("/reports/revenue", response_model=RevenueReport)
async def revenue(
    request: Request, uow: Uow, principal: ReportsFinance, from_: From, to: To
) -> dict[str, Any]:
    return await reports.revenue(uow, principal.tenant(request), from_, to)


@router.get("/reports/payments", response_model=PaymentsReport)
async def payments(
    request: Request, uow: Uow, principal: ReportsFinance, from_: From, to: To
) -> dict[str, Any]:
    return await reports.payments(uow, principal.tenant(request), from_, to)


@router.get("/reports/orders", response_model=OrdersReport)
async def orders(request: Request, uow: Uow, principal: ReportsRead, from_: From, to: To) -> dict[str, Any]:
    return await reports.orders(uow, principal.tenant(request), from_, to)


@router.get("/reports/items", response_model=ItemsReport)
async def items(request: Request, uow: Uow, principal: ReportsRead, from_: From, to: To) -> dict[str, Any]:
    return await reports.items(uow, principal.tenant(request), from_, to)


@router.get("/reports/kitchen", response_model=KitchenReport)
async def kitchen(request: Request, uow: Uow, principal: ReportsRead, from_: From, to: To) -> dict[str, Any]:
    return await reports.kitchen(uow, principal.tenant(request), from_, to)


@router.get("/reports/room-service", response_model=RoomServiceReport)
async def room_service(
    request: Request, uow: Uow, principal: ReportsRead, from_: From, to: To
) -> dict[str, Any]:
    return await reports.room_service(uow, principal.tenant(request), from_, to)


@router.get("/reports/occupancy", response_model=OccupancyReport)
async def occupancy(
    request: Request, uow: Uow, principal: ReportsRead, from_: From, to: To
) -> dict[str, Any]:
    return await reports.occupancy(uow, principal.tenant(request), from_, to)


@router.get("/reports/open-balances", response_model=OpenBalances)
async def open_balances(request: Request, uow: Uow, principal: ReportsFinance) -> dict[str, Any]:
    return await reports.open_balances(uow, principal.tenant(request))


@router.get("/reports/daily-close", response_model=DailyCloseReport)
async def daily_close(
    request: Request,
    uow: Uow,
    principal: ReportsFinance,
    day: Annotated[date | None, Query(alias="date")] = None,
) -> dict[str, Any]:
    ctx = principal.tenant(request)
    if day is None:
        settings = await HotelRepository(uow.session, ctx).get_settings()
        day = business_date(settings.timezone if settings else "Africa/Johannesburg")
    return await reports.daily_close(uow, ctx, day)


@router.put("/reports/daily-close/{day}", response_model=DailyCloseReport)
async def put_daily_close(
    day: date, body: DailyClosePut, request: Request, uow: Uow, principal: ReportsFinance
) -> dict[str, Any]:
    return await reports.put_daily_close(uow, principal.tenant(request), day, body.model_dump())


@router.get("/audit-logs", response_model=AuditList)
async def audit_logs(
    request: Request,
    uow: Uow,
    principal: AuditRead,
    actor_id: Annotated[uuid.UUID | None, Query()] = None,
    action: Annotated[str | None, Query(max_length=80)] = None,
    entity_type: Annotated[str | None, Query(max_length=80)] = None,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
    limit: Limit = DEFAULT_LIMIT,
    cursor: Cursor = None,
) -> dict[str, Any]:
    rows = await reports.audit_logs(
        uow,
        principal.tenant(request),
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        date_from=from_,
        date_to=to,
        after=decode_cursor(cursor, 1),
        limit=limit,
    )
    data, next_cursor = page(rows, limit, lambda r: [r["id"]])
    return {"data": data, "next_cursor": next_cursor}


# --- Subscription ---------------------------------------------------------------------------


@router.get("/subscription", response_model=HotelSubscription)
async def get_subscription(request: Request, uow: Uow, principal: SubscriptionRead) -> dict[str, Any]:
    return await subscription.view(uow, principal.tenant(request))


@router.post("/subscription/change-request", status_code=202, response_model=ChangeRequestOut)
async def change_request(
    idem: IdemUser, body: ChangeRequest, request: Request, uow: Uow, principal: SubscriptionManage
) -> Response:
    result = await subscription.request_change(uow, principal.tenant(request), body.model_dump())
    return await idem.complete(uow, 202, ChangeRequestOut.model_validate(result).model_dump(mode="json"))


# --- API keys -------------------------------------------------------------------------------


@router.get("/api-keys", response_model=ApiKeyList)
async def list_keys(request: Request, uow: Uow, principal: Integrations) -> dict[str, Any]:
    return {"data": await integrations.list_keys(uow, principal.tenant(request)), "next_cursor": None}


@router.post("/api-keys", status_code=201, response_model=ApiKeyCreated)
async def create_key(
    idem: IdemUser, body: ApiKeyCreate, request: Request, uow: Uow, principal: Integrations, _s: StepUp
) -> Response:
    result = await integrations.create_key(
        uow, principal.tenant(request), body.model_dump(), principal.permissions
    )
    return await idem.complete(uow, 201, ApiKeyCreated.model_validate(result).model_dump(mode="json"))


@router.delete("/api-keys/{key_id}", status_code=204)
async def revoke_key(key_id: uuid.UUID, request: Request, uow: Uow, principal: Integrations) -> Response:
    await integrations.revoke_key(uow, principal.tenant(request), key_id)
    return Response(status_code=204)


# --- Webhooks -------------------------------------------------------------------------------


@router.get("/webhooks", response_model=WebhookList)
async def list_webhooks(request: Request, uow: Uow, principal: Integrations) -> dict[str, Any]:
    return {"data": await integrations.list_webhooks(uow, principal.tenant(request)), "next_cursor": None}


@router.post("/webhooks", status_code=201, response_model=WebhookCreated)
async def create_webhook(
    idem: IdemUser, body: WebhookCreate, request: Request, uow: Uow, principal: Integrations
) -> Response:
    result = await integrations.create_webhook(
        state_of(request), uow, principal.tenant(request), body.model_dump()
    )
    return await idem.complete(uow, 201, WebhookCreated.model_validate(result).model_dump(mode="json"))


@router.post("/webhooks/{webhook_id}/status", response_model=WebhookOut)
async def webhook_status(
    webhook_id: uuid.UUID, body: WebhookStatusChange, request: Request, uow: Uow, principal: Integrations
) -> dict[str, Any]:
    return await integrations.set_webhook_status(uow, principal.tenant(request), webhook_id, body.status)


@router.post("/webhooks/{webhook_id}/test", status_code=202, response_model=WebhookTestOut)
async def test_webhook(
    webhook_id: uuid.UUID, request: Request, uow: Uow, principal: Integrations
) -> dict[str, Any]:
    return await integrations.test_webhook(uow, principal.tenant(request), webhook_id)


@router.get("/webhooks/{webhook_id}/deliveries", response_model=DeliveryList)
async def webhook_deliveries(
    webhook_id: uuid.UUID, request: Request, uow: Uow, principal: Integrations
) -> dict[str, Any]:
    return {
        "data": await integrations.deliveries(uow, principal.tenant(request), webhook_id),
        "next_cursor": None,
    }


# --- Platform analytics ---------------------------------------------------------------------


@admin_router.get("/analytics", response_model=Analytics)
async def analytics(
    uow: Uow, principal: PlatformMetrics, days: Annotated[int, Query(ge=1, le=366)] = 30
) -> dict[str, Any]:
    return {"days": await admin.analytics(uow, days)}
