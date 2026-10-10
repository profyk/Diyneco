"""Supported currencies (DECISIONS D57). Money is stored in minor units, so only currencies with
two decimal places are offered; a hotel picks its operating currency and the platform picks
each plan's billing currency from this list. Nothing else in the code assumes a currency.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Currency:
    code: str
    name: str
    symbol: str


CURRENCIES: dict[str, Currency] = {
    c.code: c
    for c in (
        Currency("ZAR", "South African rand", "R"),
        Currency("BWP", "Botswana pula", "P"),
        Currency("NAD", "Namibian dollar", "N$"),
        Currency("LSL", "Lesotho loti", "L"),
        Currency("SZL", "Eswatini lilangeni", "E"),
        Currency("MZN", "Mozambican metical", "MT"),
        Currency("ZMW", "Zambian kwacha", "K"),
        Currency("MWK", "Malawian kwacha", "MK"),
        Currency("KES", "Kenyan shilling", "KSh"),
        Currency("TZS", "Tanzanian shilling", "TSh"),
        Currency("NGN", "Nigerian naira", "₦"),
        Currency("GHS", "Ghanaian cedi", "GH₵"),
        Currency("EGP", "Egyptian pound", "E£"),
        Currency("MAD", "Moroccan dirham", "MAD"),
        Currency("MUR", "Mauritian rupee", "Rs"),
        Currency("SCR", "Seychellois rupee", "SR"),
        Currency("USD", "US dollar", "$"),
        Currency("EUR", "Euro", "€"),
        Currency("GBP", "Pound sterling", "£"),
        Currency("CHF", "Swiss franc", "CHF"),
        Currency("AUD", "Australian dollar", "A$"),
        Currency("NZD", "New Zealand dollar", "NZ$"),
        Currency("CAD", "Canadian dollar", "C$"),
        Currency("AED", "UAE dirham", "AED"),
        Currency("INR", "Indian rupee", "₹"),
        Currency("SGD", "Singapore dollar", "S$"),
        Currency("HKD", "Hong Kong dollar", "HK$"),
        Currency("CNY", "Chinese yuan", "¥"),
        Currency("BRL", "Brazilian real", "R$"),
        Currency("MXN", "Mexican peso", "MX$"),
    )
}


def is_supported(code: str) -> bool:
    return code in CURRENCIES


def symbol(code: str) -> str:
    c = CURRENCIES.get(code)
    return c.symbol if c else code


def format_minor(minor: int, code: str) -> str:
    """Plain-text amount for documents and emails, e.g. "R 1,234.50" or "€ 12.00"."""
    sign = "-" if minor < 0 else ""
    whole, cents = divmod(abs(int(minor)), 100)
    return f"{sign}{symbol(code)} {whole:,}.{cents:02d}"
