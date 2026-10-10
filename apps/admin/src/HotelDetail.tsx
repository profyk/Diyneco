"use client";

import { formatDate, formatMoney, formatTime, ok } from "@diyneco/api-client";
import { Badge, Button, Card, CardHeader, Dialog, EmptyState, ErrorNotice, Field, Input, PageHeader, Skeleton } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { label, useAction } from "./common";
import { HotelDialog } from "./screens";
import { useSession } from "./session";

const LIMITS = [
  ["rooms", "Rooms"],
  ["devices", "Devices"],
  ["staff", "Staff"],
  ["api_keys", "API keys"],
] as const;
type LimitKey = (typeof LIMITS)[number][0];

function Usage({ used, limit, title }: { used: number | null; limit: number | null | undefined; title: string }) {
  const pct = limit && used !== null ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  return (
    <div>
      <div className="flex justify-between text-sm">
        <span className="text-ink">{title}</span>
        <span className="tabular-nums text-muted">
          {used ?? "–"} / {limit ?? "no limit"}
        </span>
      </div>
      {limit ? (
        <div className="mt-1 h-2 rounded-full bg-surface-2">
          <div className={`h-2 rounded-full ${pct >= 90 ? "bg-crit" : pct >= 75 ? "bg-warn" : "bg-teal"}`} style={{ width: `${pct}%` }} />
        </div>
      ) : null}
    </div>
  );
}

