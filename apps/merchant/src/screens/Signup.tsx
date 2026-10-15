"use client";

/**
 * Hotel registration (D84): a guided form in four steps, then the 6-digit code from the
 * confirmation email. Countries are the ones Diyneco has opened for signups; the currency
 * follows the country and is shown, not asked. The draft survives a reload (never the password).
 */
import { ApiError, newIdempotencyKey, ok } from "@diyneco/api-client";
import {
  BrandLogo,
  Button,
  Card,
  cn,
  ErrorNotice,
  Field,
  Input,
  PageHeader,
  PasswordInput,
  type PropertyType,
  propertyTypeGroups,
  propertyTypeLabel,
  Select,
  Skeleton,
} from "@diyneco/shared-ui";
import { CountryPicker, Flag, PhoneInput, toE164 } from "@diyneco/shared-ui/countries";
import { useQuery } from "@tanstack/react-query";
import { type FormEvent, type ReactNode, useEffect, useMemo, useRef, useState } from "react";

import { API_URL } from "../config";
import { type LegalDoc, LegalText } from "../Legal";
import { useSession } from "../session";

interface Country {
  code: string;
  name: string;
  currency: string;
  timezone: string;
  timezones: string[];
  dial: string;
  tax_label: string;
}

interface Regions {
  label: string;
  data: { code: string; name: string }[];
}

const STEPS = ["Property", "Location", "Your account", "Review"] as const;
const DRAFT_KEY = "diyneco.signup.draft";

type Form = {
  hotel: string;
  propertyType: string;
  rooms: string;
  legalName: string;
  website: string;
  country: string;
  timezone: string;
  line1: string;
  line2: string;
  city: string;
  province: string;
  provinceCode: string;
  postalCode: string;
  hotelPhoneCountry: string;
  hotelPhone: string;
  hotelEmail: string;
  name: string;
  email: string;
  mobileCountry: string;
  mobile: string;
  password: string;
};

const EMPTY: Form = {
  hotel: "",
  propertyType: "",
  rooms: "",
  legalName: "",
  website: "",
  country: "",
  timezone: "",
  line1: "",
  line2: "",
  city: "",
  province: "",
  provinceCode: "",
  postalCode: "",
  hotelPhoneCountry: "",
  hotelPhone: "",
  hotelEmail: "",
  name: "",
  email: "",
  mobileCountry: "",
  mobile: "",
  password: "",
};

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

async function publicJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (res.status === 204) return {} as T;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, data.error ?? { code: "INTERNAL", message: "Something went wrong." });
  return data as T;
}

function loadDraft(key: string): Form {
  try {
    const raw = sessionStorage.getItem(key);
    return raw ? { ...EMPTY, ...(JSON.parse(raw) as Partial<Form>), password: "" } : EMPTY;
  } catch {
    return EMPTY;
  }
}

function saveDraft(key: string, f: Form) {
  try {
    const { password: _never, ...rest } = f;
    sessionStorage.setItem(key, JSON.stringify(rest));
  } catch {
    /* private mode: the form still works, it just is not kept */
  }
}

function clearDraft(key: string) {
  try {
    sessionStorage.removeItem(key);
  } catch {
    /* ignore */
  }
}

/** The country whose time zones include the browser's, if Diyneco is open there. */
function guessCountry(list: Country[]): string {
  try {
    const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const byZone = list.find((c) => c.timezones.includes(zone));
    if (byZone) return byZone.code;
    const region = navigator.language.split("-")[1]?.toUpperCase();
    return list.find((c) => c.code === region)?.code ?? "";
  } catch {
    return "";
  }
}

function passwordScore(pw: string): { score: number; label: string } {
  if (!pw) return { score: 0, label: "" };
  let s = 0;
  if (pw.length >= 12) s++;
  if (pw.length >= 16) s++;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) s++;
  if (/\d/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw) || /\s/.test(pw)) s++;
  if (pw.length < 12) return { score: 1, label: "Too short" };
  return s >= 5 ? { score: 4, label: "Strong" } : s >= 4 ? { score: 3, label: "Good" } : { score: 2, label: "Fair" };
}

