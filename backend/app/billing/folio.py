"""Folio ledger writes. `folio_entries` is append-only: charges are positive, payments,
discounts and reversals negative, tips positive but outside the balance. A reversal points
at the entry it cancels and carries the negated amounts."""

from __future__ import annotations

import uuid
import zoneinfo
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import TenantContext
from app.models.domain import ChargeCategory, Folio, FolioEntry


def business_date(timezone: str, now: datetime | None = None) -> date:
    """The hotel-local calendar date."""
    return (now or datetime.now(UTC)).astimezone(zoneinfo.ZoneInfo(timezone)).date()


@dataclass(frozen=True)
class Line:
    category: str
    description: str
    unit_amount_minor: int
    quantity: int
    vat_rate_bp: int
    vat_minor: int  # VAT contained in the whole line
    business_date: date
    order_id: uuid.UUID | None = None
    payment_id: uuid.UUID | None = None
    adjustment_id: uuid.UUID | None = None


class FolioLedger:
    def __init__(self, session: AsyncSession, ctx: TenantContext) -> None:
        self.s = session
        self.ctx = ctx
        self._categories: dict[str, uuid.UUID] = {}

    async def category_id(self, code: str) -> uuid.UUID:
        if code not in self._categories:
            self._categories[code] = (
                await self.s.execute(
                    select(ChargeCategory.id).where(
                        ChargeCategory.hotel_id.is_(None), ChargeCategory.code == code
                    )
                )
            ).scalar_one()
        return self._categories[code]

    async def open_folio(self, stay_id: uuid.UUID, currency: str) -> Folio:
        return (
            await self.s.execute(
                insert(Folio)
                .values(hotel_id=self.ctx.hotel_id, stay_id=stay_id, currency=currency)
                .returning(Folio)
            )
        ).scalar_one()

    async def folio_for_stay(self, stay_id: uuid.UUID) -> Folio | None:
        return (
            await self.s.execute(
                select(Folio).where(Folio.hotel_id == self.ctx.hotel_id, Folio.stay_id == stay_id)
            )
        ).scalar_one_or_none()

    async def post(self, folio: Folio, lines: list[Line], entry_type: str = "charge") -> list[FolioEntry]:
        if not lines:
            return []
        rows: list[dict[str, Any]] = []
        for ln in lines:
            rows.append(
                {
                    "hotel_id": self.ctx.hotel_id,
                    "folio_id": folio.id,
                    "entry_type": entry_type,
                    "category_id": await self.category_id(ln.category),
                    "description": ln.description,
                    "quantity": ln.quantity,
                    "unit_amount_minor": ln.unit_amount_minor,
                    "amount_minor": ln.unit_amount_minor * ln.quantity,
                    "vat_rate_bp": ln.vat_rate_bp,
                    "vat_minor": ln.vat_minor,
                    "currency": folio.currency,
                    "business_date": ln.business_date,
                    "order_id": ln.order_id,
                    "payment_id": ln.payment_id,
                    "adjustment_id": ln.adjustment_id,
                    "created_by": self.ctx.actor_id if self.ctx.actor_type == "user" else None,
                    "created_by_device": self.ctx.device_id,
                }
            )
        return list((await self.s.execute(insert(FolioEntry).returning(FolioEntry), rows)).scalars())

    def _not_reversed(self) -> Any:
        return ~FolioEntry.id.in_(
            select(FolioEntry.reverses_entry_id).where(
                FolioEntry.hotel_id == self.ctx.hotel_id,
                FolioEntry.reverses_entry_id.is_not(None),
            )
        )

    async def reverse_order(self, folio: Folio, order_id: uuid.UUID, description: str, on: date) -> int:
        """Reverses every charge of one order that is not reversed yet. Returns the count."""
        entries = (
            await self.s.execute(
                select(FolioEntry).where(
                    FolioEntry.hotel_id == self.ctx.hotel_id,
                    FolioEntry.folio_id == folio.id,
                    FolioEntry.order_id == order_id,
                    FolioEntry.entry_type == "charge",
                    self._not_reversed(),
                )
            )
        ).scalars()
        return await self.reverse(folio, list(entries), description, on)

    async def live_charges(self, folio: Folio, category: str) -> list[FolioEntry]:
        """Charges of one category on the folio that are not reversed."""
        return list(
            (
                await self.s.execute(
                    select(FolioEntry)
                    .where(
                        FolioEntry.hotel_id == self.ctx.hotel_id,
                        FolioEntry.folio_id == folio.id,
                        FolioEntry.entry_type == "charge",
                        FolioEntry.category_id == await self.category_id(category),
                        self._not_reversed(),
                    )
                    .order_by(FolioEntry.business_date, FolioEntry.id)
                )
            ).scalars()
        )

    async def reverse(self, folio: Folio, entries: list[FolioEntry], description: str, on: date) -> int:
        """Posts a reversal for each entry, carrying its negated amounts. Returns the count."""
        rows = [
            {
                "hotel_id": self.ctx.hotel_id,
                "folio_id": folio.id,
                "entry_type": "reversal",
                "category_id": e.category_id,
                "description": f"{description}: {e.description}",
                "quantity": e.quantity,
                "unit_amount_minor": -e.unit_amount_minor,
                "amount_minor": -e.amount_minor,
                "vat_rate_bp": e.vat_rate_bp,
                "vat_minor": -e.vat_minor,
                "currency": e.currency,
                "business_date": on,
                "order_id": e.order_id,
                "reverses_entry_id": e.id,
                "created_by": self.ctx.actor_id if self.ctx.actor_type == "user" else None,
                "created_by_device": self.ctx.device_id,
            }
            for e in entries
        ]
        if rows:
            await self.s.execute(insert(FolioEntry), rows)
        return len(rows)

    async def balance(self, folio_id: uuid.UUID) -> dict[str, int]:
        row = (
            (
                await self.s.execute(
                    text(
                        "SELECT coalesce(accommodation_minor, 0) AS accommodation, "
                        "coalesce(fnb_minor, 0) AS fnb, "
                        "coalesce(other_minor, 0) AS other, coalesce(tips_minor, 0) AS tips, "
                        "coalesce(paid_minor, 0) AS paid, balance_minor AS balance "
                        "FROM app.folio_balances WHERE folio_id = :f"
                    ),
                    {"f": folio_id},
                )
            )
            .mappings()
            .one()
        )
        return {k: int(v) for k, v in row.items()}
