"""VAT arithmetic on integer minor units (security spec, VAT). Rates are basis points
(1500 = 15%). Rounding is half up, per line, which is how the API spec's example works out:
R290 + R20 + R50 fee, VAT-inclusive at 15% -> 3783 + 261 + 652 = 4696 cents."""

from __future__ import annotations


def _div_half_up(numerator: int, denominator: int) -> int:
    if numerator < 0:
        return -_div_half_up(-numerator, denominator)
    return (2 * numerator + denominator) // (2 * denominator)


def vat_included(gross_minor: int, rate_bp: int) -> int:
    """VAT contained in a VAT-inclusive amount."""
    if rate_bp <= 0:
        return 0
    return _div_half_up(gross_minor * rate_bp, 10000 + rate_bp)


def vat_on_top(net_minor: int, rate_bp: int) -> int:
    """VAT to add to a VAT-exclusive amount."""
    if rate_bp <= 0:
        return 0
    return _div_half_up(net_minor * rate_bp, 10000)


def gross_and_vat(
    amount_minor: int, rate_bp: int, *, includes_vat: bool, registered: bool
) -> tuple[int, int]:
    """(gross amount the guest pays, VAT contained in it) for one unit."""
    if not registered:
        return amount_minor, 0
    if includes_vat:
        return amount_minor, vat_included(amount_minor, rate_bp)
    vat = vat_on_top(amount_minor, rate_bp)
    return amount_minor + vat, vat