function zoneLabel(zone: string): string {
  const city = zone.split("/").pop()?.replace(/_/g, " ") ?? zone;
  try {
    const offset = new Intl.DateTimeFormat("en", { timeZone: zone, timeZoneName: "shortOffset" })
      .formatToParts(new Date())
      .find((p) => p.type === "timeZoneName")?.value;
    return offset ? `${city} (${offset})` : city;
  } catch {
    return city;
  }
}

type Errors = Partial<Record<keyof Form | "agreed", string>>;

function validate(step: number, f: Form, regions?: Regions): Errors {
  const e: Errors = {};
  if (step === 0) {
    if (!f.hotel.trim()) e.hotel = "Enter the name guests know you by.";
    if (!f.propertyType) e.propertyType = "Choose the kind of property.";
    const rooms = Number(f.rooms);
    if (!f.rooms || !Number.isInteger(rooms) || rooms < 1 || rooms > 5000) e.rooms = "Enter a number from 1 to 5,000.";
    if (f.website && !/^https?:\/\/\S+\.\S+$/.test(f.website.trim())) e.website = "Start with https://, for example https://myhotel.com";
  }
  if (step === 1) {
    if (!f.country) e.country = "Choose the country the property is in.";
    if (!f.line1.trim()) e.line1 = "Enter the street address.";
    if (!f.city.trim()) e.city = "Enter the town or city.";
    if (regions?.data.length && !regions.data.some((r) => r.code === f.provinceCode)) {
      e.provinceCode = `Choose the ${regions.label.toLowerCase()}.`;
    }
    if (f.hotelPhone && toE164("+1", f.hotelPhone).length < 8) e.hotelPhone = "Enter the full phone number.";
    if (f.hotelEmail && !EMAIL.test(f.hotelEmail.trim())) e.hotelEmail = "Enter a valid email address.";
  }
  if (step === 2) {
    if (!f.name.trim()) e.name = "Enter your full name.";
    if (!EMAIL.test(f.email.trim())) e.email = "Enter a valid email address. We send a code to it.";
    if (!f.mobile.trim()) e.mobile = "Enter your mobile number, for account and billing matters.";
    else if (toE164("+1", f.mobile).length < 8) e.mobile = "Enter the full mobile number.";
    if (f.password.length < 12) e.password = "Use at least 12 characters.";
  }
  return e;
}

/** Which step holds a field the server rejected. */
function stepOf(field: string): number {
  if (field.startsWith("owner.")) return 2;
  if (/^hotel\.(country|timezone|address|phone|email)/.test(field)) return 1;
  if (field.startsWith("hotel.")) return 0;
  return 3;
}

/**
 * `signup`: a new owner registers their first property. `add`: a signed-in owner adds another
 * property (D86): the same property and location steps, no account step, and it starts
 * without a free trial (the trial is once per owner).
 */
