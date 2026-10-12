import { expect, test } from "@playwright/test";

import { accounts, ADMIN_URL, API_URL, confirmIfAsked, signIn, signInAdmin } from "./accounts";

test("a hotel account cannot sign in to the Admin panel", async ({ page }) => {
  await page.goto(ADMIN_URL);
  await signIn(page, accounts.receptionist.email, accounts.receptionist.password);
  await expect(page.getByText(/Email or password is incorrect/)).toBeVisible();
});

test("a Super Admin prices, previews and publishes a plan, then signs out", async ({ page, request }) => {
  await signInAdmin(page);

  await page.getByRole("link", { name: "Plans & Pricing" }).first().click();
  await expect(page.getByRole("heading", { name: "Plans & Pricing" })).toBeVisible();
  await expect(page.getByRole("cell", { name: /Starter/ })).toBeVisible();

  const code = `e2e_${Date.now().toString(36)}`;
  await page.getByRole("button", { name: "New plan" }).click();
  const create = page.getByRole("dialog", { name: "New plan" });
  await create.getByLabel(/^Code/).fill(code);
  await create.getByLabel("Name", { exact: true }).fill(`E2E ${code}`);
  await create.getByLabel("Billing currency").selectOption("ZAR");
  await create.getByRole("button", { name: "Create draft" }).click();
  await expect(create).toBeHidden();

  const row = page.getByRole("row", { name: new RegExp(code) });
  await row.getByRole("button", { name: "Prices" }).click();
  const prices = page.getByRole("dialog", { name: /prices/ });
  for (const [interval, amount] of [
    ["month", "499"],
    ["year", "4990"],
  ]) {
    await prices.getByLabel("Billing interval").selectOption(interval);
    await prices.getByLabel(/^Price per/).fill(amount);
    await prices.getByLabel("Reason", { exact: true }).fill("E2E price");
    await prices.getByRole("button", { name: "Save price" }).click();
    await confirmIfAsked(page, accounts.admin.password);
    await expect(prices.getByLabel(/^Price per/)).toHaveValue("");
  }
  await expect(prices.getByText(/4[\s,. ]?990[.,]00/).first()).toBeVisible();
  await page.keyboard.press("Escape");

  await row.getByRole("button", { name: "Preview" }).click();
  const preview = page.getByRole("dialog", { name: "Preview" });
  await expect(preview.getByText(/Save 16%/)).toBeVisible();
  await page.keyboard.press("Escape");

  await row.getByRole("button", { name: "Publish" }).click();
  const publish = page.getByRole("dialog", { name: "Publish plan" });
  await publish.getByLabel("Reason").fill("E2E launch");
  await publish.getByRole("button", { name: "Publish" }).click();
  await confirmIfAsked(page, accounts.admin.password);
  await expect(row.getByText("Published")).toBeVisible();

  const listed = await (await request.get(`${API_URL}/api/v1/plans`)).json();
  const plan = listed.data.find((p: { code: string }) => p.code === code);
  expect(plan.prices.map((p: { interval: string }) => p.interval)).toEqual(["month", "year"]);

  // Archive it again so the demo catalogue stays as seeded.
  await row.getByRole("button", { name: "Archive" }).click();
  const archive = page.getByRole("dialog", { name: "Archive plan" });
  await archive.getByLabel("Reason").fill("E2E clean-up");
  await archive.getByRole("button", { name: "Archive" }).click();
  await confirmIfAsked(page, accounts.admin.password);
  await expect(row.getByText("Archived")).toBeVisible();

  await page.getByRole("link", { name: "Company & tax" }).first().click();
  await expect(page.getByLabel("Legal company name")).toHaveValue("Diyneco Tech (Pty) Ltd");

  await page.getByRole("link", { name: "Diyneco staff" }).first().click();
  await expect(page.getByText(accounts.admin.email)).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).first().click();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible(); // the session really ended
});
