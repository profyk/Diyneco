"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

/** A cookieless page view (D83): path, language and referring site only; nothing about the visitor. */
export function PageView({ locale, enabled }: { locale: string; enabled: boolean }) {
  const path = usePathname();
  useEffect(() => {
    if (!enabled || navigator.doNotTrack === "1") return;
    const body = JSON.stringify({ path, locale, referrer: document.referrer.slice(0, 500) });
    void fetch(`${API}/api/v1/site/views`, { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true }).catch(
      () => undefined,
    );
  }, [path, locale, enabled]);
  return null;
}
