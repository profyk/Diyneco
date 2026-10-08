## What changed

## Checklist

- [ ] Tests added or updated (tenancy, permissions, money, idempotency and state changes have tests)
- [ ] New tables with `hotel_id` have RLS in the same migration; financial tables are append-only
- [ ] New endpoints, permissions, events and error codes match the specs, or a spec change is proposed
- [ ] Decisions the specs did not make are recorded in `docs/DECISIONS.md`
- [ ] `pnpm gen:types` run if the API changed
