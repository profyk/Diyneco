// Display helpers: amounts parse and format exactly for every currency and locale (D69).
// Run with `pnpm test` (Node's built-in test runner; Node 24 strips the types).
import assert from "node:assert/strict";
import { test } from "node:test";

import { formatDate, formatMoney, formatTime, parseAmount, setDisplayLocale } from "../src/money.ts";

function parses(locale: string, cases: [string, string, number | null][]): void {
  setDisplayLocale(locale);
  for (const [text, currency, want] of cases) {
    assert.equal(parseAmount(text, currency), want, `${locale} ${text} ${currency}`);
  }
}

test("amounts typed with a dot as the decimal sign", () => {
  parses("en-US", [
    ["125.50", "ZAR", 12550],
    ["1,200", "ZAR", 120000],
    ["1,234.50", "ZAR", 123450],
    ["R 1 850.05", "ZAR", 185005],
    ["12,5", "ZAR", 1250],
    ["0", "ZAR", 0],
    ["12.345", "ZAR", null],
    ["-5", "ZAR", null],
    ["abc", "ZAR", null],
    ["1500", "JPY", 1500],
    ["1,500", "JPY", 1500],
    ["15.5", "JPY", null],
    ["2.125", "BHD", 2125],
    ["1,200", "BHD", 1200000],
  ]);
});

test("amounts typed with a comma as the decimal sign", () => {
  parses("de-DE", [
    ["1.234,50", "EUR", 123450],
    ["1234,5", "EUR", 123450],
    ["12.50", "EUR", 1250],
    ["1.200", "EUR", 120000],
    ["1,200", "BHD", 1200],
    ["1.200", "BHD", 1200000],
  ]);
  parses("fr-FR", [["1 234,50", "EUR", 123450]]);
  parses("en-ZA", [
    ["125.50", "ZAR", 12550],
    ["125,50", "ZAR", 12550],
    ["1 850", "ZAR", 185000],
  ]);
});

test("formatting follows the hotel's locale and time zone", () => {
  setDisplayLocale("de-DE", "Pacific/Auckland");
  assert.equal(formatMoney({ amount_minor: 123450, currency: "EUR" }).replace(/\s/g, " "), "1.234,50 €");
  assert.equal(formatMoney({ amount_minor: 1500, currency: "JPY" }).replace(/\s/g, " "), "1.500 ¥");
  assert.equal(formatTime("2026-10-12T06:30:00Z"), "19:30");
  // A business date is a calendar day and never moves with the time zone.
  assert.equal(formatDate("2026-10-12"), "12. Okt. 2026");
  setDisplayLocale("en-US", "UTC");
  assert.equal(formatMoney({ amount_minor: 2125, currency: "BHD" }).replace(/\s/g, " "), "BHD 2.125");
  // Unknown values fall back instead of breaking every screen.
  setDisplayLocale("not a locale", "Mars/Base");
  assert.match(formatMoney({ amount_minor: 100, currency: "USD" }), /1\.00/);
});
