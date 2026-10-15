"use client";

import { ok } from "@diyneco/api-client";
import {
  BrandLogo,
  Button,
  Card,
  ErrorNotice,
  Field,
  Input,
  looksLikeHotelCode,
  PasswordInput,
  rememberedHotelCode,
  tidyHotelCode,
} from "@diyneco/shared-ui";
import { type FormEvent, type ReactNode, useEffect, useState } from "react";

import { useSession } from "./session";

function AuthCard({ title, subtitle, children }: { title: string; subtitle?: ReactNode; children: ReactNode }) {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-bg p-4">
      <div className="w-full max-w-sm">
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

/** Staff sign in with the Hotel ID, their 8-digit staff code and PIN (D82); managers whose role
 * needs two-step sign-in use email instead. */
export function LoginScreen() {
  const [withEmail, setWithEmail] = useState(false);
  return withEmail ? <EmailLogin onCode={() => setWithEmail(false)} /> : <CodeLogin onEmail={() => setWithEmail(true)} />;
}

function CodeLogin({ onEmail }: { onEmail: () => void }) {
  const { signInWithCode } = useSession();
  const [hotelCode, setHotelCode] = useState("");
  const [staffCode, setStaffCode] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => setHotelCode(rememberedHotelCode.get()), []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signInWithCode(hotelCode.trim(), staffCode, pin);
      rememberedHotelCode.set(hotelCode.trim());
    } catch (err) {
      setError(err);
      setPin("");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthCard title="Room service" subtitle="Sign in with your staff code">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label="Hotel ID" hint="Ask your manager. It looks like DYN-7K3M9QX2FHT4W.">
          {(p) => (
            <Input
              {...p}
              autoFocus={!hotelCode}
              autoCapitalize="characters"
              autoComplete="organization"
              spellCheck={false}
              placeholder="DYN-"
              className="h-12 font-mono text-lg tracking-wider"
              value={hotelCode}
              onChange={(e) => setHotelCode(tidyHotelCode(e.target.value))}
            />
          )}
        </Field>
        <Field label="Staff code" hint="Your own 8-digit code from your manager.">
          {(p) => (
            <Input
              {...p}
              autoFocus={Boolean(hotelCode)}
              inputMode="numeric"
              autoComplete="username"
              maxLength={8}
              className="h-12 text-center font-mono text-2xl tracking-[0.3em]"
              value={staffCode}
              onChange={(e) => setStaffCode(e.target.value.replace(/\D/g, "").slice(0, 8))}
            />
          )}
        </Field>
        <Field label="PIN">
          {(p) => (
            <PasswordInput
              {...p}
              revealLabel="PIN"
              inputMode="numeric"
              autoComplete="current-password"
              maxLength={6}
              className="h-12 text-center font-mono text-2xl tracking-[0.5em]"
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 6))}
            />
          )}
        </Field>
        {error ? <ErrorNotice error={error} /> : null}
        <Button type="submit" size="lg" loading={busy} disabled={!looksLikeHotelCode(hotelCode) || staffCode.length !== 8 || pin.length < 4}>
          Sign in
        </Button>
        <button type="button" className="text-sm text-blue hover:underline" onClick={onEmail}>
          Managers: sign in with email
        </button>
      </form>
    </AuthCard>
  );
}

function EmailLogin({ onCode }: { onCode: () => void }) {
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
            <PasswordInput {...p} autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          )}
        </Field>
        {error ? <ErrorNotice error={error} /> : null}
        <Button type="submit" loading={busy} disabled={!email || !password}>
          Sign in
        </Button>
        <button type="button" className="text-sm text-blue hover:underline" onClick={onCode}>
          Sign in with a staff code
        </button>
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
