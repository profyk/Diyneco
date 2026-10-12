"use client";

import { formatDate, ok } from "@diyneco/api-client";
import { Badge, Button, Card, CardHeader, ErrorNotice, Field, Input, PageHeader, Select, Skeleton, Table, Td, Textarea, Th } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { type ReactNode, useEffect, useState } from "react";

import { useAction } from "./common";
import { useSession } from "./session";

// Diyneco's company billing settings and tax rates (DECISIONS D72). Only verified details go
// in; empty fields stay empty. Every save needs a reason and a password confirmation.

type Address = { line1?: string | null; line2?: string | null; city?: string | null; province?: string | null; postal_code?: string | null; country?: string | null };
type Bank = {
  bank_name?: string | null;
  account_holder?: string | null;
  account_number?: string | null;
  branch_code?: string | null;
  account_type?: "cheque" | "current" | "savings" | "business" | null;
  swift_code?: string | null;
};

interface Settings {
  legal_name: string;
  trading_name: string;
  registration_number: string | null;
  country: string;
  currency: string;
  timezone: string;
  registered_address: Address;
  business_address: Address;
  billing_email: string | null;
  billing_phone: string | null;
  logo_url: string | null;
  vat_registered: boolean;
  vat_number: string | null;
  vat_effective_date: string | null;
  invoice_prefix: string;
  credit_note_prefix: string;
  number_padding: number;
  number_reset: "never" | "yearly";
  payment_terms_days: number;
  bank_details: Bank;
  payment_instructions: string | null;
  version: number;
  invoice_example: string;
  tax_today: { charged: boolean; tax_name: string | null; rate_bp: number | null };
  missing: string[];
}

const MISSING: Record<string, string> = {
  registration_number: "company registration number",
  registered_address: "registered address",
  billing_email: "billing email",
  payment_instructions: "bank details or payment instructions",
};

const clean = <T extends object>(o: T): T =>
  Object.fromEntries(Object.entries(o).map(([k, v]) => [k, typeof v === "string" && v.trim() === "" ? null : v])) as T;

