"use client";

import { connectRealtime, ok, type RealtimeStatus } from "@diyneco/api-client";
import { AppShell, Badge, cn, type IconName, type NavGroup, Spinner, useToast } from "@diyneco/shared-ui";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useEffect, useRef, useState } from "react";

import { EnrolScreen, LoginScreen } from "./auth-screens";
import { LegalGate } from "./Legal";
import { API_URL } from "./config";
import { Search } from "./Search";
import { useSession } from "./session";

type Entry = { href: string; label: string; icon: IconName; perm?: string; any?: string[]; owner?: boolean };

const NAV: { title?: string; items: Entry[] }[] = [
  {
    items: [
      { href: "/properties", label: "All properties", icon: "layers", owner: true },
      { href: "/", label: "Today", icon: "home" },
    ],
  },
  {
    title: "Service",
    items: [
      { href: "/orders", label: "Orders", icon: "receipt", perm: "orders.read" },
      { href: "/dispatch", label: "Dispatch", icon: "truck", perm: "deliveries.manage" },
      { href: "/requests", label: "Guest requests", icon: "bell", perm: "requests.view" },
      { href: "/approvals", label: "Approvals", icon: "clipboard", any: ["orders.approve", "folio.adjust.approve"] },
    ],
  },
  {
    title: "Front office",
    items: [
      { href: "/stays", label: "Stays & check-in", icon: "calendar", perm: "stays.read" },
      { href: "/rack", label: "Room rack", icon: "grid", perm: "stays.read" },
      { href: "/housekeeping", label: "Housekeeping", icon: "sparkle", perm: "rooms.read" },
      { href: "/rooms", label: "Rooms", icon: "door", perm: "rooms.read" },
      { href: "/guests", label: "Guests", icon: "user", perm: "guests.read" },
      { href: "/companies", label: "Companies", icon: "briefcase", perm: "guests.read" },
    ],
  },
  {
    title: "Food & money",
    items: [
      { href: "/menu", label: "Menu", icon: "utensils", perm: "menu.read" },
      { href: "/payments", label: "Payments", icon: "card", perm: "payments.read" },
      { href: "/reports", label: "Reports", icon: "chart", perm: "reports.read" },
    ],
  },
  {
    title: "Setup",
    items: [
      { href: "/staff", label: "Staff", icon: "users", perm: "staff.read" },
      { href: "/devices", label: "Devices", icon: "tablet", perm: "devices.read" },
      { href: "/settings", label: "Settings", icon: "settings", perm: "hotel.read" },
    ],
  },
];

const ROLE_NAMES: Record<string, string> = {
  hotel_owner: "Owner",
  hotel_admin: "Hotel admin",
  general_manager: "General manager",
  reception_manager: "Reception manager",
  receptionist: "Reception",
  finance_manager: "Finance",
  kitchen_manager: "Kitchen manager",
  kitchen_staff: "Kitchen",
  room_service_manager: "Room-service manager",
  room_service_staff: "Room service",
};

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
  return (
    <LegalGate>
      <Shell>{children}</Shell>
    </LegalGate>
  );
}

