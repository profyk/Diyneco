"use client";

import { formatMoney, ok, parseAmount } from "@diyneco/api-client";
import {
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
  Th,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { label, RoomStatus, useAction } from "../common";
import { useSession } from "../session";

const STATUSES = ["available", "cleaning", "maintenance", "out_of_service", "reserved"] as const;
type SettableStatus = (typeof STATUSES)[number];

export function Rooms() {
  const { api, can } = useSession();
  const [filter, setFilter] = useState("");
  const [dialog, setDialog] = useState<null | "room" | "range" | "type">(null);
  const rooms = useQuery({
    queryKey: ["rooms", "all"],
    queryFn: () => ok(api.GET("/api/v1/rooms", { params: { query: { limit: 200 } } })),
  });
  const types = useQuery({ queryKey: ["room-types"], queryFn: () => ok(api.GET("/api/v1/room-types")) });
  const setStatus = useAction(
    ({ id, status }: { id: string; status: SettableStatus }) =>
      ok(api.POST("/api/v1/rooms/{room_id}/status", { params: { path: { room_id: id } }, body: { status } })),
    { success: "Room status updated." },
  );
  const list = (rooms.data?.data ?? []).filter((r) => !filter || r.status === filter);
  const counts = (rooms.data?.data ?? []).reduce<Record<string, number>>((acc, r) => {
    acc[r.status] = (acc[r.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <>
      <PageHeader
        title="Rooms"
        description="Housekeeping status at a glance. Occupied rooms change only through check-in and checkout."
        actions={
          can("rooms.manage") ? (
            <>
              <Button variant="secondary" onClick={() => setDialog("type")}>
                Add room type
              </Button>
              <Button variant="secondary" onClick={() => setDialog("range")}>
                Add a range
              </Button>
              <Button onClick={() => setDialog("room")}>Add room</Button>
            </>
          ) : null
        }
      />
      <div className="mb-4 flex flex-wrap gap-1">
        {["", "available", "occupied", "reserved", "cleaning", "maintenance", "out_of_service"].map((s) => (
          <button
            key={s || "all"}
            onClick={() => setFilter(s)}
            className={cn(
              "rounded-full px-3 py-1.5 text-sm font-medium",
              filter === s ? "bg-brand text-on-brand" : "bg-surface text-ink hover:bg-surface-2",
            )}
          >
            {s ? label(s) : "All"} {s ? (counts[s] ?? 0) : (rooms.data?.data.length ?? 0)}
          </button>
        ))}
      </div>
      {setStatus.error ? <ErrorNotice error={setStatus.error} className="mb-4" /> : null}
      {rooms.isLoading ? (
        <Skeleton className="h-40" />
      ) : list.length === 0 ? (
        <Card>
          <EmptyState
            title={rooms.data?.data.length ? "No rooms with this status" : "No rooms yet"}
            body={rooms.data?.data.length ? undefined : "Add a room type, then add rooms one by one or as a range (101–120)."}
          />
        </Card>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {list.map((r) => (
            <Card key={r.id} className="flex flex-col gap-2 p-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-display text-xl font-semibold text-ink">{r.number}</p>
                  <p className="text-xs text-muted">
                    {r.room_type.name}
                    {r.floor ? ` · Floor ${r.floor}` : ""}
                  </p>
                </div>
                <RoomStatus status={r.status} />
              </div>
              <p className="text-xs text-muted">{formatMoney(r.effective_rate)} a night</p>
              {r.status === "occupied" ? (
                <Link className="text-sm text-blue hover:underline" href="/stays">
                  View stay
                </Link>
              ) : can("rooms.status") ? (
                <Select
                  aria-label={`Status of room ${r.number}`}
                  value={r.status}
                  onChange={(e) => setStatus.mutate({ id: r.id, status: e.target.value as SettableStatus })}
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {label(s)}
                    </option>
                  ))}
                </Select>
              ) : null}
            </Card>
          ))}
        </div>
      )}
      <Card className="mt-8">
        <CardHeader title="Room types" description="A type's rate is the default nightly rate for its rooms." />
        <Table>
          <thead>
            <tr>
              <Th>Name</Th>
              <Th>Rooms</Th>
              <Th>Sleeps</Th>
              <Th className="text-right">Rate</Th>
            </tr>
          </thead>
          <tbody>
            {types.data?.data.map((t) => (
              <tr key={t.id}>
                <Td>{t.name}</Td>
                <Td>{t.room_count}</Td>
                <Td>{t.capacity}</Td>
                <Td className="text-right tabular-nums">{formatMoney(t.base_rate)}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
      {dialog === "type" ? <TypeDialog onClose={() => setDialog(null)} /> : null}
      {dialog === "room" || dialog === "range" ? (
        <RoomDialog range={dialog === "range"} types={types.data?.data ?? []} onClose={() => setDialog(null)} />
      ) : null}
    </>
  );
}

function TypeDialog({ onClose }: { onClose: () => void }) {
  const { api } = useSession();
  const [name, setName] = useState("");
  const [rate, setRate] = useState("");
  const [capacity, setCapacity] = useState("2");
  const minor = parseAmount(rate);
  const save = useAction(
    () =>
      ok(
        api.POST("/api/v1/room-types", {
          body: { name: name.trim(), base_rate: { amount_minor: minor ?? 0, currency: "ZAR" }, capacity: Number(capacity) },
        }),
      ),
    { success: "Room type added.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title="Add room type"
      footer={
        <Button disabled={!name.trim() || minor === null} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Add
        </Button>
      }
    >
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Name" className="sm:col-span-3">
          {(p) => <Input {...p} placeholder="Deluxe King" value={name} onChange={(e) => setName(e.target.value)} />}
        </Field>
        <Field label="Nightly rate (R)" className="sm:col-span-2">
          {(p) => <Input {...p} inputMode="decimal" value={rate} onChange={(e) => setRate(e.target.value)} />}
        </Field>
        <Field label="Sleeps">{(p) => <Input {...p} type="number" min={1} value={capacity} onChange={(e) => setCapacity(e.target.value)} />}</Field>
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

function RoomDialog({
  range,
  types,
  onClose,
}: {
  range: boolean;
  types: { id: string; name: string }[];
  onClose: () => void;
}) {
  const { api } = useSession();
  const [typeId, setTypeId] = useState(types[0]?.id ?? "");
  const [number, setNumber] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [prefix, setPrefix] = useState("");
  const [floor, setFloor] = useState("");
  const save = useAction(
    async () =>
      range
        ? ok(
            api.POST("/api/v1/rooms/bulk", {
              body: {
                ranges: [{ room_type_id: typeId, from: Number(from), to: Number(to), prefix, floor: floor || null }],
              },
            }),
          ).then((r) => r.created)
        : ok(api.POST("/api/v1/rooms", { body: { room_type_id: typeId, number: number.trim(), floor: floor || null } })).then(() => 1),
    { success: (n) => (n === 1 ? "Room added." : `${n} rooms added.`), onDone: onClose },
  );
  const valid = typeId && (range ? Number(from) > 0 && Number(to) >= Number(from) : number.trim());
  return (
    <Dialog
      open
      onClose={onClose}
      title={range ? "Add a range of rooms" : "Add a room"}
      description={range ? "For example 101 to 120 on floor 1. Numbers that exist already are refused." : undefined}
      footer={
        <Button disabled={!valid} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Add
        </Button>
      }
    >
      {types.length === 0 ? (
        <p className="text-sm text-muted">Add a room type first.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Room type" className="sm:col-span-2">
            {(p) => (
              <Select {...p} value={typeId} onChange={(e) => setTypeId(e.target.value)}>
                {types.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          {range ? (
            <>
              <Field label="From">{(p) => <Input {...p} type="number" value={from} onChange={(e) => setFrom(e.target.value)} />}</Field>
              <Field label="To">{(p) => <Input {...p} type="number" value={to} onChange={(e) => setTo(e.target.value)} />}</Field>
              <Field label="Prefix (optional)" hint="e.g. A for A101">
                {(p) => <Input {...p} value={prefix} onChange={(e) => setPrefix(e.target.value)} />}
              </Field>
            </>
          ) : (
            <Field label="Room number">{(p) => <Input {...p} value={number} onChange={(e) => setNumber(e.target.value)} />}</Field>
          )}
          <Field label="Floor (optional)">{(p) => <Input {...p} value={floor} onChange={(e) => setFloor(e.target.value)} />}</Field>
        </div>
      )}
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}