export function Company() {
  const { api } = useSession();
  const q = useQuery({ queryKey: ["company"], queryFn: () => ok(api.GET("/api/v1/admin/company")) });
  const [f, setF] = useState<Settings | null>(null);
  const [reason, setReason] = useState("");
  useEffect(() => {
    if (q.data) setF(q.data as Settings);
  }, [q.data]);

  const save = useAction(
    () => {
      if (!f) throw new Error("not loaded");
      return ok(
        api.PUT("/api/v1/admin/company", {
          body: {
            version: f.version,
            reason,
            legal_name: f.legal_name,
            trading_name: f.trading_name,
            registration_number: f.registration_number || null,
            registered_address: clean(f.registered_address),
            business_address: clean(f.business_address),
            billing_email: f.billing_email || null,
            billing_phone: f.billing_phone || null,
            vat_registered: f.vat_registered,
            vat_number: f.vat_number || null,
            vat_effective_date: f.vat_effective_date || null,
            invoice_prefix: f.invoice_prefix,
            credit_note_prefix: f.credit_note_prefix,
            number_padding: f.number_padding,
            number_reset: f.number_reset,
            payment_terms_days: f.payment_terms_days,
            bank_details: clean(f.bank_details),
            payment_instructions: f.payment_instructions || null,
          },
        }),
      );
    },
    { success: "Saved. Invoices already issued keep the details they were issued with.", onDone: () => setReason("") },
  );

  if (q.isLoading || !f) return q.error ? <ErrorNotice error={q.error} /> : <Skeleton className="h-96" />;
  const set = (patch: Partial<Settings>) => setF({ ...f, ...patch });
  const text = (key: keyof Settings) => ({
    value: (f[key] as string | null) ?? "",
    onChange: (e: { target: { value: string } }) => set({ [key]: e.target.value } as Partial<Settings>),
  });

  return (
    <>
      <PageHeader
        title="Company & tax"
        description={`The seller on every subscription invoice. ${f.country} · ${f.currency} · ${f.timezone}.`}
      />
      {f.missing.length ? (
        <Card className="mb-4 border-warn/40 p-4 text-sm">
          Invoices will not show a {f.missing.map((m) => MISSING[m] ?? m).join(", ")} until you enter verified details.
        </Card>
      ) : null}
      <div className="flex flex-col gap-4">
        <Section title="Identity" description="Use the names and number exactly as registered with CIPC.">
          <Field label="Legal company name">{(p) => <Input {...p} {...text("legal_name")} />}</Field>
          <Field label="Trading name">{(p) => <Input {...p} {...text("trading_name")} />}</Field>
          <Field label="Company registration number" hint="CIPC format, e.g. 2026/123456/07.">
            {(p) => <Input {...p} {...text("registration_number")} />}
          </Field>
          <LogoField url={f.logo_url} />
        </Section>

        <Section title="Addresses">
          <AddressFields label="Registered address" value={f.registered_address} onChange={(a) => set({ registered_address: a })} />
          <AddressFields label="Business address" value={f.business_address} onChange={(a) => set({ business_address: a })} />
        </Section>

        <Section title="Billing contact">
          <Field label="Billing email">{(p) => <Input {...p} type="email" {...text("billing_email")} />}</Field>
          <Field label="Billing telephone">{(p) => <Input {...p} type="tel" {...text("billing_phone")} />}</Field>
        </Section>

        <Section
          title="VAT"
          description={
            f.tax_today.charged
              ? `Invoices issued today charge ${f.tax_today.tax_name} at ${(f.tax_today.rate_bp ?? 0) / 100}%.`
              : "Invoices issued today carry no VAT and are not tax invoices."
          }
        >
          <label className="flex items-center gap-2 text-sm sm:col-span-2">
            <input type="checkbox" checked={f.vat_registered} onChange={(e) => set({ vat_registered: e.target.checked })} />
            The company is registered for VAT
          </label>
          <Field label="VAT number" hint="10 digits starting with 4.">
            {(p) => <Input {...p} inputMode="numeric" {...text("vat_number")} />}
          </Field>
          <Field label="Registration effective from" hint="VAT is charged on invoices dated on or after this day.">
            {(p) => <Input {...p} type="date" {...text("vat_effective_date")} />}
          </Field>
        </Section>

        <Section title="Invoices" description={`The next invoice would be numbered like: ${f.invoice_example}.`}>
          <Field label="Invoice prefix">
            {(p) => <Input {...p} value={f.invoice_prefix} onChange={(e) => set({ invoice_prefix: e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "") })} />}
          </Field>
          <Field label="Credit note prefix">
            {(p) => (
              <Input {...p} value={f.credit_note_prefix} onChange={(e) => set({ credit_note_prefix: e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "") })} />
            )}
          </Field>
          <Field label="Digits in the number">
            {(p) => <Input {...p} type="number" min={4} max={10} value={f.number_padding} onChange={(e) => set({ number_padding: Number(e.target.value) })} />}
          </Field>
          <Field label="Numbering">
            {(p) => (
              <Select {...p} value={f.number_reset} onChange={(e) => set({ number_reset: e.target.value as Settings["number_reset"] })}>
                <option value="never">One running sequence</option>
                <option value="yearly">Restart every year (year in the number)</option>
              </Select>
            )}
          </Field>
          <Field label="Payment terms (days)">
            {(p) => (
              <Input {...p} type="number" min={0} max={90} value={f.payment_terms_days} onChange={(e) => set({ payment_terms_days: Number(e.target.value) })} />
            )}
          </Field>
        </Section>

        <Section title="Payment instructions" description="Printed on invoices for hotels paying by bank transfer.">
          <BankFields value={f.bank_details} onChange={(b) => set({ bank_details: b })} />
          <Field label="Instructions" className="sm:col-span-2" hint="E.g. use the invoice number as the payment reference.">
            {(p) => <Textarea {...p} rows={3} {...text("payment_instructions")} />}
          </Field>
        </Section>

        <Card className="p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <Field label="Reason for this change" className="flex-1" hint="Kept in the audit log with the old and new values.">
              {(p) => <Input {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}
            </Field>
            <Button loading={save.isPending} disabled={reason.trim().length < 3} onClick={() => save.mutate(undefined)}>
              Save
            </Button>
          </div>
          {save.error ? <ErrorNotice error={save.error} className="mt-3" /> : null}
        </Card>

        <TaxRates />
      </div>
    </>
  );
}

