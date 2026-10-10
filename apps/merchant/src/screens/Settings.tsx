"use client";

import { currencySymbol, formatDate, formatTime, ok, parseAmount } from "@diyneco/api-client";
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
  Textarea,
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { label, useAction } from "../common";
import { useSession } from "../session";

type Tab = "hotel" | "billing" | "tablet" | "integrations" | "plan" | "support" | "audit";

export function Settings() {
  const { can } = useSession();
  const tabs: { key: Tab; title: string; show: boolean }[] = [
    { key: "hotel", title: "Hotel", show: can("hotel.read") },
    { key: "billing", title: "Billing & VAT", show: can("settings.read") },
    { key: "tablet", title: "Guest tablet", show: can("settings.read") },
    { key: "integrations", title: "Integrations", show: can("integrations.manage") },
    { key: "plan", title: "Plan", show: can("subscription.read") },
    { key: "support", title: "Diyneco support", show: can("audit.read") },
    { key: "audit", title: "Audit log", show: can("audit.read") },
  ];
  const visible = tabs.filter((t) => t.show);
  const [tab, setTab] = useState<Tab>(visible[0]?.key ?? "hotel");
  return (
    <>
      <PageHeader title="Settings" />
      <div role="tablist" className="mb-5 flex flex-wrap gap-1">
        {visible.map((t) => (
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
      {tab === "hotel" ? <HotelProfile /> : null}
      {tab === "billing" ? <BillingSettings /> : null}
      {tab === "tablet" ? <InfoPages /> : null}
      {tab === "integrations" ? <Integrations /> : null}
      {tab === "plan" ? <Plan /> : null}
      {tab === "support" ? <Support /> : null}
      {tab === "audit" ? <Audit /> : null}
    </>
  );
}

const MONEY_FIELDS = ["room_charge_auto_approve_limit", "room_service_fee", "abridged_invoice_max"] as const;

function withCurrency(patch: Record<string, unknown>, current: Record<string, unknown>): Record<string, unknown> {
  const currency = (patch.currency as string | undefined) ?? (current.currency as string);
  if (!patch.currency) return patch;
  const out = { ...patch };
  for (const f of MONEY_FIELDS) {
    const m = (patch[f] ?? current[f]) as { amount_minor: number } | undefined;
    if (m) out[f] = { amount_minor: m.amount_minor, currency };
  }
  return out;
}

async function withEtag<T>(r: Promise<{ data?: T; response: Response; error?: unknown }>) {
  const res = await r;
  const data = await ok(Promise.resolve(res));
  return { data, etag: res.response.headers.get("ETag") ?? "" };
}

const ADDRESS = [
  ["line1", "Street address"],
  ["line2", "Suburb or building"],
  ["city", "City or town"],
  ["province", "Province or region"],
  ["postal_code", "Postal code"],
] as const;
const LOGO_TYPES = ["image/png", "image/jpeg", "image/svg+xml"] as const;
const LOGO_MAX_BYTES = 2 * 1024 * 1024;

/** Upload through a signed address: the API issues it, the browser sends the file to storage. */
function LogoField({ logoUrl }: { logoUrl: string | null }) {
  const { api } = useSession();
  const [problem, setProblem] = useState<string | null>(null);
  const upload = useAction(
    async (file: File) => {
      const target = await ok(
        api.POST("/api/v1/hotel/logo", {
          body: { content_type: file.type as (typeof LOGO_TYPES)[number], size_bytes: file.size },
        }),
      );
      const res = await fetch(target.upload_url, { method: target.method, headers: target.headers, body: file });
      if (!res.ok) throw new Error("The logo could not be uploaded. Try again.");
      return target;
    },
    { success: "Logo uploaded. It appears on guest tablets and invoices." },
  );
  return (
    <div className="mt-6">
      <h3 className="mb-3 font-display text-sm font-semibold">Logo</h3>
      <div className="flex flex-wrap items-center gap-4">
        {logoUrl ? <img src={logoUrl} alt="" className="h-14 max-w-40 rounded border border-line bg-white object-contain p-1" /> : null}
        <input
          type="file"
          accept={LOGO_TYPES.join(",")}
          aria-label="Choose a logo"
          className="text-sm"
          onChange={(e) => {
            const file = e.target.files?.[0];
            e.target.value = "";
            if (!file) return;
            if (!(LOGO_TYPES as readonly string[]).includes(file.type) || file.size > LOGO_MAX_BYTES) {
              setProblem("Choose a PNG, JPEG or SVG file of 2 MB or less.");
              return;
            }
            setProblem(null);
            upload.mutate(file);
          }}
        />
        {upload.isPending ? <span className="text-sm text-muted">Uploading…</span> : null}
      </div>
      {problem ? <p className="mt-2 text-sm text-crit">{problem}</p> : null}
      {upload.error ? <ErrorNotice error={upload.error} className="mt-2" /> : null}
    </div>
  );
}

function HotelProfile() {
  const { api, can } = useSession();
  const hotel = useQuery({ queryKey: ["hotel"], queryFn: () => withEtag(api.GET("/api/v1/hotel")) });
  const [form, setForm] = useState<Record<string, string>>({});
  const h0 = () => hotel.data?.data;
  const save = useAction(
    () =>
      ok(
        api.PATCH("/api/v1/hotel", {
          params: { header: { "If-Match": hotel.data!.etag } as never },
          body: {
            ...(form.name !== undefined ? { name: form.name } : {}),
            ...(form.legal_name !== undefined ? { legal_name: form.legal_name || null } : {}),
            ...(form.phone !== undefined ? { phone: form.phone || null } : {}),
            ...(form.email !== undefined ? { email: form.email || null } : {}),
            ...(ADDRESS.some(([k]) => form[k] !== undefined)
              ? {
                  address: {
                    ...Object.fromEntries(ADDRESS.map(([k]) => [k, (form[k] ?? String(h0()?.address[k] ?? "")).trim() || null])),
                    country: (h0()?.address.country as string | undefined) ?? null,
                  },
                }
              : {}),
          },
        }),
      ),
    { success: "Hotel details saved.", onDone: () => setForm({}) },
  );
  if (!hotel.data) return <Skeleton className="h-40" />;
  const h = hotel.data.data;
  const value = (k: "name" | "legal_name" | "phone" | "email") => form[k] ?? h[k] ?? "";
  return (
    <Card className="max-w-2xl p-5">
      <div className="grid gap-4 sm:grid-cols-2">
        {(
          [
            ["name", "Trading name"],
            ["legal_name", "Registered name (on invoices)"],
            ["phone", "Phone"],
            ["email", "Email"],
          ] as const
        ).map(([k, l]) => (
          <Field key={k} label={l}>
            {(p) => <Input {...p} disabled={!can("hotel.update")} value={value(k)} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />}
          </Field>
        ))}
      </div>
      <h3 className="mt-6 mb-3 font-display text-sm font-semibold">Address (printed on tax invoices)</h3>
      <div className="grid gap-4 sm:grid-cols-2">
        {ADDRESS.map(([k, l]) => (
          <Field key={k} label={l} className={k === "line1" || k === "line2" ? "sm:col-span-2" : undefined}>
            {(p) => (
              <Input
                {...p}
                disabled={!can("hotel.update")}
                value={form[k] ?? String(h.address[k] ?? "")}
                onChange={(e) => setForm({ ...form, [k]: e.target.value })}
              />
            )}
          </Field>
        ))}
      </div>
      {can("hotel.update") ? <LogoField logoUrl={h.logo_url} /> : null}
      <p className="mt-4 text-sm text-muted">
        Status: <Badge tone={h.status === "active" ? "good" : "warn"}>{label(h.status)}</Badge>
      </p>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
      {can("hotel.update") ? (
        <div className="mt-4 flex justify-end">
          <Button disabled={Object.keys(form).length === 0} loading={save.isPending} onClick={() => save.mutate(undefined)}>
            Save
          </Button>
        </div>
      ) : null}
    </Card>
  );
}

function BillingSettings() {
  const { api, can } = useSession();
  const settings = useQuery({ queryKey: ["settings"], queryFn: () => withEtag(api.GET("/api/v1/hotel/settings")) });
  const currencies = useQuery({ queryKey: ["currencies"], queryFn: () => ok(api.GET("/api/v1/currencies")) });
  const [patch, setPatch] = useState<Record<string, unknown>>({});
  const save = useAction(
    () =>
      ok(
        api.PATCH("/api/v1/hotel/settings", {
          params: { header: { "If-Match": settings.data!.etag } as never },
          // Money fields always travel in the currency being saved.
          body: withCurrency(patch, settings.data!.data) as never,
        }),
      ),
    { success: "Settings saved.", onDone: () => setPatch({}) },
  );
  if (!settings.data) return <Skeleton className="h-40" />;
  const s = { ...settings.data.data, ...patch } as typeof settings.data.data;
  const editable = can("settings.update");
  const money = (key: string, current: { amount_minor: number; currency: string }) => (
    <Input
      inputMode="decimal"
      disabled={!editable}
      defaultValue={(current.amount_minor / 100).toFixed(2)}
      onChange={(e) => {
        const m = parseAmount(e.target.value);
        if (m !== null) setPatch({ ...patch, [key]: { amount_minor: m, currency: s.currency } });
      }}
    />
  );
  const toggle = (key: keyof typeof s, text: string) => (
    <label className="flex items-center gap-2 text-sm text-ink">
      <input type="checkbox" disabled={!editable} checked={Boolean(s[key])} onChange={(e) => setPatch({ ...patch, [key]: e.target.checked })} />
      {text}
    </label>
  );
  return (
    <Card className="max-w-3xl p-5">
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="flex flex-col gap-3 sm:col-span-2">
          {toggle("vat_registered", "The hotel is a registered VAT vendor (issues tax invoices)")}
          {toggle("accommodation_rates_include_vat", "Room rates include VAT")}
          {toggle("menu_prices_include_vat", "Menu prices include VAT")}
          {toggle("room_charging_enabled", "Guests may charge orders to their room")}
          {toggle("checkout_override_allowed", "Managers may check out a guest who still owes money")}
          {toggle("guest_id_number_enabled", "Record guests' ID or passport numbers (encrypted; only shown in a privacy export)")}
        </div>
        <Field
          label="Currency"
          hint="Prices, bills and reports use it. It can change only before the first guest is checked in or the first order is placed."
          className="sm:col-span-2"
        >
          {(p) => (
            <Select {...p} disabled={!editable} value={s.currency} onChange={(e) => setPatch({ ...patch, currency: e.target.value })}>
              {currencies.data?.data.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} · {c.name}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="VAT number">
          {(p) => (
            <Input {...p} disabled={!editable} value={(s.vat_number as string | null) ?? ""} onChange={(e) => setPatch({ ...patch, vat_number: e.target.value || null })} />
          )}
        </Field>
        <Field label="VAT rate (%)">
          {(p) => (
            <Input
              {...p}
              disabled={!editable}
              inputMode="decimal"
              defaultValue={(s.vat_rate_bp / 100).toString()}
              onChange={(e) => setPatch({ ...patch, vat_rate_bp: Math.round(Number(e.target.value) * 100) })}
            />
          )}
        </Field>
        <Field label={`Orders above this need a manager (${currencySymbol(s.currency)})`}>{() => money("room_charge_auto_approve_limit", s.room_charge_auto_approve_limit)}</Field>
        <Field label={`Room-service fee per order (${currencySymbol(s.currency)})`}>{() => money("room_service_fee", s.room_service_fee)}</Field>
        <Field label={`Abridged tax invoice limit (${currencySymbol(s.currency)})`} hint="Above this a full tax invoice with the guest's address is issued.">
          {() => money("abridged_invoice_max", s.abridged_invoice_max)}
        </Field>
        <Field label="Invoice prefix">
          {(p) => <Input {...p} disabled={!editable} value={s.invoice_prefix} onChange={(e) => setPatch({ ...patch, invoice_prefix: e.target.value })} />}
        </Field>
        <Field label="Room after checkout">
          {(p) => (
            <Select {...p} disabled={!editable} value={s.room_status_after_checkout} onChange={(e) => setPatch({ ...patch, room_status_after_checkout: e.target.value })}>
              <option value="cleaning">Needs cleaning</option>
              <option value="available">Available straight away</option>
            </Select>
          )}
        </Field>
        <Field label="Wi-Fi network shown to guests">
          {(p) => <Input {...p} disabled={!editable} value={(s.wifi_name as string | null) ?? ""} onChange={(e) => setPatch({ ...patch, wifi_name: e.target.value || null })} />}
        </Field>
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
      {editable ? (
        <div className="mt-5 flex justify-end">
          <Button disabled={Object.keys(patch).length === 0} loading={save.isPending} onClick={() => save.mutate(undefined)}>
            Save settings
          </Button>
        </div>
      ) : null}
    </Card>
  );
}

const SCOPES = ["rooms.read", "orders.read", "stays.read", "folio.read", "payments.read", "invoices.read", "reports.read", "menu.read", "rooms.status", "menu.availability"];
const EVENTS = ["NEW_ORDER", "ORDER_READY", "ORDER_DELIVERED", "ORDER_CANCELLED", "PAYMENT_UPDATED", "STAY_CHECKED_IN", "STAY_CHECKED_OUT", "STAY_MOVED", "FOLIO_UPDATED", "MENU_UPDATED"];

function Integrations() {
  const { api } = useSession();
  const keys = useQuery({ queryKey: ["api-keys"], queryFn: () => ok(api.GET("/api/v1/api-keys")) });
  const hooks = useQuery({ queryKey: ["webhooks"], queryFn: () => ok(api.GET("/api/v1/webhooks")) });
  const [dialog, setDialog] = useState<null | "key" | "hook">(null);
  const [secret, setSecret] = useState<{ title: string; value: string } | null>(null);
  const revoke = useAction((id: string) => ok(api.DELETE("/api/v1/api-keys/{key_id}", { params: { path: { key_id: id } } })), {
    success: "Key revoked.",
  });
  const test = useAction((id: string) => ok(api.POST("/api/v1/webhooks/{webhook_id}/test", { params: { path: { webhook_id: id } } })), {
    success: "Test event sent.",
  });
  const toggleHook = useAction(
    ({ id, status }: { id: string; status: "active" | "disabled" }) =>
      ok(api.POST("/api/v1/webhooks/{webhook_id}/status", { params: { path: { webhook_id: id } }, body: { status } })),
    { success: "Webhook updated." },
  );
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader
          title="API keys"
          description="For your PMS or accounting system. Sandbox keys only read."
          actions={<Button size="sm" onClick={() => setDialog("key")}>New key</Button>}
        />
        {keys.data?.data.length ? (
          <Table>
            <tbody>
              {keys.data.data.map((k) => (
                <tr key={k.id}>
                  <Td>
                    <p className="font-medium">{k.name}</p>
                    <p className="font-mono text-xs text-muted">{k.prefix}…</p>
                  </Td>
                  <Td>
                    <Badge tone={k.environment === "production" ? "info" : "neutral"}>{k.environment}</Badge>
                  </Td>
                  <Td className="text-muted">{k.last_used_at ? `Used ${formatDate(k.last_used_at)}` : "Never used"}</Td>
                  <Td className="text-right">
                    {k.status === "active" ? (
                      <Button size="sm" variant="ghost" onClick={() => revoke.mutate(k.id)}>
                        Revoke
                      </Button>
                    ) : (
                      <Badge tone="crit">Revoked</Badge>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <EmptyState title="No API keys" />
        )}
      </Card>
      <Card>
        <CardHeader
          title="Webhooks"
          description="We sign every delivery (Diyneco-Signature) and retry for 24 hours."
          actions={<Button size="sm" onClick={() => setDialog("hook")}>New webhook</Button>}
        />
        {hooks.data?.data.length ? (
          <Table>
            <tbody>
              {hooks.data.data.map((w) => (
                <tr key={w.id}>
                  <Td className="max-w-80 truncate font-mono text-xs">{w.url}</Td>
                  <Td className="text-xs text-muted">{w.events.join(", ")}</Td>
                  <Td>
                    <Badge tone={w.status === "active" ? "good" : "crit"}>{label(w.status)}</Badge>
                  </Td>
                  <Td className="whitespace-nowrap text-right">
                    <Button size="sm" variant="secondary" onClick={() => test.mutate(w.id)}>
                      Send test
                    </Button>{" "}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => toggleHook.mutate({ id: w.id, status: w.status === "active" ? "disabled" : "active" })}
                    >
                      {w.status === "active" ? "Turn off" : "Turn on"}
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <EmptyState title="No webhooks" />
        )}
      </Card>
      {revoke.error || test.error ? <ErrorNotice error={revoke.error ?? test.error} /> : null}
      {dialog ? (
        <IntegrationDialog
          kind={dialog}
          onClose={() => setDialog(null)}
          onSecret={(title, value) => {
            setDialog(null);
            setSecret({ title, value });
          }}
        />
      ) : null}
      {secret ? (
        <Dialog
          open
          onClose={() => setSecret(null)}
          title={secret.title}
          description="Copy it now. It is shown only once and cannot be recovered."
          footer={<Button onClick={() => setSecret(null)}>I have copied it</Button>}
        >
          <code className="block break-all rounded-lg bg-surface-2 p-3 font-mono text-sm">{secret.value}</code>
          <Button size="sm" variant="secondary" className="mt-3" onClick={() => void navigator.clipboard.writeText(secret.value)}>
            Copy
          </Button>
        </Dialog>
      ) : null}
    </div>
  );
}

function IntegrationDialog({
  kind,
  onClose,
  onSecret,
}: {
  kind: "key" | "hook";
  onClose: () => void;
  onSecret: (title: string, value: string) => void;
}) {
  const { api } = useSession();
  const [name, setName] = useState("");
  const [environment, setEnvironment] = useState<"sandbox" | "production">("sandbox");
  const [url, setUrl] = useState("https://");
  const [picked, setPicked] = useState<string[]>([]);
  const save = useAction(async () => {
    if (kind === "key") {
      const k = await ok(api.POST("/api/v1/api-keys", { body: { name: name.trim(), environment, scopes: picked } }));
      onSecret("Your new API key", k.secret);
    } else {
      const w = await ok(api.POST("/api/v1/webhooks", { body: { url: url.trim(), events: picked } }));
      onSecret("Webhook signing secret", w.signing_secret);
    }
  });
  const options = kind === "key" ? SCOPES : EVENTS;
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title={kind === "key" ? "New API key" : "New webhook"}
      footer={
        <Button
          disabled={picked.length === 0 || (kind === "key" ? !name.trim() : !url.startsWith("https://"))}
          loading={save.isPending}
          onClick={() => save.mutate(undefined)}
        >
          Create
        </Button>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {kind === "key" ? (
          <>
            <Field label="Name">{(p) => <Input {...p} value={name} onChange={(e) => setName(e.target.value)} />}</Field>
            <Field label="Environment">
              {(p) => (
                <Select {...p} value={environment} onChange={(e) => setEnvironment(e.target.value as "sandbox" | "production")}>
                  <option value="sandbox">Sandbox (read-only)</option>
                  <option value="production">Production</option>
                </Select>
              )}
            </Field>
          </>
        ) : (
          <Field label="HTTPS URL" className="sm:col-span-2">
            {(p) => <Input {...p} value={url} onChange={(e) => setUrl(e.target.value)} />}
          </Field>
        )}
      </div>
      <fieldset className="mt-4">
        <legend className="mb-2 text-sm font-medium">{kind === "key" ? "Permissions" : "Events"}</legend>
        <div className="flex flex-wrap gap-2">
          {options.map((o) => (
            <label key={o} className="flex items-center gap-2 rounded-full border border-line px-3 py-1 font-mono text-xs">
              <input type="checkbox" checked={picked.includes(o)} onChange={(e) => setPicked(e.target.checked ? [...picked, o] : picked.filter((x) => x !== o))} />
              {o}
            </label>
          ))}
        </div>
      </fieldset>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

function Plan() {
  const { api, can } = useSession();
  const sub = useQuery({ queryKey: ["subscription"], queryFn: () => ok(api.GET("/api/v1/subscription")) });
  const [plan, setPlan] = useState("professional");
  const request = useAction(() => ok(api.POST("/api/v1/subscription/change-request", { body: { plan_code: plan } })), {
    success: "Request sent. Diyneco will confirm the change.",
  });
  if (!sub.data) return <Skeleton className="h-40" />;
  const s = sub.data;
  return (
    <Card className="max-w-2xl p-5">
      <p className="font-display text-xl font-semibold">
        {(s.plan as { name?: string } | null)?.name ?? "No plan"} {s.status ? <Badge tone="good">{label(s.status)}</Badge> : null}
      </p>
      {s.renews_on ? <p className="mt-1 text-sm text-muted">Renews {formatDate(s.renews_on)}</p> : null}
      <Table className="mt-4">
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
      {can("subscription.manage") ? (
        <div className="mt-5 flex items-end gap-3">
          <Field label="Change plan to">
            {(p) => (
              <Select {...p} value={plan} onChange={(e) => setPlan(e.target.value)}>
                <option value="starter">Starter</option>
                <option value="professional">Professional</option>
                <option value="enterprise">Enterprise</option>
              </Select>
            )}
          </Field>
          <Button loading={request.isPending} onClick={() => request.mutate(undefined)}>
            Request change
          </Button>
        </div>
      ) : null}
      {request.error ? <ErrorNotice error={request.error} className="mt-3" /> : null}
    </Card>
  );
}

function Support() {
  const { api, can } = useSession();
  const grants = useQuery({ queryKey: ["support-access"], queryFn: () => ok(api.GET("/api/v1/support-access")) });
  const revoke = useAction(
    (id: string) => ok(api.POST("/api/v1/support-access/{grant_id}/revoke", { params: { path: { grant_id: id } } })),
    { success: "Support access ended." },
  );
  return (
    <Card>
      <CardHeader
        title="Diyneco support access"
        description="Support can open read-only access for up to an hour, with a ticket number. They never see guest details. You can end it at any time."
      />
      {grants.data?.data.length ? (
        <Table>
          <tbody>
            {grants.data.data.map((g) => (
              <tr key={g.id}>
                <Td className="font-mono">{g.ticket_reference}</Td>
                <Td className="text-muted">{g.reason ?? "–"}</Td>
                <Td className="text-muted">
                  {formatDate(g.starts_at)} {formatTime(g.starts_at)} – {formatTime(g.expires_at)}
                </Td>
                <Td className="text-right">
                  {g.active ? (
                    can("hotel.update") ? (
                      <Button size="sm" variant="danger" onClick={() => revoke.mutate(g.id)}>
                        End now
                      </Button>
                    ) : (
                      <Badge tone="warn">Active</Badge>
                    )
                  ) : (
                    <Badge>Ended</Badge>
                  )}
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      ) : (
        <EmptyState title="Support has never accessed this hotel" />
      )}
    </Card>
  );
}

function Audit() {
  const { api } = useSession();
  const [action, setAction] = useState("");
  const logs = useQuery({
    queryKey: ["audit", action],
    queryFn: () => ok(api.GET("/api/v1/audit-logs", { params: { query: { action: action || undefined, limit: 100 } } })),
  });
  return (
    <Card>
      <CardHeader
        title="Audit log"
        description="Every sensitive action: who, what, when and from where."
        actions={<Input placeholder="Filter by action, e.g. stay.check_out" value={action} onChange={(e) => setAction(e.target.value.trim())} className="w-72" />}
      />
      {logs.isLoading ? (
        <Skeleton className="m-5 h-10" />
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>When</Th>
              <Th>Who</Th>
              <Th>Action</Th>
              <Th>Details</Th>
            </tr>
          </thead>
          <tbody>
            {logs.data?.data.map((l) => (
              <tr key={l.id}>
                <Td className="whitespace-nowrap text-muted">
                  {formatDate(l.created_at)} {formatTime(l.created_at)}
                </Td>
                <Td>
                  {l.actor_label}
                  {l.actor_type !== "user" ? <Badge className="ml-1">{l.actor_type}</Badge> : null}
                </Td>
                <Td className="font-mono text-xs">{l.action}</Td>
                <Td className="max-w-96 truncate text-xs text-muted" title={JSON.stringify(l.new_value)}>
                  {l.reason ? `“${l.reason}” ` : ""}
                  {l.new_value ? JSON.stringify(l.new_value) : ""}
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </Card>
  );
}

type Page = { title: string; body: string };

/** Information pages on the guest tablet's "Hotel info" tab (breakfast times, spa, shuttle). */
function InfoPages() {
  const { api, can } = useSession();
  const settings = useQuery({ queryKey: ["settings"], queryFn: () => withEtag(api.GET("/api/v1/hotel/settings")) });
  const [draft, setDraft] = useState<Page[] | null>(null);
  const save = useAction(
    () =>
      ok(
        api.PATCH("/api/v1/hotel/settings", {
          params: { header: { "If-Match": settings.data!.etag } as never },
          body: { info_pages: (draft ?? []).map((p) => ({ title: p.title.trim(), body: p.body.trim() })) },
        }),
      ),
    { success: "Pages saved. Tablets show them now.", onDone: () => setDraft(null) },
  );
  if (!settings.data) return <Skeleton className="h-40" />;
  const pages = draft ?? settings.data.data.info_pages;
  const editable = can("settings.update");
  const update = (i: number, patch: Partial<Page>) => setDraft(pages.map((p, j) => (j === i ? { ...p, ...patch } : p)));
  const move = (i: number, by: -1 | 1) => {
    const next = [...pages];
    [next[i], next[i + by]] = [next[i + by]!, next[i]!];
    setDraft(next);
  };
  const valid = pages.every((p) => p.title.trim() && p.body.trim());
  return (
    <Card className="max-w-3xl p-5">
      <h2 className="font-display text-base font-semibold">Hotel information</h2>
      <p className="mt-1 text-sm text-muted">
        Pages guests read on the tablet&apos;s Hotel info tab, after the Wi-Fi name, check-out time and reception contacts. Up to 20 pages.
      </p>
      <div className="mt-5 flex flex-col gap-4">
        {pages.length === 0 ? <EmptyState title="No pages yet" body="Add breakfast times, facilities, transport or house rules." /> : null}
        {pages.map((p, i) => (
          <div key={i} className="rounded-lg border border-line p-4">
            <div className="grid gap-3">
              <Field label="Title">
                {(f) => <Input {...f} maxLength={80} disabled={!editable} value={p.title} onChange={(e) => update(i, { title: e.target.value })} />}
              </Field>
              <Field label="Text">
                {(f) => (
                  <Textarea {...f} rows={4} maxLength={4000} disabled={!editable} value={p.body} onChange={(e) => update(i, { body: e.target.value })} />
                )}
              </Field>
            </div>
            {editable ? (
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" variant="ghost" disabled={i === 0} onClick={() => move(i, -1)}>
                  Move up
                </Button>
                <Button size="sm" variant="ghost" disabled={i === pages.length - 1} onClick={() => move(i, 1)}>
                  Move down
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setDraft(pages.filter((_, j) => j !== i))}>
                  Remove
                </Button>
              </div>
            ) : null}
          </div>
        ))}
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
      {editable ? (
        <div className="mt-5 flex flex-wrap justify-between gap-2">
          <Button variant="secondary" disabled={pages.length >= 20} onClick={() => setDraft([...pages, { title: "", body: "" }])}>
            Add page
          </Button>
          <Button disabled={draft === null || !valid} loading={save.isPending} onClick={() => save.mutate(undefined)}>
            Save pages
          </Button>
        </div>
      ) : null}
    </Card>
  );
}
