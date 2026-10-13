# Deployment and launch

Hosting (D80): the API and worker on **Railway**, the five web apps on **Vercel**, Postgres and
file storage on **Supabase**, the encryption master key in **AWS KMS**. One manual GitHub
workflow, **Deploy**, releases a tested commit to staging and then the same commit to production.
First-time setup: "Setting up Railway, Vercel, Supabase and AWS" below.

## What runs where

| Component | How it runs | Notes |
| --- | --- | --- |
| API | Railway service `api`: image `ghcr.io/<repo>/backend:<environment>` (built from `backend/Dockerfile`), its default command (listens on `PORT`) | Stateless; 2 replicas in production. Railway's proxy terminates TLS and passes WebSockets (`/api/v1/ws`). |
| Worker | Railway service `worker`: same image, start command `python -m app.worker` | One replica; two are safe (deliveries are claimed with `SKIP LOCKED`). No public domain. |
| Database | Supabase Postgres 15+ | Run `infra/db/bootstrap.sql` once as the Supabase `postgres` role, then `alembic upgrade head` as `diyneco_owner`. Schema `app` must never be exposed through the Supabase REST API. |
| Storage | Supabase Storage, private buckets `hotel-assets` and `invoices` | Second, separately keyed copy in another region (operations runbook, backups). |
| Redis | Railway Redis in the same project and environment | Rate limits across instances; required outside development. |
| Web apps | Vercel, one project per app (root directory `apps/<app>`), built by the Deploy workflow | `NEXT_PUBLIC_API_URL` (and, when files are not on Supabase, `NEXT_PUBLIC_STORAGE_URL`) are compiled into the pages and their Content-Security-Policy at build time; public addresses, never secrets. Guest and Room service are web apps too (D58). The container images (`infra/docker/web.Dockerfile`) are still built and scanned in CI for any other host. |

## Setting up Railway, Vercel, Supabase and AWS

Do this once for **staging**, then again for **production**; the two never share a database,
keys, Redis, buckets or Railway environment.

**Domains (required).** Staff sign-in keeps its refresh token in a `SameSite=Strict` cookie on
the API, which browsers only send when the web app and the API are on the same site. Put
everything on one domain, for example `api.diyneco.com`, `merchant.diyneco.com`,
`admin.diyneco.com`, `kitchen.diyneco.com`, `guest.diyneco.com`, `rooms.diyneco.com` (staging:
`api.staging.diyneco.com` and so on). The default `*.up.railway.app` and `*.vercel.app` addresses
do not work for staff sign-in, and the smoke checks refuse them.

