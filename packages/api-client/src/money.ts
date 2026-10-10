/**
 * Display helpers. Amounts are computed on the server; the apps only format them.
 */
export interface Money {
  amount_minor: number;
  currency: string;
}

/** "R 1 234,56"-style formatting is avoided: South African hotels write R1,234.56. */
export function formatMoney(m: Money | null | undefined): string {
  if (!m) return "–";
  const negative = m.amount_minor < 0;
  const abs = Math.abs(m.amount_minor);
  const whole = Math.floor(abs / 100).toLocaleString("en-US");
  const cents = String(abs % 100).padStart(2, "0");
  const symbol = m.currency === "ZAR" ? "R" : `${m.currency} `;
  return `${negative ? "−" : ""}${symbol}${whole}.${cents}`;
}

/** Converts a typed amount ("125.50", "R1,200") to minor units, or null if it is not a valid amount. */
export function parseAmount(text: string): number | null {
  const cleaned = text.replace(/[R\s,]/gi, "");
  if (!/^\d{1,9}(\.\d{0,2})?$/.test(cleaned)) return null;
  const [whole = "0", frac = ""] = cleaned.split(".");
  return Number(whole) * 100 + Number(frac.padEnd(2, "0"));
}

export function zar(amount_minor: number): Money {
  return { amount_minor, currency: "ZAR" };
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
