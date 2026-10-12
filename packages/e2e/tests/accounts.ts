import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { type Locator, type Page } from "@playwright/test";
import { TOTP } from "otpauth";

export const ADMIN_URL = process.env.ADMIN_URL ?? "http://localhost:3003";
export const MERCHANT_URL = process.env.MERCHANT_URL ?? "http://localhost:3001";
export const API_URL = process.env.API_URL ?? "http://localhost:8000";

export const accounts = JSON.parse(readFileSync(fileURLToPath(new URL("../.accounts.json", import.meta.url)), "utf8")) as {
  admin: { email: string; password: string; totp_secret: string };
  receptionist: { email: string; password: string };
  pin: string;
};

export function totp(secret: string): string {
  return new TOTP({ secret, digits: 6, period: 30 }).generate();
}

export async function signIn(page: Page, email: string, password: string): Promise<void> {
  // Typing before the page has hydrated would be wiped by React; wait for the app to settle.
  await page.waitForLoadState("networkidle");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

export async function signInAdmin(page: Page): Promise<void> {
  await page.goto(ADMIN_URL);
  await signIn(page, accounts.admin.email, accounts.admin.password);
  await page.getByLabel("Code").fill(totp(accounts.admin.totp_secret));
  await page.getByRole("button", { name: "Verify" }).click();
  await page.getByRole("link", { name: "Plans & Pricing" }).first().waitFor();
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
