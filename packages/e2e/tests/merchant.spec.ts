import { expect, test } from "@playwright/test";

import { accounts, MERCHANT_URL, signIn } from "./accounts";

test("a Diyneco staff account cannot sign in to the Merchant app", async ({ page }) => {
  await page.goto(MERCHANT_URL);
  await signIn(page, accounts.admin.email, accounts.admin.password);
  await expect(page.getByText(/Email or password is incorrect/)).toBeVisible();
});

test("hotel staff sign in and sign out of the Merchant app", async ({ page }) => {
  await page.goto(MERCHANT_URL);
  await signIn(page, accounts.receptionist.email, accounts.receptionist.password);
  const signOut = page.getByRole("button", { name: "Sign out" }).first();
  await expect(signOut).toBeAttached();
  if (!(await signOut.isVisible())) await page.getByRole("button", { name: /Menu/ }).click();
  await signOut.click();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible(); // the session really ended
});
