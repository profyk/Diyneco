# Progress

## 2026-10-16: Design, themes, kitchen buzzer, website images, gaps closed (D94 to D97)

### Done

- Staff app shell (D96): Admin and Merchant share a navy sidebar that scrolls on its own, a
  fixed top bar, separately scrolling pages, a phone drawer, an icon-only narrow mode and a
  Light / Dark / Same-as-device switch with no flash; show/hide on every password and PIN.
- Sessions survive a reload (D97): refreshes are single-flight per tab and serialised across
  tabs; two overlapping refreshes used to end the session as a token replay.
- Kitchen buzzer (D95): every new order buzzes and shows a banner; unaccepted orders buzz
  again every 30 s; the board shows hotel time (closes the known gap).
- Website images (D94): published images are allowed cross-site; seven original hotel
  illustrations on the built-in pages.
- Guest requests report (`/reports/requests`, merchant Reports tab); prorated upgrades carry
  the group discount (closes the D89 gap); Vercel builds compare with the last deployment.
- First Super Admin created in Supabase (staging); Supabase is at 0037.

### Next

- Owner: rename `NEXT_PUBLIC_API` to `NEXT_PUBLIC_API_URL` on five Vercel projects, set
  `CORS_ALLOWED_ORIGINS` and the app URLs on Railway, then redeploy.
- Production readiness as listed below (KMS, SMTP, production Supabase, custom domain).

### Known gaps

- Cross-site cookies: until the apps and the API share a domain, browsers that block
  third-party cookies may sign staff out on reload.

## 2026-10-15: Deployment, onboarding, owners with several properties, insights, website, guest requests (D84 to D93)

### Done

- Deployed: API and worker on Railway (staging settings: local KMS, console email), Redis on
  Railway, Postgres on Supabase (session pooler, least-privilege roles; the Supabase bootstrap
  no longer names NOSUPERUSER, which Postgres 16+ refuses to non-superusers). Supabase is
  migrated to 0036.
- Onboarding (D84, D85): every inhabited country with currency, dialling code, language, zones
  and first-level regions; operational countries chosen in Admin > Countries; a guided
  signup (property, location with province dropdown, account, review) with no currency
  question and a 6-digit emailed confirmation code; 15 property categories.
- Owners with several properties (D86, D89, D90): Add a property (no second free trial;
  Admin can grant one), All properties overview, one payment for every property's invoices
  with an optional group discount, and invitations to several properties at once.
- Admin insights (D87): adoption, activation funnel, trial conversion, churn, MRR won/lost,
  cohorts, breakdowns by country, province and category, staff activity, an Owners page, and
  hotel filters with CSV.
- Website (D83, D88): the website API is connected (two bugs fixed: leads crashed on a
  missing rate limit; unpublishing wrote JSON null), `apps/website` for Vercel with pricing
  from Plans & Pricing and legal pages from Legal documents, and Admin > Website to edit
  pages, posts, images, leads, redirects, settings and see visitors.
- Session refresh has its own rate limit, 120 a minute per IP (D92).
- Guest service requests (D93): towels, cleaning, repairs, wake-up calls and late checkout from
  the room tablet or logged by staff; a live Guest requests board in the merchant app and a
  Requests tab in the room-service app; migration 0037.
- Website photo gallery (D91): a Photo gallery section with photos by hotel area (rooms,
  reception, kitchen, restaurant, outside and more), area tabs and a full-screen viewer;
  images upload several at a time in Admin > Website; feature cards can carry an image.
- CI fixes: website code formatting, tests always on local storage, exact sign-in buttons in
  browser tests, a longer timeout for the two-sign-in subscription test.

### Next

- Production readiness: AWS KMS and an SMTP provider, then `APP_ENV=production` on Railway;
  a separate Supabase project for production (staging and production never share a database).
- Custom domain for the API and web apps (staff sign-in needs the same site).
- Vercel projects for the six web apps (the website is new: Root Directory `apps/website`).
- Migrations are applied to Supabase by hand from a trusted machine until the GitHub Migrate
  workflow has its secrets.

### Known gaps

- The browser tests in CI were last seen failing on timeouts in the subscription journey;
  the timeout was raised and needs confirming on the next run.

## 2026-10-12: Worldwide hotels (D69), legal documents (D70), locale formatting

### Done

- Hotels anywhere (D69): country required at signup (`GET /countries`, 67 countries) setting
  the data region and suggesting currency, time zone, locale and tax; ISO minor units (0, 2 or
  3 decimals) everywhere money is parsed or printed; tax numbers checked per country; bills
  name the hotel's tax (VAT, GST, IVA...). Signup validation now runs before the email lookup,
  so a known address gets the same answers as a new one.
