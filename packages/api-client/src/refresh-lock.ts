// Refresh tokens rotate on every use, and the server treats a second use of the same token as a
// stolen-token replay: it ends the whole session. So two refreshes must never overlap.
//
// - In one tab, callers that ask while a refresh is running share its result.
// - Across tabs of the same app, the Web Locks API runs them one after another; a later tab
//   then sends the cookie the earlier one already rotated, which is valid.

const running = new Map<string, Promise<unknown>>();

type Locks = { request: <T>(name: string, cb: () => Promise<T>) => Promise<T> };

function locks(): Locks | null {
  const nav = typeof navigator === "undefined" ? undefined : (navigator as Navigator & { locks?: Locks });
  return nav?.locks ?? null;
}

/**
 * Runs `refresh` at most once at a time for `key` (the app and the requested hotel). Callers
 * arriving while it runs get the same promise.
 */
export function singleRefresh<T>(key: string, refresh: () => Promise<T>): Promise<T> {
  const current = running.get(key) as Promise<T> | undefined;
  if (current) return current;
  const l = locks();
  const task = (l ? l.request(`diyneco-refresh:${key.split("|")[0]}`, refresh) : refresh()).finally(() => {
    running.delete(key);
  });
  running.set(key, task);
  return task;
}
