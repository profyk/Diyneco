"use client";

import { formatDate, formatMoney, ok } from "@diyneco/api-client";
import { Badge, Button, Card, EmptyState, ErrorNotice, PageHeader, propertyTypeLabel, Skeleton, StatTile } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { useSession } from "../session";

// Every property the owner holds, side by side (D86). Each figure comes from that hotel's own
// reports, read under its own context; money is totalled per currency, never across them.

const STATUS: Record<string, { label: string; tone: "good" | "warn" | "crit" | "neutral" }> = {
  active: { label: "Live", tone: "good" },
  pending_approval: { label: "Waiting for approval", tone: "warn" },
  suspended: { label: "Suspended", tone: "crit" },
  closed: { label: "Closed", tone: "neutral" },
};

function planLabel(status: string | null, plan: string | null, trialEnds: string | null): string {
  if (!status) return "No plan yet";
  if (status === "trial") return trialEnds ? `Free trial until ${formatDate(trialEnds)}` : "Free trial";
  return `${plan ?? "Plan"} · ${status.replace(/_/g, " ")}`;
}

export function Properties() {
  const { api, state, switchHotel } = useSession();
  const q = useQuery({ queryKey: ["portfolio"], queryFn: () => ok(api.GET("/api/v1/portfolio")), refetchInterval: 60_000 });
  const currentId = state.status === "signed-in" ? state.me.hotel?.id : undefined;

  const open = async (hotelId: string, path = "/") => {
    if (hotelId !== currentId) await switchHotel(hotelId);
    window.location.assign(path);
  };

  return (
    <>
      <PageHeader
        title="All properties"
        description="Every property you own, live. Open one to manage it."
        actions={
          <Link href="/properties/new" className="inline-flex h-10 items-center rounded-[10px] bg-brand px-4 text-sm font-medium text-on-brand hover:opacity-90">
            Add a property
          </Link>
        }
      />
      {q.isLoading ? <Skeleton className="h-64" /> : null}
      {q.error ? <ErrorNotice error={q.error} /> : null}
      {q.data ? (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label="Properties" value={q.data.totals.properties} hint={`${q.data.totals.rooms} rooms`} />
            <StatTile
              label="Occupancy tonight"
              value={`${(q.data.totals.occupancy_bp / 100).toFixed(0)}%`}
              hint={`${q.data.totals.occupied} of ${q.data.totals.rooms} rooms`}
            />
            <StatTile label="Guests in house" value={q.data.totals.in_house} hint={`${q.data.totals.open_orders} open orders`} />
            <StatTile
              label="Revenue this month"
              value={q.data.totals.revenue.map((r) => formatMoney(r.month)).join(" · ") || "–"}
              hint={q.data.totals.revenue.map((r) => `${formatMoney(r.today)} today`).join(" · ")}
              tone="good"
            />
          </div>
          {q.data.data.length === 0 ? (
            <EmptyState title="No properties" />
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {q.data.data.map((h) => {
                const status = STATUS[h.status] ?? { label: h.status, tone: "neutral" as const };
                return (
                  <Card key={h.hotel_id} className="flex flex-col p-5">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <h2 className="truncate font-display text-lg font-semibold text-ink">{h.name}</h2>
                        <p className="mt-0.5 text-sm text-muted">
                          {propertyTypeLabel(h.property_type)} · {[h.city, h.province, h.country].filter(Boolean).join(", ")}
                        </p>
                        <p className="mt-0.5 font-mono text-xs text-muted">{h.code}</p>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <Badge tone={status.tone}>{status.label}</Badge>
                        {h.hotel_id === currentId ? <Badge tone="info">Open now</Badge> : null}
                      </div>
                    </div>
                    <dl className="mt-4 grid grid-cols-3 gap-3 text-sm">
                      <div>
                        <dt className="text-xs text-muted">Occupancy</dt>
                        <dd className="font-semibold tabular-nums">
                          {(h.occupancy_bp / 100).toFixed(0)}% <span className="font-normal text-muted">({h.occupied}/{h.rooms})</span>
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-muted">In house · arriving</dt>
                        <dd className="font-semibold tabular-nums">
                          {h.in_house} · {h.arrivals_today}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-muted">Open orders</dt>
                        <dd className="font-semibold tabular-nums">{h.open_orders}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-muted">Revenue today</dt>
                        <dd className="font-semibold tabular-nums">{formatMoney(h.revenue_today)}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-muted">This month</dt>
                        <dd className="font-semibold tabular-nums">{formatMoney(h.revenue_month)}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-muted">Staff</dt>
                        <dd className="font-semibold tabular-nums">{h.staff}</dd>
                      </div>
                    </dl>
                    <p className="mt-4 text-xs text-muted">{planLabel(h.subscription_status, h.plan_name, h.trial_ends_on)}</p>
                    <div className="mt-4 flex flex-wrap gap-2 border-t border-line pt-4">
                      <Button size="sm" onClick={() => void open(h.hotel_id)}>
                        {h.hotel_id === currentId ? "Go to today" : "Open"}
                      </Button>
                      <Button size="sm" variant="secondary" onClick={() => void open(h.hotel_id, "/reports")}>
                        Reports
                      </Button>
                      {!h.subscription_status ? (
                        <Button size="sm" variant="secondary" onClick={() => void open(h.hotel_id, "/settings?tab=plan")}>
                          Choose a plan
                        </Button>
                      ) : null}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </>
      ) : null}
    </>
  );
}
