# Diyneco — Security and Compliance

2026-10-08 · Profy

Diyneco handles guest identities, hotel money and staff access for many hotels at once, so one hotel's mistake or attacker must never reach another hotel's data, and no one inside a hotel may change a bill unseen. This spec sets the controls that make that true and the South African obligations they serve. It is an engineering specification, not legal advice; an SA attorney and a registered tax practitioner should confirm sections on POPIA and VAT before launch.

## Security principles

Eight rules decide every design choice in this document; when a feature conflicts with one, the rule wins and the feature changes.

1.  **The server is the only authority.** Prices, totals, tips, permissions and tenancy are computed and checked on the server. Clients display; they never decide.

2.  **Isolation is enforced twice.** Every tenant boundary is checked in application code and again by the database, and both are tested.

3.  **Money is append-only.** Financial records are never edited or deleted; corrections are new, approved, audited entries.

4.  **Separation of duties.** The person who requests an adjustment, refund or discount cannot approve it. Kitchen and room-service staff cannot change amounts at all.

5.  **Least data.** Collect only what a feature needs, keep it only as long as the law and the hotel need it, and never store card data.

6.  **Least privilege.** Every principal (staff, device, API key, service, admin) gets only the permissions its job needs, and sensitive actions need a fresh PIN or password.

7.  **Everything sensitive leaves a trail.** Who did what, when, from which device, with old and new values, in a log nobody can edit.

8.  **Fail closed.** When a check cannot be completed (database unreachable, token unverifiable, device unknown), the request is refused, not allowed.

## Threat model

The highest risks are a staff member quietly reducing a bill or pocketing a payment, one hotel reading another's data, and a guest tablet showing the previous guest's stay. Each threat below names the control that answers it and where that control is specified.

| Surface        | Threat (STRIDE)         | Example                                             | Control                                                                                                                                                                      |
|----------------|-------------------------|-----------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Guest tablet   | Spoofing                | Guest or visitor forges requests as another room    | Device credential bound to one room; server derives the room; room is never a request field                                                                                  |
| Guest tablet   | Information disclosure  | Next guest sees previous orders or bill             | All guest queries filter by the active stay; checkout invalidates the session and sends `RESET_ROOM_SESSION`; app keeps no cache across stays                                |
| Guest tablet   | Tampering               | Modified app sends lower prices                     | Server ignores client prices; orders priced from the menu at the server; `quoted_total` mismatch returns `PRICE_CHANGED`                                                     |
| Guest tablet   | Elevation of privilege  | Guest exits kiosk mode and installs tools           | Screen pinning (v1), device-owner mode via MDM (v1.1); credential in Android Keystore; staff can revoke remotely                                                             |
| Room service   | Repudiation / tampering | Staff takes R4,000, records R3,000 and keeps R1,000 | Guest tablet shows the official amount; tip confirmation is explicit and logged with staff id; terminal reference required; end-of-day reconciliation against terminal batch |
| Reception      | Tampering               | Receptionist removes a charge before checkout       | Folio is append-only; reversals need `folio.adjust.approve` by a second person; every change is audited                                                                      |
| Kitchen        | Elevation of privilege  | Kitchen tablet used to view finances                | Kitchen sessions carry only `kitchen.*` permissions and `menu.availability` (sold out, D67); kitchen API payloads contain no prices                                                                                  |
| Merchant app   | Spoofing                | Stolen staff password                               | Lockout, rate limits, MFA required for owners, admins and finance roles; step-up for sensitive actions                                                                       |
| Merchant app   | Information disclosure  | Hotel A staff guesses Hotel B ids                   | Tenant from token only; RLS; cross-tenant ids return `404`; automated tests                                                                                                  |
| API            | Tampering / replay      | Network retry or attacker replays a payment         | `Idempotency-Key` required; one payment per order; HMAC-signed webhooks with timestamp                                                                                       |
| API            | Denial of service       | Flood of pairing or login attempts                  | Per-IP and per-principal rate limits; WAF in front of the API; pairing codes expire in 15 minutes                                                                            |
| Platform admin | Information disclosure  | Diyneco staff browse guest data                     | Admin endpoints return aggregates; support access is time-boxed, ticketed, visible to the hotel and audited                                                                  |
| Platform admin | Elevation of privilege  | Compromised admin account                           | MFA mandatory; admin network allow-list; two-person rule for tenant deletion and key rotation                                                                                |
| Database       | Information disclosure  | Leaked backup                                       | Encryption at rest; guest ID numbers and secrets additionally encrypted at field level; backups encrypted with separate keys                                                 |
| Supply chain   | Tampering               | Malicious dependency                                | Lockfiles, dependency scanning, pinned CI actions, signed builds                                                                                                             |

