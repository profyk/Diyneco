"""Every country a hotel can be in, with the defaults a hotel starts from (DECISIONS D69, D84).

The detailed entries below suggest the currency, time zone, language, tax name and rate, and how a tax
registration number looks. Hotels confirm or change everything at signup and in settings: tax
rates change and some countries tax by region (the rate is then left empty). `region` is the
regional data cell that stores the hotel's data (docs/ARCHITECTURE-GLOBAL.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from app.core.regions import REGIONS as SUBDIVISIONS
from app.core.world import WORLD

REGIONS = ("af-south", "eu-west", "me-central", "ap-southeast", "us-east")

# Used where a country's registration format is not listed: letters, digits, spaces, dots,
# slashes and hyphens, 4 to 24 characters.
GENERIC_TAX_ID = r"^[A-Za-z0-9][A-Za-z0-9 ./-]{2,22}[A-Za-z0-9]$"
EU_VAT = r"^{cc}?[0-9A-Z+*]{{2,12}}$"


@dataclass(frozen=True)
class Country:
    code: str
    name: str
    currency: str
    timezone: str
    locale: str
    dial: str
    region: str
    tax_label: str = "VAT"
    tax_id_label: str = "VAT number"
    tax_id_pattern: str | None = None
    tax_rate_bp: int | None = None
    abridged_invoice_max_minor: int = 0  # simplified invoices below this amount (0: never)
    timezones: tuple[str, ...] = ()  # every zone in the country, `timezone` first (D84)

    def tax_id_ok(self, value: str) -> bool:
        return bool(re.fullmatch(self.tax_id_pattern or GENERIC_TAX_ID, value.strip().upper()))


def _eu(code: str, name: str, currency: str, tz: str, locale: str, dial: str, rate: int) -> Country:
    return Country(
        code, name, currency, tz, locale, dial, "eu-west", "VAT", "VAT number", EU_VAT.format(cc=code), rate
    )


_COUNTRIES = (
    # Africa
    Country(
        "ZA",
        "South Africa",
        "ZAR",
        "Africa/Johannesburg",
        "en-ZA",
        "+27",
        "af-south",
        "VAT",
        "VAT number",
        r"^4\d{9}$",
        1500,
        500000,
    ),
    Country("NA", "Namibia", "NAD", "Africa/Windhoek", "en-NA", "+264", "af-south", tax_rate_bp=1500),
    Country("BW", "Botswana", "BWP", "Africa/Gaborone", "en-BW", "+267", "af-south", tax_rate_bp=1400),
    Country("ZW", "Zimbabwe", "USD", "Africa/Harare", "en-ZW", "+263", "af-south", tax_rate_bp=1500),
    Country("ZM", "Zambia", "ZMW", "Africa/Lusaka", "en-ZM", "+260", "af-south", tax_rate_bp=1600),
    Country("MZ", "Mozambique", "MZN", "Africa/Maputo", "pt-MZ", "+258", "af-south", "IVA", "NUIT"),
    Country("MU", "Mauritius", "MUR", "Indian/Mauritius", "en-MU", "+230", "af-south", tax_rate_bp=1500),
    Country(
        "KE",
        "Kenya",
        "KES",
        "Africa/Nairobi",
        "en-KE",
        "+254",
        "af-south",
        "VAT",
        "KRA PIN",
        r"^[AP]\d{9}[A-Z]$",
        1600,
    ),
    Country("TZ", "Tanzania", "TZS", "Africa/Dar_es_Salaam", "en-TZ", "+255", "af-south", tax_rate_bp=1800),
    Country(
        "UG", "Uganda", "UGX", "Africa/Kampala", "en-UG", "+256", "af-south", "VAT", "TIN", tax_rate_bp=1800
    ),
    Country(
        "RW", "Rwanda", "RWF", "Africa/Kigali", "en-RW", "+250", "af-south", "VAT", "TIN", tax_rate_bp=1800
    ),
    Country(
        "NG", "Nigeria", "NGN", "Africa/Lagos", "en-NG", "+234", "af-south", "VAT", "TIN", tax_rate_bp=750
    ),
    Country("GH", "Ghana", "GHS", "Africa/Accra", "en-GH", "+233", "af-south", "VAT", "TIN"),
    Country("EG", "Egypt", "EGP", "Africa/Cairo", "ar-EG", "+20", "me-central", tax_rate_bp=1400),
    Country(
        "MA",
        "Morocco",
        "MAD",
        "Africa/Casablanca",
        "fr-MA",
        "+212",
        "eu-west",
        "TVA",
        "ICE",
        tax_rate_bp=2000,
    ),
    # Europe
    Country(
        "GB",
        "United Kingdom",
        "GBP",
        "Europe/London",
        "en-GB",
        "+44",
        "eu-west",
        "VAT",
        "VAT number",
        r"^(GB)?(\d{9}|\d{12})$",
        2000,
    ),
    Country(
        "IE",
        "Ireland",
        "EUR",
        "Europe/Dublin",
        "en-IE",
        "+353",
        "eu-west",
        "VAT",
        "VAT number",
        EU_VAT.format(cc="IE"),
        2300,
    ),
    _eu("DE", "Germany", "EUR", "Europe/Berlin", "de-DE", "+49", 1900),
    _eu("FR", "France", "EUR", "Europe/Paris", "fr-FR", "+33", 2000),
    _eu("NL", "Netherlands", "EUR", "Europe/Amsterdam", "nl-NL", "+31", 2100),
    _eu("BE", "Belgium", "EUR", "Europe/Brussels", "nl-BE", "+32", 2100),
    _eu("ES", "Spain", "EUR", "Europe/Madrid", "es-ES", "+34", 2100),
    _eu("PT", "Portugal", "EUR", "Europe/Lisbon", "pt-PT", "+351", 2300),
    _eu("IT", "Italy", "EUR", "Europe/Rome", "it-IT", "+39", 2200),
    _eu("AT", "Austria", "EUR", "Europe/Vienna", "de-AT", "+43", 2000),
    _eu("GR", "Greece", "EUR", "Europe/Athens", "el-GR", "+30", 2400),
    _eu("SE", "Sweden", "SEK", "Europe/Stockholm", "sv-SE", "+46", 2500),
    _eu("DK", "Denmark", "DKK", "Europe/Copenhagen", "da-DK", "+45", 2500),
    _eu("FI", "Finland", "EUR", "Europe/Helsinki", "fi-FI", "+358", 2550),
    _eu("PL", "Poland", "PLN", "Europe/Warsaw", "pl-PL", "+48", 2300),
    _eu("CZ", "Czechia", "CZK", "Europe/Prague", "cs-CZ", "+420", 2100),
    _eu("HR", "Croatia", "EUR", "Europe/Zagreb", "hr-HR", "+385", 2500),
    _eu("CY", "Cyprus", "EUR", "Asia/Nicosia", "el-CY", "+357", 1900),
    _eu("MT", "Malta", "EUR", "Europe/Malta", "en-MT", "+356", 1800),
    Country(
        "CH",
        "Switzerland",
        "CHF",
        "Europe/Zurich",
        "de-CH",
        "+41",
        "eu-west",
        "MWST/TVA",
        "UID",
        r"^CHE-?\d{3}\.?\d{3}\.?\d{3}( ?(MWST|TVA|IVA))?$",
        810,
    ),
    Country(
        "NO",
        "Norway",
        "NOK",
        "Europe/Oslo",
        "nb-NO",
        "+47",
        "eu-west",
        "MVA",
        "Organisation number",
        tax_rate_bp=2500,
    ),
    Country("IS", "Iceland", "ISK", "Atlantic/Reykjavik", "is-IS", "+354", "eu-west"),
    Country("TR", "Türkiye", "TRY", "Europe/Istanbul", "tr-TR", "+90", "eu-west", "KDV", "Tax number"),
    # Middle East
    Country(
        "AE",
        "United Arab Emirates",
        "AED",
        "Asia/Dubai",
        "en-AE",
        "+971",
        "me-central",
        "VAT",
        "TRN",
        r"^\d{15}$",
        500,
    ),
    Country(
        "SA",
        "Saudi Arabia",
        "SAR",
        "Asia/Riyadh",
        "ar-SA",
        "+966",
        "me-central",
        "VAT",
        "VAT number",
        r"^3\d{13}3$",
        1500,
    ),
    Country("QA", "Qatar", "QAR", "Asia/Qatar", "ar-QA", "+974", "me-central", "Tax", "Tax ID"),
    Country("OM", "Oman", "OMR", "Asia/Muscat", "ar-OM", "+968", "me-central", tax_rate_bp=500),
    Country("BH", "Bahrain", "BHD", "Asia/Bahrain", "ar-BH", "+973", "me-central"),
    Country("JO", "Jordan", "JOD", "Asia/Amman", "ar-JO", "+962", "me-central", "GST", "Tax number"),
    # Asia-Pacific
    Country(
        "AU",
        "Australia",
        "AUD",
        "Australia/Sydney",
        "en-AU",
        "+61",
        "ap-southeast",
        "GST",
        "ABN",
        r"^\d{2} ?\d{3} ?\d{3} ?\d{3}$",
        1000,
    ),
    Country(
        "NZ",
        "New Zealand",
        "NZD",
        "Pacific/Auckland",
        "en-NZ",
        "+64",
        "ap-southeast",
        "GST",
        "GST number",
        r"^\d{2,3}-?\d{3}-?\d{3}$",
        1500,
    ),
    Country(
        "SG",
        "Singapore",
        "SGD",
        "Asia/Singapore",
        "en-SG",
        "+65",
        "ap-southeast",
        "GST",
        "GST registration number",
        tax_rate_bp=900,
    ),
    Country(
        "MY", "Malaysia", "MYR", "Asia/Kuala_Lumpur", "en-MY", "+60", "ap-southeast", "SST", "SST number"
    ),
    Country(
        "TH",
        "Thailand",
        "THB",
        "Asia/Bangkok",
        "th-TH",
        "+66",
        "ap-southeast",
        "VAT",
        "Tax ID",
        r"^\d{13}$",
        700,
    ),
    Country("ID", "Indonesia", "IDR", "Asia/Jakarta", "id-ID", "+62", "ap-southeast", "PPN", "NPWP"),
    Country(
        "PH",
        "Philippines",
        "PHP",
        "Asia/Manila",
        "en-PH",
        "+63",
        "ap-southeast",
        "VAT",
        "TIN",
        tax_rate_bp=1200,
    ),
    Country("VN", "Vietnam", "VND", "Asia/Ho_Chi_Minh", "vi-VN", "+84", "ap-southeast", "VAT", "Tax code"),
    Country(
        "IN",
        "India",
        "INR",
        "Asia/Kolkata",
        "en-IN",
        "+91",
        "ap-southeast",
        "GST",
        "GSTIN",
        r"^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]$",
    ),
    Country("LK", "Sri Lanka", "LKR", "Asia/Colombo", "en-LK", "+94", "ap-southeast", "VAT", "TIN"),
    Country("MV", "Maldives", "USD", "Indian/Maldives", "en-MV", "+960", "ap-southeast", "GST", "TIN"),
    Country(
        "JP",
        "Japan",
        "JPY",
        "Asia/Tokyo",
        "ja-JP",
        "+81",
        "ap-southeast",
        "Consumption tax",
        "Registration number",
        r"^T\d{13}$",
        1000,
    ),
    Country(
        "HK",
        "Hong Kong",
        "HKD",
        "Asia/Hong_Kong",
        "en-HK",
        "+852",
        "ap-southeast",
        "Tax",
        "Business registration",
    ),
    # Americas
    Country(
        "US",
        "United States",
        "USD",
        "America/New_York",
        "en-US",
        "+1",
        "us-east",
        "Sales tax",
        "EIN",
        r"^\d{2}-?\d{7}$",
    ),
    Country(
        "CA",
        "Canada",
        "CAD",
        "America/Toronto",
        "en-CA",
        "+1",
        "us-east",
        "GST/HST",
        "Business number",
        r"^\d{9}( ?RT ?\d{4})?$",
    ),
    Country(
        "MX",
        "Mexico",
        "MXN",
        "America/Mexico_City",
        "es-MX",
        "+52",
        "us-east",
        "IVA",
        "RFC",
        r"^[A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3}$",
        1600,
    ),
    Country(
        "BR",
        "Brazil",
        "BRL",
        "America/Sao_Paulo",
        "pt-BR",
        "+55",
        "us-east",
        "Tax",
        "CNPJ",
        r"^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$",
    ),
    Country(
        "AR",
        "Argentina",
        "ARS",
        "America/Argentina/Buenos_Aires",
        "es-AR",
        "+54",
        "us-east",
        "IVA",
        "CUIT",
        r"^\d{2}-?\d{8}-?\d$",
        2100,
    ),
    Country(
        "CL", "Chile", "CLP", "America/Santiago", "es-CL", "+56", "us-east", "IVA", "RUT", tax_rate_bp=1900
    ),
    Country(
        "CO", "Colombia", "COP", "America/Bogota", "es-CO", "+57", "us-east", "IVA", "NIT", tax_rate_bp=1900
    ),
    Country("PE", "Peru", "PEN", "America/Lima", "es-PE", "+51", "us-east", "IGV", "RUC", r"^\d{11}$"),
    Country(
        "CR",
        "Costa Rica",
        "CRC",
        "America/Costa_Rica",
        "es-CR",
        "+506",
        "us-east",
        "IVA",
        "Cédula jurídica",
        tax_rate_bp=1300,
    ),
    Country("JM", "Jamaica", "JMD", "America/Jamaica", "en-JM", "+1", "us-east", "GCT", "TRN"),
)


def _world() -> dict[str, Country]:
    """Every inhabited country (D84): the detailed entries above where they exist, otherwise
    the country's currency, main zone and language with a general tax name and no rate."""
    profiles = {c.code: c for c in _COUNTRIES}
    out: dict[str, Country] = {}
    for code, name, currency, dial, locale, region, zones in WORLD:
        p = profiles.get(code)
        if p is not None:
            out[code] = replace(p, timezones=(p.timezone, *(z for z in zones if z != p.timezone)))
        else:
            out[code] = Country(
                code, name, currency, zones[0], locale, dial, region, "Tax", "Tax number", timezones=zones
            )
    return out


# Every country Diyneco knows. Which ones take new hotels is the platform's choice
# (operational countries, D84): app.services.countries.
COUNTRIES: dict[str, Country] = _world()


def country(code: str | None) -> Country | None:
    return COUNTRIES.get((code or "").upper())


def regions(code: str) -> tuple[str, tuple[tuple[str, str], ...]]:
    """What the country calls its first-level regions and the list (ISO 3166-2), or ("Region",
    ()) where none are listed and the region is free text (D85)."""
    return SUBDIVISIONS.get(code.upper(), ("Region", ()))


def region_name(country_code: str, region_code: str) -> str | None:
    return dict(regions(country_code)[1]).get(region_code)


def tax_id_ok(country_code: str | None, value: str) -> bool:
    c = country(country_code)
    return c.tax_id_ok(value) if c else bool(re.fullmatch(GENERIC_TAX_ID, value.strip().upper()))
