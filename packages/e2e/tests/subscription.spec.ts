import { expect, test } from "@playwright/test";

import { accounts, ADMIN_URL, confirmIfAsked, MERCHANT_URL, signInAdmin, signInOwner } from "./accounts";

// The subscription journey (DECISIONS D79): a hotel on a free trial chooses a published plan,
// sees the server's total, accepts the terms, gets its first invoice, pays it through the
// clearly labelled sandbox (no money moves) and is active; Diyneco's billing dashboard lists it.
test("a hotel subscribes, pays its first invoice in the sandbox and becomes active", async ({ page }) => {
  // Two sign-ins (owner, then admin), each of which may wait out the 10-a-minute limit (61 s).
  test.setTimeout(300_000);
  await signInOwner(page);
  await page.goto(`${MERCHANT_URL}/settings?tab=plan`);
  await expect(page.getByText("Free trial").first()).toBeVisible();

  const card = page.locator("div").filter({ has: page.getByText(accounts.plan.name, { exact: true }) }).last();
  await card.getByRole("button", { name: "Choose this plan" }).click();
  const subscribe = page.getByRole("dialog", { name: `Subscribe to ${accounts.plan.name}` });
  await expect(subscribe.getByText("Total due today")).toBeVisible();
  await expect(subscribe.getByText(/499[.,]00/).first()).toBeVisible();
  await subscribe.getByRole("checkbox").check();
  await subscribe.getByRole("button", { name: "Subscribe and get invoice" }).click();
  await confirmIfAsked(page, accounts.pin); // the Merchant app confirms with the PIN

  const pay = page.getByRole("dialog", { name: /Pay invoice/ });
  await expect(pay.getByText(/Test mode/)).toBeVisible();
  await pay.getByRole("button", { name: /online/ }).click();

  await page.waitForURL(/\/billing\/return\?attempt=/);
  await expect(page.getByText(/Test mode: no real money moves/)).toBeVisible();
  await page.getByRole("button", { name: "Simulate a successful payment" }).click();
  await expect(page.getByText("Payment received. Thank you.")).toBeVisible();

  await page.getByRole("link", { name: /Back to your plan/ }).click();
  await expect(page.getByText(accounts.plan.name).first()).toBeVisible();
  await expect(page.getByText("Active").first()).toBeVisible();
  await expect(page.getByRole("cell", { name: /Test payment/ })).toBeVisible();

  await page.context().clearCookies();
  await signInAdmin(page);
  await page.goto(`${ADMIN_URL}/billing`);
  await page.getByRole("tab", { name: "Invoices" }).click();
  await page.getByLabel("Hotel, account ID or number").fill("Grand Example");
  await expect(page.getByRole("cell", { name: "Paid" }).first()).toBeVisible();
});
