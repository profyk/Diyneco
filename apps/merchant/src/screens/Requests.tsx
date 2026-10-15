"use client";

import { type components, formatTime, ok } from "@diyneco/api-client";
import { Badge, Button, Card, Dialog, EmptyState, ErrorNotice, Field, Input, PageHeader, Select, Skeleton, Textarea } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { useAction } from "../common";
import { useSession } from "../session";

// Guest service requests (D93): towels, cleaning, repairs and wake-up calls, from the room's
// tablet or logged here from a phone call. Live: the board refreshes on every request event.

type Req = components["schemas"]["RequestOut"];
type Kind = components["schemas"]["StaffRequestCreate"]["kind"];

export const REQUEST_KINDS: Record<Kind, string> = {
  towels: "Towels",
  toiletries: "Toiletries",
  pillows: "Pillows or blankets",
  cleaning: "Room cleaning",
  turndown: "Turndown",
  maintenance: "Maintenance",
  wake_up: "Wake-up call",
  late_checkout: "Late checkout",
  luggage: "Luggage",
  other: "Other",
};

const STATUS: Record<string, { label: string; tone: "warn" | "info" | "good" | "neutral" | "crit" }> = {
  open: { label: "New", tone: "warn" },
  acknowledged: { label: "Seen", tone: "info" },
  in_progress: { label: "Under way", tone: "info" },
  done: { label: "Done", tone: "good" },
  cancelled: { label: "Cancelled", tone: "neutral" },
};

/** Minutes a request may wait before it shows as late: a wake-up call is late once its time passes. */
function late(r: Req, now: number): boolean {
  if (r.status === "done" || r.status === "cancelled") return false;
  if (r.due_at) return new Date(r.due_at).getTime() < now;
  return r.waiting_minutes >= (r.status === "open" ? 10 : 30);
}

export function Requests() {
  const { api, can } = useSession();
  const [scope, setScope] = useState<"open" | "recent">("open");
  const [kind, setKind] = useState<Kind | "">("");
  const [logging, setLogging] = useState(false);
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 30_000);
    return () => clearInterval(t);
  }, []);
  const board = useQuery({
    queryKey: ["requests", scope, kind],
    queryFn: () => ok(api.GET("/api/v1/requests", { params: { query: { scope, kind: kind || undefined } } })),
    refetchInterval: 15_000,
  });
  const staff = useQuery({ queryKey: ["staff"], queryFn: () => ok(api.GET("/api/v1/staff")), enabled: can("staff.read") });
  const roles = useQuery({ queryKey: ["roles"], queryFn: () => ok(api.GET("/api/v1/roles")), enabled: can("staff.read") });
  const handlerRoles = new Set((roles.data?.data ?? []).filter((r) => r.permissions.includes("requests.update")).map((r) => r.id));
  const handlers = (staff.data?.data ?? []).filter((s) => s.status === "active" && s.roles.some((r) => handlerRoles.has(r.id)));
  const update = can("requests.update");

  const path = (id: string) => ({ params: { path: { request_id: id } } });
  const step = useAction(
    ({ id, to }: { id: string; to: "acknowledge" | "start" | "done" }) =>
      ok(
        to === "acknowledge"
          ? api.POST("/api/v1/requests/{request_id}/acknowledge", path(id))
          : to === "start"
            ? api.POST("/api/v1/requests/{request_id}/start", path(id))
            : api.POST("/api/v1/requests/{request_id}/done", path(id)),
      ),
    { success: (r) => `Room ${r.room}: ${STATUS[r.status]?.label ?? r.status}.` },
  );
  const assign = useAction(
    ({ id, user }: { id: string; user: string }) => ok(api.POST("/api/v1/requests/{request_id}/assign", { ...path(id), body: { user_id: user } })),
    { success: (r) => `Room ${r.room}: given to ${r.assigned_to?.name ?? ""}.` },
  );
  const cancel = useAction(
    (id: string) => ok(api.POST("/api/v1/requests/{request_id}/cancel", { ...path(id), body: { reason: null } })),
    { success: (r) => `Room ${r.room}: request cancelled.` },
  );

  const rows = board.data?.data ?? [];
  const s = board.data?.summary;
  const error = step.error ?? assign.error ?? cancel.error;

  return (
    <>
      <PageHeader
        title="Guest requests"
        description="Towels, cleaning, repairs and wake-up calls from the room tablets, live."
        actions={update ? <Button onClick={() => setLogging(true)}>Log a request</Button> : null}
      />
      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Tile label="Waiting" value={s?.open} warn={(s?.open ?? 0) > 0} />
        <Tile label="Under way" value={s?.in_progress} />
        <Tile label="Done today" value={s?.done_today} />
        <Tile label="Typical time to done (7 days)" value={s?.median_minutes_to_done == null ? "—" : `${s.median_minutes_to_done} min`} />
      </div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex gap-1 rounded-full bg-surface-2 p-1" role="tablist" aria-label="Which requests">
          {(["open", "recent"] as const).map((k) => (
            <button
              key={k}
              type="button"
              role="tab"
              aria-selected={scope === k}
              onClick={() => setScope(k)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium ${scope === k ? "bg-surface text-ink shadow-sm" : "text-muted"}`}
            >
              {k === "open" ? "Waiting and under way" : "Last 7 days"}
            </button>
          ))}
        </div>
        <Select aria-label="Kind" value={kind} onChange={(e) => setKind(e.target.value as Kind | "")} className="w-auto">
          <option value="">Every kind</option>
          {Object.entries(REQUEST_KINDS).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
      </div>
      {error ? <ErrorNotice error={error} className="mb-4" /> : null}
      {board.isLoading ? (
        <Skeleton className="h-60" />
      ) : board.error ? (
        <ErrorNotice error={board.error} />
      ) : rows.length === 0 ? (
        <Card>
          <EmptyState title={scope === "open" ? "Nothing waiting" : "No requests in the last 7 days"} body="Requests from the room tablets appear here the moment they are sent." />
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {rows.map((r) => {
            const st = STATUS[r.status] ?? { label: r.status, tone: "neutral" as const };
            const isLate = late(r, now);
            const live = r.status === "open" || r.status === "acknowledged" || r.status === "in_progress";
            return (
              <Card key={r.id} className={`flex flex-col gap-2 p-4 ${isLate ? "border-crit" : ""}`}>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-display text-lg font-semibold text-ink">Room {r.room}</p>
                    <p className="text-sm font-medium text-ink">
                      {REQUEST_KINDS[r.kind as Kind] ?? r.kind}
                      {r.due_at ? <span className="text-muted"> · for {formatTime(r.due_at)}</span> : null}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <Badge tone={st.tone}>{st.label}</Badge>
                    {live ? <Badge tone={isLate ? "crit" : "neutral"}>{r.waiting_minutes} min</Badge> : null}
                  </div>
                </div>
                {r.note ? <p className="rounded bg-surface-2 p-2 text-sm text-ink">{r.note}</p> : null}
                <p className="text-xs text-muted">
                  {r.source === "guest" ? "From the room tablet" : `Logged by ${r.created_by?.name ?? "staff"}`} at {formatTime(r.created_at)}
                  {r.assigned_to ? ` · with ${r.assigned_to.name}` : ""}
                  {r.cancel_reason ? ` · ${r.cancel_reason}` : ""}
                </p>
                {update && live ? (
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    {r.status === "open" ? (
                      <Button size="sm" variant="secondary" onClick={() => step.mutate({ id: r.id, to: "acknowledge" })}>
                        Seen
                      </Button>
                    ) : null}
                    {r.status !== "in_progress" ? (
                      <Button size="sm" variant="secondary" onClick={() => step.mutate({ id: r.id, to: "start" })}>
                        I'm on it
                      </Button>
                    ) : null}
                    <Button size="sm" onClick={() => step.mutate({ id: r.id, to: "done" })}>
                      Done
                    </Button>
                    {handlers.length ? (
                      <Select aria-label={`Give room ${r.room}'s request to`} value="" onChange={(e) => e.target.value && assign.mutate({ id: r.id, user: e.target.value })} className="w-auto">
                        <option value="">{r.assigned_to ? "Reassign…" : "Give to…"}</option>
                        {handlers.map((h) => (
                          <option key={h.user_id} value={h.user_id}>
                            {h.name}
                          </option>
                        ))}
                      </Select>
                    ) : null}
                    <Button size="sm" variant="ghost" onClick={() => cancel.mutate(r.id)}>
                      Cancel
                    </Button>
                  </div>
                ) : null}
              </Card>
            );
          })}
        </div>
      )}
      {logging ? <LogDialog onClose={() => setLogging(false)} /> : null}
    </>
  );
}

