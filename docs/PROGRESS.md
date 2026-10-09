# Progress

## 2026-10-09: Phase 2 (Onboarding), backend

### Done

- CI fixed and green on `main` (migration check read `backend/.env`; Trivy action tag).
- Room types and rooms: list (natural order, filters, cursor), create, ranges (max 2,000,
  all or nothing), CSV import with a per-line dry-run report and `?commit=true`, patch with
  `If-Match`, manual status changes (refused while a guest is in), soft delete with step-up.
  Rate changes on a room type need step-up. Plan limits enforced.
- Staff: list, invitations (create, list, cancel; emailed code, 7 days), accept (Phase 1),
  patch, replace roles (bumps `perms_v`), deactivate (revokes sessions), PIN reset; custom
  roles (create, patch). Cannot-grant and superior rules, one-owner rule (D19-D22).
- Devices: pairing codes (guest room or kitchen stations), redeem with a credential shown
  once, credential to 1-hour device token, heartbeat with `RESET`/`LOCK` commands, registry
  with online/offline/needs-pairing, lock, unlock, reset, disable, reassign, unpair. Device
  principal enforces the spec's checks in order. Migration 0011 (`app.device_lookup`).
- Hotel logo upload through signed URLs (Supabase Storage, or local storage in development)
  and `GET /hotel/onboarding` with the 11 steps.
- Shared pagination, ETag and plan-limit helpers.
- Tests: 198 passing, none skipped, including the exit-criterion test that takes a hotel from
  sign-up to rooms and staff through the API only.

### Next

- Merchant web app (Next.js) onboarding screens on top of these endpoints.
- Phase 3 (Guest ordering): menu admin, guest tablet endpoints, room-charge rules, orders,
  the WebSocket gateway.

### Known gaps

- The API spec should gain `POST /devices/token`, the new device events and the
  `completed_commands` heartbeat field (D23, D24).
- Device `offline` is derived on read; the `DEVICE_OFFLINE` event needs the worker job that
  arrives with the WebSocket gateway in Phase 3.
- The `hotel-assets` bucket's size and type limits must be set in Supabase (D27).
- Kitchen stations can be paired but not yet managed (Phase 4).

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
