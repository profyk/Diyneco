"use client";

import {
  ApiError,
  type components,
  connectRealtime,
  createApi,
  formatMoney,
  formatTime,
  newIdempotencyKey,
  ok,
} from "@diyneco/api-client";
import { Badge, Button, cn, Dialog, ErrorNotice, Field, Input, Spinner, Textarea } from "@diyneco/shared-ui";
import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { API_URL, APP_VERSION } from "./config";
import { credential, currentDeviceToken, DeviceRevoked, getDeviceToken } from "./device";

type MenuItem = components["schemas"]["GuestMenuItem"];
type ModifierGroup = components["schemas"]["ModifierGroupOut"];
type Quote = components["schemas"]["Quote"];
type CartLine = { key: string; item: MenuItem; quantity: number; options: string[]; note: string };
type Tab = "menu" | "orders" | "bill" | "info";

const IDLE_MS = 3 * 60_000;

const api = createApi({ baseUrl: API_URL, getToken: currentDeviceToken, refresh: () => getDeviceToken(true) });

export function GuestApp() {
  const [client] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 10_000, refetchOnWindowFocus: false } } }),
  );
  const [paired, setPaired] = useState<boolean | null>(null);
  useEffect(() => setPaired(Boolean(credential.get())), []);
  return (
    <QueryClientProvider client={client}>
      <div className="kiosk min-h-dvh bg-bg">
        {paired === null ? null : paired ? (
          <Room onUnpaired={() => setPaired(false)} />
        ) : (
          <PairScreen onDone={() => setPaired(true)} />
        )}
      </div>
    </QueryClientProvider>
  );
}