function Tile({ label, value, warn = false }: { label: string; value: number | string | undefined; warn?: boolean }) {
  return (
    <Card className="p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className={`mt-1 font-display text-2xl font-semibold tabular-nums ${warn ? "text-warn" : "text-ink"}`}>{value ?? "…"}</p>
    </Card>
  );
}

function LogDialog({ onClose }: { onClose: () => void }) {
  const { api } = useSession();
  const rooms = useQuery({ queryKey: ["rooms"], queryFn: () => ok(api.GET("/api/v1/rooms")) });
  const [room, setRoom] = useState("");
  const [kind, setKind] = useState<Kind>("towels");
  const [note, setNote] = useState("");
  const [when, setWhen] = useState("");
  const save = useAction(
    () =>
      ok(
        api.POST("/api/v1/requests", {
          body: { room_id: room, kind, note: note.trim() || null, due_at: when ? new Date(when).toISOString() : null },
        }),
      ),
    { success: (r) => `Logged for room ${r.room}.`, onDone: onClose },
  );
  const timed = kind === "wake_up" || kind === "late_checkout";
  return (
    <Dialog open onClose={onClose} title="Log a request" description="For a request by phone or at the desk. The team sees it straight away.">
      <div className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Room">
            {(p) => (
              <Select {...p} value={room} onChange={(e) => setRoom(e.target.value)}>
                <option value="">Choose a room</option>
                {(rooms.data?.data ?? []).map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.number}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="What">
            {(p) => (
              <Select {...p} value={kind} onChange={(e) => setKind(e.target.value as Kind)}>
                {Object.entries(REQUEST_KINDS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </Select>
            )}
          </Field>
        </div>
        <Field label={timed ? "When" : "When (optional)"} hint="Hotel time, within the next two weeks.">
          {(p) => <Input {...p} type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} />}
        </Field>
        <Field label="Note (optional)">
          {(p) => <Textarea {...p} rows={3} maxLength={300} value={note} onChange={(e) => setNote(e.target.value)} />}
        </Field>
        {save.error ? <ErrorNotice error={save.error} /> : null}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
          <Button loading={save.isPending} disabled={!room || (kind === "wake_up" && !when)} onClick={() => save.mutate(undefined)}>
            Log request
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
