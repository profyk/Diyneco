"use client";

import { ApiError, newIdempotencyKey } from "@diyneco/api-client";
import { Button, ErrorNotice } from "@diyneco/shared-ui";
import { useState } from "react";

import { API_URL, APP_VERSION } from "./config";
import { credential } from "./device";

const KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", "⌫"];

/** First start: a manager creates a 6-digit pairing code in the Merchant app (Devices). */
export function PairScreen({ onPaired }: { onPaired: (stations: string[]) => void }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const press = (k: string) => {
    setError(null);
    if (k === "⌫") setCode((c) => c.slice(0, -1));
    else if (k && code.length < 6) setCode((c) => c + k);
  };

  const pair = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/devices/pair`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": newIdempotencyKey() },
        body: JSON.stringify({
          code,
          device_info: { os: navigator.platform || "browser", app_version: APP_VERSION },
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new ApiError(res.status, body.error);
      if (body.kind !== "kitchen") {
        throw new ApiError(422, {
          code: "PAIRING_INVALID",
          message: "That code is for a guest tablet. Create a kitchen display code instead.",
          request_id: null,
          details: {},
        });
      }
      credential.set(body.device_credential);
      onPaired((body.stations as { name: string }[]).map((s) => s.name));
    } catch (err) {
      setError(err);
      setCode("");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="kds flex min-h-dvh items-center justify-center bg-bg p-6">
      <div className="w-full max-w-md text-center">
        <p className="font-display text-sm font-semibold uppercase tracking-[0.2em] text-muted">Diyneco Kitchen</p>
        <h1 className="mt-2 font-display text-3xl font-semibold text-ink">Pair this display</h1>
        <p className="mt-2 text-muted">
          In the Merchant app, open Devices and add a kitchen display. Enter the 6-digit code it shows.
        </p>
        <div className="mt-8 flex justify-center gap-2" aria-label="Pairing code" aria-live="polite">
          {Array.from({ length: 6 }, (_, i) => (
            <span
              key={i}
              className="flex h-16 w-12 items-center justify-center rounded-xl border-2 border-line bg-surface font-mono text-3xl text-ink"
            >
              {code[i] ?? ""}
            </span>
          ))}
        </div>
        {error ? <ErrorNotice error={error} className="mt-4 text-left" /> : null}
        <div className="mt-6 grid grid-cols-3 gap-3">
          {KEYS.map((k, i) =>
            k ? (
              <Button key={i} variant="secondary" size="xl" onClick={() => press(k)} aria-label={k === "⌫" ? "Delete" : k}>
                {k}
              </Button>
            ) : (
              <span key={i} />
            ),
          )}
        </div>
        <Button size="xl" className="mt-6 w-full" disabled={code.length !== 6} loading={busy} onClick={pair}>
          Pair display
        </Button>
      </div>
    </main>
  );
}
