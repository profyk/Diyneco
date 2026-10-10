"use client";

import { ok } from "@diyneco/api-client";
import { Badge, Button, Dialog, ErrorNotice, Input, Spinner } from "@diyneco/shared-ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { cookApi, deviceApi } from "./api";
import { getDeviceToken } from "./device";

/**
 * Dishes of this display's stations. A signed-in cook marks one sold out and guest tablets stop
 * offering it at once (D67); no prices are shown here.
 */
export function SoldOutPanel({
  open,
  onClose,
  needCook,
}: {
  open: boolean;
  onClose: () => void;
  needCook: (action: () => void) => void;
}) {
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const menu = useQuery({
    queryKey: ["kitchen-menu"],
    queryFn: async () => {
      await getDeviceToken();
      return ok(deviceApi.GET("/api/v1/kitchen/menu"));
    },
    enabled: open,
  });
  const toggle = useMutation({
    mutationFn: ({ id, available }: { id: string; available: boolean }) =>
      ok(cookApi.POST("/api/v1/kitchen/menu-items/{item_id}/availability", { params: { path: { item_id: id } }, body: { available } })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kitchen-menu"] }),
  });
  const items = (menu.data?.data ?? []).filter((i) => !q || i.name.toLowerCase().includes(q.toLowerCase()));
  const soldOut = (menu.data?.data ?? []).filter((i) => !i.is_available).length;
  let category = "";
  return (
    <Dialog
      open={open}
      onClose={onClose}
      size="lg"
      title="Sold out"
      description="Tap a dish when you run out of it; guests stop seeing it as available straight away. Tap again when it is back."
    >
      <div className="mb-3 flex items-center gap-3">
        <Input type="search" aria-label="Find a dish" placeholder="Find a dish" value={q} onChange={(e) => setQ(e.target.value)} />
        <Badge tone={soldOut ? "crit" : "good"} className="whitespace-nowrap text-sm">
          {soldOut} sold out
        </Badge>
      </div>
      {toggle.error ? <ErrorNotice error={toggle.error} className="mb-3" /> : null}
      {menu.isLoading ? (
        <Spinner className="m-6 size-8 text-muted" />
      ) : (
        <ul className="flex max-h-[60vh] flex-col gap-2 overflow-y-auto">
          {items.map((i) => {
            const header = i.category !== category ? (category = i.category) : null;
            return (
              <li key={i.id}>
                {header ? <p className="mt-2 mb-1 text-sm font-semibold text-muted">{header}</p> : null}
                <Button
                  size="lg"
                  className="w-full justify-between"
                  variant={i.is_available ? "secondary" : "danger"}
                  aria-pressed={!i.is_available}
                  disabled={toggle.isPending}
                  onClick={() => needCook(() => toggle.mutate({ id: i.id, available: !i.is_available }))}
                >
                  <span className="truncate">{i.name}</span>
                  <span>{i.is_available ? "Available" : "Sold out"}</span>
                </Button>
              </li>
            );
          })}
        </ul>
      )}
    </Dialog>
  );
}
