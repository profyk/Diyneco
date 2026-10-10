"use client";

import { connectRealtime, type RealtimeStatus } from "@diyneco/api-client";
import { Badge, Button, cn, Spinner } from "@diyneco/shared-ui";
import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useEffect, useRef, useState } from "react";

import { EnrolScreen, LoginScreen } from "./auth-screens";
import { API_URL } from "./config";
import { useSession } from "./session";

const NAV: { href: string; label: string; perm: string }[] = [
  { href: "/", label: "Overview", perm: "platform.metrics" },
  { href: "/hotels", label: "Hotels", perm: "platform.tenants.read" },
  { href: "/plans", label: "Plans & billing", perm: "platform.billing.manage" },
  { href: "/flags", label: "Feature flags", perm: "platform.flags.manage" },
  { href: "/health", label: "Health", perm: "platform.metrics" },
];

export function Gate({ children }: { children: ReactNode }) {
  const { state, signOut } = useSession();
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
  return (
    <div className="flex min-h-dvh">
      <aside className="hidden w-60 shrink-0 border-r border-line bg-surface p-4 md:block">
        <p className="mb-6 px-2 font-display text-lg font-semibold text-brand">Diyneco Admin</p>
        <nav className="flex flex-col gap-0.5" aria-label="Main">
          {NAV.filter((n) => can(n.perm)).map((n) => {
            const active = n.href === "/" ? pathname === "/" : pathname.startsWith(n.href);
            return (
              <Link
                key={n.href}
                href={n.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "rounded-lg px-3 py-2 text-sm font-medium",
                  active ? "bg-tint text-blue" : "text-ink hover:bg-surface-2",
                )}
              >
                {n.label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-8 border-t border-line px-2 pt-4 text-sm">
          <p className="font-medium">{state.me.user?.name}</p>
          <p className="text-xs text-muted">{state.me.roles.join(", ")}</p>
          <button type="button" className="mt-3 text-blue hover:underline" onClick={() => void signOut()}>
            Sign out
          </button>
        </div>
      </aside>
      <div className="min-w-0 flex-1">
        <header className="flex items-center justify-between border-b border-line bg-surface px-6 py-3">
          <nav className="flex gap-3 text-sm md:hidden">
            {NAV.filter((n) => can(n.perm)).map((n) => (
              <Link key={n.href} href={n.href} className="text-blue">
                {n.label}
              </Link>
            ))}
          </nav>
          <span className="hidden text-xs text-muted md:block">Aggregates only. Guest data is never shown here.</span>
          <Badge tone={live === "live" ? "good" : "warn"}>{live === "live" ? "Live" : "Connecting…"}</Badge>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
