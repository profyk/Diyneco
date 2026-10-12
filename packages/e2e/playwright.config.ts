import { defineConfig } from "@playwright/test";

// Browser end-to-end tests against a running API and apps with development data
// (scripts/seed_dev.py, then scripts/seed_e2e.py > .accounts.json). Locally they use the
// installed Chrome; CI installs Playwright's Chromium (E2E_BROWSER=chromium).
export default defineConfig({
  testDir: "tests",
  timeout: 120_000,
  expect: { timeout: 20_000 },
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["list"]] : [["list"]],
  use: {
    channel: process.env.E2E_BROWSER === "chromium" ? undefined : "chrome",
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
