"use client";

import { formatDate, formatMoney, ok } from "@diyneco/api-client";
import { Badge, Card, EmptyState, ErrorNotice, Field, Input, PageHeader, propertyTypeLabel, Select, Skeleton, Table, Td, Th } from "@diyneco/shared-ui";
import { Flag } from "@diyneco/shared-ui/countries";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Fragment, useMemo, useState } from "react";

import { label } from "./common";
import { useSession } from "./session";

// Hotel owners and their properties (D86, D87): one login can own several hotels.

type Money = { amount_minor: number; currency: string };
const moneys = (m: Money[]) => (m.length ? m.map(formatMoney).join(" · ") : "–");

export function Owners() {
  const { api } = useSession();
  const q = useQuery({ queryKey: ["owners"], queryFn: () => ok(api.GET("/api/v1/admin/owners")) });
  const [search, setSearch] = useState("");
  const [show, setShow] = useState<"all" | "multi" | "paying" | "unverified">("all");
  const [open, setOpen] = useState<string | null>(null);

  const rows = useMemo(() => {
    const term = search.trim().toLowerCase();
    return (q.data?.data ?? []).filter(
      (o) =>
        (!term ||
          o.name.toLowerCase().includes(term) ||
          o.email.toLowerCase().includes(term) ||
          o.hotels.some((h) => h.name.toLowerCase().includes(term) || h.code.toLowerCase().includes(term))) &&
        (show === "all" ||
          (show === "multi" && o.hotels.length > 1) ||
          (show === "paying" && o.paying > 0) ||
          (show === "unverified" && !o.email_verified)),
    );
  }, [q.data, search, show]);

  if (q.isLoading) return <Skeleton className="h-96" />;
  if (q.error) return <ErrorNotice error={q.error} />;
  const all = q.data?.data ?? [];

  return (
    <>
      <PageHeader
        title="Owners"
        description={`${all.length} owners · ${all.filter((o) => o.hotels.length > 1).length} with several properties`}
      />
      <Card>
        <div className="flex flex-wrap items-end gap-3 border-b border-line p-4">
          <Field label="Search" className="min-w-64 flex-1">
            {(p) => <Input {...p} type="search" placeholder="Name, email, property or Hotel ID" value={search} onChange={(e) => setSearch(e.target.value)} />}
          </Field>
          <Field label="Show">
            {(p) => (
              <Select {...p} value={show} onChange={(e) => setShow(e.target.value as typeof show)}>
                <option value="all">All owners</option>
                <option value="multi">Several properties</option>
                <option value="paying">Paying</option>
                <option value="unverified">Email not confirmed</option>
              </Select>
            )}
          </Field>
          <p className="ml-auto pb-2 text-sm text-muted">{rows.length} shown</p>
        </div>
        {rows.length === 0 ? (
          <EmptyState title="No owners match" />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Owner</Th>
                <Th>Countries</Th>
                <Th className="text-right">Properties</Th>
                <Th className="text-right">Rooms</Th>
                <Th className="text-right">MRR</Th>
                <Th className="text-right">Processed, 30 days</Th>
                <Th>Last sign-in</Th>
              </tr>
            </thead>
            <tbody>
              {rows.map((o) => (
                <Fragment key={o.user_id}>
                  <tr className="cursor-pointer hover:bg-surface-2" onClick={() => setOpen(open === o.user_id ? null : o.user_id)}>
                    <Td>
                      <button type="button" className="text-left" aria-expanded={open === o.user_id}>
                        <span className="font-medium">{o.name}</span>
                        {!o.email_verified ? (
                          <Badge tone="warn" className="ml-2">
                            Email not confirmed
                          </Badge>
                        ) : null}
                        <span className="block text-xs text-muted">
                          {o.email}
                          {o.phone ? ` · ${o.phone}` : ""}
                        </span>
                      </button>
                    </Td>
                    <Td>
                      <span className="flex gap-1">
                        {o.countries.map((c) => (
                          <Flag key={c} code={c} title={c} className="h-3.5 w-5" />
                        ))}
                      </span>
                    </Td>
                    <Td className="text-right tabular-nums">
                      {o.hotels.length}
                      {o.paying ? <span className="text-muted"> ({o.paying} paying)</span> : null}
                    </Td>
                    <Td className="text-right tabular-nums">{o.rooms}</Td>
                    <Td className="text-right tabular-nums">{moneys(o.mrr)}</Td>
                    <Td className="text-right tabular-nums">{moneys(o.gmv_30d)}</Td>
                    <Td className="text-muted">{o.last_login_at ? formatDate(o.last_login_at) : "Never"}</Td>
                  </tr>
                  {open === o.user_id ? (
                    <tr>
                      <td colSpan={7} className="border-b border-line bg-surface-2 px-6 py-3">
                        <ul className="grid gap-2 sm:grid-cols-2">
                          {o.hotels.map((h) => (
                            <li key={h.id} className="rounded-lg border border-line bg-surface p-3 text-sm">
                              <Link href={`/hotels/${h.id}`} className="font-medium text-blue hover:underline">
                                {h.name}
                              </Link>{" "}
                              <span className="font-mono text-xs text-muted">{h.code}</span>
                              <p className="text-xs text-muted">
                                {propertyTypeLabel(h.property_type)} · {[h.city, h.province, h.country].filter(Boolean).join(", ")} ·{" "}
                                {h.rooms} rooms
                              </p>
                              <p className="mt-1 flex gap-1">
                                <Badge tone={h.status === "active" ? "good" : h.status === "pending_approval" ? "warn" : "crit"}>{label(h.status)}</Badge>
                                <Badge>{h.subscription_status ? `${h.plan_name ?? "Trial"} · ${label(h.subscription_status)}` : "No plan"}</Badge>
                              </p>
                            </li>
                          ))}
                        </ul>
                        <p className="mt-2 text-xs text-muted">Owner since {formatDate(o.created_at)}</p>
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </>
  );
}
