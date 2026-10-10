"use client";

import { formatMoney, ok, parseAmount } from "@diyneco/api-client";
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
import { useSession } from "../session";

const DIETARY = ["vegetarian", "vegan", "halaal", "kosher", "gluten_free"] as const;

export function Menu() {
  const { api, can } = useSession();
  const [dialog, setDialog] = useState<null | "category" | "station" | { item: string | null }>(null);
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
  }>({});
  const v = {
    name: form.name ?? item?.name ?? "",
    description: form.description ?? item?.description ?? "",
    price: form.price ?? (item ? (item.price.amount_minor / 100).toFixed(2) : ""),
    category_id: form.category_id ?? item?.category_id ?? categories[0]?.id ?? "",
    station_id: form.station_id ?? item?.station_id ?? stations[0]?.id ?? "",
    charge_category: form.charge_category ?? item?.charge_category ?? "food",
    dietary: form.dietary ?? item?.dietary_tags ?? [],
  };
  const minor = parseAmount(v.price);
  const body = {
    name: v.name.trim(),
    description: v.description.trim() || null,
    price: { amount_minor: minor ?? 0, currency: "ZAR" },
    category_id: v.category_id,
    station_id: v.station_id,
    charge_category: v.charge_category,
    dietary_tags: v.dietary as (typeof DIETARY)[number][],
    sort_order: item?.sort_order ?? 0,
  };
  const save = useAction(
    async () =>
      itemId
        ? ok(
            api.PATCH("/api/v1/menu/items/{item_id}", {
              params: { path: { item_id: itemId }, header: { "If-Match": `"${item?.version}"` } as never },
              body,
            }),
          )
        : ok(api.POST("/api/v1/menu/items", { body })),
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
          <Field label="Price (R)">{(p) => <Input {...p} inputMode="decimal" value={v.price} onChange={(e) => set({ price: e.target.value })} />}</Field>
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
          <fieldset className="sm:col-span-2">
            <legend className="mb-2 text-sm font-medium text-ink">Dietary</legend>
            <div className="flex flex-wrap gap-2">
              {DIETARY.map((d) => (
                <label key={d} className="flex items-center gap-2 rounded-full border border-line px-3 py-1 text-sm">
                  <input
                    type="checkbox"
                    checked={v.dietary.includes(d)}
                    onChange={(e) => set({ dietary: e.target.checked ? [...v.dietary, d] : v.dietary.filter((x) => x !== d) })}
                  />
                  {d.replace("_", " ")}
                </label>
              ))}
            </div>
          </fieldset>
        </div>
      )}
      {save.error ? <ErrorNotice error={save.error} className="mt-4" /> : null}
    </Dialog>
  );
}
