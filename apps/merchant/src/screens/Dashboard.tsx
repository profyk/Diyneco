"use client";

import { elapsed, formatMoney, ok } from "@diyneco/api-client";
import { Badge, Card, CardHeader, EmptyState, PageHeader, Skeleton, StatTile, Table, Td, Th } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { isoDay, OrderStatus } from "../common";
import { useMe, useSession } from "../session";

const ACTIVE = ["NEW", "ACCEPTED", "PREPARING", "READY", "ASSIGNED", "PICKED_UP", "DELIVERED"];

export function Dashboard() {
  const { api, can } = useSession();
  const { me } = useMe();
  const today = isoDay();

  const onboarding = useQuery({
    queryKey: ["onboarding"],
    queryFn: () => ok(api.GET("/api/v1/hotel/onboarding")),
    enabled: can("hotel.read"),
  });
  const rooms = useQuery({
    queryKey: ["rooms", "all"],
    queryFn: () => ok(api.GET("/api/v1/rooms", { params: { query: { limit: 200 } } })),
    enabled: can("rooms.read"),
  });
  const orders = useQuery({
    queryKey: ["orders", "recent"],
    queryFn: () => ok(api.GET("/api/v1/orders", { params: { query: { limit: 50 } } })),
    enabled: can("orders.read"),
  });
  const revenue = useQuery({
    queryKey: ["reports", "revenue", today],
    queryFn: () => ok(api.GET("/api/v1/reports/revenue", { params: { query: { from: today, to: today } } })),
    enabled: can("reports.finance"),
  });

  const roomList = rooms.data?.data ?? [];
  const occupied = roomList.filter((r) => r.status === "occupied").length;
  const sellable = roomList.filter((r) => r.status !== "out_of_service").length;
  const orderList = orders.data?.data ?? [];
  const pending = orderList.filter((o) => o.status === "PENDING_APPROVAL");
  const active = orderList.filter((o) => ACTIVE.includes(o.status));
  const steps = onboarding.data;

  return (
    <>
      <PageHeader
        title={`Good ${new Date().getHours() < 12 ? "morning" : new Date().getHours() < 18 ? "afternoon" : "evening"}, ${me.user?.name.split(" ")[0] ?? ""}`}
        description={new Date().toLocaleDateString("en-ZA", { weekday: "long", day: "numeric", month: "long" })}
      />

      {steps && steps.completed < steps.total ? (
        <Card className="mb-6">
          <CardHeader
            title="Get your hotel ready"
            description={`${steps.completed} of ${steps.total} steps done`}
          />
          <ul className="divide-y divide-line">
            {steps.steps.map((s) => (
              <li key={s.key} className="flex items-center justify-between px-5 py-3 text-sm">
                <span className={s.done ? "text-muted line-through" : "text-ink"}>{s.title}</span>
                {s.done ? <Badge tone="good">Done</Badge> : <Badge tone="warn">To do</Badge>}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {can("rooms.read") ? (
          <StatTile
            label="Occupancy"
            value={rooms.isLoading ? "…" : `${sellable ? Math.round((occupied / sellable) * 100) : 0}%`}
            hint={`${occupied} of ${sellable} rooms occupied`}
          />
        ) : null}
        {can("orders.read") ? (
          <>
            <StatTile label="Orders in progress" value={orders.isLoading ? "…" : active.length} />
            <StatTile
              label="Waiting for approval"
              value={orders.isLoading ? "…" : pending.length}
              tone={pending.length ? "warn" : "neutral"}
              hint={pending.length ? <Link href="/approvals" className="text-blue hover:underline">Review now</Link> : "Nothing waiting"}
            />
          </>
        ) : null}
        {can("reports.finance") ? (
          <StatTile
            label="Revenue today"
            value={revenue.data ? formatMoney(revenue.data.total.revenue) : "…"}
            hint={revenue.data ? `Tips ${formatMoney(revenue.data.total.tips)} (not revenue)` : undefined}
          />
        ) : null}
      </div>

      {can("orders.read") ? (
        <Card className="mt-6">
          <CardHeader
            title="Live orders"
            description="Updates as the kitchen and room service work"
            actions={<Link href="/orders" className="text-sm text-blue hover:underline">All orders</Link>}
          />
          {orders.isLoading ? (
            <div className="space-y-2 p-5">
              <Skeleton />
              <Skeleton />
              <Skeleton />
            </div>
          ) : active.length + pending.length === 0 ? (
            <EmptyState title="No open orders" body="New orders from room tablets appear here instantly." />
          ) : (
            <Table>
              <thead>
                <tr>
                  <Th>Order</Th>
                  <Th>Room</Th>
                  <Th>Status</Th>
                  <Th>Waiting</Th>
                  <Th className="text-right">Total</Th>
                </tr>
              </thead>
              <tbody>
                {[...pending, ...active].map((o) => (
                  <tr key={o.id} className="hover:bg-surface-2">
                    <Td>
                      <Link className="font-mono text-blue hover:underline" href={`/orders?open=${o.id}`}>
                        #{o.number}
                      </Link>
                    </Td>
                    <Td>{o.room}</Td>
                    <Td>
                      <OrderStatus status={o.status} />
                    </Td>
                    <Td className="tabular-nums text-muted">{elapsed(o.created_at)}</Td>
                    <Td className="text-right tabular-nums">{formatMoney(o.total)}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>
      ) : null}
    </>
  );
}
