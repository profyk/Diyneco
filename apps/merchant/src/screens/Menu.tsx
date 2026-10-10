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
  const [dialog, setDialog] = useState<null | "category" | "station" | "groups" | "hours" | "import" | { item: string | null }>(null);
  const [editCategory, setEditCategory] = useState<string | null>(null);
  const schedules = useQuery({ queryKey: ["menu", "schedules"], queryFn: () => ok(api.GET("/api/v1/menu/schedules")) });
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
              <Button variant="secondary" onClick={() => setDialog("hours")}>
                Serving hours
              </Button>
              <Button variant="secondary" onClick={() => setDialog("import")}>
                Import CSV
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
                <CardHeader
                  title={c.name}
                  description={`${list.length} item${list.length === 1 ? "" : "s"}${
                    c.schedule_id ? ` · ${schedules.data?.data.find((x) => x.id === c.schedule_id)?.name ?? "limited hours"}` : " · all day"
                  }`}
                  actions={
                    can("menu.manage") ? (
                      <Button size="sm" variant="ghost" onClick={() => setEditCategory(c.id)}>
                        Edit category
                      </Button>
                    ) : undefined
                  }
                />
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
      {dialog === "hours" ? <HoursDialog onClose={() => setDialog(null)} /> : null}
      {dialog === "import" ? <MenuImportDialog onClose={() => setDialog(null)} /> : null}
      {editCategory && categories.data ? (
        <CategoryDialog
          category={categories.data.data.find((c) => c.id === editCategory)!}
          schedules={schedules.data?.data ?? []}
          onClose={() => setEditCategory(null)}
        />
      ) : null}
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
    schedule_id?: string;
    ingredients?: string;
  }>({});
  const [confirmDelete, setConfirmDelete] = useState(false);
  const schedules = useQuery({ queryKey: ["menu", "schedules"], queryFn: () => ok(api.GET("/api/v1/menu/schedules")) });
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
    schedule_id: form.schedule_id ?? item?.schedule_id ?? "",
    ingredients: form.ingredients ?? item?.ingredients.join(", ") ?? "",
  };
  const ingredients = v.ingredients
    .split(/[,;\n]/)
    .map((x) => x.trim())
    .filter(Boolean);
  const ingredientsOk = ingredients.length <= 40 && ingredients.every((x) => x.length <= 60);
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
    schedule_id: v.schedule_id || null,
    ingredients,
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
  const remove = useAction(
    () => ok(api.DELETE("/api/v1/menu/items/{item_id}", { params: { path: { item_id: itemId! } } })),
    { success: "Item removed from the menu. Past orders keep it.", onDone: onClose },
  );

  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title={itemId ? "Edit item" : "Add item"}
      description="Price changes are recorded with your name. A price change may ask for your PIN."
      footer={
        <>
          {itemId ? (
            confirmDelete ? (
              <Button variant="danger" loading={remove.isPending} onClick={() => remove.mutate(undefined)}>
                Yes, delete item
              </Button>
            ) : (
              <Button variant="ghost" onClick={() => setConfirmDelete(true)}>
                Delete item
              </Button>
            )
          ) : null}
          <Button
            disabled={!v.name.trim() || minor === null || !v.category_id || !v.station_id || !ingredientsOk}
            loading={save.isPending}
            onClick={() => save.mutate(undefined)}
          >
            Save
          </Button>
        </>
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
          <Field label="Serving hours" hint="Outside these hours guests see the item but cannot order it.">
            {(p) => (
              <Select {...p} value={v.schedule_id} onChange={(e) => set({ schedule_id: e.target.value })}>
                <option value="">Same as its category</option>
                {schedules.data?.data.map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.name}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Chips legend="Dietary" all={DIETARY} value={v.dietary} onChange={(dietary) => set({ dietary })} />
          <Field
            label="Ingredients"
            hint="Separated by commas. Guests see them on the tablet."
            error={ingredientsOk ? undefined : "At most 40 ingredients of up to 60 characters each."}
            className="sm:col-span-2"
          >
            {(p) => (
              <Textarea
                {...p}
                rows={2}
                placeholder="beef, potato, rosemary, garlic butter"
                value={v.ingredients}
                onChange={(e) => set({ ingredients: e.target.value })}
              />
            )}
          </Field>
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
      {save.error || remove.error ? <ErrorNotice error={save.error ?? remove.error} className="mt-4" /> : null}
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
      <Presets existing={(groups.data?.data ?? []).map((x) => x.name.toLowerCase())} />
      {groups.isLoading ? (
        <Skeleton className="h-24" />
      ) : groups.data?.data.length ? (
        <ul className="mb-6 divide-y divide-line rounded-lg border border-line">
          {groups.data.data.map((grp) => (
            <GroupRow key={grp.id} group={grp} />
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

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] as const;

function describeWindows(windows: { days: number[]; from: string; to: string }[]): string {
  return windows
    .map((w) => {
      const days = w.days.length === 7 ? "Every day" : w.days.map((d) => DAY_NAMES[d - 1]).join(", ");
      return `${days} ${w.from}–${w.to}`;
    })
    .join("; ");
}

function CategoryDialog({
  category,
  schedules,
  onClose,
}: {
  category: { id: string; name: string; sort_order: number; schedule_id: string | null };
  schedules: { id: string; name: string }[];
  onClose: () => void;
}) {
  const { api } = useSession();
  const [name, setName] = useState(category.name);
  const [order, setOrder] = useState(String(category.sort_order));
  const [schedule, setSchedule] = useState(category.schedule_id ?? "");
  const save = useAction(
    () =>
      ok(
        api.PATCH("/api/v1/menu/categories/{category_id}", {
          params: { path: { category_id: category.id } },
          body: { name: name.trim(), sort_order: Number(order) || 0, schedule_id: schedule || null },
        }),
      ),
    { success: "Category saved.", onDone: onClose },
  );
  const [withItems, setWithItems] = useState(false);
  const remove = useAction(
    () =>
      ok(
        api.DELETE("/api/v1/menu/categories/{category_id}", {
          params: { path: { category_id: category.id }, query: { with_items: withItems } },
        }),
      ),
    { success: withItems ? "Category and its items deleted." : "Category deleted.", onDone: onClose },
  );
  return (
    <Dialog
      open
      onClose={onClose}
      title={`Edit ${category.name}`}
      footer={
        <>
          <Button variant="ghost" loading={remove.isPending} onClick={() => remove.mutate(undefined)}>
            Delete category
          </Button>
          <Button disabled={!name.trim()} loading={save.isPending} onClick={() => save.mutate(undefined)}>
            Save
          </Button>
        </>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Name" className="sm:col-span-2">
          {(p) => <Input {...p} value={name} onChange={(e) => setName(e.target.value)} />}
        </Field>
        <Field label="Position" hint="Lower numbers show first.">
          {(p) => <Input {...p} type="number" min={0} value={order} onChange={(e) => setOrder(e.target.value)} />}
        </Field>
        <Field label="Serving hours">
          {(p) => (
            <Select {...p} value={schedule} onChange={(e) => setSchedule(e.target.value)}>
              <option value="">All day</option>
              {schedules.map((x) => (
                <option key={x.id} value={x.id}>
                  {x.name}
                </option>
              ))}
            </Select>
          )}
        </Field>
      </div>
      <label className="mt-4 flex items-start gap-2 text-sm text-ink">
        <input type="checkbox" className="mt-1" checked={withItems} onChange={(e) => setWithItems(e.target.checked)} />
        <span>
          Also delete every item in this category (asks for your PIN). Past orders and bills keep their items. Without this, a
          category can be deleted only when it is empty.
        </span>
      </label>
      {save.error || remove.error ? <ErrorNotice error={save.error ?? remove.error} className="mt-4" /> : null}
    </Dialog>
  );
}

type Win = { days: number[]; from: string; to: string };

/** Named serving hours ("Breakfast 06:30–10:30") that categories and items can follow. */
function HoursDialog({ onClose }: { onClose: () => void }) {
  const { api } = useSession();
  const schedules = useQuery({ queryKey: ["menu", "schedules"], queryFn: () => ok(api.GET("/api/v1/menu/schedules")) });
  const [name, setName] = useState("");
  const [windows, setWindows] = useState<Win[]>([{ days: [1, 2, 3, 4, 5, 6, 7], from: "06:30", to: "10:30" }]);
  const valid = name.trim() && windows.length && windows.every((w) => w.days.length && /^\d\d:\d\d$/.test(w.from) && /^\d\d:\d\d$/.test(w.to));
  const add = useAction(() => ok(api.POST("/api/v1/menu/schedules", { body: { name: name.trim(), windows } })), {
    success: "Serving hours added. Choose them on a category or item.",
    onDone: () => {
      setName("");
      setWindows([{ days: [1, 2, 3, 4, 5, 6, 7], from: "06:30", to: "10:30" }]);
    },
  });
  const setWin = (i: number, patch: Partial<Win>) => setWindows(windows.map((w, j) => (j === i ? { ...w, ...patch } : w)));
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title="Serving hours"
      description="Times are the hotel's local time. A window that ends before it starts runs past midnight."
    >
      {schedules.data?.data.length ? (
        <ul className="mb-6 divide-y divide-line rounded-lg border border-line text-sm">
          {schedules.data.data.map((x) => (
            <li key={x.id} className="px-4 py-3">
              <p className="font-medium text-ink">{x.name}</p>
              <p className="text-muted">{describeWindows(x.windows)}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mb-6 text-sm text-muted">No serving hours yet: everything can be ordered at any time.</p>
      )}
      <form
        className="flex flex-col gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          add.mutate(undefined);
        }}
      >
        <Field label="Name">{(p) => <Input {...p} placeholder="Breakfast" value={name} onChange={(e) => setName(e.target.value)} />}</Field>
        {windows.map((w, i) => (
          <fieldset key={i} className="rounded-lg border border-line p-3">
            <legend className="px-1 text-sm font-medium text-ink">Window {i + 1}</legend>
            <div className="flex flex-wrap gap-2">
              {DAY_NAMES.map((d, n) => (
                <label key={d} className="flex items-center gap-1 rounded-full border border-line px-3 py-1 text-sm">
                  <input
                    type="checkbox"
                    checked={w.days.includes(n + 1)}
                    onChange={(e) =>
                      setWin(i, { days: e.target.checked ? [...w.days, n + 1].sort() : w.days.filter((x) => x !== n + 1) })
                    }
                  />
                  {d}
                </label>
              ))}
            </div>
            <div className="mt-3 flex flex-wrap items-end gap-3">
              <Field label="From">{(p) => <Input {...p} type="time" value={w.from} onChange={(e) => setWin(i, { from: e.target.value })} />}</Field>
              <Field label="To">{(p) => <Input {...p} type="time" value={w.to} onChange={(e) => setWin(i, { to: e.target.value })} />}</Field>
              {windows.length > 1 ? (
                <Button size="sm" variant="ghost" onClick={() => setWindows(windows.filter((_, j) => j !== i))}>
                  Remove window
                </Button>
              ) : null}
            </div>
          </fieldset>
        ))}
        <div className="flex flex-wrap justify-between gap-2">
          <Button variant="secondary" disabled={windows.length >= 21} onClick={() => setWindows([...windows, { days: [6, 7], from: "07:00", to: "11:00" }])}>
            Add a window
          </Button>
          <Button type="submit" disabled={!valid} loading={add.isPending}>
            Add serving hours
          </Button>
        </div>
        {add.error ? <ErrorNotice error={add.error} /> : null}
      </form>
    </Dialog>
  );
}

const PRESETS: { name: string; min: number; max: number; hint: string; options: string[] }[] = [
  { name: "Steak temperature", min: 1, max: 1, hint: "Required: one choice", options: ["Rare", "Medium rare", "Medium", "Medium well", "Well done"] },
  { name: "Sauce", min: 0, max: 2, hint: "Optional, up to 2", options: ["Pepper sauce", "Mushroom sauce", "Cheese sauce", "Garlic butter", "Monkey gland sauce"] },
  { name: "Side", min: 1, max: 1, hint: "Required: one choice", options: ["Chips", "Side salad", "Mashed potato", "Seasonal vegetables", "Rice"] },
  { name: "Extras", min: 0, max: 5, hint: "Optional, up to 5", options: ["Extra cheese", "Bacon", "Avocado", "Fried egg", "Jalapeños"] },
  { name: "Egg style", min: 1, max: 1, hint: "Required: one choice", options: ["Fried", "Scrambled", "Poached", "Boiled"] },
  { name: "Milk", min: 0, max: 1, hint: "Optional", options: ["Full cream", "Low fat", "Oat milk", "Almond milk"] },
];

/** One-click option groups with their usual choices; prices are set before creating. */
function Presets({ existing }: { existing: string[] }) {
  const { api } = useSession();
  const currency = useCurrency();
  const [chosen, setChosen] = useState<number | null>(null);
  const [prices, setPrices] = useState<Record<string, string>>({});
  const [skip, setSkip] = useState<string[]>([]);
  const preset = chosen === null ? null : PRESETS[chosen]!;
  const options = preset ? preset.options.filter((o) => !skip.includes(o)) : [];
  const valid = options.length > 0 && options.every((o) => parseAmount(prices[o] || "0") !== null);
  const create = useAction(
    async () => {
      const group = await ok(
        api.POST("/api/v1/menu/modifier-groups", {
          body: { name: preset!.name, min_select: preset!.min, max_select: Math.min(preset!.max, options.length) },
        }),
      );
      for (const [n, o] of options.entries()) {
        await ok(
          api.POST("/api/v1/menu/modifier-groups/{group_id}/options", {
            params: { path: { group_id: group.id } },
            body: { name: o, price_delta: { amount_minor: parseAmount(prices[o] || "0") ?? 0, currency }, sort_order: n },
          }),
        );
      }
      return group;
    },
    {
      success: (g) => `${g.name} added. Tick it on the items that offer it.`,
      onDone: () => {
        setChosen(null);
        setPrices({});
        setSkip([]);
      },
    },
  );
  return (
    <div className="mb-6 rounded-lg border border-line p-4">
      <p className="text-sm font-semibold text-ink">Quick start</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {PRESETS.map((x, i) => (
          <Button
            key={x.name}
            size="sm"
            variant={chosen === i ? "primary" : "secondary"}
            disabled={existing.includes(x.name.toLowerCase())}
            onClick={() => {
              setChosen(chosen === i ? null : i);
              setSkip([]);
            }}
          >
            {x.name}
          </Button>
        ))}
      </div>
      {preset ? (
        <div className="mt-4">
          <p className="mb-2 text-sm text-muted">
            {preset.hint}. Untick choices you do not offer and set any extra charge ({currencySymbol(currency)}).
          </p>
          <ul className="grid gap-2 sm:grid-cols-2">
            {preset.options.map((o) => (
              <li key={o} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  aria-label={`Offer ${o}`}
                  checked={!skip.includes(o)}
                  onChange={(e) => setSkip(e.target.checked ? skip.filter((x) => x !== o) : [...skip, o])}
                />
                <span className="flex-1 text-sm">{o}</span>
                <Input
                  aria-label={`Extra charge for ${o}`}
                  inputMode="decimal"
                  className="w-24"
                  placeholder="0.00"
                  value={prices[o] ?? ""}
                  onChange={(e) => setPrices({ ...prices, [o]: e.target.value })}
                />
              </li>
            ))}
          </ul>
          {create.error ? <ErrorNotice error={create.error} className="mt-3" /> : null}
          <Button className="mt-3" disabled={!valid} loading={create.isPending} onClick={() => create.mutate(undefined)}>
            Add {preset.name.toLowerCase()}
          </Button>
        </div>
      ) : null}
    </div>
  );
}

const MENU_TEMPLATE =
  "category,name,description,price,type,station,dietary,allergens,ingredients,options\n" +
  'Grill,Rump steak 300 g,Flame-grilled with chips,245.00,food,,,,"beef;potato;salt;pepper","Steak temperature;Sauce"\n' +
  'Breakfast,Full English,"Eggs, bacon, sausage, beans and toast",165.00,food,,,"egg;gluten","egg;bacon;pork sausage;beans;bread",Egg style\n' +
  "Drinks,Fresh orange juice,,45.00,beverage,,vegan,,orange,\n";

/** Upload a whole menu from a spreadsheet: checked line by line, then imported all or nothing. */
function MenuImportDialog({ onClose }: { onClose: () => void }) {
  const { api } = useSession();
  const [csv, setCsv] = useState("");
  const [fileName, setFileName] = useState("");
  const send = (commit: boolean) =>
    ok(
      api.POST("/api/v1/menu/items/import", {
        params: { query: { commit } },
        body: csv as never,
        bodySerializer: (b: unknown) => b as string,
        headers: { "Content-Type": "text/csv" },
      }),
    );
  const check = useAction(() => send(false));
  const commit = useAction(() => send(true), {
    success: (r) => `${r.created} items imported${r.new_categories.length ? ` into ${r.new_categories.length} new categories` : ""}.`,
    onDone: onClose,
  });
  const report = check.data;
  return (
    <Dialog
      open
      onClose={onClose}
      size="lg"
      title="Import a menu from a spreadsheet"
      description="Columns: category, name, description, price (like 185.00), type (food or beverage), station (empty for the first), dietary, allergens, ingredients and options (option group names). Separate several values with semicolons. Missing categories are created."
      footer={
        <>
          <Button variant="secondary" disabled={!csv} loading={check.isPending} onClick={() => check.mutate(undefined)}>
            Check file
          </Button>
          <Button disabled={!report?.valid} loading={commit.isPending} onClick={() => commit.mutate(undefined)}>
            Import {report?.valid ? `${report.rows} items` : ""}
          </Button>
        </>
      }
    >
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="file"
          accept=".csv,text/csv"
          aria-label="Choose a CSV file"
          className="text-sm"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            setFileName(file.name);
            setCsv(await file.text());
            check.reset();
          }}
        />
        <a className="text-sm text-blue hover:underline" href={`data:text/csv;charset=utf-8,${encodeURIComponent(MENU_TEMPLATE)}`} download="diyneco-menu-template.csv">
          Download a template
        </a>
      </div>
      {fileName ? <p className="mt-2 text-sm text-muted">{fileName}</p> : null}
      {report ? (
        report.valid ? (
          <p className="mt-4 rounded-lg bg-good/10 p-3 text-sm text-ink">
            All {report.rows} items are ready.
            {report.new_categories.length ? ` New categories: ${report.new_categories.join(", ")}.` : ""}
          </p>
        ) : (
          <div className="mt-4 max-h-64 overflow-auto rounded-lg border border-line">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-muted">
                  <th className="px-3 py-2">Line</th>
                  <th className="px-3 py-2">Column</th>
                  <th className="px-3 py-2">Problem</th>
                </tr>
              </thead>
              <tbody>
                {report.errors.map((x, i) => (
                  <tr key={i} className="border-t border-line">
                    <td className="px-3 py-2">{x.line}</td>
                    <td className="px-3 py-2">{x.field}</td>
                    <td className="px-3 py-2">{x.problem}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : null}
      {check.error || commit.error ? <ErrorNotice error={check.error ?? commit.error} className="mt-4" /> : null}
    </Dialog>
  );
}

type OptionRow = { id: string; name: string; price_delta: { amount_minor: number; currency: string }; is_available: boolean };

/** One option group with inline edits: rules, choices, prices, sold out, remove. */
function GroupRow({
  group,
}: {
  group: { id: string; name: string; min_select: number; max_select: number; options: OptionRow[] };
}) {
  const { api, can } = useSession();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(group.name);
  const [min, setMin] = useState(String(group.min_select));
  const [max, setMax] = useState(String(group.max_select));
  const [prices, setPrices] = useState<Record<string, string>>({});
  const saveGroup = useAction(
    () =>
      ok(
        api.PATCH("/api/v1/menu/modifier-groups/{group_id}", {
          params: { path: { group_id: group.id } },
          body: { name: name.trim(), min_select: Number(min), max_select: Number(max) },
        }),
      ),
    { success: "Option group saved.", onDone: () => setEditing(false) },
  );
  const removeGroup = useAction(
    () => ok(api.DELETE("/api/v1/menu/modifier-groups/{group_id}", { params: { path: { group_id: group.id } } })),
    { success: `${group.name} removed from the menu.` },
  );
  const patchOption = useAction(
    ({ id, body }: { id: string; body: { is_available?: boolean; price_delta?: { amount_minor: number; currency: string } } }) =>
      ok(api.PATCH("/api/v1/menu/modifier-options/{option_id}", { params: { path: { option_id: id } }, body })),
  );
  const removeOption = useAction((id: string) =>
    ok(api.DELETE("/api/v1/menu/modifier-options/{option_id}", { params: { path: { option_id: id } } })),
  );
  const error = saveGroup.error ?? removeGroup.error ?? patchOption.error ?? removeOption.error;
  const rule = group.min_select
    ? `required, choose ${group.min_select}${group.max_select > group.min_select ? ` to ${group.max_select}` : ""}`
    : `optional, up to ${group.max_select}`;
  return (
    <li className="px-4 py-3">
      {editing ? (
        <div className="flex flex-wrap items-end gap-3">
          <Field label="Name">{(p) => <Input {...p} value={name} onChange={(e) => setName(e.target.value)} />}</Field>
          <Field label="At least">{(p) => <Input {...p} type="number" min={0} max={20} className="w-20" value={min} onChange={(e) => setMin(e.target.value)} />}</Field>
          <Field label="At most">{(p) => <Input {...p} type="number" min={1} max={20} className="w-20" value={max} onChange={(e) => setMax(e.target.value)} />}</Field>
          <Button size="sm" disabled={!name.trim() || Number(min) > Number(max)} loading={saveGroup.isPending} onClick={() => saveGroup.mutate(undefined)}>
            Save
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
            Cancel
          </Button>
        </div>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="font-medium text-ink">
            {group.name} <span className="text-sm font-normal text-muted">({rule})</span>
          </p>
          {can("menu.manage") ? (
            <div className="flex gap-1">
              <Button size="sm" variant="ghost" onClick={() => setEditing(true)}>
                Edit
              </Button>
              <Button size="sm" variant="ghost" loading={removeGroup.isPending} onClick={() => removeGroup.mutate(undefined)}>
                Delete group
              </Button>
            </div>
          ) : null}
        </div>
      )}
      {group.options.length ? (
        <ul className="mt-2 flex flex-col gap-1">
          {group.options.map((o) => {
            const typed = prices[o.id];
            const minor = typed === undefined ? null : parseAmount(typed || "0");
            return (
              <li key={o.id} className="flex flex-wrap items-center gap-2 text-sm">
                <span className={o.is_available ? "flex-1 text-ink" : "flex-1 text-muted line-through"}>{o.name}</span>
                {can("menu.manage") ? (
                  <>
                    <Input
                      aria-label={`Extra charge for ${o.name}`}
                      inputMode="decimal"
                      className="w-24"
                      value={typed ?? (o.price_delta.amount_minor / 100).toFixed(2)}
                      onChange={(e) => setPrices({ ...prices, [o.id]: e.target.value })}
                    />
                    {typed !== undefined && minor !== null && minor !== o.price_delta.amount_minor ? (
                      <Button
                        size="sm"
                        onClick={() =>
                          patchOption.mutate(
                            { id: o.id, body: { price_delta: { amount_minor: minor, currency: o.price_delta.currency } } },
                            { onSuccess: () => setPrices((x) => ({ ...x, [o.id]: undefined as never })) },
                          )
                        }
                      >
                        Save price
                      </Button>
                    ) : null}
                  </>
                ) : (
                  <span className="text-muted">{o.price_delta.amount_minor ? `+${formatMoney(o.price_delta)}` : "no charge"}</span>
                )}
                <Button size="sm" variant="ghost" onClick={() => patchOption.mutate({ id: o.id, body: { is_available: !o.is_available } })}>
                  {o.is_available ? "Sold out" : "Back in stock"}
                </Button>
                {can("menu.manage") ? (
                  <Button size="sm" variant="ghost" aria-label={`Remove ${o.name}`} onClick={() => removeOption.mutate(o.id)}>
                    Remove
                  </Button>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="mt-1 text-sm text-muted">No choices yet: add them below.</p>
      )}
      {error ? <ErrorNotice error={error} className="mt-2" /> : null}
    </li>
  );
}
