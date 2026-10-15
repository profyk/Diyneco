"use client";

import { type components, formatMoney, ok } from "@diyneco/api-client";
import { Card, CardHeader, cn, ErrorNotice, PageHeader, propertyTypeLabel, Skeleton, StatTile, Table, Td, Th } from "@diyneco/shared-ui";
import { Flag } from "@diyneco/shared-ui/countries";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ColumnChart, FunnelBars } from "./charts";
import { useSession } from "./session";

// Platform insights (DECISIONS D87): adoption, activation, conversion, churn, cohorts and where
// hotels are, from aggregates only. Money is shown per currency, never added across them.

type Money = { amount_minor: number; currency: string };
type Breakdown = {
  key: string;
  label: string;
  hotels: number;
  active: number;
  activated: number;
  paying: number;
  trials: number;
  rooms: number;
  orders_30d: number;
  mrr: Money[];
  gmv_30d: Money[];
};

const PERIODS = [
  { days: 30, label: "30 days" },
  { days: 90, label: "90 days" },
  { days: 365, label: "12 months" },
] as const;

const ROLES: Record<string, string> = {
  hotel_owner: "Owners",
  hotel_admin: "Hotel admins",
  general_manager: "General managers",
  reception_manager: "Reception managers",
  receptionist: "Receptionists",
  finance_manager: "Finance managers",
  kitchen_manager: "Kitchen managers",
  kitchen_staff: "Kitchen staff",
  room_service_manager: "Room-service managers",
  room_service_staff: "Room-service staff",
};

const pct = (bp: number) => `${(bp / 100).toFixed(bp % 100 ? 1 : 0)}%`;
const moneys = (m: Money[]) => (m.length ? m.map(formatMoney).join(" · ") : "–");
const share = (part: number, whole: number) => (whole ? `${Math.round((part / whole) * 100)}%` : "–");

