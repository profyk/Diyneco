"use client";

import { type components, formatDate, formatTime, ok } from "@diyneco/api-client";
import { Badge, Button, Card, CardHeader, cn, Dialog, EmptyState, ErrorNotice, Field, Input, PageHeader, Select, Skeleton, StatTile, Table, Td, Textarea, Th } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ColumnChart } from "./charts";
import { useAction } from "./common";
import { useSession } from "./session";
import { ImagePicker, MediaDialog } from "./WebsiteEditor";

// Admin > Website (D83, D88): pages, posts, leads, images, redirects, settings and visitors of
// the public site. Pricing and legal pages come from Plans & Pricing and Legal documents.

const TABS = [
  { key: "pages", label: "Pages & posts", perm: "platform.website.manage" },
  { key: "leads", label: "Leads", perm: "platform.leads.read" },
  { key: "media", label: "Images", perm: "platform.website.manage" },
  { key: "redirects", label: "Redirects", perm: "platform.website.manage" },
  { key: "settings", label: "Settings", perm: "platform.website.manage" },
  { key: "visitors", label: "Visitors", perm: "platform.website.manage" },
] as const;

type Tab = (typeof TABS)[number]["key"];

export function Website() {
  const { can } = useSession();
  const router = useRouter();
  const params = useSearchParams();
  const allowed = TABS.filter((t) => can(t.perm));
  const tab = (allowed.find((t) => t.key === params.get("tab"))?.key ?? allowed[0]?.key ?? "pages") as Tab;
  return (
    <>
      <PageHeader
        title="Website"
        description="www.diyneco.com. Pricing comes from Plans & Pricing and the legal pages from Legal documents."
      />
      <div role="tablist" className="mb-6 flex flex-wrap gap-1 border-b border-line">
        {allowed.map((t) => (
          <button
            key={t.key}
            role="tab"
            type="button"
            aria-selected={tab === t.key}
            onClick={() => router.replace(`/website?tab=${t.key}`)}
            className={cn("-mb-px border-b-2 px-4 py-2 text-sm font-medium", tab === t.key ? "border-blue text-blue" : "border-transparent text-ink hover:text-blue")}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "pages" ? <Entries /> : null}
      {tab === "leads" ? <Leads /> : null}
      {tab === "media" ? <MediaLibrary /> : null}
      {tab === "redirects" ? <Redirects /> : null}
      {tab === "settings" ? <SiteSettings /> : null}
      {tab === "visitors" ? <Visitors /> : null}
    </>
  );
}

// --- Pages and posts ---------------------------------------------------------------------

function Entries() {
  const { api } = useSession();
  const [kind, setKind] = useState<"" | "page" | "post">("");
  const [q, setQ] = useState("");
  const [creating, setCreating] = useState(false);
  const list = useQuery({
    queryKey: ["site-entries", kind, q],
    queryFn: () => ok(api.GET("/api/v1/admin/site/entries", { params: { query: { kind: kind || undefined, q: q || undefined } } })),
  });
  return (
    <Card>
      <div className="flex flex-wrap items-end gap-3 border-b border-line p-4">
        <Field label="Search" className="min-w-56 flex-1">
          {(p) => <Input {...p} type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Title or address" />}
        </Field>
        <Field label="Show">
          {(p) => (
            <Select {...p} value={kind} onChange={(e) => setKind(e.target.value as typeof kind)}>
              <option value="">Pages and posts</option>
              <option value="page">Pages</option>
              <option value="post">Blog posts</option>
            </Select>
          )}
        </Field>
        <Button onClick={() => setCreating(true)}>New page or post</Button>
      </div>
      {list.error ? <ErrorNotice error={list.error} className="m-4" /> : null}
      {!list.data ? (
        <Skeleton className="m-4 h-24" />
      ) : list.data.data.length === 0 ? (
        <EmptyState
          title="Nothing published yet"
          body="The site shows its built-in home, contact and demo pages until you publish a page at the same address (empty address = home)."
        />
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Title</Th>
              <Th>Address</Th>
              <Th>Language</Th>
              <Th>Status</Th>
              <Th>Last changed</Th>
            </tr>
          </thead>
          <tbody>
            {list.data.data.map((e) => (
              <tr key={e.id} className="hover:bg-surface-2">
                <Td>
                  <Link href={`/website/${e.id}`} className="font-medium text-blue hover:underline">
                    {e.title || "Untitled"}
                  </Link>
                  <span className="block text-xs text-muted">{e.kind === "post" ? "Blog post" : "Page"}</span>
                </Td>
                <Td className="font-mono text-xs">{e.kind === "post" ? `/blog/${e.slug}` : `/${e.slug}`}</Td>
                <Td>{e.locale}</Td>
                <Td>
                  <Badge tone={e.status === "published" ? "good" : e.status === "changed" ? "warn" : "neutral"}>
                    {e.status === "changed" ? "Unpublished changes" : e.status === "published" ? "Live" : "Draft"}
                  </Badge>
                </Td>
                <Td className="text-muted">{formatDate(e.updated_at)}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
      {creating ? <NewEntry onClose={() => setCreating(false)} /> : null}
    </Card>
  );
}

function NewEntry({ onClose }: { onClose: () => void }) {
  const { api } = useSession();
  const settings = useQuery({ queryKey: ["site-settings"], queryFn: () => ok(api.GET("/api/v1/admin/site/settings")) });
  const [f, setF] = useState({ kind: "page" as "page" | "post", locale: "", slug: "", title: "" });
  useEffect(() => {
    if (settings.data && !f.locale) setF((x) => ({ ...x, locale: settings.data.default_locale }));
  }, [settings.data, f.locale]);
  const create = useAction(
    () =>
      ok(
        api.POST("/api/v1/admin/site/entries", {
          body: {
            kind: f.kind,
            locale: f.locale,
            slug: f.slug,
            content: { title: f.title, blocks: [], tags: [] } as unknown as components["schemas"]["EntryContent"],
          },
        }),
      ),
    { onDone: (e) => window.location.assign(`/website/${e.id}`) },
  );
  const slugOk = f.kind === "page" ? /^$|^[a-z0-9]+(-[a-z0-9]+)*(\/[a-z0-9]+(-[a-z0-9]+)*)*$/.test(f.slug) : /^[a-z0-9]+(-[a-z0-9]+)*$/.test(f.slug);
  return (
    <Dialog
      open
      onClose={onClose}
      title="New page or post"
      footer={
        <Button disabled={!f.title.trim() || !slugOk || !f.locale} loading={create.isPending} onClick={() => create.mutate(undefined)}>
          Create draft
        </Button>
      }
    >
      <div className="grid gap-4">
        <Field label="Type">
          {(p) => (
            <Select {...p} value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value as "page" | "post" })}>
              <option value="page">Page</option>
              <option value="post">Blog post</option>
            </Select>
          )}
        </Field>
        <Field label="Title">{(p) => <Input {...p} value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} />}</Field>
        <Field
          label="Address"
          hint={f.kind === "post" ? "Lowercase words joined by hyphens: the post will be at /blog/<address>." : "Lowercase words and hyphens, e.g. about or features/kitchen. Empty: the home page."}
        >
          {(p) => (
            <Input
              {...p}
              value={f.slug}
              onChange={(e) =>
                setF({
                  ...f,
                  slug: e.target.value
                    .toLowerCase()
                    .replace(/[^a-z0-9/-]+/g, "-")
                    .replace(/^-+/, ""),
                })
              }
            />
          )}
        </Field>
        <Field label="Language">
          {(p) => (
            <Select {...p} value={f.locale} onChange={(e) => setF({ ...f, locale: e.target.value })}>
              {(settings.data?.locales ?? []).map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </Select>
          )}
        </Field>
      </div>
      {create.error ? <ErrorNotice error={create.error} className="mt-4" /> : null}
    </Dialog>
  );
}

// --- Leads -------------------------------------------------------------------------------

const LEAD_STATUSES = ["new", "contacted", "qualified", "closed", "spam"] as const;

function Leads() {
  const { api } = useSession();
  const [status, setStatus] = useState("");
  const [kind, setKind] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const list = useQuery({
    queryKey: ["site-leads", status, kind],
    queryFn: () =>
      ok(
        api.GET("/api/v1/admin/site/leads", {
          params: {
            query: {
              status: (status || undefined) as (typeof LEAD_STATUSES)[number] | undefined,
              kind: (kind || undefined) as "demo" | "contact" | undefined,
              limit: 100,
            },
          },
        }),
      ),
  });
  const update = useAction(
    (v: { id: string; status?: (typeof LEAD_STATUSES)[number]; notes?: string }) =>
      ok(api.PATCH("/api/v1/admin/site/leads/{lead_id}", { params: { path: { lead_id: v.id } }, body: { status: v.status, notes: v.notes } })),
    { success: "Saved." },
  );
  const erase = useAction((id: string) => ok(api.DELETE("/api/v1/admin/site/leads/{lead_id}", { params: { path: { lead_id: id } } })), {
    success: "Erased. Only the fact that a lead was erased is kept.",
    onDone: () => setOpen(null),
  });
  const rows = list.data?.data ?? [];
  const selected = rows.find((l) => l.id === open);
  const exportCsv = () => {
    const cell = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const head = ["Received", "Kind", "Name", "Email", "Phone", "Company", "Rooms", "Country", "Status", "Message"];
    const lines = rows.map((l) => [l.created_at, l.kind, l.name, l.email, l.phone, l.company, l.rooms, l.country, l.status, l.message].map(cell).join(","));
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([[head.map(cell).join(","), ...lines].join("\n")], { type: "text/csv" }));
    a.download = `diyneco-leads-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  };
  return (
    <Card>
      <div className="flex flex-wrap items-end gap-3 border-b border-line p-4">
        <Field label="Status">
          {(p) => (
            <Select {...p} value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Any status</option>
              {LEAD_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Form">
          {(p) => (
            <Select {...p} value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="">Demo and contact</option>
              <option value="demo">Demo requests</option>
              <option value="contact">Messages</option>
            </Select>
          )}
        </Field>
        <Button variant="secondary" className="ml-auto" disabled={!rows.length} onClick={exportCsv}>
          Download CSV ({rows.length})
        </Button>
      </div>
      {list.error ? <ErrorNotice error={list.error} className="m-4" /> : null}
      {!list.data ? (
        <Skeleton className="m-4 h-24" />
      ) : rows.length === 0 ? (
        <EmptyState title="No leads" body="Demo and contact requests from the website appear here and are emailed to the lead address in Settings." />
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Received</Th>
              <Th>From</Th>
              <Th>Property</Th>
              <Th>Form</Th>
              <Th>Status</Th>
            </tr>
          </thead>
          <tbody>
            {rows.map((l) => (
              <tr key={l.id} className="cursor-pointer hover:bg-surface-2" onClick={() => setOpen(l.id)}>
                <Td className="text-muted">
                  {formatDate(l.created_at)} {formatTime(l.created_at)}
                </Td>
                <Td>
                  <span className="font-medium">{l.name}</span>
                  <span className="block text-xs text-muted">{l.email}</span>
                </Td>
                <Td>
                  {l.company ?? "–"}
                  <span className="block text-xs text-muted">{[l.rooms ? `${l.rooms} rooms` : null, l.country].filter(Boolean).join(" · ")}</span>
                </Td>
                <Td>{l.kind === "demo" ? "Demo" : "Message"}</Td>
                <Td>
                  <Badge tone={l.status === "new" ? "info" : l.status === "qualified" ? "good" : l.status === "spam" ? "crit" : "neutral"}>{l.status}</Badge>
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
      {selected ? (
        <LeadDialog
          lead={selected}
          onClose={() => setOpen(null)}
          onSave={(v) => update.mutate({ id: selected.id, ...v })}
          onErase={() => erase.mutate(selected.id)}
          busy={update.isPending || erase.isPending}
          error={update.error ?? erase.error}
        />
      ) : null}
    </Card>
  );
}

function LeadDialog({
  lead,
  onClose,
  onSave,
  onErase,
  busy,
  error,
}: {
  lead: components["schemas"]["LeadOut"];
  onClose: () => void;
  onSave: (v: { status: (typeof LEAD_STATUSES)[number]; notes: string }) => void;
  onErase: () => void;
  busy: boolean;
  error: unknown;
}) {
  const [status, setStatus] = useState(lead.status as (typeof LEAD_STATUSES)[number]);
  const [notes, setNotes] = useState(lead.notes ?? "");
  const [erasing, setErasing] = useState(false);
  return (
    <Dialog
      open
      onClose={onClose}
      title={`${lead.kind === "demo" ? "Demo request" : "Message"} from ${lead.name}`}
      description={`${formatDate(lead.created_at)} ${formatTime(lead.created_at)}${lead.source_path ? ` · from ${lead.source_path}` : ""}`}
      footer={
        <>
          {erasing ? (
            <Button variant="danger" loading={busy} onClick={onErase}>
              Erase for good
            </Button>
          ) : (
            <Button variant="ghost" onClick={() => setErasing(true)}>
              Erase on request
            </Button>
          )}
          <Button loading={busy} onClick={() => onSave({ status, notes })}>
            Save
          </Button>
        </>
      }
    >
      <dl className="grid grid-cols-[8rem_1fr] gap-y-1.5 text-sm">
        <dt className="text-muted">Email</dt>
        <dd>
          <a className="text-blue hover:underline" href={`mailto:${lead.email}`}>
            {lead.email}
          </a>
        </dd>
        <dt className="text-muted">Phone</dt>
        <dd>{lead.phone ?? "–"}</dd>
        <dt className="text-muted">Hotel or company</dt>
        <dd>{lead.company ?? "–"}</dd>
        <dt className="text-muted">Rooms · country</dt>
        <dd>{[lead.rooms, lead.country].filter(Boolean).join(" · ") || "–"}</dd>
        <dt className="text-muted">Consent</dt>
        <dd className="text-xs text-muted">{lead.consent_text}</dd>
      </dl>
      {lead.message ? <p className="mt-4 whitespace-pre-wrap rounded-lg bg-surface-2 p-3 text-sm">{lead.message}</p> : null}
      <div className="mt-4 grid gap-4">
        <Field label="Status">
          {(p) => (
            <Select {...p} value={status} onChange={(e) => setStatus(e.target.value as (typeof LEAD_STATUSES)[number])}>
              {LEAD_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Notes">{(p) => <Textarea {...p} rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />}</Field>
      </div>
      {error ? <ErrorNotice error={error} className="mt-4" /> : null}
    </Dialog>
  );
}

// --- Images --------------------------------------------------------------------------------

function MediaLibrary() {
  const { api } = useSession();
  const media = useQuery({ queryKey: ["site-media"], queryFn: () => ok(api.GET("/api/v1/admin/site/media")) });
  const [uploading, setUploading] = useState(false);
  const alt = useAction(
    (v: { id: string; alt: string }) => ok(api.PATCH("/api/v1/admin/site/media/{media_id}", { params: { path: { media_id: v.id } }, body: { alt: v.alt } })),
    { success: "Description saved." },
  );
  const remove = useAction((id: string) => ok(api.DELETE("/api/v1/admin/site/media/{media_id}", { params: { path: { media_id: id } } })), {
    success: "Image deleted.",
  });
  return (
    <Card>
      <CardHeader
        title="Images"
        description="Describe each image for screen readers and search engines. An image in use can't be deleted."
        actions={<Button onClick={() => setUploading(true)}>Upload</Button>}
      />
      {remove.error ? <ErrorNotice error={remove.error} className="m-4" /> : null}
      {!media.data ? (
        <Skeleton className="m-4 h-40" />
      ) : media.data.data.length === 0 ? (
        <EmptyState title="No images yet" />
      ) : (
        <div className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4">
          {media.data.data.map((m) => (
            <div key={m.id} className="overflow-hidden rounded-lg border border-line">
              <img src={m.url} alt={m.alt} className="aspect-[4/3] w-full object-cover" />
              <div className="flex flex-col gap-2 p-3">
                <p className="truncate text-xs text-muted">
                  {m.filename} · {m.width}×{m.height}
                </p>
                <AltField initial={m.alt} onSave={(v) => alt.mutate({ id: m.id, alt: v })} />
                <Button size="sm" variant="ghost" onClick={() => remove.mutate(m.id)}>
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
      {uploading ? <MediaDialog onClose={() => setUploading(false)} /> : null}
    </Card>
  );
}

function AltField({ initial, onSave }: { initial: string; onSave: (v: string) => void }) {
  const [v, setV] = useState(initial);
  return (
    <div className="flex gap-2">
      <Input aria-label="Image description" placeholder="Describe the image" value={v} onChange={(e) => setV(e.target.value)} />
      <Button size="sm" variant="secondary" disabled={v === initial} onClick={() => onSave(v)}>
        Save
      </Button>
    </div>
  );
}

// --- Redirects -----------------------------------------------------------------------------

function Redirects() {
  const { api } = useSession();
  const list = useQuery({ queryKey: ["site-redirects"], queryFn: () => ok(api.GET("/api/v1/admin/site/redirects")) });
  const [f, setF] = useState({ from_path: "", to_path: "", permanent: true });
  const add = useAction(() => ok(api.POST("/api/v1/admin/site/redirects", { body: f })), {
    success: "Redirect added.",
    onDone: () => setF({ from_path: "", to_path: "", permanent: true }),
  });
  const remove = useAction((id: string) => ok(api.DELETE("/api/v1/admin/site/redirects/{redirect_id}", { params: { path: { redirect_id: id } } })), {
    success: "Redirect removed.",
  });
  return (
    <Card>
      <CardHeader title="Redirects" description="Old addresses sent to new ones. Changing a published page's address adds one automatically." />
      <div className="flex flex-wrap items-end gap-3 border-b border-line p-4">
        <Field label="From">{(p) => <Input {...p} placeholder="/old-page" value={f.from_path} onChange={(e) => setF({ ...f, from_path: e.target.value })} />}</Field>
        <Field label="To">{(p) => <Input {...p} placeholder="/new-page or https://…" value={f.to_path} onChange={(e) => setF({ ...f, to_path: e.target.value })} />}</Field>
        <Field label="Kind">
          {(p) => (
            <Select {...p} value={f.permanent ? "301" : "302"} onChange={(e) => setF({ ...f, permanent: e.target.value === "301" })}>
              <option value="301">Permanent (301)</option>
              <option value="302">Temporary (302)</option>
            </Select>
          )}
        </Field>
        <Button disabled={!f.from_path.startsWith("/") || !f.to_path} loading={add.isPending} onClick={() => add.mutate(undefined)}>
          Add
        </Button>
      </div>
      {add.error ? <ErrorNotice error={add.error} className="m-4" /> : null}
      {!list.data ? (
        <Skeleton className="m-4 h-16" />
      ) : list.data.data.length === 0 ? (
        <EmptyState title="No redirects" />
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>From</Th>
              <Th>To</Th>
              <Th>Kind</Th>
              <Th />
            </tr>
          </thead>
          <tbody>
            {list.data.data.map((r) => (
              <tr key={r.id}>
                <Td className="font-mono text-xs">{r.from_path}</Td>
                <Td className="font-mono text-xs">{r.to_path}</Td>
                <Td>{r.permanent ? "301" : "302"}</Td>
                <Td className="text-right">
                  <Button size="sm" variant="ghost" onClick={() => remove.mutate(r.id)}>
                    Remove
                  </Button>
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </Card>
  );
}

// --- Settings ------------------------------------------------------------------------------

type Link2 = { label: string; href: string };
type SettingsForm = {
  site_name: string;
  base_url: string;
  default_locale: string;
  locales: string;
  navigation: Link2[];
  footer_note: string;
  footer_columns: { heading: string; links: Link2[] }[];
  contact: { email: string; phone: string; address: string };
  social: { network: string; url: string }[];
  seo: { title_template: string; default_title: string; default_description: string; default_image_id?: string; organization_logo_id?: string };
  verification: { google: string; bing: string };
  analytics: string;
  lead_email: string;
};

function SiteSettings() {
  const { api } = useSession();
  const q = useQuery({ queryKey: ["site-settings"], queryFn: () => ok(api.GET("/api/v1/admin/site/settings")) });
  const [f, setF] = useState<SettingsForm | null>(null);
  useEffect(() => {
    if (!q.data) return;
    const s = q.data as unknown as {
      site_name: string;
      base_url: string;
      default_locale: string;
      locales: string[];
      navigation: Link2[];
      footer: { note?: string; columns?: { heading: string; links: Link2[] }[] };
      contact: { email?: string; phone?: string; address?: string };
      social: { network: string; url: string }[];
      seo: Record<string, string | undefined>;
      verification: { google?: string; bing?: string };
      analytics: { provider?: string };
      lead_email: string;
    };
    setF({
      site_name: s.site_name,
      base_url: s.base_url,
      default_locale: s.default_locale,
      locales: s.locales.join(", "),
      navigation: s.navigation,
      footer_note: s.footer.note ?? "",
      footer_columns: s.footer.columns ?? [],
      contact: { email: s.contact.email ?? "", phone: s.contact.phone ?? "", address: s.contact.address ?? "" },
      social: s.social,
      seo: {
        title_template: s.seo.title_template ?? "%s | Diyneco",
        default_title: s.seo.default_title ?? "",
        default_description: s.seo.default_description ?? "",
        default_image_id: s.seo.default_image_id,
        organization_logo_id: s.seo.organization_logo_id,
      },
      verification: { google: s.verification.google ?? "", bing: s.verification.bing ?? "" },
      analytics: s.analytics.provider ?? "builtin",
      lead_email: s.lead_email,
    });
  }, [q.data]);
  const save = useAction(
    () => {
      if (!f) throw new Error("not loaded");
      const opt = (v: string) => v.trim() || null;
      return ok(
        api.PUT("/api/v1/admin/site/settings", {
          body: {
            site_name: f.site_name,
            base_url: f.base_url.replace(/\/$/, ""),
            default_locale: f.default_locale,
            locales: f.locales.split(",").map((x) => x.trim()).filter(Boolean),
            navigation: f.navigation.filter((l) => l.label && l.href),
            footer: { note: opt(f.footer_note), columns: f.footer_columns.filter((c) => c.heading) },
            contact: { email: opt(f.contact.email), phone: opt(f.contact.phone), address: opt(f.contact.address) },
            social: f.social.filter((x) => x.url) as components["schemas"]["SettingsIn"]["social"],
            seo: {
              title_template: f.seo.title_template,
              default_title: opt(f.seo.default_title),
              default_description: opt(f.seo.default_description),
              default_image_id: f.seo.default_image_id ?? null,
              organization_logo_id: f.seo.organization_logo_id ?? null,
            },
            verification: { google: opt(f.verification.google), bing: opt(f.verification.bing) },
            analytics: { provider: f.analytics as "builtin" | "none" | "plausible" },
            lead_email: f.lead_email,
          } as unknown as components["schemas"]["SettingsIn"],
        }),
      );
    },
    { success: "Settings saved. The site updates within a few minutes." },
  );
  if (q.error) return <ErrorNotice error={q.error} />;
  if (!f) return <Skeleton className="h-96" />;
  const links = (list: Link2[], onChange: (l: Link2[]) => void) => (
    <div className="flex flex-col gap-2">
      {list.map((l, i) => (
        <div key={i} className="flex gap-2">
          <Input aria-label="Label" placeholder="Label" value={l.label} onChange={(e) => onChange(list.map((x, n) => (n === i ? { ...x, label: e.target.value } : x)))} />
          <Input aria-label="Link" placeholder="/pricing" value={l.href} onChange={(e) => onChange(list.map((x, n) => (n === i ? { ...x, href: e.target.value } : x)))} />
          <Button size="sm" variant="ghost" onClick={() => onChange(list.filter((_, n) => n !== i))}>
            Remove
          </Button>
        </div>
      ))}
      <Button size="sm" variant="secondary" className="self-start" onClick={() => onChange([...list, { label: "", href: "" }])}>
        + Add link
      </Button>
    </div>
  );
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="flex flex-col gap-4 p-5">
        <h2 className="font-display text-base font-semibold">Site</h2>
        <Field label="Site name">{(p) => <Input {...p} value={f.site_name} onChange={(e) => setF({ ...f, site_name: e.target.value })} />}</Field>
        <Field label="Address" hint="e.g. https://www.diyneco.com">{(p) => <Input {...p} value={f.base_url} onChange={(e) => setF({ ...f, base_url: e.target.value })} />}</Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Languages" hint="e.g. en, af, fr">{(p) => <Input {...p} value={f.locales} onChange={(e) => setF({ ...f, locales: e.target.value })} />}</Field>
          <Field label="Default language">{(p) => <Input {...p} value={f.default_locale} onChange={(e) => setF({ ...f, default_locale: e.target.value })} />}</Field>
        </div>
        <Field label="Leads are emailed to">{(p) => <Input {...p} type="email" value={f.lead_email} onChange={(e) => setF({ ...f, lead_email: e.target.value })} />}</Field>
        <Field label="Visitor counting">
          {(p) => (
            <Select {...p} value={f.analytics} onChange={(e) => setF({ ...f, analytics: e.target.value })}>
              <option value="builtin">Diyneco&apos;s own (cookieless, nothing personal stored)</option>
              <option value="none">Off</option>
            </Select>
          )}
        </Field>
      </Card>
      <Card className="flex flex-col gap-4 p-5">
        <h2 className="font-display text-base font-semibold">Search engines</h2>
        <Field label="Title template" hint="%s is replaced by the page title.">
          {(p) => <Input {...p} value={f.seo.title_template} onChange={(e) => setF({ ...f, seo: { ...f.seo, title_template: e.target.value } })} />}
        </Field>
        <Field label="Home page title">{(p) => <Input {...p} maxLength={70} value={f.seo.default_title} onChange={(e) => setF({ ...f, seo: { ...f.seo, default_title: e.target.value } })} />}</Field>
        <Field label="Default description">
          {(p) => <Textarea {...p} rows={2} maxLength={170} value={f.seo.default_description} onChange={(e) => setF({ ...f, seo: { ...f.seo, default_description: e.target.value } })} />}
        </Field>
        <Field label="Default share image">{() => <ImagePicker value={f.seo.default_image_id} onChange={(v) => setF({ ...f, seo: { ...f.seo, default_image_id: v } })} />}</Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Google verification code">{(p) => <Input {...p} value={f.verification.google} onChange={(e) => setF({ ...f, verification: { ...f.verification, google: e.target.value } })} />}</Field>
          <Field label="Bing verification code">{(p) => <Input {...p} value={f.verification.bing} onChange={(e) => setF({ ...f, verification: { ...f.verification, bing: e.target.value } })} />}</Field>
        </div>
      </Card>
      <Card className="flex flex-col gap-4 p-5">
        <h2 className="font-display text-base font-semibold">Menu</h2>
        {links(f.navigation, (l) => setF({ ...f, navigation: l }))}
        <p className="text-xs text-muted">Empty: Product, Pricing, Blog and Contact.</p>
      </Card>
      <Card className="flex flex-col gap-4 p-5">
        <h2 className="font-display text-base font-semibold">Contact and social</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Email">{(p) => <Input {...p} value={f.contact.email} onChange={(e) => setF({ ...f, contact: { ...f.contact, email: e.target.value } })} />}</Field>
          <Field label="Phone">{(p) => <Input {...p} value={f.contact.phone} onChange={(e) => setF({ ...f, contact: { ...f.contact, phone: e.target.value } })} />}</Field>
        </div>
        <Field label="Address">{(p) => <Input {...p} value={f.contact.address} onChange={(e) => setF({ ...f, contact: { ...f.contact, address: e.target.value } })} />}</Field>
        {f.social.map((x, i) => (
          <div key={i} className="flex gap-2">
            <Select aria-label="Network" className="w-40" value={x.network} onChange={(e) => setF({ ...f, social: f.social.map((y, n) => (n === i ? { ...y, network: e.target.value } : y)) })}>
              {["linkedin", "facebook", "instagram", "x", "youtube", "tiktok"].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </Select>
            <Input aria-label="Profile link" placeholder="https://…" value={x.url} onChange={(e) => setF({ ...f, social: f.social.map((y, n) => (n === i ? { ...y, url: e.target.value } : y)) })} />
            <Button size="sm" variant="ghost" onClick={() => setF({ ...f, social: f.social.filter((_, n) => n !== i) })}>
              Remove
            </Button>
          </div>
        ))}
        <Button size="sm" variant="secondary" className="self-start" onClick={() => setF({ ...f, social: [...f.social, { network: "linkedin", url: "" }] })}>
          + Add social link
        </Button>
      </Card>
      <Card className="flex flex-col gap-4 p-5 lg:col-span-2">
        <h2 className="font-display text-base font-semibold">Footer</h2>
        <Field label="Short note">{(p) => <Input {...p} value={f.footer_note} onChange={(e) => setF({ ...f, footer_note: e.target.value })} />}</Field>
        <div className="grid gap-4 md:grid-cols-2">
          {f.footer_columns.map((c, i) => (
            <div key={i} className="rounded-lg border border-line p-3">
              <div className="mb-2 flex gap-2">
                <Input aria-label="Column heading" placeholder="Heading" value={c.heading} onChange={(e) => setF({ ...f, footer_columns: f.footer_columns.map((y, n) => (n === i ? { ...y, heading: e.target.value } : y)) })} />
                <Button size="sm" variant="ghost" onClick={() => setF({ ...f, footer_columns: f.footer_columns.filter((_, n) => n !== i) })}>
                  Remove
                </Button>
              </div>
              {links(c.links, (l) => setF({ ...f, footer_columns: f.footer_columns.map((y, n) => (n === i ? { ...y, links: l } : y)) }))}
            </div>
          ))}
        </div>
        <Button size="sm" variant="secondary" className="self-start" onClick={() => setF({ ...f, footer_columns: [...f.footer_columns, { heading: "", links: [] }] })}>
          + Add column
        </Button>
        <p className="text-xs text-muted">The Legal column (terms, privacy, all documents) is always added from Legal documents.</p>
      </Card>
      <div className="lg:col-span-2">
        {save.error ? <ErrorNotice error={save.error} className="mb-3" /> : null}
        <Button size="lg" loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Save settings
        </Button>
      </div>
    </div>
  );
}

// --- Visitors ------------------------------------------------------------------------------

function Visitors() {
  const { api } = useSession();
  const [days, setDays] = useState(30);
  const until = useMemo(() => new Date(), []);
  const since = new Date(until.getTime() - (days - 1) * 86_400_000).toISOString().slice(0, 10);
  const q = useQuery({
    queryKey: ["site-analytics", days],
    queryFn: () => ok(api.GET("/api/v1/admin/site/analytics", { params: { query: { since, until: until.toISOString().slice(0, 10) } } })),
  });
  if (q.error) return <ErrorNotice error={q.error} />;
  if (!q.data) return <Skeleton className="h-80" />;
  const d = q.data;
  const top = (title: string, rows: { key: string; views: number; visitors: number }[]) => (
    <Card>
      <CardHeader title={title} />
      <Table>
        <thead>
          <tr>
            <Th>{title === "Pages" ? "Address" : title === "Referrers" ? "Site" : "Language"}</Th>
            <Th className="text-right">Views</Th>
            <Th className="text-right">Visitors</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key}>
              <Td className="max-w-[16rem] truncate font-mono text-xs">{r.key}</Td>
              <Td className="text-right tabular-nums">{r.views}</Td>
              <Td className="text-right tabular-nums">{r.visitors}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Card>
  );
  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-end">
        <Select aria-label="Period" className="w-40" value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={7}>7 days</option>
          <option value={30}>30 days</option>
          <option value={90}>90 days</option>
        </Select>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <StatTile label="Page views" value={d.views} />
        <StatTile label="Visitors" value={d.visitors} hint="Counted once a day; no cookies" />
        <StatTile label="Leads" value={d.leads} hint={d.visitors ? `${((d.leads / d.visitors) * 100).toFixed(1)}% of visitors` : undefined} tone="good" />
      </div>
      <Card>
        <CardHeader title="Views per day" />
        <div className="p-5">
          <ColumnChart
            title="Website views per day"
            points={d.days.map((x) => {
              const label = new Date(`${x.day}T12:00:00Z`).toLocaleDateString(undefined, { day: "numeric", month: "short" });
              return { label, value: x.views, tooltip: `${label}: ${x.views} views, ${x.visitors} visitors` };
            })}
          />
        </div>
      </Card>
      <div className="grid gap-6 lg:grid-cols-3">
        {top("Pages", d.pages)}
        {top("Referrers", d.referrers)}
        {top("Languages", d.locales)}
      </div>
    </div>
  );
}