## Authentication design

Each kind of principal has one credential type with fixed parameters; none of them is ever stored in a form that can be reversed.

| Credential                          | Format and storage                                                                                      | Lifetime                     | Notes                                                                                                                         |
|-------------------------------------|---------------------------------------------------------------------------------------------------------|------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| Staff password                      | Argon2id, memory 64 MiB, 3 iterations, parallelism 1, 16-byte salt; PHC string in `users.password_hash` | Until changed                | Minimum 12 characters; checked against a breached-password list; no composition rules; rehash on login when parameters change |
| Access token                        | JWT, EdDSA (Ed25519), `kid` header                                                                      | 15 minutes                   | Never stored server-side; revocation via short life + `perms_v` + session check on sensitive endpoints                        |
| Refresh token                       | 256-bit random, SHA-256 hash in `sessions.refresh_hash`                                                 | 30 days, sliding             | Rotates on every use; reuse of an old token revokes the whole session family and alerts the user                              |
| Web session cookie                  | `__Host-` prefixed, `Secure`, `HttpOnly`, `SameSite=Strict`                                             | Same as refresh              | Merchant and admin web apps keep tokens out of JavaScript; CSRF blocked by SameSite plus an `Origin` check                    |
| TOTP secret                         | 160-bit, AES-256-GCM envelope-encrypted in `mfa_factors.secret_enc`                                     | Until reset                  | 30-second step, ±1 step drift; last used step stored to block replay; 10 one-time recovery codes, hashed                      |
| Staff PIN                           | 4–6 digits, Argon2id (same parameters), per hotel membership                                            | Until changed                | Only for step-up and kitchen sign-in, never as a login on its own; 5 failures lock it for 15 minutes                          |
| Step-up token                       | JWT, 5 minutes, bound to `sid` and user                                                                 | 5 minutes                    | Single purpose: unlocks endpoints marked Step-up                                                                              |
| Device credential                   | 256-bit random shown once at pairing; SHA-256 hash in `devices.credential_hash`                         | Until revoked                | Exchanged for a 1-hour device JWT; stored on the tablet in Android Keystore via SecureStore                                   |
| Pairing code                        | 6 digits, SHA-256 with server pepper                                                                    | 15 minutes, single use       | Lockout after 5 failures per device or IP                                                                                     |
| API key                             | `dyk_live_` or `dyk_test_` + 32 random bytes base62; SHA-256 hash, prefix kept for display              | Until revoked                | Shown once; scoped to listed permissions; production keys need plan support                                                   |
| Invitation, reset and verify tokens | 256-bit random, SHA-256 hash                                                                            | 7 days, 30 minutes, 24 hours | Single use                                                                                                                    |

**MFA policy:** mandatory for every platform account and for hotel roles Owner, Hotel Admin, General Manager and Finance Manager. Optional but encouraged for other staff. Kitchen and room-service staff on shared devices sign in with their own PIN on a paired device, so actions are still attributed to a person.

**Session limits:** web sessions end after 12 hours of inactivity; kitchen-display staff sessions after 8 hours; a user may have at most 10 active sessions. Deactivating a staff member revokes every session at once.

## Permission catalogue and role matrix

The ten hotel roles below are seeded system roles; hotels may copy and narrow them but never widen one beyond what the creator holds. Permissions marked † are sensitive and always need step-up.