export function Signup({ mode = "signup" }: { mode?: "signup" | "add" }) {
  const adding = mode === "add";
  const shown = adding ? [0, 1, 3] : [0, 1, 2, 3];
  const draftKey = `${DRAFT_KEY}.${mode}`;
  const { api, switchHotel } = useSession();
  const [added, setAdded] = useState<{ hotel_id: string; name: string; code: string } | null>(null);
  const [f, setF] = useState<Form>(EMPTY);
  const [step, setStep] = useState(0);
  const [errors, setErrors] = useState<Errors>({});
  const [agreed, setAgreed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [submitError, setSubmitError] = useState<unknown>(null);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);

  const countries = useQuery({
    queryKey: ["signup-countries"],
    queryFn: () => publicJson<{ data: Country[] }>("/countries"),
    staleTime: 10 * 60_000,
  });
  const currencies = useQuery({
    queryKey: ["currencies"],
    queryFn: () => publicJson<{ data: { code: string; name: string }[] }>("/currencies"),
    staleTime: Infinity,
  });
  const list = useMemo(() => countries.data?.data ?? [], [countries.data]);
  const country = list.find((c) => c.code === f.country);
  const legal = useQuery({
    queryKey: ["legal-signup", f.country],
    enabled: Boolean(f.country),
    queryFn: () => publicJson<{ data: LegalDoc[] }>(`/legal/documents?audience=merchant&country=${f.country}`),
  });
  const docs = legal.data?.data ?? [];
  const regionsQ = useQuery({
    queryKey: ["regions", f.country],
    enabled: Boolean(f.country),
    queryFn: () => publicJson<Regions>(`/countries/${f.country}/regions`),
    staleTime: Infinity,
  });
  const regions = regionsQ.data;
  const regionName = regions?.data.find((r) => r.code === f.provinceCode)?.name;

  // Restore a draft, then fill the country from the browser when nothing was chosen yet.
  useEffect(() => setF(loadDraft(draftKey)), [draftKey]);
  useEffect(() => {
    if (!list.length) return;
    setF((cur) => {
      if (cur.country && list.some((c) => c.code === cur.country)) return cur;
      const guess = guessCountry(list) || (list.length === 1 ? (list[0]?.code ?? "") : "");
      const c = list.find((x) => x.code === guess);
      return c
        ? { ...cur, country: c.code, timezone: c.timezone, hotelPhoneCountry: c.code, mobileCountry: c.code }
        : cur;
    });
  }, [list]);
  useEffect(() => saveDraft(draftKey, f), [draftKey, f]);
  useEffect(() => heading.current?.focus(), [step]);

  const set = <K extends keyof Form>(k: K, v: Form[K]) => {
    setF((cur) => ({ ...cur, [k]: v }));
    setErrors((cur) => ({ ...cur, [k]: undefined }));
  };
  const chooseCountry = (code: string) => {
    const c = list.find((x) => x.code === code);
    setF((cur) => ({
      ...cur,
      country: code,
      provinceCode: cur.country === code ? cur.provinceCode : "",
      timezone: c?.timezone ?? "",
      hotelPhoneCountry: cur.hotelPhone ? cur.hotelPhoneCountry || code : code,
      mobileCountry: cur.mobile ? cur.mobileCountry || code : code,
    }));
    setErrors((cur) => ({ ...cur, country: undefined }));
  };
  const dialOf = (code: string) => list.find((c) => c.code === code)?.dial ?? country?.dial ?? "+";

  const next = (e?: FormEvent) => {
    e?.preventDefault();
    const found = validate(step, f, regions);
    setErrors(found);
    if (Object.keys(found).length === 0) setStep((s) => shown[shown.indexOf(s) + 1] ?? s);
  };
  const back = () => setStep((s) => shown[shown.indexOf(s) - 1] ?? 0);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (docs.length && !agreed) {
      setErrors({ agreed: "Accept the documents to continue." });
      return;
    }
    for (const s of shown.filter((x) => x < 3)) {
      const found = validate(s, f, regions);
      if (Object.keys(found).length) {
        setErrors(found);
        setStep(s);
        return;
      }
    }
    setBusy(true);
    setSubmitError(null);
    try {
      const address = {
        line1: f.line1.trim(),
        line2: f.line2.trim() || null,
        city: f.city.trim(),
        ...(regions?.data.length
          ? { province_code: f.provinceCode }
          : { province: f.province.trim() || null }),
        postal_code: f.postalCode.trim() || null,
        country: f.country,
      };
      const hotel = {
        name: f.hotel.trim(),
        property_type: f.propertyType as PropertyType,
        room_count: Number(f.rooms),
        legal_name: f.legalName.trim() || null,
        website: f.website.trim() || null,
        country: f.country,
        timezone: f.timezone || null,
        address,
        phone: f.hotelPhone ? toE164(dialOf(f.hotelPhoneCountry), f.hotelPhone) : null,
        email: f.hotelEmail.trim() || null,
      };
      const accepted_documents = agreed ? docs.map((d) => d.id) : [];
      if (adding) {
        // Step-up (PIN or password) is asked for by the API client when the server wants it.
        const created = await ok(api.POST("/api/v1/hotels", { body: { hotel, accepted_documents } }));
        clearDraft(draftKey);
        setAdded({ hotel_id: created.hotel_id, name: created.name, code: created.code });
        return;
      }
      await publicJson("/signup", {
        method: "POST",
        headers: { "Idempotency-Key": newIdempotencyKey() },
        body: JSON.stringify({
          hotel,
          owner: {
            name: f.name.trim(),
            email: f.email.trim(),
            password: f.password,
            phone: toE164(dialOf(f.mobileCountry), f.mobile) || null,
          },
          accepted_documents,
        }),
      });
      clearDraft(draftKey);
      setRegisteredEmail(f.email.trim());
    } catch (err) {
      setSubmitError(err);
      const fields = err instanceof ApiError ? (err.details.fields as { field: string; problem: string }[] | undefined) : undefined;
      const first = fields?.[0];
      if (first) setStep(stepOf(first.field));
    } finally {
      setBusy(false);
    }
  };

  if (registeredEmail) return <ConfirmEmail email={registeredEmail} />;
  if (added) {
    return (
      <Card className="mx-auto max-w-xl p-8 text-center">
        <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-good-bg text-2xl text-good">✓</div>
        <h2 className="mt-4 font-display text-xl font-semibold text-ink">{added.name} is added</h2>
        <p className="mt-2 text-sm text-muted">
          Its Hotel ID is <span className="font-mono text-ink">{added.code}</span>. Diyneco reviews new properties, usually
          within one working day. Choose a plan for it in Settings › Plan to add rooms, staff and devices.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Button
            size="lg"
            onClick={async () => {
              await switchHotel(added.hotel_id);
              window.location.assign("/settings?tab=plan");
            }}
          >
            Open {added.name}
          </Button>
          <a href="/properties" className="inline-flex h-12 items-center rounded-[10px] border border-line px-5 text-ink hover:bg-surface-2">
            All properties
          </a>
        </div>
      </Card>
    );
  }

  const currencyName = currencies.data?.data.find((c) => c.code === country?.currency)?.name;
  const score = passwordScore(f.password);

  const Frame = adding ? InApp : Shell;
  return (
    <Frame>
      <Stepper steps={shown} step={step} onJump={(s) => s < step && setStep(s)} />
      <Card className="mt-4 p-6 sm:p-8">
        <h2 ref={heading} tabIndex={-1} className="font-display text-xl font-semibold text-ink outline-none">
          {["Tell us about your property", "Where is it?", "Create your account", "Check and confirm"][step]}
        </h2>
        <p className="mt-1 text-sm text-muted">
          {
            [
              "This sets up your hotel. You can change all of it later in Settings.",
              "The country sets where your data is stored, your currency and your tax defaults.",
              "You'll be the owner of this hotel on Diyneco and can invite your team afterwards.",
              adding
                ? "Make sure everything is right, then add the property."
                : "Make sure everything is right, then register. We'll email you a 6-digit code.",
            ][step]
          }
        </p>

        {step < 3 ? (
          <form onSubmit={next} className="mt-6 flex flex-col gap-5" noValidate>
            {step === 0 ? (
              <>
                <Field label="Property name" error={errors.hotel}>
                  {(p) => <Input {...p} autoComplete="organization" value={f.hotel} onChange={(e) => set("hotel", e.target.value)} placeholder="e.g. Sunbird Lodge" />}
                </Field>
                <Field label="Type of property" error={errors.propertyType} hint="Choose the closest match; you can change it later.">
                  {(p) => (
                    <Select {...p} value={f.propertyType} onChange={(e) => set("propertyType", e.target.value)}>
                      <option value="">Choose a category</option>
                      {propertyTypeGroups().map((g) => (
                        <optgroup key={g.group} label={g.group}>
                          {g.items.map((t) => (
                            <option key={t.value} value={t.value}>
                              {t.label}
                            </option>
                          ))}
                        </optgroup>
                      ))}
                    </Select>
                  )}
                </Field>
                <div className="grid gap-5 sm:grid-cols-2">
                  <Field label="Number of rooms or units" error={errors.rooms} hint="Helps us suggest the right plan.">
                    {(p) => <Input {...p} type="number" inputMode="numeric" min={1} max={5000} value={f.rooms} onChange={(e) => set("rooms", e.target.value)} />}
                  </Field>
                  <Field label="Website (optional)" error={errors.website}>
                    {(p) => <Input {...p} type="url" inputMode="url" placeholder="https://" value={f.website} onChange={(e) => set("website", e.target.value)} />}
                  </Field>
                </div>
                <Field label="Registered company name (optional)" hint="Printed on your invoices if it differs from the property name.">
                  {(p) => <Input {...p} value={f.legalName} onChange={(e) => set("legalName", e.target.value)} />}
                </Field>
              </>
            ) : null}

            {step === 1 ? (
              <>
                <Field label="Country" error={errors.country}>
                  {(p) =>
                    countries.isLoading ? (
                      <Skeleton className="h-10 w-full" />
                    ) : (
                      <CountryPicker fieldProps={p} countries={list} value={f.country} onChange={chooseCountry} />
                    )
                  }
                </Field>
                <p className="-mt-3 text-xs text-muted">
                  Not listed? Diyneco is opening country by country. Your country will appear here as soon as we launch there.
                </p>
                {country ? (
                  <div className="flex items-start gap-3 rounded-[10px] bg-tint px-4 py-3 text-sm text-ink">
                    <Flag code={country.code} className="mt-0.5 h-4 w-[1.35rem]" />
                    <p>
                      Prices and bills will be in <strong>{country.currency}</strong>
                      {currencyName ? ` (${currencyName})` : ""}, with {country.tax_label} set up for {country.name}. You can change the
                      currency in Settings until your first guest checks in.
                    </p>
                  </div>
                ) : null}
                {country && country.timezones.length > 1 ? (
                  <Field label="Time zone" hint="Used for orders, reports and checkout times.">
                    {(p) => (
                      <Select {...p} value={f.timezone} onChange={(e) => set("timezone", e.target.value)}>
                        {country.timezones.map((z) => (
                          <option key={z} value={z}>
                            {zoneLabel(z)}
                          </option>
                        ))}
                      </Select>
                    )}
                  </Field>
                ) : null}
                <Field label="Street address" error={errors.line1}>
                  {(p) => <Input {...p} autoComplete="address-line1" value={f.line1} onChange={(e) => set("line1", e.target.value)} />}
                </Field>
                <Field label="Address line 2 (optional)">
                  {(p) => <Input {...p} autoComplete="address-line2" value={f.line2} onChange={(e) => set("line2", e.target.value)} />}
                </Field>
                <div className="grid gap-5 sm:grid-cols-3">
                  <Field label="Town or city" error={errors.city}>
                    {(p) => <Input {...p} autoComplete="address-level2" value={f.city} onChange={(e) => set("city", e.target.value)} />}
                  </Field>
                  <Field label={regions?.data.length ? regions.label : "Province or state"} error={errors.provinceCode}>
                    {(p) =>
                      regionsQ.isLoading ? (
                        <Skeleton className="h-10 w-full" />
                      ) : regions?.data.length ? (
                        <Select {...p} autoComplete="address-level1" value={f.provinceCode} onChange={(e) => set("provinceCode", e.target.value)}>
                          <option value="">Choose…</option>
                          {regions.data.map((r) => (
                            <option key={r.code} value={r.code}>
                              {r.name}
                            </option>
                          ))}
                        </Select>
                      ) : (
                        <Input {...p} autoComplete="address-level1" value={f.province} onChange={(e) => set("province", e.target.value)} />
                      )
                    }
                  </Field>
                  <Field label="Postal code">
                    {(p) => <Input {...p} autoComplete="postal-code" value={f.postalCode} onChange={(e) => set("postalCode", e.target.value)} />}
                  </Field>
                </div>
                <div className="grid gap-5 sm:grid-cols-2">
                  <Field label="Reception phone (optional)" error={errors.hotelPhone}>
                    {(p) => (
                      <PhoneInput
                        fieldProps={p}
                        countries={list}
                        country={f.hotelPhoneCountry || f.country}
                        onCountryChange={(c) => set("hotelPhoneCountry", c)}
                        number={f.hotelPhone}
                        onNumberChange={(v) => set("hotelPhone", v)}
                        placeholder="Phone number"
                      />
                    )}
                  </Field>
                  <Field label="Reservations email (optional)" error={errors.hotelEmail}>
                    {(p) => <Input {...p} type="email" value={f.hotelEmail} onChange={(e) => set("hotelEmail", e.target.value)} />}
                  </Field>
                </div>
              </>
            ) : null}

            {step === 2 ? (
              <>
                <Field label="Your full name" error={errors.name}>
                  {(p) => <Input {...p} autoComplete="name" value={f.name} onChange={(e) => set("name", e.target.value)} />}
                </Field>
                <Field label="Your email" error={errors.email} hint="You'll sign in with it. We'll send a 6-digit code to confirm it.">
                  {(p) => <Input {...p} type="email" autoComplete="email" value={f.email} onChange={(e) => set("email", e.target.value)} />}
                </Field>
                <Field label="Your mobile number" error={errors.mobile} hint="Only for account security and billing matters.">
                  {(p) => (
                    <PhoneInput
                      fieldProps={p}
                      countries={list}
                      country={f.mobileCountry || f.country}
                      onCountryChange={(c) => set("mobileCountry", c)}
                      number={f.mobile}
                      onNumberChange={(v) => set("mobile", v)}
                    />
                  )}
                </Field>
                <Field label="Password" error={errors.password} hint="At least 12 characters. A short phrase of four or more words works well.">
                  {(p) => (
                    <PasswordInput {...p} autoComplete="new-password" value={f.password} onChange={(e) => set("password", e.target.value)} />
                  )}
                </Field>
                {f.password ? (
                  <div className="-mt-3" aria-live="polite">
                    <div className="flex gap-1" aria-hidden>
                      {[1, 2, 3, 4].map((i) => (
                        <span
                          key={i}
                          className={cn(
                            "h-1.5 flex-1 rounded-full",
                            i <= score.score ? (score.score <= 1 ? "bg-crit" : score.score === 2 ? "bg-warn" : "bg-good") : "bg-surface-2",
                          )}
                        />
                      ))}
                    </div>
                    <p className="mt-1 text-xs text-muted">Password strength: {score.label}</p>
                  </div>
                ) : null}
              </>
            ) : null}

            <div className="mt-2 flex items-center justify-between gap-3">
              {step > 0 ? (
                <Button variant="ghost" onClick={back}>
                  Back
                </Button>
              ) : adding ? (
                <a className="text-sm text-blue hover:underline" href="/properties">
                  Cancel
                </a>
              ) : (
                <a className="text-sm text-blue hover:underline" href="/">
                  Already registered? Sign in
                </a>
              )}
              <Button type="submit" size="lg" disabled={step === 1 && !list.length}>
                Continue
              </Button>
            </div>
          </form>
        ) : (
          <form onSubmit={submit} className="mt-6 flex flex-col gap-5">
            <Summary
              rows={[
                ["Property", `${f.hotel} · ${propertyTypeLabel(f.propertyType)} · ${f.rooms} rooms`, 0],
                [
                  "Location",
                  [f.line1, f.line2, f.city, regionName ?? f.province, f.postalCode, country?.name].filter(Boolean).join(", "),
                  1,
                ],
                ["Currency and time zone", `${country?.currency ?? ""} · ${f.timezone ? zoneLabel(f.timezone) : ""}`, 1],
                ...(adding
                  ? []
                  : [["Owner", `${f.name} · ${f.email} · ${toE164(dialOf(f.mobileCountry), f.mobile)}`, 2] as [string, string, number]]),
              ]}
              onEdit={setStep}
            />
            {legal.isLoading ? <Skeleton className="h-24 w-full" /> : null}
            {docs.length ? (
              <div className="flex flex-col gap-2">
                {docs.map((d) => (
                  <LegalText key={d.id} doc={d} />
                ))}
                <label className="flex items-start gap-2 text-sm text-ink">
                  <input type="checkbox" className="mt-0.5" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} />
                  I accept these documents on behalf of the property and confirm I may act for it.
                </label>
                {errors.agreed ? <p className="text-sm text-crit">{errors.agreed}</p> : null}
              </div>
            ) : null}
            {submitError ? <ErrorNotice error={submitError} /> : null}
            <div className="flex items-center justify-between gap-3">
              <Button variant="ghost" onClick={back}>
                Back
              </Button>
              <Button type="submit" size="lg" loading={busy} disabled={docs.length > 0 && !agreed}>
                {adding ? "Add property" : "Register property"}
              </Button>
            </div>
            <p className="text-xs text-muted">
              Guest data is processed under the data protection law of {country?.name ?? "your country"} as described in our privacy
              notice.{" "}
              {adding
                ? "The free trial comes once per owner: choose a plan for this property, or ask Diyneco about a trial."
                : "Your free trial starts today; nothing is charged until you choose a plan."}
            </p>
          </form>
        )}
      </Card>
    </Frame>
  );
}

