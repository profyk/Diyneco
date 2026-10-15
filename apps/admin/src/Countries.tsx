"use client";

import { formatDate, ok } from "@diyneco/api-client";
import { Badge, Button, Card, Dialog, EmptyState, ErrorNotice, Field, Input, PageHeader, Select, Skeleton, StatTile, Table, Td, Textarea, Th } from "@diyneco/shared-ui";
import { Flag } from "@diyneco/shared-ui/countries";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { useAction } from "./common";
import { useSession } from "./session";

// Operational countries (DECISIONS D84): every country Diyneco knows, and the ones where new
// properties can sign up. Switching needs a reason and a password confirmation, and is audited.

interface AdminCountry {
  code: string;
  name: string;
  currency: string;
  dial: string;
  region: string;
  timezones: string[];
  tax_label: string;
  tax_rate_bp: number | null;
  operational: boolean;
  enabled_at: string | null;
  hotels: number;
  active_hotels: number;
}

const REGIONS: Record<string, string> = {
  "af-south": "Africa",
  "eu-west": "Europe",
  "me-central": "Middle East",
  "ap-southeast": "Asia-Pacific",
  "us-east": "Americas",
};

type Show = "all" | "operational" | "closed" | "with-hotels";

export function Countries() {
  const { api } = useSession();
  const q = useQuery({ queryKey: ["admin-countries"], queryFn: () => ok(api.GET("/api/v1/admin/countries")) });
  const [search, setSearch] = useState("");
  const [region, setRegion] = useState("");
  const [show, setShow] = useState<Show>("all");
  const [target, setTarget] = useState<AdminCountry | null>(null);
  const [reason, setReason] = useState("");

  const all = useMemo(() => (q.data?.data ?? []) as AdminCountry[], [q.data]);
  const rows = useMemo(() => {
    const term = search.trim().toLowerCase();
    return all.filter(
      (c) =>
        (!term || c.name.toLowerCase().includes(term) || c.code.toLowerCase() === term || c.currency.toLowerCase() === term) &&
        (!region || c.region === region) &&
        (show === "all" ||
          (show === "operational" && c.operational) ||
          (show === "closed" && !c.operational) ||
          (show === "with-hotels" && c.hotels > 0)),
    );
  }, [all, search, region, show]);

  const toggle = useAction(
    () => {
      if (!target) throw new Error("no country");
      return ok(
        api.PUT("/api/v1/admin/countries/{code}", {
          params: { path: { code: target.code } },
          body: { operational: !target.operational, reason },
        }),
      );
    },
    {
      success: (c) =>
        c.operational ? `${c.name} is open: new properties there can sign up now.` : `Signups in ${c.name} are paused. Its hotels keep working.`,
      onDone: () => {
        setTarget(null);
        setReason("");
      },
    },
  );

  if (q.isLoading) return <Skeleton className="h-96" />;
  if (q.error) return <ErrorNotice error={q.error} />;

  const open = all.filter((c) => c.operational);
  const withHotels = all.filter((c) => c.hotels > 0);
  const hotelsInOpen = open.reduce((n, c) => n + c.hotels, 0);

  return (
    <>
      <PageHeader
        title="Countries"
        description="Choose where new properties can sign up. Properties already on Diyneco keep working whatever you choose."
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Open for signups" value={open.length} hint={`of ${all.length} countries`} tone="good" />
        <StatTile label="Countries with hotels" value={withHotels.length} />
        <StatTile label="Hotels in open countries" value={hotelsInOpen} />
        <StatTile
          label="Hotels in paused countries"
          value={withHotels.filter((c) => !c.operational).reduce((n, c) => n + c.hotels, 0)}
          hint="Still served; no new signups"
        />
      </div>

      <Card>
        <div className="flex flex-wrap items-end gap-3 border-b border-line p-4">
          <Field label="Search" className="min-w-56 flex-1">
            {(p) => <Input {...p} type="search" placeholder="Country, code or currency" value={search} onChange={(e) => setSearch(e.target.value)} />}
          </Field>
          <Field label="Region">
            {(p) => (
              <Select {...p} value={region} onChange={(e) => setRegion(e.target.value)}>
                <option value="">All regions</option>
                {Object.entries(REGIONS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Show">
            {(p) => (
              <Select {...p} value={show} onChange={(e) => setShow(e.target.value as Show)}>
                <option value="all">All countries</option>
                <option value="operational">Open for signups</option>
                <option value="closed">Not open</option>
                <option value="with-hotels">With hotels</option>
              </Select>
            )}
          </Field>
          <p className="ml-auto pb-2 text-sm text-muted">{rows.length} shown</p>
        </div>
        {rows.length === 0 ? (
          <EmptyState title="No countries match" body="Change the search or filters." />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Country</Th>
                <Th>Currency</Th>
                <Th>Dialling</Th>
                <Th>Region</Th>
                <Th>Tax</Th>
                <Th className="text-right">Hotels</Th>
                <Th>Signups</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.code}>
                  <Td>
                    <span className="flex items-center gap-2.5">
                      <Flag code={c.code} className="h-4 w-[1.35rem]" />
                      <span className="font-medium">{c.name}</span>
                      <span className="text-xs text-muted">{c.code}</span>
                    </span>
                  </Td>
                  <Td className="tabular-nums">{c.currency}</Td>
                  <Td className="tabular-nums text-muted">{c.dial}</Td>
                  <Td className="text-muted">{REGIONS[c.region] ?? c.region}</Td>
                  <Td className="text-muted">
                    {c.tax_label}
                    {c.tax_rate_bp != null ? ` ${c.tax_rate_bp / 100}%` : ""}
                  </Td>
                  <Td className="text-right tabular-nums">
                    {c.hotels ? (
                      <span title={`${c.active_hotels} active`}>
                        {c.hotels}
                        <span className="text-muted"> ({c.active_hotels} active)</span>
                      </span>
                    ) : (
                      <span className="text-muted">0</span>
                    )}
                  </Td>
                  <Td>
                    {c.operational ? (
                      <Badge tone="good" title={c.enabled_at ? `Since ${formatDate(c.enabled_at)}` : undefined}>
                        Open
                      </Badge>
                    ) : (
                      <Badge>Not open</Badge>
                    )}
                  </Td>
                  <Td className="text-right">
                    <Button size="sm" variant={c.operational ? "secondary" : "primary"} onClick={() => setTarget(c)}>
                      {c.operational ? "Pause signups" : "Open signups"}
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <Dialog
        open={target !== null}
        onClose={() => {
          setTarget(null);
          setReason("");
          toggle.reset();
        }}
        title={target ? `${target.operational ? "Pause signups in" : "Open signups in"} ${target.name}?` : ""}
        description={
          target?.operational
            ? `New properties in ${target.name} will no longer see it at signup. The ${target.hotels} hotel(s) already there keep working.`
            : target
              ? `Properties in ${target.name} will be able to register, billed in ${target.currency} with ${target.tax_label} defaults. Check that legal documents, tax and payments are ready there first.`
              : undefined
        }
        footer={
          <>
            <Button variant="ghost" onClick={() => setTarget(null)}>
              Cancel
            </Button>
            <Button
              variant={target?.operational ? "danger" : "primary"}
              loading={toggle.isPending}
              disabled={reason.trim().length < 3}
              onClick={() => toggle.mutate(undefined)}
            >
              {target?.operational ? "Pause signups" : "Open signups"}
            </Button>
          </>
        }
      >
        <Field label="Reason" hint="Recorded in the audit log.">
          {(p) => <Textarea {...p} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Launch approved by the board on 14 October" />}
        </Field>
        {toggle.error ? <ErrorNotice error={toggle.error} className="mt-3" /> : null}
      </Dialog>
    </>
  );
}
