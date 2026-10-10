"use client";

import { type components, connectRealtime, elapsed, formatMoney, ok, parseAmount, type RealtimeStatus } from "@diyneco/api-client";
import { Badge, Button, Card, cn, Dialog, EmptyState, ErrorNotice, Field, Input, Spinner } from "@diyneco/shared-ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { EnrolScreen, LoginScreen } from "./auth-screens";
import { API_URL } from "./config";
import { useSession } from "./session";

type Delivery = components["schemas"]["app__schemas__room_service__DeliveryOut"];
type Step = "claim" | "release" | "picked-up" | "delivered" | "leave-on-room";

export function App() {
  const { state } = useSession();
  if (state.status === "loading") {
    return (
      <main className="flex min-h-dvh items-center justify-center">
        <Spinner className="size-8 text-muted" />
      </main>
    );
  }
  if (state.status === "signed-out") return <LoginScreen />;
  if (state.status === "mfa-enrol") return <EnrolScreen />;
  return <Deliveries />;
}

function useLive(): RealtimeStatus {
  const qc = useQueryClient();
  const { accessToken } = useSession();
  const [status, setStatus] = useState<RealtimeStatus>("connecting");
  useEffect(() => {
    const rt = connectRealtime({
      baseUrl: API_URL,
      getToken: accessToken,
      channels: (allowed) => allowed.filter((c) => c.endsWith(":room-service")),
      onEvent: (e) => {
        if (e.type === "ORDER_READY") navigator.vibrate?.([120, 60, 120]);
        void qc.invalidateQueries({ queryKey: ["deliveries"] });
      },
      onStatus: setStatus,
    });
    return () => rt.close();
  }, [accessToken, qc]);
  return status;
}

function Deliveries() {
  const { api, state, signOut, can } = useSession();
  const [tab, setTab] = useState<"ready" | "mine">("ready");
  const [paying, setPaying] = useState<Delivery | null>(null);
  const live = useLive();
  const list = useQuery({
    queryKey: ["deliveries", tab],
    queryFn: () => ok(api.GET("/api/v1/deliveries", { params: { query: { scope: tab } } })),
    refetchInterval: live === "live" ? 60_000 : 10_000,
  });
  if (state.status !== "signed-in") return null;
  if (!can("deliveries.view")) {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6 text-center">
        <p className="text-ink">Your role does not include room service.</p>
        <Button onClick={() => void signOut()}>Sign out</Button>
      </main>
    );
  }
  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col">
      <header className="sticky top-0 z-10 border-b border-line bg-surface/95 px-4 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))] backdrop-blur">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-display text-lg font-semibold text-ink">Room service</p>
            <p className="text-xs text-muted">{state.me.user?.name}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone={live === "live" ? "good" : "warn"}>{live === "live" ? "Live" : "Offline"}</Badge>
            <button type="button" className="px-2 py-2 text-sm text-blue" onClick={() => void signOut()}>
              Sign out
            </button>
          </div>
        </div>
        <div role="tablist" className="mt-3 grid grid-cols-2 gap-2">
          {(["ready", "mine"] as const).map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              onClick={() => setTab(t)}
              className={cn(
                "h-12 rounded-xl text-base font-semibold",
                tab === t ? "bg-brand text-on-brand" : "border border-line bg-surface text-ink",
              )}
            >
              {t === "ready" ? "Ready to collect" : "My deliveries"}
            </button>
          ))}
        </div>
      </header>
      <main className="flex flex-1 flex-col gap-3 p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
        {list.error ? <ErrorNotice error={list.error} /> : null}
        {list.isLoading ? (
          <Spinner className="mx-auto mt-10 size-8 text-muted" />
        ) : list.data?.data.length ? (
          list.data.data.map((d) => <DeliveryCard key={d.order_id} d={d} mine={tab === "mine"} onPay={() => setPaying(d)} />)
        ) : (
          <EmptyState title={tab === "ready" ? "Nothing waiting in the kitchen" : "You have no deliveries"} body="This updates by itself." />
        )}
      </main>
      {paying ? <PayDialog d={paying} onClose={() => setPaying(null)} /> : null}
    </div>
  );
}

