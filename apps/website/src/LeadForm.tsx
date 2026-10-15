"use client";

import { Button, Field, Input, Select, Textarea } from "@diyneco/shared-ui";
import { type FormEvent, useEffect, useRef, useState } from "react";

const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const CONSENT = "You may contact me about Diyneco using the details above. See the privacy notice.";

/**
 * Demo or contact request (D83). The API drops spam silently: a hidden field people leave
 * empty, and forms sent within 3 seconds of opening. Nothing is emailed to the sender.
 */
export function LeadForm({
  kind,
  heading,
  intro,
  locale,
  countries,
}: {
  kind: "demo" | "contact";
  heading?: string | null;
  intro?: string | null;
  locale: string;
  countries: { code: string; name: string }[];
}) {
  const opened = useRef(Date.now());
  const [f, setF] = useState({ name: "", email: "", phone: "", company: "", rooms: "", country: "", message: "", website: "" });
  const [consent, setConsent] = useState(false);
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [error, setError] = useState("");
  useEffect(() => {
    opened.current = Date.now();
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setState("sending");
    setError("");
    try {
      const res = await fetch(`${API}/api/v1/site/leads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind,
          name: f.name.trim(),
          email: f.email.trim(),
          phone: f.phone.trim() || null,
          company: f.company.trim() || null,
          rooms: f.rooms ? Number(f.rooms) : null,
          country: f.country || null,
          message: f.message.trim() || null,
          locale,
          source_path: window.location.pathname,
          consent: true,
          consent_text: CONSENT,
          website: f.website,
          elapsed_ms: Date.now() - opened.current,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.error?.message ?? "Something went wrong. Please try again or email us.");
      }
      setState("sent");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setState("error");
    }
  };

  if (state === "sent") {
    return (
      <div className="rounded-[var(--radius-card)] border border-line bg-surface p-8 text-center">
        <p className="font-display text-xl font-semibold text-ink">Thank you, we&apos;ll be in touch</p>
        <p className="mt-2 text-muted">
          {kind === "demo" ? "Someone from Diyneco will contact you within one working day to arrange your demo." : "We usually reply within one working day."}
        </p>
      </div>
    );
  }

  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  return (
    <div>
      {heading ? <h2 className="font-display text-2xl font-semibold text-ink sm:text-3xl">{heading}</h2> : null}
      {intro ? <p className="mt-2 text-muted">{intro}</p> : null}
      <form onSubmit={submit} className="mt-6 grid gap-4 rounded-[var(--radius-card)] border border-line bg-surface p-6 sm:grid-cols-2">
        <Field label="Your name">{(p) => <Input {...p} required autoComplete="name" value={f.name} onChange={set("name")} />}</Field>
        <Field label="Work email">{(p) => <Input {...p} required type="email" autoComplete="email" value={f.email} onChange={set("email")} />}</Field>
        <Field label="Phone (optional)">{(p) => <Input {...p} type="tel" autoComplete="tel" value={f.phone} onChange={set("phone")} />}</Field>
        <Field label="Hotel or company">{(p) => <Input {...p} autoComplete="organization" value={f.company} onChange={set("company")} />}</Field>
        <Field label="Rooms (optional)">{(p) => <Input {...p} type="number" min={1} inputMode="numeric" value={f.rooms} onChange={set("rooms")} />}</Field>
        <Field label="Country">
          {(p) => (
            <Select {...p} value={f.country} onChange={set("country")}>
              <option value="">Choose…</option>
              {countries.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label={kind === "demo" ? "What would you like to see? (optional)" : "Message"} className="sm:col-span-2">
          {(p) => <Textarea {...p} required={kind === "contact"} rows={4} value={f.message} onChange={set("message")} />}
        </Field>
        {/* Honeypot: hidden from people, filled by bots. */}
        <div aria-hidden className="absolute left-[-9999px] h-0 overflow-hidden">
          <label>
            Website
            <input tabIndex={-1} autoComplete="off" value={f.website} onChange={set("website")} />
          </label>
        </div>
        <label className="flex items-start gap-2 text-sm text-ink sm:col-span-2">
          <input type="checkbox" required className="mt-1" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
          <span>
            {CONSENT.replace(" See the privacy notice.", " ")}
            See the{" "}
            <a href="/legal/privacy" className="text-blue hover:underline">
              privacy notice
            </a>
            .
          </span>
        </label>
        {state === "error" ? <p className="text-sm text-crit sm:col-span-2">{error}</p> : null}
        <div className="sm:col-span-2">
          <Button type="submit" size="lg" loading={state === "sending"} disabled={!consent}>
            {kind === "demo" ? "Book a demo" : "Send message"}
          </Button>
        </div>
      </form>
    </div>
  );
}
