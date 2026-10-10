"use client";

import { currencySymbol, formatDate, formatMoney, ok, parseAmount } from "@diyneco/api-client";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  Dialog,
  EmptyState,
  ErrorNotice,
  Field,
  Input,
  PageHeader,
  Select,
  Skeleton,
  StatTile,
  Table,
  Td,
  Textarea,
  Th,
  useToast,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { label, useAction } from "./common";
import { useSession } from "./session";

function useCurrencies() {
  const { api } = useSession();
  return useQuery({ queryKey: ["currencies"], queryFn: () => ok(api.GET("/api/v1/currencies")), staleTime: Infinity });
}

// --- Overview ------------------------------------------------------------------------------

export function Overview() {
  const { api } = useSession();
  const metrics = useQuery({ queryKey: ["metrics"], queryFn: () => ok(api.GET("/api/v1/admin/metrics")), refetchInterval: 60_000 });
  const analytics = useQuery({
    queryKey: ["analytics"],
    queryFn: () => ok(api.GET("/api/v1/admin/analytics", { params: { query: { days: 30 } } })),
  });
  const m = metrics.data;
  const days = analytics.data?.days ?? [];
  const max = Math.max(1, ...days.map((d) => d.orders));
  return (
    <>
      <PageHeader title="Overview" description={m ? `As of ${new Date(m.as_of).toLocaleTimeString("en-ZA")}` : undefined} />
      {!m ? (
        <Skeleton className="h-32" />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatTile label="Hotels" value={m.hotels} hint={`${m.active_hotels} active · ${m.pending_hotels} waiting · ${m.suspended_hotels} suspended`} />
            <StatTile label="Rooms" value={m.rooms.toLocaleString()} hint={`${m.active_stays} guests in house`} />
            <StatTile label="Devices online" value={m.connected_devices} />
            <StatTile label="Orders" value={m.orders_today} hint={`${m.orders_this_month} this month`} />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
            {m.mrr.length ? (
              m.mrr.map((x) => <StatTile key={x.currency} label={`MRR · ${x.currency}`} value={formatMoney(x)} />)
            ) : (
              <StatTile label="MRR" value="–" hint="No paying hotels yet" />
            )}
            <StatTile label="Active subscriptions" value={m.active_subscriptions} />
            <StatTile
              label="Churn this month"
              value={`${(m.churn_bp / 100).toFixed(1)}%`}
              hint={`${m.cancelled_this_month} cancelled`}
              tone={m.churn_bp > 300 ? "warn" : "neutral"}
            />
          </div>
        </>
      )}
      <Card className="mt-6">
        <CardHeader title="Orders per day" description="Last 30 days, all hotels" />
        <div className="flex h-40 items-end gap-1 px-5 pb-5" role="img" aria-label="Orders per day for the last 30 days">
          {days.map((d) => (
            <div key={d.day} className="flex-1 rounded-t bg-blue" style={{ height: `${(d.orders / max) * 100}%` }} title={`${d.day}: ${d.orders} orders, ${d.checkins} check-ins, ${d.new_hotels} new hotels`} />
          ))}
        </div>
      </Card>
    </>
  );
}

// --- Hotels --------------------------------------------------------------------------------