Columns: **Own** Hotel Owner · **Adm** Hotel Admin · **GM** General Manager · **RM** Reception Manager · **Rec** Receptionist · **Fin** Finance Manager · **KM** Kitchen Manager · **KS** Kitchen Staff · **SM** Room-Service Manager · **SS** Room-Service Staff.

| Permission               | Own | Adm | GM  | RM  | Rec | Fin | KM  | KS  | SM  | SS  |
|--------------------------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| `hotel.read`             | ●   | ●   | ●   | ●   | ●   | ●   | ●   |     | ●   |     |
| `hotel.update`           | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `settings.read`          | ●   | ●   | ●   | ●   |     | ●   |     |     |     |     |
| `settings.update` †      | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `rooms.read`             | ●   | ●   | ●   | ●   | ●   | ●   |     |     | ●   |     |
| `rooms.manage`           | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `rooms.status`           | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `devices.read`           | ●   | ●   | ●   | ●   | ●   |     | ●   |     |     |     |
| `devices.manage`         | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `staff.read`             | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `staff.manage` †         | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `roles.manage` †         | ●   | ●   |     |     |     |     |     |     |     |     |
| `guests.read`            | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `guests.manage`          | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `privacy.manage` †       | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `billing.manage`         | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `stays.read`             | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `stays.manage`           | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `stays.rate_override`    | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `menu.read`              | ●   | ●   | ●   | ●   | ●   |     | ●   | ●   | ●   |     |
| `menu.manage`            | ●   | ●   | ●   |     |     |     | ●   |     |     |     |
| `menu.price.update` †    | ●   | ●   | ●   |     |     |     |     |     |     |     |
| `menu.availability`      | ●   | ●   | ●   | ●   |     |     | ●   | ●   |     |     |
| `menu.certify`           | ●   | ●   | ●   |     |     |     | ●   |     |     |     |
| `kitchen.manage`         | ●   | ●   | ●   |     |     |     | ●   |     |     |     |
| `kitchen.view`           | ●   | ●   | ●   |     |     |     | ●   | ●   |     |     |
| `kitchen.update`         | ●   | ●   | ●   |     |     |     | ●   | ●   |     |     |
| `orders.read`            | ●   | ●   | ●   | ●   | ●   | ●   | ●   |     | ●   |     |
| `orders.create`          | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `orders.approve` †       | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `orders.cancel` †        | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `deliveries.view`        | ●   | ●   | ●   | ●   | ●   |     |     |     | ●   | ●   |
| `deliveries.update`      | ●   | ●   | ●   |     |     |     |     |     | ●   | ●   |
| `deliveries.manage`      | ●   | ●   | ●   |     |     |     |     |     | ●   |     |
| `folio.read`             | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `folio.charge`           | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `folio.discount` †       | ●   | ●   | ●   | ●   |     | ●   |     |     |     |     |
| `folio.adjust.request`   | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `folio.adjust.approve` † | ●   | ●   | ●   | ●   |     | ●   |     |     |     |     |
| `payments.record`        | ●   | ●   | ●   | ●   | ●   | ●   |     |     | ●   | ●   |
| `payments.read`          | ●   | ●   | ●   | ●   | ●   | ●   |     |     | ●   |     |
| `checkout.perform` †     | ●   | ●   | ●   | ●   | ●   |     |     |     |     |     |
| `checkout.override` †    | ●   | ●   | ●   | ●   |     |     |     |     |     |     |
| `invoices.read`          | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `invoices.send`          | ●   | ●   | ●   | ●   | ●   | ●   |     |     |     |     |
| `invoices.credit` †      | ●   | ●   | ●   |     |     | ●   |     |     |     |     |
| `reports.read`           | ●   | ●   | ●   | ●   |     | ●   | ●   |     | ●   |     |
| `reports.finance`        | ●   | ●   | ●   |     |     | ●   |     |     |     |     |
| `audit.read`             | ●   | ●   | ●   | ●   |     | ●   |     |     |     |     |
| `subscription.read`      | ●   | ●   | ●   |     |     | ●   |     |     |     |     |
| `subscription.manage`    | ●   |     |     |     |     |     |     |     |     |     |
| `integrations.manage` †  | ●   | ●   |     |     |     |     |     |     |     |     |

