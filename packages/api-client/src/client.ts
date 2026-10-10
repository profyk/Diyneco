/**
 * Typed client for the Diyneco API, shared by every app.
 *
 * - Types come from the backend's OpenAPI document (`@diyneco/shared-types`), so a request or
 *   response that does not match the API fails to compile.
 * - Every state-changing request carries an Idempotency-Key. The key is created once per call
 *   and reused when the request is retried after a network failure, so a retry can never
 *   charge, pay or order twice.
 * - A 401 triggers one silent token refresh and a single retry.
 * - A 403 STEP_UP_REQUIRED asks the app for a PIN or password (`stepUp`), then retries once
 *   with the short-lived step-up token.
 * - Errors arrive as `ApiError` with the server's code, message, request id and details;
 *   the server's message is already written for people.
 */
import createFetchClient from "openapi-fetch";
import type { paths } from "@diyneco/shared-types";

export interface ErrorBody {
  code: string;
  message: string;
  request_id: string | null;
  details: Record<string, unknown>;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;
  readonly details: Record<string, unknown>;

  constructor(status: number, body: ErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.requestId = body.request_id;
    this.details = body.details ?? {};
  }
}

export class NetworkError extends Error {
  constructor(cause: unknown) {
    super("You appear to be offline. Check the connection and try again.");
    this.name = "NetworkError";
    this.cause = cause;
  }
}

export interface ClientOptions {
  /** API origin, for example "https://api.diyneco.com" (no trailing /api/v1). */
  baseUrl: string;
  /** Current access token, or null when signed out. */
  getToken: () => string | null;
  /** Gets a new access token after a 401; null means the session is over. */
  refresh?: () => Promise<string | null>;
  /** Called when the session cannot be refreshed. */
  onSignedOut?: () => void;
  /** Asks the person for their PIN or password and returns a step-up token, or null if cancelled. */
  stepUp?: () => Promise<string | null>;
  /** Extra headers on every request (for example a device token's hotel). */
  headers?: () => Record<string, string>;
  /** Send cookies (web apps use the httpOnly refresh cookie). */
  credentials?: RequestCredentials;
  /** Network retries for idempotent-safe requests (default 2). */
  retries?: number;
  fetch?: typeof fetch;
}

const MUTATING = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  // React Native without crypto.randomUUID: RFC 4122 v4 from Math.random is enough for a
  // client-generated de-duplication key (it is scoped to the caller on the server).
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

async function readError(res: Response): Promise<ErrorBody> {
  try {
    const body = (await res.clone().json()) as { error?: ErrorBody };
    if (body?.error?.code) return body.error;
  } catch {
    /* not JSON */
  }
  return { code: res.status >= 500 ? "INTERNAL_ERROR" : "UNKNOWN", message: "Something went wrong.", request_id: res.headers.get("X-Request-Id"), details: {} };
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function createApi(options: ClientOptions) {
  const baseFetch = options.fetch ?? globalThis.fetch.bind(globalThis);
  const retries = options.retries ?? 2;
  let refreshing: Promise<string | null> | null = null;

  async function send(request: Request, attempt = 0): Promise<Response> {
    try {
      return await baseFetch(request.clone());
    } catch (err) {
      // Only network failures are retried; the Idempotency-Key makes this safe for writes.
      if (attempt < retries) {
        await wait(400 * 2 ** attempt + Math.random() * 200);
        return send(request, attempt + 1);
      }
      throw new NetworkError(err);
    }
  }

  function withHeaders(request: Request, extra: Record<string, string>): Request {
    const headers = new Headers(request.headers);
    for (const [k, v] of Object.entries(extra)) headers.set(k, v);
    return new Request(request, { headers });
  }

  async function authedFetch(input: Request): Promise<Response> {
    let request = input;
    const extra: Record<string, string> = { ...(options.headers?.() ?? {}) };
    const token = options.getToken();
    if (token) extra.Authorization = `Bearer ${token}`;
    if (MUTATING.has(request.method) && !request.headers.has("Idempotency-Key")) {
      extra["Idempotency-Key"] = newIdempotencyKey();
    }
    request = withHeaders(request, extra);
    let res = await send(request);

    if (res.status === 401 && options.refresh && token) {
      refreshing ??= options.refresh().finally(() => {
        refreshing = null;
      });
      const fresh = await refreshing;
      if (!fresh) {
        options.onSignedOut?.();
        return res;
      }
      request = withHeaders(request, { Authorization: `Bearer ${fresh}` });
      res = await send(request);
    }

    if (res.status === 403 && options.stepUp) {
      const body = await readError(res);
      if (body.code === "STEP_UP_REQUIRED") {
        const stepUpToken = await options.stepUp();
        if (stepUpToken) res = await send(withHeaders(request, { "X-Step-Up": stepUpToken }));
      }
    }
    return res;
  }

  const client = createFetchClient<paths>({
    baseUrl: options.baseUrl.replace(/\/$/, ""),
    credentials: options.credentials ?? "omit",
    fetch: authedFetch,
  });

  return client;
}

export type Api = ReturnType<typeof createApi>;

/**
 * Unwraps an openapi-fetch result: returns the data, or throws ApiError with the server's
 * envelope. Use it as `const rooms = await ok(api.GET("/api/v1/rooms"))`.
 */
export async function ok<T>(
  promise: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await promise;
  if (response.ok) return data as T;
  const body = (error as { error?: ErrorBody } | undefined)?.error ?? (await readError(response));
  throw new ApiError(response.status, body);
}

/** True when the request was answered from the server's idempotency store (a safe retry). */
export function wasReplayed(response: Response): boolean {
  return response.headers.get("Idempotent-Replayed") === "true";
}