function useLiveUpdates(): RealtimeStatus {
  const qc = useQueryClient();
  const { accessToken } = useSession();
  const [status, setStatus] = useState<RealtimeStatus>("connecting");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const toast = useToast();
  const { can } = useSession();
  const canReports = can("reports.read");
  useEffect(() => {
    const rt = connectRealtime({
      baseUrl: API_URL,
      getToken: accessToken,
      onEvent: (e) => {
        // A guest unhappy enough to give 1 or 2 stars reaches managers at once (D98).
        if (e.type === "FEEDBACK_RECEIVED" && e.data.low === true && canReports) {
          toast("crit", `Room ${String(e.data.room)} gave ${String(e.data.rating)} star${e.data.rating === 1 ? "" : "s"}. See Reports > Guest feedback.`);
        }
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
  }, [accessToken, qc, toast, canReports]);
  return status;
}

function LiveBadge({ live }: { live: RealtimeStatus }) {
  return (
    <Badge tone={live === "live" ? "good" : live === "connecting" ? "info" : "warn"} className="gap-1.5">
      <span className={cn("size-1.5 rounded-full", live === "live" ? "animate-pulse bg-good" : live === "connecting" ? "bg-blue" : "bg-warn")} aria-hidden />
      {live === "live" ? "Live" : live === "connecting" ? "Connecting…" : <span title="Showing the last known data">Offline</span>}
    </Badge>
  );
}

function CountBadge({ n }: { n: number }) {
  return n > 0 ? (
    <span className="min-w-5 rounded-full bg-[#2cc9c0] px-1.5 py-0.5 text-center text-[11px] font-bold leading-none text-[#04293a]">{n > 99 ? "99+" : n}</span>
  ) : null;
}

function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { api, state, can, switchHotel, signOut } = useSession();
  const live = useLiveUpdates();
  // Waiting guest requests in the menu; live events refresh it with everything else.
  const requests = useQuery({
    queryKey: ["requests", "open", "count"],
    queryFn: () => ok(api.GET("/api/v1/requests", { params: { query: { scope: "open", limit: 1 } } })),
    enabled: state.status === "signed-in" && can("requests.view"),
    refetchInterval: 60_000,
  });
  if (state.status !== "signed-in") return null;
  const { me, hotels } = state;
  // Owners and the managers they put over several properties see them side by side (D86, D90).
  const PORTFOLIO = ["hotel_owner", "hotel_admin", "general_manager"];
  const portfolio = me.roles.some((r) => PORTFOLIO.includes(r)) || hotels.some((h) => h.roles.some((r) => PORTFOLIO.includes(r)));
  const owner = me.roles.includes("hotel_owner") || hotels.some((h) => h.roles.includes("hotel_owner"));
  const allowed = (n: Entry) => (n.owner ? portfolio : n.perm ? can(n.perm) : n.any ? n.any.some(can) : true);
  const waiting = requests.data?.summary.open ?? 0;
  const groups: NavGroup[] = NAV.map((g) => ({
    title: g.title,
    items: g.items.filter(allowed).map((n) => ({
      href: n.href,
      label: n.label,
      icon: n.icon,
      badge: n.href === "/requests" ? <CountBadge n={waiting} /> : undefined,
    })),
  }));
  const pages = groups.flatMap((g) => g.items);
  const suspended = me.hotel?.status === "suspended";
  const pending = me.hotel?.status === "pending_approval";

  const context =
    hotels.length > 1 ? (
      <label className="block">
        <span className="sr-only">Property</span>
        <select
          value={me.hotel?.id}
          onChange={(e) => void switchHotel(e.target.value)}
          className="w-full truncate rounded-xl border border-white/15 bg-white/[0.07] px-3 py-2 text-sm font-medium text-white focus:border-[#2cc9c0] focus:outline-none [&>option]:text-ink"
        >
          {hotels.map((h) => (
            <option key={h.id} value={h.id}>
              {h.name}
            </option>
          ))}
        </select>
      </label>
    ) : (
      <div className="flex items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/[0.05] px-3 py-2">
        <p className="truncate text-sm font-medium text-white">{me.hotel?.name}</p>
        {owner ? (
          <Link href="/properties/new" className="shrink-0 text-xs font-medium text-[#5fe0d8] hover:underline">
            + Add
          </Link>
        ) : null}
      </div>
    );

  return (
    <AppShell
      context={context}
      groups={groups}
      pathname={pathname}
      link={Link}
      user={{ name: me.user?.name ?? "", detail: me.roles.map((r) => ROLE_NAMES[r] ?? r).join(", ") }}
      userLinks={[{ href: "/account", label: "My account" }]}
      onSignOut={() => void signOut()}
      topbar={<Search pages={pages} />}
      status={<LiveBadge live={live} />}
      banner={
        suspended ? (
          <div className="shrink-0 bg-crit-bg px-4 py-2.5 text-sm text-crit lg:px-8">
            This hotel&apos;s account is suspended. You can view everything, but changes are paused. Contact Diyneco.
          </div>
        ) : pending ? (
          <div className="shrink-0 bg-warn-bg px-4 py-2.5 text-sm text-warn lg:px-8">
            Your hotel is waiting for approval. Set up rooms, staff and the menu now; tablets can take orders once Diyneco approves the account.
          </div>
        ) : null
      }
    >
      {children}
    </AppShell>
  );
}