**Platform roles** (Diyneco staff, separate from every hotel): Platform Super Admin holds all `platform.*` permissions; Platform Support holds `platform.metrics`, `platform.tenants.read` and `platform.support`. Neither role holds any hotel permission; support access to a hotel is a separate, time-boxed grant.

**Hard limits that no role can lift:** nobody approves their own adjustment; kitchen sessions never receive prices; room-service staff record a payment only for an order assigned to them; a role editor cannot grant a permission they lack.

## Tenant isolation

A request can only ever touch one hotel, and that hotel comes from who is asking, not from anything in the request. The spec's five enforcement points map to these controls:

| Layer            | Control                                                                                                                            | Proof                                                                       |
|------------------|------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| Authentication   | Token carries `hid`; device tokens carry the bound hotel and room; API keys belong to one hotel                                    | Unit tests on token issuance                                                |
| API routing      | No hotel-scoped route accepts a hotel id in path or body; a dependency injects `TenantContext` from the principal                  | Static check fails CI if a router function takes `hotel_id` as input        |
| Repositories     | Every repository method requires `TenantContext` and adds `WHERE hotel_id = :hid`; there is no unscoped query helper               | Code review checklist; repository tests per method                          |
| Database         | RLS policy on every table with `hotel_id`, `FORCE ROW LEVEL SECURITY`, composite foreign keys `(hotel_id, id)`                     | CI check that every such table has a policy; RLS tests run as `diyneco_api` |
| Frontend routing | Web apps scope cache keys and routes by the active hotel; switching hotel clears query caches                                      | Component tests                                                             |
| Realtime         | Channel names include the hotel id; the gateway checks the principal may join before subscribing                                   | WebSocket tests with cross-tenant subscribe attempts                        |
| Storage          | Object keys are `hotels/{hotel_id}/...` in private buckets; downloads use signed URLs minted after a tenant check, valid 5 minutes | Tests fetch another hotel's key and expect refusal                          |
| Background jobs  | Each job payload carries `hotel_id`; the worker sets the same RLS context before touching data                                     | Job tests                                                                   |

**Required automated tests (run on every pull request):** for every endpoint that takes a resource id, a test calls it with a valid id from a second hotel and expects `404`; for every list endpoint, a test seeds two hotels and checks only the caller's rows return; a raw-SQL test as `diyneco_api` with `app.hotel_id` unset expects zero rows from every tenant table.

## Data protection

All data is encrypted in transit and at rest by default, and the few fields whose leak would cause real harm get a second layer of encryption under keys the database never sees.

| Area            | Control                                                                                                                                                                                                                                                 |
|-----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| In transit      | TLS 1.2+ everywhere (TLS 1.3 preferred), HSTS with preload on all web origins, no plain HTTP endpoints. Database connections require TLS.                                                                                                               |
| At rest         | Supabase-managed disk encryption (AES-256) for the database, backups and storage buckets.                                                                                                                                                               |
| Field-level     | Guest ID numbers, TOTP secrets and webhook signing secrets use AES-256-GCM envelope encryption: a data key per hotel, wrapped by a master key in a cloud key management service. The API decrypts only when a feature needs the value.                  |
| Hashing         | Passwords and PINs: Argon2id. Tokens, device credentials, pairing codes, API keys: SHA-256 (they are already high-entropy, or protected by expiry and lockout).                                                                                         |
| Secrets         | Held in the hosting provider's secret manager and injected at runtime. Never in code, images, logs or `.env` files outside development. `SUPABASE_SERVICE_ROLE_KEY` exists only in backend and worker environments.                                     |
| Key rotation    | JWT signing keys every 90 days with overlap via `kid`; data-wrapping master key yearly; database and service credentials every 90 days or immediately on staff departure.                                                                               |
| Storage buckets | `hotel-assets` (logos, menu images): private, served by signed URLs or a CDN with signed requests. `invoices`: private, signed URLs valid 5 minutes. No public buckets.                                                                                 |
| Logging         | Request logs record ids, status, timing and principal, never request bodies on payment, auth or guest endpoints. A log filter redacts emails, phone numbers, tokens and anything matching a card-number pattern.                                        |
| Browser apps    | Content-Security-Policy with no inline scripts, `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` disabling camera, microphone and geolocation except where needed. |
| CORS            | Explicit allow-list of Diyneco web origins per environment; no wildcards; credentials only for the merchant and admin origins.                                                                                                                          |
| Mobile apps     | Certificate pinning to the API's public key set with a backup pin; no tokens in AsyncStorage; screenshots blocked on screens showing bills.                                                                                                             |

