/**
 * Display helpers. Amounts are computed on the server; the apps only format them.
 */
export interface Money {
  amount_minor: number;
  currency: string;
}

const formatters = new Map<string, Intl.NumberFormat>();

// The hotel's locale (BCP 47) and time zone (IANA), from /auth/me or the tablet session (D69).
// Until an app sets them, the browser's own are used.
let displayLocale: string | undefined;
let displayZone: string | undefined;
let timeFmt = makeTimeFmt();
let dateFmt = makeDateFmt();

function makeTimeFmt(): Intl.DateTimeFormat {
  return new Intl.DateTimeFormat(displayLocale, { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: displayZone });
}

function makeDateFmt(): Intl.DateTimeFormat {
  return new Intl.DateTimeFormat(displayLocale, { day: "numeric", month: "short", year: "numeric", timeZone: displayZone });
}

/** Formats every later amount, date and time for this hotel. Unknown values fall back to the browser's. */
export function setDisplayLocale(locale: string | null | undefined, timeZone?: string | null): void {
  const valid = (fn: () => unknown) => {
    try {
      fn();
      return true;
    } catch {
      return false;
    }
  };
  const nextLocale = locale && valid(() => new Intl.NumberFormat(locale)) ? locale : undefined;
  const nextZone = timeZone && valid(() => new Intl.DateTimeFormat("en", { timeZone })) ? timeZone : undefined;
  if (nextLocale === displayLocale && nextZone === displayZone) return;
  displayLocale = nextLocale;
  displayZone = nextZone;
  formatters.clear();
  timeFmt = makeTimeFmt();
  dateFmt = makeDateFmt();
}

// Must match the API's currency catalogue (backend/app/core/currencies.py): amounts are integers
// of 10^-decimals of the currency. Everything not listed has 2.
const ZERO_DECIMALS = new Set(["JPY", "CLP", "ISK", "VND", "UGX", "RWF", "IDR"]);
const THREE_DECIMALS = new Set(["BHD", "OMR", "JOD"]);

/** Decimal places of a currency's minor unit: 2 for most, 0 for yen, 3 for dinars. */
export function currencyDecimals(currency: string): number {
  return ZERO_DECIMALS.has(currency) ? 0 : THREE_DECIMALS.has(currency) ? 3 : 2;
}

/** The currency's own symbol and decimals, e.g. R1,234.50, €12.00, ¥1,500, BHD 2.125. */
export function formatMoney(m: Money | null | undefined): string {
  if (!m) return "–";
  const digits = currencyDecimals(m.currency);
  let f = formatters.get(m.currency);
  if (!f) {
    try {
      f = new Intl.NumberFormat(displayLocale ?? "en", {
        style: "currency",
        currency: m.currency,
        currencyDisplay: "narrowSymbol",
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });
    } catch {
      f = new Intl.NumberFormat(displayLocale ?? "en", { minimumFractionDigits: digits, maximumFractionDigits: digits });
    }
    formatters.set(m.currency, f);
  }
  return f.format(m.amount_minor / 10 ** digits).replace("-", "−");
}

/** An amount as an editable number in major units ("1500.00", "1500" for yen). */
export function toAmountInput(m: Money | null | undefined): string {
  if (!m) return "";
  const digits = currencyDecimals(m.currency);
  return (m.amount_minor / 10 ** digits).toFixed(digits);
}

/** The symbol a currency is shown with (for field labels). */
export function currencySymbol(currency: string): string {
  try {
    return (
      new Intl.NumberFormat("en", { style: "currency", currency, currencyDisplay: "narrowSymbol" })
        .formatToParts(0)
        .find((p) => p.type === "currency")?.value ?? currency
    );
  } catch {
    return currency;
  }
}

/** The decimal sign of the display locale ("." or ","). */
function decimalSign(): string {
  try {
    return new Intl.NumberFormat(displayLocale).formatToParts(1.5).find((p) => p.type === "decimal")?.value ?? ".";
  } catch {
    return ".";
  }
}

/**
 * Converts a typed amount to minor units of `currency`, or null if it is not a valid amount
 * (including more decimals than the currency has). Both "1,234.50" and "1.234,50" work: the
 * last "." or "," is the decimal sign when at most the currency's decimals follow it (with
 * exactly three digits after it, only if it is the locale's decimal sign, so "1,200" stays
 * twelve hundred); every other separator and space is grouping. A currency symbol or code is
 * ignored; a minus sign is refused.
 */
export function parseAmount(text: string, currency: string): number | null {
  const digits = currencyDecimals(currency);
  if (text.includes("-") || text.includes("−")) return null;
  const compact = text.replace(/[^\d.,]/g, "");
  if (!/\d/.test(compact)) return null;
  let whole = compact;
  let frac = "";
  const at = Math.max(compact.lastIndexOf("."), compact.lastIndexOf(","));
  if (at >= 0) {
    const after = compact.slice(at + 1);
    const isDecimal =
      digits > 0 && /^\d+$/.test(after) && after.length <= digits && (after.length !== 3 || compact[at] === decimalSign());
    if (isDecimal) {
      whole = compact.slice(0, at);
      frac = after;
    } else if (compact[at] === decimalSign()) {
      return null; // the locale's decimal sign with more decimals than the currency has
    }
  }
  whole = whole.replace(/[.,]/g, "") || "0";
  if (!/^\d{1,12}$/.test(whole)) return null;
  return Number(whole) * 10 ** digits + Number(frac.padEnd(digits, "0") || "0");
}

/** An amount in a given currency; the currency always comes from the hotel or plan. */
export function money(amount_minor: number, currency: string): Money {
  return { amount_minor, currency };
}


export function formatTime(iso: string | null | undefined): string {
  return iso ? timeFmt.format(new Date(iso)) : "–";
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "–";
  // A business date ("2026-10-12") is a calendar day, not an instant: never shift it by zone.
  if (iso.length === 10) {
    return new Intl.DateTimeFormat(displayLocale, { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(
      new Date(`${iso}T12:00:00Z`),
    );
  }
  return dateFmt.format(new Date(iso));
}

/** "4 min", "1 h 05 min" since an ISO time. */
export function elapsed(iso: string | null | undefined, now: number = Date.now()): string {
  if (!iso) return "–";
  const minutes = Math.max(0, Math.floor((now - new Date(iso).getTime()) / 60000));
  if (minutes < 60) return `${minutes} min`;
  return `${Math.floor(minutes / 60)} h ${String(minutes % 60).padStart(2, "0")} min`;
}
