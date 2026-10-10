# Room-service app

Mobile-first web app for room-service staff phones (installable full screen): sign in
(two-step when the role needs it), "Ready to collect" and "My deliveries" that update live
(with a vibration when an order is ready), claim, release, picked up, delivered, leave on the
room bill, or take payment, where the server computes what is due and any tip, which the
guest must confirm. Card numbers are never entered; card payments record the card machine's
reference only.

```
cp .env.example .env.local   # NEXT_PUBLIC_API_URL
pnpm dev                     # http://localhost:3004 (open on a phone on the same network)
```

Add the app's origin to the backend's `CORS_ALLOWED_ORIGINS`.
