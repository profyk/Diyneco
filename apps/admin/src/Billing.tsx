"use client";

// Billing & Invoices (DECISIONS D79): what was collected, invoiced, owed and projected (never
// mixed), invoices and payments across hotels with filters and CSV exports, reconciliation,
// provider webhooks, the payment provider's status and the collections policy. Every figure
// comes from the API.

import { formatDate, formatMoney, formatTime, ok } from "@diyneco/api-client";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  cn,
  Dialog,
  EmptyState,
  ErrorNotice,
  Field,
  Input,
  PageHeader,
  Select,
  Skeleton,
  Table,
  Td,
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { type ReactNode, useState } from "react";

import { isoDay, label, useAction } from "./common";
import { useSession } from "./session";

type Money = { amount_minor: number; currency: string };
type Tab = "overview" | "invoices" | "payments" | "webhooks" | "settings";

export function tone(s: string): "good" | "warn" | "crit" | "info" | "neutral" {
  if (["paid", "credited", "matched", "active", "succeeded"].includes(s)) return "good";
  if (["overdue", "disputed", "suspended", "failed", "past_due"].includes(s)) return "crit";
  if (["partially_paid", "unreconciled", "pending_payment", "pending"].includes(s)) return "warn";
  return "neutral";
}

function download(name: string, body: string) {
  const url = URL.createObjectURL(new Blob([body], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export function Billing() {
  const [tab, setTab] = useState<Tab>("overview");
  const tabs: [Tab, string][] = [
    ["overview", "Overview"],
    ["invoices", "Invoices"],
    ["payments", "Payments & reconciliation"],
    ["webhooks", "Provider webhooks"],
    ["settings", "Payments & collections"],
  ];
  return (
    <>
      <PageHeader title="Billing & Invoices" description="Diyneco's subscription billing to hotels." />
      <div role="tablist" className="mb-5 flex flex-wrap gap-1">
        {tabs.map(([k, t]) => (
          <button
            key={k}
            role="tab"
            aria-selected={tab === k}
            onClick={() => setTab(k)}
            className={cn(
              "rounded-full px-3 py-1.5 text-sm font-medium",
              tab === k ? "bg-brand text-on-brand" : "bg-surface text-ink hover:bg-surface-2",
            )}
          >
            {t}
          </button>
        ))}
      </div>
      {tab === "overview" ? <Overview /> : null}
      {tab === "invoices" ? <Invoices /> : null}
      {tab === "payments" ? <Payments /> : null}
      {tab === "webhooks" ? <Webhooks /> : null}
      {tab === "settings" ? <Collections /> : null}
    </>
  );
}

function Stat({ title, value, hint }: { title: string; value: ReactNode; hint?: string }) {
  return (
    <Card className="p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-muted">{title}</p>
      <p className="mt-1 font-display text-2xl font-semibold tabular-nums">{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted">{hint}</p> : null}
    </Card>
  );
}

function Overview() {
  const { api } = useSession();
  const [from, setFrom] = useState(isoDay(-(new Date().getDate() - 1)));
  const [to, setTo] = useState(isoDay());
  const q = useQuery({
    queryKey: ["billing-summary", from, to],
    queryFn: () => ok(api.GET("/api/v1/admin/billing/summary", { params: { query: { from, to } } })),
  });
  return (
    <>
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <Field label="From">{(p) => <Input {...p} type="date" value={from} onChange={(e) => setFrom(e.target.value)} />}</Field>
        <Field label="To">{(p) => <Input {...p} type="date" value={to} onChange={(e) => setTo(e.target.value)} />}</Field>
      </div>
      {q.isError ? <ErrorNotice error={q.error} /> : null}
      {!q.data ? (
        <Skeleton className="h-60" />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat title="Active subscriptions" value={q.data.active_subscriptions} hint={`${q.data.trials} on trial`} />
            <Stat title="New in period" value={q.data.new_subscriptions} hint={`${q.data.cancelled_subscriptions} ended in period`} />
            <Stat title="Past due / suspended" value={`${q.data.past_due} / ${q.data.suspended}`} />
            <Stat title="Failed payments in period" value={q.data.failed_payments} />
          </div>
          {q.data.currencies.length ? (
            q.data.currencies.map((c) => (
              <Card key={c.currency} className="mt-6">
                <CardHeader
                  title={`${c.currency}`}
                  description="Collected is money received (less refunds). Invoiced is issued invoices less credit notes. Outstanding is what open invoices still owe. MRR and ARR are projections from agreed prices."
                />
                <div className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4">
                  <Stat title="Collected (net)" value={formatMoney(c.net_collected)} hint={`${formatMoney(c.collected)} received, ${formatMoney(c.refunded)} refunded`} />
                  <Stat title="Invoiced (net)" value={formatMoney({ ...c.invoiced, amount_minor: c.invoiced.amount_minor - c.credited.amount_minor })} hint={`${formatMoney(c.credited)} credited`} />
                  <Stat title="Outstanding now" value={formatMoney(c.outstanding)} hint={`${formatMoney(c.overdue)} overdue on ${c.overdue_invoices} invoice${c.overdue_invoices === 1 ? "" : "s"}`} />
                  <Stat title="Projected MRR" value={formatMoney(c.mrr)} hint={`ARR ${formatMoney(c.arr)}`} />
                </div>
                {c.test_collected.amount_minor ? (
                  <p className="px-5 pb-4 text-xs text-muted">
                    Test payments (sandbox, not money): {formatMoney(c.test_collected)}. Never included above.
                  </p>
                ) : null}
              </Card>
            ))
          ) : (
            <EmptyState title="No billing yet" body="Figures appear once hotels subscribe." />
          )}
          <Card className="mt-6">
            <CardHeader title="Revenue by plan" description="Current subscriptions and money collected in the period." />
            <Table>
              <thead>
                <tr>
                  <Th>Plan</Th>
                  <Th className="text-right">Subscriptions</Th>
                  <Th className="text-right">Projected MRR</Th>
                  <Th className="text-right">Collected in period</Th>
                </tr>
              </thead>
              <tbody>
                {q.data.by_plan.map((p) => (
                  <tr key={p.plan_code}>
                    <Td>{p.plan_name}</Td>
                    <Td className="text-right tabular-nums">{p.subscriptions}</Td>
                    <Td className="text-right tabular-nums">{formatMoney(p.mrr)}</Td>
                    <Td className="text-right tabular-nums">{formatMoney(p.collected)}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card>
        </>
      )}
    </>
  );
}

type InvoiceFilters = { q: string; status: string; payment: string; plan: string; from: string; to: string };

function Invoices() {
  const { api } = useSession();
  const [f, setF] = useState<InvoiceFilters>({ q: "", status: "", payment: "", plan: "", from: "", to: "" });
  const [page, setPage] = useState(0);
  const [error, setError] = useState<unknown>(null);
  const plans = useQuery({ queryKey: ["admin-plans"], queryFn: () => ok(api.GET("/api/v1/admin/plans")) });
  const query = {
    q: f.q || undefined,
    status: (f.status || undefined) as never,
    payment: (f.payment || undefined) as never,
    plan: f.plan || undefined,
    from: f.from || undefined,
    to: f.to || undefined,
  };
  const list = useQuery({
    queryKey: ["billing-invoices", f, page],
    queryFn: () => ok(api.GET("/api/v1/admin/billing/invoices", { params: { query: { ...query, limit: 50, offset: page * 50 } } })),
  });
  const exportCsv = async () => {
    setError(null);
    try {
      const body = await ok(api.GET("/api/v1/admin/billing/invoices", { params: { query: { ...query, format: "csv" } }, parseAs: "text" }));
      download(`diyneco-invoices-${isoDay()}.csv`, body as unknown as string);
    } catch (e) {
      setError(e);
    }
  };
  const set = (patch: Partial<InvoiceFilters>) => (setF({ ...f, ...patch }), setPage(0));
  return (
    <Card>
      <div className="flex flex-wrap items-end gap-3 p-5">
        <Field label="Hotel, account ID or number">{(p) => <Input {...p} value={f.q} onChange={(e) => set({ q: e.target.value })} />}</Field>
        <Field label="Status">
          {(p) => (
            <Select {...p} value={f.status} onChange={(e) => set({ status: e.target.value })}>
              <option value="">Any</option>
              {["issued", "partially_paid", "paid", "overdue", "void", "credited"].map((s) => (
                <option key={s} value={s}>
                  {label(s)}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Payment">
          {(p) => (
            <Select {...p} value={f.payment} onChange={(e) => set({ payment: e.target.value })}>
              <option value="">Any</option>
              <option value="unpaid">Unpaid</option>
              <option value="partial">Part paid</option>
              <option value="paid">Paid</option>
              <option value="overdue">Overdue</option>
            </Select>
          )}
        </Field>
        <Field label="Plan">
          {(p) => (
            <Select {...p} value={f.plan} onChange={(e) => set({ plan: e.target.value })}>
              <option value="">Any</option>
              {(plans.data?.data ?? []).map((pl) => (
                <option key={pl.code} value={pl.code}>
                  {pl.name}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Issued from">{(p) => <Input {...p} type="date" value={f.from} onChange={(e) => set({ from: e.target.value })} />}</Field>
        <Field label="to">{(p) => <Input {...p} type="date" value={f.to} onChange={(e) => set({ to: e.target.value })} />}</Field>
        <Button variant="secondary" onClick={() => void exportCsv()}>
          Export CSV
        </Button>
      </div>
      {error ? <ErrorNotice error={error} className="mx-5 mb-3" /> : null}
      {list.isError ? <ErrorNotice error={list.error} className="mx-5 mb-3" /> : null}
      {!list.data ? (
        <Skeleton className="m-5 h-40" />
      ) : list.data.data.length ? (
        <>
          <Table>
            <thead>
              <tr>
                <Th>Number</Th>
                <Th>Hotel</Th>
                <Th>Issued</Th>
                <Th>Due</Th>
                <Th className="text-right">Total</Th>
                <Th className="text-right">Balance</Th>
                <Th>Status</Th>
              </tr>
            </thead>
            <tbody>
              {list.data.data.map((i) => (
                <tr key={i.id}>
                  <Td>
                    <p className="font-medium">{i.number}</p>
                    <p className="text-xs text-muted">
                      {i.kind === "credit_note" ? "Credit note" : label(i.purpose)}
                      {i.plan_code ? ` · ${i.plan_code}` : ""}
                    </p>
                  </Td>
                  <Td>
                    <Link className="text-blue hover:underline" href={`/hotels/${i.hotel_id}`}>
                      {i.hotel_name}
                    </Link>
                  </Td>
                  <Td>{i.issued_at ? formatDate(i.issued_at) : ""}</Td>
                  <Td>{i.due_on ? formatDate(i.due_on) : ""}</Td>
                  <Td className="text-right tabular-nums">{formatMoney(i.total)}</Td>
                  <Td className="text-right tabular-nums">{i.kind === "invoice" ? formatMoney(i.balance) : ""}</Td>
                  <Td>
                    <Badge tone={tone(i.status)}>{label(i.status)}</Badge>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
          <Pager page={page} total={list.data.total} onPage={setPage} />
        </>
      ) : (
        <EmptyState title="No invoices match" />
      )}
    </Card>
  );
}

function Pager({ page, total, onPage }: { page: number; total: number; onPage: (p: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / 50));
  return (
    <div className="flex items-center justify-between p-4 text-sm text-muted">
      <span>
        {total} result{total === 1 ? "" : "s"}
      </span>
      <span className="flex items-center gap-2">
        <Button size="sm" variant="secondary" disabled={page === 0} onClick={() => onPage(page - 1)}>
          Previous
        </Button>
        {page + 1} of {pages}
        <Button size="sm" variant="secondary" disabled={page + 1 >= pages} onClick={() => onPage(page + 1)}>
          Next
        </Button>
      </span>
    </div>
  );
}

const METHODS: Record<string, string> = { eft: "Bank transfer", pay_by_bank: "Pay by bank", sandbox: "Sandbox", card: "Card", other: "Other" };

function Payments() {
  const { api } = useSession();
  const [q, setQ] = useState("");
  const [rec, setRec] = useState("unreconciled");
  const [page, setPage] = useState(0);
  const [error, setError] = useState<unknown>(null);
  const [marking, setMarking] = useState<{ id: string; hotel_id: string; status: "matched" | "disputed" } | null>(null);
  const query = { q: q || undefined, reconciliation: (rec || undefined) as never };
  const list = useQuery({
    queryKey: ["billing-payments", q, rec, page],
    queryFn: () => ok(api.GET("/api/v1/admin/billing/payments", { params: { query: { ...query, limit: 50, offset: page * 50 } } })),
  });
  const exportCsv = async () => {
    setError(null);
    try {
      const body = await ok(api.GET("/api/v1/admin/billing/payments", { params: { query: { ...query, format: "csv" } }, parseAs: "text" }));
      download(`diyneco-payments-${isoDay()}.csv`, body as unknown as string);
    } catch (e) {
      setError(e);
    }
  };
  return (
    <Card>
      <CardHeader
        title="Payments"
        description="Bank transfers recorded by staff are matched when recorded. Provider payments start unreconciled: match each against the provider's settlement report."
      />
      <div className="flex flex-wrap items-end gap-3 px-5 pb-4">
        <Field label="Hotel, invoice or reference">{(p) => <Input {...p} value={q} onChange={(e) => (setQ(e.target.value), setPage(0))} />}</Field>
        <Field label="Reconciliation">
          {(p) => (
            <Select {...p} value={rec} onChange={(e) => (setRec(e.target.value), setPage(0))}>
              <option value="">Any</option>
              <option value="unreconciled">Unreconciled</option>
              <option value="matched">Matched</option>
              <option value="disputed">Disputed</option>
            </Select>
          )}
        </Field>
        <Button variant="secondary" onClick={() => void exportCsv()}>
          Export CSV
        </Button>
      </div>
      {error ? <ErrorNotice error={error} className="mx-5 mb-3" /> : null}
      {!list.data ? (
        <Skeleton className="m-5 h-40" />
      ) : list.data.data.length ? (
        <>
          <Table>
            <thead>
              <tr>
                <Th>Received</Th>
                <Th>Hotel</Th>
                <Th>Invoice</Th>
                <Th>Method</Th>
                <Th>Reference</Th>
                <Th className="text-right">Amount</Th>
                <Th>Reconciliation</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {list.data.data.map((p) => (
                <tr key={p.id}>
                  <Td>{formatDate(p.received_on)}</Td>
                  <Td>
                    <Link className="text-blue hover:underline" href={`/hotels/${p.hotel_id}`}>
                      {p.hotel_name}
                    </Link>
                  </Td>
                  <Td>{p.invoice_number}</Td>
                  <Td>
                    {METHODS[p.method] ?? p.method} {p.test_mode ? <Badge tone="warn">Test</Badge> : null}
                  </Td>
                  <Td className="text-xs text-muted">{p.reference ?? p.provider_payment_id}</Td>
                  <Td className="text-right tabular-nums">
                    {formatMoney(p.amount)}
                    {p.refunded.amount_minor ? <span className="block text-xs text-muted">refunded {formatMoney(p.refunded)}</span> : null}
                  </Td>
                  <Td>
                    <Badge tone={tone(p.reconciliation_status)}>{label(p.reconciliation_status)}</Badge>
                    {p.reconciliation_note ? <span className="block text-xs text-muted">{p.reconciliation_note}</span> : null}
                  </Td>
                  <Td className="flex justify-end gap-2">
                    {p.reconciliation_status !== "matched" ? (
                      <Button size="sm" variant="secondary" onClick={() => setMarking({ id: p.id, hotel_id: p.hotel_id, status: "matched" })}>
                        Matched
                      </Button>
                    ) : null}
                    {p.reconciliation_status !== "disputed" ? (
                      <Button size="sm" variant="ghost" onClick={() => setMarking({ id: p.id, hotel_id: p.hotel_id, status: "disputed" })}>
                        Dispute
                      </Button>
                    ) : null}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
          <Pager page={page} total={list.data.total} onPage={setPage} />
        </>
      ) : (
        <EmptyState title="No payments match" />
      )}
      {marking ? <ReconcileDialog {...marking} onClose={() => setMarking(null)} /> : null}
    </Card>
  );
}

function ReconcileDialog({ id, hotel_id, status, onClose }: { id: string; hotel_id: string; status: "matched" | "disputed"; onClose: () => void }) {
  const { api } = useSession();
  const [note, setNote] = useState("");
  const save = useAction(
    () =>
      ok(
        api.POST("/api/v1/admin/hotels/{hotel_id}/payments/{payment_id}/reconcile", {
          params: { path: { hotel_id, payment_id: id } },
          body: { status, note: note.trim() || null },
        }),
      ),
    { success: "Saved.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title={status === "matched" ? "Mark as matched" : "Mark as disputed"}
      description={status === "matched" ? "Found on the settlement report or bank statement." : "Not found, or the amount differs."}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button loading={save.isPending} onClick={() => save.mutate(undefined)}>
            Save
          </Button>
        </>
      }
    >
      <Field label="Note">{(p) => <Input {...p} value={note} onChange={(e) => setNote(e.target.value)} />}</Field>
      {save.error ? <ErrorNotice error={save.error} className="mt-3" /> : null}
    </Dialog>
  );
}

function Webhooks() {
  const { api } = useSession();
  const q = useQuery({ queryKey: ["billing-webhooks"], queryFn: () => ok(api.GET("/api/v1/admin/billing/webhooks", { params: { query: { limit: 100 } } })) });
  if (!q.data) return <Skeleton className="h-40" />;
  return (
    <Card>
      <CardHeader title="Provider webhooks" description="Every signed webhook received, stored once per event id. A repeat is acknowledged and not processed again." />
      {q.data.data.length ? (
        <Table>
          <thead>
            <tr>
              <Th>Received</Th>
              <Th>Provider</Th>
              <Th>Event</Th>
              <Th>Outcome</Th>
            </tr>
          </thead>
          <tbody>
            {q.data.data.map((e) => (
              <tr key={e.id}>
                <Td>
                  {formatDate(e.received_at)} {formatTime(e.received_at)}
                </Td>
                <Td>{e.provider}</Td>
                <Td className="text-xs">
                  {e.event_type ?? ""} <span className="text-muted">{e.event_id}</span>
                </Td>
                <Td className="text-sm">{e.error ? <span className="text-crit">{e.error}</span> : (e.outcome ?? (e.processed_at ? "Processed" : "Waiting"))}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      ) : (
        <EmptyState title="No webhooks yet" />
      )}
    </Card>
  );
}

function Collections() {
  const { api } = useSession();
  const provider = useQuery({ queryKey: ["billing-provider"], queryFn: () => ok(api.GET("/api/v1/admin/billing/provider")) });
  const s = useQuery({ queryKey: ["billing-settings"], queryFn: () => ok(api.GET("/api/v1/admin/billing-settings")) });
  const [edit, setEdit] = useState<Record<string, string | boolean> | null>(null);
  const [reason, setReason] = useState("");
  const save = useAction(
    () => {
      const d = s.data;
      if (!d || !edit) throw new Error("not loaded");
      const v = { ...base(d), ...edit };
      return ok(
        api.PUT("/api/v1/admin/billing-settings", {
          body: {
            version: d.version,
            reason,
            price_change_notice_days: d.price_change_notice_days,
            trial_days: d.trial_days,
            trial_limits: d.trial_limits,
            reminder_offsets: String(v.reminder_offsets)
              .split(",")
              .map((x) => x.trim())
              .filter(Boolean)
              .map(Number),
            grace_days: Number(v.grace_days),
            renewal_lead_days: Number(v.renewal_lead_days),
            suspend_after_grace: Boolean(v.suspend_after_grace),
            read_only_when_suspended: Boolean(v.read_only_when_suspended),
            proration_enabled: Boolean(v.proration_enabled),
            card_provider: v.card_provider as "none" | "sandbox" | "stitch",
            eft_enabled: Boolean(v.eft_enabled),
          },
        }),
      );
    },
    { success: "Saved.", onDone: () => (setEdit(null), setReason("")) },
  );
  if (!s.data || !provider.data) return <Skeleton className="h-60" />;
  const p = provider.data;
  const cur = { ...base(s.data), ...(edit ?? {}) };
  const set = (k: string, v: string | boolean) => setEdit({ ...(edit ?? {}), [k]: v });
  const check = (k: string, text: string) => (
    <label className="flex items-center gap-2 text-sm">
      <input type="checkbox" checked={Boolean(cur[k])} onChange={(e) => set(k, e.target.checked)} /> {text}
    </label>
  );
  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <Card>
        <CardHeader title="Payment provider" description="Secrets live in the server's environment (STITCH_*) and are never shown here." />
        <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 px-5 pb-5 text-sm">
          <dt className="text-muted">Selected</dt>
          <dd>{label(p.selected)}</dd>
          <dt className="text-muted">Environment</dt>
          <dd>{p.environment}</dd>
          <dt className="text-muted">Stitch</dt>
          <dd>
            {p.stitch.ready ? <Badge tone="good">Configured</Badge> : <Badge tone="neutral">Not configured</Badge>}{" "}
            {p.stitch.ready ? (p.stitch.test_mode ? "test client" : "live client") : ""}
            <span className="block text-xs text-muted">
              Client ID {p.stitch.client_id_set ? "set" : "missing"} · client secret {p.stitch.client_secret_set ? "set" : "missing"} · webhook
              secret {p.stitch.webhook_secret_set ? "set" : "missing"}
            </span>
          </dd>
          <dt className="text-muted">Sandbox</dt>
          <dd>{p.sandbox_allowed ? "Available here (test payments only)" : "Not available in production"}</dd>
          <dt className="text-muted">Bank transfer</dt>
          <dd>
            {p.eft_enabled ? "Offered" : "Off"} · bank details {p.bank_details_set ? "set" : "missing (Company & tax)"}
          </dd>
        </dl>
      </Card>
      <Card>
        <CardHeader title="Collections policy" description="Applies from now on to every hotel." />
        <div className="grid gap-4 p-5 sm:grid-cols-2">
          <Field label="Online payments">
            {(f) => (
              <Select {...f} value={String(cur.card_provider)} onChange={(e) => set("card_provider", e.target.value)}>
                <option value="none">Off</option>
                <option value="sandbox">Sandbox (test payments, not in production)</option>
                <option value="stitch">Stitch</option>
              </Select>
            )}
          </Field>
          <Field label="Reminder days around the due date" hint="Comma separated: -3 is three days before, 0 the due date, 3 three days after">
            {(f) => <Input {...f} value={String(cur.reminder_offsets)} onChange={(e) => set("reminder_offsets", e.target.value)} />}
          </Field>
          <Field label="Grace period after the due date (days)">
            {(f) => <Input {...f} type="number" min={0} max={90} value={String(cur.grace_days)} onChange={(e) => set("grace_days", e.target.value)} />}
          </Field>
          <Field label="Renewal invoice issued before the period ends (days)">
            {(f) => (
              <Input {...f} type="number" min={0} max={60} value={String(cur.renewal_lead_days)} onChange={(e) => set("renewal_lead_days", e.target.value)} />
            )}
          </Field>
          <div className="flex flex-col gap-2 sm:col-span-2">
            {check("eft_enabled", "Offer bank transfer (EFT) with Diyneco's bank details")}
            {check("suspend_after_grace", "Suspend a subscription still unpaid after the grace period")}
            {check("read_only_when_suspended", "While suspended, the hotel is read-only except for billing (data is never deleted)")}
            {check("proration_enabled", "Upgrades apply at once with a prorated invoice for the rest of the period")}
          </div>
          <Field label="Reason for the change" className="sm:col-span-2">
            {(f) => <Input {...f} value={reason} onChange={(e) => setReason(e.target.value)} />}
          </Field>
        </div>
        <div className="px-5 pb-5">
          <Button disabled={!edit || reason.trim().length < 3} loading={save.isPending} onClick={() => save.mutate(undefined)}>
            Save policy
          </Button>
          {save.error ? <ErrorNotice error={save.error} className="mt-3" /> : null}
        </div>
      </Card>
    </div>
  );
}

function base(d: {
  reminder_offsets: number[];
  grace_days: number;
  renewal_lead_days: number;
  suspend_after_grace: boolean;
  read_only_when_suspended: boolean;
  proration_enabled: boolean;
  card_provider: string;
  eft_enabled: boolean;
}): Record<string, string | boolean> {
  return {
    reminder_offsets: d.reminder_offsets.join(", "),
    grace_days: String(d.grace_days),
    renewal_lead_days: String(d.renewal_lead_days),
    suspend_after_grace: d.suspend_after_grace,
    read_only_when_suspended: d.read_only_when_suspended,
    proration_enabled: d.proration_enabled,
    card_provider: d.card_provider,
    eft_enabled: d.eft_enabled,
  };
}

export type { Money };
