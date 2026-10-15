"use client";

import { formatDate, formatMoney, ok } from "@diyneco/api-client";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  ErrorNotice,
  PageHeader,
  propertyTypeLabel,
  Skeleton,
  StatTile,
  Table,
  Td,
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { useAction } from "../common";
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
      <GroupBilling />
    </>
  );
}

/** Every property's open invoices and one payment for them all (D89). */
function GroupBilling() {
  const { api } = useSession();
  const q = useQuery({ queryKey: ["group-statement"], queryFn: () => ok(api.GET("/api/v1/portfolio/billing")) });
  const pay = useAction(
    (currency: string) => ok(api.POST("/api/v1/portfolio/payments", { body: { currency } })),
    { onDone: (g) => window.location.assign(g.checkout_url ?? "/properties") },
  );
  if (!q.data) return q.error ? <ErrorNotice error={q.error} className="mt-6" /> : null;
  const s = q.data;
  const online = (s.options.online as { available?: boolean; label?: string } | undefined) ?? {};
  const eft = (s.options.eft as { available?: boolean; bank?: Record<string, string>; instructions?: string | null } | undefined) ?? {};
  return (
    <Card className="mt-8">
      <CardHeader
        title="Billing for all properties"
        description="Each property keeps its own tax invoice. Pay them together in one payment, split across the invoices."
      />
      {s.group_discount_bp > 0 ? (
        <p className="mx-5 mt-4 rounded-lg bg-good-bg px-4 py-2 text-sm text-good">
          Owners with {s.group_discount_min_properties} or more paid properties get {s.group_discount_bp / 100}% off each property&apos;s plan.
        </p>
      ) : null}
      {s.invoices.length === 0 ? (
        <EmptyState title="Nothing due" body="Every property's invoices are paid." />
      ) : (
        <>
          <Table>
            <thead>
              <tr>
                <Th>Property</Th>
                <Th>Invoice</Th>
                <Th>Due</Th>
                <Th className="text-right">Balance</Th>
              </tr>
            </thead>
            <tbody>
              {s.invoices.map((i) => (
                <tr key={i.invoice_id}>
                  <Td>{i.hotel_name}</Td>
                  <Td className="font-mono text-xs">
                    {i.number} {i.status === "overdue" ? <Badge tone="crit">Overdue</Badge> : null}
                  </Td>
                  <Td className="text-muted">{i.due_on ? formatDate(i.due_on) : "–"}</Td>
                  <Td className="text-right tabular-nums">{formatMoney(i.balance)}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
          <div className="flex flex-wrap items-center gap-3 p-5">
            {s.due.map((d) => (
              <Button key={d.currency} disabled={!online.available} loading={pay.isPending} onClick={() => pay.mutate(d.currency)}>
                Pay {formatMoney(d)} for all
              </Button>
            ))}
            {online.available ? (
              <span className="text-xs text-muted">{online.label}</span>
            ) : (
              <span className="text-sm text-muted">Online payment is not available yet; pay by bank transfer.</span>
            )}
          </div>
          {pay.error ? <ErrorNotice error={pay.error} className="mx-5 mb-4" /> : null}
          {eft.available && eft.bank ? (
            <div className="mx-5 mb-5 rounded-lg border border-line p-4 text-sm">
              <p className="font-medium text-ink">Bank transfer (EFT)</p>
              <p className="mt-1 text-muted">
                {Object.entries(eft.bank)
                  .map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`)
                  .join(" · ")}
              </p>
              <p className="mt-1 text-muted">Pay each invoice with its own number as the reference, so each property is credited.</p>
            </div>
          ) : null}
        </>
      )}
      {s.payments.length ? (
        <div className="border-t border-line p-5">
          <p className="mb-2 text-sm font-medium text-ink">Recent payments for all properties</p>
          <ul className="flex flex-col gap-1 text-sm">
            {s.payments.map((g) => (
              <li key={g.id} className="flex flex-wrap items-center gap-2">
                <span className="text-muted">{formatDate(g.created_at)}</span>
                <span className="tabular-nums">{formatMoney(g.paid ?? g.amount)}</span>
                <Badge tone={g.status === "succeeded" ? "good" : g.status === "pending" ? "info" : "crit"}>{g.status}</Badge>
                {g.test_mode ? <Badge tone="warn">Test</Badge> : null}
                {g.status === "pending" ? (
                  <Link href={`/billing/return?group=${g.id}`} className="text-blue hover:underline">
                    Check
                  </Link>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Card>
  );
}
