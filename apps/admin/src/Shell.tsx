"use client";

import { connectRealtime, type RealtimeStatus } from "@diyneco/api-client";
import { AppShell, Badge, Button, cn, Icon, type IconName, type NavGroup, Spinner } from "@diyneco/shared-ui";
import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useEffect, useRef, useState } from "react";

import { EnrolScreen, LoginScreen } from "./auth-screens";
import { API_URL } from "./config";
import { useSession } from "./session";

type Entry = { href: string; label: string; icon: IconName; perm: string };

const NAV: { title?: string; items: Entry[] }[] = [
  {
    items: [
      { href: "/", label: "Overview", icon: "home", perm: "platform.metrics" },
      { href: "/insights", label: "Insights", icon: "trend", perm: "platform.metrics" },
    ],
  },
  {
    title: "Customers",
    items: [
      { href: "/hotels", label: "Hotels", icon: "building", perm: "platform.tenants.read" },
      { href: "/owners", label: "Owners", icon: "users", perm: "platform.tenants.read" },
    ],
  },
  {
    title: "Revenue",
    items: [
      { href: "/plans", label: "Plans & Pricing", icon: "tag", perm: "platform.billing.manage" },
      { href: "/billing", label: "Billing & Invoices", icon: "receipt", perm: "platform.billing.manage" },
    ],
  },
  {
    title: "Growth",
    items: [
      { href: "/website", label: "Website", icon: "layout", perm: "platform.website.manage" },
      { href: "/countries", label: "Countries", icon: "globe", perm: "platform.countries.manage" },
    ],
  },
  {
    title: "Platform",
    items: [
      { href: "/health", label: "Health", icon: "pulse", perm: "platform.metrics" },
      { href: "/flags", label: "Feature flags", icon: "flag", perm: "platform.flags.manage" },
      { href: "/legal", label: "Legal documents", icon: "file", perm: "platform.legal.manage" },
      { href: "/company", label: "Company & tax", icon: "briefcase", perm: "platform.company.manage" },
      { href: "/staff", label: "Diyneco staff", icon: "shield", perm: "platform.staff.manage" },
    ],
  },
];

const ROLE_NAMES: Record<string, string> = {
  platform_super_admin: "Super Admin",
  platform_support: "Support",
  platform_website_editor: "Website editor",
};

export function Gate({ children }: { children: ReactNode }) {
  const { state, signOut } = useSession();
  const pathname = usePathname();
  // An invited person has no account to sign in with yet (D71).
  if (pathname === "/accept-invite") return <>{children}</>;
  if (state.status === "loading") {
    return (
      <main className="flex min-h-dvh items-center justify-center">
        <Spinner className="size-8 text-muted" />
      </main>
    );
  }
  if (state.status === "signed-out") return <LoginScreen />;
  if (state.status === "mfa-enrol") return <EnrolScreen />;
  if (state.me.kind !== "platform") {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6 text-center">
        <h1 className="font-display text-2xl font-semibold">This is the Diyneco staff panel</h1>
        <p className="max-w-md text-muted">Hotel accounts use the Merchant app.</p>
        <Button onClick={() => void signOut()}>Sign out</Button>
      </main>
    );
  }
  return <Shell>{children}</Shell>;
}

function useLive(): RealtimeStatus {
  const qc = useQueryClient();
  const { accessToken } = useSession();
  const [status, setStatus] = useState<RealtimeStatus>("connecting");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    const rt = connectRealtime({
      baseUrl: API_URL,
      getToken: accessToken,
      onEvent: () => {
        if (timer.current) return;
        timer.current = setTimeout(() => {
          timer.current = null;
          void qc.invalidateQueries();
        }, 2000);
      },
      onStatus: setStatus,
    });
    return () => rt.close();
  }, [accessToken, qc]);
  return status;
}

function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { state, can, signOut } = useSession();
  const live = useLive();
  if (state.status !== "signed-in") return null;
  const groups: NavGroup[] = NAV.map((g) => ({
    title: g.title,
    items: g.items.filter((n) => can(n.perm)).map(({ href, label, icon }) => ({ href, label, icon })),
  }));
  return (
    <AppShell
      product="Admin"
      context={
        <p className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.05] px-3 py-2 text-xs text-[var(--dy-sidebar-ink)]">
          <Icon name="shield" className="size-4 shrink-0 text-[#5fe0d8]" />
          Aggregates only. Guest data is never shown here.
        </p>
      }
      groups={groups}
      pathname={pathname}
      link={Link}
      user={{ name: state.me.user?.name ?? "", detail: state.me.roles.map((r) => ROLE_NAMES[r] ?? r).join(", ") }}
      onSignOut={() => void signOut()}
      topbar={<p className="hidden truncate font-display text-sm font-semibold text-ink sm:block">Diyneco platform</p>}
      status={
        <Badge tone={live === "live" ? "good" : "warn"} className="gap-1.5">
          <span className={cn("size-1.5 rounded-full", live === "live" ? "animate-pulse bg-good" : "bg-warn")} aria-hidden />
          {live === "live" ? "Live" : "Connecting…"}
        </Badge>
      }
    >
      {children}
    </AppShell>
  );
}
