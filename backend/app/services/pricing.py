"""Server-side pricing for carts (guest tablet and staff orders). The client sends item ids,
quantities and modifier ids only; every amount is computed here from the current menu.

Unit price = item price + chosen modifier deltas. If menu prices exclude VAT, VAT is added
per unit so guests always see and pay VAT-inclusive amounts. VAT contained in each line and
in the fee is rounded half up per line (app.billing.vat).
"""

from __future__ import annotations

import uuid
import zoneinfo
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.billing.vat import gross_and_vat, vat_included
from app.core.errors import AppError
from app.db.session import TenantContext
from app.repositories.menu import MenuRepository
from app.services import schedules

MAX_LINES = 50
MAX_QUANTITY = 99


@dataclass
class PricedModifier:
    id: uuid.UUID
    group: str
    name: str
    price_delta_minor: int


@dataclass
class PricedLine:
    menu_item_id: uuid.UUID
    station_id: uuid.UUID
    name: str
    description: str | None
    charge_category: str
    quantity: int
    unit_price_minor: int  # VAT-inclusive, incl. modifier deltas
    vat_rate_bp: int
    vat_minor: int
    note: str | None
    modifiers: list[PricedModifier] = field(default_factory=list)

    @property
    def line_total_minor(self) -> int:
        return self.unit_price_minor * self.quantity


@dataclass
class PricedCart:
    lines: list[PricedLine]
    subtotal_minor: int
    fee_minor: int
    fee_vat_minor: int
    fee_vat_rate_bp: int
    vat_minor: int
    currency: str
    needs_approval: bool

    @property
    def total_minor(self) -> int:
        return self.subtotal_minor + self.fee_minor


def _unavailable(item_id: uuid.UUID, problem: str) -> AppError:
    return AppError("ITEM_UNAVAILABLE", problem, details={"menu_item_id": str(item_id)})


async def price_cart(
    session: Any, ctx: TenantContext, settings: Any, lines: list[dict[str, Any]]
) -> PricedCart:
    if len(lines) > MAX_LINES or any(ln["quantity"] > MAX_QUANTITY for ln in lines):
        raise AppError(
            "ORDER_TOO_LARGE",
            f"An order can have at most {MAX_LINES} lines and {MAX_QUANTITY} of one item.",
            details={"max_lines": MAX_LINES, "max_quantity": MAX_QUANTITY},
        )
    repo = MenuRepository(session, ctx)
    item_ids = list({ln["menu_item_id"] for ln in lines})
    items = {i.id: i for i in await repo.items(ids=item_ids)}
    categories = {c.id: c for c in await repo.categories()}
    windows = {s.id: s.windows for s in await repo.schedules()}
    stations = {s.id for s in await repo.stations(active_only=True)}
    item_groups = await repo.item_groups(item_ids)
    group_ids = list({g for gs in item_groups.values() for g in gs})
    groups = {g.id: g for g in await repo.groups(group_ids)}
    options = {o.id: o for opts in (await repo.options(group_ids)).values() for o in opts}
    local_now = datetime.now(zoneinfo.ZoneInfo(settings.timezone)).replace(tzinfo=None)
    registered = settings.vat_registered

    priced: list[PricedLine] = []
    for ln in lines:
        item = items.get(ln["menu_item_id"])
        if item is None:
            raise _unavailable(ln["menu_item_id"], "This item is no longer on the menu.")
        category = categories.get(item.category_id)
        schedule_id = item.schedule_id or (category.schedule_id if category else None)
        if (
            not item.is_available
            or category is None
            or item.station_id not in stations
            or not schedules.is_open(windows.get(schedule_id) if schedule_id else None, local_now)
        ):
            raise _unavailable(item.id, f"{item.name} is not available right now.")
        offered = item_groups.get(item.id, [])
        chosen: dict[uuid.UUID, list[PricedModifier]] = {g: [] for g in offered}
        for opt_id in dict.fromkeys(ln.get("modifier_option_ids") or []):
            opt = options.get(opt_id)
            if opt is None or opt.group_id not in chosen:
                raise AppError("VALIDATION_FAILED", f"That option is not offered for {item.name}.")
            if not opt.is_available:
                raise _unavailable(item.id, f"{opt.name} is not available right now.")
            chosen[opt.group_id].append(
                PricedModifier(opt.id, groups[opt.group_id].name, opt.name, opt.price_delta_minor)
            )
        for gid, picks in chosen.items():
            g = groups[gid]
            if not g.min_select <= len(picks) <= g.max_select:
                raise AppError(
                    "VALIDATION_FAILED",
                    f"Choose {g.min_select}-{g.max_select} for {g.name} on {item.name}.",
                    details={"menu_item_id": str(item.id), "group_id": str(gid)},
                )
        mods = [m for picks in chosen.values() for m in picks]
        rate = item.vat_rate_bp if item.vat_rate_bp is not None else settings.vat_rate_bp
        unit, _ = gross_and_vat(
            item.price_minor + sum(m.price_delta_minor for m in mods),
            rate,
            includes_vat=settings.menu_prices_include_vat,
            registered=registered,
        )
        priced.append(
            PricedLine(
                menu_item_id=item.id,
                station_id=item.station_id,
                name=item.name,
                description=item.description,
                charge_category=item.charge_category_code,
                quantity=ln["quantity"],
                unit_price_minor=unit,
                vat_rate_bp=rate if registered else 0,
                vat_minor=vat_included(unit * ln["quantity"], rate) if registered else 0,
                note=(ln.get("note") or None),
                modifiers=mods,
            )
        )
    fee, fee_vat = gross_and_vat(
        settings.room_service_fee_minor,
        settings.vat_rate_bp,
        includes_vat=settings.menu_prices_include_vat,
        registered=registered,
    )
    subtotal = sum(p.line_total_minor for p in priced)
    total = subtotal + fee
    return PricedCart(
        lines=priced,
        subtotal_minor=subtotal,
        fee_minor=fee,
        fee_vat_minor=fee_vat,
        fee_vat_rate_bp=settings.vat_rate_bp if registered else 0,
        vat_minor=sum(p.vat_minor for p in priced) + fee_vat,
        currency=settings.currency,
        needs_approval=total > settings.room_charge_auto_limit_minor,
    )


def money(amount: int, currency: str) -> dict[str, Any]:
    return {"amount_minor": amount, "currency": currency}


def quote_payload(cart: PricedCart) -> dict[str, Any]:
    c = cart.currency
    return {
        "lines": [
            {
                "menu_item_id": p.menu_item_id,
                "name": p.name,
                "quantity": p.quantity,
                "unit_price": money(p.unit_price_minor, c),
                "line_total": money(p.line_total_minor, c),
                "modifiers": [
                    {
                        "id": m.id,
                        "group": m.group,
                        "name": m.name,
                        "price_delta": money(m.price_delta_minor, c),
                    }
                    for m in p.modifiers
                ],
                "note": p.note,
            }
            for p in cart.lines
        ],
        "subtotal": money(cart.subtotal_minor, c),
        "fee": money(cart.fee_minor, c),
        "total": money(cart.total_minor, c),
        "vat_included": money(cart.vat_minor, c),
        "needs_approval": cart.needs_approval,
    }
