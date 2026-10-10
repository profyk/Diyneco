"use client";

import { ok } from "@diyneco/api-client";
import { Button, Card, cn, ErrorNotice, PageHeader, Skeleton } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { isoDay } from "../common";
import { useSession } from "../session";

const DAYS = 14;

function addDays(day: string, n: number): string {
  const d = new Date(`${day}T12:00:00`);
  d.setDate(d.getDate() + n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

const TONES: Record<string, string> = {
  reserved: "bg-blue/15 text-ink border-blue/40",
  checked_in: "bg-teal/20 text-ink border-teal/50",
  active: "bg-teal/20 text-ink border-teal/50",
  checkout_pending: "bg-warn/20 text-ink border-warn/50",
  checked_out: "bg-surface-2 text-muted border-line",
};

/** Rooms down the side, nights across: who is in which room over the next two weeks. */
export function Rack() {
  const { api } = useSession();
  const [start, setStart] = useState(isoDay());
  const end = addDays(start, DAYS - 1);
  const days = Array.from({ length: DAYS }, (_, i) => addDays(start, i));
  const rooms = useQuery({
    queryKey: ["rooms", "all"],
    queryFn: () => ok(api.GET("/api/v1/rooms", { params: { query: { limit: 200 } } })),
  });
  const stays = useQuery({
    queryKey: ["stays", "rack", start],
    queryFn: async () => {
      // Every stay overlapping the window, page by page (large hotels have many).
      const all = [];
      let cursor: string | undefined;
      for (let i = 0; i < 20; i++) {
        const page = await ok(api.GET("/api/v1/stays", { params: { query: { from: start, to: end, limit: 200, cursor } } }));
        all.push(...page.data);
        if (!page.next_cursor) break;
        cursor = page.next_cursor;
      }
      return all.filter((s) => s.status !== "cancelled");
    },
  });
  const today = isoDay();

  return (
    <>
      <PageHeader
        title="Room rack"
        description="Each row is a room; each column a night. Select a stay to open it."
        actions={
          <>
            <Button variant="secondary" onClick={() => setStart(addDays(start, -7))}>
              Previous week
            </Button>
            <Button variant="secondary" onClick={() => setStart(isoDay())}>
              Today
            </Button>
            <Button variant="secondary" onClick={() => setStart(addDays(start, 7))}>
              Next week
            </Button>
          </>
        }
      />
      {rooms.error || stays.error ? <ErrorNotice error={rooms.error ?? stays.error} className="mb-4" /> : null}
      {rooms.isLoading || stays.isLoading ? (
        <Skeleton className="h-80" />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[56rem] border-collapse text-xs">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 bg-surface px-3 py-2 text-left font-medium text-muted">Room</th>
                {days.map((d) => {
                  const date = new Date(`${d}T12:00:00`);
                  return (
                    <th key={d} className={cn("px-1 py-2 text-center font-medium", d === today ? "text-blue" : "text-muted")}>
                      {date.toLocaleDateString(undefined, { weekday: "short" })}
                      <br />
                      {date.getDate()}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {rooms.data?.data.map((r) => {
                const mine = (stays.data ?? []).filter((s) => s.room.id === r.id);
                const cells: React.ReactNode[] = [];
                for (let i = 0; i < DAYS; ) {
                  const night = days[i]!;
                  const stay = mine.find((s) => s.arrival_date <= night && s.departure_date > night);
                  if (!stay) {
                    cells.push(<td key={night} className="border-l border-line/60" />);
                    i += 1;
                    continue;
                  }
                  let span = 1;
                  while (i + span < DAYS && stay.departure_date > days[i + span]!) span += 1;
                  cells.push(
                    <td key={night} colSpan={span} className="border-l border-line/60 p-0.5">
                      <Link
                        href={`/stays/${stay.id}`}
                        title={`${stay.guest.name} · ${stay.arrival_date} to ${stay.departure_date}`}
                        className={cn("block truncate rounded border px-2 py-1 font-medium hover:opacity-80", TONES[stay.status] ?? TONES.reserved)}
                      >
                        {stay.guest.name}
                      </Link>
                    </td>,
                  );
                  i += span;
                }
                return (
                  <tr key={r.id} className="border-t border-line">
                    <th scope="row" className="sticky left-0 z-10 bg-surface px-3 py-1.5 text-left font-semibold text-ink">
                      {r.number}
                      <span className="ml-1 font-normal text-muted">{r.room_type.name}</span>
                    </th>
                    {cells}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
        <span className="flex items-center gap-1"><span className={cn("size-3 rounded border", TONES.reserved)} /> Reserved</span>
        <span className="flex items-center gap-1"><span className={cn("size-3 rounded border", TONES.active)} /> In house</span>
        <span className="flex items-center gap-1"><span className={cn("size-3 rounded border", TONES.checkout_pending)} /> Checking out</span>
        <span className="flex items-center gap-1"><span className={cn("size-3 rounded border", TONES.checked_out)} /> Checked out</span>
      </div>
    </>
  );
}
