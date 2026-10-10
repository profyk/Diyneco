# Diyneco — project memory for Claude Code

Diyneco is a multi-tenant hotel operations platform for South African hotels, lodges and guest houses (5 to 1,000+ rooms). One FastAPI backend and one PostgreSQL database (Supabase) serve five interfaces: Guest tablet app, Kitchen display, Room-service app, Merchant (hotel management) app and Diyneco Admin panel.

You are building it as production software, phase by phase. Read this file at the start of every session.

## Source of truth

All specifications live in `docs/`. When they disagree, the higher one in this list wins:

1. `docs/02-api-specification.md`: endpoints, permissions, idempotency, step-up, WebSocket protocol, error codes
2. `docs/03-database-specification.md`: every table, constraint, RLS policy, trigger and index (the SQL is the target schema)
3. `docs/04-security-and-compliance.md`: credentials, permission matrix, tenant isolation, POPIA, VAT, PCI, required security tests
4. `docs/05-operations-runbooks.txt`: environments, config, `.env.example`, alerts, release rules
5. `docs/01-platform-foundation.txt`: architecture decisions and the phase plan with exit criteria
6. `docs/00-build-spec.md`: the original 82-section product brief (intent and acceptance tests)

`docs/reference/prototype.html` is a throwaway clickable prototype. Use it to understand flows and screens. Never copy its code; its "backend" is an in-page simulation.

If a spec is silent or contradictory on something that matters, stop and ask before inventing a rule. If you must choose to keep moving, choose the more restrictive option and note it in `docs/DECISIONS.md`.

## Adopted decisions

- FastAPI owns all authentication: staff JWT (EdDSA), rotating refresh tokens, TOTP MFA, PIN step-up, device credentials, API keys. Supabase Auth is not used.
- Realtime goes through a FastAPI WebSocket gateway fed by the `event_outbox` table. Clients never subscribe to Supabase Realtime and never hold any Supabase key.
- Supabase is used only for Postgres and Storage. Schema `app` is never exposed through Supabase's REST API.
- Guest tablet lockdown in v1: Android screen pinning plus a staff exit PIN. MDM device-owner mode comes in v1.1.
- Local development uses plain Postgres 15+ and Redis in Docker Compose. The Supabase CLI is optional.

## Rules that are never broken

- The backend is the only authority. Prices, totals, tips, balances, permissions and tenancy are computed on the server. Frontends display results and never decide them.
- Every hotel-owned row has `hotel_id`. The hotel comes from the authenticated principal, never from a request body or path. Cross-tenant ids return `404 NOT_FOUND`.
- Tenant isolation is enforced twice: repository queries filter by `hotel_id`, and Postgres RLS (`app.hotel_id` set with `SET LOCAL` per transaction) blocks anything that slips through. The API connects as the non-superuser role `diyneco_api`; superusers bypass RLS, so tests must use that role too.
- Money is `bigint` minor units (cents) plus `currency char(3)`. Never floats, never `numeric` for stored amounts. Rates are basis points (1500 = 15%).
- Financial tables are append-only (`folio_entries`, `payments`, `payment_allocations`, `tips`, `invoices`, `invoice_items`, `audit_logs`, `order_status_history`). Corrections are new reversing or adjusting entries. A database trigger and revoked grants enforce this.
- `tip = max(0, amount_received − amount_due)`. Tips are never hotel revenue and never count toward a folio balance. A positive tip needs explicit confirmation.
- Orders snapshot names, prices, VAT and modifiers when placed. Amounts lock when the kitchen accepts an order.
- Adjustments need two people: the requester can never approve their own request.
- Every state-changing financial or device operation requires an `Idempotency-Key` and is safe to retry.
- No card numbers, CVV, PIN or track data are stored or accepted. Card payments record amount, method and terminal reference only.
- Checkout invalidates the room tablet's session and sends `RESET_ROOM_SESSION`. A new guest can never see a previous guest's data. History stays in the database.
- Every sensitive action writes an audit entry (actor, hotel, action, entity, old value, new value, time, device or IP).
- Never show stack traces or SQL errors to clients. Every error uses the envelope `{"error": {"code", "message", "request_id", "details"}}` with codes from the API spec.
- Never hard-code secrets. Never put `SUPABASE_SERVICE_ROLE_KEY`, JWT keys or database URLs in any frontend.
- No fake functionality. If something is not built yet, it is absent or clearly labelled with the phase that builds it. Seed and demo data exist only in development.

