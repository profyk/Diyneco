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
        # The rest of the world (D84): every currency of a country in app/core/world.py.
        Currency("AFN", "Afghan afghani", "Af"),
        Currency("ALL", "Albanian lek", "L"),
        Currency("AMD", "Armenian dram", "֏"),
        Currency("AOA", "Angolan kwanza", "Kz"),
        Currency("AWG", "Aruban florin", "Afl"),
        Currency("AZN", "Azerbaijani manat", "₼"),
        Currency("BAM", "Bosnia-Herzegovina convertible mark", "KM"),
        Currency("BBD", "Barbadian dollar", "Bds$"),
        Currency("BDT", "Bangladeshi taka", "৳"),
        Currency("BIF", "Burundian franc", "FBu", 0),
        Currency("BMD", "Bermudian dollar", "BD$"),
        Currency("BND", "Brunei dollar", "B$"),
        Currency("BOB", "Bolivian boliviano", "Bs"),
        Currency("BSD", "Bahamian dollar", "B$"),
        Currency("BTN", "Bhutanese ngultrum", "Nu"),
        Currency("BYN", "Belarusian ruble", "Br"),
        Currency("BZD", "Belize dollar", "BZ$"),
        Currency("CDF", "Congolese franc", "FC"),
        Currency("CUP", "Cuban peso", "CUP"),
        Currency("CVE", "Cape Verdean escudo", "Esc"),
        Currency("DJF", "Djiboutian franc", "Fdj", 0),
        Currency("DOP", "Dominican peso", "RD$"),
        Currency("DZD", "Algerian dinar", "DA"),
        Currency("ERN", "Eritrean nakfa", "Nfk"),
        Currency("ETB", "Ethiopian birr", "Br"),
        Currency("FJD", "Fijian dollar", "FJ$"),
        Currency("FKP", "Falkland Islands pound", "FK£"),
        Currency("GEL", "Georgian lari", "₾"),
        Currency("GIP", "Gibraltar pound", "£"),
        Currency("GMD", "Gambian dalasi", "D"),
        Currency("GNF", "Guinean franc", "FG", 0),
        Currency("GTQ", "Guatemalan quetzal", "Q"),
        Currency("GYD", "Guyanese dollar", "G$"),
        Currency("HNL", "Honduran lempira", "L"),
        Currency("HTG", "Haitian gourde", "G"),
        Currency("HUF", "Hungarian forint", "Ft"),
        Currency("ILS", "Israeli new shekel", "₪"),
        Currency("IQD", "Iraqi dinar", "IQD", 3),
        Currency("IRR", "Iranian rial", "IRR"),
        Currency("KGS", "Kyrgyzstani som", "som"),
        Currency("KHR", "Cambodian riel", "៛"),
        Currency("KMF", "Comorian franc", "CF", 0),
        Currency("KPW", "North Korean won", "₩"),
        Currency("KRW", "South Korean won", "₩", 0),
        Currency("KWD", "Kuwaiti dinar", "KWD", 3),
        Currency("KYD", "Cayman Islands dollar", "CI$"),
        Currency("KZT", "Kazakhstani tenge", "₸"),
        Currency("LAK", "Lao kip", "₭"),
        Currency("LBP", "Lebanese pound", "LBP"),
        Currency("LRD", "Liberian dollar", "L$"),
        Currency("LYD", "Libyan dinar", "LD", 3),
        Currency("MDL", "Moldovan leu", "L"),
        Currency("MGA", "Malagasy ariary", "Ar"),
        Currency("MKD", "Macedonian denar", "den"),
        Currency("MMK", "Myanmar kyat", "K"),
        Currency("MNT", "Mongolian tögrög", "₮"),
        Currency("MOP", "Macanese pataca", "MOP$"),
        Currency("MRU", "Mauritanian ouguiya", "UM"),
        Currency("NIO", "Nicaraguan córdoba", "C$"),
        Currency("NPR", "Nepalese rupee", "Rs"),
        Currency("PGK", "Papua New Guinean kina", "K"),
        Currency("PKR", "Pakistani rupee", "Rs"),
        Currency("PYG", "Paraguayan guaraní", "₲", 0),
        Currency("RON", "Romanian leu", "lei"),
        Currency("RSD", "Serbian dinar", "din"),
        Currency("RUB", "Russian ruble", "₽"),
        Currency("SBD", "Solomon Islands dollar", "SI$"),
        Currency("SDG", "Sudanese pound", "SDG"),
        Currency("SHP", "Saint Helena pound", "£"),
        Currency("SLE", "Sierra Leonean leone", "Le"),
        Currency("SOS", "Somali shilling", "Sh"),
        Currency("SRD", "Surinamese dollar", "Sr$"),
        Currency("SSP", "South Sudanese pound", "SSP"),
        Currency("STN", "São Tomé and Príncipe dobra", "Db"),
        Currency("SYP", "Syrian pound", "SYP"),
        Currency("TJS", "Tajikistani somoni", "SM"),
        Currency("TMT", "Turkmenistani manat", "m"),
        Currency("TND", "Tunisian dinar", "DT", 3),
        Currency("TOP", "Tongan pa'anga", "T$"),
        Currency("TTD", "Trinidad and Tobago dollar", "TT$"),
        Currency("TWD", "New Taiwan dollar", "NT$"),
        Currency("UAH", "Ukrainian hryvnia", "₴"),
        Currency("UYU", "Uruguayan peso", "$U"),
        Currency("UZS", "Uzbekistani so'm", "so'm"),
        Currency("VES", "Venezuelan bolívar", "Bs.S"),
        Currency("VUV", "Vanuatu vatu", "VT", 0),
        Currency("WST", "Samoan tālā", "WS$"),
        Currency("XAF", "Central African CFA franc", "FCFA", 0),
        Currency("XCD", "East Caribbean dollar", "EC$"),
        Currency("XCG", "Caribbean guilder", "Cg"),
        Currency("XOF", "West African CFA franc", "CFA", 0),
        Currency("XPF", "CFP franc", "CFPF", 0),
        Currency("YER", "Yemeni rial", "YER"),
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