function Section({ title, description, children }: { title: string; description?: string; children: ReactNode }) {
  return (
    <Card>
      <CardHeader title={title} description={description} />
      <div className="grid gap-4 p-5 sm:grid-cols-2">{children}</div>
    </Card>
  );
}

function AddressFields({ label, value, onChange }: { label: string; value: Address; onChange: (a: Address) => void }) {
  const field = (key: keyof Address, name: string) => (
    <Field label={name}>{(p) => <Input {...p} value={value[key] ?? ""} onChange={(e) => onChange({ ...value, [key]: e.target.value })} />}</Field>
  );
  return (
    <fieldset className="flex flex-col gap-3">
      <legend className="mb-2 text-sm font-semibold text-ink">{label}</legend>
      {field("line1", "Street")}
      {field("line2", "Unit, building or suburb")}
      <div className="grid grid-cols-2 gap-3">
        {field("city", "City")}
        {field("postal_code", "Postal code")}
      </div>
      {field("province", "Province")}
    </fieldset>
  );
}

function BankFields({ value, onChange }: { value: Bank; onChange: (b: Bank) => void }) {
  const field = (key: Exclude<keyof Bank, "account_type">, name: string, numeric = false) => (
    <Field label={name}>
      {(p) => (
        <Input {...p} inputMode={numeric ? "numeric" : undefined} value={value[key] ?? ""} onChange={(e) => onChange({ ...value, [key]: e.target.value })} />
      )}
    </Field>
  );
  return (
    <>
      {field("bank_name", "Bank")}
      {field("account_holder", "Account holder")}
      {field("account_number", "Account number", true)}
      {field("branch_code", "Branch code", true)}
      <Field label="Account type">
        {(p) => (
          <Select {...p} value={value.account_type ?? ""} onChange={(e) => onChange({ ...value, account_type: (e.target.value || null) as Bank["account_type"] })}>
            <option value="">–</option>
            <option value="current">Current / cheque</option>
            <option value="savings">Savings</option>
            <option value="business">Business</option>
          </Select>
        )}
      </Field>
      {field("swift_code", "SWIFT code")}
    </>
  );
}

function LogoField({ url }: { url: string | null }) {
  const { api } = useSession();
  const upload = useAction(
    async (file: File) => {
      const target = await ok(
        api.POST("/api/v1/admin/company/logo", {
          body: { content_type: file.type as "image/png" | "image/jpeg", size_bytes: file.size },
        }),
      );
      const res = await fetch(target.upload_url, { method: target.method, headers: target.headers, body: file });
      if (!res.ok) throw new Error("The logo could not be uploaded. Try again.");
      return target;
    },
    { success: "Logo uploaded. New invoices print it." },
  );
  return (
    <div className="sm:col-span-2">
      <p className="mb-2 text-sm font-medium text-ink">Logo</p>
      <div className="flex flex-wrap items-center gap-4">
        {url ? <img src={url} alt="" className="h-14 max-w-40 rounded border border-line bg-white object-contain p-1" /> : null}
        <input
          type="file"
          accept="image/png,image/jpeg"
          className="text-sm"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) upload.mutate(file);
          }}
        />
      </div>
      <p className="mt-1 text-xs text-muted">PNG or JPEG, up to 1 MB.</p>
      {upload.error ? <ErrorNotice error={upload.error} className="mt-2" /> : null}
    </div>
  );
}

