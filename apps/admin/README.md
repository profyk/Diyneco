# Admin panel

Diyneco staff only (platform accounts with two-step sign-in): overview with metrics,
MRR per billing currency and 30-day activity, hotels (approve, suspend, reactivate,
subscriptions, time-boxed read-only support access), plans with their billing currency,
feature flags and health. It shows aggregates only; guest data is never reachable.

```
cp .env.example .env.local   # NEXT_PUBLIC_API_URL
pnpm dev                     # http://localhost:3003
```