- Legal documents (D70): platform drafts and publishes versioned terms, privacy notice, DPA,
  acceptable use and guest documents per country (frozen once published); signup and the
  Merchant app require acceptance of current versions; tablets show the guest documents;
  acceptances are append-only and audited. Admin panel screen "Legal documents".
- Formatting follows the hotel: `/auth/me` and the tablet session return `locale`, `timezone`
  and `tax_label`; the apps format money, dates and times with them. Typed amounts accept
  either decimal sign ("1.234,50" and "1,234.50"), refusing extra decimals; unit tests for the
  API client run in CI.
- Diyneco staff accounts (D71): Super Admins invite platform staff, change their roles,
  deactivate and reactivate them from the Admin panel ("Diyneco staff"); invitees set their
  password on `/accept-invite`; the database keeps at least one active Super Admin.
- Subscription billing, slice 1 (D72, D73): Diyneco's company and VAT settings and
  effective-dated tax rates, edited in the Admin panel ("Company & tax") with step-up, a
  reason and an audit trail. Seeded with the company names only.
- Subscription billing, slice 2 (D74): Plans & Pricing in the Admin panel: plan details,
  monthly, quarterly and annual prices with an append-only price history, scheduled
  changes, preview, publish and archive; public `GET /plans`. The Merchant app's plan
  picker now lists published plans from the server instead of fixed names.
- Account separation (D75): separate sign-ins for hotel apps and the Admin panel, kind checks
  on every permission, database triggers keeping the two kinds of account apart, and a test
  that tries every route with the wrong kind of token.
- Sign-out in the Merchant, Admin and room-service apps ends the server session, clears
  cached data and signs out the app's other tabs; the Admin panel has a sign-out on small
  screens and confirms actions with the staff member's password.
- Browser end-to-end tests (`packages/e2e`, Playwright) run in CI against production builds and
  a seeded API: cross-app sign-in refusals, plan pricing and publishing, sign-out.
- Subscription billing, slice 3 (D76): plan-free signup trial with configurable length and
  limits, the eight subscription statuses, agreed-price snapshot and month-end billing
  anchor, server-side quotes with VAT, cancellation and resume, billing contact.
- Subscription billing, slice 4 (D78): Diyneco's invoices and credit notes to hotels: drafts,
  safe gapless numbering, frozen issued invoices, PDFs, email, void and credit rules; hotels
  list and download theirs in the Merchant app (Settings > Plan).
- Subscription billing, slices 5-8 (D79): hotels subscribe from Settings > Plan (compare
  plans, server quote, terms, first invoice), pay online (Stitch Pay by Bank, or the labelled
  sandbox until credentials are set) or by EFT recorded by Diyneco; refunds with credit notes;
  signed, de-duplicated Stitch webhooks; the worker renews, reminds, marks overdue, suspends
  (read-only except billing) and reactivates; billing emails; Admin > Billing & Invoices
  (collected vs invoiced vs outstanding vs MRR, filters, CSV, reconciliation, collections
  policy) and per-hotel billing on the hotel page; browser test of the whole journey.
- API address with fallback (api.diyneco.com, then the Railway address) and a Migrate workflow
  for Supabase (prepare roles, status, upgrade) with a Supabase bootstrap script (D81).
- Deployment on Railway, Vercel, Supabase and AWS KMS (D80): AWS KMS provider for envelope
  encryption; manual Deploy workflow (check the commit, migrate, roll the API and worker,
  deploy the web apps, smoke checks; production behind required reviewers); setup guide with
  every variable in `infra/deployment/README.md`.
- Fixed (D77): confirmed actions with an Idempotency-Key failed after the PIN or password
  prompt because the refusal was replayed to the retry.
- Deployment: container images for all five web apps (`infra/docker/web.Dockerfile`, Next.js
  standalone, non-root) built, started and scanned in CI; `scripts/create_platform_admin.py`
  for the first Super Admin; launch checklist updated.

### Next

- First deployment (owner): domain, Railway project, Vercel projects, Supabase project, AWS
  KMS key, GitHub environments, then Deploy to staging (infra/deployment/README.md).
- Interface translations (message catalogues per language, English first).
- Stitch: run the adapter against a Stitch test client (credentials from the owner), then
  register `https://<api>/api/v1/billing/webhooks/stitch` for PAYMENT events.
- Propose `SUBSCRIPTION_SUSPENDED` (403) for the API spec's error catalogue (D79).