interface Rate {
  id: string;
  country: string;
  tax_name: string;
  category: string;
  rate_bp: number;
  effective_from: string;
  reason: string;
  in_force: boolean;
  scheduled: boolean;
}

function TaxRates() {
  const { api } = useSession();
  const q = useQuery({ queryKey: ["tax-rates"], queryFn: () => ok(api.GET("/api/v1/admin/tax-rates")) });
  const [n, setN] = useState({ country: "ZA", tax_name: "VAT", percent: "", effective_from: "", reason: "" });
  const bp = Math.round(Number(n.percent.replace(",", ".")) * 100);
  const schedule = useAction(
    () =>
      ok(
        api.POST("/api/v1/admin/tax-rates", {
          body: { country: n.country, tax_name: n.tax_name, rate_bp: bp, effective_from: n.effective_from, reason: n.reason },
        }),
      ),
    { success: "Rate scheduled. Invoices dated from that day use it.", onDone: () => setN({ ...n, percent: "", effective_from: "", reason: "" }) },
  );
  const withdraw = useAction(
    (id: string) => ok(api.DELETE("/api/v1/admin/tax-rates/{rate_id}", { params: { path: { rate_id: id } } })),
    { success: "Scheduled rate withdrawn." },
  );
  const rows = (q.data?.data ?? []) as Rate[];
  return (
    <Card>
      <CardHeader
        title="Tax rates"
        description="A rate already in force is never changed. Schedule a new rate from a future date; issued invoices keep theirs."
      />
      {q.isLoading ? (
        <Skeleton className="m-5 h-24" />
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Country</Th>
              <Th>Tax</Th>
              <Th>Rate</Th>
              <Th>From</Th>
              <Th>Reason</Th>
              <Th />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <Td>{r.country}</Td>
                <Td>{r.tax_name}</Td>
                <Td>{r.rate_bp / 100}%</Td>
                <Td>
                  {formatDate(r.effective_from)}{" "}
                  {r.in_force ? <Badge tone="good">In force</Badge> : r.scheduled ? <Badge tone="info">Scheduled</Badge> : <Badge>Replaced</Badge>}
                </Td>
                <Td className="max-w-xs text-xs text-muted">{r.reason}</Td>
                <Td className="text-right">
                  {r.scheduled ? (
                    <Button size="sm" variant="secondary" loading={withdraw.isPending} onClick={() => withdraw.mutate(r.id)}>
                      Withdraw
                    </Button>
                  ) : null}
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
      <div className="grid gap-3 border-t border-line p-5 sm:grid-cols-5 sm:items-end">
        <Field label="Country">
          {(p) => <Input {...p} maxLength={2} value={n.country} onChange={(e) => setN({ ...n, country: e.target.value.toUpperCase().replace(/[^A-Z]/g, "") })} />}
        </Field>
        <Field label="Tax name">{(p) => <Input {...p} value={n.tax_name} onChange={(e) => setN({ ...n, tax_name: e.target.value })} />}</Field>
        <Field label="Rate (%)">{(p) => <Input {...p} inputMode="decimal" value={n.percent} onChange={(e) => setN({ ...n, percent: e.target.value })} />}</Field>
        <Field label="From">{(p) => <Input {...p} type="date" value={n.effective_from} onChange={(e) => setN({ ...n, effective_from: e.target.value })} />}</Field>
        <Field label="Legal basis">{(p) => <Input {...p} value={n.reason} onChange={(e) => setN({ ...n, reason: e.target.value })} />}</Field>
        <div className="sm:col-span-5">
          <Button
            loading={schedule.isPending}
            disabled={!n.effective_from || n.reason.trim().length < 3 || !(bp >= 0 && bp <= 10000) || n.percent === ""}
            onClick={() => schedule.mutate(undefined)}
          >
            Schedule rate
          </Button>
          {schedule.error || withdraw.error ? <ErrorNotice error={schedule.error ?? withdraw.error} className="mt-3" /> : null}
        </div>
      </div>
    </Card>
  );
}