function DeliveryCard({ d, mine, onPay }: { d: Delivery; mine: boolean; onPay: () => void }) {
  const { api } = useSession();
  const qc = useQueryClient();
  const act = useMutation({
    mutationFn: (step: Step) => {
      const path = `/api/v1/deliveries/{order_id}/${step}` as "/api/v1/deliveries/{order_id}/claim";
      return ok(api.POST(path, { params: { path: { order_id: d.order_id } } }));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["deliveries"] }),
  });
  const big = "h-14 w-full text-base";
  return (
    <Card className="flex flex-col gap-3 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-display text-2xl font-semibold text-ink">Room {d.room}</p>
          <p className="text-sm text-muted">
            #{d.number} · ready {elapsed(d.ready_at)} ago
          </p>
        </div>
        <p className="font-display text-xl font-semibold tabular-nums text-ink">{formatMoney(d.amount_due)}</p>
      </div>
      <ul className="text-base text-ink">
        {d.items.map((i, n) => (
          <li key={n}>
            {String(i.quantity)}× {String(i.name)}
          </li>
        ))}
      </ul>
      {d.special_instructions ? <p className="rounded-lg bg-warn-bg px-3 py-2 text-warn">{d.special_instructions}</p> : null}
      {act.error ? <ErrorNotice error={act.error} /> : null}
      {!mine ? (
        <Button className={big} loading={act.isPending} onClick={() => act.mutate("claim")}>
          I&apos;ll take it
        </Button>
      ) : d.status === "ASSIGNED" ? (
        <div className="grid grid-cols-3 gap-2">
          <Button variant="secondary" className={big} onClick={() => act.mutate("release")}>
            Release
          </Button>
          <Button className={cn(big, "col-span-2")} loading={act.isPending} onClick={() => act.mutate("picked-up")}>
            Picked up
          </Button>
        </div>
      ) : d.status === "PICKED_UP" ? (
        <Button variant="success" className={big} loading={act.isPending} onClick={() => act.mutate("delivered")}>
          Delivered to the room
        </Button>
      ) : d.status === "DELIVERED" && !d.paid ? (
        <div className="grid grid-cols-2 gap-2">
          <Button variant="secondary" className={big} loading={act.isPending} onClick={() => act.mutate("leave-on-room")}>
            Leave on bill
          </Button>
          <Button className={big} onClick={onPay}>
            Take payment
          </Button>
        </div>
      ) : null}
    </Card>
  );
}

/** The server computes what is due and any tip; the phone shows it and the guest confirms the tip. */
function PayDialog({ d, onClose }: { d: Delivery; onClose: () => void }) {
  const { api } = useSession();
  const qc = useQueryClient();
  const [method, setMethod] = useState<"card_terminal" | "cash">("card_terminal");
  const [received, setReceived] = useState("");
  const [reference, setReference] = useState("");
  const [tipOk, setTipOk] = useState(false);
  const minor = parseAmount(received);
  const amount = minor === null ? null : { amount_minor: minor, currency: d.amount_due.currency };
  const preview = useQuery({
    queryKey: ["preview", d.order_id, minor],
    queryFn: () => ok(api.POST("/api/v1/payments/preview", { body: { order_id: d.order_id, amount_received: amount! } })),
    enabled: Boolean(amount),
  });
  const tip = preview.data?.tip.amount_minor ?? 0;
  const pay = useMutation({
    mutationFn: () =>
      ok(
        api.POST("/api/v1/payments", {
          body: {
            order_id: d.order_id,
            method,
            amount_received: amount!,
            confirm_tip: tipOk,
            terminal_reference: method === "card_terminal" ? reference.trim() : null,
          },
        }),
      ),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["deliveries"] });
      onClose();
    },
  });
  const refOk = method !== "card_terminal" || /^[A-Za-z0-9-]{4,20}$/.test(reference.trim());
  return (
    <Dialog open onClose={onClose} title={`Room ${d.room} · due ${formatMoney(d.amount_due)}`} description="Never type card numbers here. Use the hotel's card machine.">
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-2">
          {(["card_terminal", "cash"] as const).map((m) => (
            <Button key={m} variant={method === m ? "primary" : "secondary"} className="h-12" onClick={() => setMethod(m)}>
              {m === "cash" ? "Cash" : "Card machine"}
            </Button>
          ))}
        </div>
        <Field label="Amount received">
          {(p) => <Input {...p} inputMode="decimal" className="h-12 text-lg" placeholder="0.00" value={received} onChange={(e) => setReceived(e.target.value)} />}
        </Field>
        {method === "card_terminal" ? (
          <Field label="Card machine reference" hint="From the slip, 4 to 20 letters or digits">
            {(p) => <Input {...p} className="h-12 text-lg uppercase" autoComplete="off" value={reference} onChange={(e) => setReference(e.target.value)} />}
          </Field>
        ) : null}
        {preview.data ? (
          <dl className="space-y-1 rounded-xl bg-surface-2 p-3 text-base">
            <div className="flex justify-between">
              <dt className="text-muted">Due</dt>
              <dd className="tabular-nums">{formatMoney(preview.data.amount_due)}</dd>
            </div>
            {preview.data.shortfall.amount_minor ? (
              <div className="flex justify-between text-warn">
                <dt>Stays on the room bill</dt>
                <dd className="tabular-nums">{formatMoney(preview.data.shortfall)}</dd>
              </div>
            ) : null}
            {tip ? (
              <div className="flex justify-between text-lg font-semibold text-teal">
                <dt>Tip for you</dt>
                <dd className="tabular-nums">{formatMoney(preview.data.tip)}</dd>
              </div>
            ) : null}
          </dl>
        ) : null}
        {tip ? (
          <label className="flex items-center gap-3 text-base">
            <input type="checkbox" className="size-6" checked={tipOk} onChange={(e) => setTipOk(e.target.checked)} />
            The guest confirmed the tip
          </label>
        ) : null}
        {pay.error ? <ErrorNotice error={pay.error} /> : null}
        <Button className="h-14 text-lg" loading={pay.isPending} disabled={!amount || !refOk || (tip > 0 && !tipOk)} onClick={() => pay.mutate()}>
          Record payment
        </Button>
      </div>
    </Dialog>
  );
}
