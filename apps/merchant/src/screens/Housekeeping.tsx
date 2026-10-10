"use client";

import { ok } from "@diyneco/api-client";
import { Badge, Button, Card, CardHeader, EmptyState, ErrorNotice, PageHeader, Skeleton, StatTile } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";

import { isoDay, label, useAction } from "../common";
import { useSession } from "../session";

type Room = { id: string; number: string; floor: string | null; status: string; room_type: { name: string } };

/**
 * The housekeeping list: rooms to clean (priority to those with a guest arriving today), rooms
 * in maintenance, and guests still due out today. One tap marks a room ready.
 */
export function Housekeeping() {
  const { api, can } = useSession();
  const today = isoDay();
  const rooms = useQuery({
    queryKey: ["rooms", "all"],
    queryFn: () => ok(api.GET("/api/v1/rooms", { params: { query: { limit: 200 } } })),
    refetchInterval: 30_000,
  });
  const arrivals = useQuery({
    queryKey: ["stays", "arrivals", today],
    queryFn: () => ok(api.GET("/api/v1/stays", { params: { query: { status: "reserved", from: today, to: today, limit: 200 } } })),
    enabled: can("stays.read"),
  });
  const inHouse = useQuery({
    queryKey: ["stays", "inhouse"],
    queryFn: () => ok(api.GET("/api/v1/stays", { params: { query: { status: "active", limit: 200 } } })),
    enabled: can("stays.read"),
  });
  const setStatus = useAction(
    ({ id, status }: { id: string; status: "available" | "cleaning" | "maintenance" }) =>
      ok(api.POST("/api/v1/rooms/{room_id}/status", { params: { path: { room_id: id } }, body: { status } })),
    { success: (r) => `Room ${r.number}: ${label(r.status)}.` },
  );
  const all = (rooms.data?.data ?? []) as Room[];
  const arrivingRooms = new Set((arrivals.data?.data ?? []).filter((s) => s.arrival_date === today).map((s) => s.room.id));
  const dueOut = (inHouse.data?.data ?? []).filter((s) => s.departure_date <= today);
  const byNumber = (a: Room, b: Room) => a.number.localeCompare(b.number, undefined, { numeric: true });
  const dirty = all.filter((r) => r.status === "cleaning").sort((a, b) => Number(arrivingRooms.has(b.id)) - Number(arrivingRooms.has(a.id)) || byNumber(a, b));
  const broken = all.filter((r) => r.status === "maintenance" || r.status === "out_of_service").sort(byNumber);
  const ready = all.filter((r) => r.status === "available").length;
  const canSet = can("rooms.status");

  const row = (r: Room, actions: React.ReactNode) => (
    <li key={r.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
      <div>
        <p className="font-display text-lg font-semibold text-ink">
          {r.number}{" "}
          {arrivingRooms.has(r.id) ? <Badge tone="warn">Guest arriving today</Badge> : null}
        </p>
        <p className="text-sm text-muted">
          {r.room_type.name}
          {r.floor ? ` · Floor ${r.floor}` : ""} · {label(r.status)}
        </p>
      </div>
      {canSet ? <div className="flex gap-2">{actions}</div> : null}
    </li>
  );

  return (
    <>
      <PageHeader title="Housekeeping" description="Rooms to turn around today. The list refreshes by itself." />
      {setStatus.error ? <ErrorNotice error={setStatus.error} className="mb-4" /> : null}
      {rooms.isLoading ? (
        <Skeleton className="h-60" />
      ) : (
        <>
          <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatTile label="To clean" value={String(dirty.length)} />
            <StatTile label="Needed for arrivals" value={String(dirty.filter((r) => arrivingRooms.has(r.id)).length)} />
            <StatTile label="Guests due out" value={String(dueOut.length)} />
            <StatTile label="Ready to sell" value={String(ready)} />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader title="To clean" description="Rooms with a guest arriving today come first." />
              {dirty.length ? (
                <ul className="divide-y divide-line">
                  {dirty.map((r) =>
                    row(
                      r,
                      <>
                        <Button size="lg" variant="success" loading={setStatus.isPending} onClick={() => setStatus.mutate({ id: r.id, status: "available" })}>
                          Clean and ready
                        </Button>
                        <Button size="lg" variant="ghost" onClick={() => setStatus.mutate({ id: r.id, status: "maintenance" })}>
                          Needs repair
                        </Button>
                      </>,
                    ),
                  )}
                </ul>
              ) : (
                <EmptyState title="Nothing to clean" />
              )}
            </Card>
            <div className="flex flex-col gap-6">
              <Card>
                <CardHeader title="Guests due out" description="These rooms need cleaning after checkout." />
                {dueOut.length ? (
                  <ul className="divide-y divide-line text-sm">
                    {dueOut.map((s) => (
                      <li key={s.id} className="flex items-center justify-between px-5 py-3">
                        <span className="font-medium text-ink">Room {s.room.number}</span>
                        {s.departure_date < today ? <Badge tone="crit">Overdue</Badge> : <Badge tone="warn">Today</Badge>}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <EmptyState title="No departures left today" />
                )}
              </Card>
              <Card>
                <CardHeader title="Maintenance" />
                {broken.length ? (
                  <ul className="divide-y divide-line">
                    {broken.map((r) =>
                      row(
                        r,
                        <Button variant="secondary" onClick={() => setStatus.mutate({ id: r.id, status: "cleaning" })}>
                          Fixed, needs cleaning
                        </Button>,
                      ),
                    )}
                  </ul>
                ) : (
                  <EmptyState title="All rooms in order" />
                )}
              </Card>
            </div>
          </div>
        </>
      )}
    </>
  );
}
