import { readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { type Locator, type Page } from "@playwright/test";
import { TOTP } from "otpauth";

export const ADMIN_URL = process.env.ADMIN_URL ?? "http://localhost:3003";
export const MERCHANT_URL = process.env.MERCHANT_URL ?? "http://localhost:3001";
export const API_URL = process.env.API_URL ?? "http://localhost:8000";
export const KITCHEN_URL = process.env.KITCHEN_URL ?? "http://localhost:3002";
export const ROOM_SERVICE_URL = process.env.ROOM_SERVICE_URL ?? "http://localhost:3004";
export const GUEST_URL = process.env.GUEST_URL ?? "http://localhost:3005";

export const accounts = JSON.parse(readFileSync(fileURLToPath(new URL("../.accounts.json", import.meta.url)), "utf8")) as {
  admin: { email: string; password: string; totp_secret: string };
  receptionist: { email: string; password: string };
  owner: { email: string; password: string; totp_secret: string };
  plan: { code: string; name: string };
  pin: string;
  hotel_code: string; // the demo hotel's Hotel ID (D82)
  room: string; // a room with no tablet
  room_service: string; // email of the demo room-service staff member
};

export function totp(secret: string): string {
  return new TOTP({ secret, digits: 6, period: 30 }).generate();
}

// The API refuses a code whose 30-second step was already used (replay protection), and the
// suite signs the same accounts in more than once: wait for a step not used yet.
// Kept in a file: Playwright starts a new worker process after a failed test.
const STEPS_FILE = join(tmpdir(), "diyneco-e2e-totp-steps.json");
function usedSteps(): Record<string, number> {
  try {
    return JSON.parse(readFileSync(STEPS_FILE, "utf8")) as Record<string, number>;
  } catch {
    return {};
  }
}
export async function freshTotp(secret: string): Promise<string> {
  const step = () => Math.floor(Date.now() / 30_000);
  const last = usedSteps()[secret] ?? -1;
  while (step() <= last) await new Promise((r) => setTimeout(r, 500));
  writeFileSync(STEPS_FILE, JSON.stringify({ ...usedSteps(), [secret]: step() }));
  return totp(secret);
}

export async function signIn(page: Page, email: string, password: string): Promise<void> {
  // Typing before the page has hydrated would be wiped by React; wait for the app to settle.
  await page.waitForLoadState("networkidle");
  for (let attempt = 0; attempt < 2; attempt++) {
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    // The API allows 10 sign-ins a minute per address; the whole suite signs in from one.
    // Wait the window out once rather than loosening the limit for tests.
    const limited = page.getByText(/Too many requests/);
    try {
      await limited.waitFor({ state: "visible", timeout: 3_000 });
    } catch {
      return;
    }
    await page.waitForTimeout(61_000);
  }
}

/**
 * The two-step code, sent once more after waiting out the per-address limit if the API says
 * "Too many requests" (the code step counts toward the same 10-a-minute limit as the password,
 * and the whole suite signs in from one address).
 */
async function verifyCode(page: Page, secret: string, signedIn: Locator): Promise<void> {
  for (let attempt = 0; attempt < 2; attempt++) {
    await page.getByLabel("Code").fill(await freshTotp(secret));
    await page.getByRole("button", { name: "Verify" }).click();
    const limited = page.getByText(/Too many requests/);
    const outcome = await Promise.race([
      signedIn.waitFor({ state: "attached", timeout: 30_000 }).then(() => "in" as const),
      limited.waitFor({ state: "visible", timeout: 30_000 }).then(() => "limited" as const),
    ]).catch(() => "unknown" as const);
    if (outcome !== "limited") return;
    await page.waitForTimeout(61_000);
  }
}

export async function signInAdmin(page: Page): Promise<void> {
  await page.goto(ADMIN_URL);
  await signIn(page, accounts.admin.email, accounts.admin.password);
  const nav = page.getByRole("link", { name: "Plans & Pricing" }).first();
  await verifyCode(page, accounts.admin.totp_secret, nav);
  await nav.waitFor();
}

export async function signInOwner(page: Page): Promise<void> {
  await page.goto(MERCHANT_URL);
  await signIn(page, accounts.owner.email, accounts.owner.password);
  const signOut = page.getByRole("button", { name: "Sign out" }).first();
  await verifyCode(page, accounts.owner.totp_secret, signOut);
  await signOut.waitFor({ state: "attached" });
}

/** Answers the confirmation dialog if it appears. */
export async function confirmIfAsked(page: Page, secret: string): Promise<void> {
  const dialog = page.getByRole("dialog", { name: /Confirm it/ });
  try {
    await dialog.waitFor({ state: "visible", timeout: 10_000 });
  } catch {
    return; // still confirmed from an earlier step-up
  }
  await dialog.getByLabel(/Password|PIN/).fill(secret);
  await dialog.getByRole("button", { name: "Confirm" }).click();
  await dialog.waitFor({ state: "hidden" });
}

/** Waits until `done` holds; if the page shows an error first, fails with its text. */
export async function expectNoErrorUntil(scope: Locator, done: () => Promise<boolean>, timeoutMs = 30_000): Promise<void> {
  const until = Date.now() + timeoutMs;
  while (Date.now() < until) {
    if (await done()) return;
    const alert = scope.getByRole("alert").first();
    if (await alert.isVisible().catch(() => false)) throw new Error(`The page showed an error: ${await alert.innerText()}`);
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error("Timed out waiting for the action to finish");
}
