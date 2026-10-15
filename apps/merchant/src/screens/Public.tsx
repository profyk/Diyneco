"use client";

import { ApiError, formatDate, newIdempotencyKey, ok } from "@diyneco/api-client";
import { Badge, BrandLogo, Button, Card, CardHeader, ErrorNotice, Field, Input, PageHeader, PasswordInput, Table, Td } from "@diyneco/shared-ui";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { type FormEvent, type ReactNode, useState } from "react";

import { useAction } from "../common";
import { API_URL } from "../config";
import { useSession } from "../session";

async function publicPost(path: string, body: unknown): Promise<unknown> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", "Idempotency-Key": newIdempotencyKey() },
    body: JSON.stringify(body),
  });
  const data = res.status === 204 || res.status === 202 ? await res.json().catch(() => ({})) : await res.json();
  if (!res.ok) throw new ApiError(res.status, data.error);
  return data;
}

function Panel({ title, subtitle, children }: { title: string; subtitle?: ReactNode; children: ReactNode }) {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-bg p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <BrandLogo className="w-48" />
          <h1 className="mt-4 font-display text-2xl font-semibold text-ink">{title}</h1>
          {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
        </div>
        <Card className="p-6">{children}</Card>
      </div>
    </main>
  );
}

function useSubmit(fn: () => Promise<unknown>) {
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await fn();
      setDone(true);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };
  return { error, busy, done, submit };
}

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const s = useSubmit(() => publicPost("/auth/password/forgot", { email }));
  return (
    <Panel title="Reset your password">
      {s.done ? (
        <p className="text-sm text-ink">If that email has an account, a reset link is on its way. It works for one hour.</p>
      ) : (
        <form onSubmit={s.submit} className="flex flex-col gap-4">
          <Field label="Email">{(p) => <Input {...p} type="email" value={email} onChange={(e) => setEmail(e.target.value)} />}</Field>
          {s.error ? <ErrorNotice error={s.error} /> : null}
          <Button type="submit" loading={s.busy} disabled={!email}>
            Send reset link
          </Button>
        </form>
      )}
    </Panel>
  );
}

/** The token from an email link, or a field to paste the code from the email. */
function useEmailCode(): [string, ReactNode] {
  const fromLink = useSearchParams().get("token") ?? "";
  const [typed, setTyped] = useState("");
  const field = fromLink ? null : (
    <Field label="Code from the email" hint="Paste the code exactly as it appears in the email.">
      {(p) => <Input {...p} autoComplete="one-time-code" spellCheck={false} value={typed} onChange={(e) => setTyped(e.target.value)} />}
    </Field>
  );
  return [fromLink || typed.trim(), field];
}

export function ResetPassword() {
  const [token, codeField] = useEmailCode();
  const [password, setPassword] = useState("");
  const s = useSubmit(() => publicPost("/auth/password/reset", { token, new_password: password }));
  return (
    <Panel title="Choose a new password">
      {s.done ? (
        <p className="text-sm text-ink">
          Done. All your other sessions were signed out. <a className="text-blue hover:underline" href="/">Sign in</a>
        </p>
      ) : (
        <form onSubmit={s.submit} className="flex flex-col gap-4">
          {codeField}
          <Field label="New password" hint="At least 12 characters.">
            {(p) => <PasswordInput {...p} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />}
          </Field>
          {s.error ? <ErrorNotice error={s.error} /> : null}
          <Button type="submit" loading={s.busy} disabled={!token || password.length < 12}>
            Save password
          </Button>
        </form>
      )}
    </Panel>
  );
}

