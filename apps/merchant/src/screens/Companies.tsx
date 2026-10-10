"use client";

import { ok } from "@diyneco/api-client";
import { Button, Card, Dialog, EmptyState, ErrorNotice, Field, Input, PageHeader, Skeleton, Table, Td, Th } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useDeferredValue, useState } from "react";

import { useAction } from "../common";
import { useSession } from "../session";

/** Companies that are billed for their staff's stays (tax invoices carry their details). */
export function Companies() {
  const { api, can } = useSession();
  const [q, setQ] = useState("");
  const [adding, setAdding] = useState(false);
  const query = useDeferredValue(q.trim());
  const list = useQuery({
    queryKey: ["billing-profiles", query],
    queryFn: () => ok(api.GET("/api/v1/billing-profiles", { params: { query: { q: query || undefined, limit: 100 } } })),
  });
  return (
    <>
      <PageHeader
        title="Companies"
        description="Company details printed on tax invoices when a stay is billed to a company."
        actions={can("billing.manage") ? <Button onClick={() => setAdding(true)}>Add company</Button> : undefined}
      />
      <Input
        type="search"
        aria-label="Search companies"
        placeholder="Search by company name"
        className="mb-4 max-w-md"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <Card>
        {list.isLoading ? (
          <Skeleton className="m-5 h-10" />
        ) : list.error ? (
          <ErrorNotice error={list.error} className="m-5" />
        ) : !list.data?.data.length ? (
          <EmptyState title={query ? "No companies match" : "No companies yet"} body="Add a company before billing a stay to it." />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Company</Th>
                <Th>Registration no.</Th>
                <Th>VAT no.</Th>
                <Th>Accounts email</Th>
                <Th>Address</Th>
              </tr>
            </thead>
            <tbody>
              {list.data.data.map((c) => (
                <tr key={c.id}>
                  <Td className="font-medium">{c.company_name}</Td>
                  <Td className="text-muted">{c.registration_number ?? "–"}</Td>
                  <Td className="text-muted tabular-nums">{c.vat_number ?? "–"}</Td>
                  <Td className="text-muted">{c.billing_email ?? "–"}</Td>
                  <Td className="text-muted">{Object.values(c.billing_address).filter(Boolean).join(", ") || "–"}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
      {adding ? <CompanyDialog onClose={() => setAdding(false)} /> : null}
    </>
  );
}

const EMPTY = { company_name: "", registration_number: "", vat_number: "", billing_email: "", line1: "", line2: "", city: "", postal_code: "" };

export function CompanyDialog({ onClose, onCreated }: { onClose: () => void; onCreated?: (id: string) => void }) {
  const { api } = useSession();
  const [f, setF] = useState(EMPTY);
  const set = (k: keyof typeof EMPTY) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const vatOk = !f.vat_number.trim() || /^4\d{9}$/.test(f.vat_number.trim());
  const address = Object.fromEntries(
    (["line1", "line2", "city", "postal_code"] as const).map((k) => [k, f[k].trim()]).filter(([, v]) => v),
  );
  const save = useAction(
    () =>
      ok(
        api.POST("/api/v1/billing-profiles", {
          body: {
            company_name: f.company_name.trim(),
            registration_number: f.registration_number.trim() || null,
            vat_number: f.vat_number.trim() || null,
            billing_email: f.billing_email.trim() || null,
            billing_address: address,
          },
        }),
      ),
    {
      success: "Company added.",
      onDone: (c) => {
        onCreated?.(c.id);
        onClose();
      },
    },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title="Add company"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button disabled={!f.company_name.trim() || !vatOk} loading={save.isPending} onClick={() => save.mutate(undefined)}>
            Add company
          </Button>
        </>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Company name" className="sm:col-span-2">
          {(p) => <Input {...p} value={f.company_name} onChange={set("company_name")} />}
        </Field>
        <Field label="Registration number">{(p) => <Input {...p} value={f.registration_number} onChange={set("registration_number")} />}</Field>
        <Field label="VAT number" hint="10 digits starting with 4." error={vatOk ? undefined : "Enter a 10-digit VAT number starting with 4."}>
          {(p) => <Input {...p} inputMode="numeric" maxLength={10} value={f.vat_number} onChange={set("vat_number")} />}
        </Field>
        <Field label="Accounts email" className="sm:col-span-2">
          {(p) => <Input {...p} type="email" value={f.billing_email} onChange={set("billing_email")} />}
        </Field>
        <Field label="Address line 1">{(p) => <Input {...p} value={f.line1} onChange={set("line1")} />}</Field>
        <Field label="Address line 2">{(p) => <Input {...p} value={f.line2} onChange={set("line2")} />}</Field>
        <Field label="City">{(p) => <Input {...p} value={f.city} onChange={set("city")} />}</Field>
        <Field label="Postal code">{(p) => <Input {...p} value={f.postal_code} onChange={set("postal_code")} />}</Field>
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}
