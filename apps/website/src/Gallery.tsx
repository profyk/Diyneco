"use client";

import { cn } from "@diyneco/shared-ui";
import { useCallback, useEffect, useMemo, useState } from "react";

// Photos of hotels using Diyneco, by area (D91), with a keyboard-friendly full-screen viewer.

export const AREAS: Record<string, string> = {
  rooms: "Rooms",
  reception: "Reception",
  kitchen: "Kitchen",
  restaurant: "Restaurant",
  outside: "Outside",
  pool: "Pool",
  spa: "Spa",
  conference: "Conference",
  events: "Events",
  other: "Other",
};

export interface Photo {
  url: string;
  srcSet?: string;
  alt: string;
  width: number;
  height: number;
  caption?: string | null;
  category: string;
}

export function GalleryGrid({ photos, showFilters }: { photos: Photo[]; showFilters: boolean }) {
  const [area, setArea] = useState("all");
  const [open, setOpen] = useState<number | null>(null);
  const areas = useMemo(() => Object.keys(AREAS).filter((a) => photos.some((p) => p.category === a)), [photos]);
  const shown = useMemo(() => (area === "all" ? photos : photos.filter((p) => p.category === area)), [photos, area]);
  const move = useCallback((d: number) => setOpen((i) => (i === null ? i : (i + d + shown.length) % shown.length)), [shown.length]);

  useEffect(() => {
    if (open === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(null);
      if (e.key === "ArrowRight") move(1);
      if (e.key === "ArrowLeft") move(-1);
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, move]);

  const current = open !== null ? shown[open] : undefined;
  return (
    <div>
      {showFilters && areas.length > 1 ? (
        <div role="tablist" aria-label="Areas" className="mb-6 flex flex-wrap justify-center gap-2">
          {["all", ...areas].map((a) => (
            <button
              key={a}
              type="button"
              role="tab"
              aria-selected={area === a}
              onClick={() => setArea(a)}
              className={cn(
                "rounded-full px-4 py-1.5 text-sm font-medium transition",
                area === a ? "bg-brand text-on-brand" : "border border-line bg-surface text-ink hover:bg-surface-2",
              )}
            >
              {a === "all" ? "All" : AREAS[a]}
            </button>
          ))}
        </div>
      ) : null}
      <ul className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3">
        {shown.map((p, i) => (
          <li key={p.url + i}>
            <button type="button" onClick={() => setOpen(i)} className="group relative block w-full overflow-hidden rounded-xl bg-surface-2" aria-label={`Open: ${p.caption ?? p.alt}`}>
              <img
                src={p.url}
                srcSet={p.srcSet}
                sizes="(min-width: 768px) 33vw, 50vw"
                alt={p.alt}
                width={p.width}
                height={p.height}
                loading="lazy"
                className="aspect-[4/3] w-full object-cover transition duration-300 group-hover:scale-105"
              />
              {p.caption ? (
                <span className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent px-3 pb-2 pt-8 text-left text-sm text-white">
                  {p.caption}
                </span>
              ) : null}
            </button>
          </li>
        ))}
      </ul>
      {current ? (
        <div role="dialog" aria-modal="true" aria-label={current.caption ?? current.alt} className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4" onClick={() => setOpen(null)}>
          <figure className="max-h-full max-w-6xl" onClick={(e) => e.stopPropagation()}>
            <img src={current.url} srcSet={current.srcSet} sizes="100vw" alt={current.alt} className="max-h-[80vh] w-auto rounded-lg object-contain" />
            <figcaption className="mt-3 flex items-center justify-between gap-4 text-sm text-white/90">
              <span>
                {current.caption ?? current.alt}
                <span className="ml-2 text-white/60">{AREAS[current.category]}</span>
              </span>
              <span className="text-white/60">
                {(open ?? 0) + 1} / {shown.length}
              </span>
            </figcaption>
          </figure>
          {shown.length > 1 ? (
            <>
              <button type="button" aria-label="Previous photo" onClick={(e) => { e.stopPropagation(); move(-1); }} className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-white/15 px-3 py-2 text-2xl text-white hover:bg-white/25">
                ‹
              </button>
              <button type="button" aria-label="Next photo" onClick={(e) => { e.stopPropagation(); move(1); }} className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-white/15 px-3 py-2 text-2xl text-white hover:bg-white/25">
                ›
              </button>
            </>
          ) : null}
          <button type="button" aria-label="Close" onClick={() => setOpen(null)} className="absolute right-4 top-4 rounded-full bg-white/15 px-3 py-1.5 text-white hover:bg-white/25">
            ✕
          </button>
        </div>
      ) : null}
    </div>
  );
}
