"""Owners with several properties (DECISIONS D86).

- One login, many hotels: each hotel stays its own tenant (RLS); the owner switches between
  them (POST /auth/refresh with hotel_id) and sees them side by side in the portfolio.
- Adding a property: a Hotel Owner of at least one hotel adds another with the signup form's
  hotel details (step-up). The new hotel starts with no subscription: the free trial is once
  per owner, at signup. The platform can grant a trial (POST /admin/hotels/{id}/trial).
- The portfolio is built hotel by hotel, each read under that hotel's own context, and only for
  hotels where the caller is the Hotel Owner. Money is never added across currencies.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select, text

from app.core.errors import AppError
from app.core.state import AppState
from app.db.session import TenantContext, UnitOfWork, set_tenant
from app.models.tenancy import Hotel, HotelSettings, Plan, Subscription, User
from app.repositories.hotels import CURRENT_STATUSES
from app.repositories.roles import RoleRepository
from app.repositories.staff import StaffRepository
from app.services import reports, staff
from app.services.auth import ClientInfo, Membership, memberships
from app.services.pricing import money
from app.services.signup import create_hotel, prepare_hotel

OWNER = "hotel_owner"

COUNTS_SQL = """
SELECT
  (SELECT count(*) FROM app.stays WHERE hotel_id = :h AND NOT is_training
     AND status IN ('active', 'checkout_pending')) AS in_house,
  (SELECT count(*) FROM app.stays WHERE hotel_id = :h AND NOT is_training
     AND status = 'reserved' AND arrival_date = :d) AS arrivals,
  (SELECT count(*) FROM app.orders WHERE hotel_id = :h
     AND status IN ('PENDING_APPROVAL', 'NEW', 'ACCEPTED', 'PREPARING', 'READY', 'ASSIGNED', 'PICKED_UP'))
     AS open_orders,
  (SELECT count(*) FROM app.hotel_users WHERE hotel_id = :h AND status = 'active') AS staff
