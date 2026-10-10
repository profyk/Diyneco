"use client";

import { currencySymbol, formatMoney, ok, parseAmount } from "@diyneco/api-client";
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
  Textarea,
} from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAction } from "../common";
import { useCurrency, useSession } from "../session";

const DIETARY = ["vegetarian", "vegan", "halaal", "kosher", "gluten_free"] as const;
const ALLERGENS = [
  "gluten",
  "crustaceans",
  "egg",
  "fish",
  "peanuts",
  "soy",
  "dairy",
  "tree_nuts",
  "celery",
  "mustard",
  "sesame",
  "sulphites",
  "lupin",
  "molluscs",
] as const;
const IMAGE_TYPES = ["image/jpeg", "image/webp"] as const;
const IMAGE_MAX_BYTES = 5 * 1024 * 1024;

export function Menu() {
  const { api, can } = useSession();
  const [dialog, setDialog] = useState<null | "category" | "station" | "groups" | { item: string | null }>(null);
  const categories = useQuery({ queryKey: ["menu", "categories"], queryFn: () => ok(api.GET("/api/v1/menu/categories")) });
  const items = useQuery({ queryKey: ["menu", "items"], queryFn: () => ok(api.GET("/api/v1/menu/items")) });
  const stations = useQuery({ queryKey: ["stations"], queryFn: () => ok(api.GET("/api/v1/kitchen-stations")) });
  const availability = useAction(
    ({ id, available }: { id: string; available: boolean }) =>
      ok(api.POST("/api/v1/menu/items/{item_id}/availability", { params: { path: { item_id: id } }, body: { available } })),
    { success: (i) => (i.is_available ? `${i.name} is back on the menu.` : `${i.name} is sold out.`) },
  );

  return (
    <>
      <PageHeader
        title="Menu"
        description="What guests see on their tablets. Changes appear on tablets and kitchen displays immediately."
        actions={
          can("menu.manage") ? (
            <>
              <Button variant="secondary" onClick={() => setDialog("station")}>
                Add kitchen station
              </Button>
              <Button variant="secondary" onClick={() => setDialog("category")}>
                Add category
              </Button>
              <Button variant="secondary" onClick={() => setDialog("groups")}>
                Options
              </Button>
              <Button onClick={() => setDialog({ item: null })}>Add item</Button>
            </>
          ) : null
        }
      />
      {availability.error ? <ErrorNotice error={availability.error} className="mb-4" /> : null}
      {categories.isLoading || items.isLoading ? (
        <Skeleton className="h-40" />
      ) : !categories.data?.data.length ? (
        <Card>
          <EmptyState title="Start your menu" body="Add a kitchen station and a category, then add items." />
        </Card>
      ) : (
        <div className="flex flex-col gap-6">
          {categories.data.data.map((c) => {
            const list = (items.data?.data ?? []).filter((i) => i.category_id === c.id);
            return (
              <Card key={c.id}>
                <CardHeader title={c.name} description={`${list.length} item${list.length === 1 ? "" : "s"}`} />
                {list.length === 0 ? (
                  <EmptyState title="No items in this category" />
                ) : (
                  <ul className="divide-y divide-line">
                    {list.map((i) => (
                      <li key={i.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                        <div className="min-w-0">
                          <p className="font-medium text-ink">
                            {i.name}{" "}
                            {!i.is_available ? <Badge tone="crit">Sold out</Badge> : !i.available_now ? <Badge>Outside its hours</Badge> : null}
                          </p>
                          <p className="text-sm text-muted">
                            {formatMoney(i.price)}
                            {i.dietary_tags.length ? ` · ${i.dietary_tags.join(", ").replace(/_/g, " ")}` : ""}
                            {i.allergens.length ? ` · contains ${i.allergens.join(", ").replace(/_/g, " ")}` : ""}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          {can("menu.availability") ? (
                            <Button
                              size="sm"
                              variant={i.is_available ? "secondary" : "success"}
                              onClick={() => availability.mutate({ id: i.id, available: !i.is_available })}
                            >
                              {i.is_available ? "Mark sold out" : "Back in stock"}
                            </Button>
                          ) : null}
                          {can("menu.manage") ? (
                            <Button size="sm" variant="ghost" onClick={() => setDialog({ item: i.id })}>
                              Edit
                            </Button>
                          ) : null}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            );
          })}
        </div>
      )}
      {dialog === "category" ? <NameDialog kind="category" onClose={() => setDialog(null)} /> : null}
      {dialog === "station" ? <NameDialog kind="station" onClose={() => setDialog(null)} /> : null}
      {dialog === "groups" ? <GroupsDialog onClose={() => setDialog(null)} /> : null}
      {dialog && typeof dialog === "object" ? (
        <ItemDialog
          itemId={dialog.item}
          categories={categories.data?.data ?? []}
          stations={stations.data?.data ?? []}
          onClose={() => setDialog(null)}
        />
      ) : null}
    </>
  );
}

function NameDialog({ kind, onClose }: { kind: "category" | "station"; onClose: () => void }) {
  const { api } = useSession();
  const [name, setName] = useState("");
  const save = useAction(
    async () =>
      kind === "category"
        ? ok(api.POST("/api/v1/menu/categories", { body: { name: name.trim(), sort_order: 0 } }))
        : ok(api.POST("/api/v1/kitchen-stations", { body: { name: name.trim(), sort_order: 0 } })),
    { success: kind === "category" ? "Category added." : "Station added.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      size="sm"
      title={kind === "category" ? "Add category" : "Add kitchen station"}
      description={kind === "station" ? "Each station gets its own kitchen display, e.g. Grill, Pastry, Bar." : undefined}
      footer={
        <Button disabled={!name.trim()} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Add
        </Button>
      }
    >
      <Field label="Name">{(p) => <Input {...p} autoFocus value={name} onChange={(e) => setName(e.target.value)} />}</Field>
      {save.error ? <ErrorNotice error={save.error} className="mt-3" /> : null}
    </Dialog>
  );
}

function ItemDialog({
  itemId,
  categories,
  stations,
  onClose,
}: {
  itemId: string | null;
  categories: { id: string; name: string }[];
  stations: { id: string; name: string }[];
  onClose: () => void;
}) {
  const { api } = useSession();
  const currency = useCurrency();
  const existing = useQuery({
    queryKey: ["menu", "item", itemId],
    queryFn: () => ok(api.GET("/api/v1/menu/items/{item_id}", { params: { path: { item_id: itemId! } } })),
    enabled: Boolean(itemId),
  });
  const item = existing.data;
  const [form, setForm] = useState<{
    name?: string;
    description?: string;
    price?: string;
    category_id?: string;
    station_id?: string;
    charge_category?: "food" | "beverage";
    dietary?: string[];
    allergens?: string[];
    groups?: string[];
  }>({});
  const groups = useQuery({ queryKey: ["menu", "modifier-groups"], queryFn: () => ok(api.GET("/api/v1/menu/modifier-groups")) });
  const v = {
    name: form.name ?? item?.name ?? "",
    description: form.description ?? item?.description ?? "",
    price: form.price ?? (item ? (item.price.amount_minor / 100).toFixed(2) : ""),
    category_id: form.category_id ?? item?.category_id ?? categories[0]?.id ?? "",
    station_id: form.station_id ?? item?.station_id ?? stations[0]?.id ?? "",
    charge_category: form.charge_category ?? item?.charge_category ?? "food",
    dietary: form.dietary ?? item?.dietary_tags ?? [],
    allergens: form.allergens ?? item?.allergens ?? [],
    groups: form.groups ?? item?.modifier_groups.map((g) => g.id) ?? [],
  };
  const minor = parseAmount(v.price);
  const body = {
    name: v.name.trim(),
    description: v.description.trim() || null,
    price: { amount_minor: minor ?? 0, currency },
    category_id: v.category_id,
    station_id: v.station_id,
    charge_category: v.charge_category,
    dietary_tags: v.dietary as (typeof DIETARY)[number][],
    allergens: v.allergens as (typeof ALLERGENS)[number][],
    sort_order: item?.sort_order ?? 0,
  };
  const groupsChanged = form.groups !== undefined;
  const save = useAction(
    async () => {
      const saved = itemId
        ? await ok(
            api.PATCH("/api/v1/menu/items/{item_id}", {
              params: { path: { item_id: itemId }, header: { "If-Match": `"${item?.version}"` } as never },
              body,
            }),
          )
        : await ok(api.POST("/api/v1/menu/items", { body }));
      if (groupsChanged) {
        await ok(
          api.PUT("/api/v1/menu/items/{item_id}/modifier-groups", {
            params: { path: { item_id: saved.id } },
            body: { group_ids: v.groups },
          }),
        );
      }
      return saved;
    },
    { success: itemId ? "Item updated." : "Item added.", onDone: onClose },
  );
  const set = (patch: Partial<typeof form>) => setForm((f) => ({ ...f, ...patch }));

  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title={itemId ? "Edit item" : "Add item"}
      description="Price changes are recorded with your name. A price change may ask for your PIN."
      footer={
        <Button disabled={!v.name.trim() || minor === null || !v.category_id || !v.station_id} loading={save.isPending} onClick={() => save.mutate(undefined)}>
          Save
        </Button>
      }
    >
      {itemId && !item ? (
        <Skeleton className="h-40" />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Name" className="sm:col-span-2">
            {(p) => <Input {...p} value={v.name} onChange={(e) => set({ name: e.target.value })} />}
          </Field>
          <Field label="Description" className="sm:col-span-2">
            {(p) => <Textarea {...p} value={v.description} onChange={(e) => set({ description: e.target.value })} />}
          </Field>
          <Field label={`Price (${currencySymbol(currency)})`}>{(p) => <Input {...p} inputMode="decimal" value={v.price} onChange={(e) => set({ price: e.target.value })} />}</Field>
          <Field label="Type">
            {(p) => (
              <Select {...p} value={v.charge_category} onChange={(e) => set({ charge_category: e.target.value as "food" | "beverage" })}>
                <option value="food">Food</option>
                <option value="beverage">Beverage</option>
              </Select>
            )}
          </Field>
          <Field label="Category">
            {(p) => (
              <Select {...p} value={v.category_id} onChange={(e) => set({ category_id: e.target.value })}>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Kitchen station">
            {(p) => (
              <Select {...p} value={v.station_id} onChange={(e) => set({ station_id: e.target.value })}>
                {stations.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Chips legend="Dietary" all={DIETARY} value={v.dietary} onChange={(dietary) => set({ dietary })} />
          <Chips legend="Contains allergens" all={ALLERGENS} value={v.allergens} onChange={(allergens) => set({ allergens })} />
          {groups.data?.data.length ? (
            <fieldset className="sm:col-span-2">
              <legend className="mb-2 text-sm font-medium text-ink">Options guests choose</legend>
              <div className="flex flex-col gap-2">
                {groups.data.data.map((g) => (
                  <label key={g.id} className="flex items-center gap-2 text-sm text-ink">
                    <input
                      type="checkbox"
                      checked={v.groups.includes(g.id)}
                      onChange={(e) => set({ groups: e.target.checked ? [...v.groups, g.id] : v.groups.filter((x) => x !== g.id) })}
                    />
                    {g.name}
                    <span className="text-muted">({g.options.map((o) => o.name).join(", ") || "no options yet"})</span>
                  </label>
                ))}
              </div>
            </fieldset>
          ) : null}
          {itemId && item ? <ImageField itemId={itemId} imageUrl={item.image_url} /> : null}
        </div>
      )}
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}

function Chips<T extends string>({
  legend,
  all,
  value,
  onChange,
}: {
  legend: string;
  all: readonly T[];
  value: readonly string[];
  onChange: (next: T[]) => void;
}) {
  return (
    <fieldset className="sm:col-span-2">
      <legend className="mb-2 text-sm font-medium text-ink">{legend}</legend>
      <div className="flex flex-wrap gap-2">
        {all.map((d) => (
          <label key={d} className="flex items-center gap-2 rounded-full border border-line px-3 py-1 text-sm">
            <input
              type="checkbox"
              checked={value.includes(d)}
              onChange={(e) => onChange((e.target.checked ? [...value, d] : value.filter((x) => x !== d)) as T[])}
            />
            {d.replace("_", " ")}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

/** Two steps: ask the API for a signed upload address, then send the file straight to storage. */
function ImageField({ itemId, imageUrl }: { itemId: string; imageUrl: string | null }) {
  const { api } = useSession();
  const [problem, setProblem] = useState<string | null>(null);
  const upload = useAction(
    async (file: File) => {
      const target = await ok(
        api.POST("/api/v1/menu/items/{item_id}/image", {
          params: { path: { item_id: itemId } },
          body: { content_type: file.type as (typeof IMAGE_TYPES)[number], size_bytes: file.size },
        }),
      );
      const res = await fetch(target.upload_url, { method: target.method, headers: target.headers, body: file });
      if (!res.ok) throw new Error("The photo could not be uploaded. Try again.");
      return target;
    },
    { success: "Photo uploaded." },
  );
  return (
    <div className="sm:col-span-2">
      <p className="mb-2 text-sm font-medium text-ink">Photo</p>
      <div className="flex flex-wrap items-center gap-4">
        {imageUrl ? <img src={imageUrl} alt="" className="size-20 rounded-lg border border-line object-cover" /> : null}
        <input
          type="file"
          accept={IMAGE_TYPES.join(",")}
          aria-label="Choose a photo"
          className="text-sm"
          onChange={(e) => {
            const file = e.target.files?.[0];
            e.target.value = "";
            if (!file) return;
            if (!(IMAGE_TYPES as readonly string[]).includes(file.type) || file.size > IMAGE_MAX_BYTES) {
              setProblem("Choose a JPEG or WebP photo of 5 MB or less.");
              return;
            }
            setProblem(null);
            upload.mutate(file);
          }}
        />
        {upload.isPending ? <span className="text-sm text-muted">Uploading…</span> : null}
      </div>
      {problem ? <p className="mt-2 text-sm text-crit">{problem}</p> : null}
      {upload.error ? <ErrorNotice error={upload.error} className="mt-2" /> : null}
    </div>
  );
}

/** Option groups such as "Cooking" (rare, medium, well done) or "Sides", shared between items. */
function GroupsDialog({ onClose }: { onClose: () => void }) {
  const { api } = useSession();
  const currency = useCurrency();
  const groups = useQuery({ queryKey: ["menu", "modifier-groups"], queryFn: () => ok(api.GET("/api/v1/menu/modifier-groups")) });
  const [g, setG] = useState({ name: "", min: "0", max: "1" });
  const [opt, setOpt] = useState({ group: "", name: "", price: "0" });
  const min = Number(g.min);
  const max = Number(g.max);
  const groupOk =
    g.name.trim() !== "" && Number.isInteger(min) && Number.isInteger(max) && min >= 0 && max >= 1 && max <= 20 && min <= max;
  const delta = parseAmount(opt.price);
  const addGroup = useAction(
    () => ok(api.POST("/api/v1/menu/modifier-groups", { body: { name: g.name.trim(), min_select: min, max_select: max } })),
    {
      success: "Option group added.",
      onDone: (created) => {
        setG({ name: "", min: "0", max: "1" });
        setOpt({ group: created.id, name: "", price: "0" });
      },
    },
  );
  const addOption = useAction(
    () =>
      ok(
        api.POST("/api/v1/menu/modifier-groups/{group_id}/options", {
          params: { path: { group_id: opt.group } },
          body: { name: opt.name.trim(), price_delta: { amount_minor: delta ?? 0, currency }, sort_order: 0 },
        }),
      ),
    { success: "Option added.", onDone: () => setOpt((o) => ({ ...o, name: "", price: "0" })) },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title="Options"
      description="Choices guests make when ordering, such as cooking preference or a side. Tick a group on an item to offer it."
    >
      {groups.isLoading ? (
        <Skeleton className="h-24" />
      ) : groups.data?.data.length ? (
        <ul className="mb-6 divide-y divide-line rounded-lg border border-line">
          {groups.data.data.map((grp) => (
            <li key={grp.id} className="px-4 py-3">
              <p className="font-medium text-ink">
                {grp.name}{" "}
                <span className="text-sm font-normal text-muted">
                  {grp.min_select
                    ? `choose ${grp.min_select}${grp.max_select > grp.min_select ? ` to ${grp.max_select}` : ""}`
                    : `optional, up to ${grp.max_select}`}
                </span>
              </p>
              <p className="text-sm text-muted">
                {grp.options.length
                  ? grp.options
                      .map((o) => (o.price_delta.amount_minor ? `${o.name} (+${formatMoney(o.price_delta)})` : o.name))
                      .join(", ")
                  : "No options yet"}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mb-6 text-sm text-muted">No option groups yet.</p>
      )}
      <div className="grid gap-6 sm:grid-cols-2">
        <form
          className="flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            addGroup.mutate(undefined);
          }}
        >
          <h3 className="font-display text-sm font-semibold">New group</h3>
          <Field label="Name">{(p) => <Input {...p} placeholder="Cooking" value={g.name} onChange={(e) => setG({ ...g, name: e.target.value })} />}</Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Must choose at least">
              {(p) => <Input {...p} type="number" min={0} max={20} value={g.min} onChange={(e) => setG({ ...g, min: e.target.value })} />}
            </Field>
            <Field label="May choose up to">
              {(p) => <Input {...p} type="number" min={1} max={20} value={g.max} onChange={(e) => setG({ ...g, max: e.target.value })} />}
            </Field>
          </div>
          {addGroup.error ? <ErrorNotice error={addGroup.error} /> : null}
          <Button type="submit" variant="secondary" disabled={!groupOk} loading={addGroup.isPending}>
            Add group
          </Button>
        </form>
        <form
          className="flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            addOption.mutate(undefined);
          }}
        >
          <h3 className="font-display text-sm font-semibold">New option</h3>
          <Field label="Group">
            {(p) => (
              <Select {...p} value={opt.group} onChange={(e) => setOpt({ ...opt, group: e.target.value })}>
                <option value="">Choose a group</option>
                {groups.data?.data.map((grp) => (
                  <option key={grp.id} value={grp.id}>
                    {grp.name}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Name">{(p) => <Input {...p} placeholder="Medium rare" value={opt.name} onChange={(e) => setOpt({ ...opt, name: e.target.value })} />}</Field>
          <Field label={`Extra charge (${currencySymbol(currency)})`} hint="0 for no extra charge.">
            {(p) => <Input {...p} inputMode="decimal" value={opt.price} onChange={(e) => setOpt({ ...opt, price: e.target.value })} />}
          </Field>
          {addOption.error ? <ErrorNotice error={addOption.error} /> : null}
          <Button
            type="submit"
            variant="secondary"
            disabled={!opt.group || !opt.name.trim() || delta === null || delta < 0}
            loading={addOption.isPending}
          >
            Add option
          </Button>
        </form>
      </div>
    </Dialog>
  );
}