## Device and kiosk security

A guest tablet sits in a room used by strangers, so it holds nothing worth stealing: no staff credentials, no guest history, and a device credential the hotel can revoke from the merchant app in seconds.

**Guest tablet**

- **Lockdown, v1:** Android screen pinning with a staff-only exit PIN, launcher set to the Guest App, notifications and status bar hidden, USB debugging off. **v1.1:** provisioned as device owner through an MDM (Android Enterprise dedicated device), which also allows remote wipe and silent app updates.

- **Credential:** stored in Android Keystore via SecureStore; never logged; exchanged for a 1-hour device JWT. Revoked credentials stop working on the next request.

- **No guest data at rest across stays:** the app holds the current menu and the active stay's orders in memory and an encrypted query cache keyed by `stay_id`. On `RESET_ROOM_SESSION`, a `4409` close code, or a `stay_id` change, it wipes the cache and returns to the welcome screen. History is fetched fresh from the server, which returns only the active stay.

- **Offline:** the tablet shows an offline banner and disables Place order; queued orders are not allowed, so there is nothing to replay later.

- **Physical:** hotels are advised to use a tamper-resistant mount and a dedicated power supply. A tablet reported missing is revoked and its room re-paired.

**Kitchen display:** paired to stations, not rooms. The device credential alone only shows the board; acting on it needs a staff PIN sign-in, so every accept and ready is attributed to a person. The session ends after 8 hours or when another staff member signs in.

**Staff phones (room service):** personal or hotel-owned phones sign in with the staff member's own account. Biometric unlock may gate the stored refresh token. Assigned deliveries are cached for offline viewing; payments can only be recorded online, with an idempotency key generated when the payment form opens.

## Financial integrity and anti-theft controls

Transparent billing is a product feature: the guest, the kitchen, room service and management see one transaction from one source, and any change to it is visible, approved and attributed.

| Risk                                                            | Preventive control                                                                  | Detective control                                                                                      |
|-----------------------------------------------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Staff quotes the guest a higher amount and keeps the difference | Guest tablet shows the official amount due for every order                          | Tips per staff member in reports; tips above 25% of the bill or above R500 flagged on the daily report |
| Staff records less than the terminal took                       | Terminal reference required; amount received entered once and confirmed             | Daily reconciliation of card payments against the terminal batch total, per staff member               |
| Charge removed before checkout                                  | Folio is append-only; removal needs a reversing entry approved by a second person   | Every reversal and adjustment listed on the daily report with requester and approver                   |
| Discount given to friends                                       | `folio.discount` limited to managers and finance, step-up, reason required          | Discounts by staff and by guest in the weekly report                                                   |
| Order placed and "lost"                                         | Every order has a status history; cancellation only before preparation, with reason | Orders cancelled after acceptance shown as exceptions                                                  |
| Checkout with unpaid balance                                    | Blocked unless policy allows override, reason given, `checkout.override` held       | Overrides on the daily report; balance carried to an accounts-receivable list                          |
| Price changed to manipulate an order                            | Orders snapshot prices; price changes audited with old and new value                | Price changes listed in the audit log and weekly report                                                |
| Duplicate payment or tip from a retry                           | Idempotency key; one payment per order                                              | Payments with identical amount, room and minute flagged                                                |

**Daily close report** (per hotel, emailed to Finance and the GM at 06:00 hotel time): revenue by category, payments by method and staff, tips by staff, card total versus terminal batch total (entered by finance), adjustments, discounts, cancellations, overrides, open balances on checked-out stays, and any flagged anomalies. The report itself is generated from folio entries, so it cannot disagree with the bills.

