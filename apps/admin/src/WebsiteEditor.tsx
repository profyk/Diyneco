"use client";

import { type components, formatDate, formatTime, ok } from "@diyneco/api-client";
import { Badge, Button, Card, CardHeader, Dialog, ErrorNotice, Field, Input, PageHeader, Select, Skeleton, Textarea } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useState } from "react";

import { useAction } from "./common";
import { useSession } from "./session";

// Editing one page or blog post of the public website (D83, D88). Changes go to the draft;
// Publish makes the draft live and keeps a version; Preview opens the draft for 15 minutes.

type Json = Record<string, unknown>;
type FieldKind =
  | "text"
  | "textarea"
  | "markdown"
  | "cta"
  | "image"
  | "number"
  | "checkbox"
  | { select: string[]; labels?: Record<string, string> }
  | { list: Spec[]; bulkImage?: string };
type Spec = { key: string; label: string; kind: FieldKind; required?: boolean; hint?: string };

const T = (key: string, label: string, required = false, hint?: string): Spec => ({ key, label, kind: "text", required, hint });
const TA = (key: string, label: string, required = false): Spec => ({ key, label, kind: "textarea", required });

// Areas of a hotel a gallery photo shows (D91); the website offers them as filter tabs.
export const GALLERY_AREAS: Record<string, string> = {
  rooms: "Rooms",
  reception: "Reception",
  kitchen: "Kitchen",
  restaurant: "Restaurant",
  outside: "Outside",
  pool: "Pool",
  spa: "Spa",
  conference: "Conference",
  events: "Events",
  other: "Other",
};

export const BLOCKS: Record<string, { label: string; fields: Spec[] }> = {
  hero: {
    label: "Hero",
    fields: [T("eyebrow", "Small line above"), T("heading", "Heading", true), TA("subheading", "Subheading"), { key: "primary", label: "Main button", kind: "cta" }, { key: "secondary", label: "Second button", kind: "cta" }, { key: "image_id", label: "Image", kind: "image" }],
  },
  features: {
    label: "Features",
    fields: [
      T("heading", "Heading"),
      TA("intro", "Intro"),
      { key: "items", label: "Features", kind: { list: [T("title", "Title", true), TA("body", "Text", true), { key: "image_id", label: "Image", kind: "image" }] } },
    ],
  },
  gallery: {
    label: "Photo gallery",
    fields: [
      T("heading", "Heading"),
      TA("intro", "Intro"),
      { key: "show_filters", label: "Show area tabs (Rooms, Kitchen, …)", kind: "checkbox" },
      {
        key: "items",
        label: "Photos",
        kind: {
          bulkImage: "image_id",
          list: [
            { key: "image_id", label: "Photo", kind: "image", required: true },
            { key: "category", label: "Area", kind: { select: Object.keys(GALLERY_AREAS), labels: GALLERY_AREAS } },
            T("caption", "Caption", false, "e.g. Orders on the kitchen display"),
          ],
        },
      },
    ],
  },
  steps: { label: "Steps", fields: [T("heading", "Heading"), { key: "items", label: "Steps", kind: { list: [T("title", "Title", true), TA("body", "Text", true)] } }] },
  split: {
    label: "Text and image",
    fields: [T("heading", "Heading", true), { key: "body", label: "Text (Markdown)", kind: "markdown", required: true }, { key: "image_id", label: "Image", kind: "image" }, { key: "image_side", label: "Image side", kind: { select: ["right", "left"] } }, { key: "cta", label: "Button", kind: "cta" }],
  },
  stats: { label: "Figures", fields: [T("heading", "Heading"), { key: "items", label: "Figures", kind: { list: [T("value", "Figure", true, "Only real, verifiable figures"), T("label", "Label", true)] } }] },
  testimonials: {
    label: "Testimonials",
    fields: [T("heading", "Heading"), { key: "items", label: "Quotes", kind: { list: [TA("quote", "Quote", true), T("name", "Name", true), T("role", "Role"), T("hotel", "Hotel")] } }],
  },
  faq: { label: "Questions", fields: [T("heading", "Heading"), { key: "items", label: "Questions", kind: { list: [T("question", "Question", true), TA("answer", "Answer", true)] } }] },
  cta: { label: "Call to action", fields: [T("heading", "Heading", true), TA("body", "Text"), { key: "primary", label: "Main button", kind: "cta", required: true }, { key: "secondary", label: "Second button", kind: "cta" }] },
  logos: { label: "Logos", fields: [T("heading", "Heading"), { key: "items", label: "Logos", kind: { list: [{ key: "image_id", label: "Logo", kind: "image", required: true }, T("name", "Name", true), T("href", "Link")] } }] },
  pricing: { label: "Pricing (live plans)", fields: [T("heading", "Heading"), TA("intro", "Intro")] },
  rich_text: { label: "Text", fields: [{ key: "body", label: "Text (Markdown)", kind: "markdown", required: true }] },
  lead_form: { label: "Contact or demo form", fields: [{ key: "kind", label: "Form", kind: { select: ["demo", "contact"] }, required: true }, T("heading", "Heading"), TA("intro", "Intro")] },
  post_list: { label: "Latest posts", fields: [T("heading", "Heading"), { key: "limit", label: "How many", kind: "number" }] },
};

