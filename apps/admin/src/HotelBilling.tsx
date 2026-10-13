"use client";

// One hotel's billing in the admin panel (DECISIONS D78, D79): Diyneco's invoices and credit
// notes to it, manual invoices for approved charges, bank transfers seen on the statement,
// refunds (always with a credit note) and resending. Amounts, tax and statuses come from the
// API; sensitive actions ask for the password again (step-up).

import { formatDate, formatMoney, ok, parseAmount, toAmountInput } from "@diyneco/api-client";
import { Badge, Button, Card, CardHeader, Dialog, EmptyState, ErrorNotice, Field, Input, Select, Table, Td, Textarea, Th } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { tone } from "./Billing";
import { isoDay, label, useAction } from "./common";
import { useSession } from "./session";

type Money = { amount_minor: number; currency: string };
type Inv = {
  id: string;
  number: string | null;
  kind: string;
  purpose: string;
  status: string;
  is_tax_invoice: boolean;
  total: Money;
  balance: Money;
  credited: Money;
  paid: Money;
  issued_at: string | null;
  due_on: string | null;
  has_pdf: boolean;
};
type Pay = { id: string; invoice_number: string | null; method: string; provider: string; test_mode: boolean; amount: Money; refunded: Money; reference: string | null; received_on: string; reconciliation_status?: string | null };

type Open =
  | { kind: "new" }
  | { kind: "void" | "credit"; inv: Inv }
  | { kind: "payment"; inv?: Inv }
  | { kind: "refund"; pay: Pay }
  | null;