## POPIA programme

Under the Protection of Personal Information Act 4 of 2013, each hotel is the responsible party for its guests' and staff's information, and Diyneco processes it on the hotel's behalf as an operator. Diyneco is itself the responsible party for its own customers' account data (hotel owners and staff logins) and its platform logs.

**Obligations and how Diyneco meets them**

| Obligation                                    | What Diyneco does                                                                                                                                                                                                                                       |
|-----------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Operator agreement (sections 20–21)           | Data Processing Agreement accepted in onboarding: process only on the hotel's instructions, keep it confidential, apply the safeguards in this spec, notify the hotel of any compromise without delay. Acceptance is logged with version and timestamp. |
| Information Officer                           | Diyneco registers its Information Officer with the Information Regulator and publishes contact details. Hotels are reminded during onboarding to register their own.                                                                                    |
| Processing limitation and minimality          | Guest record holds name and, optionally, email and phone. ID or passport number only if the hotel turns it on. No guest dietary, health, religious or other special personal information is stored; allergens describe menu items, not guests.          |
| Purpose specification                         | Guest data is used for the stay, billing and the hotel's legal records only. No marketing use; any future marketing feature needs separate opt-in consent.                                                                                              |
| Security safeguards                           | The controls in this spec, reviewed annually and after any incident.                                                                                                                                                                                    |
| Data subject participation                    | Hotel staff with `privacy.manage` can export everything held on a guest and correct or anonymise it. Diyneco support assists within 5 business days of a hotel's request.                                                                               |
| Security compromise notification (section 22) | See the Data Breach runbook: hotels notified within 24 hours of Diyneco confirming a compromise, so they can notify the Regulator and guests as soon as reasonably possible.                                                                            |
| Cross-border transfer (section 72)            | The hosting region is disclosed in the DPA. If data is stored outside South Africa, the DPA includes binding protections equivalent to POPIA, and the hotel acknowledges the transfer.                                                                  |
| Children                                      | The product does not ask for guests' ages or dates of birth; minors are recorded only as part of an adult's stay if at all.                                                                                                                             |
| Retention                                     | Kept no longer than needed: personal fields anonymised after the hotel's retention period (default 5 years after the last stay), financial amounts kept for tax law.                                                                                    |

**Personal data inventory**

| Data                        | Whose            | Purpose                               | Who can see it                                                   | Retention                                                     |
|-----------------------------|------------------|---------------------------------------|------------------------------------------------------------------|---------------------------------------------------------------|
| Name                        | Guest            | Stay, bill                            | Reception, managers, finance; guest tablet shows first name only | Hotel retention period                                        |
| Email, phone                | Guest            | Bill delivery, contact during stay    | Reception, managers, finance                                     | Hotel retention period                                        |
| ID or passport number       | Guest (optional) | Hotel's legal or security requirement | Managers only; encrypted                                         | Hotel retention period, or shorter if set                     |
| Company billing details     | Company          | Invoicing                             | Reception, finance                                               | 5 years after last invoice                                    |
| Orders and folio            | Guest            | Billing                               | Staff by permission; guest during stay only                      | Amounts 5 years; links to guest anonymised with the guest     |
| Staff name, email, PIN hash | Staff            | Access, attribution                   | Hotel admins                                                     | Membership + 1 year, then anonymised; audit actor labels kept |
| Audit actor, IP, device     | Staff, devices   | Security and accountability           | Hotel admins, finance; Diyneco under support grant               | 7 years                                                       |
| Platform account data       | Hotel owners     | Contract, billing                     | Diyneco                                                          | Contract + 5 years                                            |

## VAT, invoicing and record retention

Diyneco never decides a hotel's tax position; it applies the hotel's settings consistently and refuses to issue a document labelled "Tax Invoice" unless the hotel has said it is a VAT vendor and given its VAT number. The rules below reflect our understanding of the VAT Act and Tax Administration Act and must be confirmed by a registered tax practitioner.