/** A new list item or block with each select at its first option and each checkbox on. */
function defaults(fields: Spec[]): Json {
  const b: Json = {};
  for (const f of fields) {
    if (typeof f.kind === "object" && "list" in f.kind) b[f.key] = f.kind.bulkImage ? [] : [defaults(f.kind.list)];
    if (typeof f.kind === "object" && "select" in f.kind) b[f.key] = f.kind.select[0];
    if (f.kind === "checkbox") b[f.key] = true;
  }
  return b;
}

function blank(type: string): Json {
  return { type, ...defaults(BLOCKS[type]?.fields ?? []) };
}

/** Drops empty optional values so the API's strict schema accepts the content. */
function clean(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(clean);
  if (value && typeof value === "object") {
    const out: Json = {};
    for (const [k, v] of Object.entries(value as Json)) {
      const c = clean(v);
      if (c === "" || c === undefined || c === null) continue;
      if (c && typeof c === "object" && !Array.isArray(c) && "label" in (c as Json) && !(c as Json).label && !(c as Json).href) continue;
      out[k] = c;
    }
    return out;
  }
  return value;
}

function useMedia() {
  const { api } = useSession();
  return useQuery({ queryKey: ["site-media"], queryFn: () => ok(api.GET("/api/v1/admin/site/media")) });
}

export function ImagePicker({ value, onChange }: { value: string | undefined; onChange: (id: string | undefined) => void }) {
  const media = useMedia();
  const [open, setOpen] = useState(false);
  const current = media.data?.data.find((m) => m.id === value);
  return (
    <div className="flex items-center gap-3">
      {current ? <img src={current.url} alt={current.alt} className="h-14 w-20 rounded-md object-cover" /> : <span className="text-sm text-muted">No image</span>}
      <Button size="sm" variant="secondary" onClick={() => setOpen(true)}>
        {current ? "Change" : "Choose image"}
      </Button>
      {current ? (
        <Button size="sm" variant="ghost" onClick={() => onChange(undefined)}>
          Remove
        </Button>
      ) : null}
      {open ? (
        <MediaDialog
          onClose={() => setOpen(false)}
          onPick={(id) => {
            onChange(id);
            setOpen(false);
          }}
        />
      ) : null}
    </div>
  );
}

function readBase64(file: File): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(",", 2)[1] ?? "");
    r.onerror = () => reject(new Error(`${file.name} could not be read.`));
    r.readAsDataURL(file);
  });
}

/**
 * The image library. Several files upload at once (one after another, so a slow connection
 * is not flooded). With `onPickMany`, images are ticked and added together; new uploads come
 * ticked already.
 */