export function HotelBilling({ hotelId, currency }: { hotelId: string; currency: string }) {
  const { api } = useSession();
  const path = { params: { path: { hotel_id: hotelId } } };
  const invoices = useQuery({ queryKey: ["admin-hotel-invoices", hotelId], queryFn: () => ok(api.GET("/api/v1/admin/hotels/{hotel_id}/invoices", path)) });
  const payments = useQuery({ queryKey: ["admin-hotel-payments", hotelId], queryFn: () => ok(api.GET("/api/v1/admin/hotels/{hotel_id}/payments", path)) });
  const [open, setOpen] = useState<Open>(null);
  const [error, setError] = useState<unknown>(null);
  const issue = useAction(
    (id: string) => ok(api.POST("/api/v1/admin/hotels/{hotel_id}/invoices/{invoice_id}/issue", { params: { path: { hotel_id: hotelId, invoice_id: id } } })),
    { success: (r) => `Issued ${r.number} and emailed it.` },
  );
  const send = useAction(
    (id: string) => ok(api.POST("/api/v1/admin/hotels/{hotel_id}/invoices/{invoice_id}/send", { params: { path: { hotel_id: hotelId, invoice_id: id } } })),
    { success: (r) => `Sent to ${r.recipients} recipient${r.recipients === 1 ? "" : "s"}.` },
  );
  const pdf = async (id: string) => {
    setError(null);
    try {
      const { url } = await ok(api.GET("/api/v1/admin/hotels/{hotel_id}/invoices/{invoice_id}/pdf", { params: { path: { hotel_id: hotelId, invoice_id: id } } }));
      window.open(url, "_blank", "noopener");
    } catch (e) {
      setError(e);
    }
  };
  const rows = (invoices.data?.data ?? []) as Inv[];
  const pays = (payments.data?.data ?? []) as Pay[];
  const openInvoices = rows.filter((i) => i.kind === "invoice" && ["issued", "partially_paid", "overdue"].includes(i.status) && i.balance.amount_minor > 0);
  return (
    <>
      <Card className="mt-6">
        <CardHeader
          title="Invoices and credit notes"
          description="Issued documents are permanent. Tax invoices are corrected with credit notes."
          actions={
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => setOpen({ kind: "payment" })} disabled={!openInvoices.length}>
                Record bank transfer
              </Button>
              <Button size="sm" onClick={() => setOpen({ kind: "new" })}>
                New invoice
              </Button>
            </div>
          }
        />
        {rows.length ? (
          <Table>
            <thead>
              <tr>
                <Th>Document</Th>
                <Th>Issued</Th>
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
                    <p className="font-medium">{i.number ?? "Draft"}</p>
                    <p className="text-xs text-muted">
                      {i.kind === "credit_note" ? "Credit note" : `${i.is_tax_invoice ? "Tax invoice" : "Invoice"} · ${label(i.purpose)}`}
                    </p>
                  </Td>
                  <Td>
                    {i.issued_at ? formatDate(i.issued_at) : ""}
                    {i.due_on ? <span className="block text-xs text-muted">due {formatDate(i.due_on)}</span> : null}
                  </Td>
                  <Td className="text-right tabular-nums">{formatMoney(i.total)}</Td>
                  <Td className="text-right tabular-nums">{i.kind === "invoice" && i.number ? formatMoney(i.balance) : ""}</Td>
                  <Td>
                    <Badge tone={tone(i.status)}>{label(i.status)}</Badge>
                  </Td>
                  <Td>
                    <div className="flex flex-wrap justify-end gap-1">
                      {i.status === "draft" ? (
                        <>
                          <Button size="sm" loading={issue.isPending} onClick={() => issue.mutate(i.id)}>
                            Issue
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => setOpen({ kind: "void", inv: i })}>
                            Discard
                          </Button>
                        </>
                      ) : null}
                      {i.kind === "invoice" && ["issued", "partially_paid", "overdue"].includes(i.status) && i.balance.amount_minor > 0 ? (
                        <Button size="sm" variant="secondary" onClick={() => setOpen({ kind: "payment", inv: i })}>
                          Record payment
                        </Button>
                      ) : null}
                      {i.kind === "invoice" && i.number && i.status !== "void" && i.status !== "credited" ? (
                        <Button size="sm" variant="secondary" onClick={() => setOpen({ kind: "credit", inv: i })}>
                          Credit
                        </Button>
                      ) : null}
                      {i.kind === "invoice" && !i.is_tax_invoice && ["issued", "overdue"].includes(i.status) && i.paid.amount_minor === 0 ? (
                        <Button size="sm" variant="ghost" onClick={() => setOpen({ kind: "void", inv: i })}>
                          Void
                        </Button>
                      ) : null}
                      {i.number ? (
                        <>
                          <Button size="sm" variant="ghost" loading={send.isPending} onClick={() => send.mutate(i.id)}>
                            Resend
                          </Button>
                          <Button size="sm" variant="ghost" disabled={!i.has_pdf} onClick={() => void pdf(i.id)}>
                            PDF
                          </Button>
                        </>
                      ) : null}
                    </div>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <EmptyState title="No invoices yet" />
        )}
        {[issue.error, send.error, error].map((e, n) => (e ? <ErrorNotice key={n} error={e} className="m-4" /> : null))}
      </Card>
      <Card className="mt-6">
        <CardHeader title="Payments" description="Money received from this hotel. Refunds always come with a credit note." />
        {pays.length ? (
          <Table>
            <thead>
              <tr>
                <Th>Received</Th>
                <Th>Invoice</Th>
                <Th>Method</Th>
                <Th>Reference</Th>
                <Th className="text-right">Amount</Th>
                <Th>Reconciliation</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {pays.map((p) => (
                <tr key={p.id}>
                  <Td>{formatDate(p.received_on)}</Td>
                  <Td>{p.invoice_number}</Td>
                  <Td>
                    {label(p.method)} {p.test_mode ? <Badge tone="warn">Test</Badge> : null}
                  </Td>
                  <Td className="text-xs text-muted">{p.reference ?? ""}</Td>
                  <Td className="text-right tabular-nums">
                    {formatMoney(p.amount)}
                    {p.refunded.amount_minor ? <span className="block text-xs text-muted">refunded {formatMoney(p.refunded)}</span> : null}
                  </Td>
                  <Td>{p.reconciliation_status ? <Badge tone={tone(p.reconciliation_status)}>{label(p.reconciliation_status)}</Badge> : null}</Td>
                  <Td className="text-right">
                    {p.refunded.amount_minor < p.amount.amount_minor ? (
                      <Button size="sm" variant="ghost" onClick={() => setOpen({ kind: "refund", pay: p })}>
                        Refund
                      </Button>
                    ) : null}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <EmptyState title="No payments yet" />
        )}
      </Card>
      {open?.kind === "new" ? <NewInvoice hotelId={hotelId} currency={currency} onClose={() => setOpen(null)} /> : null}
      {open?.kind === "void" || open?.kind === "credit" ? <Correct hotelId={hotelId} kind={open.kind} inv={open.inv} onClose={() => setOpen(null)} /> : null}
      {open?.kind === "payment" ? <RecordPayment hotelId={hotelId} invoices={openInvoices} initial={open.inv} onClose={() => setOpen(null)} /> : null}
      {open?.kind === "refund" ? <Refund hotelId={hotelId} pay={open.pay} onClose={() => setOpen(null)} /> : null}
    </>
  );
}

type Line = { description: string; quantity: string; unit: string };

function NewInvoice({ hotelId, currency, onClose }: { hotelId: string; currency: string; onClose: () => void }) {
  const { api } = useSession();
  const [lines, setLines] = useState<Line[]>([{ description: "", quantity: "1", unit: "" }]);
  const [inclusive, setInclusive] = useState(false);
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");
  const parsed = lines.map((l) => ({ ...l, minor: parseAmount(l.unit, currency), qty: Number(l.quantity) }));
  const valid = parsed.every((l) => l.description.trim() && l.minor !== null && l.qty >= 1) && reason.trim().length >= 3;
  const save = useAction(
    () =>
      ok(
        api.POST("/api/v1/admin/hotels/{hotel_id}/invoices", {
          params: { path: { hotel_id: hotelId } },
          body: {
            currency,
            prices_include_tax: inclusive,
            reason,
            notes: notes.trim() || null,
            lines: parsed.map((l) => ({ code: "charge", description: l.description.trim(), quantity: l.qty, unit_amount_minor: l.minor ?? 0, discount_minor: 0 })),
          },
        }),
      ),
    { success: "Draft saved. Check it, then issue it.", onDone: onClose },
  );
  const set = (i: number, patch: Partial<Line>) => setLines(lines.map((l, j) => (j === i ? { ...l, ...patch } : l)));
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title="New invoice"
      description={`For an approved charge, in ${currency}. Tax is worked out by the server from Diyneco's VAT position.`}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button disabled={!valid} loading={save.isPending} onClick={() => save.mutate(undefined)}>
            Save draft
          </Button>
        </>
      }
    >
      {lines.map((l, i) => (
        <div key={i} className="mb-2 grid grid-cols-[1fr_5rem_8rem] gap-2">
          <Field label={i === 0 ? "Description" : ""}>{(p) => <Input {...p} value={l.description} onChange={(e) => set(i, { description: e.target.value })} />}</Field>
          <Field label={i === 0 ? "Qty" : ""}>{(p) => <Input {...p} type="number" min={1} value={l.quantity} onChange={(e) => set(i, { quantity: e.target.value })} />}</Field>
          <Field label={i === 0 ? "Unit price" : ""}>{(p) => <Input {...p} inputMode="decimal" value={l.unit} onChange={(e) => set(i, { unit: e.target.value })} />}</Field>
        </div>
      ))}
      <Button size="sm" variant="ghost" onClick={() => setLines([...lines, { description: "", quantity: "1", unit: "" }])}>
        Add line
      </Button>
      <label className="mt-3 flex items-center gap-2 text-sm">
        <input type="checkbox" checked={inclusive} onChange={(e) => setInclusive(e.target.checked)} /> Prices include VAT
      </label>
      <Field label="Notes on the invoice" className="mt-3">
        {(p) => <Textarea {...p} value={notes} onChange={(e) => setNotes(e.target.value)} />}
      </Field>
      <Field label="Reason (who approved the charge)" className="mt-3">
        {(p) => <Input {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}
      </Field>
      {save.error ? <ErrorNotice error={save.error} className="mt-3" /> : null}
    </Dialog>
  );
}

