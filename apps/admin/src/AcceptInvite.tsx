"use client";

import { ApiError, newIdempotencyKey } from "@diyneco/api-client";
import { Button, Card, ErrorNotice, Field, Input } from "@diyneco/shared-ui";
import { useSearchParams } from "next/navigation";
import { type FormEvent, useState } from "react";

import { API_URL } from "./config";

// A new Diyneco staff member chooses a password from the invitation email (DECISIONS D71).
// Two-step sign-in is set up at the first sign-in, like for every platform account.

export function AcceptInvite() {
  const fromLink = useSearchParams().get("token") ?? "";
  const [typed, setTyped] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const token = fromLink || typed.trim();

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/platform-invitations/accept`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": newIdempotencyKey() },
        body: JSON.stringify({ token, password }),
      });
      if (!res.ok) throw new ApiError(res.status, (await res.json()).error);
      setDone(true);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="flex min-h-dvh items-center justify-center bg-bg p-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <p className="font-display text-sm font-semibold uppercase tracking-[0.2em] text-brand">Diyneco</p>
          <h1 className="mt-2 font-display text-2xl font-semibold text-ink">Join the Diyneco admin panel</h1>
          <p className="mt-1 text-sm text-muted">Choose your password. You set up two-step sign-in when you first sign in.</p>
        </div>
        <Card className="p-6">
          {done ? (
            <p className="text-sm text-ink">
              Your password is set.{" "}
              <a className="text-blue hover:underline" href="/">
                Sign in
              </a>
            </p>
          ) : (
            <form onSubmit={submit} className="flex flex-col gap-4">
              {fromLink ? null : (
                <Field label="Code from the email" hint="Paste the code exactly as it appears in the email.">
                  {(p) => (
                    <Input {...p} autoComplete="one-time-code" spellCheck={false} value={typed} onChange={(e) => setTyped(e.target.value)} />
                  )}
                </Field>
              )}
              <Field label="Password" hint="At least 12 characters.">
                {(p) => (
                  <Input {...p} type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />
                )}
              </Field>
              {error ? <ErrorNotice error={error} /> : null}
              <Button type="submit" loading={busy} disabled={!token || password.length < 12}>
                Set password
              </Button>
            </form>
          )}
        </Card>
      </div>
    </main>
  );
}