| Topic                  | How the platform handles it                                                                                                                                                                                                                                                                                                                                            |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VAT rate               | Stored per hotel as basis points (default 1500 = 15%) and snapshotted on every folio entry, so a future rate change applies from its effective date without altering old bills.                                                                                                                                                                                        |
| Which documents        | Not VAT-registered: "Guest Statement". VAT-registered: "Tax Invoice". For totals at or under the configured abridged threshold (default R5,000), an abridged tax invoice without recipient details is allowed; above it, a full tax invoice with the recipient's name, address and VAT number (when the recipient is a VAT vendor). Thresholds are hotel-configurable. |
| Required fields        | The words "Tax Invoice", supplier name, address and VAT number, recipient details where required, sequential serial number, issue date, description of supplies, value, VAT amount or a statement that VAT is included at the rate applied.                                                                                                                            |
| Numbering              | Gap-free sequence per hotel and year (`invoice_sequences` row locked inside the checkout transaction). Voided numbers are never reused; corrections use credit notes.                                                                                                                                                                                                  |
| Tips                   | Recorded separately and excluded from VAT and from hotel revenue, on the basis that a voluntary tip is not payment for a supply. A compulsory service charge, by contrast, is a normal charge and carries VAT.                                                                                                                                                         |
| Room-service fee       | A charge for a supply; VAT applies like food.                                                                                                                                                                                                                                                                                                                          |
| Long stays             | VAT treatment of commercial accommodation for stays longer than 28 days differs; the platform flags such stays at checkout for the hotel to confirm treatment. Automatic handling is out of scope for v1.                                                                                                                                                              |
| Corporate billing      | Company name, VAT number, address, purchase order and traveller appear on the invoice when billing type is company.                                                                                                                                                                                                                                                    |
| Retention              | Invoices, credit notes, folio entries and payments kept at least 5 years, matching the general record-keeping period in the Tax Administration Act; the platform default is 7 years for audit logs.                                                                                                                                                                    |
| Voluntary tourism levy | Not built in. If a hotel participates in a voluntary levy scheme, it can be added as a charge category.                                                                                                                                                                                                                                                                |

## PCI DSS scope

Diyneco v1 never stores, processes or transmits cardholder data, so the platform aims to stay out of PCI DSS scope; the card terminal remains the hotel's own standalone device and the hotel's acquirer relationship.

- **What Diyneco records for a card payment:** amount due, amount received, tip, method (`card_terminal`), the terminal approval reference, staff member, time. Nothing else from the card.

- **What Diyneco refuses:** any request field matching a card number pattern (13–19 digits passing a Luhn check), CVV or PIN fields. The API returns `CARD_DATA_REJECTED` and logs a security event without the value.

- **Hotel responsibility:** the hotel's terminal, acquirer agreement and its own PCI self-assessment are unchanged by Diyneco.

- **Future online payments or integrated terminals:** use a payment provider's hosted fields, redirect or terminal SDK so card data goes straight to the provider; Diyneco keeps only tokens and references. A scope review is required before any such integration ships.

## Secure development and security testing

Security checks run on every pull request, and nothing reaches production without passing them and a second person's review.

**Pipeline gates**

| Gate            | Tool class                                                                    | Blocks merge when                                                                    |
|-----------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Code review     | Required reviewer; security reviewer for auth, billing, tenancy or migrations | Not approved                                                                         |
| Static analysis | Python and TypeScript SAST with security rules                                | High-severity finding                                                                |
| Dependency scan | Lockfile audit for Python, npm and Expo packages                              | Known high or critical vulnerability with a fix available                            |
| Secret scan     | Pre-commit and CI secret scanner                                              | Any secret detected                                                                  |
| Migration check | Custom script                                                                 | Table with `hotel_id` lacks an RLS policy; financial table lacks append-only trigger |
| Tenant tests    | Pytest suite                                                                  | Any cross-tenant test fails                                                          |
| Container scan  | Image scanner on the backend image                                            | Critical OS package vulnerability                                                    |
| Dynamic scan    | DAST against staging, weekly                                                  | High finding unresolved after 7 days                                                 |

**Security test cases (spec section 71), automated in CI**