function Correct({ hotelId, kind, inv, onClose }: { hotelId: string; kind: "void" | "credit"; inv: Inv; onClose: () => void }) {
  const { api } = useSession();
  const [reason, setReason] = useState("");
  const [amount, setAmount] = useState("");
  const minor = amount ? parseAmount(amount, inv.total.currency) : null;
  const path = { params: { path: { hotel_id: hotelId, invoice_id: inv.id } } };
  const save = useAction(
    () =>
      kind === "void"
        ? ok(api.POST("/api/v1/admin/hotels/{hotel_id}/invoices/{invoice_id}/void", { ...path, body: { reason } }))
        : ok(api.POST("/api/v1/admin/hotels/{hotel_id}/invoices/{invoice_id}/credit", { ...path, body: { reason, amount_minor: minor } })),
    { success: kind === "void" ? "Voided." : (r) => `Credit note ${r.number} issued.`, onDone: onClose },
  );
  const creditable = inv.total.amount_minor - inv.credited.amount_minor;
  return (
    <Dialog
      open
      onClose={onClose}
      title={kind === "void" ? (inv.number ? `Void ${inv.number}` : "Discard draft") : `Credit ${inv.number}`}
      description={
        kind === "void"
          ? "The number is never reused. Only unpaid plain invoices can be voided."
          : `Up to ${formatMoney({ ...inv.total, amount_minor: creditable })} (including tax). Leave the amount empty to credit all of it.`
      }
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="danger"
            disabled={reason.trim().length < 3 || (kind === "credit" && amount !== "" && minor === null)}
            loading={save.isPending}
            onClick={() => save.mutate(undefined)}
          >
            {kind === "void" ? "Void" : "Issue credit note"}
          </Button>
        </>
      }
    >
      {kind === "credit" ? (
        <Field label="Amount">{(p) => <Input {...p} inputMode="decimal" placeholder={toAmountInput({ ...inv.total, amount_minor: creditable })} value={amount} onChange={(e) => setAmount(e.target.value)} />}</Field>
      ) : null}
      <Field label="Reason" className="mt-3">
        {(p) => <Input {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}
      </Field>
      {save.error ? <ErrorNotice error={save.error} className="mt-3" /> : null}
    </Dialog>
  );
}

