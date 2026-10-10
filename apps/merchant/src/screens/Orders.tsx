"use client";

import { type components, elapsed, formatMoney, formatTime, ok, parseAmount } from "@diyneco/api-client";
import {
  Button,
  Card,
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
  Textarea,
  Th,
  cn,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { label, OrderStatus, useAction } from "../common";
import { useSession } from "../session";

type Order = components["schemas"]["OrderOut"];

const TABS: { key: string; title: string; statuses: string[] | null }[] = [
  { key: "open", title: "Open", statuses: ["NEW", "ACCEPTED", "PREPARING", "READY", "ASSIGNED", "PICKED_UP", "DELIVERED"] },
  { key: "approval", title: "Needs approval", statuses: ["PENDING_APPROVAL"] },
  { key: "done", title: "Completed", statuses: ["CLOSED"] },
  { key: "stopped", title: "Cancelled & declined", statuses: ["CANCELLED", "DECLINED"] },
  { key: "all", title: "All", statuses: null },
];

export function Orders() {
  const { api, can } = useSession();
  const router = useRouter();
  const params = useSearchParams();
  const [tab, setTab] = useState("open");
  const [creating, setCreating] = useState(false);
  const openId = params.get("open");

  const orders = useQuery({
    queryKey: ["orders", "list"],
    queryFn: () => ok(api.GET("/api/v1/orders", { params: { query: { limit: 200 } } })),
  });
  const statuses = TABS.find((t) => t.key === tab)?.statuses;
  const list = (orders.data?.data ?? []).filter((o) => !statuses || statuses.includes(o.status));

  return (
    <>
      <PageHeader
        title="Orders"
        description="Every order from room tablets and staff, newest first."
        actions={can("orders.create") ? <Button onClick={() => setCreating(true)}>New phone order</Button> : null}
      />
      <div role="tablist" className="mb-4 flex flex-wrap gap-1">
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "rounded-full px-3 py-1.5 text-sm font-medium",
              tab === t.key ? "bg-brand text-on-brand" : "bg-surface text-ink hover:bg-surface-2",
            )}
          >
            {t.title}
          </button>
        ))}
      </div>
      <Card>
        {orders.isLoading ? (
          <div className="space-y-2 p-5">
            <Skeleton />
            <Skeleton />
          </div>
        ) : orders.error ? (
          <ErrorNotice error={orders.error} className="m-5" />
        ) : list.length === 0 ? (
          <EmptyState title="No orders here" />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Order</Th>
                <Th>Room</Th>
                <Th>Placed</Th>
                <Th>Status</Th>
                <Th>By</Th>
                <Th className="text-right">Total</Th>
              </tr>
            </thead>
            <tbody>
              {list.map((o) => (
                <tr
                  key={o.id}
                  className="cursor-pointer hover:bg-surface-2"
                  onClick={() => router.push(`/orders?open=${o.id}`)}
                >
                  <Td className="font-mono">#{o.number}</Td>
                  <Td>{o.room}</Td>
                  <Td className="text-muted">
                    {formatTime(o.created_at)} · {elapsed(o.created_at)} ago
                  </Td>
                  <Td>
                    <OrderStatus status={o.status} />
                  </Td>
                  <Td className="text-muted">{o.placed_by === "guest" ? "Tablet" : "Staff"}</Td>
                  <Td className="text-right tabular-nums">{formatMoney(o.total)}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
      {openId ? <OrderDialog id={openId} onClose={() => router.push("/orders")} /> : null}
      {creating ? <PhoneOrder onClose={() => setCreating(false)} /> : null}
    </>
  );
}

function OrderDialog({ id, onClose }: { id: string; onClose: () => void }) {
  const { api, can } = useSession();
  const order = useQuery({
    queryKey: ["orders", id],
    queryFn: () => ok(api.GET("/api/v1/orders/{order_id}", { params: { path: { order_id: id } } })),
  });
  const [reason, setReason] = useState("");
  const [mode, setMode] = useState<null | "decline" | "cancel" | "adjust" | { void: string; name: string }>(null);
  const [newAmount, setNewAmount] = useState("");

  const approve = useAction(
    () => ok(api.POST("/api/v1/orders/{order_id}/approve", { params: { path: { order_id: id } } })),
    { success: "Order approved and sent to the kitchen." },
  );
  const decline = useAction(
    () => ok(api.POST("/api/v1/orders/{order_id}/decline", { params: { path: { order_id: id } }, body: { reason } })),
    { success: "Order declined.", onDone: () => setMode(null) },
  );
  const cancel = useAction(
    () => ok(api.POST("/api/v1/orders/{order_id}/cancel", { params: { path: { order_id: id } }, body: { reason } })),
    { success: "Order cancelled; the charge was reversed.", onDone: () => setMode(null) },
  );
  const adjust = useAction(
    (minor: number) =>
      ok(
        api.POST("/api/v1/adjustments", {
          body: { order_id: id, new_amount: { amount_minor: minor, currency: order.data?.total.currency ?? "" }, reason },
        }),
      ),
    { success: "Adjustment requested. Another manager must approve it.", onDone: () => setMode(null) },
  );
  const voidLine = useAction(
    (itemId: string) =>
      ok(
        api.POST("/api/v1/orders/{order_id}/items/{item_id}/void", {
          params: { path: { order_id: id, item_id: itemId } },
          body: { reason },
        }),
      ),
    {
      success: (r) => (r.status === "CANCELLED" ? "Last item voided: the order was cancelled." : "Item voided; its charge was reversed."),
      onDone: () => {
        setMode(null);
        setReason("");
      },
    },
  );
  const o = order.data;
  const error = approve.error ?? decline.error ?? cancel.error ?? adjust.error ?? voidLine.error;
  // Until delivery (D67); the API refuses paid orders, which are corrected with an adjustment.
  const canCancel =
    o && ["NEW", "ACCEPTED", "PREPARING", "READY", "ASSIGNED", "PICKED_UP"].includes(o.status) && can("orders.cancel");
  const canAdjust = o && !["PENDING_APPROVAL", "DECLINED", "CANCELLED"].includes(o.status) && can("folio.adjust.request");

  return (
    <Dialog open onClose={onClose} size="lg" title={o ? `Order #${o.number} · Room ${o.room}` : "Order"}>
      {!o ? (
        <Skeleton className="h-40" />
      ) : (
        <div className="flex flex-col gap-4 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <OrderStatus status={o.status} />
            <span className="text-muted">
              {o.placed_by === "guest" ? "From the room tablet" : "Phone order"} at {formatTime(o.created_at)}
            </span>
          </div>
          {o.special_instructions ? (
            <p className="rounded-lg bg-warn-bg px-3 py-2 text-warn">{o.special_instructions}</p>
          ) : null}
          <table className="w-full">
            <tbody>
              {o.items.map((i) => (
                <tr key={i.id} className="border-b border-line">
                  <td className="py-2 pr-2 tabular-nums">{i.quantity}×</td>
                  <td className="py-2">
                    {i.name}
                    {i.modifiers.length ? (
                      <span className="block text-xs text-muted">
                        {i.modifiers.map((m) => String((m as { name?: string }).name ?? "")).join(" · ")}
                      </span>
                    ) : null}
                    {i.note ? <span className="block text-xs text-warn">{i.note}</span> : null}
                  </td>
                  <td className="py-2 text-right tabular-nums">{formatMoney(i.line_total)}</td>
                  {canCancel ? (
                    <td className="py-2 pl-2 text-right">
                      <Button size="sm" variant="ghost" onClick={() => setMode({ void: i.id, name: i.name })}>
                        Void
                      </Button>
                    </td>
                  ) : null}
                </tr>
              ))}
              {o.voided_items.map((v) => (
                <tr key={v.id} className="border-b border-line text-muted">
                  <td className="py-2 pr-2 tabular-nums line-through">{v.quantity}×</td>
                  <td className="py-2">
                    <span className="line-through">{v.name}</span>
                    <span className="block text-xs">Voided: {v.reason}</span>
                  </td>
                  <td className="py-2 text-right tabular-nums line-through">{formatMoney(v.line_total)}</td>
                </tr>
              ))}
              {o.fee.amount_minor ? (
                <tr className="border-b border-line">
                  <td />
                  <td className="py-2 text-muted">Room-service fee</td>
                  <td className="py-2 text-right tabular-nums">{formatMoney(o.fee)}</td>
                </tr>
              ) : null}
              <tr>
                <td />
                <td className="py-2 font-semibold">Total (VAT {formatMoney(o.vat_included)} included)</td>
                <td className="py-2 text-right font-semibold tabular-nums">{formatMoney(o.total)}</td>
              </tr>
            </tbody>
          </table>
          {o.decline_reason ? <p className="text-crit">Reason: {o.decline_reason}</p> : null}
          <details>
            <summary className="cursor-pointer text-muted">History</summary>
            <ol className="mt-2 space-y-1">
              {o.history.map((h, i) => (
                <li key={i} className="text-muted">
                  {formatTime(h.at)} · {h.from_status ? `${label(h.from_status)} → ` : ""}
                  {label(h.to_status)}
                </li>
              ))}
            </ol>
          </details>
          {mode ? (
            <div className="flex flex-col gap-3 rounded-lg border border-line p-3">
              {typeof mode === "object" ? (
                <p className="font-medium text-ink">Void {mode.name}: it leaves the kitchen ticket and its charge is reversed. Asks for your PIN.</p>
              ) : null}
              {mode === "adjust" ? (
                <Field label="New amount for this order" hint={`Currently ${formatMoney(o.total)}`}>
                  {(p) => <Input {...p} inputMode="decimal" placeholder="0.00" value={newAmount} onChange={(e) => setNewAmount(e.target.value)} />}
                </Field>
              ) : null}
              <Field label="Reason">
                {(p) => <Textarea {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}
              </Field>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setMode(null)}>
                  Back
                </Button>
                {typeof mode === "object" ? (
                  <Button variant="danger" disabled={!reason.trim()} loading={voidLine.isPending} onClick={() => voidLine.mutate(mode.void)}>
                    Void item
                  </Button>
                ) : mode === "decline" ? (
                  <Button variant="danger" disabled={!reason.trim()} loading={decline.isPending} onClick={() => decline.mutate(undefined)}>
                    Decline order
                  </Button>
                ) : mode === "cancel" ? (
                  <Button variant="danger" disabled={!reason.trim()} loading={cancel.isPending} onClick={() => cancel.mutate(undefined)}>
                    Cancel order
                  </Button>
                ) : (
                  <Button
                    disabled={reason.trim().length < 3 || parseAmount(newAmount) === null}
                    loading={adjust.isPending}
                    onClick={() => adjust.mutate(parseAmount(newAmount) ?? 0)}
                  >
                    Request adjustment
                  </Button>
                )}
              </div>
            </div>
          ) : null}
          {error ? <ErrorNotice error={error} /> : null}
          {!mode ? (
            <div className="flex flex-wrap justify-end gap-2 border-t border-line pt-3">
              {o.status === "PENDING_APPROVAL" && can("orders.approve") ? (
                <>
                  <Button variant="secondary" onClick={() => setMode("decline")}>
                    Decline
                  </Button>
                  <Button loading={approve.isPending} onClick={() => approve.mutate(undefined)}>
                    Approve
                  </Button>
                </>
              ) : null}
              {canCancel ? (
                <Button variant="secondary" onClick={() => setMode("cancel")}>
                  Cancel order
                </Button>
              ) : null}
              {canAdjust ? (
                <Button variant="secondary" onClick={() => setMode("adjust")}>
                  Request adjustment
                </Button>
              ) : null}
            </div>
          ) : null}
        </div>
      )}
    </Dialog>
  );
}

/** A guest phones reception: same menu, pricing and approval rules as the tablet. */
function PhoneOrder({ onClose }: { onClose: () => void }) {
  const { api } = useSession();
  const [roomId, setRoomId] = useState("");
  const [qty, setQty] = useState<Record<string, number>>({});
  const [notes, setNotes] = useState("");
  const [quote, setQuote] = useState<components["schemas"]["Quote"] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const rooms = useQuery({
    queryKey: ["rooms", "occupied"],
    queryFn: () => ok(api.GET("/api/v1/rooms", { params: { query: { status: "occupied", limit: 200 } } })),
  });
  const items = useQuery({
    queryKey: ["menu", "items", "available"],
    queryFn: () => ok(api.GET("/api/v1/menu/items", { params: { query: { available: true } } })),
  });
  const lines = useMemo(
    () => Object.entries(qty).filter(([, n]) => n > 0).map(([menu_item_id, quantity]) => ({ menu_item_id, quantity })),
    [qty],
  );
  const place = useAction(
    () =>
      ok(
        api.POST("/api/v1/orders", {
          body: {
            room_id: roomId,
            lines,
            payment_method: "room_charge",
            quoted_total: quote!.total,
            special_instructions: notes.trim() || null,
          },
        }),
      ),
    { success: (o) => `Order #${o.number} placed.`, onDone: onClose },
  );

  const review = async () => {
    setBusy(true);
    setError(null);
    try {
      setQuote(await ok(api.POST("/api/v1/orders/quote", { body: { room_id: roomId, lines } })));
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title="New phone order"
      description="Charged to the room. Orders above the hotel's limit wait for a manager's approval."
      footer={
        quote ? (
          <>
            <Button variant="secondary" onClick={() => setQuote(null)}>
              Change
            </Button>
            <Button loading={place.isPending} onClick={() => place.mutate(undefined)}>
              Place order · {formatMoney(quote.total)}
            </Button>
          </>
        ) : (
          <Button disabled={!roomId || lines.length === 0} loading={busy} onClick={review}>
            Review total
          </Button>
        )
      }
    >
      {quote ? (
        <div className="text-sm">
          <ul className="divide-y divide-line">
            {quote.lines.map((l, i) => (
              <li key={i} className="flex justify-between py-2">
                <span>
                  {l.quantity}× {l.name}
                </span>
                <span className="tabular-nums">{formatMoney(l.line_total)}</span>
              </li>
            ))}
          </ul>
          {quote.fee.amount_minor ? (
            <p className="flex justify-between py-2 text-muted">
              <span>Room-service fee</span>
              <span>{formatMoney(quote.fee)}</span>
            </p>
          ) : null}
          <p className="flex justify-between border-t border-line pt-2 font-semibold">
            <span>Total</span>
            <span>{formatMoney(quote.total)}</span>
          </p>
          {place.error ? <ErrorNotice error={place.error} className="mt-3" /> : null}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <Field label="Room">
            {(p) => (
              <Select {...p} value={roomId} onChange={(e) => setRoomId(e.target.value)}>
                <option value="">Choose an occupied room</option>
                {rooms.data?.data.map((r) => (
                  <option key={r.id} value={r.id}>
                    Room {r.number}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <div className="max-h-80 overflow-y-auto rounded-lg border border-line">
            {items.data?.data.map((item) => (
              <div key={item.id} className="flex items-center justify-between gap-3 border-b border-line px-3 py-2 last:border-0">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">{item.name}</p>
                  <p className="text-xs text-muted">{formatMoney(item.price)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="secondary" aria-label={`Fewer ${item.name}`} onClick={() => setQty((q) => ({ ...q, [item.id]: Math.max(0, (q[item.id] ?? 0) - 1) }))}>
                    −
                  </Button>
                  <span className="w-6 text-center tabular-nums">{qty[item.id] ?? 0}</span>
                  <Button size="sm" variant="secondary" aria-label={`More ${item.name}`} onClick={() => setQty((q) => ({ ...q, [item.id]: (q[item.id] ?? 0) + 1 }))}>
                    +
                  </Button>
                </div>
              </div>
            ))}
            {items.data?.data.length === 0 ? <EmptyState title="Nothing available right now" /> : null}
          </div>
          <Field label="Instructions for the kitchen (optional)">
            {(p) => <Textarea {...p} value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={500} />}
          </Field>
          {error ? <ErrorNotice error={error} /> : null}
        </div>
      )}
    </Dialog>
  );
}