export function MediaDialog({ onClose, onPick, onPickMany }: { onClose: () => void; onPick?: (id: string) => void; onPickMany?: (ids: string[]) => void }) {
  const { api } = useSession();
  const media = useMedia();
  const [picked, setPicked] = useState<string[]>([]);
  const [progress, setProgress] = useState("");
  const upload = useAction(
    async (files: File[]) => {
      const ids: string[] = [];
      for (const [n, file] of files.entries()) {
        setProgress(`Uploading ${n + 1} of ${files.length}…`);
        // A descriptive file name ("kitchen-display.jpg") is a fair first alt text; a camera's is not.
        const name = file.name.replace(/\.[a-z0-9]+$/i, "").replace(/[-_]+/g, " ").trim();
        const alt = /^(img|dsc|pxl|photo|image|whatsapp)?[\s\d]*$/i.test(name) || /^(img|dsc|pxl)\s/i.test(name) ? "" : name.slice(0, 300);
        const m = await ok(api.POST("/api/v1/admin/site/media", { body: { filename: file.name, alt, data_base64: await readBase64(file) } }));
        ids.push(m.id);
      }
      return ids;
    },
    {
      success: (ids) => (ids.length === 1 ? "Image uploaded." : `${ids.length} images uploaded.`),
      onDone: (ids) => {
        setProgress("");
        if (onPickMany) setPicked((p) => [...p, ...ids.filter((id) => !p.includes(id))]);
      },
    },
  );
  const toggle = (id: string) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title="Images"
      description="JPEG, PNG or WebP up to 6 MB each; choose several at once if you like. Images are resized and stripped of camera data."
    >
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-[10px] border border-line px-4 py-2 text-sm hover:bg-surface-2">
          Upload images
          <input
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp"
            className="sr-only"
            disabled={upload.isPending}
            onChange={(e) => {
              const files = Array.from(e.target.files ?? []);
              e.target.value = "";
              if (files.length) upload.mutate(files);
            }}
          />
        </label>
        {onPickMany ? (
          <Button disabled={!picked.length} onClick={() => onPickMany(picked)}>
            {picked.length ? `Add ${picked.length} photo${picked.length === 1 ? "" : "s"}` : "Tick photos to add"}
          </Button>
        ) : null}
      </div>
      {upload.isPending ? (
        <p className="mb-2 text-sm text-muted" aria-live="polite">
          {progress || "Uploading…"}
        </p>
      ) : null}
      {upload.error ? <ErrorNotice error={upload.error} className="mb-2" /> : null}
      {!media.data ? (
        <Skeleton className="h-40" />
      ) : (
        <div className="grid max-h-96 grid-cols-2 gap-3 overflow-auto sm:grid-cols-4">
          {media.data.data.map((m) => {
            const on = picked.includes(m.id);
            return (
              <button
                key={m.id}
                type="button"
                disabled={!onPick && !onPickMany}
                aria-pressed={onPickMany ? on : undefined}
                onClick={() => (onPickMany ? toggle(m.id) : onPick?.(m.id))}
                className={`relative overflow-hidden rounded-lg border text-left hover:border-blue ${on ? "border-blue ring-2 ring-blue" : "border-line"}`}
              >
                <img src={m.url} alt={m.alt} className="aspect-[4/3] w-full object-cover" />
                {on ? <span className="absolute right-1.5 top-1.5 rounded-full bg-blue px-2 py-0.5 text-xs font-semibold text-white">{picked.indexOf(m.id) + 1}</span> : null}
                <span className="block truncate px-2 py-1 text-xs text-muted">{m.filename}</span>
              </button>
            );
          })}
        </div>
      )}
    </Dialog>
  );
}

