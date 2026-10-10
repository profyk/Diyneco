"use client";

import { connectRealtime, type RealtimeStatus } from "@diyneco/api-client";
import { Badge, cn, Select, Spinner } from "@diyneco/shared-ui";
import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useEffect, useRef, useState } from "react";

import { EnrolScreen, LoginScreen } from "./auth-screens";
import { API_URL } from "./config";
import { useSession } from "./session";

const NAV: { href: string; label: string; perm?: string; any?: string[] }[] = [
  { href: "/", label: "Today" },
  { href: "/orders", label: "Orders", perm: "orders.read" },
  { href: "/approvals", label: "Approvals", any: ["orders.approve", "folio.adjust.approve"] },
  { href: "/stays", label: "Stays & check-in", perm: "stays.read" },
  { href: "/rooms", label: "Rooms", perm: "rooms.read" },
  { href: "/guests", label: "Guests", perm: "guests.read" },
  { href: "/companies", label: "Companies", perm: "guests.read" },
  { href: "/menu", label: "Menu", perm: "menu.read" },
  { href: "/payments", label: "Payments", perm: "payments.read" },
  { href: "/reports", label: "Reports", perm: "reports.read" },
  { href: "/staff", label: "Staff", perm: "staff.read" },
  { href: "/devices", label: "Devices", perm: "devices.read" },
  { href: "/settings", label: "Settings", perm: "hotel.read" },
];

const PUBLIC = ["/signup", "/forgot-password", "/reset-password", "/invite", "/verify-email"];

/** Public pages render as they are; everything else needs a signed-in session. */
export function Gate({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { state } = useSession();
  if (PUBLIC.some((p) => pathname.startsWith(p))) return <>{children}</>;
  if (state.status === "loading") {
    return (
      <main className="flex min-h-dvh items-center justify-center">
        <Spinner className="size-8 text-muted" />
      </main>
    );
  }
  if (state.status === "signed-out") return <LoginScreen />;
  if (state.status === "mfa-enrol") return <EnrolScreen />;
  return <Shell>{children}</Shell>;
}

function useLiveUpdates(): RealtimeStatus {
  const qc = useQueryClient();
  const { accessToken } = useSession();
  const [status, setStatus] = useState<RealtimeStatus>("connecting");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    const rt = connectRealtime({
      baseUrl: API_URL,
      getToken: accessToken,
      onEvent: () => {
        // Events are notifications; refetch what is on screen, at most every 1.5 s.
        if (timer.current) return;
        timer.current = setTimeout(() => {
          timer.current = null;
          void qc.invalidateQueries();
        }, 1500);
      },
      onStatus: setStatus,
    });
    return () => rt.close();
  }, [accessToken, qc]);
  return status;
}

function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { state, can, switchHotel, signOut } = useSession();
  const live = useLiveUpdates();
  const [menuOpen, setMenuOpen] = useState(false);
  if (state.status !== "signed-in") return null;
  const { me, hotels } = state;
  const nav = NAV.filter((n) => (n.perm ? can(n.perm) : n.any ? n.any.some(can) : true));
  const suspended = me.hotel?.status === "suspended";
  const pending = me.hotel?.status === "pending_approval";

  return (
    <div className="flex min-h-dvh">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 w-64 shrink-0 border-r border-line bg-surface p-4 transition-transform lg:static lg:translate-x-0",
          menuOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="mb-6 px-2">
          <p className="font-display text-lg font-semibold text-brand">Diyneco</p>
          {hotels.length > 1 ? (
            <Select
              aria-label="Hotel"
              className="mt-2"
              value={me.hotel?.id}
              onChange={(e) => void switchHotel(e.target.value)}
            >
              {hotels.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name}
                </option>
              ))}
            </Select>
          ) : (
            <p className="mt-1 truncate text-sm text-muted">{me.hotel?.name}</p>
          )}
        </div>
        <nav className="flex flex-col gap-0.5" aria-label="Main">
          {nav.map((n) => {
            const active = n.href === "/" ? pathname === "/" : pathname.startsWith(n.href);
            return (
              <Link
                key={n.href}
                href={n.href}
                onClick={() => setMenuOpen(false)}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "rounded-lg px-3 py-2 text-sm font-medium transition",
                  active ? "bg-tint text-blue" : "text-ink hover:bg-surface-2",
                )}
              >
                {n.label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-8 border-t border-line px-2 pt-4 text-sm">
          <p className="truncate font-medium text-ink">{me.user?.name}</p>
          <p className="truncate text-xs text-muted">{me.roles.join(", ")}</p>
          <div className="mt-3 flex flex-col items-start gap-1">
            <Link href="/account" className="text-blue hover:underline">
              My account
            </Link>
            <button type="button" className="text-blue hover:underline" onClick={() => void signOut()}>
              Sign out
            </button>
          </div>
        </div>
      </aside>
      {menuOpen ? (
        <button
          type="button"
          aria-label="Close menu"
          className="fixed inset-0 z-20 bg-black/40 lg:hidden"
          onClick={() => setMenuOpen(false)}
        />
      ) : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-line bg-surface/90 px-4 py-3 backdrop-blur lg:px-8">
          <button type="button" className="rounded-md px-2 py-1 text-ink lg:hidden" onClick={() => setMenuOpen(true)}>
            ☰ <span className="sr-only">Menu</span>
          </button>
          <span className="hidden lg:block" />
          <Badge tone={live === "live" ? "good" : live === "connecting" ? "info" : "warn"}>
            {live === "live" ? "Live" : live === "connecting" ? "Connecting…" : "Offline: showing last known data"}
          </Badge>
        </header>
        {suspended ? (
          <div className="bg-crit-bg px-8 py-3 text-sm text-crit">
            This hotel&apos;s account is suspended. You can view everything, but changes are paused. Contact Diyneco.
          </div>
        ) : pending ? (
          <div className="bg-warn-bg px-8 py-3 text-sm text-warn">
            Your hotel is waiting for approval. Set up rooms, staff and the menu now; tablets can take orders once
            Diyneco approves the account.
          </div>
        ) : null}
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
