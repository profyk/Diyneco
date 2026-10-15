"use client";

import { cn } from "@diyneco/shared-ui";
import { usePathname } from "next/navigation";
import { useState } from "react";

export function SiteHeader({
  siteName,
  links,
  merchantUrl,
}: {
  siteName: string;
  links: { label: string; href: string }[];
  merchantUrl: string;
}) {
  const [open, setOpen] = useState(false);
  const path = usePathname();
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-surface/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <a href="/" className="flex items-center gap-2" aria-label={`${siteName} home`}>
          <img src="/brand/diyneco-logo.png" alt="" width={120} height={80} className="h-9 w-auto" />
          <span className="font-display text-lg font-semibold text-brand">{siteName}</span>
        </a>
        <nav className="hidden items-center gap-6 md:flex" aria-label="Main">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              aria-current={path === l.href ? "page" : undefined}
              className={cn("text-sm font-medium", path === l.href ? "text-blue" : "text-ink hover:text-blue")}
            >
              {l.label}
            </a>
          ))}
        </nav>
        <div className="hidden items-center gap-3 md:flex">
          <a href={`${merchantUrl}/`} className="text-sm font-medium text-ink hover:text-blue">
            Sign in
          </a>
          <a href={`${merchantUrl}/signup`} className="inline-flex h-10 items-center rounded-[10px] bg-brand px-4 text-sm font-medium text-on-brand hover:opacity-90">
            Start free trial
          </a>
        </div>
        <button type="button" className="rounded-md px-2 py-1 text-ink md:hidden" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
          {open ? "✕" : "☰"} <span className="sr-only">Menu</span>
        </button>
      </div>
      {open ? (
        <nav className="flex flex-col gap-1 border-t border-line px-4 py-3 md:hidden" aria-label="Main">
          {links.map((l) => (
            <a key={l.href} href={l.href} className="rounded-lg px-3 py-2 text-ink hover:bg-surface-2">
              {l.label}
            </a>
          ))}
          <a href={`${merchantUrl}/`} className="rounded-lg px-3 py-2 text-ink hover:bg-surface-2">
            Sign in
          </a>
          <a href={`${merchantUrl}/signup`} className="mt-1 rounded-[10px] bg-brand px-3 py-2.5 text-center font-medium text-on-brand">
            Start free trial
          </a>
        </nav>
      ) : null}
    </header>
  );
}