## Stack

- Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x (async, asyncpg), Alembic, pytest + pytest-asyncio + httpx, Ruff, mypy (strict on `app/`). Argon2id via `argon2-cffi`, EdDSA JWT via `pyjwt[crypto]` or `joserfc`, TOTP via `pyotp`.
- Web apps (all five: Merchant, Kitchen, Admin, Guest, Room service): Next.js (App Router), TypeScript strict, Tailwind, shadcn/ui, TanStack Query.
- Guest tablet and Room-service apps: Next.js web apps like the others, mobile-first (responsive, large touch targets, installable full screen). DECISIONS D58.
- Monorepo: pnpm workspaces for TypeScript; the backend is a separate Python project under `backend/`. API types for frontends are generated from FastAPI's OpenAPI into `packages/shared-types`.
- Use current stable releases of each library, pinned in lockfiles.

## Repository layout

```
apps/        guest/ room-service/ kitchen/ merchant/ admin/
backend/     app/{api/v1, core, models, schemas, services, repositories, realtime, billing,
                  payments, notifications, audit, integrations}  tests/  alembic/
database/    seeds/  (dev-only)
packages/    shared-types/ shared-ui/ config/
docs/        specifications (read-only unless told) + DECISIONS.md + progress notes
infra/       docker/ deployment/
brand/       logo and icon drafts (raster; a clean SVG master is still to come)
```

Layering inside the backend is strict: router → tenancy context → service → repository → database. Routers hold no business logic or SQL. Services hold all business rules. Repositories require a `TenantContext` and always filter by `hotel_id`. Events and audit entries are written in the same transaction (outbox) and published only after commit.

## Brand

Name: Diyneco. Colours (approximate until an SVG master exists): navy `#0B2350`, blue `#1E7FD8`, teal `#2CC9C0`, green `#16B57A`, clean white or light backgrounds. The interface should feel premium, calm and professional, never childish. The kitchen display needs very large touch targets and a high-visibility mode. The guest app must be extremely simple.

## How to work

- Work one phase at a time, following the phase table in `docs/01-platform-foundation.txt`. Do not start the next phase until the current phase's exit criteria pass and the user says to continue.
- Plan before large changes. List the files you will create and the order, then build in small steps.
- Write tests alongside the code. Tenant isolation, permissions, money calculations, idempotency and state transitions get tests before or with the code that implements them.
- Run the full test suite, Ruff and mypy before saying a step is done. Report real results; never claim a test passed without running it.
- Every Alembic migration must have an upgrade and a safe downgrade. Every new table with `hotel_id` gets its RLS policy in the same migration, and every new financial table gets the append-only trigger. `backend/scripts/check_migrations.py` enforces both in CI.
- When you add an endpoint, permission, table, event or error code, keep it consistent with the specs. If the specs must change, propose the change to the user instead of silently diverging.
- Record any decision the specs did not make in `docs/DECISIONS.md` (date, decision, reason).
- At the end of each work session, update `docs/PROGRESS.md`: what is done, what is next, known gaps.
- Commits: small, imperative subject lines, one logical change each.

## Commands

Keep these accurate.

```
# Database: native Postgres (see README) or
docker compose -f infra/docker/compose.yml --env-file infra/docker/.env up -d
cd backend && uv sync
cd backend && uv run alembic upgrade head
cd backend && uv run python scripts/check_migrations.py
cd backend && uv run python scripts/check_routes.py
cd backend && uv run python scripts/seed_dev.py                       # development only
cd backend && uv run pytest                                           # rebuilds diyneco_test
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy
cd backend && uv run uvicorn app.main:create_app --factory --reload
cd backend && uv run python -m app.worker
pnpm gen:types                                                        # packages/shared-types
```

Local machine note: this laptop has no hardware virtualisation and 2 GB RAM, so it runs
PostgreSQL 17 natively and no Docker; Redis is optional in development (docs/DECISIONS.md D2, D3).
