"""What a hotel pays for a plan, computed on the server only (DECISIONS D76).

Inputs are the plan and its price row as they are now, Diyneco's tax position on the day and
whether this is the hotel's first paid subscription (a setup fee is charged once). An
introductory price replaces the price for its periods; a live promotional discount applies to
the first period only and `renews_at_minor` is what later periods cost. Every
amount is integer minor units; discounts and tax round half up per line, like the hotels'
own bills (app.billing.vat). The browser only ever shows the result.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.billing.periods import period_end
from app.billing.vat import div_half_up, gross_and_vat

INTERVAL_NAMES = {"month": "monthly", "quarter": "quarterly", "year": "annual"}


@dataclass(frozen=True)
class Line:
    code: str
    description: str
    amount_minor: int  # before discount, in the plan's tax treatment
    discount_minor: int = 0

    @property
    def net_of_discount(self) -> int:
        return self.amount_minor - self.discount_minor


def quote(
    *,
    plan_name: str,
    interval: str,
    amount_minor: int,
    intro_amount_minor: int | None,
    currency: str,
    tax_treatment: str,
    setup_fee_minor: int,
    promo_discount_bp: int,
    first_subscription: bool,
    tax: dict[str, Any],
    start: date,
    group_discount_bp: int = 0,
) -> dict[str, Any]:
    price = intro_amount_minor if intro_amount_minor is not None else amount_minor
    # A live promotion and the group discount (D89) add up, each on the price, never past it.
    discount = div_half_up(price * promo_discount_bp, 10000) if promo_discount_bp else 0
    discount += div_half_up(price * group_discount_bp, 10000) if group_discount_bp else 0
    discount = min(discount, price)
    lines = [Line("subscription", f"{plan_name}, {INTERVAL_NAMES[interval]}", price, discount)]
    if first_subscription and setup_fee_minor:
        lines.append(Line("setup_fee", "One-time setup fee", setup_fee_minor))
    rate = tax["rate_bp"] if tax["charged"] else 0
    out_lines = []
    total = tax_total = 0
    for line in lines:
        gross, vat = gross_and_vat(
            line.net_of_discount, rate, includes_vat=tax_treatment == "inclusive", registered=tax["charged"]
        )
        total += gross
        tax_total += vat
        out_lines.append(
            {
                "code": line.code,
                "description": line.description,
                "amount_minor": line.amount_minor,
                "discount_minor": line.discount_minor,
                "tax_minor": vat,
                "total_minor": gross,
            }
        )
    return {
        "currency": currency,
        "lines": out_lines,
        "subtotal_minor": total - tax_total,
        "tax_minor": tax_total,
        "total_minor": total,
        "tax_charged": tax["charged"],
        "tax_name": tax["tax_name"],
        "tax_rate_bp": tax["rate_bp"],
        "prices_include_tax": tax_treatment == "inclusive",
        "period_start": start,
        "period_end": period_end(start, interval, start.day),
        "renews_at_minor": amount_minor,
        "group_discount_bp": group_discount_bp,
    }
