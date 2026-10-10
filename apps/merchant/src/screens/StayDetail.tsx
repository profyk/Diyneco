"use client";

import { ApiError, formatDate, formatMoney, formatTime, ok, parseAmount } from "@diyneco/api-client";
import {
  Badge,
  Button,
  Card,
  CardHeader,
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
  useToast,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { label, StayStatus, useAction } from "../common";
import { useSession } from "../session";

type Panel = null | "charge" | "discount" | "payment" | "dates" | "move" | "checkout" | { adjust: string };

export function StayDetail({ id }: { id: string }) {
  const { api, can } = useSession();
  const [panel, setPanel] = useState<Panel>(null);
  const stay = useQuery({
    queryKey: ["stays", id],
    queryFn: () => ok(api.GET("/api/v1/stays/{stay_id}", { params: { path: { stay_id: id } } })),
  });
  const folio = useQuery({
    queryKey: ["folio", id],
    queryFn: () => ok(api.GET("/api/v1/folios/{stay_id}", { params: { path: { stay_id: id } } })),
    enabled: can("folio.read") && Boolean(stay.data?.folio),
  });
  const invoices = useQuery({
    queryKey: ["invoices", id],
    queryFn: () => ok(api.GET("/api/v1/stays/{stay_id}/invoices", { params: { path: { stay_id: id } } })),
    enabled: can("invoices.read") && Boolean(stay.data?.folio),
  });
  const checkIn = useAction(
    () => ok(api.POST("/api/v1/stays/{stay_id}/check-in", { params: { path: { stay_id: id } } })),
    { success: "Checked in. The room's tablet is ready." },
  );
  const cancel = useAction(
    () => ok(api.POST("/api/v1/stays/{stay_id}/cancel", { params: { path: { stay_id: id } } })),
    { success: "Reservation cancelled." },
  );

  if (stay.isLoading) return <Skeleton className="h-40" />;
  if (stay.error || !stay.data) return <ErrorNotice error={stay.error} />;
  const s = stay.data;
  const f = folio.data;
  const open = f?.status === "open";
  const live = ["active", "checkout_pending"].includes(s.status);

  return (
    <>
      <PageHeader
        title={`Room ${s.room.number} · ${s.guest.name}`}
        description={
          <>
            {formatDate(s.arrival_date)} – {formatDate(s.departure_date)} · {s.nights} night{s.nights === 1 ? "" : "s"} at{" "}
            {formatMoney(s.nightly_rate)}
          </>
        }
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <StayStatus status={s.status} />
            {s.status === "reserved" && can("stays.manage") ? (
              <>
                <Button variant="secondary" loading={cancel.isPending} onClick={() => cancel.mutate(undefined)}>
                  Cancel reservation
                </Button>
                <Button loading={checkIn.isPending} onClick={() => checkIn.mutate(undefined)}>
                  Check in
                </Button>
              </>
            ) : null}
            {(s.status === "reserved" || live) && can("stays.manage") ? (
              <>
                <Button variant="secondary" onClick={() => setPanel("dates")}>
                  Change dates
                </Button>
                <Button variant="secondary" onClick={() => setPanel("move")}>
                  Move room
                </Button>
              </>
            ) : null}
            {open && can("checkout.perform") && (live || s.status === "checked_out") ? (
              <Button onClick={() => setPanel("checkout")}>{s.status === "checked_out" ? "Issue new bill" : "Check out"}</Button>
            ) : null}
          </div>
        }
      />
      {checkIn.error || cancel.error ? <ErrorNotice error={checkIn.error ?? cancel.error} className="mb-4" /> : null}

      {f ? (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader
              title="Bill"
              description={open ? "Charges, payments and corrections, as they were posted." : "Closed at checkout."}
              actions={
                open ? (
                  <>
                    {can("folio.charge") ? (
                      <Button size="sm" variant="secondary" onClick={() => setPanel("charge")}>
                        Add charge
                      </Button>
                    ) : null}
                    {can("folio.discount") ? (
                      <Button size="sm" variant="secondary" onClick={() => setPanel("discount")}>
                        Discount
                      </Button>
                    ) : null}
                    {can("payments.record") ? (
                      <Button size="sm" onClick={() => setPanel("payment")}>
                        Take payment
                      </Button>
                    ) : null}
                  </>
                ) : null
              }
            />
            <Table>
              <thead>
                <tr>
                  <Th>Date</Th>
                  <Th>Description</Th>
                  <Th>Type</Th>
                  <Th className="text-right">Amount</Th>
                  <Th />
                </tr>
              </thead>
              <tbody>
                {f.entries.map((e) => (
                  <tr key={e.id} className={e.type === "tip" ? "text-muted" : undefined}>
                    <Td className="whitespace-nowrap text-muted">{formatDate(e.business_date)}</Td>
                    <Td>
                      {e.quantity > 1 ? `${e.quantity}× ` : ""}
                      {e.description}
                    </Td>
                    <Td>
                      <Badge tone={e.type === "payment" ? "good" : e.type === "tip" ? "teal" : e.type === "charge" ? "neutral" : "warn"}>
                        {e.type === "tip" ? "Tip (not on bill)" : label(e.type)}
                      </Badge>
                    </Td>
                    <Td className="text-right tabular-nums">{formatMoney(e.amount)}</Td>
                    <Td className="text-right">
                      {open && e.type === "charge" && can("folio.adjust.request") ? (
                        <button type="button" className="text-xs text-blue hover:underline" onClick={() => setPanel({ adjust: e.id })}>
                          Adjust
                        </button>
                      ) : null}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card>
          <div className="flex flex-col gap-6">
            <Card className="p-5">
              <h2 className="font-display text-base font-semibold text-ink">Summary</h2>
              <dl className="mt-3 space-y-2 text-sm">
                {(
                  [
                    ["Accommodation", f.totals.accommodation],
                    ["Food & beverage", f.totals.fnb],
                    ["Other services", f.totals.other],
                    ["VAT included", f.totals.vat_included],
                    ["Paid", f.totals.paid],
                  ] as const
                ).map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <dt className="text-muted">{k}</dt>
                    <dd className="tabular-nums">{formatMoney(v)}</dd>
                  </div>
                ))}
                <div className="flex justify-between border-t border-line pt-2 text-base font-semibold">
                  <dt>Balance</dt>
                  <dd className="tabular-nums">{formatMoney(f.totals.balance)}</dd>
                </div>
                <div className="flex justify-between text-muted">
                  <dt>Tips for staff</dt>
                  <dd className="tabular-nums">{formatMoney(f.totals.tips)}</dd>
                </div>
              </dl>
            </Card>
            {can("invoices.read") ? <Invoices data={invoices.data?.data ?? []} /> : null}
          </div>
        </div>
      ) : s.status === "reserved" ? (
        <Card>
          <EmptyState title="No bill yet" body="The bill opens when the guest checks in." />
        </Card>
      ) : null}

      {panel === "charge" ? <ChargeDialog stayId={id} onClose={() => setPanel(null)} /> : null}
      {panel === "discount" ? <DiscountDialog stayId={id} onClose={() => setPanel(null)} /> : null}
      {panel === "payment" ? <PaymentDialog stayId={id} onClose={() => setPanel(null)} /> : null}
      {panel === "dates" ? <DatesDialog stayId={id} onClose={() => setPanel(null)} /> : null}
      {panel === "move" ? <MoveDialog stayId={id} onClose={() => setPanel(null)} /> : null}
      {panel === "checkout" ? <CheckoutDialog stayId={id} onClose={() => setPanel(null)} /> : null}
      {panel && typeof panel === "object" ? <AdjustDialog entryId={panel.adjust} onClose={() => setPanel(null)} /> : null}
    </>
  );
}

function amountOrNull(text: string) {
  const minor = parseAmount(text);
  return minor === null ? null : { amount_minor: minor, currency: "ZAR" };
}

function ChargeDialog({ stayId, onClose }: { stayId: string; onClose: () => void }) {
  const { api } = useSession();
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [quantity, setQuantity] = useState("1");
  const categories = useQuery({
    queryKey: ["charge-categories"],
    queryFn: () => ok(api.GET("/api/v1/charge-categories")),
  });
  const save = useAction(
    () =>
      ok(
        api.POST("/api/v1/folios/{stay_id}/charges", {
          params: { path: { stay_id: stayId } },
          body: { charge_category_id: category, description: description.trim(), amount: amountOrNull(amount)!, quantity: Number(quantity) },
        }),
      ),
    { success: "Charge added.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title="Add a charge"
      description="Laundry, minibar, spa and other services. Prices include VAT if the hotel is registered."
      footer={
        <Button disabled={!category || !description.trim() || !amountOrNull(amount)} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Add charge
        </Button>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Category">
          {(p) => (
            <Select {...p} value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">Choose</option>
              {categories.data?.data.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Description">{(p) => <Input {...p} value={description} onChange={(e) => setDescription(e.target.value)} />}</Field>
        <Field label="Unit price (R)">{(p) => <Input {...p} inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} />}</Field>
        <Field label="Quantity">
          {(p) => <Input {...p} type="number" min={1} value={quantity} onChange={(e) => setQuantity(e.target.value)} />}
        </Field>
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

function DiscountDialog({ stayId, onClose }: { stayId: string; onClose: () => void }) {
  const { api } = useSession();
  const [kind, setKind] = useState<"percent" | "fixed">("percent");
  const [value, setValue] = useState("");
  const [appliesTo, setAppliesTo] = useState<"all" | "accommodation" | "fnb" | "other">("all");
  const [reason, setReason] = useState("");
  const percentBp = Math.round(Number(value) * 100);
  const valid = kind === "percent" ? percentBp >= 1 && percentBp <= 10000 : Boolean(amountOrNull(value));
  const save = useAction(
    () =>
      ok(
        api.POST("/api/v1/folios/{stay_id}/discounts", {
          params: { path: { stay_id: stayId } },
          body:
            kind === "percent"
              ? { kind, percent_bp: percentBp, applies_to: appliesTo, reason: reason.trim() }
              : { kind, amount: amountOrNull(value)!, applies_to: appliesTo, reason: reason.trim() },
        }),
      ),
    { success: "Discount applied.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title="Give a discount"
      description="Recorded with your name and reason, and shown on the daily close."
      footer={
        <Button disabled={!valid || !reason.trim()} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Apply discount
        </Button>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Type">
          {(p) => (
            <Select {...p} value={kind} onChange={(e) => setKind(e.target.value as "percent" | "fixed")}>
              <option value="percent">Percentage</option>
              <option value="fixed">Fixed amount</option>
            </Select>
          )}
        </Field>
        <Field label={kind === "percent" ? "Percent" : "Amount (R)"}>
          {(p) => <Input {...p} inputMode="decimal" value={value} onChange={(e) => setValue(e.target.value)} />}
        </Field>
        <Field label="Applies to">
          {(p) => (
            <Select {...p} value={appliesTo} onChange={(e) => setAppliesTo(e.target.value as typeof appliesTo)}>
              <option value="all">Whole bill</option>
              <option value="accommodation">Accommodation</option>
              <option value="fnb">Food & beverage</option>
              <option value="other">Other services</option>
            </Select>
          )}
        </Field>
        <Field label="Reason" className="sm:col-span-2">
          {(p) => <Textarea {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}
        </Field>
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

function AdjustDialog({ entryId, onClose }: { entryId: string; onClose: () => void }) {
  const { api } = useSession();
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const save = useAction(
    () =>
      ok(
        api.POST("/api/v1/adjustments", {
          body: { folio_entry_id: entryId, new_amount: amountOrNull(amount)!, reason: reason.trim() },
        }),
      ),
    { success: "Adjustment requested. Another manager must approve it.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title="Request an adjustment"
      description="Charges are never edited. A second manager approves a correcting entry."
      footer={
        <Button disabled={!amountOrNull(amount) || reason.trim().length < 3} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Request
        </Button>
      }
    >
      <div className="grid gap-4">
        <Field label="Correct amount (R)">{(p) => <Input {...p} inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} />}</Field>
        <Field label="Reason">{(p) => <Textarea {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}</Field>
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

/** Reception settles the bill: the server works out what is due and any tip. */
function PaymentDialog({ stayId, onClose }: { stayId: string; onClose: () => void }) {
  const { api } = useSession();
  const toast = useToast();
  const [method, setMethod] = useState<"card_terminal" | "cash" | "eft">("card_terminal");
  const [received, setReceived] = useState("");
  const [reference, setReference] = useState("");
  const [confirmTip, setConfirmTip] = useState(false);
  const money = amountOrNull(received);
  const preview = useQuery({
    queryKey: ["payment-preview", stayId, money?.amount_minor],
    queryFn: () => ok(api.POST("/api/v1/payments/preview", { body: { stay_id: stayId, amount_received: money! } })),
    enabled: Boolean(money),
  });
  const save = useAction(
    () =>
      ok(
        api.POST("/api/v1/payments", {
          body: {
            stay_id: stayId,
            method,
            amount_received: money!,
            confirm_tip: confirmTip,
            terminal_reference: method === "card_terminal" ? reference.trim() : null,
          },
        }),
      ),
    {
      onDone: (p) => {
        toast("good", p.tip.amount_minor ? `Payment recorded with a ${formatMoney(p.tip)} tip.` : "Payment recorded.");
        onClose();
      },
    },
  );
  const tip = preview.data?.tip.amount_minor ?? 0;
  const tipNeedsConfirm = tip > 0 && !confirmTip;
  return (
    <Dialog
      open
      onClose={onClose}
      title="Take payment"
      description="Card numbers are never entered here; use the hotel's card machine and type its approval reference."
      footer={
        <Button
          disabled={!money || tipNeedsConfirm || (method === "card_terminal" && !/^[A-Za-z0-9-]{4,20}$/.test(reference.trim()))}
          loading={save.isPending}
          onClick={() => save.mutate(undefined)}
        >
          Record payment
        </Button>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Method">
          {(p) => (
            <Select {...p} value={method} onChange={(e) => setMethod(e.target.value as typeof method)}>
              <option value="card_terminal">Card machine</option>
              <option value="cash">Cash</option>
              <option value="eft">EFT</option>
            </Select>
          )}
        </Field>
        <Field label="Amount received (R)">{(p) => <Input {...p} inputMode="decimal" value={received} onChange={(e) => setReceived(e.target.value)} />}</Field>
        {method === "card_terminal" ? (
          <Field label="Card machine reference" hint="4–20 letters or digits from the slip">
            {(p) => <Input {...p} value={reference} onChange={(e) => setReference(e.target.value)} autoComplete="off" />}
          </Field>
        ) : null}
      </div>
      {preview.data ? (
        <dl className="mt-4 space-y-1 rounded-lg bg-surface-2 p-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-muted">Due</dt>
            <dd className="tabular-nums">{formatMoney(preview.data.amount_due)}</dd>
          </div>
          {preview.data.shortfall.amount_minor ? (
            <div className="flex justify-between text-warn">
              <dt>Still owing after this (part payment)</dt>
              <dd className="tabular-nums">{formatMoney(preview.data.shortfall)}</dd>
            </div>
          ) : null}
          {tip ? (
            <div className="flex justify-between font-medium text-teal">
              <dt>Tip for staff (not hotel revenue)</dt>
              <dd className="tabular-nums">{formatMoney(preview.data.tip)}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}
      {tip ? (
        <label className="mt-3 flex items-center gap-2 text-sm text-ink">
          <input type="checkbox" checked={confirmTip} onChange={(e) => setConfirmTip(e.target.checked)} />
          The guest confirmed the {formatMoney(preview.data?.tip)} tip
        </label>
      ) : null}
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

function DatesDialog({ stayId, onClose }: { stayId: string; onClose: () => void }) {
  const { api } = useSession();
  const stay = useQuery({
    queryKey: ["stays", stayId, "etag"],
    queryFn: async () => {
      const r = await api.GET("/api/v1/stays/{stay_id}", { params: { path: { stay_id: stayId } } });
      return { data: r.data!, etag: r.response.headers.get("ETag") ?? "" };
    },
  });
  const [departure, setDeparture] = useState("");
  const [arrival, setArrival] = useState("");
  const save = useAction(
    () =>
      ok(
        api.PATCH("/api/v1/stays/{stay_id}", {
          params: { path: { stay_id: stayId }, header: { "If-Match": stay.data!.etag } as never },
          body: { ...(departure ? { departure_date: departure } : {}), ...(arrival ? { arrival_date: arrival } : {}) },
        }),
      ),
    { success: "Dates changed; nights were posted or reversed on the bill.", onDone: onClose },
  );
  const s = stay.data?.data;
  return (
    <Dialog
      open
      onClose={onClose}
      title="Change dates"
      footer={
        <Button disabled={!s || (!departure && !arrival)} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Save
        </Button>
      }
    >
      {s ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {s.status === "reserved" ? (
            <Field label="Arrival">
              {(p) => <Input {...p} type="date" defaultValue={s.arrival_date} onChange={(e) => setArrival(e.target.value)} />}
            </Field>
          ) : null}
          <Field label="Departure">
            {(p) => <Input {...p} type="date" defaultValue={s.departure_date} onChange={(e) => setDeparture(e.target.value)} />}
          </Field>
        </div>
      ) : (
        <Skeleton />
      )}
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

function MoveDialog({ stayId, onClose }: { stayId: string; onClose: () => void }) {
  const { api } = useSession();
  const [roomId, setRoomId] = useState("");
  const [reason, setReason] = useState("");
  const rooms = useQuery({
    queryKey: ["rooms", "available"],
    queryFn: () => ok(api.GET("/api/v1/rooms", { params: { query: { status: "available", limit: 200 } } })),
  });
  const save = useAction(
    () => ok(api.POST("/api/v1/stays/{stay_id}/move", { params: { path: { stay_id: stayId } }, body: { room_id: roomId, reason: reason.trim() || null } })),
    { success: "Guest moved. Their tablet session followed them.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title="Move to another room"
      description="The nightly rate stays the same. The old room goes to cleaning and its tablet resets."
      footer={
        <Button disabled={!roomId} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Move guest
        </Button>
      }
    >
      <div className="grid gap-4">
        <Field label="New room">
          {(p) => (
            <Select {...p} value={roomId} onChange={(e) => setRoomId(e.target.value)}>
              <option value="">Choose an available room</option>
              {rooms.data?.data.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.number} · {r.room_type.name}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Reason (optional)">{(p) => <Input {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}</Field>
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

function CheckoutDialog({ stayId, onClose }: { stayId: string; onClose: () => void }) {
  const { api, can } = useSession();
  const toast = useToast();
  const summary = useQuery({
    queryKey: ["checkout-summary", stayId],
    queryFn: () => ok(api.GET("/api/v1/stays/{stay_id}/checkout-summary", { params: { path: { stay_id: stayId } } })),
  });
  const [email, setEmail] = useState(false);
  const [emailTo, setEmailTo] = useState("");
  const [override, setOverride] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const [confirmLong, setConfirmLong] = useState(false);
  const [address, setAddress] = useState({ line1: "", city: "", postal_code: "" });
  const [needAddress, setNeedAddress] = useState(false);

  const checkout = useAction(
    () =>
      ok(
        api.POST("/api/v1/stays/{stay_id}/checkout", {
          params: { path: { stay_id: stayId } },
          body: {
            override,
            override_reason: override ? overrideReason.trim() : null,
            bill_delivery: email ? ["pdf", "email"] : ["pdf"],
            email_to: email && emailTo.trim() ? [emailTo.trim()] : [],
            confirm_long_stay_vat: confirmLong,
            recipient_address: address.line1 ? { ...address, country: "ZA" } : null,
          },
        }),
      ),
    {
      onDone: (r) => {
        toast("good", `Checked out. ${r.invoice.title} ${r.invoice.number} issued; the room's tablet was reset.`);
        onClose();
      },
    },
  );
  const err = checkout.error;
  if (err instanceof ApiError && err.details.reason === "recipient_address_required" && !needAddress) setNeedAddress(true);

  const s = summary.data;
  const owing = (s?.totals.balance.amount_minor ?? 0) > 0;
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title="Check out"
      description="Closes the bill, issues the invoice and resets the room's tablet for the next guest. Asks for your PIN."
      footer={
        <Button
          disabled={!s || s.open_orders.length > 0 || (owing && !override) || (override && !overrideReason.trim()) || (s.flags.includes("long_stay") && !confirmLong)}
          loading={checkout.isPending}
          onClick={() => checkout.mutate(undefined)}
        >
          Check out and issue bill
        </Button>
      }
    >
      {!s ? (
        <Skeleton className="h-32" />
      ) : (
        <div className="flex flex-col gap-4 text-sm">
          <dl className="grid grid-cols-2 gap-2 rounded-lg bg-surface-2 p-3">
            <dt className="text-muted">Balance</dt>
            <dd className="text-right font-semibold tabular-nums">{formatMoney(s.totals.balance)}</dd>
            <dt className="text-muted">Tips (separate)</dt>
            <dd className="text-right tabular-nums">{formatMoney(s.totals.tips)}</dd>
            <dt className="text-muted">Document</dt>
            <dd className="text-right">{label(s.invoice_kind)}</dd>
          </dl>
          {s.open_orders.length ? (
            <p className="rounded-lg bg-warn-bg px-3 py-2 text-warn">
              Finish or cancel these orders first: {s.open_orders.map((o) => `#${o.number} (${label(o.status)})`).join(", ")}
            </p>
          ) : null}
          {owing ? (
            s.override_allowed && can("checkout.override") ? (
              <div className="rounded-lg border border-line p-3">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={override} onChange={(e) => setOverride(e.target.checked)} />
                  Check out with a balance (it goes to accounts receivable)
                </label>
                {override ? (
                  <Field label="Reason" className="mt-3">
                    {(p) => <Textarea {...p} value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} />}
                  </Field>
                ) : null}
              </div>
            ) : (
              <p className="rounded-lg bg-warn-bg px-3 py-2 text-warn">Take payment for the balance before checking out.</p>
            )
          ) : null}
          {s.flags.includes("long_stay") ? (
            <label className="flex items-start gap-2 rounded-lg bg-warn-bg px-3 py-2 text-warn">
              <input type="checkbox" className="mt-1" checked={confirmLong} onChange={(e) => setConfirmLong(e.target.checked)} />
              This stay is longer than 28 days, so VAT on accommodation may differ. I confirm the accommodation charges are correct.
            </label>
          ) : null}
          {needAddress || s.invoice_kind === "tax_invoice" ? (
            <div className="grid gap-3 sm:grid-cols-3">
              <p className="text-muted sm:col-span-3">A full tax invoice needs the guest&apos;s address (printed on the invoice only).</p>
              <Field label="Street">{(p) => <Input {...p} value={address.line1} onChange={(e) => setAddress({ ...address, line1: e.target.value })} />}</Field>
              <Field label="City">{(p) => <Input {...p} value={address.city} onChange={(e) => setAddress({ ...address, city: e.target.value })} />}</Field>
              <Field label="Postal code">{(p) => <Input {...p} value={address.postal_code} onChange={(e) => setAddress({ ...address, postal_code: e.target.value })} />}</Field>
            </div>
          ) : null}
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={email} onChange={(e) => setEmail(e.target.checked)} />
            Email the bill
          </label>
          {email ? (
            <Field label="Email to" hint="Leave empty to use the guest's or company's email.">
              {(p) => <Input {...p} type="email" value={emailTo} onChange={(e) => setEmailTo(e.target.value)} />}
            </Field>
          ) : null}
          {err ? <ErrorNotice error={err} /> : null}
        </div>
      )}
    </Dialog>
  );
}

function Invoices({ data }: { data: { id: string; number: string; title: string; kind: string; issued_at: string; totals: { charges: { amount_minor: number; currency: string } } }[] }) {
  const { api, can } = useSession();
  const toast = useToast();
  const [credit, setCredit] = useState<string | null>(null);
  const download = async (id: string) => {
    try {
      const r = await ok(api.GET("/api/v1/invoices/{invoice_id}/pdf", { params: { path: { invoice_id: id } } }));
      window.open(r.url, "_blank", "noopener");
    } catch (err) {
      toast("crit", (err as Error).message);
    }
  };
  return (
    <Card>
      <CardHeader title="Invoices" />
      {data.length === 0 ? (
        <EmptyState title="Issued at checkout" />
      ) : (
        <ul className="divide-y divide-line text-sm">
          {data.map((i) => (
            <li key={i.id} className="flex items-center justify-between gap-2 px-5 py-3">
              <div>
                <p className="font-medium text-ink">
                  {i.title} {i.number}
                </p>
                <p className="text-xs text-muted">
                  {formatDate(i.issued_at)} {formatTime(i.issued_at)} · {formatMoney(i.totals.charges)}
                </p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => void download(i.id)}>
                  PDF
                </Button>
                {i.kind !== "credit_note" && can("invoices.credit") ? (
                  <Button size="sm" variant="ghost" onClick={() => setCredit(i.id)}>
                    Credit
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
      {credit ? <CreditDialog invoiceId={credit} onClose={() => setCredit(null)} /> : null}
    </Card>
  );
}

function CreditDialog({ invoiceId, onClose }: { invoiceId: string; onClose: () => void }) {
  const { api } = useSession();
  const [reason, setReason] = useState("");
  const save = useAction(
    () => ok(api.POST("/api/v1/invoices/{invoice_id}/credit-note", { params: { path: { invoice_id: invoiceId } }, body: { reason: reason.trim() } })),
    { success: "Credit note issued; the bill is open for corrections.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      size="sm"
      title="Issue a credit note"
      description="Cancels the whole invoice and re-opens the bill. Check out again to issue a corrected invoice."
      footer={
        <Button variant="danger" disabled={reason.trim().length < 3} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Issue credit note
        </Button>
      }
    >
      <Field label="Reason">{(p) => <Textarea {...p} value={reason} onChange={(e) => setReason(e.target.value)} />}</Field>
      {save.error ? <ErrorNotice error={save.error} className="mt-3" /> : null}
    </Dialog>
  );
}
