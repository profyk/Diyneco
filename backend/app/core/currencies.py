"""Supported currencies (DECISIONS D57, D69). Money is stored as an integer count of the
currency's minor unit: cents for most, whole units for currencies without one (yen, Chilean
peso, Ugandan shilling...) and thousandths for the three-decimal dinars (Bahrain, Oman, Jordan).
`decimals` says which. A hotel picks its operating currency and the platform picks each plan's
billing currency from this list. Nothing else in the code assumes a currency.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Currency:
    code: str
    name: str
    symbol: str
    decimals: int = 2  # ISO 4217 minor unit


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
        Currency("ARS", "Argentine peso", "ARS"),
        Currency("COP", "Colombian peso", "COP"),
        Currency("PEN", "Peruvian sol", "S/"),
        Currency("CRC", "Costa Rican colón", "₡"),
        Currency("JMD", "Jamaican dollar", "J$"),
        Currency("CLP", "Chilean peso", "CLP", 0),
        Currency("SEK", "Swedish krona", "kr"),
        Currency("NOK", "Norwegian krone", "kr"),
        Currency("DKK", "Danish krone", "kr"),
        Currency("ISK", "Icelandic króna", "kr", 0),
        Currency("PLN", "Polish złoty", "zł"),
        Currency("CZK", "Czech koruna", "Kč"),
        Currency("TRY", "Turkish lira", "₺"),
        Currency("SAR", "Saudi riyal", "SAR"),
        Currency("QAR", "Qatari riyal", "QAR"),
        Currency("BHD", "Bahraini dinar", "BHD", 3),
        Currency("OMR", "Omani rial", "OMR", 3),
        Currency("JOD", "Jordanian dinar", "JOD", 3),
        Currency("THB", "Thai baht", "฿"),
        Currency("MYR", "Malaysian ringgit", "RM"),
        Currency("IDR", "Indonesian rupiah", "Rp", 0),  # priced in whole rupiah in practice
        Currency("PHP", "Philippine peso", "₱"),
        Currency("VND", "Vietnamese đồng", "₫", 0),
        Currency("LKR", "Sri Lankan rupee", "Rs"),
        Currency("JPY", "Japanese yen", "¥", 0),
        Currency("UGX", "Ugandan shilling", "USh", 0),
        Currency("RWF", "Rwandan franc", "FRw", 0),
    )
}


def is_supported(code: str) -> bool:
    return code in CURRENCIES


def symbol(code: str) -> str:
    c = CURRENCIES.get(code)
    return c.symbol if c else code


def decimals(code: str) -> int:
    c = CURRENCIES.get(code)
    return c.decimals if c else 2


def to_minor(value: Decimal | str, code: str) -> int:
    """An amount in major units ("1250.5") as minor units of `code`, exactly. Raises ValueError
    when it has more decimals than the currency allows."""
    d = Decimal(str(value))
    places = decimals(code)
    if d != d.quantize(Decimal(1).scaleb(-places)):
        raise ValueError(f"{code} amounts have at most {places} decimals")
    return int(d.scaleb(places))


def format_minor(minor: int, code: str) -> str:
    """Plain-text amount for documents and emails, e.g. "R 1,234.50", "¥ 1,500", "BHD 2.125"."""
    sign = "-" if minor < 0 else ""
    places = decimals(code)
    whole, frac = divmod(abs(int(minor)), 10**places)
    tail = f".{frac:0{places}d}" if places else ""
    return f"{sign}{symbol(code)} {whole:,}{tail}"