function InApp({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-2xl">
      <PageHeader title="Add a property" description="Another hotel, lodge or guest house under your account." />
      {children}
    </div>
  );
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <main className="flex min-h-dvh justify-center bg-bg px-4 py-8 sm:py-12">
      <div className="w-full max-w-2xl">
        <div className="mb-6 flex flex-col items-center text-center">
          <BrandLogo className="w-44" />
          <h1 className="mt-4 font-display text-2xl font-semibold text-ink">Register your property</h1>
          <p className="mt-1 text-sm text-muted">Guest tablets, kitchen displays, room service and billing in one place.</p>
        </div>
        {children}
      </div>
    </main>
  );
}

function Stepper({ steps, step, onJump }: { steps: number[]; step: number; onJump: (s: number) => void }) {
  const items = steps.map((i) => ({ i, label: STEPS[i] ?? "" }));
  return (
    <ol className="flex items-center gap-2" aria-label="Registration steps">
      {items.map(({ i, label }, n) => (
        <li key={label} className="flex flex-1 items-center gap-2">
          <button
            type="button"
            onClick={() => onJump(i)}
            disabled={i >= step}
            aria-current={i === step ? "step" : undefined}
            className="flex items-center gap-2 disabled:cursor-default"
          >
            <span
              className={cn(
                "flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
                i < step ? "bg-good text-white" : i === step ? "bg-brand text-on-brand" : "bg-surface-2 text-muted",
              )}
            >
              {i < step ? "✓" : n + 1}
            </span>
            <span className={cn("hidden text-sm sm:inline", i === step ? "font-medium text-ink" : "text-muted")}>{label}</span>
          </button>
          {n < items.length - 1 ? <span className={cn("h-px flex-1", i < step ? "bg-good" : "bg-line")} /> : null}
        </li>
      ))}
    </ol>
  );
}

