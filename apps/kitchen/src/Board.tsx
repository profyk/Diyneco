"use client";

import { type components, elapsed, formatTime, ok } from "@diyneco/api-client";
import { Badge, Button, cn, EmptyState, useToast } from "@diyneco/shared-ui";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { cookApi } from "./api";

type Order = components["schemas"]["KitchenOrder"];
type Item = components["schemas"]["KitchenItem"];

const LATE_MIN = 15;
const VERY_LATE_MIN = 25;

function minutesSince(iso: string | null | undefined, now: number): number {
  return iso ? (now - new Date(iso).getTime()) / 60000 : 0;
}

function useNow(everyMs = 15_000): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), everyMs);
    return () => clearInterval(t);
  }, [everyMs]);
  return now;
}

/**
 * Three lanes, oldest first: New (accept), Accepted (start) and Preparing (mark items ready).
 * Prices never appear. Tickets turn amber after 15 minutes and red after 25.
 */
export function Board({
  orders,
  needCook,
}: {
  orders: Order[];
  /** Runs the action once a cook is signed in (opens the PIN pad if nobody is). */
  needCook: (action: () => void) => void;
}) {
  const now = useNow();
  const lanes: { key: string; title: string; statuses: string[] }[] = [
    { key: "new", title: "New", statuses: ["NEW"] },
    { key: "accepted", title: "Accepted", statuses: ["ACCEPTED"] },
    { key: "preparing", title: "Preparing", statuses: ["PREPARING"] },
  ];
  return (
    <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 overflow-hidden lg:grid-cols-3">
      {lanes.map((lane) => {
        const list = orders
          .filter((o) => lane.statuses.includes(o.status))
          .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        return (
          <section key={lane.key} aria-label={lane.title} className="flex min-h-0 flex-col">
            <h2 className="mb-3 flex items-center gap-2 font-display text-lg font-semibold text-ink">
              {lane.title}
              <span className="rounded-full bg-surface-2 px-2.5 py-0.5 text-sm text-muted">{list.length}</span>
            </h2>
            <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-6 pr-1">
              {list.length === 0 ? (
                <div className="rounded-[var(--radius-card)] border border-dashed border-line">
                  <EmptyState title="Nothing here" />
                </div>
              ) : (
                list.map((o) => <Ticket key={o.id} order={o} now={now} needCook={needCook} />)
              )}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function Ticket({ order, now, needCook }: { order: Order; now: number; needCook: (a: () => void) => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const age = minutesSince(order.created_at, now);
  const tone = age >= VERY_LATE_MIN ? "crit" : age >= LATE_MIN ? "warn" : "neutral";

  const act = useMutation({
    mutationFn: async (fn: () => Promise<unknown>) => fn(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["board"] }),
    onError: (err: Error) => toast("crit", err.message),
  });

  const run = (fn: () => Promise<unknown>) => needCook(() => act.mutate(fn));
  const accept = () =>
    run(() => ok(cookApi.POST("/api/v1/kitchen/orders/{order_id}/accept", { params: { path: { order_id: order.id } } })));
  const start = () =>
    run(() => ok(cookApi.POST("/api/v1/kitchen/orders/{order_id}/start", { params: { path: { order_id: order.id } } })));

  return (
    <article
      className={cn(
        "rounded-[var(--radius-card)] border-2 bg-surface p-4",
        tone === "crit" ? "border-crit" : tone === "warn" ? "border-warn" : "border-line",
      )}
    >
      <header className="flex items-start justify-between gap-3">
        <div>
          <p className="font-display text-2xl font-semibold text-ink">Room {order.room}</p>
          <p className="font-mono text-sm text-muted">#{order.number}</p>
        </div>
        <div className="text-right">
          <Badge tone={tone === "neutral" ? "info" : tone} className="text-sm">
            {elapsed(order.created_at, now)}
          </Badge>
          <p className="mt-1 text-xs text-muted">Placed {formatTime(order.created_at)}</p>
        </div>
      </header>
      {order.special_instructions ? (
        <p className="mt-3 rounded-lg bg-warn-bg px-3 py-2 text-base font-medium text-warn">{order.special_instructions}</p>
      ) : null}
      <ul className="mt-3 flex flex-col gap-2">
        {order.items.map((item) => (
          <ItemRow key={item.id} item={item} order={order} run={run} busy={act.isPending} />
        ))}
      </ul>
      {order.status === "NEW" ? (
        <Button size="xl" className="mt-4 w-full" onClick={accept} loading={act.isPending}>
          Accept order
        </Button>
      ) : order.status === "ACCEPTED" ? (
        <Button size="xl" variant="success" className="mt-4 w-full" onClick={start} loading={act.isPending}>
          Start preparing
        </Button>
      ) : null}
    </article>
  );
}

function ItemRow({
  item,
  order,
  run,
  busy,
}: {
  item: Item;
  order: Order;
  run: (fn: () => Promise<unknown>) => void;
  busy: boolean;
}) {
  const ready = item.prep_status === "ready";
  const canMark = order.status === "PREPARING" && item.mine;
  const toggle = () =>
    run(() =>
      ok(
        ready
          ? cookApi.POST("/api/v1/kitchen/order-items/{item_id}/unready", { params: { path: { item_id: item.id } } })
          : cookApi.POST("/api/v1/kitchen/order-items/{item_id}/ready", { params: { path: { item_id: item.id } } }),
      ),
    );
  return (
    <li className={cn("flex items-center gap-3 rounded-lg px-2 py-1.5", ready && "bg-good-bg")}>
      <span className="min-w-10 font-display text-2xl font-semibold tabular-nums text-ink">{item.quantity}×</span>
      <div className="min-w-0 flex-1">
        <p className={cn("text-lg font-medium text-ink", ready && "line-through decoration-2")}>{item.name}</p>
        {item.modifiers.length ? (
          <p className="text-sm text-muted">{item.modifiers.map((m) => m.name).join(" · ")}</p>
        ) : null}
        {item.note ? <p className="text-sm font-medium text-warn">{item.note}</p> : null}
        {!item.mine ? <p className="text-xs text-muted">{String(item.station?.name ?? "Another station")}</p> : null}
      </div>
      {canMark ? (
        <Button size="lg" variant={ready ? "secondary" : "success"} onClick={toggle} disabled={busy} className="min-w-28">
          {ready ? "Undo" : "Ready"}
        </Button>
      ) : ready ? (
        <Badge tone="good">Ready</Badge>
      ) : null}
    </li>
  );
}
