"use client";

import { currencySymbol, formatDate, formatMoney, type Money, ok, parseAmount, toAmountInput } from "@diyneco/api-client";
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
  Table,
  Td,
  Textarea,
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAction } from "./common";
import { useCurrencies } from "./screens";
import { useSession } from "./session";

// Plans & Pricing (DECISIONS D74). Every plan, price, interval, limit and discount is data
// edited here; the server validates and computes everything. Drafts are invisible to hotels
// until published; a price already in force is never changed, only replaced by a new one.

type Interval = "month" | "quarter" | "year";
const INTERVALS: [Interval, string][] = [
  ["month", "Monthly"],
  ["quarter", "Quarterly"],
  ["year", "Annual"],
];
const LIMITS = ["rooms", "devices", "staff", "api_keys"] as const;

interface Price {
  id: string;
  interval: Interval;
  amount: Money;
  intro_amount: Money | null;
  intro_periods: number | null;
  per_month: Money;
  effective_from: string;
  existing_policy: "new_only" | "next_renewal";
  notice_days: number | null;
  reason: string;
}

export interface Plan {
  id: string;
  code: string;
  name: string;
  currency: string;
  short_description: string | null;
  description: string | null;
  highlights: string[];
  status: "draft" | "published" | "archived";
  display_order: number;
  recommended: boolean;
  setup_fee: Money;
  trial_days: number;
  tax_treatment: "exclusive" | "inclusive";
  support_level: string | null;
  overage_policy: string | null;
  can_upgrade: boolean;
  can_downgrade: boolean;
  promo_discount_bp: number;
  promo_ends_on: string | null;
  limits: Record<string, number>;
  version: number;
  prices: Partial<Record<Interval, Price>>;
  scheduled: Price[];
  history: Price[];
}

const STATUS: Record<Plan["status"], ["good" | "warn" | "neutral", string]> = {
  draft: ["warn", "Draft"],
  published: ["good", "Published"],
  archived: ["neutral", "Archived"],
};

/** "R499.00 a month", or the first interval the plan is priced on. */
export function planPriceLabel(plan: { prices: Partial<Record<string, { amount: Money }>> }): string {
  const names: [string, string][] = [
    ["month", "a month"],
    ["quarter", "a quarter"],
    ["year", "a year"],
  ];
  for (const [interval, name] of names) {
    const p = plan.prices[interval];
    if (p) return `${formatMoney(p.amount)} ${name}`;
  }
  return "no price";
}

