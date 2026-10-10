# Progress

## 2026-10-10: Phase 7 (Admin panel), backend

### Done

- Platform admin under `/admin` (platform token with MFA): metrics (hotels, rooms,
  connected devices, active stays, orders today and this month, MRR, churn), hotel list
  with counts and last activity, approve / suspend (step-up, reason) / reactivate, hotel
  subscriptions with limit overrides, plan catalogue, global and per-hotel feature flags,
  health (database, queue, realtime, email).
- Cross-hotel reads only through aggregate definer functions; platform requests see no
  tenant rows (D48). Writes to one hotel are audited in that hotel's log.
- Support access: ticketed, time-boxed (max 60 minutes), step-up, read-only token without
  guest data, owners emailed, listed and revocable by the hotel.
- `platform` realtime channel (D49).
- Exit criterion covered by a test: every GET route, called with a platform token and with a
  support token, returns no guest name, email or phone.
- CI fix: the card-data guard no longer mistakes UUIDs for card numbers.


## 2026-10-10: Phase 6 (Billing and checkout), backend

### Done

- Recovered the work lost when the previous session crashed (NUL-filled files rebuilt from
  the session transcript) and committed Phases 4 and 5.
- Folio for staff: view with totals by group and category, other charges, discounts
  (step-up, reason, audited), two-person adjustments (request, approve with step-up, reject;
  never by the requester; refused when the amount changed after the request).
- Checkout: summary, open-order and balance gates, override policy, gap-free invoice
  numbering, invoice kind by VAT status and the abridged limit, supplier and recipient
  snapshots (corporate billing with PO and traveller), long-stay VAT confirmation, folio
  closed, room to cleaning, tablet reset with `RESET_ROOM_SESSION`.
- Invoices: JSON, PDF (stored, hashed, signed URL), email with the PDF attached, list per
  stay, credit notes that re-open the folio for a re-issued bill.
- Stay changes: extend or shorten (posting or reversing nights) and room moves where the
  tablet session follows the guest.
- Exit criterion covered by a test: build spec test case 70 end to end.

### Next

- Phase 7 (Admin panel) once Phase 6 is signed off.
- The five front-end apps have not been started.

### Known gaps

- A balance left by a checkout override cannot be paid against the closed bill; the
  accounts-receivable list arrives with reports (Phase 8, D45).
- Email uses the console provider only; a real provider is still to be chosen.
- PDF text is Latin-1; names outside it print with replacement characters.


## 2026-10-09: Phases 3 (Guest ordering), 4 (Kitchen) and 5 (Room service), backend

### Done

- Menu administration: kitchen stations, schedules (hotel time zone, past-midnight windows),
  categories, items (allergens, dietary tags, halaal/kosher gated by `menu.certify`),
  price changes gated by `menu.price.update` + step-up and audited, availability, modifier
  groups and options, item images through signed uploads, `MENU_UPDATED` events.
- Guests, billing profiles, reservations, check-in and walk-ins: check-in opens the folio,
  posts every night with VAT, occupies the room and notifies the tablet.
- Server-side pricing and room-charge rules; guest tablet endpoints (session, menu, quote,
  orders, folio, info) limited to the active stay; staff phone orders; approval with
  step-up, decline, cancel with reversing folio entries.
- WebSocket gateway at `/api/v1/ws` fed by the outbox: auth, per-principal channels,
  24-hour replay since a seq, live fan-out, revalidation, connection limit.
- Kitchen display: PIN sign-in on a paired display, price-free board, accept, start, item
  ready, undo within 2 minutes; an order spanning stations is READY only when all items are.
- Room service: ready and mine lists, claim (first wins), release, manager assign, pick-up,
  delivered, leave on room; payment preview and recording with tips, partial payments, late
  entries, card terminal references; payments list.
- Exit criteria covered by tests: a paired tablet places an idempotent order with limit
  rules enforced (Phase 3); an order split across 3 stations reaches READY only when every
  item is ready (Phase 4); R3,000 due, R4,000 received, R1,000 tip, no duplicates on retry
  (Phase 5).

### Next

- Phase 6 (Billing and checkout): folio view, other charges, discounts, adjustments with two
  people, checkout with tablet reset, invoices (numbering, PDF, email), corporate billing.
- The five front-end apps (Merchant, Kitchen, Admin on Next.js; Guest and Room service on
  Expo) have not been started.

### Known gaps

- Menu images are stored as uploaded; resized versions need an image job (D32).
- The `platform` realtime channel and `DEVICE_OFFLINE` events need the worker/admin work.
- Guest ID numbers, stay extension and room moves are not built yet (Phase 6 with billing).

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
