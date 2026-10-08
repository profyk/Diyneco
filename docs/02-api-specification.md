# Diyneco — API Specification v1

Oct 8, 2026 · @Profy D Keakile

Every Diyneco interface talks to one versioned REST API at `/api/v1` plus one WebSocket. This spec is the contract the FastAPI backend implements and the TypeScript clients are generated from; the OpenAPI document produced by the code must match it.

## Conventions

Every rule here applies to every endpoint unless the endpoint says otherwise.

| Topic | Rule |
| --- | --- |
| Base URL | `https://api.diyneco.com/api/v1` (prod), `https://api.staging.diyneco.com/api/v1` (staging). JSON only, UTF-8. |
| Versioning | Breaking changes ship as `/api/v2`. Additive fields may appear in v1 at any time; clients must ignore unknown fields. Deprecations carry a `Deprecation` and `Sunset` header for at least 90 days. |
| Principals | `Authorization: Bearer <token>`. Token kinds: `staff` (hotel user), `platform` (Diyneco admin), `device` (guest tablet or kitchen display), `api_key` (hotel integration, header `X-Api-Key`). Each endpoint lists which kinds it accepts. |
| Tenancy | Hotel endpoints never take a hotel id. The hotel comes from the principal. A staff user who belongs to several hotels sends `X-Hotel-Id`, and the server checks membership. Cross-tenant ids return `404 NOT_FOUND`, never `403`, so existence does not leak. |
| IDs | UUIDv7 strings. Human numbers (order #10482, invoice GEH-2026-000123) are separate fields and never used as path keys. |
| Money | Always an object: `{"amount_minor": 300000, "currency": "ZAR"}`. Integers only. Clients never compute totals the server returns. |
| Time | ISO 8601 in UTC with `Z`. The hotel's IANA time zone (`Africa/Johannesburg`) is in hotel settings and used for schedules, business days and reports. |
| Pagination | Cursor based: `?limit=50&cursor=<opaque>`. Response: `{"data": [...], "next_cursor": "..." or null}`. Max limit 200. |
| Filtering and sort | `?status=READY&room_id=...&from=...&to=...&sort=-created_at`. Only documented filters are accepted; unknown ones return `400 VALIDATION_FAILED`. |
| Idempotency | `Idempotency-Key: <uuid>` is required on every endpoint marked Idem. Same key + same body within 24 h returns the original status and body with `Idempotent-Replayed: true`. Same key + different body returns `409 IDEMPOTENCY_CONFLICT`. A request still in flight with that key returns `409 IDEMPOTENCY_IN_PROGRESS`. |
| Concurrency | Mutable resources return `ETag`. Updates (`PATCH`) require `If-Match`; a stale tag returns `412 PRECONDITION_FAILED`. |
| Step-up | Endpoints marked Step-up need header `X-Step-Up: <token>` from `POST /auth/step-up`, valid 5 minutes and bound to the user. |
| Rate limits | Per principal and per IP. Headers: `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`. Excess returns `429 RATE_LIMITED` with `Retry-After`. Defaults: staff 600/min, device 120/min, api\_key per plan, auth endpoints 10/min per IP. |
| Request id | Server sets `X-Request-Id` on every response and in every error body. Clients may send their own for tracing. |
| Errors | Non-2xx bodies are always `{"error": {"code": "ROOM_CHARGE_LIMIT", "message": "Orders over R500.00 need manager approval", "request_id": "...", "details": {...}}}`. Messages are safe to show users; `details` holds field errors. Stack traces and SQL never appear. |

In the tables that follow, **Perm** is the permission the principal must hold, **Idem** marks idempotent writes, and **Step-up** marks endpoints that need a fresh PIN or password.

## Authentication and sessions

Staff sign in with email and password, platform admins always add TOTP, and sensitive actions take a short-lived step-up token from a PIN or password. Access tokens last 15 minutes; refresh tokens rotate on every use and a reused refresh token revokes the whole session family.

| Method | Path | Principal | Perm | Idem | Purpose |
| --- | --- | --- | --- | --- | --- |
| POST | `/auth/login` | none | — | — | Email + password. Returns tokens, or `{mfa_required: true, mfa_token}` |
| POST | `/auth/mfa/verify` | none | — | — | `mfa_token` + 6-digit TOTP code → tokens |
| POST | `/auth/mfa/enroll` | staff, platform | self | — | Returns TOTP secret + otpauth URI; confirm with `/auth/mfa/verify` |
| POST | `/auth/refresh` | none | — | — | Refresh token (httpOnly cookie on web, body on mobile) → new pair |
| POST | `/auth/logout` | staff, platform | self | — | Revokes the current session |
| GET | `/auth/sessions` | staff, platform | self | — | Lists own sessions: device, IP, last used |
| DELETE | `/auth/sessions/{id}` | staff, platform | self | — | Revokes one session |
| POST | `/auth/step-up` | staff, platform | self | — | `{pin}` or `{password}` → `{step_up_token, expires_at}` (5 min) |
| PUT | `/auth/pin` | staff | self + Step-up | — | Set or change own 4–6 digit PIN |
| POST | `/auth/password/forgot` | none | — | — | Always returns 202, whether or not the email exists |
| POST | `/auth/password/reset` | none | — | — | One-time token (30 min) + new password; revokes all sessions |
| POST | `/auth/email/verify` | none | — | — | One-time token from email |
| POST | `/auth/invitations/{token}/accept` | none | — | Idem | Staff sets name, password, PIN; joins the hotel with invited roles |
| POST | `/auth/kitchen/sign-in` | device (kitchen) | — | — | Staff PIN on a kitchen display → 8-hour staff session bound to that device |

**Login response**

```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "rt_...",
  "user": {"id": "0192...", "name": "Naledi K.", "email": "naledi@grandexample.example"},
  "hotels": [{"id": "0191...", "name": "Grand Example Hotel", "roles": ["general_manager"]}]
}
```

**Access token claims:** `sub` (user id), `kind` (`staff`, `platform`, `device`), `sid` (session id), `hid` (active hotel id, staff only), `perms_v` (permission version; a role change bumps it and forces refresh), `amr` (`pwd`, `mfa`), `iat`, `exp`. Signed with EdDSA; `kid` in the header supports key rotation.

**Lockout:** 5 failed passwords in 15 minutes locks the account for 15 minutes and emails the user. 5 failed PINs locks that PIN for 15 minutes. All failures are logged as security events.

## Hotel, settings and onboarding

A new owner signs up, creates a hotel, and the onboarding wizard tracks which of the 11 setup steps are complete. Hotel status is `pending_approval` until Diyneco approves it; a pending hotel can configure everything but its tablets cannot take orders.

| Method | Path | Principal | Perm | Idem | Purpose |
| --- | --- | --- | --- | --- | --- |
| POST | `/signup` | none | — | Idem | Owner account + hotel in one call; sends verification email |
| GET | `/hotel` | staff | `hotel.read` | — | Name, address, contacts, logo URL, status, plan |
| PATCH | `/hotel` | staff | `hotel.update` | — | Profile fields; audited |
| POST | `/hotel/logo` | staff | `hotel.update` | — | Returns a signed upload URL (PNG/SVG/JPEG, max 2 MB) |
| GET | `/hotel/settings` | staff | `settings.read` | — | All operational settings |
| PATCH | `/hotel/settings` | staff | `settings.update` + Step-up | — | Audited per field |
| GET | `/hotel/onboarding` | staff | `hotel.read` | — | Step list with `done` flags and next step |

**Settings object**

```json
{
  "timezone": "Africa/Johannesburg",
  "currency": "ZAR",
  "vat_registered": true,
  "vat_number": "4123456789",
  "vat_rate_bp": 1500,
  "accommodation_rates_include_vat": false,
  "menu_prices_include_vat": true,
  "room_charging_enabled": true,
  "room_charge_auto_approve_limit": {"amount_minor": 50000, "currency": "ZAR"},
  "room_service_fee": {"amount_minor": 5000, "currency": "ZAR"},
  "checkout_override_allowed": true,
  "room_status_after_checkout": "cleaning",
  "checkout_time": "10:00",
  "wifi_name": "GrandGuest",
  "invoice_prefix": "GEH",
  "abridged_invoice_max": {"amount_minor": 500000, "currency": "ZAR"},
  "guest_data_retention_days": 1825
}
```

`vat_rate_bp` is basis points (1500 = 15%) so the rate is an integer and can change by date without code. **Onboarding steps:** account, hotel profile, settings, room types, rooms, menu, kitchen stations, devices, staff invites, tablet pairing, room charging.

## Rooms and room types

Rooms can be created one at a time, as number ranges, or from a CSV; every bulk call either creates all rows or none. Occupancy (`occupied`) is set only by check-in and checkout, never by these endpoints.

| Method | Path | Principal | Perm | Idem | Purpose |
| --- | --- | --- | --- | --- | --- |
| GET | `/room-types` | staff | `rooms.read` | — | List |
| POST | `/room-types` | staff | `rooms.manage` | Idem | Name, base rate, capacity, amenities |
| PATCH | `/room-types/{id}` | staff | `rooms.manage` + Step-up if rate changes | — | Rate change applies to new stays only; audited |
| GET | `/rooms` | staff | `rooms.read` | — | Filters: `status`, `floor`, `room_type_id` |
| POST | `/rooms` | staff | `rooms.manage` | Idem | One room |
| POST | `/rooms/bulk` | staff | `rooms.manage` | Idem | Ranges, e.g. `{"ranges": [{"from": 301, "to": 350, "floor": 3, "room_type_id": "..."}]}`; max 2,000 rooms per call |
| POST | `/rooms/import` | staff | `rooms.manage` | Idem | CSV upload. Returns a dry-run report first; `?commit=true` applies it |
| PATCH | `/rooms/{id}` | staff | `rooms.manage` | — | Number, floor, type, amenities, capacity |
| POST | `/rooms/{id}/status` | staff | `rooms.status` | — | `available`, `reserved`, `cleaning`, `maintenance`, `out_of_service`; rejected if the room has an active stay |
| DELETE | `/rooms/{id}` | staff | `rooms.manage` + Step-up | — | Soft delete; rejected if the room has ever had a stay |

**CSV columns:** `room_number,floor,room_type,rate,capacity,amenities` (amenities separated by `|`). Rate is in rands with up to 2 decimals and is converted to minor units on import. Duplicate room numbers, unknown room types and bad rates are reported per line; nothing is written until the report is clean.

## Devices

A tablet becomes a trusted device only by redeeming a single-use pairing code issued for one room; the server then binds device, hotel and room and returns a device credential once. Every later device request is checked against that binding.

| Method | Path | Principal | Perm | Idem | Purpose |
| --- | --- | --- | --- | --- | --- |
| GET | `/devices` | staff | `devices.read` | — | Filters: `type` (`guest`, `kitchen`), `status`, `room_id` |
| POST | `/devices/pairings` | staff | `devices.manage` | Idem | `{type, room_id \| station_id}` → `{code, qr_payload, expires_at}` (15 min, single use) |
| POST | `/devices/pair` | none | — | Idem | `{code, device_info}` → `{device_id, device_credential, hotel, room}`; credential shown once |
| POST | `/devices/heartbeat` | device | — | — | Every 30 s: app version, battery, network. Returns pending commands (`RESET`, `LOCK`) |
| POST | `/devices/{id}/lock` | staff | `devices.manage` | — | Guest screen shows "paused"; publishes `DEVICE_LOCKED` |
| POST | `/devices/{id}/unlock` | staff | `devices.manage` | — |  |
| POST | `/devices/{id}/reset` | staff | `devices.manage` | — | Clears guest session and local cache; publishes `RESET_ROOM_SESSION` |
| POST | `/devices/{id}/reassign` | staff | `devices.manage` + Step-up | — | Move to another room; old room's binding ends |
| POST | `/devices/{id}/disable` | staff | `devices.manage` | — | Credential rejected until re-enabled |
| DELETE | `/devices/{id}/pairing` | staff | `devices.manage` + Step-up | — | Unpair; credential revoked permanently |

**Device states:** `online` and `offline` are derived from `last_seen_at` (offline after 90 s without a heartbeat). Stored states are `active`, `locked`, `disabled`, `reset_required` and `revoked`; a device with no binding shows as `needs_pairing`.

**Device request checks**, in order: credential valid and not revoked → device enabled → hotel active → device still bound to this room → room still exists. Any failure returns `401 DEVICE_UNAUTHORISED` or `403 DEVICE_DISABLED`, and the app falls back to its pairing or paused screen.

## Staff, roles and permissions

Staff join by invitation and receive roles; a role is a named bundle of permissions, and authorisation always checks the permission, never the role name. A user can never grant a permission they do not hold themselves.

| Method | Path | Principal | Perm | Idem | Purpose |
| --- | --- | --- | --- | --- | --- |
| GET | `/staff` | staff | `staff.read` | — | Members with roles, department, status, last sign-in |
| POST | `/staff/invitations` | staff | `staff.manage` | Idem | `{name, email, department, role_ids}` → invitation email, valid 7 days |
| GET | `/staff/invitations` | staff | `staff.read` | — | Pending invitations |
| DELETE | `/staff/invitations/{id}` | staff | `staff.manage` | — | Cancel |
| PATCH | `/staff/{user_id}` | staff | `staff.manage` | — | Department, display name |
| PUT | `/staff/{user_id}/roles` | staff | `staff.manage` + Step-up | — | Replace roles; bumps `perms_v`; audited |
| POST | `/staff/{user_id}/deactivate` | staff | `staff.manage` + Step-up | — | Revokes all sessions immediately; history kept |
| POST | `/staff/{user_id}/pin/reset` | staff | `staff.manage` + Step-up | — | Forces the user to set a new PIN |
| GET | `/roles` | staff | `staff.read` | — | System roles + hotel custom roles with permissions |
| POST | `/roles` | staff | `roles.manage` + Step-up | Idem | Custom role from a subset of the caller's permissions |
| PATCH | `/roles/{id}` | staff | `roles.manage` + Step-up | — | System roles cannot be edited, only copied |
| GET | `/permissions` | staff | `staff.read` | — | Full permission catalogue with descriptions |

The permission catalogue and the role-to-permission matrix live in the Security and Compliance spec. Permission strings follow `domain.action`, for example `orders.read`, `folio.adjust.approve`, `checkout.override`.

## Guests, stays and check-in

A stay links one guest to one room for a date range and owns exactly one folio. Check-in posts the accommodation charges for every night up front, activates the room's tablet and sets the room to occupied, all in one transaction.

| Method | Path | Principal | Perm | Idem | Purpose |
| --- | --- | --- | --- | --- | --- |
| GET | `/guests?q=` | staff | `guests.read` | — | Search by name, email or phone; returns minimal fields |
| POST | `/guests` | staff | `guests.manage` | Idem | Name required; email, phone, ID number only if the hotel enables them |
| GET | `/guests/{id}` | staff | `guests.read` | — | Profile + stay history |
| PATCH | `/guests/{id}` | staff | `guests.manage` | — | Audited |
| GET | `/guests/{id}/export` | staff | `privacy.manage` + Step-up | — | POPIA access request: all data held about this guest, JSON |
| POST | `/guests/{id}/anonymise` | staff | `privacy.manage` + Step-up | Idem | Replaces personal fields; financial rows keep amounts |
| GET | `/billing-profiles?q=` | staff | `guests.read` | — | Saved company profiles |
| POST | `/billing-profiles` | staff | `billing.manage` | Idem | Company name, registration no., VAT no., address, email |
| GET | `/stays` | staff | `stays.read` | — | Filters: `status`, `room_id`, `from`, `to` |
| POST | `/stays` | staff | `stays.manage` | Idem | Create a reservation (`reserved`) |
| POST | `/stays/{id}/check-in` | staff | `stays.manage` | Idem | Moves to `active`; posts accommodation; activates tablet |
| POST | `/rooms/{id}/walk-in` | staff | `stays.manage` | Idem | Create and check in in one call |
| PATCH | `/stays/{id}` | staff | `stays.manage` | — | Extend or shorten; posts or reverses nights; audited |
| POST | `/stays/{id}/move` | staff | `stays.manage` + Step-up | Idem | Move to another room; tablet sessions follow; audited |
| POST | `/stays/{id}/cancel` | staff | `stays.manage` | Idem | Only from `reserved` |
| GET | `/stays/{id}` | staff | `stays.read` | — | Stay, guest, billing profile, folio summary |

**Walk-in request**

```json
{
  "guest": {"name": "John Smith", "email": "travel@abctech.example"},
  "nights": 3,
  "rate_override": null,
  "billing": {
    "type": "company",
    "billing_profile_id": "0192...",
    "purchase_order": "TRAVEL-10482",
    "traveller_name": "John Smith"
  }
}
```

A `rate_override` (corporate or negotiated rate) needs `stays.rate_override` and is recorded in the audit log with the original rate.

**Training stays and charge blocks:** `"training": true` on a walk-in marks a go-live test stay, excluded from reports while its folio is kept. `POST /stays/{id}/block-charges` and `POST /stays/{id}/unblock-charges` (Perm `stays.manage`) stop or allow tablet room charges for one stay; blocked attempts return `STAY_BLOCKED`.

## Menu, stations, schedules and images

The hotel owns its menu; every item points at one preparation station, and schedules decide when a category or item can be ordered in the hotel's time zone. Price changes affect new orders only, because orders store a snapshot.

| Method | Path | Principal | Perm | Idem | Purpose |
| --- | --- | --- | --- | --- | --- |
| GET / POST | `/kitchen-stations` | staff | `menu.read` / `kitchen.manage` | POST Idem | Main Kitchen, Bar, Dessert Station, Pool Bar |
| PATCH / DELETE | `/kitchen-stations/{id}` | staff | `kitchen.manage` | — | Delete only when no items point at it |
| GET / POST | `/menu/schedules` | staff | `menu.read` / `menu.manage` | POST Idem | Named windows, e.g. Breakfast 06:00–11:00, per weekday |
| GET / POST | `/menu/categories` | staff | `menu.read` / `menu.manage` | POST Idem | Name, sort order, schedule |
| PATCH / DELETE | `/menu/categories/{id}` | staff | `menu.manage` | — | Soft delete |
| GET | `/menu/items` | staff | `menu.read` | — | Filters: `category_id`, `station_id`, `available` |
| POST | `/menu/items` | staff | `menu.manage` | Idem | Name, description, price, VAT treatment, station, category, schedule, dietary tags, allergens |
| PATCH | `/menu/items/{id}` | staff | `menu.manage`; price needs `menu.price.update` | — | Price change audited with old and new value |
| POST | `/menu/items/{id}/availability` | staff | `menu.availability` | — | Sold out / back in stock; kitchen managers may use it |
| POST | `/menu/items/{id}/image` | staff | `menu.manage` | — | Signed upload URL (JPEG/WebP, max 5 MB); server makes 3 sizes |
| GET / POST | `/menu/modifier-groups` | staff | `menu.read` / `menu.manage` | POST Idem | e.g. "Cooking" (choose 1), "Extras" (choose 0–3) |
| POST | `/menu/modifier-groups/{id}/options` | staff | `menu.manage` | Idem | Option name and price delta (may be 0) |
| PUT | `/menu/items/{id}/modifier-groups` | staff | `menu.manage` | — | Attach groups to an item |

**Allergen list (fixed codes):** `gluten`, `crustaceans`, `egg`, `fish`, `peanuts`, `soy`, `dairy`, `tree_nuts`, `celery`, `mustard`, `sesame`, `sulphites`, `lupin`, `molluscs`. **Dietary tags:** `vegetarian`, `vegan`, `halaal`, `kosher`, `gluten_free`. Halaal and kosher may only be set by a user with `menu.certify` and should reflect the hotel's real certification.

## Guest tablet endpoints

Guest endpoints take only a device token; the server derives hotel, room and active stay from it, and every response is limited to that one stay. When no stay is active, these endpoints return the welcome state and no history.

| Method | Path | Principal | Idem | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/guest/session` | device (guest) | — | `{state, hotel, room, stay}`; `state` is `active`, `idle`, `locked` or `suspended` |
| GET | `/guest/menu` | device (guest) | — | Categories and items orderable now, with `available_now` and next window |
| POST | `/guest/orders/quote` | device (guest) | — | Server-priced quote for a cart: lines, fee, total, `needs_approval` |
| POST | `/guest/orders` | device (guest) | Idem | Place order, charge to room |
| GET | `/guest/orders` | device (guest) | — | Orders for the active stay only |
| GET | `/guest/orders/{id}` | device (guest) | — | One order with status timeline |
| GET | `/guest/folio` | device (guest) | — | Charges by category, payments, balance; tips listed separately |
| GET | `/guest/info` | device (guest) | — | Wi-Fi, check-out time, contacts, hotel information pages |

**Place order request**

```json
{
  "lines": [
    {"menu_item_id": "0192...a1", "quantity": 2, "modifier_option_ids": [], "note": null},
    {"menu_item_id": "0192...b7", "quantity": 2, "modifier_option_ids": ["0192...c3"], "note": "No ice"}
  ],
  "special_instructions": "No onions. Extra sauce.",
  "payment_method": "room_charge",
  "quoted_total": {"amount_minor": 36000, "currency": "ZAR"}
}
```

**Response `201`**

```json
{
  "id": "0192...",
  "number": 10482,
  "status": "NEW",
  "room": "259",
  "subtotal": {"amount_minor": 31000, "currency": "ZAR"},
  "fee": {"amount_minor": 5000, "currency": "ZAR"},
  "total": {"amount_minor": 36000, "currency": "ZAR"},
  "vat_included": {"amount_minor": 4696, "currency": "ZAR"},
  "created_at": "2026-10-08T16:21:00Z"
}
```

If `quoted_total` no longer matches the server's price (a price changed between quote and order), the server returns `409 PRICE_CHANGED` with the new quote, and the guest confirms again. Orders over the auto-approve limit return `status: "PENDING_APPROVAL"` and do not reach the kitchen until approved. Rejections: `NO_ACTIVE_STAY`, `ROOM_CHARGE_DISABLED`, `ITEM_UNAVAILABLE`, `STAY_BLOCKED`, `ORDER_TOO_LARGE` (over 50 lines or 99 per line).

## Orders, kitchen and deliveries

The kitchen moves orders and items through preparation; room service moves deliveries from claim to handover. Neither interface can change an amount: no endpoint in this group accepts a price, total or discount.

| Method | Path | Principal | Perm | Idem | Purpose |
| --- | --- | --- | --- | --- | --- |
| GET | `/orders` | staff | `orders.read` | — | Filters: `status`, `room_id`, `stay_id`, `from`, `to` |
| GET | `/orders/{id}` | staff | `orders.read` | — | Order, items, modifiers, status history, delivery, payments, adjustments |
| POST | `/orders/{id}/approve` | staff | `orders.approve` + Step-up | Idem | `PENDING_APPROVAL` → `NEW`; posts charges to the folio |
| POST | `/orders/{id}/decline` | staff | `orders.approve` | Idem | `{reason}`; guest sees the decline |
| POST | `/orders/{id}/cancel` | staff | `orders.cancel` + Step-up | Idem | Only before `PREPARING`; posts a reversing folio entry |
| GET | `/kitchen/orders` | staff (kitchen session) | `kitchen.view` | — | Active orders, filtered to the device's station(s); no prices in the payload |
| POST | `/kitchen/orders/{id}/accept` | staff (kitchen session) | `kitchen.update` | Idem | `NEW` → `ACCEPTED`; amounts lock |
| POST | `/kitchen/orders/{id}/start` | staff (kitchen session) | `kitchen.update` | Idem | `ACCEPTED` → `PREPARING` for the caller's station items |
| POST | `/kitchen/order-items/{id}/ready` | staff (kitchen session) | `kitchen.update` | Idem | Item → `READY`; order becomes `READY` when every item is ready |
| POST | `/kitchen/order-items/{id}/unready` | staff (kitchen session) | `kitchen.update` | Idem | Undo within 2 minutes |
| GET | `/deliveries` | staff | `deliveries.view` | — | `?scope=ready` or `?scope=mine` |
| POST | `/deliveries/{order_id}/claim` | staff | `deliveries.update` | Idem | `READY` → `ASSIGNED` to caller; first claim wins, others get `409 ALREADY_CLAIMED` |
| POST | `/deliveries/{order_id}/release` | staff | `deliveries.update` | Idem | Give back before pick-up |
| POST | `/deliveries/{order_id}/assign` | staff | `deliveries.manage` | Idem | Manager assigns to a named staff member |
| POST | `/deliveries/{order_id}/picked-up` | staff | `deliveries.update` (assignee only) | Idem | `ASSIGNED` → `PICKED_UP` |
| POST | `/deliveries/{order_id}/delivered` | staff | `deliveries.update` (assignee only) | Idem | `PICKED_UP` → `DELIVERED` |
| POST | `/deliveries/{order_id}/leave-on-room` | staff | `deliveries.update` (assignee only) | Idem | `DELIVERED` → `CLOSED`; amount stays on folio |
| POST | `/orders` | staff | `orders.create` | Idem | Staff enter an order for a room (phone order, Wi-Fi outage fallback). Same pricing and approval rules as the tablet; the staff member is recorded as the placer |

Each transition writes one `order_status_history` row with actor, device and timestamp, then publishes its realtime event after commit. Calls that would skip a state or repeat one return `409 INVALID_TRANSITION` with the current status.

## Order lifecycle

```
Allowed order status transitions (amounts lock on ACCEPTED):
PENDING_APPROVAL -> NEW (approve) | DECLINED (decline)
NEW              -> ACCEPTED | CANCELLED
ACCEPTED         -> PREPARING | CANCELLED
PREPARING        -> READY (when every item is ready)
READY            -> ASSIGNED (claim / assign)
ASSIGNED         -> READY (release) | PICKED_UP
PICKED_UP        -> DELIVERED
DELIVERED        -> CLOSED (paid, or left on room bill)
Orders within the auto-approve limit start at NEW.
```

Orders over the auto-approve limit wait in Pending approval and never reach the kitchen unless a manager approves them. Cancellation is possible only before preparation starts, and posts a reversing folio entry.

## Folios, payments, checkout and invoices

The folio is append-only: charges, payments and corrections are new entries, and the balance is always computed from them. Tips are recorded with payments but never count toward the bill or hotel revenue.

| Method | Path | Principal | Perm | Idem | Purpose |
| --- | --- | --- | --- | --- | --- |
| GET | `/folios/{stay_id}` | staff | `folio.read` | — | Entries, totals by category, payments, tips, balance |
| POST | `/folios/{stay_id}/charges` | staff | `folio.charge` | Idem | Other services: `{charge_category_id, description, amount, quantity}` |
| POST | `/folios/{stay_id}/discounts` | staff | `folio.discount` + Step-up | Idem | Percent or fixed; reason required; audited |
| POST | `/adjustments` | staff | `folio.adjust.request` | Idem | `{folio_entry_id or order_id, new_amount, reason}` → `pending` |
| POST | `/adjustments/{id}/approve` | staff | `folio.adjust.approve` + Step-up | Idem | Requester cannot approve their own adjustment; posts a correcting entry |
| POST | `/adjustments/{id}/reject` | staff | `folio.adjust.approve` | Idem | Reason required |
| POST | `/payments/preview` | staff | `payments.record` | — | `{order_id or stay_id, amount_received}` → due, received, difference, tip, shortfall |
| POST | `/payments` | staff | `payments.record` | Idem | Record a payment; see rules below |
| GET | `/payments` | staff | `payments.read` | — | Filters: `method`, `from`, `to`, `staff_id` |
| GET | `/stays/{id}/checkout-summary` | staff | `checkout.perform` | — | Categories, tips, total, payments, balance, open orders |
| POST | `/stays/{id}/checkout` | staff | `checkout.perform` + Step-up | Idem | Closes stay, issues bill, resets tablet |
| GET | `/invoices/{id}` | staff | `invoices.read` | — | Invoice JSON |
| GET | `/invoices/{id}/pdf` | staff | `invoices.read` | — | Short-lived signed URL to the PDF |
| POST | `/invoices/{id}/email` | staff | `invoices.send` | Idem | `{to: [...]}`; logged in notifications |
| POST | `/invoices/{id}/credit-note` | staff | `invoices.credit` + Step-up | Idem | Issued invoices are never edited; corrections use a credit note |

**Record payment request**

```json
{
  "order_id": "0192...",
  "method": "card_terminal",
  "amount_received": {"amount_minor": 400000, "currency": "ZAR"},
  "confirm_tip": true,
  "terminal_reference": "4F82C1"
}
```

**Payment rules**

1. The server computes `amount_due` from the order or folio; the client never sends it.
2. `tip = max(0, amount_received − amount_due)`. If the tip is above zero and `confirm_tip` is not `true`, the server returns `409 TIP_CONFIRMATION_REQUIRED` with the computed figures.
3. If `amount_received` is less than `amount_due`, the payment is `partial` and the remainder stays on the folio.
4. Methods: `room_charge` (no money moves), `card_terminal`, `cash`, `eft`. `card_terminal` requires `terminal_reference` (4–20 letters or digits). Card number, CVV, PIN and track data are rejected if sent.
5. One order can have at most one payment. A second attempt with a new key returns `409 ALREADY_PAID`.

**Late entries:** a payment or staff-entered order recorded after the fact (for example after a Wi-Fi outage) sends `occurred_at` (at most 72 hours earlier) and a `late_reason`. Both appear as flags on the daily close report.

**Checkout request:** `{"override": false, "override_reason": null, "bill_delivery": ["pdf", "email"], "email_to": ["accounts@abctech.example"]}`. Checkout is refused with `OPEN_ORDERS` while any order is unfinished, and with `OUTSTANDING_BALANCE` while the balance is above zero, unless `override` is true, the hotel allows overrides, a reason is given and the caller holds `checkout.override`.

## Reports, integrations and platform admin

Hotel reports are computed from folio entries and order history, so every report figure reconciles to the folio to the cent. Platform admin endpoints are a separate router, need a `platform` token with MFA, and return aggregates rather than guest records.

**Hotel reports** (all take `from`, `to` as hotel-local dates; Perm `reports.read`, finance figures need `reports.finance`)

| Path | Returns |
| --- | --- |
| `/reports/revenue` | Per business day: accommodation, F&B, other services, discounts, adjustments; tips shown separately |
| `/reports/payments` | By method and staff: count, amount, tips |
| `/reports/orders` | Count, average order value, cancelled and declined, by hour of day |
| `/reports/items` | Top items by quantity and revenue |
| `/reports/kitchen` | Median and 90th-percentile time accept → ready, by station |
| `/reports/room-service` | Median time ready → delivered, by staff member |
| `/reports/occupancy` | Occupied, available and out-of-service room-nights |
| `/audit-logs` | Filters: `actor_id`, `action`, `entity_type`, `from`, `to`; Perm `audit.read` |
| `/reports/daily-close?date=` | Daily close: revenue, payments by method and staff, tips, card total vs terminal batch total, adjustments, discounts, overrides, late entries, anomaly flags; needs reports.finance |
| `PUT /reports/daily-close/{date}` | Finance enters the terminal batch total and cash count, then marks the day reviewed; audited; needs reports.finance |

**Subscription, API keys and webhooks**

| Method | Path | Perm | Purpose |
| --- | --- | --- | --- |
| GET | `/subscription` | `subscription.read` | Plan, status, renewal date, usage against limits |
| POST | `/subscription/change-request` | `subscription.manage` | Request a plan change; platform applies it |
| GET / POST | `/api-keys` | `integrations.manage` + Step-up for POST | `{name, environment: sandbox \| production, scopes}`; secret returned once |
| DELETE | `/api-keys/{id}` | `integrations.manage` | Revoke immediately |
| GET / POST | `/webhooks` | `integrations.manage` | `{url (https only), events}`; signing secret returned once |
| POST | `/webhooks/{id}/test` | `integrations.manage` | Sends a `ping` event |
| GET | `/webhooks/{id}/deliveries` | `integrations.manage` | Last 100 attempts with status code |

**Webhook delivery:** JSON body `{id, type, created_at, hotel_id, data}`; header `Diyneco-Signature: t=<unix>,v1=<hex HMAC-SHA256 of "t.body">`. Receivers must reject signatures older than 5 minutes. Retries back off over 24 hours (1 m, 5 m, 30 m, 2 h, 6 h, 12 h), then the endpoint is disabled and the hotel is emailed. Webhook payloads never contain guest contact details.

**Platform admin** (`/admin/...`, platform token, MFA required)

| Method | Path | Perm | Purpose |
| --- | --- | --- | --- |
| GET | `/admin/metrics` | `platform.metrics` | Hotels, active hotels, rooms, connected devices, active stays, orders today and this month, MRR, churn |
| GET | `/admin/hotels` | `platform.tenants.read` | Name, status, plan, counts, created, last activity |
| POST | `/admin/hotels/{id}/approve` | `platform.tenants.manage` | `pending_approval` → `active` |
| POST | `/admin/hotels/{id}/suspend` | `platform.tenants.manage` + Step-up | Reason required; tablets show "service unavailable" |
| POST | `/admin/hotels/{id}/reactivate` | `platform.tenants.manage` |  |
| PUT | `/admin/hotels/{id}/subscription` | `platform.billing.manage` | Change plan, dates, limits |
| GET / POST | `/admin/plans` | `platform.billing.manage` | Plan catalogue; prices are data, never code |
| GET / PATCH | `/admin/feature-flags` | `platform.flags.manage` | Global and per-hotel flags |
| POST | `/admin/hotels/{id}/support-access` | `platform.support` + Step-up | Time-boxed (max 60 min) read access with a ticket reference; audited and visible to the hotel |
| GET | `/admin/health` | `platform.metrics` | API, database, realtime, queue, email provider status |

## Realtime WebSocket protocol

One socket per client at `wss://api.diyneco.com/api/v1/ws`. Events are notifications, not data: a client that receives one refetches the resource over REST if it needs the full record, so a lost or reordered event can never corrupt state.

**Handshake**

1. Client connects and sends `{"op": "auth", "token": "<access or device token>"}` within 5 seconds, or the server closes with `4401`.
2. Server replies `{"op": "ready", "channels": [...]}` listing the channels this principal may join.
3. Client sends `{"op": "subscribe", "channels": ["hotel:{id}:kitchen:{station}"], "since_seq": 18342}`. The server replays every event after `since_seq` from the last 24 hours, then streams live.

**Event envelope**

```json
{
  "op": "event",
  "seq": 18343,
  "event_id": "0192...",
  "type": "ORDER_READY",
  "channel": "hotel:0191...:room-service",
  "occurred_at": "2026-10-08T16:34:12Z",
  "data": {"order_id": "0192...", "order_number": 10482, "room": "259"}
}
```

`seq` increases per hotel. Clients store the last `seq` they processed and ignore any event whose `seq` they have already seen.

**Channels and who may join**

| Channel | Principal | Events |
| --- | --- | --- |
| `hotel:{id}:room:{room_id}` | that room's guest device only | `ORDER_ACCEPTED`, `ORDER_PREPARING`, `ORDER_READY`, `ORDER_DELIVERING`, `ORDER_DELIVERED`, `ORDER_DECLINED`, `PAYMENT_UPDATED`, `FOLIO_UPDATED`, `STAY_CHECKED_IN`, `RESET_ROOM_SESSION`, `DEVICE_LOCKED`, `DEVICE_UNLOCKED`, `MENU_UPDATED` |
| `hotel:{id}:kitchen:{station_id}` | kitchen device or `kitchen.view` | `NEW_ORDER`, `ORDER_CANCELLED`, `MENU_UPDATED` |
| `hotel:{id}:room-service` | `deliveries.view` | `ORDER_READY`, `DELIVERY_ASSIGNED`, `DELIVERY_RELEASED`, `ORDER_CANCELLED` |
| `hotel:{id}:ops` | `orders.read` | Every order, payment, stay, device and settings event, incl. `ORDER_PENDING_APPROVAL`, `STAY_CHECKED_OUT`, `DEVICE_OFFLINE` |
| `platform` | platform token | `TENANT_CREATED`, `TENANT_SUSPENDED`, `HEALTH_DEGRADED` |

**Keepalive and recovery:** the server pings every 25 s; two missed pongs close the socket. Clients reconnect with exponential back-off (1 s, 2 s, 4 s, up to 30 s, with jitter) and resubscribe with their last `seq`. While disconnected, clients poll their main list endpoint every 10 s and show an offline banner after 15 s.

**Close codes:** `4401` not authenticated, `4403` channel not allowed, `4409` device rebound or revoked (go to pairing screen), `4410` hotel suspended, `4429` too many connections (max 5 per principal).

## Error code catalogue

Clients switch on `code`, never on `message`. Codes are stable within v1; new ones may be added.

| HTTP | Code | When |
| --- | --- | --- |
| 400 | `VALIDATION_FAILED` | Body or query fails schema; `details.fields` lists each problem |
| 400 | `AMOUNT_INVALID` | Money not a positive integer, or currency mismatch |
| 400 | `CARD_DATA_REJECTED` | A field looks like a card number, CVV or PIN |
| 401 | `UNAUTHENTICATED` | Missing, expired or invalid token |
| 401 | `MFA_REQUIRED` | Platform or MFA-enrolled user without a verified second factor |
| 401 | `DEVICE_UNAUTHORISED` | Device credential invalid, revoked or rebound |
| 403 | `PERMISSION_DENIED` | Principal lacks the permission |
| 403 | `STEP_UP_REQUIRED` | Step-up token missing or expired |
| 403 | `PIN_INVALID` | Wrong PIN; `details.attempts_left` |
| 403 | `DEVICE_DISABLED` | Device locked or disabled |
| 403 | `HOTEL_SUSPENDED` | Write attempted while the tenant is suspended by Diyneco; reads stay available so the hotel can export its data |
| 403 | `SELF_APPROVAL` | Requester tried to approve their own adjustment |
| 404 | `NOT_FOUND` | Missing, deleted, or belongs to another hotel |
| 409 | `INVALID_TRANSITION` | State change not allowed from the current status |
| 409 | `IDEMPOTENCY_CONFLICT` | Key reused with a different body |
| 409 | `IDEMPOTENCY_IN_PROGRESS` | Same key still being processed |
| 409 | `ALREADY_CLAIMED` | Delivery taken by someone else |
| 409 | `ALREADY_PAID` | Order already has a payment |
| 409 | `PRICE_CHANGED` | Quoted total differs from current price; `details.quote` |
| 409 | `TIP_CONFIRMATION_REQUIRED` | Overpayment needs explicit tip confirmation |
| 409 | `OPEN_ORDERS` | Checkout while orders are unfinished |
| 409 | `OUTSTANDING_BALANCE` | Checkout with a balance and no valid override |
| 409 | `ROOM_NOT_AVAILABLE` | Check-in to a room that is not available |
| 409 | `ROOM_OCCUPIED` | Room status change or delete while a stay is active |
| 412 | `PRECONDITION_FAILED` | `If-Match` ETag is stale |
| 422 | `NO_ACTIVE_STAY` | Guest action with no active stay |
| 422 | `ROOM_CHARGE_DISABLED` | Hotel has room charging off |
| 422 | `STAY_BLOCKED` | Reception blocked charges on this stay |
| 422 | `ITEM_UNAVAILABLE` | Sold out or outside its schedule |
| 422 | `ORDER_TOO_LARGE` | Over 50 lines or 99 of one item |
| 422 | `OVERRIDE_NOT_ALLOWED` | Hotel policy forbids checkout override |
| 422 | `REASON_REQUIRED` | Override, adjustment, discount or decline without a reason |
| 422 | `PAIRING_INVALID` | Pairing code wrong, used or expired |
| 422 | `PLAN_LIMIT_REACHED` | Rooms, devices or staff over the plan limit |
| 429 | `RATE_LIMITED` | Too many requests; see `Retry-After` |
| 500 | `INTERNAL_ERROR` | Unexpected failure; logged with `request_id` |
| 503 | `SERVICE_UNAVAILABLE` | Maintenance or dependency outage; safe to retry with the same idempotency key |
