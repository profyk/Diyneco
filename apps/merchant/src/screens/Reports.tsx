"use client";

import { currencySymbol, formatDate, formatMoney, type Money, ok, parseAmount } from "@diyneco/api-client";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  cn,
  EmptyState,
  ErrorNotice,
  Field,
  Input,
  PageHeader,
  Skeleton,
  StatTile,
  Table,
  Td,
  Textarea,
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { isoDay, label, useAction } from "../common";
import { useCurrency, useSession } from "../session";

type Tab = "revenue" | "payments" | "operations" | "occupancy" | "close" | "receivable";

const TABS: { key: Tab; title: string; perm: string }[] = [
  { key: "revenue", title: "Revenue", perm: "reports.finance" },
  { key: "payments", title: "Payments & tips", perm: "reports.finance" },
  { key: "close", title: "Daily close", perm: "reports.finance" },
  { key: "receivable", title: "Open balances", perm: "reports.finance" },
  { key: "operations", title: "Orders & kitchen", perm: "reports.read" },
  { key: "occupancy", title: "Occupancy", perm: "reports.read" },
];

function minutes(seconds: number): string {
  return `${Math.round(seconds / 60)} min`;
}

export function Reports() {
  const { can } = useSession();
  const tabs = TABS.filter((t) => can(t.perm));
  const [tab, setTab] = useState<Tab>(tabs[0]?.key ?? "operations");
  const [from, setFrom] = useState(isoDay(-6));
  const [to, setTo] = useState(isoDay());

  return (
    <>
      <PageHeader
        title="Reports"
        description="Computed from the bills themselves, so every figure reconciles to the cent."
        actions={
          tab !== "close" && tab !== "receivable" ? (
            <div className="flex items-center gap-2">
              <Input type="date" aria-label="From" value={from} onChange={(e) => setFrom(e.target.value)} className="w-40" />
              <span className="text-muted">to</span>
              <Input type="date" aria-label="To" value={to} onChange={(e) => setTo(e.target.value)} className="w-40" />
            </div>
          ) : null
        }
      />
      <div role="tablist" className="mb-5 flex flex-wrap gap-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "rounded-full px-3 py-1.5 text-sm font-medium",
              tab === t.key ? "bg-brand text-on-brand" : "bg-surface text-ink hover:bg-surface-2",
            )}
          >
            {t.title}
          </button>
        ))}
      </div>
      {tab === "revenue" ? <Revenue from={from} to={to} /> : null}
      {tab === "payments" ? <PaymentsReport from={from} to={to} /> : null}
      {tab === "operations" ? <Operations from={from} to={to} /> : null}
      {tab === "occupancy" ? <Occupancy from={from} to={to} /> : null}
      {tab === "close" ? <DailyClose /> : null}
      {tab === "receivable" ? <Receivable /> : null}
    </>
  );
}

