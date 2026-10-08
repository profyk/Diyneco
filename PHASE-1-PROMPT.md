# Phase 1 kickoff — Foundation

You are starting the Diyneco codebase. Read `CLAUDE.md` first, then read the specs in `docs/` (all of `02`, `03` and `04`; the Phase table and decisions in `01`; the configuration and release sections of `05`). Skim `docs/00-build-spec.md` for intent.

## Goal

Build the foundation every later phase depends on: the monorepo, the complete database schema with tenant isolation and financial safeguards, authentication and permissions, idempotency, audit and the event outbox, with tests and CI. No frontend apps in this phase.

## Step 1: plan, then wait

Before writing code, produce a plan and stop for my approval. The plan should cover:

- the file tree you will create
- the migration breakdown (how you will split the schema in `docs/03-database-specification.md` into migrations)
- the list of tests you will write, grouped by concern
- any spec gaps or contradictions you found, with the option you recommend for each

## Step 2: build (after I approve the plan)

1. **Repository skeleton.** Directory layout from `CLAUDE.md`; pnpm workspace file with empty `apps/` and `packages/` placeholders (README in each saying which phase builds it); `.gitignore`; `.editorconfig`; root `README.md` with setup steps; `docs/DECISIONS.md` and `docs/PROGRESS.md`.
2. **Local infrastructure.** `infra/docker/compose.yml` with Postgres 15+ and Redis. An init script that creates the roles `diyneco_owner`, `diyneco_api` and `diyneco_worker`, with `diyneco_api` and `diyneco_worker` as non-superusers without `BYPASSRLS`.
3. **Backend project.** `backend/pyproject.toml` (uv or pip), FastAPI app factory, settings from environment (fail fast on missing required values), structured JSON logging with request id, the error envelope and the exception handlers that map domain errors and SQLSTATE `P0001`–`P0004` to API error codes, secure headers, CORS allow-list, health endpoint. `backend/.env.example` exactly as in the runbooks' configuration section.
4. **Full schema migrations.** Every table, constraint, index, view, function, RLS policy, trigger and grant from the database spec, split into reviewable Alembic migrations. Include `app.uuid_v7()`, `app.current_hotel_id()`, the append-only triggers and revoked grants, `folio_must_be_open`, the order state-machine trigger and `redeem_pairing`. Partition `audit_logs` and `order_status_history` by month and create the current month and the next 3. SQLAlchemy models for all tables.
5. **Migration check.** `backend/scripts/check_migrations.py`: fails if any `app` table with `hotel_id` lacks RLS (enabled and forced) and a policy, or if any financial table lacks its append-only trigger.
6. **Seeds.** A migration seeds the permission catalogue, the 10 hotel system roles with exactly the permissions in the security spec's matrix, the 2 platform roles, the system charge categories and the 3 plans. A separate dev-only seed script (never run in production) creates the two demo hotels (Grand Example Hotel, Seabreeze Lodge) with rooms, stations and one user per role, PIN `1234`.
7. **Tenancy and database session.** A dependency that opens one transaction per request as `diyneco_api` and runs `SET LOCAL app.hotel_id`, `app.actor_user` and `app.actor_device`. A `TenantContext` passed to every repository. No unscoped repository helpers.
8. **Authentication.** Everything in the API spec's "Authentication and sessions" section: login, MFA verify and enrol (TOTP with replay protection and hashed recovery codes), refresh rotation with reuse detection that revokes the session family, logout, session list and revoke, step-up tokens from PIN or password, set PIN, forgot and reset password, email verification, invitation acceptance, lockouts and rate limits. Argon2id with the parameters in the security spec. EdDSA JWTs with `kid` and the claims listed in the spec. Email goes through a provider interface with a `console` implementation for development.
9. **Authorisation.** A `require_permission("...")` dependency, a `require_step_up` dependency, permission version (`perms_v`) checks, and the rule that a user cannot grant a permission they lack. Kitchen-session and device principal types exist even though their endpoints come later.
10. **Idempotency.** Middleware or dependency implementing the API spec rules: same key and same body returns the stored response with `Idempotent-Replayed: true`; same key and a different body returns `409 IDEMPOTENCY_CONFLICT`; in-flight returns `409 IDEMPOTENCY_IN_PROGRESS`; keys expire after 24 hours.
11. **Audit and outbox.** An audit writer used by services. An outbox writer that assigns the per-hotel `seq` inside the transaction. A worker process that drains the outbox and, for now, publishes to an in-process bus and logs (the WebSocket gateway is built when the first realtime consumer arrives in Phase 3).
12. **Minimal hotel endpoints**, enough to prove tenancy end to end: `POST /signup`, `GET`/`PATCH /hotel`, `GET`/`PATCH /hotel/settings` (step-up for the patch), `GET /permissions`, `GET /roles`. Everything else waits for its phase.
13. **OpenAPI.** Served at `/api/v1/openapi.json`. Add a script that generates TypeScript types into `packages/shared-types`.
14. **CI.** A GitHub Actions workflow with a Postgres service: Ruff, mypy, Alembic upgrade from empty, the migration check, pytest, a secret scan and a dependency audit.

## Tests that must exist and pass

- Every financial table rejects `UPDATE` and `DELETE` when connected as `diyneco_api`.
- With `app.hotel_id` unset, `diyneco_api` sees zero rows in every tenant table.
- With `app.hotel_id` set to hotel A, rows of hotel B are invisible and cannot be inserted.
- Composite foreign keys stop a row in hotel A pointing at a parent in hotel B.
- The order transition trigger allows every transition in the API spec's lifecycle and rejects every other one; amounts cannot change once `locked_at` is set.
- `payments` rejects a row whose tip is not `max(0, received − due)`.
- `stays_one_live_per_room` and `devices_one_guest_per_room` work.
- Auth: lockout after 5 failed passwords, refresh reuse revokes the family, expired tokens are rejected, MFA codes cannot be replayed, step-up expires after 5 minutes, a receptionist cannot call a `settings.update` endpoint, and nobody can grant a permission they lack.
- Idempotency: replay, conflict and in-flight cases.
- Cross-tenant: staff of hotel A calling hotel endpoints get only hotel A data, and a hotel B id returns `404`.
- The seeded role matrix matches the security spec exactly (a test that compares against a fixture copied from the spec).

## Exit criteria for Phase 1

- `docker compose up`, `alembic upgrade head` from empty, then `pytest` all pass on a clean machine, using only the steps in the README.
- The migration check passes and CI is green.
- Login with MFA works against the dev seed users.
- OpenAPI is published and the TypeScript types generate.

## When you finish

Stop. Do not start Phase 2. Give me:

1. what was built, as a short list
2. the exact commands to run it and the tests
3. test results (counts, with nothing skipped silently)
4. every decision you made that the specs did not, also written to `docs/DECISIONS.md`
5. open questions for me before Phase 2
