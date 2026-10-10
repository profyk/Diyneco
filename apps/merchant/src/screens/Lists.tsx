"use client";

import { formatDate, formatMoney, formatTime, ok } from "@diyneco/api-client";
import { Badge, Card, EmptyState, ErrorNotice, Input, PageHeader, Select, Skeleton, Table, Td, Th } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useDeferredValue, useState } from "react";

import { isoDay, label } from "../common";
import { useSession } from "../session";

export function Guests() {
  const { api } = useSession();
  const [q, setQ] = useState("");
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
              </tr>
            </thead>
            <tbody>
              {guests.data.data.map((g) => (
                <tr key={g.id}>
                  <Td className="font-medium">
                    {g.anonymised ? <Badge>Anonymised</Badge> : g.name}
                  </Td>
                  <Td className="text-muted">{g.email ?? "–"}</Td>
                  <Td className="text-muted">{g.phone ?? "–"}</Td>
                  <Td className="text-muted">{formatDate(g.created_at)}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </>
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