function isoDay(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function Insights() {
  const { api } = useSession();
  const [days, setDays] = useState<number>(30);
  const [tab, setTab] = useState<"country" | "region" | "type">("country");
  const until = new Date();
  const since = new Date(until.getTime() - (days - 1) * 86_400_000);
  const q = useQuery({
    queryKey: ["insights", days],
    queryFn: () => ok(api.GET("/api/v1/admin/insights", { params: { query: { since: isoDay(since), until: isoDay(until) } } })),
  });

  return (
    <>
      <PageHeader
        title="Insights"
        description="Adoption, activation, conversion and churn across every hotel. Aggregates only."
        actions={
          <div role="radiogroup" aria-label="Period" className="flex rounded-[10px] border border-line bg-surface p-0.5">
            {PERIODS.map((p) => (
              <button
                key={p.days}
                type="button"
                role="radio"
                aria-checked={days === p.days}
                onClick={() => setDays(p.days)}
                className={cn("rounded-lg px-3 py-1.5 text-sm", days === p.days ? "bg-tint font-medium text-blue" : "text-ink hover:bg-surface-2")}
              >
                {p.label}
              </button>
            ))}
          </div>
        }
      />
      {q.error ? <ErrorNotice error={q.error} /> : null}
      {!q.data ? (
        <Skeleton className="h-96" />
      ) : (
        <InsightsBody data={q.data} days={days} tab={tab} setTab={setTab} />
      )}
    </>
  );
}

function InsightsBody({
  data,
  days,
  tab,
  setTab,
}: {
  data: components["schemas"]["InsightsOut"];
  days: number;
  tab: "country" | "region" | "type";
  setTab: (t: "country" | "region" | "type") => void;
}) {
  const t = data.totals;
  const p = data.period;
  // Daily columns for 30 days; weekly sums beyond that so columns stay readable.
  const step = days <= 31 ? 1 : 7;
  const points = [];
  for (let i = 0; i < data.days.length; i += step) {
    const chunk = data.days.slice(i, i + step);
    const value = chunk.reduce((n, d) => n + d.signups, 0);
    const first = chunk[0]?.day ?? "";
    const label = new Date(`${first}T12:00:00Z`).toLocaleDateString(undefined, { day: "numeric", month: "short" });
    points.push({ label, value, tooltip: `${step === 1 ? label : `Week of ${label}`}: ${value} signup${value === 1 ? "" : "s"}` });
  }
  const rows: Breakdown[] = tab === "country" ? data.by_country : tab === "region" ? data.by_region : data.by_property_type;

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Hotels" value={t.hotels} hint={`${t.active} live · ${t.pending_approval} waiting · ${t.suspended} suspended`} />
        <StatTile label="In daily use" value={t.in_use_30d} hint={`an order in 30 days · ${t.activated} fully set up`} />
        <StatTile label="Paying" value={t.paying} hint={`${t.trials} on trial · ${t.no_plan} without a plan`} tone="good" />
        <StatTile label="Monthly recurring revenue" value={moneys(t.mrr)} hint={`${t.owners} owners · ${t.multi_property_owners} with several properties`} />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label={`Signups, last ${days} days`} value={p.signups} hint={`${pct(p.activation_bp)} fully set up`} />
        <StatTile
          label="Trial to paid"
          value={p.trials_ended ? pct(p.trial_conversion_bp) : "–"}
          hint={`${p.trials_converted} of ${p.trials_ended} trials that ended`}
        />
        <StatTile
          label="Churn"
          value={p.paying_at_start ? pct(p.churn_bp) : "–"}
          hint={`${p.churned} of ${p.paying_at_start} paying at the start`}
          tone={p.churn_bp > 500 ? "warn" : "neutral"}
        />
        <StatTile label="MRR won · lost" value={moneys(p.new_mrr)} hint={`lost ${moneys(p.churned_mrr)}`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader title="Signups" description={step === 1 ? "New properties per day" : "New properties per week"} />
          <div className="p-5">
            <ColumnChart title="New properties over time" points={points} />
          </div>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader title="Activation" description={`What the last ${days} days' signups have done so far`} />
          <div className="p-5">
            <FunnelBars steps={data.funnel.map((f) => ({ label: f.label, value: f.hotels }))} />
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Where hotels are and what they are"
          description={`Money processed through hotels' bills in the last 30 days: ${moneys(t.gmv_30d)}`}
          actions={
            <div role="tablist" className="flex gap-1">
              {(
                [
                  ["country", "Country"],
                  ["region", "Province or state"],
                  ["type", "Category"],
                ] as const
              ).map(([k, l]) => (
                <button
                  key={k}
                  type="button"
                  role="tab"
                  aria-selected={tab === k}
                  onClick={() => setTab(k)}
                  className={cn("rounded-lg px-3 py-1.5 text-sm", tab === k ? "bg-tint font-medium text-blue" : "text-ink hover:bg-surface-2")}
                >
                  {l}
                </button>
              ))}
            </div>
          }
        />
        <Table>
          <thead>
            <tr>
              <Th>{tab === "country" ? "Country" : tab === "region" ? "Province or state" : "Category"}</Th>
              <Th className="text-right">Hotels</Th>
              <Th className="text-right">Live</Th>
              <Th className="text-right">Set up</Th>
              <Th className="text-right">Paying</Th>
              <Th className="text-right">Rooms</Th>
              <Th className="text-right">Orders, 30 days</Th>
              <Th className="text-right">MRR</Th>
              <Th className="text-right">Processed, 30 days</Th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key}>
                <Td>
                  <span className="flex items-center gap-2">
                    {tab === "country" ? <Flag code={r.key} className="h-3.5 w-5" /> : null}
                    {tab === "type" ? propertyTypeLabel(r.key === "unknown" ? null : r.key) : r.label}
                  </span>
                </Td>
                <Td className="text-right tabular-nums">{r.hotels}</Td>
                <Td className="text-right tabular-nums">{r.active}</Td>
                <Td className="text-right tabular-nums">
                  {r.activated} <span className="text-muted">({share(r.activated, r.hotels)})</span>
                </Td>
                <Td className="text-right tabular-nums">{r.paying}</Td>
                <Td className="text-right tabular-nums">{r.rooms}</Td>
                <Td className="text-right tabular-nums">{r.orders_30d}</Td>
                <Td className="text-right tabular-nums">{moneys(r.mrr)}</Td>
                <Td className="text-right tabular-nums">{moneys(r.gmv_30d)}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Signup cohorts" description="Properties by the month they joined, and where they are today" />
          <Table>
            <thead>
              <tr>
                <Th>Joined</Th>
                <Th className="text-right">Signups</Th>
                <Th className="text-right">Set up</Th>
                <Th className="text-right">In use</Th>
                <Th className="text-right">Paying</Th>
                <Th className="text-right">Closed</Th>
              </tr>
            </thead>
            <tbody>
              {data.cohorts.map((c) => (
                <tr key={c.month}>
                  <Td>{new Date(`${c.month}-15T12:00:00Z`).toLocaleDateString(undefined, { month: "short", year: "numeric" })}</Td>
                  <Td className="text-right tabular-nums">{c.signups}</Td>
                  <Td className="text-right tabular-nums">{share(c.activated, c.signups)}</Td>
                  <Td className="text-right tabular-nums">{share(c.in_use_30d, c.signups)}</Td>
                  <Td className="text-right tabular-nums">{share(c.paying, c.signups)}</Td>
                  <Td className="text-right tabular-nums">{c.closed}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
        <Card>
          <CardHeader title="Hotel users" description="Staff accounts by role, and who signed in recently" />
          <Table>
            <thead>
              <tr>
                <Th>Role</Th>
                <Th className="text-right">Accounts</Th>
                <Th className="text-right">Active, 7 days</Th>
                <Th className="text-right">Active, 30 days</Th>
              </tr>
            </thead>
            <tbody>
              {data.users.map((u) => (
                <tr key={u.role}>
                  <Td>{ROLES[u.role] ?? u.role}</Td>
                  <Td className="text-right tabular-nums">{u.members}</Td>
                  <Td className="text-right tabular-nums">
                    {u.active_7d} <span className="text-muted">({share(u.active_7d, u.members)})</span>
                  </Td>
                  <Td className="text-right tabular-nums">
                    {u.active_30d} <span className="text-muted">({share(u.active_30d, u.members)})</span>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      </div>
    </div>
  );
}
