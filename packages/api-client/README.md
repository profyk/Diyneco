# api-client

Typed client for the Diyneco API shared by every app: `createApi` (bearer token, silent
refresh, step-up retry, stable idempotency keys across retries, `ApiError` from the error
envelope), `ok()` to unwrap results, money and time formatting, and `connectRealtime` for
the WebSocket gateway.