function FieldEditor({ spec, value, onChange }: { spec: Spec; value: unknown; onChange: (v: unknown) => void }) {
  const label = `${spec.label}${spec.required ? "" : " (optional)"}`;
  const k = spec.kind;
  const [bulk, setBulk] = useState(false);
  if (k === "checkbox") {
    return (
      <label className="flex items-center gap-2 self-end pb-2 text-sm text-ink">
        <input type="checkbox" checked={value !== false} onChange={(e) => onChange(e.target.checked)} />
        {spec.label}
      </label>
    );
  }
  if (k === "image") return <Field label={label}>{() => <ImagePicker value={value as string | undefined} onChange={onChange} />}</Field>;
  if (k === "cta") {
    const v = (value as { label?: string; href?: string } | undefined) ?? {};
    return (
      <fieldset className="grid gap-3 rounded-lg border border-line p-3 sm:grid-cols-2">
        <legend className="px-1 text-sm font-medium text-ink">{label}</legend>
        <Field label="Label">{(p) => <Input {...p} value={v.label ?? ""} onChange={(e) => onChange({ ...v, label: e.target.value })} />}</Field>
        <Field label="Link" hint="/signup, /demo, /pricing or https://…">
          {(p) => <Input {...p} value={v.href ?? ""} onChange={(e) => onChange({ ...v, href: e.target.value })} />}
        </Field>
      </fieldset>
    );
  }
  if (typeof k === "object" && "select" in k) {
    return (
      <Field label={label}>
        {(p) => (
          <Select {...p} value={String(value ?? k.select[0])} onChange={(e) => onChange(e.target.value)}>
            {k.select.map((o) => (
              <option key={o} value={o}>
                {k.labels?.[o] ?? o}
              </option>
            ))}
          </Select>
        )}
      </Field>
    );
  }
  if (typeof k === "object" && "list" in k) {
    const items = (value as Json[] | undefined) ?? [];
    const set = (i: number, item: Json) => onChange(items.map((x, n) => (n === i ? item : x)));
    return (
      <fieldset className="flex flex-col gap-3">
        <legend className="mb-2 text-sm font-medium text-ink">{spec.label}</legend>
        {items.map((item, i) => (
          <div key={i} className="rounded-lg border border-line p-3">
            <div className="grid gap-3 sm:grid-cols-2">
              {k.list.map((s) => (
                <FieldEditor key={s.key} spec={s} value={item[s.key]} onChange={(v) => set(i, { ...item, [s.key]: v })} />
              ))}
            </div>
            <div className="mt-2 flex gap-2">
              <Button size="sm" variant="ghost" disabled={i === 0} onClick={() => onChange(items.map((x, n) => (n === i - 1 ? item : n === i ? items[i - 1] : x)))}>
                ↑ Up
              </Button>
              <Button size="sm" variant="ghost" onClick={() => onChange(items.filter((_, n) => n !== i))}>
                Remove
              </Button>
            </div>
          </div>
        ))}
        <div className="flex flex-wrap gap-2">
          {k.bulkImage ? (
            <Button size="sm" className="self-start" onClick={() => setBulk(true)}>
              + Add photos
            </Button>
          ) : null}
          <Button size="sm" variant="secondary" className="self-start" onClick={() => onChange([...items, defaults(k.list)])}>
            {k.bulkImage ? "+ Add one" : "+ Add"}
          </Button>
        </div>
        {k.bulkImage && items.length ? <p className="text-xs text-muted">{items.length} of 60 photos</p> : null}
        {bulk && k.bulkImage ? (
          <MediaDialog
            onClose={() => setBulk(false)}
            onPickMany={(ids) => {
              const key = k.bulkImage as string;
              onChange([...items, ...ids.map((id) => ({ ...defaults(k.list), [key]: id }))].slice(0, 60));
              setBulk(false);
            }}
          />
        ) : null}
      </fieldset>
    );
  }
  return (
    <Field label={label} hint={spec.hint ?? (k === "markdown" ? "Markdown: **bold**, *italic*, [link](https://…), # headings, - lists" : undefined)}>
      {(p) =>
        k === "textarea" || k === "markdown" ? (
          <Textarea {...p} rows={k === "markdown" ? 8 : 3} value={String(value ?? "")} onChange={(e) => onChange(e.target.value)} className={k === "markdown" ? "font-mono" : undefined} />
        ) : (
          <Input
            {...p}
            type={k === "number" ? "number" : "text"}
            value={String(value ?? "")}
            onChange={(e) => onChange(k === "number" ? (e.target.value ? Number(e.target.value) : undefined) : e.target.value)}
          />
        )
      }
    </Field>
  );
}

