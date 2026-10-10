"use client";

import { formatMoney, ok } from "@diyneco/api-client";
import { Badge, Card, EmptyState, ErrorNotice, PageHeader, Select, Skeleton } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { useAction } from "../common";
import { useSession } from "../session";

const COLUMNS = [
  { status: "READY", title: "Waiting for a runner", since: "ready_at" },
  { status: "ASSIGNED", title: "Assigned", since: "assigned_at" },
  { status: "PICKED_UP", title: "On the way", since: "picked_up_at" },
  { status: "DELIVERED", title: "Delivered, not settled", since: "delivered_at" },
] as const;

type Item = { name?: unknown; quantity?: unknown; note?: unknown };

function minutesSince(iso: string | null | undefined, now: number): number | null {
  return iso ? Math.max(0, Math.floor((now - new Date(iso).getTime()) / 60000)) : null;
}

/** Room-service dispatch: every order ready or on its way, with who has it and for how long. */
export function Dispatch() {
  const { api, can } = useSession();
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 30_000);
    return () => clearInterval(t);
  }, []);
  const board = useQuery({
    queryKey: ["deliveries", "all"],
    queryFn: () => ok(api.GET("/api/v1/deliveries", { params: { query: { scope: "all" } } })),
    refetchInterval: 10_000,
  });
  const staff = useQuery({ queryKey: ["staff"], queryFn: () => ok(api.GET("/api/v1/staff")) });
  const roles = useQuery({ queryKey: ["roles"], queryFn: () => ok(api.GET("/api/v1/roles")) });
  const runnerRoles = new Set((roles.data?.data ?? []).filter((r) => r.permissions.includes("deliveries.update")).map((r) => r.id));
  const runners = (staff.data?.data ?? []).filter((s) => s.status === "active" && s.roles.some((r) => runnerRoles.has(r.id)));
  const assign = useAction(
    ({ order, user }: { order: string; user: string }) =>
      ok(api.POST("/api/v1/deliveries/{order_id}/assign", { params: { path: { order_id: order } }, body: { user_id: user } })),
    { success: (d) => `Order ${d.number} assigned to ${String(d.assigned_to?.name ?? "")}.` },
  );
  const manage = can("deliveries.manage");
  const orders = board.data?.data ?? [];

  return (
    <>
      <PageHeader
        title="Dispatch"
        description="Room-service orders from the kitchen pass to the guest's door. Updates every few seconds."
      />
      {assign.error ? <ErrorNotice error={assign.error} className="mb-4" /> : null}
      {board.isLoading ? (
        <Skeleton className="h-60" />
      ) : board.error ? (
        <ErrorNotice error={board.error} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {COLUMNS.map((col) => {
            const list = orders.filter((o) => o.status === col.status);
            return (
              <section key={col.status} aria-label={col.title} className="flex flex-col gap-3">
                <h2 className="flex items-center justify-between font-display text-sm font-semibold text-ink">
                  {col.title} <Badge>{list.length}</Badge>
                </h2>
                {list.length === 0 ? (
                  <Card>
                    <EmptyState title="None" />
                  </Card>
                ) : (
                  list.map((o) => {
                    const mins = minutesSince(o[col.since], now);
                    const late = mins !== null && ((col.status === "READY" && mins >= 5) || (col.status !== "READY" && mins >= 20));
                    return (
                      <Card key={o.order_id} className="flex flex-col gap-2 p-4">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="font-display text-lg font-semibold text-ink">Room {o.room}</p>
                            <p className="text-xs text-muted">
                              Order {o.number} · {formatMoney(o.amount_due)} {o.paid ? "· paid" : ""}
                            </p>
                          </div>
                          {mins !== null ? <Badge tone={late ? "crit" : "neutral"}>{mins} min</Badge> : null}
                        </div>
                        <ul className="text-sm text-ink">
                          {(o.items as Item[]).map((i, n) => (
                            <li key={n}>
                              {String(i.quantity)} × {String(i.name)}
                              {i.note ? <span className="text-muted"> ({String(i.note)})</span> : null}
                            </li>
                          ))}
                        </ul>
                        {o.special_instructions ? <p className="rounded bg-surface-2 p-2 text-xs text-ink">{o.special_instructions}</p> : null}
                        {o.assigned_to ? <p className="text-sm text-muted">With {String(o.assigned_to.name)}</p> : null}
                        {manage && (col.status === "READY" || col.status === "ASSIGNED") ? (
                          <div>
                            <Select
                              aria-label={`Assign order ${o.number}`}
                              value=""
                              onChange={(e) => e.target.value && assign.mutate({ order: o.order_id, user: e.target.value })}
                            >
                              <option value="">{o.assigned_to ? "Reassign to…" : "Assign to…"}</option>
                              {runners.map((r) => (
                                <option key={r.user_id} value={r.user_id}>
                                  {r.name}
                                </option>
                              ))}
                            </Select>
                          </div>
                        ) : null}
                      </Card>
                    );
                  })
                )}
              </section>
            );
          })}
        </div>
      )}
    </>
  );
}