export function Plans() {
  const { api } = useSession();
  const plans = useQuery({ queryKey: ["plans"], queryFn: () => ok(api.GET("/api/v1/admin/plans")) });
  const [editing, setEditing] = useState<Plan | "new" | null>(null);
  const [pricing, setPricing] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [changing, setChanging] = useState<{ plan: Plan; action: "publish" | "archive" | "restore" } | null>(null);
  const rows = (plans.data?.data ?? []) as unknown as Plan[];
  const byId = (id: string | null) => rows.find((p) => p.id === id) ?? null;

  return (
    <>
      <PageHeader
        title="Plans & Pricing"
        description="Plans are drafts until you publish them. Prices are set per billing interval and never change once in force."
        actions={<Button onClick={() => setEditing("new")}>New plan</Button>}
      />
      <Card>
        {plans.isLoading ? (
          <Skeleton className="h-40" />
        ) : plans.error ? (
          <ErrorNotice error={plans.error} />
        ) : rows.length ? (
          <Table>
            <thead>
              <tr>
                <Th>Plan</Th>
                {INTERVALS.map(([, name]) => (
                  <Th key={name} className="text-right">
                    {name}
                  </Th>
                ))}
                <Th>Status</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id}>
                  <Td>
                    <p className="font-medium">
                      {p.name} {p.recommended ? <Badge tone="info">Recommended</Badge> : null}
                    </p>
                    <p className="font-mono text-xs text-muted">
                      {p.code} · {p.currency}
                      {p.setup_fee.amount_minor ? ` · setup ${formatMoney(p.setup_fee)}` : ""}
                      {p.trial_days ? ` · ${p.trial_days}-day trial` : ""}
                    </p>
                  </Td>
                  {INTERVALS.map(([interval]) => {
                    const price = p.prices[interval];
                    const next = p.scheduled.find((s) => s.interval === interval);
                    return (
                      <Td key={interval} className="text-right tabular-nums">
                        {price ? formatMoney(price.amount) : <span className="text-muted">–</span>}
                        {next ? (
                          <p className="text-xs text-muted">
                            {formatMoney(next.amount)} from {formatDate(next.effective_from)}
                          </p>
                        ) : null}
                      </Td>
                    );
                  })}
                  <Td>
                    <Badge tone={STATUS[p.status][0]}>{STATUS[p.status][1]}</Badge>
                  </Td>
                  <Td className="text-right">
                    <div className="flex flex-wrap justify-end gap-2">
                      {p.status !== "archived" ? (
                        <>
                          <Button size="sm" variant="secondary" onClick={() => setEditing(p)}>
                            Details
                          </Button>
                          <Button size="sm" variant="secondary" onClick={() => setPricing(p.id)}>
                            Prices
                          </Button>
                        </>
                      ) : null}
                      <Button size="sm" variant="secondary" onClick={() => setPreview(p.id)}>
                        Preview
                      </Button>
                      {p.status === "draft" ? (
                        <Button size="sm" onClick={() => setChanging({ plan: p, action: "publish" })}>
                          Publish
                        </Button>
                      ) : null}
                      {p.status !== "archived" ? (
                        <Button size="sm" variant="secondary" onClick={() => setChanging({ plan: p, action: "archive" })}>
                          Archive
                        </Button>
                      ) : (
                        <Button size="sm" variant="secondary" onClick={() => setChanging({ plan: p, action: "restore" })}>
                          Restore
                        </Button>
                      )}
                    </div>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <EmptyState title="No plans yet" body="Create a plan, price it, preview it, then publish it." />
        )}
      </Card>
      <NoticeSettings />
      {editing ? <PlanDialog plan={editing === "new" ? null : editing} onClose={() => setEditing(null)} /> : null}
      {byId(pricing) ? <PricesDialog plan={byId(pricing) as Plan} onClose={() => setPricing(null)} /> : null}
      {preview ? <PreviewDialog planId={preview} onClose={() => setPreview(null)} /> : null}
      {changing ? <StatusDialog {...changing} onClose={() => setChanging(null)} /> : null}
    </>
  );
}

