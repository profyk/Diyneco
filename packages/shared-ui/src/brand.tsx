"use client";

import { type FormEvent, useEffect, useState } from "react";

import { ErrorNotice } from "./overlays";
import { Button, cn, Field, Input } from "./primitives";

/**
 * The Diyneco logo (brand/logo-draft.png, trimmed and resized into each app's
 * public/brand/). It sits on its own white tile so the navy wordmark stays readable in
 * dark and kitchen high-visibility themes. Replace with the SVG master when it exists.
 */
export function BrandLogo({ className }: { className?: string }) {
  return (
    <span className={cn("inline-block rounded-2xl bg-white p-3", className)}>
      <img src="/brand/diyneco-logo.png" alt="Diyneco" width={640} height={428} className="h-auto w-full" />
    </span>
  );
}

const HOTEL_CODE_KEY = "diyneco.hotel_code";

/** Keeps what people type close to the canonical form; the server does the real check. */
export function tidyHotelCode(raw: string): string {
  return raw.toUpperCase().replace(/[^0-9A-Z-]/g, "").slice(0, 20);
}

export function looksLikeHotelCode(raw: string): boolean {
  return /^(DYN-?)?[0-9A-Z]{13}$/.test(raw.replace(/\s/g, "").toUpperCase());
}

/** The Hotel ID this device used last (not a secret: it only names the hotel). */
export const rememberedHotelCode = {
  get: (): string => (typeof localStorage === "undefined" ? "" : localStorage.getItem(HOTEL_CODE_KEY) ?? ""),
  set: (code: string) => localStorage.setItem(HOTEL_CODE_KEY, code),
};

export interface DeviceSetup {
  hotelCode: string;
  code: string;
  pin: string;
}

/**
 * First start of a guest tablet or kitchen display (D82): the Hotel ID, the 8-digit setup
 * code a manager created in the Merchant app (Devices) and that manager's PIN.
 */
export function DeviceSetupForm({
  title,
  intro,
  submitLabel,
  onSubmit,
}: {
  title: string;
  intro: string;
  submitLabel: string;
  onSubmit: (setup: DeviceSetup) => Promise<void>;
}) {
  const [hotelCode, setHotelCode] = useState("");
  const [code, setCode] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => setHotelCode(rememberedHotelCode.get()), []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSubmit({ hotelCode: hotelCode.trim(), code, pin });
      rememberedHotelCode.set(hotelCode.trim());
    } catch (err) {
      setError(err);
      setPin("");
    } finally {
      setBusy(false);
    }
  };

  const ready = looksLikeHotelCode(hotelCode) && code.length === 8 && pin.length >= 4;
  return (
    <main className="flex min-h-dvh items-center justify-center bg-bg p-6">
      <div className="w-full max-w-md">
        <div className="text-center">
          <BrandLogo className="w-56" />
          <h1 className="mt-6 font-display text-3xl font-semibold text-ink">{title}</h1>
          <p className="mt-2 text-muted">{intro}</p>
        </div>
        <form onSubmit={submit} className="mt-8 flex flex-col gap-5">
          <Field label="Hotel ID" hint="Shown in the Merchant app with the setup code, for example DYN-7K3M9QX2FHT4W.">
            {(p) => (
              <Input
                {...p}
                autoFocus={!hotelCode}
                autoCapitalize="characters"
                autoComplete="off"
                spellCheck={false}
                placeholder="DYN-"
                className="h-14 font-mono text-xl tracking-wider"
                value={hotelCode}
                onChange={(e) => setHotelCode(tidyHotelCode(e.target.value))}
              />
            )}
          </Field>
          <Field label="Setup code" hint="8 digits. It works once and expires after 15 minutes.">
            {(p) => (
              <Input
                {...p}
                autoFocus={Boolean(hotelCode)}
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={8}
                className="h-16 text-center font-mono text-3xl tracking-[0.35em]"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 8))}
              />
            )}
          </Field>
          <Field label="Manager PIN" hint="The PIN of the manager who created the code.">
            {(p) => (
              <Input
                {...p}
                type="password"
                inputMode="numeric"
                autoComplete="off"
                maxLength={6}
                className="h-14 text-center font-mono text-2xl tracking-[0.5em]"
                value={pin}
                onChange={(e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 6))}
              />
            )}
          </Field>
          {error ? <ErrorNotice error={error} /> : null}
          <Button type="submit" size="xl" className="w-full" disabled={!ready} loading={busy}>
            {submitLabel}
          </Button>
        </form>
      </div>
    </main>
  );
}