**Supabase.** Choose the region next to the Railway region: Railway `europe-west4` (Amsterdam)
with Supabase Frankfurt (`eu-central-1`) is the nearest pair to South Africa. Hosting outside
South Africa is a cross-border transfer of personal information, which the POPIA review must
cover. Turn on point-in-time recovery and create the private buckets `hotel-assets` and `invoices`.
Prepare the database with the **Migrate** workflow (below), not the SQL editor:
`infra/db/supabase-bootstrap.sql` is the Supabase version of `infra/db/bootstrap.sql` (one
`postgres` database, Supabase's own `extensions` schema, no superuser). Railway connects over IPv4, so use Supabase's **session pooler** connection string
(port 5432; the user becomes `diyneco_api.<project-ref>`), never the transaction pooler: the API
relies on per-transaction settings and prepared statements.

**AWS KMS** (envelope encryption of TOTP secrets, guest ID numbers and webhook secrets). Per
environment, create a symmetric key (`SYMMETRIC_DEFAULT`, automatic yearly rotation on) in one
AWS region, and an IAM user whose only policy is:

```json
{"Version": "2012-10-17", "Statement": [{"Effect": "Allow",
  "Action": ["kms:Encrypt", "kms:Decrypt"], "Resource": "<the key's ARN>"}]}
```

Give its access key to the API and worker as `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`,
with `KMS_PROVIDER=aws`, `KMS_MASTER_KEY_ID=<the key's ARN>` and `AWS_REGION`. Never schedule the
key for deletion: every secret encrypted under it would become unreadable.

**Railway.** One project with environments `staging` and `production`. In each: a Redis
database, and two services from the Docker image `ghcr.io/<owner>/<repo>/backend:<environment>`
(add GitHub Container Registry credentials, a token with only `read:packages`, in each
service's image settings):

- `api`: the image's default command, healthcheck path `/api/v1/health`, region
  `europe-west4`, 2 replicas in production, the API's custom domain;
- `worker`: start command `python -m app.worker`, 1 replica, no domain.

Variables on both services (Railway's sealed variables, never the repository):

| Variable | Value |
| --- | --- |
| `APP_ENV` | `staging` or `production` |
| `API_BASE_URL` | the API's public address |
| `CORS_ALLOWED_ORIGINS` | every web app's address, comma-separated |
| `MERCHANT_APP_URL`, `ADMIN_APP_URL` | the Merchant app's and Admin panel's addresses |
| `DATABASE_URL`, `WORKER_DATABASE_URL` | session pooler, `postgresql+asyncpg://diyneco_api.<ref>:...` and `diyneco_worker.<ref>` |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | from the Supabase project |
| `JWT_SIGNING_KEYS_JSON`, `JWT_ACTIVE_KID`, `PAIRING_CODE_PEPPER` | new per environment (`uv run python scripts/gen_dev_keys.py` prints a fresh set; use only these three lines) |
| `KMS_PROVIDER`, `KMS_MASTER_KEY_ID`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | AWS KMS, above |
| `EMAIL_PROVIDER=smtp`, `EMAIL_SMTP_URL`, `EMAIL_PROVIDER_KEY`, `EMAIL_FROM` | the email provider |
| `STITCH_*` | once Stitch is ready (checklist below) |
| `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE=0.05` | monitoring |
| `FORWARDED_ALLOW_IPS` | `*`: on Railway the containers are reachable only through Railway's proxy, which sets `X-Forwarded-For` |
| `RELEASE` | `${{RAILWAY_DEPLOYMENT_ID}}` |

`MIGRATIONS_DATABASE_URL` (`diyneco_owner`) is **not** given to Railway. Migrations run from the
Deploy workflow, so the running API never holds the schema owner's password.

**Vercel.** Five projects (`admin`, `merchant`, `kitchen`, `guest`, `room-service`), each with
root directory `apps/<app>` and framework Next.js, **Git deployments switched off** (the Deploy
workflow builds exactly the released commit), and its production domain attached. Staging is
a preview deployment given the staging domain.

**GitHub.** Environments `staging` and `production` (production with required reviewers),
each holding the secrets and variables listed at the top of `.github/workflows/deploy.yml`
and `.github/workflows/migrate.yml`.

**Database migrations** (Actions > Migrate, D81). Once per Supabase project, run action
`prepare`: it creates the roles `diyneco_owner`, `diyneco_api` and `diyneco_worker` with the
passwords held in the GitHub environment, plus the extensions and grants. After that, `status`
shows the database's revision and what a commit would apply, and `upgrade` applies it and runs
the migration check (row-level security, append-only protections, grants). Only commits on main
run. Deploy also migrates on every release. Migrations are additive first, and downgrades are
never run against Supabase (the first migration's downgrade would drop shared extensions).

**API address and fallback** (D81). The web apps are built with `PUBLIC_API_URL`
(`https://api.diyneco.com`) and, optionally, `PUBLIC_API_FALLBACK_URL` (the Railway address,
for example `https://diyneco-production.up.railway.app`). When an app starts it uses the first
that answers `/api/v1/health` and keeps that choice for the browser tab. Add `api.diyneco.com`
as a custom domain on the Railway `api` service (Settings > Networking, then the CNAME record
it shows at your DNS provider), and set `API_BASE_URL=https://api.diyneco.com` either way. On
the fallback, staff sign-in works but does not survive a page reload (the refresh cookie is
SameSite=Strict and the Railway address is another site), so it is a stopgap while DNS is set
up.

**Releasing.** Actions > Deploy > Run workflow, environment `staging`, a commit hash from
main. The workflow checks that every workflow on the commit is green and its backend image
exists, runs `alembic upgrade head` and the migration check as the owner role, points
`backend:staging` at that build and redeploys `api` and `worker` on Railway, builds and deploys
the five web apps on Vercel, then runs `infra/deployment/smoke.sh`. Once staging is checked,
run it again with `production` and the same commit.

**First Super Admin** (once per environment, from a trusted machine, never in CI logs, since
the script prints a one-time link to choose a password):

```
docker run --rm --env-file prod.env ghcr.io/<owner>/<repo>/backend:production \
    python scripts/create_platform_admin.py --email ... --name ...
```

where `prod.env` holds the API's variables, kept out of the repository and deleted afterwards.

## Environments

`development` (laptop), `staging` (production-like, seeded test hotels, used for load tests
and release checks) and `production`. They never share a database, keys, buckets or email
domain. Configuration is in `backend/.env.example`; the settings refuse to start in
`staging`/`production` without Redis, Supabase, a real email provider and a non-local KMS in
production.

Secrets come from Railway's sealed variables, never from the image: `DATABASE_URL`,
`WORKER_DATABASE_URL`, `JWT_SIGNING_KEYS_JSON`, `PAIRING_CODE_PEPPER`,
`SUPABASE_SERVICE_ROLE_KEY`, `EMAIL_PROVIDER_KEY`, `REDIS_URL`, `SENTRY_DSN`, the AWS and
Stitch credentials. `MIGRATIONS_DATABASE_URL` lives only in the GitHub environment used by the
Deploy workflow.

## Release process (staging, then production)

1. CI is green on `main`: lint, strict types, migrations (including a full downgrade and
   upgrade), route tenancy check, the full test suite (cross-tenant, section 71 security
   tests, the spec's test case 70, report reconciliation) and the restore drill.
2. CI builds the backend image once per commit on main. Deploy to staging releases that **same
   image** (migrations, API, worker, web apps, smoke checks).
3. Check staging; for releases that touch hot paths run the load test
   (`infra/loadtest/locustfile.py`) there.
4. Deploy the same commit to production in a quiet window (not 06:00–09:00 or 17:00–21:00
   hotel time). Migrations are additive first; destructive changes ship in a later release.
5. Watch error rate, p95 latency and outbox lag for 30 minutes. Roll back by running Deploy
   with the previous release's commit (its migrations are already applied, so this only rolls
   the code back); downgrade migrations only if the release notes say it is safe.

## Smoke checks after a deploy

The Deploy workflow runs `infra/deployment/smoke.sh`: the API answers healthily over HTTPS with
its hardening headers and the standard error envelope, refuses anonymous admin access, and
each web app loads with its security headers, a Content-Security-Policy built for this API and
a domain on the same site as the API. Then by hand:

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

- [ ] Railway, Vercel, Supabase and AWS set up per environment as above, on one domain for the
      API and web apps (DNS records from Railway and Vercel; both issue TLS certificates).
- [ ] AWS KMS key and least-privilege IAM user per environment (`KMS_PROVIDER=aws`).
- [ ] Email domain with SPF, DKIM and DMARC; `EMAIL_PROVIDER=smtp` and `EMAIL_SMTP_URL` set.
- [ ] An SA attorney has reviewed the POPIA sections and a registered tax practitioner the
      VAT and invoicing rules (security spec).
- [ ] Company details verified and entered in Admin > Company & tax (CIPC registration number,
      registered address, billing contacts, bank details); VAT switched on only once registered.
- [ ] Plans reviewed in Admin > Plans & Pricing (the seeded R499, R999 and R1,999 monthly
      drafts, plus any quarterly or annual prices) and published.
- [ ] Stitch (D79): a test client first, then a live one; set `STITCH_CLIENT_ID`,
      `STITCH_CLIENT_SECRET`, `STITCH_WEBHOOK_SECRET` (Svix `whsec_...`) and `STITCH_TEST_MODE`
      (false only for the live client) on the API, register the webhook
      `https://<api>/api/v1/billing/webhooks/stitch` for payment events, set `MERCHANT_APP_URL`
      (checkouts return there), then choose Stitch in Admin > Billing & Invoices > Payments &
      collections. The sandbox is refused in production. Bank details in Company & tax for EFT.
- [ ] Collections policy reviewed (reminder days, grace period, suspension, proration).
- [ ] External penetration test of the staging environment, findings fixed.
- [ ] Load test on staging meets the targets in `infra/loadtest/locustfile.py`.
- [ ] Restore drill run against a real backup.
- [ ] First Super Admin created with `uv run python scripts/create_platform_admin.py --email ...
      --name ...` (prints a one-time link to choose a password), then further Diyneco staff
      invited from Admin > Diyneco staff (D71);
      break-glass procedure documented. Do not run `scripts/seed_dev.py` or
      `scripts/seed_e2e.py` outside development (they refuse to).
- [ ] Browser end-to-end tests green in CI on the release commit.
