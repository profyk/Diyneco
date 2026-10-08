# Progress

## 2026-10-08: Phase 1 (Foundation)

### Done

- Monorepo skeleton: `apps/*` and `packages/*` placeholders naming the phase that builds them,
  pnpm workspace, `.editorconfig`, `.gitattributes`, root README.
- Database bootstrap (`infra/db/bootstrap.sql`) shared by native Postgres and Docker Compose.
- Ten Alembic migrations: the full schema from the database spec plus approved additions
  (DECISIONS G1-G19), RLS on every tenant table, append-only triggers and revoked grants on
  the 8 financial tables, monthly partitions (Oct 2026 to Jan 2027), catalogue seeds.
- `scripts/check_migrations.py` (RLS, append-only, partitions, views, definer functions) and
  `scripts/check_routes.py` (no route accepts a hotel id).
- SQLAlchemy models for all 60 tables, checked against the migrated schema by a test.
- FastAPI app: fail-fast settings, JSON logging with redaction, error envelope, security
  headers, CORS allow-list, request ids, rate limits, unknown-query and card-data rejection.
- Per-request transaction as `diyneco_api` with `SET LOCAL` tenant context; `TenantContext` in
  every repository.
- Authentication: login, lockout, TOTP MFA (enrol, confirm, verify, replay protection, recovery
  codes), mandatory MFA for owner/admin/GM/finance and platform, refresh rotation with family
  revocation on reuse, logout, sessions list and revoke, 10-session limit, step-up (PIN or
  password), set PIN, forgot/reset password, email verification, invitation acceptance.
- Authorisation: `require_permission`, `require_step_up`, `perms_v` checks, the cannot-grant rule,
  device and kitchen principal kinds rejected on staff endpoints.
- Idempotency, audit writer, transactional outbox with per-hotel `seq`, worker (drain,
  partitions, purges).
- Endpoints: `POST /signup`, `GET`/`PATCH /hotel`, `GET`/`PATCH /hotel/settings`, `GET /permissions`,
  `GET /roles`, `GET /health`, and all `/auth/*` endpoints except kitchen sign-in.
- Dev seed: Grand Example Hotel and Seabreeze Lodge, one user per role, PIN 1234.
- OpenAPI at `/api/v1/openapi.json`; `pnpm gen:types` generates `packages/shared-types`.
- GitHub Actions: CI, security (gitleaks, pip-audit, pnpm audit, frontend secret check,
  CodeQL), backend image build and Trivy scan, Dependabot.
- Tests: 149 passing, none skipped.

### Next

- Phase 2 (Onboarding), after Profy approves: onboarding steps, room types and rooms (single,
  ranges, CSV), staff invitations and roles, device registry, logo upload, merchant app start.

### Known gaps and open items

- CI has not run yet: the commits are local until pushed to GitHub.
- Docker Compose is untested here (no virtualisation on the development laptop); CI uses a
  Postgres service container instead.
- CodeQL needs GitHub Advanced Security if the repository is private.
- Only the `local` KMS provider and the `console` email provider exist; production needs a cloud
  KMS and a real email provider before Phase 9 (start-up refuses otherwise).
- Supabase's transaction-mode pooler needs asyncpg's statement cache disabled; to be set when
  the hosting is configured.
- Kitchen sign-in (`/auth/kitchen/sign-in`) arrives with Phase 4; the WebSocket gateway with
  Phase 3; platform role grants with Phase 7.
- The API spec should list the new event types (D11) and the approved schema additions.
