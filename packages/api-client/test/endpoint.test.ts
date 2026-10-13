// Choosing the API address at start-up (D81) and clients created before the choice.
import assert from "node:assert/strict";
import { test } from "node:test";

import { createApi } from "../src/client.ts";
import { chooseApiUrl } from "../src/endpoint.ts";

function browser(up: Set<string>): string[] {
  const calls: string[] = [];
  const store = new Map<string, string>();
  Object.assign(globalThis, {
    window: { sessionStorage: { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => store.set(k, v) } },
  });
  globalThis.fetch = (async (url: string) => {
    calls.push(url);
    if (![...up].some((u) => url.startsWith(u))) throw new TypeError("unreachable");
    return new Response("{}", { status: 200 });
  }) as typeof fetch;
  return calls;
}

test("the primary address is used when it answers", async () => {
  const calls = browser(new Set(["https://api.diyneco.com"]));
  assert.equal(await chooseApiUrl(["https://api.diyneco.com/", "https://x.up.railway.app"]), "https://api.diyneco.com");
  assert.deepEqual(calls, ["https://api.diyneco.com/api/v1/health"]);
});

test("the fallback is used when the primary does not answer, and remembered for the tab", async () => {
  const calls = browser(new Set(["https://x.up.railway.app"]));
  const list = ["https://api.diyneco.com", "https://x.up.railway.app"];
  assert.equal(await chooseApiUrl(list), "https://x.up.railway.app");
  assert.equal(await chooseApiUrl(list), "https://x.up.railway.app");
  assert.equal(calls.length, 2); // the second start did not check again
});

test("with nothing answering, the primary is kept; one address is never checked", async () => {
  const calls = browser(new Set());
  assert.equal(await chooseApiUrl(["https://a.example", "https://b.example"]), "https://a.example");
  calls.length = 0;
  assert.equal(await chooseApiUrl(["https://a.example", ""]), "https://a.example");
  assert.deepEqual(calls, []);
});

test("a client created before the choice sends to the chosen address", async () => {
  let current = "https://api.diyneco.com";
  const seen: string[] = [];
  const api = createApi({
    baseUrl: () => current,
    getToken: () => null,
    fetch: async (req: Request) => {
      seen.push(req.url);
      return new Response(JSON.stringify({ status: "ok" }), { status: 200, headers: { "content-type": "application/json" } });
    },
  });
  current = "https://x.up.railway.app";
  await api.GET("/api/v1/health" as never);
  assert.deepEqual(seen, ["https://x.up.railway.app/api/v1/health"]);
});