export function WebsiteEditor({ id }: { id: string }) {
  const { api } = useSession();
  const q = useQuery({ queryKey: ["site-entry", id], queryFn: () => ok(api.GET("/api/v1/admin/site/entries/{entry_id}", { params: { path: { entry_id: id } } })) });
  const versions = useQuery({ queryKey: ["site-versions", id], queryFn: () => ok(api.GET("/api/v1/admin/site/entries/{entry_id}/versions", { params: { path: { entry_id: id } } })) });
  const [content, setContent] = useState<Json | null>(null);
  const [slug, setSlug] = useState("");
  const [adding, setAdding] = useState("hero");
  const [dirty, setDirty] = useState(false);
  useEffect(() => {
    if (q.data && !dirty) {
      setContent(q.data.draft as Json);
      setSlug(q.data.slug);
    }
  }, [q.data, dirty]);

  const path = { params: { path: { entry_id: id } } };
  const save = useAction(
    () =>
      ok(
        api.PATCH("/api/v1/admin/site/entries/{entry_id}", {
          ...path,
          body: { slug: slug !== q.data?.slug ? slug : undefined, content: clean(content) as unknown as components["schemas"]["EntryContent"] },
        }),
      ),
    { success: "Draft saved.", onDone: () => setDirty(false) },
  );
  const publish = useAction(() => ok(api.POST("/api/v1/admin/site/entries/{entry_id}/publish", path)), { success: "Published. The site updates within a few minutes." });
  const unpublish = useAction(() => ok(api.POST("/api/v1/admin/site/entries/{entry_id}/unpublish", path)), { success: "Unpublished." });
  const preview = useAction(() => ok(api.POST("/api/v1/admin/site/entries/{entry_id}/preview", path)), {
    onDone: (r) => window.open(r.url, "_blank", "noopener"),
  });
  const restore = useAction(
    (version: number) => ok(api.POST("/api/v1/admin/site/entries/{entry_id}/versions/{version}/restore", { params: { path: { entry_id: id, version } } })),
    { success: "Version copied into the draft. Publish to make it live.", onDone: () => setDirty(false) },
  );
  const remove = useAction(() => ok(api.DELETE("/api/v1/admin/site/entries/{entry_id}", path)), {
    success: "Deleted.",
    onDone: () => window.location.assign("/website"),
  });

  if (q.error) return <ErrorNotice error={q.error} />;
  if (!q.data || !content) return <Skeleton className="h-96" />;
  const e = q.data;
  const isPost = e.kind === "post";
  const blocks = (content.blocks as Json[] | undefined) ?? [];
  const seo = (content.seo as Json | undefined) ?? {};
  const set = (patch: Json) => {
    setContent({ ...content, ...patch });
    setDirty(true);
  };
  const setBlock = (i: number, b: Json) => set({ blocks: blocks.map((x, n) => (n === i ? b : x)) });
  const move = (i: number, d: -1 | 1) => {
    const next = [...blocks];
    const [b] = next.splice(i, 1);
    if (b) next.splice(i + d, 0, b);
    set({ blocks: next });
  };
  const error = save.error ?? publish.error ?? unpublish.error ?? preview.error ?? restore.error ?? remove.error;
  const address = isPost ? `/blog/${slug}` : `/${slug}`;

  return (
    <>
      <p className="mb-2 text-sm">
        <Link href="/website" className="text-blue hover:underline">
          ← Website
        </Link>
      </p>
      <PageHeader
        title={String(content.title || "Untitled")}
        description={`${isPost ? "Blog post" : "Page"} · ${e.locale} · ${address} · ${e.version ? `version ${e.version}` : "never published"}`}
        actions={
          <>
            <Badge tone={e.status === "published" ? "good" : e.status === "changed" ? "warn" : "neutral"}>
              {e.status === "changed" ? "Unpublished changes" : e.status === "published" ? "Live" : "Draft"}
            </Badge>
            <Button variant="secondary" loading={preview.isPending} onClick={() => preview.mutate(undefined)} disabled={dirty}>
              Preview
            </Button>
            <Button variant="secondary" loading={save.isPending} disabled={!dirty} onClick={() => save.mutate(undefined)}>
              Save draft
            </Button>
            <Button loading={publish.isPending} disabled={dirty} onClick={() => publish.mutate(undefined)}>
              Publish
            </Button>
          </>
        }
      />
      {dirty ? <p className="mb-4 rounded-lg bg-warn-bg px-4 py-2 text-sm text-warn">You have unsaved changes. Save the draft before previewing or publishing.</p> : null}
      {error ? <ErrorNotice error={error} className="mb-4" /> : null}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-6 lg:col-span-2">
          <Card className="flex flex-col gap-4 p-5">
            <Field label="Title">{(p) => <Input {...p} value={String(content.title ?? "")} onChange={(ev) => set({ title: ev.target.value })} />}</Field>
            <Field label="Address" hint={slug ? `The page is at ${address}. Changing it adds a redirect from the old address.` : "Empty: the home page."}>
              {(p) => <Input {...p} value={slug} onChange={(ev) => { setSlug(ev.target.value.toLowerCase()); setDirty(true); }} placeholder="e.g. pricing or about/team" />}
            </Field>
          </Card>
          {isPost ? (
            <Card className="flex flex-col gap-4 p-5">
              <Field label="Summary (optional)">{(p) => <Textarea {...p} rows={2} value={String(content.excerpt ?? "")} onChange={(ev) => set({ excerpt: ev.target.value })} />}</Field>
              <Field label="Cover image (optional)">{() => <ImagePicker value={content.cover_id as string | undefined} onChange={(v) => set({ cover_id: v })} />}</Field>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Author (optional)">{(p) => <Input {...p} value={String(content.author ?? "")} onChange={(ev) => set({ author: ev.target.value })} />}</Field>
                <Field label="Tags (comma separated)">
                  {(p) => (
                    <Input
                      {...p}
                      value={((content.tags as string[] | undefined) ?? []).join(", ")}
                      onChange={(ev) => set({ tags: ev.target.value.split(",").map((t) => t.trim()).filter(Boolean).slice(0, 10) })}
                    />
                  )}
                </Field>
              </div>
              <Field label="Post (Markdown)" hint="Markdown: **bold**, *italic*, [link](https://…), # headings, - lists">
                {(p) => <Textarea {...p} rows={18} className="font-mono" value={String(content.body ?? "")} onChange={(ev) => set({ body: ev.target.value })} />}
              </Field>
            </Card>
          ) : (
            <>
              {blocks.map((b, i) => {
                const type = String(b.type);
                const def = BLOCKS[type];
                return (
                  <Card key={i}>
                    <CardHeader
                      title={def?.label ?? type}
                      actions={
                        <>
                          <Button size="sm" variant="ghost" disabled={i === 0} onClick={() => move(i, -1)}>
                            ↑
                          </Button>
                          <Button size="sm" variant="ghost" disabled={i === blocks.length - 1} onClick={() => move(i, 1)}>
                            ↓
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => set({ blocks: blocks.filter((_, n) => n !== i) })}>
                            Remove
                          </Button>
                        </>
                      }
                    />
                    <div className="grid gap-4 p-5 sm:grid-cols-2">
                      {(def?.fields ?? []).map((f) => (
                        <div key={f.key} className={typeof f.kind === "object" && "list" in f.kind ? "sm:col-span-2" : f.kind === "markdown" || f.kind === "cta" ? "sm:col-span-2" : ""}>
                          <FieldEditor spec={f} value={b[f.key]} onChange={(v) => setBlock(i, { ...b, [f.key]: v })} />
                        </div>
                      ))}
                    </div>
                  </Card>
                );
              })}
              <Card className="flex flex-wrap items-end gap-3 p-5">
                <Field label="Add a section">
                  {(p) => (
                    <Select {...p} value={adding} onChange={(ev) => setAdding(ev.target.value)}>
                      {Object.entries(BLOCKS).map(([k, v]) => (
                        <option key={k} value={k}>
                          {v.label}
                        </option>
                      ))}
                    </Select>
                  )}
                </Field>
                <Button variant="secondary" onClick={() => set({ blocks: [...blocks, blank(adding)] })} disabled={blocks.length >= 40}>
                  + Add section
                </Button>
              </Card>
            </>
          )}
        </div>
        <div className="flex flex-col gap-6">
          <Card className="flex flex-col gap-4 p-5">
            <h2 className="font-display text-base font-semibold">Search engines</h2>
            <Field label="Title (optional)" hint="Up to 70 characters; defaults to the page title.">
              {(p) => <Input {...p} maxLength={70} value={String(seo.title ?? "")} onChange={(ev) => set({ seo: { ...seo, title: ev.target.value } })} />}
            </Field>
            <Field label="Description (optional)" hint="Up to 170 characters.">
              {(p) => <Textarea {...p} rows={3} maxLength={170} value={String(seo.description ?? "")} onChange={(ev) => set({ seo: { ...seo, description: ev.target.value } })} />}
            </Field>
            <Field label="Share image (optional)">{() => <ImagePicker value={seo.image_id as string | undefined} onChange={(v) => set({ seo: { ...seo, image_id: v } })} />}</Field>
            <label className="flex items-center gap-2 text-sm text-ink">
              <input type="checkbox" checked={Boolean(seo.noindex)} onChange={(ev) => set({ seo: { ...seo, noindex: ev.target.checked } })} />
              Hide from search engines
            </label>
          </Card>
          <Card>
            <CardHeader title="Published versions" />
            <ul className="divide-y divide-line text-sm">
              {(versions.data?.data ?? []).map((v) => (
                <li key={v.version} className="flex items-center justify-between gap-2 px-5 py-2">
                  <span>
                    Version {v.version}
                    <span className="block text-xs text-muted">
                      {formatDate(v.published_at)} {formatTime(v.published_at)}
                      {v.published_by ? ` · ${v.published_by}` : ""}
                    </span>
                  </span>
                  <Button size="sm" variant="ghost" onClick={() => restore.mutate(v.version)}>
                    Restore
                  </Button>
                </li>
              ))}
              {versions.data?.data.length === 0 ? <li className="px-5 py-3 text-muted">Not published yet.</li> : null}
            </ul>
          </Card>
          <Card className="flex flex-col gap-2 p-5">
            {e.status !== "draft" ? (
              <Button variant="secondary" loading={unpublish.isPending} onClick={() => unpublish.mutate(undefined)}>
                Unpublish
              </Button>
            ) : (
              <DeleteButton onConfirm={() => remove.mutate(undefined)} loading={remove.isPending} />
            )}
            {e.translations.length ? (
              <p className="text-xs text-muted">
                Other languages:{" "}
                {e.translations.map((t) => (
                  <Link key={String(t.id)} href={`/website/${String(t.id)}`} className="mr-2 text-blue hover:underline">
                    {String(t.locale)}
                  </Link>
                ))}
              </p>
            ) : null}
          </Card>
        </div>
      </div>
    </>
  );
}

function DeleteButton({ onConfirm, loading }: { onConfirm: () => void; loading: boolean }) {
  const [sure, setSure] = useState(false);
  return sure ? (
    <div className="flex gap-2">
      <Button variant="danger" loading={loading} onClick={onConfirm}>
        Delete for good
      </Button>
      <Button variant="ghost" onClick={() => setSure(false)}>
        Keep
      </Button>
    </div>
  ) : (
    <Button variant="ghost" onClick={() => setSure(true)}>
      Delete draft
    </Button>
  );
}
