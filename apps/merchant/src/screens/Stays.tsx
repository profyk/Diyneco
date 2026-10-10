"use client";

import { formatDate, formatMoney, ok } from "@diyneco/api-client";
import {
  Button,
  Card,
  cn,
  Dialog,
  EmptyState,
  ErrorNotice,
  Field,
  Badge,
  Input,
  PageHeader,
  Select,
  Skeleton,
  Table,
  Td,
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { isoDay, StayStatus, useAction } from "../common";
import { useSession } from "../session";
import { CompanyDialog } from "./Companies";

type StayRow = { arrival_date: string; departure_date: string };

// Dates are compared as YYYY-MM-DD strings in the hotel's local calendar.
const TABS: {
  key: string;
  title: string;
  query: { status: "active" | "reserved" | "checked_out"; from?: string; to?: string };
  keep?: (s: StayRow, today: string) => boolean;
}[] = [
  { key: "arrivals", title: "Arrivals today", query: { status: "reserved", from: isoDay(), to: isoDay() }, keep: (s, t) => s.arrival_date === t },
  { key: "inhouse", title: "In house", query: { status: "active" } },
  { key: "departures", title: "Departures today", query: { status: "active" }, keep: (s, t) => s.departure_date <= t },
  { key: "upcoming", title: "Reservations", query: { status: "reserved" }, keep: (s, t) => s.arrival_date >= t },
  { key: "noshow", title: "No-shows", query: { status: "reserved" }, keep: (s, t) => s.arrival_date < t },
  { key: "out", title: "Checked out", query: { status: "checked_out" } },
];

export function Stays() {
  const { api, can } = useSession();
  const [tab, setTab] = useState("arrivals");
  const [q, setQ] = useState("");
  const [form, setForm] = useState<null | "walkin" | "reservation">(null);
  const t = TABS.find((x) => x.key === tab) ?? TABS[0]!;
  const stays = useQuery({
    queryKey: ["stays", tab],
    queryFn: () => ok(api.GET("/api/v1/stays", { params: { query: { ...t.query, limit: 200 } } })),
  });
  const today = isoDay();
  const needle = q.trim().toLowerCase();
  const rows = (stays.data?.data ?? []).filter(
    (s) =>
      (!t.keep || t.keep(s, today)) &&
      (!needle || s.room.number.toLowerCase().includes(needle) || s.guest.name.toLowerCase().includes(needle)),
  );

  return (
    <>
      <PageHeader
        title="Stays & check-in"
        description="Check guests in and out, manage reservations and open their bills."
        actions={
          can("stays.manage") ? (
            <>
              <Button variant="secondary" onClick={() => setForm("reservation")}>
                New reservation
              </Button>
              <Button onClick={() => setForm("walkin")}>Walk-in check-in</Button>
            </>
          ) : null
        }
      />
      <div role="tablist" className="mb-4 flex flex-wrap gap-1">
        {TABS.map((x) => (
          <button
            key={x.key}
            role="tab"
            aria-selected={tab === x.key}
            onClick={() => setTab(x.key)}
            className={cn(
              "rounded-full px-3 py-1.5 text-sm font-medium",
              tab === x.key ? "bg-brand text-on-brand" : "bg-surface text-ink hover:bg-surface-2",
            )}
          >
            {x.title}
          </button>
        ))}
      </div>
      <Input
        type="search"
        aria-label="Find a stay"
        placeholder="Find by room or guest name"
        className="mb-4 max-w-md"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <Card>
        {stays.isLoading ? (
          <Skeleton className="m-5 h-10" />
        ) : stays.error ? (
          <ErrorNotice error={stays.error} className="m-5" />
        ) : !rows.length ? (
          <EmptyState title={needle ? "No stays match" : "No stays here"} />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Room</Th>
                <Th>Guest</Th>
                <Th>Dates</Th>
                <Th>Status</Th>
                <Th className="text-right">Balance</Th>
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.id} className="hover:bg-surface-2">
                  <Td className="font-medium">
                    <Link className="text-blue hover:underline" href={`/stays/${s.id}`}>
                      {s.room.number}
                    </Link>
                  </Td>
                  <Td>
                    {s.guest.name}
                    {s.billing_type === "company" ? <span className="ml-2 text-xs text-muted">Company</span> : null}
                    {s.is_training ? <span className="ml-2 text-xs text-warn">Training</span> : null}
                  </Td>
                  <Td className="text-muted">
                    {formatDate(s.arrival_date)} – {formatDate(s.departure_date)} · {s.nights} night{s.nights === 1 ? "" : "s"}
                  </Td>
                  <Td>
                    <StayStatus status={s.status} />
                    {s.status === "active" && s.departure_date < today ? <Badge tone="crit" className="ml-1">Overdue</Badge> : null}
                    {s.status === "active" && s.departure_date === today ? <Badge tone="warn" className="ml-1">Due out</Badge> : null}
                    {s.status === "reserved" && s.arrival_date < today ? <Badge tone="crit" className="ml-1">No-show</Badge> : null}
                    {s.charges_blocked ? <Badge tone="warn" className="ml-1">Charges stopped</Badge> : null}
                  </Td>
                  <Td className="text-right tabular-nums">{s.folio ? formatMoney(s.folio.balance) : "–"}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
      {form ? <StayForm kind={form} onClose={() => setForm(null)} /> : null}
    </>
  );
}

function StayForm({ kind, onClose }: { kind: "walkin" | "reservation"; onClose: () => void }) {
  const { api, can } = useSession();
  const router = useRouter();
  const [roomId, setRoomId] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [nights, setNights] = useState("1");
  const [arrival, setArrival] = useState(isoDay(1));
  const [departure, setDeparture] = useState(isoDay(2));
  const [company, setCompany] = useState("");
  const [newCompany, setNewCompany] = useState(false);
  const [po, setPo] = useState("");
  const [training, setTraining] = useState(false);

  const rooms = useQuery({
    queryKey: ["rooms", kind === "walkin" ? "available" : "all"],
    queryFn: () =>
      ok(
        api.GET("/api/v1/rooms", {
          params: { query: kind === "walkin" ? { status: "available", limit: 200 } : { limit: 200 } },
        }),
      ),
  });
  const profiles = useQuery({
    queryKey: ["billing-profiles"],
    queryFn: () => ok(api.GET("/api/v1/billing-profiles", { params: { query: { limit: 100 } } })),
    enabled: can("guests.read"),
  });

  const guest = { name: name.trim(), email: email.trim() || null, phone: phone.trim() || null };
  const billing = company
    ? { type: "company" as const, billing_profile_id: company, purchase_order: po.trim() || null, traveller_name: name.trim() }
    : { type: "personal" as const };

  const save = useAction(
    async () =>
      kind === "walkin"
        ? ok(
            api.POST("/api/v1/rooms/{room_id}/walk-in", {
              params: { path: { room_id: roomId } },
              body: { guest, nights: Number(nights), billing, training },
            }),
          )
        : ok(
            api.POST("/api/v1/stays", {
              body: { room_id: roomId, guest, arrival_date: arrival, departure_date: departure, billing, training },
            }),
          ),
    {
      success: kind === "walkin" ? "Checked in. The room's tablet is ready for the guest." : "Reservation saved.",
      onDone: (stay) => {
        onClose();
        router.push(`/stays/${stay.id}`);
      },
    },
  );

  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title={kind === "walkin" ? "Walk-in check-in" : "New reservation"}
      description={
        kind === "walkin"
          ? "Posts every night to the bill now and activates the room's tablet."
          : "Holds the room; check the guest in when they arrive."
      }
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button disabled={!roomId || !name.trim()} loading={save.isPending} onClick={() => save.mutate(undefined)}>
            {kind === "walkin" ? "Check in" : "Save reservation"}
          </Button>
        </>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Room" className="sm:col-span-2">
          {(p) => (
            <Select {...p} value={roomId} onChange={(e) => setRoomId(e.target.value)}>
              <option value="">{kind === "walkin" ? "Choose an available room" : "Choose a room"}</option>
              {rooms.data?.data.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.number} · {r.room_type.name} · {formatMoney(r.effective_rate)} a night
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Guest name">{(p) => <Input {...p} value={name} onChange={(e) => setName(e.target.value)} autoComplete="off" />}</Field>
        <Field label="Email (for the bill)">
          {(p) => <Input {...p} type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="off" />}
        </Field>
        <Field label="Phone">{(p) => <Input {...p} type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} autoComplete="off" />}</Field>
        {kind === "walkin" ? (
          <Field label="Nights">
            {(p) => <Input {...p} type="number" min={1} max={90} value={nights} onChange={(e) => setNights(e.target.value)} />}
          </Field>
        ) : (
          <>
            <Field label="Arrival">{(p) => <Input {...p} type="date" value={arrival} onChange={(e) => setArrival(e.target.value)} />}</Field>
            <Field label="Departure">{(p) => <Input {...p} type="date" value={departure} onChange={(e) => setDeparture(e.target.value)} />}</Field>
          </>
        )}
        <Field label="Bill to" hint="Company bills show the company, its VAT number and the order number.">
          {(p) => (
            <Select
              {...p}
              value={company}
              onChange={(e) => (e.target.value === "+new" ? setNewCompany(true) : setCompany(e.target.value))}
            >
              <option value="">The guest</option>
              {profiles.data?.data.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.company_name}
                </option>
              ))}
              {can("billing.manage") ? <option value="+new">New company…</option> : null}
            </Select>
          )}
        </Field>
        {newCompany ? <CompanyDialog onClose={() => setNewCompany(false)} onCreated={setCompany} /> : null}
        {company ? (
          <Field label="Company order number">{(p) => <Input {...p} value={po} onChange={(e) => setPo(e.target.value)} />}</Field>
        ) : null}
        <label className="flex items-center gap-2 text-sm text-ink sm:col-span-2">
          <input type="checkbox" checked={training} onChange={(e) => setTraining(e.target.checked)} />
          Training stay (excluded from reports)
        </label>
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}