export function Hotels() {
  const { api, can } = useSession();
  const [open, setOpen] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const hotels = useQuery({ queryKey: ["hotels"], queryFn: () => ok(api.GET("/api/v1/admin/hotels")) });
  const approve = useAction(
    (id: string) => ok(api.POST("/api/v1/admin/hotels/{hotel_id}/approve", { params: { path: { hotel_id: id } } })),
    { success: "Approved. The owner was emailed." },
  );
  const list = (hotels.data?.data ?? []).filter((h) => !q || h.name.toLowerCase().includes(q.toLowerCase()));
  const selected = hotels.data?.data.find((h) => h.id === open);
  return (
    <>
      <PageHeader title="Hotels" description="Counts only: guest records are never visible to Diyneco staff." />
      <Input type="search" placeholder="Search hotels" className="mb-4 max-w-sm" value={q} onChange={(e) => setQ(e.target.value)} />
      {approve.error ? <ErrorNotice error={approve.error} className="mb-4" /> : null}
      <Card>
        {hotels.isLoading ? (
          <Skeleton className="m-5 h-10" />
        ) : list.length === 0 ? (
          <EmptyState title="No hotels" />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Hotel</Th>
                <Th>Status</Th>
                <Th>Plan</Th>
                <Th className="text-right">Rooms</Th>
                <Th className="text-right">Devices</Th>
                <Th>Last activity</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {list.map((h) => (
                <tr key={h.id} className="hover:bg-surface-2">
                  <Td>
                    <p className="font-medium">{h.name}</p>
                    <p className="text-xs text-muted">Since {formatDate(h.created_at)}</p>
                  </Td>
                  <Td>
                    <Badge tone={h.status === "active" ? "good" : h.status === "pending_approval" ? "warn" : "crit"}>{label(h.status)}</Badge>
                  </Td>
                  <Td>{h.plan ?? "–"}</Td>
                  <Td className="text-right">{h.counts.rooms}</Td>
                  <Td className="text-right">
                    {h.counts.connected_devices}/{h.counts.devices}
                  </Td>
                  <Td className="text-muted">{h.last_activity ? formatDate(h.last_activity) : "–"}</Td>
                  <Td className="whitespace-nowrap text-right">
                    {h.status === "pending_approval" && can("platform.tenants.manage") ? (
                      <Button size="sm" loading={approve.isPending} onClick={() => approve.mutate(h.id)}>
                        Approve
                      </Button>
                    ) : null}{" "}
                    <Button size="sm" variant="secondary" onClick={() => setOpen(h.id)}>
                      Manage
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
      {selected ? <HotelDialog hotel={selected} onClose={() => setOpen(null)} /> : null}
    </>
  );
}

function HotelDialog({ hotel, onClose }: { hotel: { id: string; name: string; status: string }; onClose: () => void }) {
  const { api, can } = useSession();
  const toast = useToast();
  const [reason, setReason] = useState("");
  const [ticket, setTicket] = useState("");
  const [minutes, setMinutes] = useState("30");
  const [planId, setPlanId] = useState("");
  const [status, setStatus] = useState<"trialing" | "active" | "past_due" | "cancelled">("active");
  const [startsOn, setStartsOn] = useState(new Date().toISOString().slice(0, 10));
  const [renewsOn, setRenewsOn] = useState("");
  const plans = useQuery({
    queryKey: ["plans"],
    queryFn: () => ok(api.GET("/api/v1/admin/plans")),
    enabled: can("platform.billing.manage"),
  });
  const id = { params: { path: { hotel_id: hotel.id } } };
  const suspend = useAction(() => ok(api.POST("/api/v1/admin/hotels/{hotel_id}/suspend", { ...id, body: { reason } })), {
    success: "Hotel suspended. Tablets show a paused screen.",
    onDone: onClose,
  });
  const reactivate = useAction(() => ok(api.POST("/api/v1/admin/hotels/{hotel_id}/reactivate", id)), {
    success: "Hotel reactivated.",
    onDone: onClose,
  });
  const subscribe = useAction(
    () =>
      ok(
        api.PUT("/api/v1/admin/hotels/{hotel_id}/subscription", {
          ...id,
          body: { plan_id: planId, status, starts_on: startsOn, renews_on: renewsOn || null },
        }),
      ),
    { success: "Subscription saved.", onDone: onClose },
  );
  const support = useAction(
    () =>
      ok(
        api.POST("/api/v1/admin/hotels/{hotel_id}/support-access", {
          ...id,
          body: { ticket_reference: ticket.trim(), minutes: Number(minutes), reason: reason.trim() || null },
        }),
      ),
    {
      onDone: (r) => {
        void navigator.clipboard?.writeText(r.access_token);
        toast("info", "Read-only support token copied. The hotel's owners were told.");
        onClose();
      },
    },
  );
  const error = suspend.error ?? reactivate.error ?? subscribe.error ?? support.error;
  return (
    <Dialog open onClose={onClose} size="lg" title={hotel.name} description={`Status: ${label(hotel.status)}`}>
      <div className="flex flex-col gap-6 text-sm">
        {can("platform.billing.manage") ? (
          <section className="grid gap-3 sm:grid-cols-2">
            <h3 className="font-display font-semibold sm:col-span-2">Subscription</h3>
            <Field label="Plan">
              {(p) => (
                <Select {...p} value={planId} onChange={(e) => setPlanId(e.target.value)}>
                  <option value="">Choose a plan</option>
                  {plans.data?.data.map((pl) => (
                    <option key={pl.id} value={pl.id}>
                      {pl.name} · {formatMoney(pl.monthly_price)} a month
                    </option>
                  ))}
                </Select>
              )}
            </Field>
            <Field label="Status">
              {(p) => (
                <Select {...p} value={status} onChange={(e) => setStatus(e.target.value as typeof status)}>
                  <option value="trialing">Trial</option>
                  <option value="active">Active</option>
                  <option value="past_due">Past due</option>
                  <option value="cancelled">Cancelled</option>
                </Select>
              )}
            </Field>
            <Field label="Starts">{(p) => <Input {...p} type="date" value={startsOn} onChange={(e) => setStartsOn(e.target.value)} />}</Field>
            <Field label="Renews">{(p) => <Input {...p} type="date" value={renewsOn} onChange={(e) => setRenewsOn(e.target.value)} />}</Field>
            <div className="sm:col-span-2">
              <Button disabled={!planId} loading={subscribe.isPending} onClick={() => subscribe.mutate(undefined)}>
                Save subscription
              </Button>
            </div>
          </section>
        ) : null}
        {can("platform.tenants.manage") ? (
          <section className="flex flex-col gap-3">
            <h3 className="font-display font-semibold">Account</h3>
            {hotel.status === "suspended" ? (
              <Button variant="success" loading={reactivate.isPending} onClick={() => reactivate.mutate(undefined)}>
                Reactivate
              </Button>
            ) : hotel.status === "active" ? (
              <>
                <Field label="Reason for suspension">{(p) => <Textarea {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}</Field>
                <Button variant="danger" disabled={reason.trim().length < 3} loading={suspend.isPending} onClick={() => suspend.mutate(undefined)}>
                  Suspend hotel
                </Button>
              </>
            ) : null}
          </section>
        ) : null}
        {can("platform.support") ? (
          <section className="grid gap-3 sm:grid-cols-2">
            <h3 className="font-display font-semibold sm:col-span-2">Support access</h3>
            <p className="text-muted sm:col-span-2">Read-only, no guest data, at most 60 minutes. The hotel sees it and can end it.</p>
            <Field label="Ticket">{(p) => <Input {...p} value={ticket} onChange={(e) => setTicket(e.target.value)} />}</Field>
            <Field label="Minutes">{(p) => <Input {...p} type="number" min={1} max={60} value={minutes} onChange={(e) => setMinutes(e.target.value)} />}</Field>
            <div className="sm:col-span-2">
              <Button variant="secondary" disabled={ticket.trim().length < 3} loading={support.isPending} onClick={() => support.mutate(undefined)}>
                Open support access
              </Button>
            </div>
          </section>
        ) : null}
        {error ? <ErrorNotice error={error} /> : null}
      </div>
    </Dialog>
  );
}

// --- Plans ---------------------------------------------------------------------------------

export function Plans() {
  const { api } = useSession();
  const plans = useQuery({ queryKey: ["plans"], queryFn: () => ok(api.GET("/api/v1/admin/plans")) });
  const [editing, setEditing] = useState<string | "new" | null>(null);
  return (
    <>
      <PageHeader
        title="Plans & billing"
        description="Each plan bills in the currency you choose for it. Prices are data, never code."
        actions={<Button onClick={() => setEditing("new")}>New plan</Button>}
      />
      <Card>
        <Table>
          <thead>
            <tr>
              <Th>Plan</Th>
              <Th className="text-right">Monthly price</Th>
              <Th>Currency</Th>
              <Th>Limits</Th>
              <Th>Status</Th>
              <Th />
            </tr>
          </thead>
          <tbody>
            {plans.data?.data.map((p) => (
              <tr key={p.id}>
                <Td>
                  <p className="font-medium">{p.name}</p>
                  <p className="font-mono text-xs text-muted">{p.code}</p>
                </Td>
                <Td className="text-right tabular-nums">{formatMoney(p.monthly_price)}</Td>
                <Td>{p.monthly_price.currency}</Td>
                <Td className="text-xs text-muted">
                  {Object.entries(p.limits)
                    .map(([k, v]) => `${v} ${k.replace("_", " ")}`)
                    .join(" · ")}
                </Td>
                <Td>
                  <Badge tone={p.is_active ? "good" : "neutral"}>{p.is_active ? "Offered" : "Retired"}</Badge>
                  {p.features.placeholder ? <Badge tone="warn" className="ml-1">Placeholder price</Badge> : null}
                </Td>
                <Td className="text-right">
                  <Button size="sm" variant="secondary" onClick={() => setEditing(p.id)}>
                    Edit
                  </Button>
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
      {editing ? (
        <PlanDialog plan={editing === "new" ? null : (plans.data?.data.find((p) => p.id === editing) ?? null)} onClose={() => setEditing(null)} />
      ) : null}
    </>
  );
}

function PlanDialog({
  plan,
  onClose,
}: {
  plan: { id: string; code: string; name: string; monthly_price: { amount_minor: number; currency: string }; limits: Record<string, unknown>; is_active: boolean } | null;
  onClose: () => void;
}) {
  const { api } = useSession();
  const currencies = useCurrencies();
  const [code, setCode] = useState("");
  const [name, setName] = useState(plan?.name ?? "");
  const [price, setPrice] = useState(plan ? (plan.monthly_price.amount_minor / 100).toFixed(2) : "");
  const [currency, setCurrency] = useState(plan?.monthly_price.currency ?? "");
  const [limits, setLimits] = useState<Record<string, string>>(
    Object.fromEntries(["rooms", "devices", "staff", "api_keys"].map((k) => [k, String(plan?.limits[k] ?? "")])),
  );
  const [active, setActive] = useState(plan?.is_active ?? true);
  const minor = parseAmount(price);
  const limitValues = Object.fromEntries(Object.entries(limits).filter(([, v]) => v !== "").map(([k, v]) => [k, Number(v)]));
  const save = useAction(
    async () =>
      plan
        ? ok(
            api.PATCH("/api/v1/admin/plans/{plan_id}", {
              params: { path: { plan_id: plan.id } },
              body: { name, monthly_price: { amount_minor: minor ?? 0, currency }, limits: limitValues, is_active: active },
            }),
          )
        : ok(
            api.POST("/api/v1/admin/plans", {
              body: { code, name, monthly_price: { amount_minor: minor ?? 0, currency }, limits: limitValues, features: {} },
            }),
          ),
    { success: "Plan saved.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title={plan ? `Edit ${plan.name}` : "New plan"}
      description="Hotels on this plan are billed in its currency from their next period."
      footer={
        <Button disabled={!name || minor === null || !currency || (!plan && !/^[a-z][a-z0-9_]{1,40}$/.test(code))} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Save plan
        </Button>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {!plan ? (
          <Field label="Code" hint="Lowercase, e.g. boutique">
            {(p) => <Input {...p} value={code} onChange={(e) => setCode(e.target.value)} />}
          </Field>
        ) : null}
        <Field label="Name">{(p) => <Input {...p} value={name} onChange={(e) => setName(e.target.value)} />}</Field>
        <Field label="Billing currency">
          {(p) => (
            <Select {...p} value={currency} onChange={(e) => setCurrency(e.target.value)}>
              <option value="">Choose a currency</option>
              {currencies.data?.data.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} · {c.name}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label={`Monthly price${currency ? ` (${currencySymbol(currency)})` : ""}`}>
          {(p) => <Input {...p} inputMode="decimal" value={price} onChange={(e) => setPrice(e.target.value)} />}
        </Field>
        {Object.keys(limits).map((k) => (
          <Field key={k} label={`Limit: ${k.replace("_", " ")}`} hint="Empty means no limit">
            {(p) => <Input {...p} type="number" min={0} value={limits[k]} onChange={(e) => setLimits({ ...limits, [k]: e.target.value })} />}
          </Field>
        ))}
        {plan ? (
          <label className="flex items-center gap-2 text-sm sm:col-span-2">
            <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
            Offered to hotels
          </label>
        ) : null}
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

// --- Flags and health ----------------------------------------------------------------------

export function Flags() {
  const { api } = useSession();
  const flags = useQuery({ queryKey: ["flags"], queryFn: () => ok(api.GET("/api/v1/admin/feature-flags")) });
  const hotels = useQuery({ queryKey: ["hotels"], queryFn: () => ok(api.GET("/api/v1/admin/hotels")) });
  const [key, setKey] = useState("");
  const [hotelId, setHotelId] = useState("");
  const set = useAction(
    (change: { key: string; hotel_id: string | null; enabled: boolean }) =>
      ok(api.PATCH("/api/v1/admin/feature-flags", { body: { changes: [change] } })),
    { success: "Flag saved." },
  );
  const name = (id: string | null) => (id ? (hotels.data?.data.find((h) => h.id === id)?.name ?? id) : "Everyone");
  return (
    <>
      <PageHeader title="Feature flags" description="A hotel's own setting overrides the global one." />
      <Card className="mb-6 p-5">
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="Flag">{(p) => <Input {...p} placeholder="beta.new_menu" value={key} onChange={(e) => setKey(e.target.value.trim())} />}</Field>
          <Field label="For">
            {(p) => (
              <Select {...p} value={hotelId} onChange={(e) => setHotelId(e.target.value)}>
                <option value="">Everyone</option>
                {hotels.data?.data.map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.name}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <div className="flex items-end gap-2">
            <Button disabled={!key} onClick={() => set.mutate({ key, hotel_id: hotelId || null, enabled: true })}>
              Turn on
            </Button>
            <Button variant="secondary" disabled={!key} onClick={() => set.mutate({ key, hotel_id: hotelId || null, enabled: false })}>
              Turn off
            </Button>
          </div>
        </div>
        {set.error ? <ErrorNotice error={set.error} className="mt-3" /> : null}
      </Card>
      <Card>
        {flags.data?.data.length ? (
          <Table>
            <tbody>
              {flags.data.data.map((f) => (
                <tr key={`${f.key}-${f.hotel_id}`}>
                  <Td className="font-mono text-sm">{f.key}</Td>
                  <Td>{name(f.hotel_id)}</Td>
                  <Td>
                    <Badge tone={f.enabled ? "good" : "neutral"}>{f.enabled ? "On" : "Off"}</Badge>
                  </Td>
                  <Td className="text-right">
                    <Button size="sm" variant="secondary" onClick={() => set.mutate({ key: f.key, hotel_id: f.hotel_id, enabled: !f.enabled })}>
                      {f.enabled ? "Turn off" : "Turn on"}
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <EmptyState title="No flags yet" />
        )}
      </Card>
    </>
  );
}

export function Health() {
  const { api } = useSession();
  const health = useQuery({ queryKey: ["health"], queryFn: () => ok(api.GET("/api/v1/admin/health")), refetchInterval: 15_000 });
  const h = health.data;
  return (
    <>
      <PageHeader title="Health" description="Refreshes every 15 seconds." />
      {!h ? (
        <Skeleton className="h-32" />
      ) : (
        <>
          <Badge tone={h.status === "ok" ? "good" : h.status === "degraded" ? "warn" : "crit"} className="mb-4 text-sm">
            Overall: {label(h.status)}
          </Badge>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(h.checks).map(([name, c]) => (
              <Card key={name} className="p-4">
                <div className="flex items-center justify-between">
                  <p className="font-display font-semibold">{label(name)}</p>
                  <Badge tone={c.status === "ok" ? "good" : c.status === "development" ? "info" : "warn"}>{label(c.status)}</Badge>
                </div>
                <dl className="mt-2 space-y-1 text-xs text-muted">
                  {Object.entries(c)
                    .filter(([k]) => k !== "status")
                    .map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <dt>{label(k)}</dt>
                        <dd>{String(v)}</dd>
                      </div>
                    ))}
                </dl>
              </Card>
            ))}
          </div>
        </>
      )}
    </>
  );
}