"""


async def owned(uow: UnitOfWork, user_id: uuid.UUID) -> list[Membership]:
    return [m for m in await memberships(uow.session, user_id) if OWNER in m.role_codes]


# Roles that see the portfolio of the hotels where they hold them (D90): owners, and the
# managers an owner put over several properties.
PORTFOLIO_ROLES = {OWNER, "hotel_admin", "general_manager"}


async def managed(uow: UnitOfWork, user_id: uuid.UUID) -> list[Membership]:
    return [m for m in await memberships(uow.session, user_id) if PORTFOLIO_ROLES & set(m.role_codes)]


async def invite_to_properties(
    st: AppState,
    uow: UnitOfWork,
    *,
    user_id: uuid.UUID,
    current: TenantContext,
    name: str,
    email: str,
    department: str | None,
    assignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """One person invited to several of the caller's properties at once, with a role at each
    (D90). Each invitation is the hotel's own, made under its context by the ordinary staff
    invitation (permission check, staff limit, audit, email), so each hotel stays separate."""
    mine = {m.hotel_id: m for m in await owned(uow, user_id)}
    if not mine:
        raise AppError("PERMISSION_DENIED", "Only a hotel owner can invite to several properties.")
    if any(a["hotel_id"] not in mine for a in assignments):
        raise AppError("NOT_FOUND", "One of the properties is not yours.")
    out = []
    try:
        for a in assignments:
            m = mine[a["hotel_id"]]
            await set_tenant(uow.session, m.hotel_id, user_id)
            ctx = TenantContext(
                hotel_id=m.hotel_id,
                actor_type="user",
                actor_id=user_id,
                actor_label=current.actor_label,
                ip=current.ip,
                request_id=current.request_id,
            )
            roles = RoleRepository(uow.session, ctx)
            role_ids = [await roles.system_role_id(code) for code in a["role_codes"]]
            perms = frozenset(await StaffRepository(uow.session, ctx).member_permissions(m.hotel_user_id))
            inv = await staff.invite(
                st,
                uow,
                ctx,
                {"name": name, "email": email, "department": department, "role_ids": role_ids},
                perms,
            )
            out.append({"hotel_id": m.hotel_id, "hotel_name": m.hotel_name, **inv})
    finally:
        await set_tenant(uow.session, current.hotel_id, user_id)
    return out


async def add_property(
    st: AppState,
    uow: UnitOfWork,
    *,
    user_id: uuid.UUID,
    hotel: dict[str, Any],
    client: ClientInfo,
    accepted_documents: list[uuid.UUID] | None,
) -> dict[str, Any]:
    if not await owned(uow, user_id):
        raise AppError("PERMISSION_DENIED", "Only a hotel owner can add a property.")
    user = (await uow.session.execute(select(User).where(User.id == user_id))).scalar_one()
    prepared = await prepare_hotel(uow, hotel, accepted_documents)
    created = await create_hotel(
        st,
        uow,
        prepared,
        user_id=user_id,
        owner_label=f"{user.name} (Hotel Owner)",
        client=client,
        trial=False,  # one free trial per owner, at signup (D86)
        action="hotel.added_by_owner",
    )
    return {
        "hotel_id": created.id,
        "name": created.name,
        "code": created.code,
        "status": created.status,
        "subscription_status": None,
    }


async def _hotel_summary(uow: UnitOfWork, ctx: TenantContext) -> dict[str, Any]:
    s = uow.session
    hotel = (await s.execute(select(Hotel).where(Hotel.id == ctx.hotel_id))).scalar_one()
    settings = (
        await s.execute(select(HotelSettings).where(HotelSettings.hotel_id == ctx.hotel_id))
    ).scalar_one()
    today = datetime.now(UTC).astimezone(ZoneInfo(settings.timezone)).date()
    month_start = date(today.year, today.month, 1)
    rev_today = (await reports.revenue(uow, ctx, today, today))["total"]
    rev_month = (await reports.revenue(uow, ctx, month_start, today))["total"]
    occ = (await reports.occupancy(uow, ctx, today, today))["total"]
    counts = (await s.execute(text(COUNTS_SQL), {"h": ctx.hotel_id, "d": today})).mappings().one()
    sub = (
        await s.execute(
            select(Subscription.status, Plan.name, Subscription.trial_ends_on)
            .join(Plan, Plan.id == Subscription.plan_id, isouter=True)
            .where(Subscription.hotel_id == ctx.hotel_id, Subscription.status.in_(CURRENT_STATUSES))
        )
    ).first()
    return {
        "hotel_id": hotel.id,
        "name": hotel.name,
        "code": hotel.code,
        "status": hotel.status,
        "property_type": hotel.property_type,
        "country": hotel.country,
        "city": hotel.address.get("city"),
        "province": hotel.address.get("province"),
        "currency": settings.currency,
        "business_date": today,
        "subscription_status": sub[0] if sub else None,
        "plan_name": sub[1] if sub else None,
        "trial_ends_on": sub[2] if sub else None,
        "rooms": occ["rooms"],
        "occupied": occ["occupied"],
        "occupancy_bp": occ["occupancy_bp"],
        "in_house": int(counts["in_house"]),
        "arrivals_today": int(counts["arrivals"]),
        "open_orders": int(counts["open_orders"]),
        "staff": int(counts["staff"]),
        "revenue_today": rev_today["revenue"],
        "revenue_month": rev_month["revenue"],
        "payments_month": rev_month["payments"],
    }


async def portfolio(uow: UnitOfWork, user_id: uuid.UUID, current: TenantContext) -> dict[str, Any]:
    """Every hotel the caller owns or manages, side by side, with totals per currency."""
    hotels = await managed(uow, user_id)
    if not hotels:
        raise AppError("PERMISSION_DENIED", "Only owners and general managers see the portfolio.")
    out = []
    try:
        for m in sorted(hotels, key=lambda m: m.hotel_name.lower()):
            await set_tenant(uow.session, m.hotel_id, user_id)
            ctx = TenantContext(
                hotel_id=m.hotel_id,
                actor_type="user",
                actor_id=user_id,
                actor_label=current.actor_label,
                ip=current.ip,
                request_id=current.request_id,
            )
            out.append(await _hotel_summary(uow, ctx))
    finally:
        await set_tenant(uow.session, current.hotel_id, user_id)
    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"today": 0, "month": 0, "payments": 0})
    for h in out:
        t = totals[h["currency"]]
        t["today"] += h["revenue_today"]["amount_minor"]
        t["month"] += h["revenue_month"]["amount_minor"]
        t["payments"] += h["payments_month"]["amount_minor"]
    rooms = sum(h["rooms"] for h in out)
    occupied = sum(h["occupied"] for h in out)
    return {
        "data": out,
        "totals": {
            "properties": len(out),
            "rooms": rooms,
            "occupied": occupied,
            "occupancy_bp": occupied * 10000 // rooms if rooms else 0,
            "in_house": sum(h["in_house"] for h in out),
            "open_orders": sum(h["open_orders"] for h in out),
            "revenue": [
                {
                    "currency": c,
                    "today": money(t["today"], c),
                    "month": money(t["month"], c),
                    "payments_month": money(t["payments"], c),
                }
                for c, t in sorted(totals.items())
            ],
        },
    }
