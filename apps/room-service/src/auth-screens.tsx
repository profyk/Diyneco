"use client";

import { ok } from "@diyneco/api-client";
import { Button, Card, ErrorNotice, Field, Input } from "@diyneco/shared-ui";
import { type FormEvent, type ReactNode, useEffect, useState } from "react";

import { useSession } from "./session";

function AuthCard({ title, subtitle, children }: { title: string; subtitle?: ReactNode; children: ReactNode }) {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-bg p-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <p className="font-display text-sm font-semibold uppercase tracking-[0.2em] text-brand">Diyneco</p>
          <h1 className="mt-2 font-display text-2xl font-semibold text-ink">{title}</h1>
          {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
        </div>
        <Card className="p-6">{children}</Card>
      </div>
    </main>
  );
}

export function LoginScreen() {
  const { signIn, verifyMfa } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [recovery, setRecovery] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mfaToken) await verifyMfa(mfaToken, code.trim(), recovery);
      else {
        const challenge = await signIn(email.trim(), password);
        if (challenge) setMfaToken(challenge.mfaToken);
      }
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  if (mfaToken) {
    return (
      <AuthCard title="Two-step sign-in" subtitle="Enter the 6-digit code from your authenticator app.">
        <form onSubmit={submit} className="flex flex-col gap-4">
          <Field label={recovery ? "Recovery code" : "Code"}>
            {(p) => (
              <Input
                {...p}
                autoFocus
                inputMode={recovery ? "text" : "numeric"}
                autoComplete="one-time-code"
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            )}
          </Field>
          {error ? <ErrorNotice error={error} /> : null}
          <Button type="submit" loading={busy} disabled={!code}>
            Verify
          </Button>
          <button type="button" className="text-sm text-blue hover:underline" onClick={() => setRecovery(!recovery)}>
            {recovery ? "Use an authenticator code" : "Use a recovery code"}
          </button>
        </form>
      </AuthCard>
    );
  }

  return (
    <AuthCard title="Room service" subtitle="Sign in with your hotel account">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label="Email">
          {(p) => <Input {...p} type="email" autoComplete="username" autoFocus value={email} onChange={(e) => setEmail(e.target.value)} />}
        </Field>
        <Field label="Password">
          {(p) => (
            <Input {...p} type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          )}
        </Field>
        {error ? <ErrorNotice error={error} /> : null}
        <Button type="submit" loading={busy} disabled={!email || !password}>
          Sign in
        </Button>

      </form>
    </AuthCard>
  );
}

/** Owners, admins, GMs and finance managers must set up two-step sign-in before anything else. */
export function EnrolScreen() {
  const { api, completeEnrolment, signOut } = useSession();
  const [secret, setSecret] = useState<{ secret: string; otpauth_uri: string } | null>(null);
  const [code, setCode] = useState("");
  const [codes, setCodes] = useState<string[] | null>(null);
  const [tokens, setTokens] = useState<unknown>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    ok(api.POST("/api/v1/auth/mfa/enroll")).then(setSecret).catch(setError);
  }, [api]);

  const confirm = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = (await ok(api.POST("/api/v1/auth/mfa/verify", { body: { code: code.trim() } }))) as {
        recovery_codes?: string[];
      };
      setCodes(res.recovery_codes ?? []);
      setTokens(res);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  if (codes) {
    return (
      <AuthCard title="Save your recovery codes" subtitle="Each code works once if you lose your phone. They are shown only now.">
        <ul className="grid grid-cols-2 gap-2 font-mono text-sm text-ink">
          {codes.map((c) => (
            <li key={c} className="rounded-md bg-surface-2 px-2 py-1 text-center">
              {c}
            </li>
          ))}
        </ul>
        <Button className="mt-5 w-full" onClick={() => completeEnrolment(tokens as never)}>
          I have saved them
        </Button>
      </AuthCard>
    );
  }

  return (
    <AuthCard title="Set up two-step sign-in" subtitle="Your role needs it. Use Google Authenticator, Microsoft Authenticator or similar.">
      <ol className="flex list-decimal flex-col gap-3 pl-5 text-sm text-ink">
        <li>
          Add an account in your authenticator app with this key:
          <code className="mt-1 block break-all rounded-md bg-surface-2 px-2 py-1.5 font-mono text-xs">
            {secret?.secret ?? "…"}
          </code>
          {secret ? (
            <a className="mt-1 inline-block text-blue hover:underline" href={secret.otpauth_uri}>
              Open in authenticator app
            </a>
          ) : null}
        </li>
        <li>Enter the 6-digit code it shows.</li>
      </ol>
      <form onSubmit={confirm} className="mt-4 flex flex-col gap-3">
        <Field label="Code">
          {(p) => <Input {...p} inputMode="numeric" autoComplete="one-time-code" value={code} onChange={(e) => setCode(e.target.value)} />}
        </Field>
        {error ? <ErrorNotice error={error} /> : null}
        <Button type="submit" loading={busy} disabled={code.length < 6}>
          Turn on two-step sign-in
        </Button>
        <Button variant="ghost" onClick={signOut}>
          Sign out
        </Button>
      </form>
    </AuthCard>
  );
}
