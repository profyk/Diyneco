/**
 * Display helpers. Amounts are computed on the server; the apps only format them.
 */
export interface Money {
  amount_minor: number;
  currency: string;
}

const formatters = new Map<string, Intl.NumberFormat>();

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
      f = new Intl.NumberFormat("en", {
        style: "currency",
        currency: m.currency,
        currencyDisplay: "narrowSymbol",
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });
    } catch {
      f = new Intl.NumberFormat("en", { minimumFractionDigits: digits, maximumFractionDigits: digits });
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

/**
 * Converts a typed amount ("125.50", "1,200") to minor units of `currency`, or null if it is not
 * a valid amount (including more decimals than the currency has).
 */
export function parseAmount(text: string, currency: string): number | null {
  const digits = currencyDecimals(currency);
  const cleaned = text.replace(/[^\d.]/g, "");
  const pattern = digits ? new RegExp(`^\\d{1,12}(\\.\\d{0,${digits}})?$`) : /^\d{1,12}$/;
  if (!pattern.test(cleaned)) return null;
  const [whole = "0", frac = ""] = cleaned.split(".");
  return Number(whole) * 10 ** digits + Number(frac.padEnd(digits, "0") || "0");
}

/** An amount in a given currency; the currency always comes from the hotel or plan. */
export function money(amount_minor: number, currency: string): Money {
  return { amount_minor, currency };
}

const timeFmt = new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", hour12: false });
const dateFmt = new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short", year: "numeric" });

export function formatTime(iso: string | null | undefined): string {
  return iso ? timeFmt.format(new Date(iso)) : "–";
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "–";
  return dateFmt.format(new Date(iso.length === 10 ? `${iso}T12:00:00` : iso));
}

/** "4 min", "1 h 05 min" since an ISO time. */
export function elapsed(iso: string | null | undefined, now: number = Date.now()): string {
  if (!iso) return "–";
  const minutes = Math.max(0, Math.floor((now - new Date(iso).getTime()) / 60000));
  if (minutes < 60) return `${minutes} min`;
  return `${Math.floor(minutes / 60)} h ${String(minutes % 60).padStart(2, "0")} min`;
}