### Known gaps

- `tests/api/test_realtime.py::test_tablet_sees_only_its_room_with_replay_and_live_events`
  failed once under full-suite load on this 2 GB laptop and passed on three reruns: a timing
  margin to widen if it recurs in CI.
- The kitchen display still shows times in the browser's zone (it is always in the hotel).

## 2026-10-10: Gap audit, fixes and full-scale operations screens

### Done

- POPIA: guest export and anonymisation (step-up), daily retention job, encrypted guest ID
  numbers when a hotel opts in (D59, D62).
- Bugs fixed: account emails could not be completed (links plus pasted codes, D60); the daily
  close wiped saved totals on review; changing a subscription wiped custom limits; the
  schedule API returned `from_`.
- Security: Content-Security-Policy, HSTS and COOP on every web app; CI actions on Node 24.
- Merchant: Companies; allergens, option groups, photos, serving hours and category editing on
  the menu; room edit/delete, room-type edit and CSV import; device disable and move; custom
  roles and staff details; room-charge blocks and invoice emails; webhook delivery log;
  hotel address and logo; guest-tablet information pages (D61); Dispatch board; Room rack;
  Housekeeping; arrivals, departures and no-show views; typed daily close with overrides and
  late entries.
- Admin: hotel page (account, owners, usage against limits, custom limits, support access,
  platform actions), activity feed, hotel status filters (D63).

### Next

- Global search, platform staff management, subscription invoicing, image resizing (D32),
  `HEALTH_DEGRADED` events.

## 2026-10-10: Front ends (all five web apps) and currencies

### Done

- Shared packages: `@diyneco/api-client` (typed client, refresh, step-up retry, stable
  idempotency keys, realtime client, currency-agnostic money formatting) and
  `@diyneco/shared-ui` (design tokens, components, PIN step-up dialog).
- Kitchen display, Merchant app, Admin panel, Room-service app (mobile-first) and Guest
  tablet (mobile-first, kiosk) as Next.js web apps (D58). All type-check; the kitchen
  display also completed a production build on this machine.
- Currencies chosen, never assumed (D57): hotel currency at signup and in settings, plan
  billing currency in the Admin panel, MRR per currency, no database default.
- API additions for the apps: `/auth/me`, staff order quote, adjustment queue, charge
  categories, currency catalogue, plan editing.

### Next

- Browser end-to-end tests (Playwright) against a seeded API, and production builds of every
  app in CI.
- Before production: hosting and Supabase region, production KMS, SMTP provider and email
  domain, legal and tax reviews, final plan prices, penetration and load tests.


## 2026-10-10: Phase 9 (Hardening and launch), backend

### Done

- Security suite for build spec section 71 (`tests/security/test_section_71.py`): hotel
  access, cross-tenant requests, device credentials, expired and revoked sessions, privilege
  escalation, checkout, bill changes, discounts, payment changes, replays, duplicate payments
  and duplicate orders, all at the API and, where it matters, the database.
- Restore drill script, run in CI after the tests (D53).
- Sentry monitoring with personal data scrubbed; release tagging.
- Load test (Locust) for the hot paths; provider-neutral deployment and launch guide.
- Exit criteria covered: restore drill succeeds; section 71 security tests pass.

### Next

- The five front-end apps (Merchant, Kitchen, Admin on Next.js; Guest and Room service on
  Expo) on top of the finished API.

### Open before production

- Hosting chosen (D80: Railway, Vercel, Supabase, AWS KMS); accounts, domain, email domain and
  SMTP provider still to set up.
- Legal (POPIA) and tax (VAT, invoicing) reviews; final plan prices.
- External penetration test and a staging load test.


## 2026-10-10: Phase 8 (Reports and API), backend

### Done

- Reports from folio entries and payments: revenue by day and group (discounts, adjustments,
  reversals, VAT, tips apart), payments by method and staff, orders by hour, top items,
  kitchen accept-to-ready times by station, room-service ready-to-delivered by staff,
  occupancy, open balances (accounts receivable), audit log.
- Daily close: report, finance entry of terminal batch total and cash count, review,
  mismatch and override flags; emailed by the worker after 06:00 hotel time.
- API keys (scoped, sandbox read-only, plan-gated production keys, usage tracking) and
  webhooks (HMAC-signed, retried 1 m to 12 h, disabled after a day with owners emailed,
  internal addresses refused), subscription view and plan change requests, admin analytics.
- SMTP email provider.
- Exit criterion covered by a test: the revenue and payments reports reconcile to folio
  entries to the cent, day by day and in total.


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
