# Deployment and launch

This guide is provider-neutral. **Two decisions are still open and block production:** the
hosting provider for the API and worker containers, and the Supabase project region (choose
the region closest to South Africa that the chosen plan offers, and confirm point-in-time
recovery is available on it). Everything below works the same on any container host.

## What runs where

| Component | How it runs | Notes |
| --- | --- | --- |
| API | `backend/Dockerfile`, command `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --proxy-headers` | Stateless; run at least 2 instances behind TLS. WebSockets at `/api/v1/ws` must be allowed by the load balancer (idle timeout above 60 s). |
| Worker | same image, command `python -m app.worker` | Exactly one instance per environment is enough; it is safe to run two (deliveries are claimed with `SKIP LOCKED`). |
| Database | Supabase Postgres 15+ | Run `infra/db/bootstrap.sql` once as the Supabase `postgres` role, then `alembic upgrade head` as `diyneco_owner`. Schema `app` must never be exposed through the Supabase REST API. |
| Storage | Supabase Storage, private buckets `hotel-assets` and `invoices` | Second, separately keyed copy in another region (operations runbook, backups). |
| Redis | any managed Redis 7 | Rate limits across instances; required outside development. |
| Web apps | Next.js (Merchant, Kitchen, Admin) | Static hosting or Node; they only need `NEXT_PUBLIC_API_URL`. |
| Mobile apps | Expo / EAS (Guest, Room service) | Build profiles `staging` and `production`, each with its API URL. |

## Environments

`development` (laptop), `staging` (production-like, seeded test hotels, used for load tests
and release checks) and `production`. They never share a database, keys, buckets or email
domain. Configuration is in `backend/.env.example`; the settings refuse to start in
`staging`/`production` without Redis, Supabase, a real email provider and a non-local KMS in
production.

Secrets come from the host's secret manager, never from the image: `DATABASE_URL`,
`WORKER_DATABASE_URL`, `MIGRATIONS_DATABASE_URL`, `JWT_SIGNING_KEYS_JSON`, `PAIRING_CODE_PEPPER`,
`SUPABASE_SERVICE_ROLE_KEY`, `EMAIL_PROVIDER_KEY`, `REDIS_URL`, `SENTRY_DSN`, the KMS settings.
Set `RELEASE` to the git commit so errors are tied to a release.

## Release process (staging, then production)

1. CI is green on `main`: lint, strict types, migrations (including a full downgrade and
   upgrade), route tenancy check, the full test suite (cross-tenant, section 71 security
   tests, the spec's test case 70, report reconciliation) and the restore drill.
2. Build the image once; deploy the **same image** to staging.
3. On staging: `alembic upgrade head`, deploy API and worker, run the smoke checks below and,
   for releases that touch hot paths, the load test (`infra/loadtest/locustfile.py`).
4. Promote the same image to production in a quiet window (not 06:00–09:00 or 17:00–21:00
   hotel time). Migrations are additive first; destructive changes ship in a later release.
5. Watch error rate, p95 latency and outbox lag for 30 minutes. Roll back by redeploying the
   previous image; downgrade migrations only if the release notes say it is safe.

## Smoke checks after a deploy

- `GET /api/v1/health` returns 200; `GET /api/v1/admin/health` (platform token) shows the
  database, queue (oldest pending event under 60 s), realtime and email as `ok`.
- A test hotel's tablet loads its session and menu; a kitchen display receives a test order
  over the WebSocket; the worker sends a webhook `ping` to a test endpoint.

## Monitoring and alerts

- Errors and traces: Sentry (`SENTRY_DSN`, sample traces at about 5%). Events are scrubbed:
  no bodies, cookies, query strings, credentials or user details beyond an id.
- Logs: structured JSON on stdout with request ids; ship them to the host's log store and
  keep security events (`diyneco.security`) for 12 months.
- Alert on: API 5xx above 1% for 5 minutes, p95 above 1 s, outbox oldest pending above
  60 s, worker not running, failed backups, webhook endpoints disabled, and every
  `admin.support_access_granted` (operations runbook, alerts).

## Backups and the restore drill

Supabase daily backups plus point-in-time recovery; storage copied daily to a second region.
The restore drill (`backend/scripts/restore_drill.py`) restores into an isolated database and
checks row counts, folio balances against their entries, orders without folio entries,
invoice number gaps and that tenant isolation and append-only protections survived. CI runs it
on every push against the test database; run it quarterly against a real production backup in
an isolated, access-controlled environment, time it against the 4-hour target, record the
JSON result in the drill log, and destroy the copy the same day.

```
uv run python scripts/restore_drill.py --source-url "$RESTORED_FROM" --target-url "$ISOLATED_DB" \
    --log drill-log.jsonl
```

## Before the first hotel goes live

- [ ] Hosting provider and Supabase region chosen; DNS and TLS for the API and web apps.
- [ ] Production KMS configured (`KMS_PROVIDER` other than `local`).
- [ ] Email domain with SPF, DKIM and DMARC; `EMAIL_PROVIDER=smtp` and `EMAIL_SMTP_URL` set.
- [ ] An SA attorney has reviewed the POPIA sections and a registered tax practitioner the
      VAT and invoicing rules (security spec).
- [ ] Plan prices and limits replaced (they are placeholders, DECISIONS) through `/admin/plans`.
- [ ] External penetration test of the staging environment, findings fixed.
- [ ] Load test on staging meets the targets in `infra/loadtest/locustfile.py`.
- [ ] Restore drill run against a real backup.
- [ ] Platform admin accounts created with MFA; break-glass procedure documented.