| Case                                                                       | Expected result                                                      |
|----------------------------------------------------------------------------|----------------------------------------------------------------------|
| Hotel A token requests Hotel B order, stay, folio, room, device, menu item | `404 NOT_FOUND`                                                      |
| Hotel A token lists orders while Hotel B has orders                        | Only Hotel A rows                                                    |
| Forged, expired or revoked device credential                               | `401 DEVICE_UNAUTHORISED`                                            |
| Device rebound to another room uses its old token                          | `401`; socket closed `4409`                                          |
| Expired access token; reused refresh token                                 | `401`; whole session family revoked                                  |
| Receptionist calls a `roles.manage` or `folio.adjust.approve` endpoint     | `403 PERMISSION_DENIED`                                              |
| Staff grants a permission they lack via a custom role                      | `403`                                                                |
| Checkout without step-up, wrong PIN, with balance and no override          | `403 STEP_UP_REQUIRED`, `403 PIN_INVALID`, `409 OUTSTANDING_BALANCE` |
| Kitchen session sends a price or calls a folio endpoint                    | `400` (unknown field) or `403`                                       |
| Room service records payment on an order assigned to someone else          | `403`                                                                |
| Requester approves own adjustment                                          | `403 SELF_APPROVAL`                                                  |
| Direct SQL `UPDATE` or `DELETE` on `folio_entries` as `diyneco_api`        | Permission denied                                                    |
| Same payment replayed with the same key; with a new key                    | Original response returned; `409 ALREADY_PAID`                       |
| Same order replayed with the same key                                      | Original order returned, no second order                             |
| Card number in any request field                                           | `400 CARD_DATA_REJECTED`                                             |
| 11 logins in a minute from one IP                                          | `429 RATE_LIMITED`                                                   |

**External testing:** an independent penetration test before production launch (scope: API, web apps, guest tablet, WebSocket, tenant isolation), then annually and after major changes. Critical findings are fixed before launch; high findings within 30 days.

**Vulnerability disclosure:** `security@diyneco.com` and a `security.txt` file; acknowledgement within 2 business days.

## Security monitoring and alerting

Security events are structured log records with a fixed `event` name, shipped to the monitoring stack and kept for 1 year; the ones below raise alerts. Response steps live in the Operations Runbooks.

| Event                                          | Alert when                                                                                   | Severity                                    |
|------------------------------------------------|----------------------------------------------------------------------------------------------|---------------------------------------------|
| `auth.login_failed`                            | 50 failures for one account in 1 hour, or 500 platform-wide in 10 minutes                    | High                                        |
| `auth.refresh_reuse`                           | Any occurrence                                                                               | High; session family already revoked        |
| `auth.pin_locked`                              | 3 PIN lockouts at one hotel in 1 hour                                                        | Medium                                      |
| `tenant.cross_access_denied`                   | Any `404` from a cross-tenant id on a sensitive resource, more than 5 per principal per hour | High                                        |
| `db.append_only_violation` (SQLSTATE P0001)    | Any occurrence                                                                               | Critical; the API should never attempt this |
| `db.locked_order_change` (P0003)               | Any occurrence                                                                               | Critical                                    |
| `device.credential_invalid`                    | 20 from one IP in 10 minutes                                                                 | Medium                                      |
| `device.pairing_failed`                        | 10 from one IP in 10 minutes                                                                 | Medium                                      |
| `payment.card_data_rejected`                   | Any occurrence                                                                               | High; investigate the client that sent it   |
| `admin.support_access_granted`                 | Any occurrence                                                                               | Info; notify the hotel's owner              |
| `admin.tenant_suspended`                       | Any occurrence                                                                               | Info                                        |
| `finance.anomaly`                              | Daily report flags (tip ratio, terminal mismatch, overrides)                                 | Medium; sent to the hotel, not paged        |
| `rbac.role_changed` with sensitive permissions | Any occurrence                                                                               | Info; notify hotel owner by email           |

**Severity meaning:** Critical pages the on-call engineer immediately, day or night. High pages during business hours and opens an incident ticket outside them. Medium and Info go to the security channel and the weekly review.
