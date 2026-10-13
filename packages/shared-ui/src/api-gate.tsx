"use client";

import { type ReactNode, useEffect, useState } from "react";

/**
 * Holds the app back until its API address is chosen (DECISIONS D81). When the app has a
 * single address (`needed` false) it renders straight away, as before.
 */
export function ApiGate({ ready, needed, children }: { ready: Promise<unknown>; needed: boolean; children: ReactNode }) {
  const [done, setDone] = useState(!needed);
  useEffect(() => {
    if (!needed) return;
    let live = true;
    void ready.finally(() => {
      if (live) setDone(true);
    });
    return () => {
      live = false;
    };
  }, [ready, needed]);
  return done ? <>{children}</> : null;
}