/** Everything the platform team needs to run one hotel's account (never its guests' data). */
export function HotelDetail({ id }: { id: string }) {
  const { api, can } = useSession();
  const [managing, setManaging] = useState(false);
  const [limitsOpen, setLimitsOpen] = useState(false);
  const detail = useQuery({
    queryKey: ["hotel", id],
    queryFn: () => ok(api.GET("/api/v1/admin/hotels/{hotel_id}", { params: { path: { hotel_id: id } } })),
  });
  if (detail.error) return <ErrorNotice error={detail.error} />;
  if (!detail.data) return <Skeleton className="h-80" />;
  const d = detail.data;
  const h = d.hotel;
  const sub = d.subscription;
  const limits = (sub?.limits ?? {}) as Record<string, number | undefined>;
  const used: Record<LimitKey, number | null> = { rooms: h.counts.rooms, devices: h.counts.devices, staff: h.counts.staff, api_keys: null };

  return (
    <>
      <p className="mb-2 text-sm">
        <Link className="text-blue hover:underline" href="/hotels">
          ← All hotels
        </Link>
      </p>
      <PageHeader
        title={h.name}
        description={`${h.slug} · joined ${formatDate(h.created_at)}${h.last_activity ? ` · last active ${formatDate(h.last_activity)}` : ""}`}
        actions={
          <>
            <Badge tone={h.status === "active" ? "good" : h.status === "pending_approval" ? "warn" : "crit"}>{label(h.status)}</Badge>
            <Button onClick={() => setManaging(true)}>Manage</Button>
          </>
        }
      />
      {h.status_reason ? <p className="mb-4 rounded-lg bg-warn/10 p-3 text-sm text-ink">Reason: {h.status_reason}</p> : null}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="p-5">
          <h2 className="font-display text-base font-semibold">Account</h2>
          <dl className="mt-3 grid grid-cols-2 gap-y-2 text-sm">
            <dt className="text-muted">Registered name</dt>
            <dd>{d.legal_name ?? "–"}</dd>
            <dt className="text-muted">Country</dt>
            <dd>{d.country}</dd>
            <dt className="text-muted">Currency</dt>
            <dd>{d.currency}</dd>
            <dt className="text-muted">Time zone</dt>
            <dd>{d.timezone}</dd>
            <dt className="text-muted">Phone</dt>
            <dd>{d.phone ?? "–"}</dd>
            <dt className="text-muted">Email</dt>
            <dd className="truncate">{d.email ?? "–"}</dd>
          </dl>
          <h3 className="mt-5 text-sm font-semibold">Owners</h3>
          <ul className="mt-2 text-sm">
            {d.owners.map((o) => (
              <li key={o.email}>
                {o.name} ·{" "}
                <a className="text-blue hover:underline" href={`mailto:${o.email}`}>
                  {o.email}
                </a>
              </li>
            ))}
          </ul>
        </Card>
        <Card className="p-5">
          <div className="flex items-start justify-between gap-2">
            <h2 className="font-display text-base font-semibold">Subscription</h2>
            {sub && can("platform.billing.manage") ? (
              <Button size="sm" variant="secondary" onClick={() => setLimitsOpen(true)}>
                Custom limits
              </Button>
            ) : null}
          </div>
          {sub ? (
            <>
              <p className="mt-3 text-sm">
                <span className="font-medium">{sub.plan.name}</span> · {formatMoney(sub.plan.monthly_price)} a month ·{" "}
                <Badge tone={sub.status === "active" ? "good" : sub.status === "past_due" ? "crit" : "neutral"}>{label(sub.status)}</Badge>
              </p>
              <p className="text-xs text-muted">
                Since {formatDate(sub.starts_on)}
                {sub.renews_on ? ` · renews ${formatDate(sub.renews_on)}` : ""}
              </p>
              <div className="mt-4 flex flex-col gap-3">
                {LIMITS.map(([k, t]) => (
                  <Usage key={k} title={`${t}${k in sub.limit_overrides ? " (custom)" : ""}`} used={used[k]} limit={limits[k]} />
                ))}
              </div>
            </>
          ) : (
            <EmptyState title="No subscription" body="Choose a plan under Manage." />
          )}
          <p className="mt-4 text-sm text-muted">
            {h.counts.connected_devices} of {h.counts.devices} devices online · {h.counts.active_stays} guests in house
          </p>
        </Card>
        <Card>
          <CardHeader title="Support access" description="Read-only access granted for tickets." />
          {d.support_grants.length ? (
            <ul className="divide-y divide-line text-sm">
              {d.support_grants.map((g) => (
                <li key={g.id} className="px-5 py-2">
                  <p className="font-medium">
                    {g.ticket_reference} {g.active ? <Badge tone="warn">Active</Badge> : null}
                  </p>
                  <p className="text-xs text-muted">
                    {formatDate(g.starts_at)} {formatTime(g.starts_at)} – {formatTime(g.expires_at)}
                    {g.revoked_at ? " · revoked" : ""}
                    {g.reason ? ` · ${g.reason}` : ""}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="Never granted" />
          )}
        </Card>
      </div>
      <Card className="mt-6">
        <CardHeader title="Platform actions" description="What Diyneco staff did on this account, newest first." />
        {d.platform_actions.length ? (
          <ul className="divide-y divide-line text-sm">
            {d.platform_actions.map((a) => (
              <li key={a.id} className="flex flex-wrap justify-between gap-2 px-5 py-2">
                <span>
                  <span className="font-medium">{label(a.action.replace(".", "_"))}</span> by {a.actor}
                  {a.reason ? <span className="text-muted"> · {a.reason}</span> : null}
                </span>
                <span className="text-muted">
                  {formatDate(a.created_at)} {formatTime(a.created_at)}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title="None yet" />
        )}
      </Card>
      {managing ? <HotelDialog hotel={h} onClose={() => setManaging(false)} /> : null}
      {limitsOpen && sub ? (
        <LimitsDialog
          hotelId={h.id}
          planId={sub.plan.id}
          status={sub.status as "trialing" | "active" | "past_due"}
          startsOn={sub.starts_on}
          renewsOn={sub.renews_on}
          planLimits={sub.plan.limits as Record<string, number | undefined>}
          overrides={sub.limit_overrides as Record<string, number | undefined>}
          onClose={() => setLimitsOpen(false)}
        />
      ) : null}
    </>
  );
}

function LimitsDialog(props: {
  hotelId: string;
  planId: string;
  status: "trialing" | "active" | "past_due";
  startsOn: string;
  renewsOn: string | null;
  planLimits: Record<string, number | undefined>;
  overrides: Record<string, number | undefined>;
  onClose: () => void;
}) {
  const { api } = useSession();
  const [values, setValues] = useState<Record<string, string>>(
    Object.fromEntries(LIMITS.map(([k]) => [k, props.overrides[k] !== undefined ? String(props.overrides[k]) : ""])),
  );
  const valid = Object.values(values).every((v) => v === "" || /^\d{1,6}$/.test(v));
  const save = useAction(
    () =>
      ok(
        api.PUT("/api/v1/admin/hotels/{hotel_id}/subscription", {
          params: { path: { hotel_id: props.hotelId } },
          body: {
            plan_id: props.planId,
            status: props.status,
            starts_on: props.startsOn,
            renews_on: props.renewsOn,
            limit_overrides: Object.fromEntries(Object.entries(values).filter(([, v]) => v !== "").map(([k, v]) => [k, Number(v)])),
          },
        }),
      ),
    { success: "Limits saved.", onDone: props.onClose },
  );
  return (
    <Dialog
      open
      onClose={props.onClose}
      title="Custom limits"
      description="Override the plan's limits for this hotel only. Leave a field empty to use the plan's limit."
      footer={
        <Button disabled={!valid} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Save limits
        </Button>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {LIMITS.map(([k, t]) => (
          <Field key={k} label={t} hint={`Plan: ${props.planLimits[k] ?? "no limit"}`}>
            {(p) => <Input {...p} inputMode="numeric" value={values[k]} onChange={(e) => setValues({ ...values, [k]: e.target.value.trim() })} />}
          </Field>
        ))}
      </div>
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}