function RecordPayment({ hotelId, invoices, initial, onClose }: { hotelId: string; invoices: Inv[]; initial?: Inv; onClose: () => void }) {
  const { api } = useSession();
  const [invoiceId, setInvoiceId] = useState(initial?.id ?? invoices[0]?.id ?? "");
  const inv = invoices.find((i) => i.id === invoiceId);
  const [amount, setAmount] = useState(initial ? toAmountInput(initial.balance) : "");
  const [reference, setReference] = useState("");
  const [received, setReceived] = useState(isoDay());
  const [notes, setNotes] = useState("");
  const minor = inv ? parseAmount(amount, inv.balance.currency) : null;
  const save = useAction(
    () =>
      ok(
        api.POST("/api/v1/admin/hotels/{hotel_id}/payments", {
          params: { path: { hotel_id: hotelId } },
          body: { invoice_id: invoiceId, amount_minor: minor ?? 0, method: "eft", reference: reference.trim(), received_on: received, notes: notes.trim() || null },
        }),
      ),
    { success: "Payment recorded. The hotel gets a confirmation email.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title="Record a bank transfer"
      description="Only after you have seen the money on Diyneco's bank statement."
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button disabled={!inv || !minor || !reference.trim()} loading={save.isPending} onClick={() => save.mutate(undefined)}>
            Record payment
          </Button>
        </>
      }
    >
      <Field label="Invoice">
        {(p) => (
          <Select {...p} value={invoiceId} onChange={(e) => setInvoiceId(e.target.value)}>
            {invoices.map((i) => (
              <option key={i.id} value={i.id}>
                {i.number} · balance {formatMoney(i.balance)}
              </option>
            ))}
          </Select>
        )}
      </Field>
      <div className="mt-3 grid gap-3 sm:grid-cols-3">
        <Field label="Amount">{(p) => <Input {...p} inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} />}</Field>
        <Field label="Bank reference">{(p) => <Input {...p} value={reference} onChange={(e) => setReference(e.target.value)} />}</Field>
        <Field label="Received on">{(p) => <Input {...p} type="date" max={isoDay()} value={received} onChange={(e) => setReceived(e.target.value)} />}</Field>
      </div>
      <Field label="Notes" className="mt-3">
        {(p) => <Input {...p} value={notes} onChange={(e) => setNotes(e.target.value)} />}
      </Field>
      {save.error ? <ErrorNotice error={save.error} className="mt-3" /> : null}
    </Dialog>
  );
}

function Refund({ hotelId, pay, onClose }: { hotelId: string; pay: Pay; onClose: () => void }) {
  const { api } = useSession();
  const left = { ...pay.amount, amount_minor: pay.amount.amount_minor - pay.refunded.amount_minor };
  const [amount, setAmount] = useState(toAmountInput(left));
  const [reason, setReason] = useState("");
  const [reference, setReference] = useState("");
  const minor = parseAmount(amount, pay.amount.currency);
  const save = useAction(
    () =>
      ok(
        api.POST("/api/v1/admin/hotels/{hotel_id}/payments/{payment_id}/refund", {
          params: { path: { hotel_id: hotelId, payment_id: pay.id } },
          body: { amount_minor: minor ?? 0, reason, reference: reference.trim() || null },
        }),
      ),
    { success: (r) => `Refund recorded with credit note ${r.credit_note_number}.`, onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title="Refund"
      description={
        pay.provider === "sandbox"
          ? "A sandbox refund: no money moves."
          : "Make the refund first (bank transfer, or in the provider's dashboard), then record it here with its reference."
      }
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="danger" disabled={!minor || reason.trim().length < 3} loading={save.isPending} onClick={() => save.mutate(undefined)}>
            Refund {minor ? formatMoney({ ...pay.amount, amount_minor: minor }) : ""}
          </Button>
        </>
      }
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label={`Amount (up to ${formatMoney(left)})`}>{(p) => <Input {...p} inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} />}</Field>
        <Field label="Refund reference">{(p) => <Input {...p} value={reference} onChange={(e) => setReference(e.target.value)} />}</Field>
      </div>
      <Field label="Reason" className="mt-3">
        {(p) => <Input {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}
      </Field>
      {save.error ? <ErrorNotice error={save.error} className="mt-3" /> : null}
    </Dialog>
  );
}
