"use client";

import { Badge, useToast } from "@diyneco/shared-ui";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const ORDER_TONES: Record<string, "neutral" | "info" | "good" | "warn" | "crit" | "teal"> = {
  PENDING_APPROVAL: "warn",
  NEW: "info",
  ACCEPTED: "info",
  PREPARING: "teal",
  READY: "good",
  ASSIGNED: "teal",
  PICKED_UP: "teal",
  DELIVERED: "good",
  CLOSED: "neutral",
  DECLINED: "crit",
  CANCELLED: "crit",
};

const LABELS: Record<string, string> = {
  PENDING_APPROVAL: "Needs approval",
  PICKED_UP: "On the way",
  checkout_pending: "Checking out",
  checked_out: "Checked out",
  out_of_service: "Out of service",
  reset_required: "Reset pending",
};

export function label(status: string): string {
  return LABELS[status] ?? status.charAt(0).toUpperCase() + status.slice(1).toLowerCase().replace(/_/g, " ");
}

export function OrderStatus({ status }: { status: string }) {
  return <Badge tone={ORDER_TONES[status] ?? "neutral"}>{label(status)}</Badge>;
}

const STAY_TONES: Record<string, "neutral" | "info" | "good" | "warn" | "crit"> = {
  reserved: "info",
  active: "good",
  checkout_pending: "warn",
  checked_out: "neutral",
  cancelled: "crit",
};

export function StayStatus({ status }: { status: string }) {
  return <Badge tone={STAY_TONES[status] ?? "neutral"}>{status === "active" ? "In house" : label(status)}</Badge>;
}

const ROOM_TONES: Record<string, "neutral" | "info" | "good" | "warn" | "crit" | "teal"> = {
  available: "good",
  occupied: "info",
  reserved: "teal",
  cleaning: "warn",
  maintenance: "warn",
  out_of_service: "crit",
};

export function RoomStatus({ status }: { status: string }) {
  return <Badge tone={ROOM_TONES[status] ?? "neutral"}>{label(status)}</Badge>;
}

/** Local calendar date as YYYY-MM-DD (hotels are in South Africa, like their staff). */
export function isoDay(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** A mutation that refreshes everything on success and reports the outcome. */
export function useAction<TArgs, TResult>(
  fn: (args: TArgs) => Promise<TResult>,
  { success, onDone }: { success?: string | ((r: TResult) => string); onDone?: (r: TResult) => void } = {},
) {
  const qc = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: fn,
    onSuccess: async (result) => {
      await qc.invalidateQueries();
      if (success) toast("good", typeof success === "function" ? success(result) : success);
      onDone?.(result);
    },
  });
}