function PlanDialog({ plan, onClose }: { plan: Plan | null; onClose: () => void }) {
  const { api } = useSession();
  const currencies = useCurrencies();
  const [f, setF] = useState({
    code: "",
    name: plan?.name ?? "",
    currency: plan?.currency ?? "",
    short_description: plan?.short_description ?? "",
    description: plan?.description ?? "",
    highlights: (plan?.highlights ?? []).join("\n"),
    display_order: String(plan?.display_order ?? 0),
    recommended: plan?.recommended ?? false,
    setup_fee: plan ? toAmountInput(plan.setup_fee) : "",
    trial_days: String(plan?.trial_days ?? 0),
    tax_treatment: plan?.tax_treatment ?? "exclusive",
    support_level: plan?.support_level ?? "",
    overage_policy: plan?.overage_policy ?? "",
    can_upgrade: plan?.can_upgrade ?? true,
    can_downgrade: plan?.can_downgrade ?? true,
    promo_percent: plan ? String(plan.promo_discount_bp / 100) : "0",
    promo_ends_on: plan?.promo_ends_on ?? "",
    reason: "",
  });
  const [limits, setLimits] = useState<Record<string, string>>(
    Object.fromEntries(LIMITS.map((k) => [k, plan?.limits[k] !== undefined ? String(plan.limits[k]) : ""])),
  );
  const priced = !!plan && (Object.keys(plan.prices).length > 0 || plan.history.length > 0 || plan.scheduled.length > 0);
  const currency = f.currency || "ZAR";
  const setup = f.setup_fee.trim() === "" ? 0 : parseAmount(f.setup_fee, currency);
  const promoBp = Math.round(Number(f.promo_percent.replace(",", ".") || "0") * 100);
  const limitValues = Object.fromEntries(Object.entries(limits).filter(([, v]) => v !== "").map(([k, v]) => [k, Number(v)]));
  const fields = {
    name: f.name,
    short_description: f.short_description || null,
    description: f.description || null,
    highlights: f.highlights
      .split("\n")
      .map((h) => h.trim())
      .filter(Boolean),
    display_order: Number(f.display_order) || 0,
    recommended: f.recommended,
    setup_fee_minor: setup ?? 0,
    trial_days: Number(f.trial_days) || 0,
    tax_treatment: f.tax_treatment,
    support_level: f.support_level || null,
    overage_policy: f.overage_policy || null,
    can_upgrade: f.can_upgrade,
    can_downgrade: f.can_downgrade,
    promo_discount_bp: promoBp,
    promo_ends_on: f.promo_ends_on || null,
    limits: limitValues,
  };
  const save = useAction(
    () =>
      plan
        ? ok(
            api.PATCH("/api/v1/admin/plans/{plan_id}", {
              params: { path: { plan_id: plan.id } },
              body: {
                ...fields,
                version: plan.version,
                ...(priced ? {} : { currency: f.currency }),
                reason: f.reason || null,
              },
            }),
          )
        : ok(api.POST("/api/v1/admin/plans", { body: { ...fields, code: f.code, currency: f.currency } })),
    { success: plan ? "Plan saved." : "Draft created. Give it a price next.", onDone: onClose },
  );
  const text = (key: keyof typeof f) => ({
    value: f[key] as string,
    onChange: (e: { target: { value: string } }) => setF({ ...f, [key]: e.target.value }),
  });
  const needsReason = plan?.status === "published";
  const valid =
    f.name.trim() &&
    f.currency &&
    setup !== null &&
    promoBp >= 0 &&
    promoBp <= 10000 &&
    (plan || /^[a-z][a-z0-9_]{1,40}$/.test(f.code)) &&
    (!needsReason || f.reason.trim().length >= 3);

  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title={plan ? `${plan.name}: details` : "New plan"}
      description={plan ? "Prices are changed under Prices." : "New plans start as drafts."}
      footer={
        <Button loading={save.isPending} disabled={!valid} onClick={() => save.mutate(undefined)}>
          {plan ? "Save" : "Create draft"}
        </Button>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {!plan ? (
          <Field label="Code" hint="Lowercase and permanent, e.g. boutique">
            {(p) => <Input {...p} {...text("code")} />}
          </Field>
        ) : null}
        <Field label="Name">{(p) => <Input {...p} {...text("name")} />}</Field>
        <Field label="Billing currency" hint={priced ? "Fixed once the plan has a price." : undefined}>
          {(p) => (
            <Select {...p} disabled={priced} {...text("currency")}>
              <option value="">Choose a currency</option>
              {currencies.data?.data.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} · {c.name}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Display order" hint="Lower comes first on the pricing page.">
          {(p) => <Input {...p} type="number" min={0} {...text("display_order")} />}
        </Field>
        <Field label="Short description" className="sm:col-span-2">
          {(p) => <Input {...p} maxLength={200} {...text("short_description")} />}
        </Field>
        <Field label="Full description" className="sm:col-span-2">
          {(p) => <Textarea {...p} rows={4} {...text("description")} />}
        </Field>
        <Field label="Included features" hint="One per line, shown on the pricing page." className="sm:col-span-2">
          {(p) => <Textarea {...p} rows={4} {...text("highlights")} />}
        </Field>
        <Field label={`One-time setup fee${f.currency ? ` (${currencySymbol(f.currency)})` : ""}`} hint="Empty or 0: none.">
          {(p) => <Input {...p} inputMode="decimal" {...text("setup_fee")} />}
        </Field>
        <Field label="Trial (days)" hint="0: no trial.">
          {(p) => <Input {...p} type="number" min={0} max={365} {...text("trial_days")} />}
        </Field>
        <Field label="Prices are">
          {(p) => (
            <Select {...p} {...text("tax_treatment")}>
              <option value="exclusive">Before VAT (VAT added when charged)</option>
              <option value="inclusive">Including VAT</option>
            </Select>
          )}
        </Field>
        <Field label="Support level">{(p) => <Input {...p} placeholder="e.g. Email, next business day" {...text("support_level")} />}</Field>
        <Field label="Overage policy" className="sm:col-span-2">
          {(p) => <Input {...p} placeholder="What happens above the limits" {...text("overage_policy")} />}
        </Field>
        <Field label="Promotional discount (%)">{(p) => <Input {...p} inputMode="decimal" {...text("promo_percent")} />}</Field>
        <Field label="Promotion ends on">{(p) => <Input {...p} type="date" {...text("promo_ends_on")} />}</Field>
        {LIMITS.map((k) => (
          <Field key={k} label={`Limit: ${k.replace("_", " ")}`} hint="Empty: no limit">
            {(p) => <Input {...p} type="number" min={0} value={limits[k]} onChange={(e) => setLimits({ ...limits, [k]: e.target.value })} />}
          </Field>
        ))}
        <div className="flex flex-col gap-2 text-sm sm:col-span-2">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={f.recommended} onChange={(e) => setF({ ...f, recommended: e.target.checked })} />
            Mark as recommended
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={f.can_upgrade} onChange={(e) => setF({ ...f, can_upgrade: e.target.checked })} />
            Hotels on this plan may upgrade
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={f.can_downgrade} onChange={(e) => setF({ ...f, can_downgrade: e.target.checked })} />
            Hotels on this plan may downgrade
          </label>
        </div>
        {needsReason ? (
          <Field label="Reason for this change" hint="The plan is published; kept in the audit log." className="sm:col-span-2">
            {(p) => <Input {...p} {...text("reason")} />}
          </Field>
        ) : null}
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

function PriceRow({ p, onWithdraw, busy }: { p: Price; onWithdraw?: () => void; busy?: boolean }) {
  return (
    <tr>
      <Td>{INTERVALS.find(([i]) => i === p.interval)?.[1]}</Td>
      <Td className="tabular-nums">
        {formatMoney(p.amount)}
        {p.interval !== "month" ? <span className="block text-xs text-muted">{formatMoney(p.per_month)} a month</span> : null}
        {p.intro_amount ? (
          <span className="block text-xs text-muted">
            {formatMoney(p.intro_amount)} for the first {p.intro_periods}
          </span>
        ) : null}
      </Td>
      <Td>{formatDate(p.effective_from)}</Td>
      <Td className="text-xs">
        {p.existing_policy === "next_renewal" ? `Existing hotels at renewal (${p.notice_days} days' notice)` : "New subscriptions only"}
        <span className="block text-muted">{p.reason}</span>
      </Td>
      <Td className="text-right">
        {onWithdraw ? (
          <Button size="sm" variant="secondary" loading={busy} onClick={onWithdraw}>
            Withdraw
          </Button>
        ) : null}
      </Td>
    </tr>
  );
}

function PricesDialog({ plan, onClose }: { plan: Plan; onClose: () => void }) {
  const { api } = useSession();
  const [f, setF] = useState({
    interval: "month" as Interval,
    amount: "",
    intro: "",
    intro_periods: "",
    when: "",
    policy: "new_only" as Price["existing_policy"],
    reason: "",
  });
  const amount = parseAmount(f.amount, plan.currency);
  const intro = f.intro.trim() ? parseAmount(f.intro, plan.currency) : null;
  const add = useAction(
    () =>
      ok(
        api.POST("/api/v1/admin/plans/{plan_id}/prices", {
          params: { path: { plan_id: plan.id } },
          body: {
            interval: f.interval,
            amount: { amount_minor: amount ?? 0, currency: plan.currency },
            intro_amount: intro !== null ? { amount_minor: intro, currency: plan.currency } : null,
            intro_periods: f.intro_periods ? Number(f.intro_periods) : null,
            effective_from: f.when ? new Date(f.when).toISOString() : null,
            existing_policy: f.policy,
            reason: f.reason,
          },
        }),
      ),
    { success: "Price saved.", onDone: () => setF({ ...f, amount: "", intro: "", intro_periods: "", when: "", reason: "" }) },
  );
  const withdraw = useAction(
    (id: string) =>
      ok(api.DELETE("/api/v1/admin/plans/{plan_id}/prices/{price_id}", { params: { path: { plan_id: plan.id, price_id: id } } })),
    { success: "Scheduled price withdrawn." },
  );
  const published = plan.status === "published";
  const current = INTERVALS.map(([i]) => plan.prices[i]).filter((p): p is Price => !!p);
  const head = (
    <thead>
      <tr>
        <Th>Interval</Th>
        <Th>Price</Th>
        <Th>From</Th>
        <Th>Applies to</Th>
        <Th />
      </tr>
    </thead>
  );
  return (
    <Dialog open onClose={onClose} size="lg" title={`${plan.name}: prices`} description={`Billed in ${plan.currency}. Prices already in force never change.`}>
      <div className="flex flex-col gap-5">
        <section>
          <h3 className="mb-2 text-sm font-semibold">In force</h3>
          {current.length ? (
            <Table>
              {head}
              <tbody>
                {current.map((p) => (
                  <PriceRow key={p.id} p={p} />
                ))}
              </tbody>
            </Table>
          ) : (
            <p className="text-sm text-muted">No price yet. A plan needs one before it can be published.</p>
          )}
        </section>
        {plan.scheduled.length ? (
          <section>
            <h3 className="mb-2 text-sm font-semibold">Scheduled</h3>
            <Table>
              {head}
              <tbody>
                {plan.scheduled.map((p) => (
                  <PriceRow key={p.id} p={p} busy={withdraw.isPending} onWithdraw={() => withdraw.mutate(p.id)} />
                ))}
              </tbody>
            </Table>
          </section>
        ) : null}
        <section className="grid gap-3 rounded-md border border-line p-4 sm:grid-cols-2">
          <h3 className="text-sm font-semibold sm:col-span-2">{published ? "Change a price" : "Set a price"}</h3>
          <Field label="Billing interval">
            {(p) => (
              <Select {...p} value={f.interval} onChange={(e) => setF({ ...f, interval: e.target.value as Interval })}>
                {INTERVALS.map(([i, n]) => (
                  <option key={i} value={i}>
                    {n}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label={`Price per ${f.interval} (${currencySymbol(plan.currency)})`}>
            {(p) => <Input {...p} inputMode="decimal" value={f.amount} onChange={(e) => setF({ ...f, amount: e.target.value })} />}
          </Field>
          <Field label="Introductory price (optional)">
            {(p) => <Input {...p} inputMode="decimal" value={f.intro} onChange={(e) => setF({ ...f, intro: e.target.value })} />}
          </Field>
          <Field label={`For how many ${f.interval}s`}>
            {(p) => (
              <Input {...p} type="number" min={1} max={36} value={f.intro_periods} onChange={(e) => setF({ ...f, intro_periods: e.target.value })} />
            )}
          </Field>
          {published ? (
            <>
              <Field label="Starts" hint="Empty: at once, for new subscriptions.">
                {(p) => <Input {...p} type="datetime-local" value={f.when} onChange={(e) => setF({ ...f, when: e.target.value })} />}
              </Field>
              <Field label="Existing subscribers">
                {(p) => (
                  <Select {...p} value={f.policy} onChange={(e) => setF({ ...f, policy: e.target.value as Price["existing_policy"] })}>
                    <option value="new_only">Keep their price (new subscriptions only)</option>
                    <option value="next_renewal">Move at their next renewal after notice</option>
                  </Select>
                )}
              </Field>
            </>
          ) : null}
          <Field label="Reason" className="sm:col-span-2" hint="Kept in the audit log with the old and new price.">
            {(p) => <Input {...p} value={f.reason} onChange={(e) => setF({ ...f, reason: e.target.value })} />}
          </Field>
          <div className="sm:col-span-2">
            <Button
              loading={add.isPending}
              disabled={amount === null || (f.intro.trim() !== "" && (intro === null || !f.intro_periods)) || f.reason.trim().length < 3}
              onClick={() => add.mutate(undefined)}
            >
              Save price
            </Button>
            {add.error || withdraw.error ? <ErrorNotice error={add.error ?? withdraw.error} className="mt-3" /> : null}
          </div>
        </section>
        {plan.history.length ? (
          <section>
            <h3 className="mb-2 text-sm font-semibold">Earlier prices</h3>
            <Table>
              {head}
              <tbody>
                {plan.history.map((p) => (
                  <PriceRow key={p.id} p={p} />
                ))}
              </tbody>
            </Table>
          </section>
        ) : null}
      </div>
    </Dialog>
  );
}

function PreviewDialog({ planId, onClose }: { planId: string; onClose: () => void }) {
  const { api } = useSession();
  const q = useQuery({
    queryKey: ["plan-preview", planId],
    queryFn: () => ok(api.GET("/api/v1/admin/plans/{plan_id}/preview", { params: { path: { plan_id: planId } } })),
  });
  const p = q.data;
  return (
    <Dialog open onClose={onClose} title="Preview" description="How hotels see this plan on the pricing page.">
      {!p ? (
        q.error ? <ErrorNotice error={q.error} /> : <Skeleton className="h-60" />
      ) : (
        <Card className="p-5">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-display text-xl font-semibold">{p.name}</h3>
            {p.recommended ? <Badge tone="info">Recommended</Badge> : null}
          </div>
          {p.short_description ? <p className="mt-1 text-sm text-muted">{p.short_description}</p> : null}
          <div className="mt-4 flex flex-col gap-2">
            {p.prices.length ? (
              p.prices.map((pr) => (
                <div key={pr.interval} className="flex items-baseline justify-between gap-2">
                  <span className="text-sm">{INTERVALS.find(([i]) => i === pr.interval)?.[1]}</span>
                  <span className="text-right">
                    <span className="font-display text-lg font-semibold tabular-nums">{formatMoney(pr.amount)}</span>
                    {pr.saving_bp ? <Badge tone="good" className="ml-2">Save {Math.floor(pr.saving_bp / 100)}%</Badge> : null}
                    {pr.intro_amount ? (
                      <span className="block text-xs text-muted">
                        {formatMoney(pr.intro_amount)} for the first {pr.intro_periods}
                      </span>
                    ) : null}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">No price yet: this plan would not be listed.</p>
            )}
          </div>
          <p className="mt-2 text-xs text-muted">
            Prices {p.tax_treatment === "inclusive" ? "include" : "exclude"} VAT where it applies.
            {p.setup_fee.amount_minor ? ` One-time setup fee ${formatMoney(p.setup_fee)}.` : ""}
            {p.trial_days ? ` ${p.trial_days}-day free trial.` : ""}
            {p.promo_discount_bp ? ` ${p.promo_discount_bp / 100}% off until ${formatDate(p.promo_ends_on)}.` : ""}
          </p>
          {p.highlights.length ? (
            <ul className="mt-4 list-disc pl-5 text-sm">
              {p.highlights.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ul>
          ) : null}
          {p.description ? <p className="mt-4 whitespace-pre-line text-sm">{p.description}</p> : null}
          {p.support_level ? <p className="mt-3 text-xs text-muted">Support: {p.support_level}</p> : null}
        </Card>
      )}
    </Dialog>
  );
}

function StatusDialog({ plan, action, onClose }: { plan: Plan; action: "publish" | "archive" | "restore"; onClose: () => void }) {
  const { api } = useSession();
  const [reason, setReason] = useState("");
  const path = { params: { path: { plan_id: plan.id } }, body: { reason } };
  const run = useAction(
    () =>
      ok(
        action === "publish"
          ? api.POST("/api/v1/admin/plans/{plan_id}/publish", path)
          : action === "archive"
            ? api.POST("/api/v1/admin/plans/{plan_id}/archive", path)
            : api.POST("/api/v1/admin/plans/{plan_id}/restore", path),
      ),
    {
      success:
        action === "publish"
          ? "Published. Hotels can now choose this plan."
          : action === "archive"
            ? "Archived. Hotels already on it keep it."
            : "Restored as a draft.",
      onDone: onClose,
    },
  );
  const text = {
    publish: `Hotels will be able to subscribe to ${plan.name} at the prices in force (${planPriceLabel(plan)}). Check the preview first.`,
    archive: `${plan.name} disappears from the pricing page. Hotels already on it keep it and its price.`,
    restore: `${plan.name} comes back as a draft, invisible to hotels until published again.`,
  }[action];
  return (
    <Dialog
      open
      onClose={onClose}
      title={{ publish: "Publish plan", archive: "Archive plan", restore: "Restore plan" }[action]}
      description={text}
      footer={
        <Button loading={run.isPending} disabled={reason.trim().length < 3} onClick={() => run.mutate(undefined)}>
          {{ publish: "Publish", archive: "Archive", restore: "Restore" }[action]}
        </Button>
      }
    >
      <Field label="Reason" hint="Kept in the audit log.">
        {(p) => <Input {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}
      </Field>
      {run.error ? <ErrorNotice error={run.error} className="mt-3" /> : null}
    </Dialog>
  );
}

function NoticeSettings() {
  const { api } = useSession();
  const q = useQuery({ queryKey: ["billing-settings"], queryFn: () => ok(api.GET("/api/v1/admin/billing-settings")) });
  const [edit, setEdit] = useState<{ notice: string; trial: string; limits: Record<string, string> } | null>(null);
  const [reason, setReason] = useState("");
  const save = useAction(
    () => {
      if (!q.data || !edit) throw new Error("not loaded");
      return ok(
        api.PUT("/api/v1/admin/billing-settings", {
          body: {
            version: q.data.version,
            price_change_notice_days: Number(edit.notice),
            trial_days: Number(edit.trial),
            trial_limits: Object.fromEntries(
              Object.entries(edit.limits)
                .filter(([, v]) => v !== "")
                .map(([k, v]) => [k, Number(v)]),
            ),
            reason,
          },
        }),
      );
    },
    { success: "Saved. New trials and price changes use it; running trials keep their end date.", onDone: () => (setEdit(null), setReason("")) },
  );
  if (!q.data) return null;
  const current = edit ?? {
    notice: String(q.data.price_change_notice_days),
    trial: String(q.data.trial_days),
    limits: Object.fromEntries(LIMITS.map((k) => [k, q.data.trial_limits[k] !== undefined ? String(q.data.trial_limits[k]) : ""])),
  };
  const set = (patch: Partial<typeof current>) => setEdit({ ...current, ...patch });
  return (
    <Card className="mt-6">
      <CardHeader
        title="Trial and price-change policy"
        description="A new hotel starts a free trial without a plan. Notice applies when a new price reaches existing hotels at renewal."
      />
      <div className="grid gap-3 p-5 sm:grid-cols-3">
        <Field label="Free trial (days)">
          {(p) => <Input {...p} type="number" min={0} max={365} value={current.trial} onChange={(e) => set({ trial: e.target.value })} />}
        </Field>
        <Field label="Notice before a price change (days)">
          {(p) => <Input {...p} type="number" min={0} max={365} value={current.notice} onChange={(e) => set({ notice: e.target.value })} />}
        </Field>
        <span />
        {LIMITS.map((k) => (
          <Field key={k} label={`Trial limit: ${k.replace("_", " ")}`} hint="Empty: no limit">
            {(p) => (
              <Input
                {...p}
                type="number"
                min={0}
                value={current.limits[k]}
                onChange={(e) => set({ limits: { ...current.limits, [k]: e.target.value } })}
              />
            )}
          </Field>
        ))}
        <Field label="Reason" className="sm:col-span-2">
          {(p) => <Input {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}
        </Field>
        <div className="flex items-end">
          <Button loading={save.isPending} disabled={edit === null || reason.trim().length < 3} onClick={() => save.mutate(undefined)}>
            Save
          </Button>
        </div>
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mx-5 mb-5" /> : null}
    </Card>
  );
}
