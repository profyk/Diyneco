/**
 * Chooses the API address when an app starts (DECISIONS D81): the first candidate whose health
 * check answers, so a primary address (api.diyneco.com) can fall back to another (the Railway
 * address) while DNS is not ready or the primary is unreachable. The choice is kept for the
 * browser tab. With one candidate nothing is checked.
 */
export async function chooseApiUrl(candidates: string[], timeoutMs = 4000): Promise<string> {
  const list = [...new Set(candidates.map((c) => c.trim().replace(/\/$/, "")).filter(Boolean))];
  const first = list[0] ?? "";
  if (list.length < 2 || typeof window === "undefined") return first;
  const key = `diyneco.api:${list.join(",")}`;
  try {
    const saved = window.sessionStorage.getItem(key);
    if (saved && list.includes(saved)) return saved;
  } catch {
    // Storage blocked: check again each time.
  }
  for (const url of list) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const res = await fetch(`${url}/api/v1/health`, { signal: ctrl.signal, credentials: "omit", cache: "no-store" });
      if (res.ok) {
        try {
          window.sessionStorage.setItem(key, url);
        } catch {
          // Not remembered; harmless.
        }
        return url;
      }
    } catch {
      // Unreachable: try the next address.
    } finally {
      clearTimeout(timer);
    }
  }
  return first;
}
