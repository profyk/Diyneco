"use client";

import { formatDate, formatMoney, formatTime, ok } from "@diyneco/api-client";
import {
  Badge,
  Button,
  Card,
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
  useToast,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useDeferredValue, useState } from "react";

import { isoDay, label, useAction } from "../common";
import { useSession } from "../session";

export function Guests() {
  const { api, can } = useSession();
  const privacy = can("privacy.manage");
  const [q, setQ] = useState("");
  const [forgetting, setForgetting] = useState<{ id: string; name: string } | null>(null);
  const [idFor, setIdFor] = useState<{ id: string; name: string; has: boolean } | null>(null);
  const settings = useQuery({
    queryKey: ["settings", "id-numbers"],
    queryFn: () => ok(api.GET("/api/v1/hotel/settings")),
    enabled: can("settings.read"),
  });
  const idNumbers = Boolean(settings.data?.guest_id_number_enabled) && can("guests.manage");
  const query = useDeferredValue(q.trim());
  const guests = useQuery({
    queryKey: ["guests", query],
    queryFn: () => ok(api.GET("/api/v1/guests", { params: { query: { q: query || undefined, limit: 50 } } })),
  });
  return (
    <>
      <PageHeader title="Guests" description="Personal details are protected (POPIA): only roles that need them can see them." />
      <Input
        type="search"
        aria-label="Search guests"
        placeholder="Search by name, email or phone"
        className="mb-4 max-w-md"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <Card>
        {guests.isLoading ? (
          <Skeleton className="m-5 h-10" />
        ) : guests.error ? (
          <ErrorNotice error={guests.error} className="m-5" />
        ) : !guests.data?.data.length ? (
          <EmptyState title={query ? "No guests match" : "No guests yet"} />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Name</Th>
                <Th>Email</Th>
                <Th>Phone</Th>
                <Th>First stay</Th>
                {privacy ? <Th className="text-right">Personal data</Th> : null}
              </tr>
            </thead>
            <tbody>
              {guests.data.data.map((g) => (
                <tr key={g.id}>
                  <Td className="font-medium">
                    {g.anonymised ? <Badge>Anonymised</Badge> : g.name}
                    {g.has_id_number ? <Badge className="ml-2">ID on file</Badge> : null}
                  </Td>
                  <Td className="text-muted">{g.email ?? "–"}</Td>
                  <Td className="text-muted">{g.phone ?? "–"}</Td>
                  <Td className="text-muted">{formatDate(g.created_at)}</Td>
                  {privacy ? (
                    <Td className="text-right whitespace-nowrap">
                      {idNumbers && !g.anonymised ? (
                        <Button variant="ghost" size="sm" onClick={() => setIdFor({ id: g.id, name: g.name, has: g.has_id_number })}>
                          ID number
                        </Button>
                      ) : null}
                      <ExportButton guestId={g.id} />
                      {g.anonymised ? null : (
                        <Button variant="ghost" size="sm" onClick={() => setForgetting({ id: g.id, name: g.name })}>
                          Anonymise
                        </Button>
                      )}
                    </Td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
      {forgetting ? <AnonymiseDialog guest={forgetting} onClose={() => setForgetting(null)} /> : null}
      {idFor ? <IdNumberDialog guest={idFor} onClose={() => setIdFor(null)} /> : null}
    </>
  );
}

/** POPIA access request: downloads everything held on the guest as a JSON file (step-up). */
function ExportButton({ guestId }: { guestId: string }) {
  const { api } = useSession();
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  async function download() {
    setBusy(true);
    try {
      const data = await ok(api.GET("/api/v1/guests/{guest_id}/export", { params: { path: { guest_id: guestId } } }));
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `guest-data-${guestId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast("crit", e instanceof Error ? e.message : "The export failed.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <Button variant="ghost" size="sm" loading={busy} onClick={download}>
      Export
    </Button>
  );
}

function AnonymiseDialog({ guest, onClose }: { guest: { id: string; name: string }; onClose: () => void }) {
  const { api } = useSession();
  const [reason, setReason] = useState("");
  const run = useAction(
    () =>
      ok(
        api.POST("/api/v1/guests/{guest_id}/anonymise", {
          params: { path: { guest_id: guest.id } },
          body: { reason: reason.trim() },
        }),
      ),
    { success: "Guest anonymised.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title={`Anonymise ${guest.name}?`}
      description="Name, email, phone, ID number and order notes are removed for good. Amounts and issued tax invoices are kept as the law requires. This cannot be undone."
      footer={
        <Button variant="danger" disabled={reason.trim().length < 3} loading={run.isPending} onClick={() => run.mutate(undefined)}>
          Anonymise
        </Button>
      }
    >
      <Field label="Reason" hint="For example the guest's request by email, with the date.">
        {(p) => <Textarea {...p} rows={3} maxLength={300} value={reason} onChange={(e) => setReason(e.target.value)} />}
      </Field>
      {run.error ? <ErrorNotice error={run.error} className="mt-4" /> : null}
    </Dialog>
  );
}

export function Payments() {
  const { api } = useSession();
  const [method, setMethod] = useState<"" | "card_terminal" | "cash" | "eft">("");
  const [day, setDay] = useState(isoDay());
  const from = new Date(`${day}T00:00:00`).toISOString();
  const to = new Date(`${day}T23:59:59`).toISOString();
  const payments = useQuery({
    queryKey: ["payments", method, day],
    queryFn: () =>
      ok(api.GET("/api/v1/payments", { params: { query: { method: method || undefined, from, to, limit: 200 } } })),
  });
  return (
    <>
      <PageHeader title="Payments" description="Payments and tips recorded by staff. Tips are never hotel revenue." />
      <div className="mb-4 flex flex-wrap gap-3">
        <Input type="date" aria-label="Day" className="w-44" value={day} onChange={(e) => setDay(e.target.value)} />
        <Select aria-label="Method" className="w-48" value={method} onChange={(e) => setMethod(e.target.value as typeof method)}>
          <option value="">All methods</option>
          <option value="card_terminal">Card machine</option>
          <option value="cash">Cash</option>
          <option value="eft">EFT</option>
        </Select>
      </div>
      <Card>
        {payments.isLoading ? (
          <Skeleton className="m-5 h-10" />
        ) : !payments.data?.data.length ? (
          <EmptyState title="No payments on this day" />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Time</Th>
                <Th>Method</Th>
                <Th>For</Th>
                <Th className="text-right">Due</Th>
                <Th className="text-right">Received</Th>
                <Th className="text-right">Tip</Th>
                <Th>Status</Th>
              </tr>
            </thead>
            <tbody>
              {payments.data.data.map((p) => (
                <tr key={p.id}>
                  <Td className="text-muted">
                    {formatTime(p.occurred_at)}
                    {p.late_reason ? <Badge tone="warn" className="ml-2">Late entry</Badge> : null}
                  </Td>
                  <Td>{label(p.method)}</Td>
                  <Td className="text-muted">{p.order_id ? "Order" : "Bill"}</Td>
                  <Td className="text-right tabular-nums">{formatMoney(p.amount_due)}</Td>
                  <Td className="text-right tabular-nums">{formatMoney(p.amount_received)}</Td>
                  <Td className="text-right tabular-nums text-teal">{p.tip.amount_minor ? formatMoney(p.tip) : "–"}</Td>
                  <Td>
                    <Badge tone={p.status === "paid" ? "good" : "warn"}>{label(p.status)}</Badge>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </>
  );
}

/** Records or removes a guest's ID or passport number. It is stored encrypted and never shown again. */
function IdNumberDialog({ guest, onClose }: { guest: { id: string; name: string; has: boolean }; onClose: () => void }) {
  const { api } = useSession();
  const [value, setValue] = useState("");
  const valid = /^[A-Za-z0-9][A-Za-z0-9 -]{3,29}$/.test(value.trim());
  const save = useAction(
    (id_number: string | null) =>
      ok(api.PATCH("/api/v1/guests/{guest_id}", { params: { path: { guest_id: guest.id } }, body: { id_number } })),
    { success: (g) => (g.has_id_number ? "ID number saved." : "ID number removed."), onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title={`ID number for ${guest.name}`}
      description={
        guest.has
          ? "A number is on file. It is encrypted and appears only in a privacy export. Enter a new one to replace it."
          : "Stored encrypted. It is never shown on screen again and appears only in a privacy export."
      }
      footer={
        <>
          {guest.has ? (
            <Button variant="secondary" loading={save.isPending} onClick={() => save.mutate(null)}>
              Remove number
            </Button>
          ) : null}
          <Button disabled={!valid} loading={save.isPending} onClick={() => save.mutate(value.trim())}>
            Save
          </Button>
        </>
      }
    >
      <Field label="ID or passport number" hint="Letters, digits, spaces and hyphens; 4 to 30 characters.">
        {(p) => <Input {...p} autoComplete="off" spellCheck={false} value={value} onChange={(e) => setValue(e.target.value)} />}
      </Field>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}
