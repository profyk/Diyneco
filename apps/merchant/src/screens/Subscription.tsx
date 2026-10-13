"use client";

// The hotel's subscription and billing (DECISIONS D79): status, plans to compare and choose,
// the server's quote, paying Diyneco's invoices, payment history and the billing contact.
// Every price, total and status comes from the API; nothing here names a plan or a price.

import { formatDate, formatMoney, ok } from "@diyneco/api-client";
import {
  Badge,
  Button,
  Card,
  Dialog,
  ErrorNotice,
  Field,
  Input,
  Skeleton,
  Table,
  Td,
  Textarea,
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { label, useAction } from "../common";
import { LegalText } from "../Legal";
import { useSession } from "../session";

type Money = { amount_minor: number; currency: string };
type Interval = "month" | "quarter" | "year";
const PER: Record<string, string> = { month: "a month", quarter: "a quarter", year: "a year" };
const INTERVAL_NAME: Record<Interval, string> = { month: "Monthly", quarter: "Quarterly", year: "Annually" };

function statusTone(s: string | null | undefined): "good" | "warn" | "crit" | "info" | "neutral" {
  if (s === "active" || s === "paid" || s === "succeeded" || s === "credited") return "good";
  if (s === "past_due" || s === "suspended" || s === "overdue" || s === "failed") return "crit";
  if (s === "pending_payment" || s === "partially_paid" || s === "cancellation_scheduled" || s === "pending") return "warn";
  if (s === "trial") return "info";
  return "neutral";
}

export function Plan() {
  const { api, can } = useSession();
  const sub = useQuery({ queryKey: ["subscription"], queryFn: () => ok(api.GET("/api/v1/subscription")) });
  const [paying, setPaying] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const resume = useAction(() => ok(api.POST("/api/v1/subscription/resume")), { success: "Cancellation withdrawn." });
  const withdraw = useAction(
    (body: { plan_code: string; interval: Interval }) => ok(api.POST("/api/v1/subscription/change", { body })),
    { success: "The scheduled change is withdrawn." },
  );
  if (sub.isError) return <ErrorNotice error={sub.error} />;
  if (!sub.data) return <Skeleton className="h-40" />;
  const s = sub.data;
  const manage = can("subscription.manage");
  const current = s.plan as { code?: string; name?: string } | null;
  return (
    <div className="flex max-w-4xl flex-col gap-5">
      <Card className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="font-display text-xl font-semibold">
              {current?.name ?? (s.status === "trial" ? "Free trial" : "No subscription")}{" "}
              {s.status ? <Badge tone={statusTone(s.status)}>{label(s.status)}</Badge> : null}
            </p>
            {s.trial_ends_on && s.status === "trial" ? (
              <p className="mt-1 text-sm text-muted">Trial ends {formatDate(s.trial_ends_on)}</p>
            ) : null}
            {s.price ? (
              <p className="mt-1 text-sm text-muted">
                {formatMoney(s.price)} {PER[s.interval ?? "month"]} (the price agreed when you subscribed)
              </p>
            ) : null}
            {s.current_period_start && s.renews_on ? (
              <p className="mt-1 text-sm text-muted">
                Current period {formatDate(s.current_period_start)} to {formatDate(s.renews_on)} ·{" "}
                {s.cancel_at_period_end ? "ends" : s.status === "pending_payment" ? "starts once paid, renews" : "renews"}{" "}
                {formatDate(s.renews_on)}
              </p>
            ) : null}
          </div>
          {manage && s.status === "cancellation_scheduled" ? (
            <Button variant="secondary" loading={resume.isPending} onClick={() => resume.mutate(undefined)}>
              Keep my subscription
            </Button>
          ) : null}
          {manage && s.status && ["trial", "pending_payment", "active", "past_due"].includes(s.status) ? (
            <Button variant="ghost" onClick={() => setCancelling(true)}>
              Cancel subscription
            </Button>
          ) : null}
        </div>
        {s.status === "suspended" ? (
          <p role="alert" className="mt-4 rounded-md bg-crit/10 p-3 text-sm text-crit">
            Your subscription is suspended for an unpaid invoice. Your data is safe and can still be viewed; changes are
            paused until the invoice is paid.
          </p>
        ) : s.status === "past_due" ? (
          <p role="alert" className="mt-4 rounded-md bg-warn/10 p-3 text-sm">
            An invoice is past its due date. Pay it to avoid interruption.
          </p>
        ) : s.status === "pending_payment" ? (
          <p className="mt-4 rounded-md bg-surface-2 p-3 text-sm">Your subscription starts as soon as its first invoice is paid.</p>
        ) : s.status === null ? (
          <p className="mt-4 rounded-md bg-surface-2 p-3 text-sm">
            You have no current subscription. Your data is kept; choose a plan below to carry on adding rooms, devices and staff.
          </p>
        ) : null}
        {s.pending_change ? (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-md bg-surface-2 p-3 text-sm">
            <span>
              Changes to <strong>{s.pending_change.plan_name}</strong> ({INTERVAL_NAME[(s.pending_change.interval ?? "month") as Interval]},{" "}
              {formatMoney(s.pending_change.price)}) on {formatDate(s.pending_change.effective_on)}.
            </span>
            {manage && current?.code && s.interval ? (
              <Button
                size="sm"
                variant="secondary"
                loading={withdraw.isPending}
                onClick={() => withdraw.mutate({ plan_code: current.code ?? "", interval: s.interval as Interval })}
              >
                Keep current plan
              </Button>
            ) : null}
          </div>
        ) : null}
        {s.outstanding.length ? (
          <div className="mt-4">
            <h3 className="mb-2 font-display text-sm font-semibold">To pay</h3>
            <Table>
              <tbody>
                {s.outstanding.map((o) => (
                  <tr key={o.invoice_id}>
                    <Td className="font-medium">{o.number}</Td>
                    <Td className="text-sm text-muted">due {formatDate(o.due_on)}</Td>
                    <Td>
                      <Badge tone={statusTone(o.status)}>{label(o.status)}</Badge>
                    </Td>
                    <Td className="text-right tabular-nums">{formatMoney(o.balance)}</Td>
                    <Td className="text-right">
                      {manage ? (
                        <Button size="sm" onClick={() => setPaying(o.invoice_id)}>
                          Pay
                        </Button>
                      ) : null}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        ) : null}
        <Table className="mt-4">
          <thead>
            <tr>
              <Th>Usage</Th>
              <Th className="text-right">Used of limit</Th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(s.usage).map(([k, u]) => (
              <tr key={k}>
                <Td>{label(k)}</Td>
                <Td className="text-right tabular-nums">
                  {u.used} of {u.limit ?? "unlimited"}
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
        {withdraw.error ? <ErrorNotice error={withdraw.error} className="mt-3" /> : null}
        {resume.error ? <ErrorNotice error={resume.error} className="mt-3" /> : null}
      </Card>

      <Plans
        currentCode={current?.code ?? null}
        currentInterval={(s.interval as Interval | null) ?? null}
        mode={s.status && ["active"].includes(s.status) ? "change" : s.status === "pending_payment" || s.status === "past_due" || s.status === "suspended" || s.status === "cancellation_scheduled" ? "locked" : "subscribe"}
        onInvoice={setPaying}
      />
      <SubscriptionInvoices onPay={manage ? setPaying : undefined} />
      <PaymentHistory onRetry={manage ? setPaying : undefined} />
      {manage ? <BillingContact /> : null}
      {paying ? <PayDialog invoiceId={paying} onClose={() => setPaying(null)} /> : null}
      {cancelling ? <CancelDialog status={s.status ?? ""} onClose={() => setCancelling(false)} /> : null}
    </div>
  );
}

type PublicPlan = {
  code: string;
  name: string;
  short_description: string | null;
  highlights: string[];
  recommended: boolean;
  tax_treatment: string;
  setup_fee: Money;
  promo_discount_bp: number;
  promo_ends_on: string | null;
  support_level: string | null;
  limits: Record<string, unknown>;
  prices: { interval: string; amount: Money; per_month: Money; intro_amount: Money | null; intro_periods: number | null; saving_bp: number | null }[];
};

function Plans({
  currentCode,
  currentInterval,
  mode,
  onInvoice,
}: {
  currentCode: string | null;
  currentInterval: Interval | null;
  mode: "subscribe" | "change" | "locked";
  onInvoice: (id: string) => void;
}) {
  const { api, can } = useSession();
  const catalogue = useQuery({ queryKey: ["public-plans"], queryFn: () => ok(api.GET("/api/v1/plans")) });
  const plans = (catalogue.data?.data ?? []) as PublicPlan[];
  const intervals = (["month", "quarter", "year"] as Interval[]).filter((i) => plans.some((p) => p.prices.some((x) => x.interval === i)));
  const [interval, setInterval] = useState<Interval>("month");
  const [chosen, setChosen] = useState<PublicPlan | null>(null);
  const shown = intervals.includes(interval) ? interval : (intervals[0] ?? "month");
  if (catalogue.isError) return <ErrorNotice error={catalogue.error} />;
  if (!catalogue.data) return <Skeleton className="h-40" />;
  return (
    <Card className="p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-lg font-semibold">Plans</h2>
          <p className="text-sm text-muted">
            Prices {catalogue.data.tax_charged ? `exclude or include ${catalogue.data.tax_name ?? "tax"} as shown` : "include no VAT"}.
            The total is worked out before you confirm.
          </p>
        </div>
        {intervals.length > 1 ? (
          <div role="tablist" aria-label="Billing interval" className="flex gap-1">
            {intervals.map((i) => (
              <button
                key={i}
                role="tab"
                aria-selected={shown === i}
                onClick={() => setInterval(i)}
                className={`rounded-full px-3 py-1.5 text-sm font-medium ${shown === i ? "bg-brand text-on-brand" : "bg-surface-2"}`}
              >
                {INTERVAL_NAME[i]}
              </button>
            ))}
          </div>
        ) : null}
      </div>
      {plans.length ? (
        <div className="grid gap-4 md:grid-cols-3">
          {plans.map((p) => {
            const price = p.prices.find((x) => x.interval === shown);
            const isCurrent = p.code === currentCode && shown === currentInterval;
            return (
              <div key={p.code} className={`flex flex-col rounded-lg border p-4 ${p.recommended ? "border-brand" : "border-line"}`}>
                <p className="font-display font-semibold">
                  {p.name} {p.recommended ? <Badge tone="info">Recommended</Badge> : null}
                </p>
                {p.short_description ? <p className="mt-1 text-sm text-muted">{p.short_description}</p> : null}
                {price ? (
                  <>
                    <p className="mt-3 font-display text-2xl font-semibold tabular-nums">
                      {formatMoney(price.intro_amount ?? price.amount)}
                      <span className="text-sm font-normal text-muted"> {PER[shown]}</span>
                    </p>
                    {price.intro_amount ? (
                      <p className="text-xs text-muted">
                        for {price.intro_periods} period{price.intro_periods === 1 ? "" : "s"}, then {formatMoney(price.amount)}
                      </p>
                    ) : null}
                    {shown !== "month" ? <p className="text-xs text-muted">{formatMoney(price.per_month)} a month</p> : null}
                    {price.saving_bp ? <p className="text-xs text-good">Save {Math.floor(price.saving_bp / 100)}% against monthly</p> : null}
                    <p className="text-xs text-muted">{p.tax_treatment === "inclusive" ? "Includes VAT" : "Before VAT, where charged"}</p>
                  </>
                ) : (
                  <p className="mt-3 text-sm text-muted">Not offered {INTERVAL_NAME[shown].toLowerCase()}.</p>
                )}
                {p.setup_fee.amount_minor ? <p className="mt-1 text-xs text-muted">One-time setup fee {formatMoney(p.setup_fee)}</p> : null}
                {p.promo_discount_bp && p.promo_ends_on ? (
                  <p className="mt-1 text-xs text-good">
                    {Math.floor(p.promo_discount_bp / 100)}% off the first period until {formatDate(p.promo_ends_on)}
                  </p>
                ) : null}
                <ul className="mt-3 flex-1 list-disc pl-5 text-sm">
                  {p.highlights.map((h) => (
                    <li key={h}>{h}</li>
                  ))}
                  {Object.entries(p.limits).map(([k, v]) => (
                    <li key={k}>
                      {v === null ? "Unlimited" : String(v)} {label(k).toLowerCase()}
                    </li>
                  ))}
                  {p.support_level ? <li>{p.support_level}</li> : null}
                </ul>
                {can("subscription.manage") && price && mode !== "locked" ? (
                  <Button className="mt-4" variant={isCurrent ? "secondary" : "primary"} disabled={isCurrent} onClick={() => setChosen(p)}>
                    {isCurrent ? "Your plan" : mode === "change" ? "Switch to this plan" : "Choose this plan"}
                  </Button>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-muted">No plans are offered right now.</p>
      )}
      {mode === "locked" ? (
        <p className="mt-4 text-sm text-muted">Plan changes open again once your subscription is active and paid up.</p>
      ) : null}
      {chosen ? (
        mode === "change" ? (
          <ChangeDialog plan={chosen} interval={shown} onClose={() => setChosen(null)} />
        ) : (
          <SubscribeDialog
            plan={chosen}
            interval={shown}
            onClose={() => setChosen(null)}
            onInvoice={(id) => {
              setChosen(null);
              onInvoice(id);
            }}
          />
        )
      ) : null}
    </Card>
  );
}

function SubscribeDialog({
  plan,
  interval,
  onClose,
  onInvoice,
}: {
  plan: PublicPlan;
  interval: Interval;
  onClose: () => void;
  onInvoice: (id: string) => void;
}) {
  const { api } = useSession();
  const quote = useQuery({
    queryKey: ["subscription-quote", plan.code, interval],
    queryFn: () => ok(api.POST("/api/v1/subscription/quote", { body: { plan_code: plan.code, interval } })),
  });
  const terms = useQuery({
    queryKey: ["legal", "merchant"],
    queryFn: () => ok(api.GET("/api/v1/legal/documents", { params: { query: { audience: "merchant" } } })),
  });
  const termsDoc = terms.data?.data.find((d) => d.kind === "terms");
  const [accepted, setAccepted] = useState(false);
  const subscribe = useAction(
    () =>
      ok(
        api.POST("/api/v1/subscription/subscribe", {
          body: { plan_code: plan.code, interval, accept_terms: true },
        }),
      ),
    { success: (r) => `Subscribed. Invoice ${r.invoice.number} is ready to pay.`, onDone: (r) => onInvoice(r.invoice.id) },
  );
  const q = quote.data;
  const m = (minor: number) => formatMoney({ amount_minor: minor, currency: q?.currency ?? "ZAR" });
  return (
    <Dialog
      open
      onClose={onClose}
      title={`Subscribe to ${plan.name}`}
      description="This is what you pay today. Nothing is charged until you pay the invoice."
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Not now
          </Button>
          <Button disabled={!q || !accepted} loading={subscribe.isPending} onClick={() => subscribe.mutate(undefined)}>
            Subscribe and get invoice
          </Button>
        </>
      }
    >
      {quote.isError ? <ErrorNotice error={quote.error} /> : null}
      {q ? (
        <Table>
          <tbody>
            {q.lines.map((l) => (
              <tr key={l.code}>
                <Td>
                  {l.description}
                  {l.discount_minor ? <span className="block text-xs text-good">Discount {m(l.discount_minor)}</span> : null}
                </Td>
                <Td className="text-right tabular-nums">{m(l.total_minor)}</Td>
              </tr>
            ))}
            <tr>
              <Td className="text-muted">Subtotal</Td>
              <Td className="text-right tabular-nums">{m(q.subtotal_minor)}</Td>
            </tr>
            <tr>
              <Td className="text-muted">{q.tax_charged ? `${q.tax_name} at ${(q.tax_rate_bp ?? 0) / 100}%` : "No VAT charged"}</Td>
              <Td className="text-right tabular-nums">{m(q.tax_minor)}</Td>
            </tr>
            <tr>
              <Td className="font-semibold">Total due today</Td>
              <Td className="text-right font-semibold tabular-nums">{m(q.total_minor)}</Td>
            </tr>
          </tbody>
        </Table>
      ) : (
        <Skeleton className="h-32" />
      )}
      {q ? (
        <p className="mt-3 text-sm text-muted">
          Period {formatDate(q.period_start)} to {formatDate(q.period_end)}. It then renews {INTERVAL_NAME[interval].toLowerCase()} at{" "}
          {m(q.renews_at_minor)}
          {q.prices_include_tax ? " including VAT" : q.tax_charged ? " plus VAT" : ""} until you cancel.
        </p>
      ) : null}
      {termsDoc ? <div className="mt-3">{<LegalText doc={termsDoc} />}</div> : null}
      <label className="mt-4 flex items-start gap-2 text-sm">
        <input type="checkbox" className="mt-1" checked={accepted} onChange={(e) => setAccepted(e.target.checked)} />
        <span>I accept the subscription terms{termsDoc ? ` (${termsDoc.title}, version ${termsDoc.version})` : ""} for this hotel.</span>
      </label>
      {subscribe.error ? <ErrorNotice error={subscribe.error} className="mt-3" /> : null}
    </Dialog>
  );
}

function ChangeDialog({ plan, interval, onClose }: { plan: PublicPlan; interval: Interval; onClose: () => void }) {
  const { api } = useSession();
  const price = plan.prices.find((p) => p.interval === interval);
  const change = useAction(() => ok(api.POST("/api/v1/subscription/change", { body: { plan_code: plan.code, interval } })), {
    success: (r) =>
      r.effective === "now"
        ? `You are now on ${plan.name}.${r.invoice ? ` Invoice ${r.invoice.number} covers the rest of this period.` : ""}`
        : `${plan.name} starts at your next renewal.`,
    onDone: onClose,
  });
  return (
    <Dialog
      open
      onClose={onClose}
      title={`Switch to ${plan.name}`}
      description="Diyneco works out when the change applies and what it costs."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Not now
          </Button>
          <Button loading={change.isPending} onClick={() => change.mutate(undefined)}>
            Confirm change
          </Button>
        </>
      }
    >
      {price ? (
        <p className="text-sm">
          {plan.name}, {INTERVAL_NAME[interval].toLowerCase()}: {formatMoney(price.amount)} {PER[interval]}.
        </p>
      ) : null}
      <p className="mt-2 text-sm text-muted">
        Downgrades and changes of billing interval start at your next renewal. An upgrade starts at once with an invoice for the rest
        of the current period when Diyneco offers that; otherwise it starts at your next renewal too.
      </p>
      {change.error ? <ErrorNotice error={change.error} className="mt-3" /> : null}
    </Dialog>
  );
}

function CancelDialog({ status, onClose }: { status: string; onClose: () => void }) {
  const { api } = useSession();
  const [reason, setReason] = useState("");
  const cancel = useAction(() => ok(api.POST("/api/v1/subscription/cancel", { body: { reason } })), {
    success: "Subscription cancelled.",
    onDone: onClose,
  });
  const when =
    status === "trial"
      ? "Your trial ends now."
      : status === "pending_payment"
        ? "The subscription ends now and its unpaid invoice is cancelled."
        : "Your subscription runs to the end of the period you paid for, then ends. Nothing is refunded.";
  return (
    <Dialog
      open
      onClose={onClose}
      title="Cancel subscription"
      description={`${when} Your data and invoices are kept.`}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Keep it
          </Button>
          <Button variant="danger" disabled={reason.trim().length < 3} loading={cancel.isPending} onClick={() => cancel.mutate(undefined)}>
            Cancel subscription
          </Button>
        </>
      }
    >
      <Field label="Why are you cancelling?">{(p) => <Textarea {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}</Field>
      {cancel.error ? <ErrorNotice error={cancel.error} className="mt-3" /> : null}
    </Dialog>
  );
}

/** Paying one invoice: online through the configured provider, or by bank transfer. */
function PayDialog({ invoiceId, onClose }: { invoiceId: string; onClose: () => void }) {
  const { api } = useSession();
  const invoice = useQuery({
    queryKey: ["subscription-invoice", invoiceId],
    queryFn: () => ok(api.GET("/api/v1/subscription/invoices/{invoice_id}", { params: { path: { invoice_id: invoiceId } } })),
  });
  const options = useQuery({ queryKey: ["payment-options"], queryFn: () => ok(api.GET("/api/v1/subscription/payment-options")) });
  const pay = useAction(
    () => ok(api.POST("/api/v1/subscription/invoices/{invoice_id}/pay", { params: { path: { invoice_id: invoiceId } } })),
    { onDone: (r) => window.location.assign(r.checkout_url) },
  );
  const inv = invoice.data;
  const online = options.data?.online as { available: boolean; label: string | null; test_mode: boolean } | undefined;
  const eft = options.data?.eft as { available: boolean; bank: Record<string, string>; instructions: string | null } | undefined;
  return (
    <Dialog open onClose={onClose} title={inv ? `Pay invoice ${inv.number}` : "Pay invoice"} description="Choose how to pay." size="lg">
      {invoice.isError ? <ErrorNotice error={invoice.error} /> : null}
      {inv ? (
        <p className="text-sm">
          Balance due <strong className="tabular-nums">{formatMoney(inv.balance)}</strong>
          {inv.due_on ? ` by ${formatDate(inv.due_on)}` : ""}.
        </p>
      ) : (
        <Skeleton className="h-6" />
      )}
      {online?.available ? (
        <div className="mt-4 rounded-md border border-line p-4">
          <p className="font-medium">Pay online</p>
          {online.test_mode ? (
            <p className="mt-1 rounded bg-warn/15 px-2 py-1 text-xs font-semibold uppercase tracking-wide">
              Test mode: no real money moves
            </p>
          ) : null}
          <p className="mt-1 text-sm text-muted">{online.label}. You are taken to the payment page and come back here.</p>
          <Button className="mt-3" disabled={!inv || inv.balance.amount_minor <= 0} loading={pay.isPending} onClick={() => pay.mutate(undefined)}>
            Pay {inv ? formatMoney(inv.balance) : ""} online
          </Button>
        </div>
      ) : null}
      {eft?.available ? (
        <div className="mt-4 rounded-md border border-line p-4">
          <p className="font-medium">Pay by bank transfer (EFT)</p>
          <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
            {Object.entries(eft.bank).map(([k, v]) => (
              <div key={k} className="contents">
                <dt className="text-muted">{label(k)}</dt>
                <dd>{v}</dd>
              </div>
            ))}
            <dt className="text-muted">Reference</dt>
            <dd className="font-semibold">{inv?.number}</dd>
          </dl>
          {eft.instructions ? <p className="mt-2 text-sm text-muted">{eft.instructions}</p> : null}
          <p className="mt-2 text-xs text-muted">Diyneco confirms the payment once it reaches the bank account; you get an email.</p>
        </div>
      ) : null}
      {options.data && !online?.available && !eft?.available ? (
        <p className="mt-4 text-sm text-muted">Payment details are not set up yet. Contact Diyneco to pay this invoice.</p>
      ) : null}
      {pay.error ? <ErrorNotice error={pay.error} className="mt-3" /> : null}
    </Dialog>
  );
}

/** Invoices and credit notes from Diyneco; PDFs open through a short-lived signed link. */
function SubscriptionInvoices({ onPay }: { onPay?: (id: string) => void }) {
  const { api } = useSession();
  const list = useQuery({ queryKey: ["subscription-invoices"], queryFn: () => ok(api.GET("/api/v1/subscription/invoices")) });
  const [error, setError] = useState<unknown>(null);
  const open = async (id: string) => {
    setError(null);
    try {
      const { url } = await ok(api.GET("/api/v1/subscription/invoices/{invoice_id}/pdf", { params: { path: { invoice_id: id } } }));
      window.open(url, "_blank", "noopener");
    } catch (err) {
      setError(err);
    }
  };
  const rows = list.data?.data ?? [];
  return (
    <Card className="p-5">
      <h2 className="mb-3 font-display text-lg font-semibold">Invoices from Diyneco</h2>
      {rows.length ? (
        <Table>
          <thead>
            <tr>
              <Th>Document</Th>
              <Th className="text-right">Total</Th>
              <Th className="text-right">Balance</Th>
              <Th>Status</Th>
              <Th />
            </tr>
          </thead>
          <tbody>
            {rows.map((i) => (
              <tr key={i.id}>
                <Td>
                  <p className="font-medium">{i.number}</p>
                  <p className="text-xs text-muted">
                    {i.kind === "credit_note" ? "Credit note" : i.is_tax_invoice ? "Tax invoice" : "Invoice"} · {formatDate(i.issued_at)}
                    {i.due_on && i.kind === "invoice" ? ` · due ${formatDate(i.due_on)}` : ""}
                  </p>
                </Td>
                <Td className="text-right tabular-nums">{formatMoney(i.total)}</Td>
                <Td className="text-right tabular-nums">{i.kind === "invoice" ? formatMoney(i.balance) : ""}</Td>
                <Td>
                  <Badge tone={statusTone(i.status)}>{label(i.status)}</Badge>
                </Td>
                <Td className="flex justify-end gap-2">
                  {onPay && i.kind === "invoice" && i.balance.amount_minor > 0 && ["issued", "partially_paid", "overdue"].includes(i.status) ? (
                    <Button size="sm" onClick={() => onPay(i.id)}>
                      Pay
                    </Button>
                  ) : null}
                  <Button size="sm" variant="secondary" disabled={!i.has_pdf} onClick={() => void open(i.id)}>
                    PDF
                  </Button>
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      ) : (
        <p className="text-sm text-muted">No invoices yet.</p>
      )}
      {error ? <ErrorNotice error={error} className="mt-3" /> : null}
    </Card>
  );
}

const METHODS: Record<string, string> = { eft: "Bank transfer", pay_by_bank: "Pay by bank", sandbox: "Test payment", card: "Card", other: "Other" };

function PaymentHistory({ onRetry }: { onRetry?: (invoiceId: string) => void }) {
  const { api } = useSession();
  const payments = useQuery({ queryKey: ["subscription-payments"], queryFn: () => ok(api.GET("/api/v1/subscription/payments")) });
  const attempts = useQuery({ queryKey: ["subscription-attempts"], queryFn: () => ok(api.GET("/api/v1/subscription/payment-attempts")) });
  const rows = payments.data?.data ?? [];
  const failed = (attempts.data?.data ?? []).filter((a) => a.status === "failed");
  return (
    <Card className="p-5">
      <h2 className="mb-3 font-display text-lg font-semibold">Payments</h2>
      {rows.length ? (
        <Table>
          <thead>
            <tr>
              <Th>Received</Th>
              <Th>Invoice</Th>
              <Th>Method</Th>
              <Th>Reference</Th>
              <Th className="text-right">Amount</Th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id}>
                <Td>{formatDate(p.received_on)}</Td>
                <Td>{p.invoice_number}</Td>
                <Td>
                  {METHODS[p.method] ?? label(p.method)} {p.test_mode ? <Badge tone="warn">Test</Badge> : null}
                </Td>
                <Td className="text-sm text-muted">{p.reference ?? ""}</Td>
                <Td className="text-right tabular-nums">
                  {formatMoney(p.amount)}
                  {p.refunded.amount_minor ? <span className="block text-xs text-muted">refunded {formatMoney(p.refunded)}</span> : null}
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      ) : (
        <p className="text-sm text-muted">No payments yet.</p>
      )}
      {failed.length ? (
        <div className="mt-4">
          <h3 className="mb-2 font-display text-sm font-semibold">Payments that did not go through</h3>
          <Table>
            <tbody>
              {failed.map((a) => (
                <tr key={a.id}>
                  <Td>{formatDate(a.created_at)}</Td>
                  <Td className="text-sm text-muted">{a.failure_reason ?? "Declined"}</Td>
                  <Td className="text-right tabular-nums">{formatMoney(a.amount)}</Td>
                  <Td className="text-right">
                    {onRetry ? (
                      <Button size="sm" variant="secondary" onClick={() => onRetry(a.invoice_id)}>
                        Try again
                      </Button>
                    ) : null}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ) : null}
    </Card>
  );
}

const CONTACT_FIELDS = [
  ["legal_name", "Legal name"],
  ["vat_number", "VAT number"],
  ["billing_email", "Billing email"],
  ["phone", "Phone"],
  ["contact_name", "Contact person"],
] as const;
const ADDRESS_FIELDS = [
  ["line1", "Address"],
  ["line2", "Address line 2"],
  ["city", "City"],
  ["province", "Province"],
  ["postal_code", "Postal code"],
] as const;

/** Who Diyneco invoices for this hotel; invoices copy it when they are issued. */
function BillingContact() {
  const { api } = useSession();
  const contact = useQuery({ queryKey: ["billing-contact"], queryFn: () => ok(api.GET("/api/v1/subscription/billing-contact")) });
  const [form, setForm] = useState<Record<string, string>>({});
  const save = useAction(
    () => {
      const c = contact.data;
      const value = (k: string) => (form[k] ?? ((c as Record<string, unknown> | undefined)?.[k] as string | null) ?? "").trim() || null;
      const addr = (k: string) =>
        (form[`address.${k}`] ?? ((c?.address as Record<string, string> | undefined)?.[k] ?? "")).trim() || null;
      return ok(
        api.PUT("/api/v1/subscription/billing-contact", {
          body: {
            version: c?.version ?? 0,
            legal_name: value("legal_name"),
            vat_number: value("vat_number"),
            billing_email: value("billing_email"),
            phone: value("phone"),
            contact_name: value("contact_name"),
            address: Object.fromEntries(ADDRESS_FIELDS.map(([k]) => [k, addr(k)])),
          },
        }),
      );
    },
    { success: "Billing details saved.", onDone: () => setForm({}) },
  );
  if (!contact.data) return <Skeleton className="h-40" />;
  const c = contact.data as unknown as Record<string, unknown> & { address: Record<string, string> };
  return (
    <Card className="p-5">
      <h2 className="font-display text-lg font-semibold">Billing details</h2>
      <p className="mb-3 text-sm text-muted">Who Diyneco invoices. Leave blank to use the hotel&apos;s own details and send invoices to the owners.</p>
      <div className="grid gap-3 md:grid-cols-2">
        {CONTACT_FIELDS.map(([k, title]) => (
          <Field key={k} label={title}>
            {(p) => <Input {...p} value={form[k] ?? (c[k] as string | null) ?? ""} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />}
          </Field>
        ))}
        {ADDRESS_FIELDS.map(([k, title]) => (
          <Field key={k} label={title}>
            {(p) => (
              <Input
                {...p}
                value={form[`address.${k}`] ?? c.address?.[k] ?? ""}
                onChange={(e) => setForm({ ...form, [`address.${k}`]: e.target.value })}
              />
            )}
          </Field>
        ))}
      </div>
      <Button className="mt-4" disabled={!Object.keys(form).length} loading={save.isPending} onClick={() => save.mutate(undefined)}>
        Save billing details
      </Button>
      {save.error ? <ErrorNotice error={save.error} className="mt-3" /> : null}
    </Card>
  );
}
