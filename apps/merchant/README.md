# Merchant app

The hotel's control centre (Next.js): Today, orders and phone orders, approvals, stays with
check-in, bills, payments, checkout and invoices, rooms, guests, menu, payments, reports and
the daily close, staff and roles, devices and pairing, settings (VAT, integrations, plan,
Diyneco support access, audit log), plus hotel signup, invitations and password reset.

- Signs in with email and password, two-step codes for roles that need them; the access
  token stays in memory and the refresh token in the API's httpOnly cookie.
- Shows only what the person's permissions allow (`GET /auth/me`); the API still checks.
- Sensitive actions ask for a PIN automatically when the API answers `STEP_UP_REQUIRED`.
- Live over the WebSocket: screens refresh as orders, payments and stays change.

```
cp .env.example .env.local   # NEXT_PUBLIC_API_URL
pnpm dev                     # http://localhost:3001
```

Add `http://localhost:3001` to the backend's `CORS_ALLOWED_ORIGINS`.
