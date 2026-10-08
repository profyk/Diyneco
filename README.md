# Diyneco

Hotel operations platform for South African hotels, lodges and guest houses. One FastAPI
backend and one PostgreSQL database serve five interfaces: Guest tablet, Kitchen display,
Room service, Merchant (hotel management) and Diyneco Admin.

Status: **Phase 1 (Foundation)** is built: schema, tenancy, authentication, permissions,
idempotency, audit, outbox and CI. The apps arrive in later phases; see `docs/PROGRESS.md`.

## Repository

```
apps/        guest, room-service, kitchen, merchant, admin   (placeholders until their phase)
backend/     FastAPI app, Alembic migrations, tests, scripts
database/    seed notes
packages/    shared-types (generated API types), shared-ui, config
docs/        specifications, DECISIONS.md, PROGRESS.md
infra/       db bootstrap, Docker Compose, deployment notes
```

Specifications live in `docs/`; `CLAUDE.md` explains which one wins when they disagree.

## Prerequisites

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- Node 20+ and pnpm (only for generating the shared TypeScript types)
- PostgreSQL 15+ (17 recommended), either installed natively or through Docker
- Redis is optional in development

## Setup

### 1. Database

**With Docker** (needs hardware virtualisation and about 4 GB of RAM):

```
cp infra/docker/.env.example infra/docker/.env      # then replace every CHANGE_ME
docker compose -f infra/docker/compose.yml --env-file infra/docker/.env up -d
```

The first start runs `infra/db/bootstrap.sql`, which creates the roles `diyneco_owner`,
`diyneco_api`, `diyneco_worker`, `diyneco_platform` and the databases `diyneco` and `diyneco_test`.

**Without Docker** (PostgreSQL installed natively, e.g. `winget install PostgreSQL.PostgreSQL.17`):

```
psql -h localhost -U postgres -d postgres -f infra/db/bootstrap.sql \
     -v owner_password=... -v api_password=... -v worker_password=...
```

Choose three strong passwords; you will put them in `backend/.env` next.

### 2. Backend configuration

```
cd backend
cp .env.example .env
uv run python scripts/gen_dev_keys.py >> .env        # JWT keys, pepper, local KMS key
```

Edit `.env`: put the three role passwords into `DATABASE_URL`, `WORKER_DATABASE_URL` and
`MIGRATIONS_DATABASE_URL`, remove the earlier `CHANGE_ME` lines that `gen_dev_keys.py` replaced,
and add the test database URLs (same roles, database `diyneco_test`):

```
TEST_DATABASE_URL=postgresql+asyncpg://diyneco_api:...@localhost:5432/diyneco_test
TEST_WORKER_DATABASE_URL=postgresql+asyncpg://diyneco_worker:...@localhost:5432/diyneco_test
TEST_MIGRATIONS_DATABASE_URL=postgresql+psycopg://diyneco_owner:...@localhost:5432/diyneco_test
```

The API refuses to start while a required value is missing or still `CHANGE_ME`.

### 3. Install, migrate, seed, run

```
uv sync
uv run alembic upgrade head
uv run python scripts/check_migrations.py
uv run python scripts/seed_dev.py                     # development only
uv run uvicorn app.main:create_app --factory --reload # API on http://localhost:8000
uv run python -m app.worker                           # outbox worker and maintenance
```

API docs (development only): http://localhost:8000/api/v1/docs ·
OpenAPI: http://localhost:8000/api/v1/openapi.json

Demo users (from `seed_dev.py`): `gm@grandexample.example`, `reception@grandexample.example`,
`owner@seabreeze.example` and so on; one per role in each hotel. The password is printed by the
seed script, and every PIN is `1234`. Owner, admin, general manager and finance users set up
two-step sign-in with an authenticator app at first sign-in.

## Checks and tests

```
cd backend
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run python scripts/check_migrations.py
uv run python scripts/check_routes.py
uv run pytest
```

`pytest` rebuilds `diyneco_test` from empty with the real migrations, then runs every test as
the `diyneco_api` role, so row-level security is always in force.

## Shared TypeScript types

```
pnpm install
pnpm gen:types        # writes packages/shared-types/openapi.json and src/api.d.ts
```

## CI

`.github/workflows/`: `ci.yml` (lint, types, migrations, checks, tests, generated types),
`security.yml` (secret scan, dependency audit, frontend secret check, CodeQL),
`container.yml` (build, scan and publish the backend image). Dependabot keeps dependencies current.
