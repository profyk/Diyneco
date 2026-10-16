"use client";

import { type ComponentType, type ReactNode, useEffect, useRef, useState } from "react";

import { Icon, type IconName } from "./icons";
import { cn } from "./primitives";
import { ThemeSwitch } from "./theme";

// The frame of the Merchant app and the Admin panel: a dark sidebar that scrolls on its own,
// a top bar that stays put, and the page, which scrolls on its own too. On small screens the
// sidebar becomes a drawer; on large screens it can be narrowed to icons (remembered).

export interface NavItem {
  href: string;
  label: string;
  icon: IconName;
  /** A small count or marker after the label (for example waiting requests). */
  badge?: ReactNode;
}

export interface NavGroup {
  title?: string;
  items: NavItem[];
}

type LinkLike = ComponentType<{
  href: string;
  className?: string;
  onClick?: () => void;
  title?: string;
  "aria-current"?: "page";
  children: ReactNode;
}>;

const COLLAPSE_KEY = "diyneco.nav.collapsed";

function isActive(href: string, pathname: string): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return ((parts[0]?.[0] ?? "") + (parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? "") : "")).toUpperCase() || "?";
}

export function AppShell({
  product,
  context,
  groups,
  pathname,
  link: Link,
  user,
  userLinks,
  onSignOut,
  topbar,
  status,
  banner,
  children,
}: {
  /** Shown after the logo, e.g. "Admin". */
  product?: string;
  /** Under the logo: the hotel, a hotel switcher or a short line. */
  context?: ReactNode;
  groups: NavGroup[];
  pathname: string;
  link: LinkLike;
  user: { name: string; detail?: string };
  /** Extra links in the user menu, e.g. My account. */
  userLinks?: { href: string; label: string }[];
  onSignOut: () => void;
  /** Left side of the top bar, e.g. search. */
  topbar?: ReactNode;
  /** Right side of the top bar before the theme switch, e.g. the live badge. */
  status?: ReactNode;
  /** A full-width notice under the top bar. */
  banner?: ReactNode;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const main = useRef<HTMLElement>(null);

  useEffect(() => {
    try {
      setCollapsed(localStorage.getItem(COLLAPSE_KEY) === "1");
    } catch {
      /* not remembered */
    }
  }, []);

  // The page scrolls inside <main>, so a new page starts at its top and the drawer closes.
  useEffect(() => {
    main.current?.scrollTo({ top: 0 });
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const toggleCollapsed = () => {
    const next = !collapsed;
    setCollapsed(next);
    try {
      localStorage.setItem(COLLAPSE_KEY, next ? "1" : "0");
    } catch {
      /* not remembered */
    }
  };

  const narrow = collapsed && !open;

  return (
    <div className="flex h-dvh overflow-hidden bg-bg">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-md focus:bg-surface focus:px-3 focus:py-2">
        Skip to content
      </a>
      <aside
        aria-label="Sidebar"
        className={cn(
          "dy-sidebar fixed inset-y-0 left-0 z-40 flex h-dvh shrink-0 flex-col text-[var(--dy-sidebar-ink)] shadow-2xl transition-[transform,width] duration-200 lg:static lg:translate-x-0 lg:shadow-none",
          open ? "translate-x-0" : "-translate-x-full",
          narrow ? "w-[76px]" : "w-72",
        )}
      >
        <div className={cn("flex shrink-0 items-center gap-3 px-5 pb-4 pt-5", narrow && "justify-center px-0")}>
          <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#1e7fd8] to-[#2cc9c0] font-display text-lg font-bold text-white shadow-lg shadow-black/20">
            D
          </span>
          {narrow ? null : (
            <span className="min-w-0 font-display text-lg font-semibold tracking-tight text-white">
              Diyneco
              {product ? <span className="ml-1.5 font-sans text-sm font-medium text-[var(--dy-sidebar-muted)]">{product}</span> : null}
            </span>
          )}
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
            className="ml-auto flex size-9 items-center justify-center rounded-lg text-[var(--dy-sidebar-muted)] hover:bg-white/10 hover:text-white lg:hidden"
          >
            <Icon name="close" />
          </button>
        </div>
        {context && !narrow ? <div className="shrink-0 px-4 pb-3">{context}</div> : null}
        <nav aria-label="Main" className="dy-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 pb-4">
          {groups.map((g, gi) =>
            g.items.length ? (
              <div key={g.title ?? gi} className="mt-3 first:mt-0">
                {g.title && !narrow ? (
                  <p className="px-3 pb-1.5 pt-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--dy-sidebar-muted)]">
                    {g.title}
                  </p>
                ) : g.title ? (
                  <div className="mx-3 my-2 border-t border-white/10" aria-hidden />
                ) : null}
                <ul className="flex flex-col gap-0.5">
                  {g.items.map((n) => {
                    const active = isActive(n.href, pathname);
                    return (
                      <li key={n.href}>
                        <Link
                          href={n.href}
                          onClick={() => setOpen(false)}
                          aria-current={active ? "page" : undefined}
                          title={narrow ? n.label : undefined}
                          className={cn(
                            "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                            narrow && "justify-center px-0",
                            active
                              ? "bg-white/[0.12] text-white shadow-inner shadow-white/5"
                              : "text-[var(--dy-sidebar-ink)] hover:bg-white/[0.06] hover:text-white",
                          )}
                        >
                          {active ? <span className="absolute inset-y-2 left-0 w-1 rounded-r-full bg-[#2cc9c0]" aria-hidden /> : null}
                          <Icon name={n.icon} className={cn("size-[18px] shrink-0", active ? "text-[#5fe0d8]" : "opacity-80 group-hover:opacity-100")} />
                          {narrow ? <span className="sr-only">{n.label}</span> : <span className="min-w-0 flex-1 truncate">{n.label}</span>}
                          {n.badge && !narrow ? <span className="shrink-0">{n.badge}</span> : null}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ) : null,
          )}
        </nav>
        <div className="shrink-0 border-t border-white/10 p-3">
          <div className={cn("flex items-center gap-3 rounded-xl p-2", narrow && "justify-center p-0")}>
            <span
              className="flex size-9 shrink-0 items-center justify-center rounded-full bg-white/10 text-sm font-semibold text-white ring-1 ring-white/15"
              title={narrow ? user.name : undefined}
            >
              {initials(user.name)}
            </span>
            {narrow ? null : (
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-white">{user.name}</p>
                {user.detail ? <p className="truncate text-xs text-[var(--dy-sidebar-muted)]">{user.detail}</p> : null}
              </div>
            )}
          </div>
          <div className={cn("mt-1 flex flex-wrap items-center gap-1", narrow && "flex-col")}>
            {narrow
              ? null
              : userLinks?.map((l) => (
                  <Link key={l.href} href={l.href} onClick={() => setOpen(false)} className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-[var(--dy-sidebar-ink)] hover:bg-white/[0.06] hover:text-white">
                    {l.label}
                  </Link>
                ))}
            <button
              type="button"
              onClick={onSignOut}
              title="Sign out"
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-[var(--dy-sidebar-ink)] hover:bg-white/[0.06] hover:text-white",
                narrow ? "" : "ml-auto",
              )}
            >
              <Icon name="logout" className="size-4" />
              {narrow ? <span className="sr-only">Sign out</span> : "Sign out"}
            </button>
          </div>
          <button
            type="button"
            onClick={toggleCollapsed}
            aria-label={collapsed ? "Widen the menu" : "Narrow the menu"}
            title={collapsed ? "Widen the menu" : "Narrow the menu"}
            className="mt-2 hidden w-full items-center justify-center rounded-lg py-1.5 text-[var(--dy-sidebar-muted)] hover:bg-white/[0.06] hover:text-white lg:flex"
          >
            <Icon name={collapsed ? "chevronRight" : "chevronLeft"} className="size-4" />
          </button>
        </div>
      </aside>
      {open ? <button type="button" aria-label="Close menu" className="fixed inset-0 z-30 bg-[#020817]/60 backdrop-blur-[2px] lg:hidden" onClick={() => setOpen(false)} /> : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="z-20 flex h-16 shrink-0 items-center gap-3 border-b border-line bg-surface/85 px-4 backdrop-blur-md lg:px-8">
          <button
            type="button"
            onClick={() => setOpen(true)}
            aria-label="Open menu"
            className="flex size-10 items-center justify-center rounded-xl text-ink hover:bg-surface-2 lg:hidden"
          >
            <Icon name="menu" />
          </button>
          <div className="min-w-0 flex-1">{topbar}</div>
          <div className="flex shrink-0 items-center gap-2">
            {status}
            <span className="hidden sm:block">
              <ThemeSwitch />
            </span>
          </div>
        </header>
        {banner}
        <main id="main" ref={main} tabIndex={-1} className="dy-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain focus:outline-none">
          <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:py-8 lg:px-8">{children}</div>
          <div className="flex items-center justify-between gap-3 border-t border-line px-4 py-4 text-sm text-muted sm:hidden">
            Theme
            <ThemeSwitch />
          </div>
        </main>
      </div>
    </div>
  );
}
