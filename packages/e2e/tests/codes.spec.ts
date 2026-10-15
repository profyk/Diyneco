import { expect, type Locator, type Page, test } from "@playwright/test";

import {
  accounts,
  confirmIfAsked,
  GUEST_URL,
  KITCHEN_URL,
  MERCHANT_URL,
  ROOM_SERVICE_URL,
  signInOwner,
} from "./accounts";

// D82: the guest, kitchen and room-service apps start from the hotel's Hotel ID, an 8-digit
// code and a PIN. The owner creates the codes in the Merchant app; the code is read off the
// screen exactly as a person would.

async function readCode(dialog: Locator, label: string): Promise<string> {
  const value = dialog.getByText(label, { exact: true }).locator("xpath=following-sibling::p[1]");
  return (await value.innerText()).replace(/\s/g, "");
}

async function setUpDevice(page: Page, kind: "Room tablet" | "Kitchen display"): Promise<{ hotelCode: string; code: string }> {
  await page.goto(`${MERCHANT_URL}/devices`);
  await page.getByRole("button", { name: "Set up a device" }).click();
  const dialog = page.getByRole("dialog", { name: "Set up a device" });
  await dialog.getByLabel("Device").selectOption({ label: kind });
  if (kind === "Room tablet") await dialog.getByLabel("Room").selectOption({ label: accounts.room });
  else await dialog.getByLabel("Kitchen station").selectOption({ index: 1 });
  await dialog.getByRole("button", { name: "Create setup code" }).click();
  await expect(dialog.getByText("Setup code", { exact: true })).toBeVisible();
  const hotelCode = await readCode(dialog, "Hotel ID");
  const code = await readCode(dialog, "Setup code");
  expect(hotelCode).toBe(accounts.hotel_code);
  expect(code).toMatch(/^\d{8}$/);
  await dialog.getByRole("button", { name: "Done" }).click();
  return { hotelCode, code };
}

async function fillSetup(page: Page, hotelCode: string, code: string, pin: string) {
  await page.waitForLoadState("networkidle");
  await expect(page.getByRole("img", { name: "Diyneco" })).toBeVisible(); // the logo on the set-up screen
  // Typed loosely, as on a tablet keyboard: lower case, without the dash.
  await page.getByLabel("Hotel ID").fill(hotelCode.toLowerCase().replace("-", ""));
  await page.getByLabel("Setup code").fill(code);
  await page.getByLabel("Manager PIN", { exact: true }).fill(pin);
}

test("a staff code signs a room-service member in with the Hotel ID and their PIN", async ({ page, browser }) => {
  await signInOwner(page);
  await page.goto(`${MERCHANT_URL}/staff`);
  const row = page.getByRole("row").filter({ hasText: accounts.room_service });
  await row.getByRole("button", { name: /Staff code|New staff code/ }).click();
  await confirmIfAsked(page, accounts.pin);
  const dialog = page.getByRole("dialog", { name: /Staff code for/ });
  await expect(dialog).toBeVisible();
  const hotelCode = await readCode(dialog, "Hotel ID");
  const staffCode = await readCode(dialog, "Staff code");
  expect(hotelCode).toBe(accounts.hotel_code);
  expect(staffCode).toMatch(/^\d{8}$/);
  await dialog.getByRole("button", { name: "Done" }).click();
  await expect(row.getByText("Staff code", { exact: true })).toBeVisible();

  const runner = await (await browser.newContext()).newPage();
  await runner.goto(ROOM_SERVICE_URL);
  await runner.waitForLoadState("networkidle");
  await expect(runner.getByRole("img", { name: "Diyneco" })).toBeVisible();
  await runner.getByLabel("Hotel ID").fill(hotelCode);
  await runner.getByLabel("Staff code").fill(staffCode);
  await runner.getByLabel("PIN", { exact: true }).fill("9999");
  await runner.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(runner.getByText(/That PIN is not correct/)).toBeVisible();
  await runner.getByLabel("PIN", { exact: true }).fill(accounts.pin);
  await runner.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(runner.getByRole("button", { name: "Sign out" }).first()).toBeAttached();
});

test("a kitchen display is set up with the Hotel ID, a setup code and the manager's PIN", async ({ page, browser }) => {
  await signInOwner(page);
  const { hotelCode, code } = await setUpDevice(page, "Kitchen display");
  const display = await (await browser.newContext()).newPage();
  await display.goto(KITCHEN_URL);
  await fillSetup(display, hotelCode, code, "9999");
  await display.getByRole("button", { name: "Set up display" }).click();
  await expect(display.getByText(/That PIN is not correct/)).toBeVisible(); // the code survives a wrong PIN
  await display.getByLabel("Manager PIN", { exact: true }).fill(accounts.pin);
  await display.getByRole("button", { name: "Set up display" }).click();
  await expect(display.getByRole("heading", { name: "Kitchen" })).toBeVisible();
});

test("a room tablet is set up the same way and opens on its room", async ({ page, browser }) => {
  await signInOwner(page);
  const { hotelCode, code } = await setUpDevice(page, "Room tablet");
  const tablet = await (await browser.newContext()).newPage();
  await tablet.goto(GUEST_URL);
  await fillSetup(tablet, hotelCode, code, accounts.pin);
  await tablet.getByRole("button", { name: "Set up tablet" }).click();
  await expect(tablet.getByText(`Room ${accounts.room}`)).toBeVisible();
});