export function AcceptInvite() {
  const [token, codeField] = useEmailCode();
  const [f, setF] = useState({ name: "", password: "", pin: "" });
  const s = useSubmit(() => publicPost(`/auth/invitations/${encodeURIComponent(token)}/accept`, f));
  return (
    <Panel title="Join your hotel on Diyneco" subtitle="Set your password and a PIN for confirming sensitive actions.">
      {s.done ? (
        <p className="text-sm text-ink">
          You&apos;re in. <a className="text-blue hover:underline" href="/">Sign in</a>
        </p>
      ) : (
        <form onSubmit={s.submit} className="flex flex-col gap-4">
          {codeField}
          <Field label="Your name">{(p) => <Input {...p} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />}</Field>
          <Field label="Password" hint="At least 12 characters.">
            {(p) => <PasswordInput {...p} autoComplete="new-password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} />}
          </Field>
          <Field label="PIN" hint="4 to 6 digits, used on kitchen displays and to confirm actions.">
            {(p) => <PasswordInput {...p} revealLabel="PIN" inputMode="numeric" maxLength={6} value={f.pin} onChange={(e) => setF({ ...f, pin: e.target.value })} />}
          </Field>
          {s.error ? <ErrorNotice error={s.error} /> : null}
          <Button type="submit" loading={s.busy} disabled={!token || !f.name || f.password.length < 12 || !/^\d{4,6}$/.test(f.pin)}>
            Join
          </Button>
        </form>
      )}
    </Panel>
  );
}

export function VerifyEmail() {
  const [token, codeField] = useEmailCode();
  const s = useSubmit(() => publicPost("/auth/email/verify", { token }));
  return (
    <Panel title="Confirm your email address">
      {s.done ? (
        <p className="text-sm text-ink">
          Thank you, your email address is confirmed. <a className="text-blue hover:underline" href="/">Continue</a>
        </p>
      ) : (
        <form onSubmit={s.submit} className="flex flex-col gap-4">
          {codeField ?? <p className="text-sm text-muted">Confirm the address this link was sent to.</p>}
          {s.error ? <ErrorNotice error={s.error} /> : null}
          <Button type="submit" loading={s.busy} disabled={!token}>
            Confirm email
          </Button>
        </form>
      )}
    </Panel>
  );
}

export function Account() {
  const { api } = useSession();
  const [pin, setPin] = useState("");
  const sessions = useQuery({ queryKey: ["sessions"], queryFn: () => ok(api.GET("/api/v1/auth/sessions")) });
  const savePin = useAction(() => ok(api.PUT("/api/v1/auth/pin", { body: { pin } })), {
    success: "PIN saved.",
    onDone: () => setPin(""),
  });
  const end = useAction((id: string) => ok(api.DELETE("/api/v1/auth/sessions/{session_id}", { params: { path: { session_id: id } } })), {
    success: "Session ended.",
  });
  return (
    <>
      <PageHeader title="My account" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-5">
          <h2 className="font-display text-base font-semibold">PIN</h2>
          <p className="mt-1 text-sm text-muted">Used on kitchen displays and in room service, to set up tablets and displays, and to confirm approvals, discounts and checkouts.</p>
          <div className="mt-4 flex items-end gap-3">
            <Field label="New PIN">
              {(p) => <PasswordInput {...p} revealLabel="PIN" inputMode="numeric" maxLength={6} value={pin} onChange={(e) => setPin(e.target.value)} />}
            </Field>
            <Button disabled={!/^\d{4,6}$/.test(pin)} loading={savePin.isPending} onClick={() => savePin.mutate(undefined)}>
              Save PIN
            </Button>
          </div>
          {savePin.error ? <ErrorNotice error={savePin.error} className="mt-3" /> : null}
        </Card>
        <Card>
          <CardHeader title="Where you're signed in" />
          <Table>
            <tbody>
              {sessions.data?.data.map((s) => (
                <tr key={s.id}>
                  <Td className="text-sm">
                    {s.user_agent ?? "Unknown device"}
                    {s.current ? <Badge tone="good" className="ml-2">This device</Badge> : null}
                  </Td>
                  <Td className="text-muted">{formatDate(s.last_used_at ?? s.created_at)}</Td>
                  <Td className="text-right">
                    {!s.current ? (
                      <Button size="sm" variant="ghost" onClick={() => end.mutate(s.id)}>
                        Sign out
                      </Button>
                    ) : null}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      </div>
    </>
  );
}
