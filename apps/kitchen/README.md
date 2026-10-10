# Kitchen display

Next.js app for the kitchen display (build spec, Kitchen; API spec, Kitchen).

- **Pairing:** a manager creates a kitchen-display code in the Merchant app (Devices); the
  display enters it once and keeps its device credential.
- **Board:** New → Accepted → Preparing lanes, oldest first, no prices; tickets turn amber at
  15 minutes and red at 25; items are marked ready per station and an order is ready only
  when every item is. Live over the WebSocket, with 10-second polling while offline.
- **People:** reading the board needs no sign-in; every action asks for a cook's PIN once and
  is recorded against them (8-hour session bound to this display).
- **Kitchen-friendly:** 64 px touch targets, high-visibility mode, a chime for new orders,
  full screen, heartbeat with manager commands (lock, reset).

```
cp .env.example .env.local   # NEXT_PUBLIC_API_URL
pnpm dev                     # http://localhost:3002
```

Add `http://localhost:3002` to the backend's `CORS_ALLOWED_ORIGINS`.