function Summary({ rows, onEdit }: { rows: [string, string, number][]; onEdit: (step: number) => void }) {
  return (
    <dl className="divide-y divide-line rounded-[10px] border border-line">
      {rows.map(([label, value, step]) => (
        <div key={label} className="flex items-start justify-between gap-4 px-4 py-3">
          <div className="min-w-0">
            <dt className="text-xs font-medium uppercase tracking-wide text-muted">{label}</dt>
            <dd className="mt-0.5 break-words text-sm text-ink">{value}</dd>
          </div>
          <button type="button" className="shrink-0 text-sm text-blue hover:underline" onClick={() => onEdit(step)}>
            Edit
          </button>
        </div>
      ))}
    </dl>
  );
}

const RESEND_SECONDS = 60;

/** Step 5: the 6-digit code from the email (D84). */
function ConfirmEmail({ email }: { email: string }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [wait, setWait] = useState(RESEND_SECONDS);
  const [resent, setResent] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => input.current?.focus(), []);
  useEffect(() => {
    if (wait <= 0) return;
    const t = setTimeout(() => setWait((w) => w - 1), 1000);
    return () => clearTimeout(t);
  }, [wait]);

  const verify = async (value: string) => {
    setBusy(true);
    setError(null);
    try {
      await publicJson("/auth/email/verify-code", { method: "POST", body: JSON.stringify({ email, code: value }) });
      setDone(true);
    } catch (err) {
      setError(err);
      setCode("");
      input.current?.focus();
    } finally {
      setBusy(false);
    }
  };
  const resend = async () => {
    setError(null);
    try {
      await publicJson("/auth/email/resend", { method: "POST", body: JSON.stringify({ email }) });
      setResent(true);
      setWait(RESEND_SECONDS);
    } catch (err) {
      setError(err);
    }
  };

  if (done) {
    return (
      <Shell>
        <Card className="p-8 text-center">
          <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-good-bg text-2xl text-good">✓</div>
          <h2 className="mt-4 font-display text-xl font-semibold text-ink">Email confirmed</h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted">
            Sign in to set up two-step sign-in, then add your rooms, team and menu. Diyneco reviews new properties before tablets can take
            orders, usually within one working day.
          </p>
          <a href="/" className="mt-6 inline-flex h-12 items-center rounded-[10px] bg-brand px-6 font-medium text-on-brand hover:opacity-90">
            Sign in
          </a>
        </Card>
      </Shell>
    );
  }

  return (
    <Shell>
      <Card className="p-6 text-center sm:p-8">
        <h2 className="font-display text-xl font-semibold text-ink">Check your email</h2>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted">
          We sent a 6-digit code to <strong className="text-ink">{email}</strong>. It works for 15 minutes.
        </p>
        <form
          className="mx-auto mt-6 flex max-w-xs flex-col gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (code.length === 6) void verify(code);
          }}
        >
          <label htmlFor="otp" className="sr-only">
            6-digit code
          </label>
          <input
            ref={input}
            id="otp"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="\d{6}"
            maxLength={6}
            aria-invalid={error ? true : undefined}
            className={cn(
              "h-14 w-full rounded-[12px] border border-line bg-surface text-center font-mono text-3xl tracking-[0.5em] text-ink",
              "focus:border-blue focus:outline-none aria-[invalid=true]:border-crit",
            )}
            value={code}
            onChange={(e) => {
              const digits = e.target.value.replace(/\D/g, "").slice(0, 6);
              setCode(digits);
              if (digits.length === 6 && !busy) void verify(digits);
            }}
          />
          {error ? <ErrorNotice error={error} /> : null}
          <Button type="submit" size="lg" loading={busy} disabled={code.length !== 6}>
            Confirm email
          </Button>
        </form>
        <p className="mt-6 text-sm text-muted">
          No email? Check spam, or{" "}
          {wait > 0 ? (
            <span>send a new code in {wait} s</span>
          ) : (
            <button type="button" className="text-blue hover:underline" onClick={() => void resend()}>
              send a new code
            </button>
          )}
          .
        </p>
        {resent ? <p className="mt-2 text-xs text-good">A new code is on its way. Earlier codes no longer work.</p> : null}
        <p className="mt-4 text-xs text-muted">The email also has a link that confirms your address if you prefer.</p>
      </Card>
    </Shell>
  );
}
