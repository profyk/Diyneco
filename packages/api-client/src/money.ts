/**
 * Display helpers. Amounts are computed on the server; the apps only format them.
 */
export interface Money {
  amount_minor: number;
  currency: string;
}

const formatters = new Map<string, Intl.NumberFormat>();

/** The currency's own symbol and two decimals, e.g. R1,234.50, €12.00, KSh 300.00. */
export function formatMoney(m: Money | null | undefined): string {
  if (!m) return "–";
  let f = formatters.get(m.currency);
  if (!f) {
    try {
      f = new Intl.NumberFormat("en", {
        style: "currency",
        currency: m.currency,
        currencyDisplay: "narrowSymbol",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    } catch {
      f = new Intl.NumberFormat("en", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    formatters.set(m.currency, f);
  }
  return f.format(m.amount_minor / 100).replace("-", "−");
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

/** Converts a typed amount ("125.50", "1,200") to minor units, or null if it is not a valid amount. */
export function parseAmount(text: string): number | null {
  const cleaned = text.replace(/[^\d.]/g, "");
  if (!/^\d{1,9}(\.\d{0,2})?$/.test(cleaned)) return null;
  const [whole = "0", frac = ""] = cleaned.split(".");
  return Number(whole) * 100 + Number(frac.padEnd(2, "0"));
}

/** An amount in a given currency; the currency always comes from the hotel or plan. */
export function money(amount_minor: number, currency: string): Money {
  return { amount_minor, currency };
}

const timeFmt = new Intl.DateTimeFormat("en-ZA", { hour: "2-digit", minute: "2-digit", hour12: false });
const dateFmt = new Intl.DateTimeFormat("en-ZA", { day: "numeric", month: "short", year: "numeric" });

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
