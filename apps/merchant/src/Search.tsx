"use client";

import { ok } from "@diyneco/api-client";
import { cn } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useDeferredValue, useEffect, useRef, useState } from "react";

import { useSession } from "./session";

type Hit = { key: string; group: string; title: string; detail?: string; href: string };

/**
 * Ctrl+K (or ⌘K) search across screens, rooms, guests in house and guest records. Results come
 * only from endpoints the person may already read; nothing is fetched until they type.
 */
export function Search({ pages }: { pages: { href: string; label: string }[] }) {
  const { api, can } = useSession();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [index, setIndex] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const term = useDeferredValue(q.trim().toLowerCase());

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  useEffect(() => {
    if (open) setTimeout(() => input.current?.focus(), 0);
    else setQ("");
  }, [open]);

  const rooms = useQuery({
    queryKey: ["rooms", "all"],
    queryFn: () => ok(api.GET("/api/v1/rooms", { params: { query: { limit: 200 } } })),
    enabled: open && can("rooms.read"),
  });
  const inHouse = useQuery({
    queryKey: ["stays", "inhouse"],
    queryFn: () => ok(api.GET("/api/v1/stays", { params: { query: { status: "active", limit: 200 } } })),
    enabled: open && can("stays.read"),
  });
  const guests = useQuery({
    queryKey: ["guests", term],
    queryFn: () => ok(api.GET("/api/v1/guests", { params: { query: { q: term, limit: 8 } } })),
    enabled: open && can("guests.read") && term.length >= 2,
  });

  const hits: Hit[] = [];
  if (term) {
    for (const p of pages.filter((x) => x.label.toLowerCase().includes(term)).slice(0, 5)) {
      hits.push({ key: `p${p.href}`, group: "Go to", title: p.label, href: p.href });
    }
    for (const s of (inHouse.data?.data ?? [])
      .filter((s) => s.room.number.toLowerCase().startsWith(term) || s.guest.name.toLowerCase().includes(term))
      .slice(0, 6)) {
      hits.push({
        key: `s${s.id}`,
        group: "In house",
        title: `Room ${s.room.number} · ${s.guest.name}`,
        detail: `until ${s.departure_date}`,
        href: `/stays/${s.id}`,
      });
    }
    for (const r of (rooms.data?.data ?? []).filter((r) => r.number.toLowerCase().startsWith(term)).slice(0, 5)) {
      hits.push({ key: `r${r.id}`, group: "Rooms", title: `Room ${r.number}`, detail: `${r.room_type.name} · ${r.status.replace(/_/g, " ")}`, href: "/rooms" });
    }
    for (const g of guests.data?.data ?? []) {
      if (g.anonymised) continue;
      hits.push({ key: `g${g.id}`, group: "Guests", title: g.name, detail: g.email ?? g.phone ?? undefined, href: `/guests?q=${encodeURIComponent(g.name)}` });
    }
  }
  const go = (h: Hit | undefined) => {
    if (!h) return;
    setOpen(false);
    router.push(h.href);
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex min-w-0 flex-1 items-center gap-2 rounded-lg border border-line bg-surface px-3 py-1.5 text-left text-sm text-muted hover:bg-surface-2 sm:max-w-sm"
      >
        <span aria-hidden>⌕</span>
        <span className="truncate">Search rooms, guests, screens</span>
        <kbd className="ml-auto hidden rounded border border-line px-1.5 text-xs sm:inline">Ctrl K</kbd>
      </button>
      {open ? (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 pt-[12vh]" onClick={() => setOpen(false)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Search"
            className="w-full max-w-xl overflow-hidden rounded-[var(--radius-card)] border border-line bg-surface shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <input
              ref={input}
              type="search"
              aria-label="Search"
              placeholder="Room number, guest name or a screen"
              className="w-full border-b border-line bg-transparent px-4 py-3 text-base text-ink outline-none"
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setIndex(0);
              }}
              onKeyDown={(e) => {
                if (e.key === "ArrowDown") {
                  e.preventDefault();
                  setIndex((i) => Math.min(i + 1, hits.length - 1));
                } else if (e.key === "ArrowUp") {
                  e.preventDefault();
                  setIndex((i) => Math.max(i - 1, 0));
                } else if (e.key === "Enter") {
                  go(hits[index]);
                }
              }}
            />
            <ul className="max-h-[50vh] overflow-auto py-1" role="listbox" aria-label="Results">
              {!term ? (
                <li className="px-4 py-3 text-sm text-muted">Type a room number, a guest&apos;s name or a screen such as Housekeeping.</li>
              ) : hits.length === 0 ? (
                <li className="px-4 py-3 text-sm text-muted">{guests.isFetching ? "Searching…" : "Nothing found."}</li>
              ) : (
                hits.map((h, i) => (
                  <li key={h.key} role="option" aria-selected={i === index}>
                    <button
                      type="button"
                      onMouseEnter={() => setIndex(i)}
                      onClick={() => go(h)}
                      className={cn("flex w-full items-baseline gap-3 px-4 py-2 text-left", i === index ? "bg-tint" : "")}
                    >
                      <span className="w-20 shrink-0 text-xs text-muted">{h.group}</span>
                      <span className="truncate font-medium text-ink">{h.title}</span>
                      {h.detail ? <span className="ml-auto truncate text-xs text-muted">{h.detail}</span> : null}
                    </button>
                  </li>
                ))
              )}
            </ul>
          </div>
        </div>
      ) : null}
    </>
  );
}
