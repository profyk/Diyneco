"use client";

import { formatMoney } from "@diyneco/api-client";
import { cn } from "@diyneco/shared-ui";
import { useState } from "react";

import type { Plans } from "./api";

// Pricing comes only from Admin > Plans & Pricing (GET /plans): published plans with the
// prices in force, so the site always matches what hotels are billed (D79, D87).

const INTERVALS = [
  { key: "month", label: "Monthly" },
  { key: "quarter", label: "Quarterly" },
  { key: "year", label: "Yearly" },
] as const;

const LIMIT_LABELS: Record<string, string> = {
  rooms: "rooms",
  devices: "tablets and displays",
  staff: "staff accounts",
  api_keys: "API keys",
};

function periodLabel(interval: string, n: number | null | undefined): string {
  const unit = { month: "month", quarter: "quarter", year: "year" }[interval] ?? interval;
  return n && n > 1 ? `${n} ${unit}s` : unit;
}

export function PricingTable({ plans, signupUrl }: { plans: Plans | null; signupUrl: string }) {
  const available = INTERVALS.filter((i) => plans?.data.some((p) => p.prices.some((x) => x.interval === i.key)));
  const [interval, setInterval] = useState<string>(available[0]?.key ?? "month");

  if (!plans || plans.data.length === 0) {
    return (
      <div className="rounded-[var(--radius-card)] border border-line bg-surface p-8 text-center text-muted">
        Plans are being finalised. <a href="/contact" className="text-blue hover:underline">Contact us</a> for pricing.
      </div>
    );
  }
  const bestSaving = Math.max(0, ...plans.data.flatMap((p) => p.prices.filter((x) => x.interval === "year").map((x) => x.saving_bp ?? 0)));

  return (
    <div>
      {available.length > 1 ? (
        <div className="mb-8 flex justify-center">
          <div role="radiogroup" aria-label="Billing period" className="inline-flex rounded-full border border-line bg-surface p-1">
            {available.map((i) => (
              <button
                key={i.key}
                type="button"
                role="radio"
                aria-checked={interval === i.key}
                onClick={() => setInterval(i.key)}
                className={cn(
                  "rounded-full px-4 py-1.5 text-sm font-medium transition",
                  interval === i.key ? "bg-brand text-on-brand" : "text-ink hover:bg-surface-2",
                )}
              >
                {i.label}
                {i.key === "year" && bestSaving > 0 ? <span className="ml-1 text-xs opacity-80">save up to {Math.round(bestSaving / 100)}%</span> : null}
              </button>
            ))}
          </div>
        </div>
      ) : null}
      <div className={cn("grid gap-6", plans.data.length >= 3 ? "lg:grid-cols-3" : plans.data.length === 2 ? "md:grid-cols-2" : "")}>
        {plans.data.map((p) => {
          const price = p.prices.find((x) => x.interval === interval) ?? p.prices[0];
          const limits = Object.entries(p.limits).filter(([k]) => LIMIT_LABELS[k]);
          return (
            <div
              key={p.code}
              className={cn(
                "relative flex flex-col rounded-[var(--radius-card)] border bg-surface p-6",
                p.recommended ? "border-blue shadow-lg ring-1 ring-blue" : "border-line",
              )}
            >
              {p.recommended ? (
                <span className="absolute -top-3 left-6 rounded-full bg-blue px-3 py-0.5 text-xs font-medium text-white">Most popular</span>
              ) : null}
              <h3 className="font-display text-xl font-semibold text-ink">{p.name}</h3>
              {p.short_description ? <p className="mt-1 text-sm text-muted">{p.short_description}</p> : null}
              {price ? (
                <div className="mt-5">
                  <p className="flex items-baseline gap-1">
                    <span className="font-display text-4xl font-semibold text-ink">{formatMoney(price.per_month)}</span>
                    <span className="text-muted">/ month</span>
                  </p>
                  <p className="mt-1 text-sm text-muted">
                    {price.interval === "month" ? "Billed monthly" : `${formatMoney(price.amount)} billed every ${periodLabel(price.interval, 1)}`}
                    {price.saving_bp ? ` · save ${Math.round(price.saving_bp / 100)}%` : ""}
                  </p>
                  {price.intro_amount ? (
                    <p className="mt-2 inline-block rounded-md bg-good-bg px-2 py-1 text-xs font-medium text-good">
                      {formatMoney(price.intro_amount)} for the first {periodLabel(price.interval, price.intro_periods)}
                    </p>
                  ) : null}
                  {p.promo_discount_bp && p.promo_ends_on ? (
                    <p className="mt-2 text-xs font-medium text-good">
                      {Math.round(p.promo_discount_bp / 100)}% off until {new Date(`${p.promo_ends_on}T12:00:00Z`).toLocaleDateString()}
                    </p>
                  ) : null}
                </div>
              ) : null}
              <a
                href={`${signupUrl}?plan=${encodeURIComponent(p.code)}`}
                className={cn(
                  "mt-6 inline-flex h-11 items-center justify-center rounded-[10px] px-5 font-medium",
                  p.recommended ? "bg-brand text-on-brand hover:opacity-90" : "border border-line text-ink hover:bg-surface-2",
                )}
              >
                {p.trial_days ? `Start ${p.trial_days}-day free trial` : "Get started"}
              </a>
              <ul className="mt-6 flex flex-col gap-2 text-sm text-ink">
                {limits.map(([k, v]) => (
                  <li key={k} className="flex gap-2">
                    <span aria-hidden className="text-good">✓</span>
                    {v} {LIMIT_LABELS[k]}
                  </li>
                ))}
                {p.highlights.map((h) => (
                  <li key={h} className="flex gap-2">
                    <span aria-hidden className="text-good">✓</span>
                    {h}
                  </li>
                ))}
                {p.support_level ? (
                  <li className="flex gap-2">
                    <span aria-hidden className="text-good">✓</span>
                    {p.support_level} support
                  </li>
                ) : null}
              </ul>
              {p.setup_fee.amount_minor ? <p className="mt-4 text-xs text-muted">One-off setup fee {formatMoney(p.setup_fee)}</p> : null}
            </div>
          );
        })}
      </div>
      <p className="mt-6 text-center text-xs text-muted">
        {plans.tax_charged && plans.tax_name
          ? `Prices ${plans.data[0]?.tax_treatment === "inclusive" ? "include" : "exclude"} ${plans.tax_name}${plans.tax_rate_bp ? ` (${plans.tax_rate_bp / 100}%)` : ""}.`
          : "No tax is added to these prices."}{" "}
        Cancel any time; nothing is charged during the free trial.
      </p>
    </div>
  );
}