function PairScreen({ onDone }: { onDone: () => void }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const pair = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/devices/pair`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": newIdempotencyKey() },
        body: JSON.stringify({ code, device_info: { os: navigator.platform || "browser", app_version: APP_VERSION } }),
      });
      const body = await res.json();
      if (!res.ok) throw new ApiError(res.status, body.error);
      if (body.kind !== "guest") {
        throw new ApiError(422, { code: "PAIRING_INVALID", message: "That code is for a kitchen display. Create a room tablet code.", request_id: null, details: {} });
      }
      credential.set(body.device_credential);
      onDone();
    } catch (e) {
      setError(e);
      setCode("");
    } finally {
      setBusy(false);
    }
  };
  return (
    <main className="flex min-h-dvh items-center justify-center p-6">
      <div className="w-full max-w-md text-center">
        <h1 className="font-display text-3xl font-semibold text-ink">Pair this tablet</h1>
        <p className="mt-2 text-muted">A manager creates a 6-digit code for this room in the Merchant app, under Devices.</p>
        <Input
          aria-label="Pairing code"
          inputMode="numeric"
          maxLength={6}
          autoFocus
          className="mt-6 h-16 text-center font-mono text-3xl tracking-[0.4em]"
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
        />
        {error ? <ErrorNotice error={error} className="mt-4 text-left" /> : null}
        <Button size="xl" className="mt-6 w-full" disabled={code.length !== 6} loading={busy} onClick={pair}>
          Pair tablet
        </Button>
      </div>
    </main>
  );
}

function Room({ onUnpaired }: { onUnpaired: () => void }) {
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("menu");
  const [cart, setCart] = useState<CartLine[]>([]);
  const lastTouch = useRef(Date.now());

  /** Drops everything about the current guest (checkout, room move, manager reset). */
  const resetGuest = useCallback(() => {
    setCart([]);
    setTab("menu");
    qc.removeQueries({ predicate: (q) => q.queryKey[0] !== "session" });
    void qc.invalidateQueries({ queryKey: ["session"] });
  }, [qc]);

  const session = useQuery({
    queryKey: ["session"],
    queryFn: async () => {
      await getDeviceToken();
      return ok(api.GET("/api/v1/guest/session"));
    },
    refetchInterval: 60_000,
    retry: (n, err) => !(err instanceof DeviceRevoked) && n < 2,
  });
  useEffect(() => {
    if (session.error instanceof DeviceRevoked) onUnpaired();
  }, [session.error, onUnpaired]);

  useEffect(() => {
    const rt = connectRealtime({
      baseUrl: API_URL,
      getToken: () => getDeviceToken(),
      onEvent: (e) => {
        if (e.type === "RESET_ROOM_SESSION" || e.type === "STAY_CHECKED_IN") resetGuest();
        else void qc.invalidateQueries();
      },
      onFatal: (code) => (code === 4409 ? onUnpaired() : void qc.invalidateQueries({ queryKey: ["session"] })),
    });
    return () => rt.close();
  }, [qc, resetGuest, onUnpaired]);

  useEffect(() => {
    let done: string[] = [];
    const beat = async () => {
      try {
        await getDeviceToken();
        const r = await ok(api.POST("/api/v1/devices/heartbeat", { body: { app_version: APP_VERSION, completed_commands: done as never } }));
        done = [];
        if (r.commands.includes("RESET")) {
          resetGuest();
          done.push("RESET");
        }
      } catch (e) {
        if (e instanceof DeviceRevoked) onUnpaired();
      }
    };
    void beat();
    const t = setInterval(beat, 60_000);
    return () => clearInterval(t);
  }, [resetGuest, onUnpaired]);

  // A guest who walks away leaves no half-finished cart for the next person.
  useEffect(() => {
    const t = setInterval(() => {
      if (Date.now() - lastTouch.current > IDLE_MS) {
        setCart([]);
        setTab("menu");
      }
    }, 15_000);
    return () => clearInterval(t);
  }, []);

  const s = session.data;
  if (!s) {
    return (
      <main className="flex min-h-dvh items-center justify-center">
        <Spinner className="size-8 text-muted" />
      </main>
    );
  }
  const hotel = s.hotel as { name?: string; logo_url?: string | null };
  const room = s.room as { number?: string };

  if (s.state !== "active") {
    const text =
      s.state === "idle"
        ? `Room ${room.number}. Ordering opens once you are checked in.`
        : s.state === "locked"
          ? "This tablet is paused. Please contact reception."
          : "Service is unavailable right now. Please contact reception.";
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center gap-5 p-8 text-center">
        {hotel.logo_url ? <img src={hotel.logo_url} alt="" className="max-h-40 max-w-60 object-contain" /> : null}
        <h1 className="font-display text-4xl font-semibold text-ink">{s.state === "idle" ? `Welcome to ${hotel.name}` : hotel.name}</h1>
        <p className="max-w-lg text-lg text-muted">{text}</p>
      </main>
    );
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "menu", label: "Menu" },
    { key: "orders", label: "My orders" },
    { key: "bill", label: "My bill" },
    { key: "info", label: "Hotel info" },
  ];
  return (
    <div className="flex min-h-dvh flex-col" onPointerDown={() => (lastTouch.current = Date.now())}>
      <header className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-3 border-b border-line bg-surface px-4 py-3 lg:px-8">
        <div>
          <p className="font-display text-xl font-semibold text-ink">{hotel.name}</p>
          <p className="text-sm text-muted">Room {room.number}</p>
        </div>
        <nav className="flex gap-2 overflow-x-auto" aria-label="Sections">
          {tabs.map((t) => (
            <Button key={t.key} size="lg" variant={tab === t.key ? "primary" : "secondary"} aria-current={tab === t.key ? "page" : undefined} onClick={() => setTab(t.key)}>
              {t.label}
            </Button>
          ))}
        </nav>
      </header>
      {!s.ordering_enabled && tab === "menu" ? (
        <p className="bg-warn-bg px-6 py-3 text-warn">Room charges are paused for this room. Please contact reception.</p>
      ) : null}
      <main className="flex-1">
        {tab === "menu" ? (
          <MenuTab cart={cart} setCart={setCart} enabled={s.ordering_enabled} onOrdered={() => { setCart([]); setTab("orders"); }} />
        ) : null}
        {tab === "orders" ? <OrdersTab /> : null}
        {tab === "bill" ? <BillTab /> : null}
        {tab === "info" ? <InfoTab /> : null}
      </main>
    </div>
  );
}

function MenuTab({ cart, setCart, enabled, onOrdered }: { cart: CartLine[]; setCart: (c: CartLine[]) => void; enabled: boolean; onOrdered: () => void }) {
  const menu = useQuery({ queryKey: ["menu"], queryFn: () => ok(api.GET("/api/v1/guest/menu")) });
  const [category, setCategory] = useState<string | null>(null);
  const [picking, setPicking] = useState<MenuItem | null>(null);
  const [review, setReview] = useState(false);
  const cats = menu.data?.categories ?? [];
  const current = cats.find((c) => c.id === category) ?? cats[0];
  const count = cart.reduce((n, l) => n + l.quantity, 0);
  return (
    <div className="flex flex-col md:flex-row">
      <nav className="flex gap-2 overflow-x-auto border-b border-line p-3 md:w-56 md:flex-col md:border-b-0 md:border-r" aria-label="Categories">
        {cats.map((c) => (
          <Button key={c.id} size="lg" variant={current?.id === c.id ? "primary" : "ghost"} className="shrink-0 justify-start" onClick={() => setCategory(c.id)}>
            {c.name}
          </Button>
        ))}
      </nav>
      <section className="grid flex-1 grid-cols-1 gap-4 p-4 pb-32 sm:grid-cols-2 xl:grid-cols-3">
        {menu.isLoading ? <Spinner className="m-10 size-8 text-muted" /> : null}
        {current?.items.map((item) => (
          <button
            key={item.id}
            type="button"
            disabled={!item.available_now || !enabled}
            onClick={() => setPicking(item)}
            className="flex flex-col overflow-hidden rounded-[var(--radius-card)] border border-line bg-surface text-left transition active:scale-[0.99] disabled:opacity-50"
          >
            {item.image_url ? <img src={item.image_url} alt="" loading="lazy" className="h-44 w-full object-cover" /> : null}
            <div className="flex flex-1 flex-col gap-1 p-4">
              <p className="text-lg font-semibold text-ink">{item.name}</p>
              {item.description ? <p className="line-clamp-2 text-sm text-muted">{item.description}</p> : null}
              {item.dietary_tags.length ? <p className="text-xs text-teal">{item.dietary_tags.join(" · ").replace(/_/g, " ")}</p> : null}
              {(item.modifier_groups as ModifierGroup[]).some((g) => g.min_select > 0) ? (
                <p className="text-xs text-muted">Choose your options</p>
              ) : null}
              <div className="mt-auto flex items-center justify-between pt-2">
                <span className="text-lg font-semibold tabular-nums text-ink">{formatMoney(item.price)}</span>
                {!item.available_now ? <Badge>{item.next_available_at ? `From ${formatTime(item.next_available_at)}` : "Not available"}</Badge> : null}
              </div>
            </div>
          </button>
        ))}
      </section>
      {count ? (
        <div className="fixed inset-x-4 bottom-4 z-20 md:left-64">
          <Button size="xl" className="w-full shadow-xl" onClick={() => setReview(true)}>
            Review order · {count} item{count === 1 ? "" : "s"}
          </Button>
        </div>
      ) : null}
      {picking ? (
        <ItemDialog item={picking} onClose={() => setPicking(null)} onAdd={(l) => { setCart([...cart, l]); setPicking(null); }} />
      ) : null}
      {review ? <ReviewDialog cart={cart} setCart={setCart} onClose={() => setReview(false)} onOrdered={() => { setReview(false); onOrdered(); }} /> : null}
    </div>
  );
}

const QUICK_NOTES = ["No onion", "No salt", "Extra spicy", "Not spicy", "Sauce on the side", "No ice", "Cut in half"];

function ItemDialog({ item, onClose, onAdd }: { item: MenuItem; onClose: () => void; onAdd: (l: CartLine) => void }) {
  const groups = item.modifier_groups as ModifierGroup[];
  const [quantity, setQuantity] = useState(1);
  const [picked, setPicked] = useState<string[]>([]);
  const [note, setNote] = useState("");
  const [tried, setTried] = useState(false);
  const count = (g: ModifierGroup) => g.options.filter((o) => picked.includes(o.id)).length;
  const missing = groups.filter((g) => count(g) < g.min_select);
  const valid = missing.length === 0 && groups.every((g) => count(g) <= g.max_select);
  const toggle = (g: ModifierGroup, id: string) => {
    const inGroup = picked.filter((p) => g.options.some((o) => o.id === p));
    if (picked.includes(id)) return setPicked(picked.filter((p) => p !== id));
    if (g.max_select === 1) return setPicked([...picked.filter((p) => !inGroup.includes(p)), id]);
    if (inGroup.length < g.max_select) setPicked([...picked, id]);
  };
  // Shown for guidance only; the server prices the order and the guest confirms its total.
  const extras = groups.flatMap((g) => g.options).filter((o) => picked.includes(o.id)).reduce((sum, o) => sum + o.price_delta.amount_minor, 0);
  const lineTotal = { amount_minor: (item.price.amount_minor + extras) * quantity, currency: item.price.currency };
  const addQuick = (q: string) => setNote((n) => (n.toLowerCase().includes(q.toLowerCase()) ? n : (n ? `${n}, ${q}` : q).slice(0, 200)));
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title={item.name}
      footer={
        <div className="flex w-full flex-wrap items-center gap-3">
          <Button size="lg" variant="secondary" aria-label="One fewer" onClick={() => setQuantity(Math.max(1, quantity - 1))}>
            −
          </Button>
          <span className="w-8 text-center text-xl font-semibold tabular-nums">{quantity}</span>
          <Button size="lg" variant="secondary" aria-label="One more" onClick={() => setQuantity(Math.min(20, quantity + 1))}>
            +
          </Button>
          <span className="flex-1" />
          <Button size="lg" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            size="lg"
            onClick={() => {
              if (!valid) return setTried(true);
              onAdd({ key: `${item.id}-${Date.now()}`, item, quantity, options: picked, note: note.trim() });
            }}
          >
            Add · {formatMoney(lineTotal)}
          </Button>
        </div>
      }
    >
      <div className="flex flex-col gap-5">
        {item.image_url ? (
          <img src={item.image_url} alt={item.name} className="max-h-72 w-full rounded-[var(--radius-card)] object-cover" />
        ) : null}
        {item.description ? <p className="text-lg text-ink">{item.description}</p> : null}
        {item.ingredients.length ? (
          <p className="text-muted">
            <span className="font-semibold text-ink">Ingredients: </span>
            {item.ingredients.join(", ")}
          </p>
        ) : null}
        {item.allergens.length ? (
          <p className="rounded-lg bg-warn-bg px-3 py-2 font-medium text-warn">
            Contains {item.allergens.join(", ").replace(/_/g, " ")}. Tell us about any allergy in your message.
          </p>
        ) : null}
        {groups.map((g) => {
          const short = tried && count(g) < g.min_select;
          return (
            <fieldset key={g.id} className={short ? "rounded-lg ring-2 ring-crit ring-offset-4 ring-offset-surface" : undefined}>
              <legend className="mb-2 font-semibold text-ink">
                {g.name}{" "}
                {g.min_select ? (
                  <Badge tone={short ? "crit" : "warn"}>Required{g.max_select > 1 ? `, choose ${g.min_select}–${g.max_select}` : ""}</Badge>
                ) : (
                  <span className="font-normal text-muted">(optional{g.max_select > 1 ? `, up to ${g.max_select}` : ""})</span>
                )}
              </legend>
              <div className="flex flex-wrap gap-2">
                {g.options.filter((o) => o.is_available).map((o) => (
                  <Button key={o.id} size="lg" variant={picked.includes(o.id) ? "primary" : "secondary"} aria-pressed={picked.includes(o.id)} onClick={() => toggle(g, o.id)}>
                    {o.name}
                    {o.price_delta.amount_minor ? ` +${formatMoney(o.price_delta)}` : ""}
                  </Button>
                ))}
              </div>
              {short ? <p className="mt-2 font-medium text-crit">Please choose your {g.name.toLowerCase()}.</p> : null}
            </fieldset>
          );
        })}
        <Field label="Message to the kitchen (optional)">
          {(p) => (
            <Textarea {...p} maxLength={200} placeholder="For example: no onion, or an allergy we should know about" value={note} onChange={(e) => setNote(e.target.value)} />
          )}
        </Field>
        <div className="-mt-3 flex flex-wrap gap-2">
          {QUICK_NOTES.map((q) => (
            <Button key={q} size="sm" variant="ghost" onClick={() => addQuick(q)}>
              + {q}
            </Button>
          ))}
        </div>
      </div>
    </Dialog>
  );
}

/** The server prices the cart; the guest confirms that exact total. */
function ReviewDialog({ cart, setCart, onClose, onOrdered }: { cart: CartLine[]; setCart: (c: CartLine[]) => void; onClose: () => void; onOrdered: () => void }) {
  const [instructions, setInstructions] = useState("");
  const lines = useMemo(
    () => cart.map((l) => ({ menu_item_id: l.item.id, quantity: l.quantity, modifier_option_ids: l.options, note: l.note || null })),
    [cart],
  );
  const quote = useQuery({
    queryKey: ["quote", JSON.stringify(lines)],
    queryFn: () => ok(api.POST("/api/v1/guest/orders/quote", { body: { lines } })),
    enabled: lines.length > 0,
  });
  const place = useMutation({
    mutationFn: (q: Quote) => ok(api.POST("/api/v1/guest/orders", { body: { lines, payment_method: "room_charge", quoted_total: q.total, special_instructions: instructions.trim() || null } })),
    onSuccess: onOrdered,
  });
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title="Your order"
      description="Charged to your room. Large orders may need the hotel's approval before the kitchen starts."
      footer={
        <>
          <Button size="lg" variant="secondary" onClick={onClose}>
            Keep browsing
          </Button>
          <Button size="lg" disabled={!quote.data || cart.length === 0} loading={place.isPending} onClick={() => quote.data && place.mutate(quote.data)}>
            {quote.data ? `Place order · ${formatMoney(quote.data.total)}` : "Pricing…"}
          </Button>
        </>
      }
    >
      <ul className="divide-y divide-line">
        {(quote.data?.lines ?? []).map((l, i) => (
          <li key={i} className="flex items-center justify-between gap-3 py-3">
            <span className="text-ink">
              {l.quantity}× {l.name}
              {l.modifiers.length ? <span className="block text-sm text-muted">{l.modifiers.map((m) => m.name).join(", ")}</span> : null}
            </span>
            <span className="flex items-center gap-3">
              <span className="tabular-nums">{formatMoney(l.line_total)}</span>
              <Button size="sm" variant="ghost" onClick={() => setCart(cart.filter((_, n) => n !== i))}>
                Remove
              </Button>
            </span>
          </li>
        ))}
      </ul>
      {quote.data?.fee.amount_minor ? (
        <p className="flex justify-between py-2 text-muted">
          <span>Room-service fee</span>
          <span>{formatMoney(quote.data.fee)}</span>
        </p>
      ) : null}
      <Field label="Anything we should know? (optional)" className="mt-3">
        {(p) => <Textarea {...p} maxLength={500} value={instructions} onChange={(e) => setInstructions(e.target.value)} />}
      </Field>
      {quote.error ? <ErrorNotice error={quote.error} className="mt-3" /> : null}
      {place.error ? <ErrorNotice error={place.error} className="mt-3" /> : null}
    </Dialog>
  );
}

const STEPS = ["NEW", "ACCEPTED", "PREPARING", "READY", "PICKED_UP", "DELIVERED"];
const STEP_LABEL: Record<string, string> = {
  PENDING_APPROVAL: "Waiting for the hotel to confirm",
  NEW: "Received",
  ACCEPTED: "Accepted by the kitchen",
  PREPARING: "Being prepared",
  READY: "Ready, on its way soon",
  ASSIGNED: "Ready, on its way soon",
  PICKED_UP: "On its way to you",
  DELIVERED: "Delivered",
  CLOSED: "Delivered",
  DECLINED: "Not accepted",
  CANCELLED: "Cancelled",
};

function OrdersTab() {
  const orders = useQuery({ queryKey: ["orders"], queryFn: () => ok(api.GET("/api/v1/guest/orders")), refetchInterval: 30_000 });
  const list = orders.data?.data ?? [];
  return (
    <section className="mx-auto flex max-w-3xl flex-col gap-4 p-4">
      {orders.isLoading ? <Spinner className="mx-auto size-8 text-muted" /> : null}
      {!orders.isLoading && list.length === 0 ? <p className="p-6 text-center text-muted">No orders yet.</p> : null}
      {list.map((o) => {
        const at = Math.max(0, STEPS.indexOf(o.status === "ASSIGNED" ? "READY" : o.status === "CLOSED" ? "DELIVERED" : o.status));
        const stopped = ["DECLINED", "CANCELLED"].includes(o.status);
        return (
          <article key={o.id} className="rounded-[var(--radius-card)] border border-line bg-surface p-5">
            <div className="flex justify-between gap-3">
              <p className="font-display text-lg font-semibold">Order #{o.number}</p>
              <p className="text-lg font-semibold tabular-nums">{formatMoney(o.total)}</p>
            </div>
            <Badge tone={stopped ? "crit" : o.status === "PENDING_APPROVAL" ? "warn" : "info"} className="mt-2 text-sm">
              {STEP_LABEL[o.status] ?? o.status}
            </Badge>
            {!stopped && o.status !== "PENDING_APPROVAL" ? (
              <div className="mt-3 flex gap-1" aria-hidden>
                {STEPS.map((s, i) => (
                  <span key={s} className={cn("h-2 flex-1 rounded-full", i <= at ? "bg-blue" : "bg-line")} />
                ))}
              </div>
            ) : null}
            {o.decline_reason ? <p className="mt-2 text-sm text-muted">{o.decline_reason}</p> : null}
            <p className="mt-2 text-sm text-muted">{o.items.map((i) => `${i.quantity}× ${i.name}`).join(", ")}</p>
          </article>
        );
      })}
    </section>
  );
}

function BillTab() {
  const folio = useQuery({ queryKey: ["folio"], queryFn: () => ok(api.GET("/api/v1/guest/folio")) });
  const f = folio.data;
  if (!f) return <Spinner className="m-10 size-8 text-muted" />;
  const totals = f.totals as Record<string, components["schemas"]["Money"] | undefined>;
  const rows: [string, string][] = [
    ["Accommodation", "accommodation"],
    ["Food & beverage", "food_and_beverage"],
    ["Other", "other"],
    ["Paid", "paid"],
  ];
  return (
    <section className="mx-auto max-w-xl p-4">
      <div className="rounded-[var(--radius-card)] border border-line bg-surface p-6">
        <dl className="space-y-3 text-lg">
          {rows.map(([label, key]) =>
            totals[key] ? (
              <div key={key} className="flex justify-between">
                <dt className="text-muted">{label}</dt>
                <dd className="tabular-nums">{formatMoney(totals[key])}</dd>
              </div>
            ) : null,
          )}
          <div className="flex justify-between border-t border-line pt-3 text-xl font-semibold">
            <dt>Balance</dt>
            <dd className="tabular-nums">{formatMoney(totals.balance)}</dd>
          </div>
        </dl>
        {totals.tips?.amount_minor ? (
          <p className="mt-4 text-sm text-muted">Tips of {formatMoney(totals.tips)} go to the staff and are not part of your bill.</p>
        ) : null}
      </div>
      <p className="mt-4 text-center text-muted">You settle your bill at reception when you check out.</p>
    </section>
  );
}

function InfoTab() {
  const info = useQuery({ queryKey: ["info"], queryFn: () => ok(api.GET("/api/v1/guest/info")) });
  const i = info.data;
  if (!i) return <Spinner className="m-10 size-8 text-muted" />;
  return (
    <section className="mx-auto max-w-xl p-4">
      <div className="flex flex-col gap-2 rounded-[var(--radius-card)] border border-line bg-surface p-6 text-lg">
        <h2 className="font-display text-2xl font-semibold">{i.hotel_name}</h2>
        <p>Checkout by {i.checkout_time.slice(0, 5)}</p>
        {i.wifi_name ? <p>Wi-Fi: {i.wifi_name}</p> : null}
        {i.phone ? <p>Reception: {i.phone}</p> : null}
        {i.email ? <p>Email: {i.email}</p> : null}
      </div>
      {i.pages.map((p, n) => (
        <details key={n} className="mt-3 rounded-[var(--radius-card)] border border-line bg-surface p-5 text-lg" open={i.pages.length === 1}>
          <summary className="min-h-12 cursor-pointer font-display text-xl font-semibold">{p.title}</summary>
          <p className="mt-3 whitespace-pre-line text-ink">{p.body}</p>
        </details>
      ))}
    </section>
  );
}