function Revenue({ from, to }: { from: string; to: string }) {
  const { api } = useSession();
  const r = useQuery({
    queryKey: ["reports", "revenue", from, to],
    queryFn: () => ok(api.GET("/api/v1/reports/revenue", { params: { query: { from, to } } })),
  });
  if (r.isLoading) return <Skeleton className="h-40" />;
  if (r.error || !r.data) return <ErrorNotice error={r.error} />;
  const { total, days } = r.data;
  const max = Math.max(1, ...days.map((d) => d.revenue.amount_minor));
  const csv = () => {
    const rows = [
      ["date", "accommodation", "fnb", "other", "revenue", "vat_included", "discounts", "adjustments", "tips"],
      ...days.map((d) =>
        [d.date, d.accommodation, d.fnb, d.other, d.revenue, d.vat_included, d.discounts, d.adjustments, d.tips].map((v) =>
          typeof v === "object" && v ? (v.amount_minor / 100).toFixed(2) : String(v),
        ),
      ),
    ];
    const blob = new Blob([rows.map((row) => row.join(",")).join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `revenue-${from}-${to}.csv`;
    a.click();
  };
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile label="Revenue (incl. VAT)" value={formatMoney(total.revenue)} hint={`${formatMoney(total.revenue_excluding_vat)} excl. VAT`} />
        <StatTile label="Accommodation" value={formatMoney(total.accommodation)} />
        <StatTile label="Food & beverage" value={formatMoney(total.fnb)} />
        <StatTile label="Tips for staff" value={formatMoney(total.tips)} hint="Not hotel revenue" />
      </div>
      <Card>
        <CardHeader
          title="By day"
          description={`Discounts ${formatMoney(total.discounts)} · adjustments ${formatMoney(total.adjustments)} · reversals ${formatMoney(total.reversals)}`}
          actions={
            <Button size="sm" variant="secondary" onClick={csv}>
              Download CSV
            </Button>
          }
        />
        <Table>
          <thead>
            <tr>
              <Th>Day</Th>
              <Th className="w-1/3" />
              <Th className="text-right">Rooms</Th>
              <Th className="text-right">F&amp;B</Th>
              <Th className="text-right">Other</Th>
              <Th className="text-right">Revenue</Th>
            </tr>
          </thead>
          <tbody>
            {days.map((d) => (
              <tr key={d.date}>
                <Td className="whitespace-nowrap">{formatDate(d.date)}</Td>
                <Td>
                  <div className="h-2 rounded-full bg-surface-2" aria-hidden>
                    <div className="h-2 rounded-full bg-blue" style={{ width: `${(d.revenue.amount_minor / max) * 100}%` }} />
                  </div>
                </Td>
                <Td className="text-right tabular-nums">{formatMoney(d.accommodation)}</Td>
                <Td className="text-right tabular-nums">{formatMoney(d.fnb)}</Td>
                <Td className="text-right tabular-nums">{formatMoney(d.other)}</Td>
                <Td className="text-right font-medium tabular-nums">{formatMoney(d.revenue)}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
    </div>
  );
}

function PaymentsReport({ from, to }: { from: string; to: string }) {
  const { api } = useSession();
  const r = useQuery({
    queryKey: ["reports", "payments", from, to],
    queryFn: () => ok(api.GET("/api/v1/reports/payments", { params: { query: { from, to } } })),
  });
  if (r.isLoading) return <Skeleton className="h-40" />;
  if (!r.data) return <ErrorNotice error={r.error} />;
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader title="By method" description={`${r.data.total.count} payments · ${formatMoney(r.data.total.amount)}`} />
        <Table>
          <tbody>
            {r.data.by_method.map((m) => (
              <tr key={m.method}>
                <Td>{label(m.method)}</Td>
                <Td className="text-right">{m.count}</Td>
                <Td className="text-right tabular-nums">{formatMoney(m.amount)}</Td>
                <Td className="text-right tabular-nums text-teal">{formatMoney(m.tips)}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
      <Card>
        <CardHeader title="By staff member" description="Tips belong to the person who recorded them." />
        <Table>
          <tbody>
            {r.data.by_staff.map((s) => (
              <tr key={s.staff_id ?? s.name}>
                <Td>
                  {s.name}
                  {s.late ? <Badge tone="warn" className="ml-2">{s.late} late</Badge> : null}
                </Td>
                <Td className="text-right">{s.count}</Td>
                <Td className="text-right tabular-nums">{formatMoney(s.amount)}</Td>
                <Td className="text-right tabular-nums text-teal">{formatMoney(s.tips)}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
    </div>
  );
}

function Operations({ from, to }: { from: string; to: string }) {
  const { api } = useSession();
  const q = { params: { query: { from, to } } };
  const orders = useQuery({ queryKey: ["reports", "orders", from, to], queryFn: () => ok(api.GET("/api/v1/reports/orders", q)) });
  const items = useQuery({ queryKey: ["reports", "items", from, to], queryFn: () => ok(api.GET("/api/v1/reports/items", q)) });
  const kitchen = useQuery({ queryKey: ["reports", "kitchen", from, to], queryFn: () => ok(api.GET("/api/v1/reports/kitchen", q)) });
  const rs = useQuery({ queryKey: ["reports", "rs", from, to], queryFn: () => ok(api.GET("/api/v1/reports/room-service", q)) });
  const o = orders.data;
  return (
    <div className="flex flex-col gap-6">
      {o ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatTile label="Orders" value={o.orders} />
          <StatTile label="Average order" value={formatMoney(o.average_order_value)} />
          <StatTile label="Cancelled" value={o.cancelled} tone={o.cancelled ? "warn" : "neutral"} />
          <StatTile label="Declined" value={o.declined} />
        </div>
      ) : (
        <Skeleton className="h-20" />
      )}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Top items" />
          {items.data?.items.length ? (
            <Table>
              <tbody>
                {items.data.items.map((i) => (
                  <tr key={i.menu_item_id ?? i.name}>
                    <Td>{i.name}</Td>
                    <Td className="text-right">{i.quantity}</Td>
                    <Td className="text-right tabular-nums">{formatMoney(i.revenue)}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <EmptyState title="No orders in this period" />
          )}
        </Card>
        <Card>
          <CardHeader title="Kitchen speed" description="Accepted to ready, per station" />
          {kitchen.data?.stations.length ? (
            <Table>
              <thead>
                <tr>
                  <Th>Station</Th>
                  <Th className="text-right">Median</Th>
                  <Th className="text-right">90% within</Th>
                </tr>
              </thead>
              <tbody>
                {kitchen.data.stations.map((s) => (
                  <tr key={s.station_id}>
                    <Td>{s.name}</Td>
                    <Td className="text-right">{minutes(s.median_seconds)}</Td>
                    <Td className="text-right">{minutes(s.p90_seconds)}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <EmptyState title="No completed items yet" />
          )}
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader title="Room-service speed" description="Ready in the kitchen to delivered, per staff member" />
          {rs.data?.staff.length ? (
            <Table>
              <tbody>
                {rs.data.staff.map((s) => (
                  <tr key={s.staff_id ?? s.name}>
                    <Td>{s.name ?? "Unknown"}</Td>
                    <Td className="text-right">{s.deliveries} deliveries</Td>
                    <Td className="text-right">{minutes(s.median_seconds)} median</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <EmptyState title="No deliveries yet" />
          )}
        </Card>
      </div>
    </div>
  );
}

function Occupancy({ from, to }: { from: string; to: string }) {
  const { api } = useSession();
  const r = useQuery({
    queryKey: ["reports", "occupancy", from, to],
    queryFn: () => ok(api.GET("/api/v1/reports/occupancy", { params: { query: { from, to } } })),
  });
  if (!r.data) return <Skeleton className="h-40" />;
  return (
    <Card>
      <CardHeader title={`Occupancy ${(r.data.total.occupancy_bp / 100).toFixed(1)}%`} description={`${r.data.total.occupied} room-nights sold`} />
      <Table>
        <thead>
          <tr>
            <Th>Night</Th>
            <Th className="text-right">Occupied</Th>
            <Th className="text-right">Available</Th>
            <Th className="text-right">Out of service</Th>
            <Th className="text-right">Occupancy</Th>
          </tr>
        </thead>
        <tbody>
          {r.data.nights.map((n) => (
            <tr key={n.date}>
              <Td>{formatDate(n.date)}</Td>
              <Td className="text-right">{n.occupied}</Td>
              <Td className="text-right">{n.available}</Td>
              <Td className="text-right">{n.out_of_service}</Td>
              <Td className="text-right">{(n.occupancy_bp / 100).toFixed(0)}%</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
}

function DailyClose() {
  const { api } = useSession();
  const currency = useCurrency();
  const [day, setDay] = useState(isoDay(-1));
  const [batch, setBatch] = useState("");
  const [cash, setCash] = useState("");
  const [notes, setNotes] = useState("");
  const r = useQuery({
    queryKey: ["reports", "close", day],
    queryFn: () => ok(api.GET("/api/v1/reports/daily-close", { params: { query: { date: day } } })),
  });
  const money = (t: string) => {
    const m = parseAmount(t);
    return m === null ? null : { amount_minor: m, currency };
  };
  const save = useAction(
    (review: boolean) =>
      ok(
        api.PUT("/api/v1/reports/daily-close/{day}", {
          params: { path: { day } },
          body: { terminal_batch_total: money(batch), cash_counted: money(cash), notes: notes.trim() || null, mark_reviewed: review },
        }),
      ),
    { success: (d) => (d.reviewed_at ? "Day reviewed." : "Saved.") },
  );
  const d = r.data;
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-end gap-3">
        <Field label="Day">{(p) => <Input {...p} type="date" value={day} onChange={(e) => setDay(e.target.value)} className="w-44" />}</Field>
        {d?.reviewed_at ? <Badge tone="good">Reviewed {formatDate(d.reviewed_at)}</Badge> : null}
        {d?.flags.map((f) => (
          <Badge key={f} tone="warn">
            {label(f)}
          </Badge>
        ))}
      </div>
      {!d ? (
        <Skeleton className="h-40" />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatTile label="Revenue" value={formatMoney(d.revenue.revenue)} />
            <StatTile label="Tips" value={formatMoney(d.revenue.tips)} />
            <StatTile
              label="Card recorded"
              value={formatMoney(d.card.recorded as Money)}
              hint={d.card.terminal_batch_total ? `Machine batch ${formatMoney(d.card.terminal_batch_total as Money)}` : "Enter the machine's batch total"}
            />
            <StatTile
              label="Cash recorded"
              value={formatMoney(d.cash.recorded as Money)}
              hint={d.cash.counted ? `Counted ${formatMoney(d.cash.counted as Money)}` : undefined}
            />
          </div>
          <Card className="p-5">
            <h2 className="font-display text-base font-semibold">Finance check</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label={`Card machine batch total (${currencySymbol(currency)})`}>{(p) => <Input {...p} inputMode="decimal" value={batch} onChange={(e) => setBatch(e.target.value)} />}</Field>
              <Field label={`Cash counted (${currencySymbol(currency)})`}>{(p) => <Input {...p} inputMode="decimal" value={cash} onChange={(e) => setCash(e.target.value)} />}</Field>
              <Field label="Notes" className="sm:col-span-2">{(p) => <Textarea {...p} value={notes} onChange={(e) => setNotes(e.target.value)} />}</Field>
            </div>
            {save.error ? <ErrorNotice error={save.error} className="mt-3" /> : null}
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="secondary" loading={save.isPending} onClick={() => save.mutate(false)}>
                Save
              </Button>
              <Button loading={save.isPending} onClick={() => save.mutate(true)}>
                Mark day reviewed
              </Button>
            </div>
          </Card>
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader title="Adjustments" />
              {d.adjustments.length ? (
                <ul className="divide-y divide-line text-sm">
                  {d.adjustments.map((a) => (
                    <li key={String(a.id)} className="px-5 py-2">
                      {formatMoney(a.original as Money)} → {formatMoney(a.new_amount as Money)} · {String(a.reason)} ({label(String(a.status))})
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState title="None" />
              )}
            </Card>
            <Card>
              <CardHeader title="Discounts" />
              {d.discounts.length ? (
                <ul className="divide-y divide-line text-sm">
                  {d.discounts.map((x) => (
                    <li key={String(x.id)} className="px-5 py-2">
                      {x.percent_bp ? `${Number(x.percent_bp) / 100}%` : formatMoney(x.amount as Money)} on {label(String(x.applies_to))} by{" "}
                      {String(x.given_by)}: {String(x.reason)}
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState title="None" />
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function Receivable() {
  const { api } = useSession();
  const r = useQuery({ queryKey: ["reports", "receivable"], queryFn: () => ok(api.GET("/api/v1/reports/open-balances")) });
  if (!r.data) return <Skeleton className="h-40" />;
  return (
    <Card>
      <CardHeader title="Open balances" description={`Guests and companies who left with a balance · total ${formatMoney(r.data.total)}`} />
      {r.data.data.length ? (
        <Table>
          <thead>
            <tr>
              <Th>Bill to</Th>
              <Th>Room</Th>
              <Th>Left</Th>
              <Th>Reason</Th>
              <Th className="text-right">Balance</Th>
            </tr>
          </thead>
          <tbody>
            {r.data.data.map((b) => (
              <tr key={b.stay_id}>
                <Td>
                  <Link className="text-blue hover:underline" href={`/stays/${b.stay_id}`}>
                    {b.bill_to}
                  </Link>
                </Td>
                <Td>{b.room}</Td>
                <Td className="text-muted">{formatDate(b.checked_out_at)}</Td>
                <Td className="text-muted">{b.override_reason}</Td>
                <Td className="text-right tabular-nums">{formatMoney(b.balance)}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      ) : (
        <EmptyState title="Nothing outstanding" />
      )}
    </Card>
  );
}
