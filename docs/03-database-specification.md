# Diyneco — Database Specification

Oct 8, 2026 · @Profy D Keakile

One PostgreSQL 15+ database on Supabase holds every hotel's data, separated by `hotel_id` and enforced by both the API and row-level security. This spec is the reference for the Alembic migrations; the SQL here is the target schema, written as plain PostgreSQL.

## Conventions

Every table follows the same rules so that tenancy, money and history work the same way everywhere.

| Topic | Rule |
| --- | --- |
| Schema | All application tables live in schema `app`. Supabase's `auth` schema is not used. |
| Names | `snake_case`, plural table names, singular column names. Foreign keys are `<table_singular>_id`. |
| Primary keys | `id uuid PRIMARY KEY DEFAULT app.uuid_v7()`. Time-ordered, so inserts stay index-friendly. |
| Tenancy | Every hotel-owned table has `hotel_id uuid NOT NULL REFERENCES app.hotels(id)`. Child tables carry `hotel_id` too, even when the parent has it, so RLS never needs a join. Composite foreign keys `(hotel_id, parent_id)` stop a row pointing at another hotel's parent. |
| Money | `<name>_minor bigint NOT NULL` + `currency char(3) NOT NULL DEFAULT 'ZAR'`. Never `numeric` for stored amounts, never floats. Rates in basis points (`vat_rate_bp integer`, 1500 = 15%). |
| Time | `timestamptz` everywhere, stored in UTC. Hotel-local business dates are `date` columns computed with the hotel's time zone at write time. |
| Standard columns | `created_at timestamptz NOT NULL DEFAULT now()`, `updated_at timestamptz NOT NULL DEFAULT now()` (trigger-maintained), `created_by uuid` where an actor matters. |
| Soft delete | Configuration tables (rooms, menu items, staff membership) use `deleted_at timestamptz`. Financial tables never delete: no `deleted_at`, no `DELETE` grant. |
| Enumerations | `text` columns with `CHECK (col IN (...))`. Easier to extend in a migration than Postgres enum types. |
| Foreign key actions | `ON DELETE RESTRICT` by default. `CASCADE` only for pure child rows of configuration (e.g. a modifier option under its group), never for anything financial. |
| Optimistic locking | Mutable configuration rows have `version integer NOT NULL DEFAULT 1`, incremented on update; the API exposes it as the ETag. |
| Personal data | Columns holding guest personal data are listed in `app.pii_columns` so exports, anonymisation and retention jobs find them without guesswork. |

## Domain map

```
Platform & tenancy (hotels, hotel_settings, plans, subscriptions, feature_flags) - every table below carries hotel_id
  Property & devices  -> one live stay per room ->  Guests & stays (folios, charge_categories)
  Identity & access                                 Menu -> copied (snapshot) into each order
  Guests & stays -> one folio per stay -> Ledger & money (append-only: folio_entries, adjustments,
                                          discounts, payments, payment_allocations, tips, invoices)
  Orders -> post charges to the stay's folio (ledger)
Eventing, idempotency & audit used by every domain (event_outbox, event_seq, idempotency_keys,
  audit_logs, api_keys, webhooks, notifications)
```

A stay places orders; each order posts its charges to that stay's folio, and the folio is the only place balances come from. The menu feeds orders by copying, not by reference, so history never moves.

## Platform and tenancy

A hotel is the tenant; its settings, plan and subscription sit beside it, and plan prices and limits are data rather than code.

```sql
CREATE TABLE app.plans (
  id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  code              text NOT NULL UNIQUE,                -- starter, professional, enterprise
  name              text NOT NULL,
  monthly_price_minor bigint NOT NULL CHECK (monthly_price_minor >= 0),
  currency          char(3) NOT NULL DEFAULT 'ZAR',
  limits            jsonb NOT NULL DEFAULT '{}',         -- {"rooms": 50, "devices": 60, "staff": 40, "api_keys": 2}
  features          jsonb NOT NULL DEFAULT '{}',
  is_active         boolean NOT NULL DEFAULT true,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.hotels (
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  name          text NOT NULL,
  legal_name    text,
  slug          text NOT NULL UNIQUE,
  status        text NOT NULL DEFAULT 'pending_approval'
                CHECK (status IN ('pending_approval','active','suspended','closed')),
  status_reason text,
  address       jsonb NOT NULL DEFAULT '{}',             -- line1, line2, city, province, postal_code, country
  phone         text,
  email         text,
  logo_path     text,                                    -- storage object key, private bucket
  country       char(2) NOT NULL DEFAULT 'ZA',
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  version       integer NOT NULL DEFAULT 1
);

CREATE TABLE app.hotel_settings (
  hotel_id                       uuid PRIMARY KEY REFERENCES app.hotels(id),
  timezone                       text NOT NULL DEFAULT 'Africa/Johannesburg',
  currency                       char(3) NOT NULL DEFAULT 'ZAR',
  vat_registered                 boolean NOT NULL DEFAULT false,
  vat_number                     text,
  vat_rate_bp                    integer NOT NULL DEFAULT 1500 CHECK (vat_rate_bp BETWEEN 0 AND 10000),
  accommodation_rates_include_vat boolean NOT NULL DEFAULT false,
  menu_prices_include_vat        boolean NOT NULL DEFAULT true,
  room_charging_enabled          boolean NOT NULL DEFAULT true,
  room_charge_auto_limit_minor   bigint NOT NULL DEFAULT 50000 CHECK (room_charge_auto_limit_minor >= 0),
  room_service_fee_minor         bigint NOT NULL DEFAULT 0 CHECK (room_service_fee_minor >= 0),
  checkout_override_allowed      boolean NOT NULL DEFAULT false,
  room_status_after_checkout     text NOT NULL DEFAULT 'cleaning' CHECK (room_status_after_checkout IN ('cleaning','available')),
  checkout_time                  time NOT NULL DEFAULT '10:00',
  wifi_name                      text,
  invoice_prefix                 text NOT NULL,
  abridged_invoice_max_minor     bigint NOT NULL DEFAULT 500000 CHECK (abridged_invoice_max_minor >= 0),
  guest_id_number_enabled        boolean NOT NULL DEFAULT false,
  guest_data_retention_days      integer NOT NULL DEFAULT 1825 CHECK (guest_data_retention_days >= 365),
  updated_at                     timestamptz NOT NULL DEFAULT now(),
  version                        integer NOT NULL DEFAULT 1,
  CHECK (NOT vat_registered OR vat_number IS NOT NULL)
);

CREATE TABLE app.subscriptions (
  id                 uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id           uuid NOT NULL REFERENCES app.hotels(id),
  plan_id            uuid NOT NULL REFERENCES app.plans(id),
  status             text NOT NULL CHECK (status IN ('trialing','active','past_due','cancelled')),
  starts_on          date NOT NULL,
  renews_on          date,
  cancelled_at       timestamptz,
  limit_overrides    jsonb NOT NULL DEFAULT '{}',
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX subscriptions_one_current ON app.subscriptions(hotel_id)
  WHERE status IN ('trialing','active','past_due');

CREATE TABLE app.feature_flags (
  key        text NOT NULL,
  hotel_id   uuid REFERENCES app.hotels(id),            -- NULL = global default
  enabled    boolean NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  updated_by uuid,
  UNIQUE NULLS NOT DISTINCT (key, hotel_id)
);
```

## Identity and access

Users are global; membership in a hotel and the roles held there are per hotel. Permissions are fixed codes shipped with the product, and roles are bundles of them, either system roles or a hotel's own custom roles.

```sql
CREATE TABLE app.users (
  id               uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  email            citext NOT NULL UNIQUE,
  name             text NOT NULL,
  password_hash    text,                                  -- Argon2id PHC string; NULL until invitation accepted
  email_verified_at timestamptz,
  is_platform      boolean NOT NULL DEFAULT false,        -- Diyneco staff
  status           text NOT NULL DEFAULT 'active' CHECK (status IN ('invited','active','locked','deactivated')),
  failed_logins    integer NOT NULL DEFAULT 0,
  locked_until     timestamptz,
  last_login_at    timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.mfa_factors (
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  user_id       uuid NOT NULL REFERENCES app.users(id),
  kind          text NOT NULL CHECK (kind IN ('totp')),
  secret_enc    bytea NOT NULL,                           -- envelope-encrypted, see Security spec
  confirmed_at  timestamptz,
  last_used_step bigint,                                  -- blocks TOTP code replay
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.sessions (
  id              uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  user_id         uuid NOT NULL REFERENCES app.users(id),
  family_id       uuid NOT NULL,                          -- all refresh tokens of one login
  refresh_hash    bytea NOT NULL UNIQUE,                  -- SHA-256 of the current refresh token
  device_id       uuid,                                   -- set for kitchen-display staff sessions
  user_agent      text,
  ip              inet,
  amr             text[] NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now(),
  last_used_at    timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz NOT NULL,
  revoked_at      timestamptz,
  revoked_reason  text
);
CREATE INDEX sessions_user_active ON app.sessions(user_id) WHERE revoked_at IS NULL;

CREATE TABLE app.permissions (
  code        text PRIMARY KEY,                           -- e.g. folio.adjust.approve
  scope       text NOT NULL CHECK (scope IN ('hotel','platform')),
  description text NOT NULL,
  sensitive   boolean NOT NULL DEFAULT false              -- requires step-up
);

CREATE TABLE app.roles (
  id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id    uuid REFERENCES app.hotels(id),             -- NULL = system role
  code        text NOT NULL,                              -- general_manager, receptionist, ...
  name        text NOT NULL,
  is_system   boolean NOT NULL DEFAULT false,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE NULLS NOT DISTINCT (hotel_id, code),
  CHECK (is_system = (hotel_id IS NULL))
);

CREATE TABLE app.role_permissions (
  role_id          uuid NOT NULL REFERENCES app.roles(id) ON DELETE CASCADE,
  permission_code  text NOT NULL REFERENCES app.permissions(code),
  PRIMARY KEY (role_id, permission_code)
);

CREATE TABLE app.hotel_users (
  id             uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id       uuid NOT NULL REFERENCES app.hotels(id),
  user_id        uuid NOT NULL REFERENCES app.users(id),
  department     text,
  pin_hash       text,                                    -- Argon2id; NULL until set
  pin_failed     integer NOT NULL DEFAULT 0,
  pin_locked_until timestamptz,
  perms_version  integer NOT NULL DEFAULT 1,
  status         text NOT NULL DEFAULT 'active' CHECK (status IN ('active','deactivated')),
  created_at     timestamptz NOT NULL DEFAULT now(),
  deactivated_at timestamptz,
  UNIQUE (hotel_id, user_id),
  UNIQUE (hotel_id, id)
);

CREATE TABLE app.user_roles (
  hotel_id      uuid NOT NULL,
  hotel_user_id uuid NOT NULL,
  role_id       uuid NOT NULL REFERENCES app.roles(id),
  granted_by    uuid REFERENCES app.users(id),
  granted_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (hotel_user_id, role_id),
  FOREIGN KEY (hotel_id, hotel_user_id) REFERENCES app.hotel_users(hotel_id, id)
);

CREATE TABLE app.platform_user_roles (
  user_id   uuid NOT NULL REFERENCES app.users(id),
  role_id   uuid NOT NULL REFERENCES app.roles(id),
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE app.invitations (
  id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id    uuid NOT NULL REFERENCES app.hotels(id),
  email       citext NOT NULL,
  name        text NOT NULL,
  department  text,
  role_ids    uuid[] NOT NULL,
  token_hash  bytea NOT NULL UNIQUE,
  invited_by  uuid NOT NULL REFERENCES app.users(id),
  expires_at  timestamptz NOT NULL,
  accepted_at timestamptz,
  cancelled_at timestamptz,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.one_time_tokens (                      -- password reset, email verification
  token_hash  bytea PRIMARY KEY,
  user_id     uuid NOT NULL REFERENCES app.users(id),
  purpose     text NOT NULL CHECK (purpose IN ('password_reset','email_verify')),
  expires_at  timestamptz NOT NULL,
  used_at     timestamptz
);
```

## Property and devices

Rooms, room types and kitchen stations describe the property; devices are bound to exactly one room (guest tablets) or one or more stations (kitchen displays). The partial unique index on `devices` enforces one active guest tablet per room.

```sql
CREATE TABLE app.room_types (
  id               uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id         uuid NOT NULL REFERENCES app.hotels(id),
  name             text NOT NULL,
  base_rate_minor  bigint NOT NULL CHECK (base_rate_minor >= 0),
  currency         char(3) NOT NULL DEFAULT 'ZAR',
  capacity         smallint NOT NULL DEFAULT 2 CHECK (capacity BETWEEN 1 AND 20),
  amenities        text[] NOT NULL DEFAULT '{}',
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  deleted_at       timestamptz,
  version          integer NOT NULL DEFAULT 1,
  UNIQUE (hotel_id, id)
);
CREATE UNIQUE INDEX room_types_name ON app.room_types(hotel_id, lower(name)) WHERE deleted_at IS NULL;

CREATE TABLE app.rooms (
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
  room_type_id  uuid NOT NULL,
  number        text NOT NULL,                            -- '259', 'Garden Suite 3'
  floor         text,
  rate_minor    bigint CHECK (rate_minor >= 0),           -- NULL = use room type rate
  capacity      smallint,
  amenities     text[] NOT NULL DEFAULT '{}',
  status        text NOT NULL DEFAULT 'available'
                CHECK (status IN ('available','occupied','reserved','cleaning','maintenance','out_of_service')),
  status_changed_at timestamptz NOT NULL DEFAULT now(),
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  deleted_at    timestamptz,
  version       integer NOT NULL DEFAULT 1,
  UNIQUE (hotel_id, id),
  FOREIGN KEY (hotel_id, room_type_id) REFERENCES app.room_types(hotel_id, id)
);
CREATE UNIQUE INDEX rooms_number ON app.rooms(hotel_id, number) WHERE deleted_at IS NULL;
CREATE INDEX rooms_status ON app.rooms(hotel_id, status) WHERE deleted_at IS NULL;

CREATE TABLE app.kitchen_stations (
  id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id    uuid NOT NULL REFERENCES app.hotels(id),
  name        text NOT NULL,                              -- Main Kitchen, Bar, Dessert Station, Pool Bar
  sort_order  smallint NOT NULL DEFAULT 0,
  is_active   boolean NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (hotel_id, id),
  UNIQUE (hotel_id, name)
);

CREATE TABLE app.devices (
  id               uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id         uuid NOT NULL REFERENCES app.hotels(id),
  label            text NOT NULL,                         -- DY-259-01, KITCHEN-01
  kind             text NOT NULL CHECK (kind IN ('guest','kitchen')),
  room_id          uuid,
  credential_hash  bytea,                                 -- SHA-256 of a 256-bit random secret
  status           text NOT NULL DEFAULT 'active'
                   CHECK (status IN ('active','locked','disabled','reset_required','revoked')),
  os               text,
  app_version      text,
  last_seen_at     timestamptz,
  last_ip          inet,
  paired_at        timestamptz,
  revoked_at       timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (hotel_id, id),
  UNIQUE (hotel_id, label),
  FOREIGN KEY (hotel_id, room_id) REFERENCES app.rooms(hotel_id, id),
  CHECK (kind <> 'guest' OR room_id IS NOT NULL OR status = 'revoked'),
  CHECK (kind <> 'kitchen' OR room_id IS NULL)
);
CREATE UNIQUE INDEX devices_one_guest_per_room ON app.devices(room_id)
  WHERE kind = 'guest' AND status <> 'revoked';
CREATE INDEX devices_last_seen ON app.devices(hotel_id, last_seen_at);

CREATE TABLE app.device_stations (                       -- kitchen display → stations it shows
  hotel_id    uuid NOT NULL,
  device_id   uuid NOT NULL,
  station_id  uuid NOT NULL,
  PRIMARY KEY (device_id, station_id),
  FOREIGN KEY (hotel_id, device_id)  REFERENCES app.devices(hotel_id, id),
  FOREIGN KEY (hotel_id, station_id) REFERENCES app.kitchen_stations(hotel_id, id)
);

CREATE TABLE app.device_pairings (
  id           uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id     uuid NOT NULL REFERENCES app.hotels(id),
  kind         text NOT NULL CHECK (kind IN ('guest','kitchen')),
  room_id      uuid,
  station_ids  uuid[],
  code_hash    bytea NOT NULL,                            -- SHA-256 of the 6-digit code + pepper
  created_by   uuid NOT NULL REFERENCES app.users(id),
  expires_at   timestamptz NOT NULL,
  used_at      timestamptz,
  used_by_device uuid,
  attempts     smallint NOT NULL DEFAULT 0,
  created_at   timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (hotel_id, room_id) REFERENCES app.rooms(hotel_id, id)
);
CREATE UNIQUE INDEX device_pairings_live_code ON app.device_pairings(code_hash) WHERE used_at IS NULL;
```

A 6-digit code has only a million values, so pairing is protected by the 15-minute expiry, a lockout after 5 failed attempts from one device or IP, and per-IP rate limiting on `/devices/pair`, not by the hash alone.

## Guests, stays and folios

One stay has one folio, and the folio is a ledger: `folio_entries` is append-only, every row carries a category and a signed amount, and the balance is the sum. A partial unique index allows only one live stay per room.

```sql
CREATE TABLE app.guests (
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
  full_name     text NOT NULL,                            -- PII
  email         citext,                                   -- PII
  phone         text,                                     -- PII
  id_number_enc bytea,                                    -- PII, encrypted; only if hotel enables it
  nationality   char(2),
  anonymised_at timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (hotel_id, id)
);
CREATE INDEX guests_search ON app.guests USING gin (hotel_id, full_name gin_trgm_ops);

CREATE TABLE app.billing_profiles (                     -- companies
  id                  uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id            uuid NOT NULL REFERENCES app.hotels(id),
  company_name        text NOT NULL,
  registration_number text,
  vat_number          text,
  billing_address     jsonb NOT NULL DEFAULT '{}',
  billing_email       citext,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (hotel_id, id)
);

CREATE TABLE app.stays (
  id                 uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id           uuid NOT NULL REFERENCES app.hotels(id),
  room_id            uuid NOT NULL,
  guest_id           uuid NOT NULL,
  billing_type       text NOT NULL DEFAULT 'personal' CHECK (billing_type IN ('personal','company')),
  billing_profile_id uuid,
  purchase_order     text,
  traveller_name     text,
  status             text NOT NULL DEFAULT 'reserved'
                     CHECK (status IN ('reserved','checked_in','active','checkout_pending','checked_out','cancelled')),
  arrival_date       date NOT NULL,
  departure_date     date NOT NULL,
  nightly_rate_minor bigint NOT NULL CHECK (nightly_rate_minor >= 0),
  rate_override_reason text,
  currency           char(3) NOT NULL DEFAULT 'ZAR',
  charges_blocked    boolean NOT NULL DEFAULT false,
  is_training        boolean NOT NULL DEFAULT false,      -- go-live test stay; excluded from reports
  checked_in_at      timestamptz,
  checked_in_by      uuid,
  checked_out_at     timestamptz,
  checked_out_by     uuid,
  checkout_override_reason text,
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now(),
  version            integer NOT NULL DEFAULT 1,
  UNIQUE (hotel_id, id),
  FOREIGN KEY (hotel_id, room_id)  REFERENCES app.rooms(hotel_id, id),
  FOREIGN KEY (hotel_id, guest_id) REFERENCES app.guests(hotel_id, id),
  FOREIGN KEY (hotel_id, billing_profile_id) REFERENCES app.billing_profiles(hotel_id, id),
  CHECK (departure_date > arrival_date),
  CHECK (billing_type = 'personal' OR billing_profile_id IS NOT NULL)
);
CREATE UNIQUE INDEX stays_one_live_per_room ON app.stays(room_id)
  WHERE status IN ('checked_in','active','checkout_pending');
CREATE INDEX stays_dates ON app.stays(hotel_id, arrival_date, departure_date);

CREATE TABLE app.folios (
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
  stay_id       uuid NOT NULL,
  status        text NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
  currency      char(3) NOT NULL DEFAULT 'ZAR',
  closed_at     timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (hotel_id, id),
  UNIQUE (stay_id),
  FOREIGN KEY (hotel_id, stay_id) REFERENCES app.stays(hotel_id, id)
);

CREATE TABLE app.charge_categories (
  id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id    uuid REFERENCES app.hotels(id),             -- NULL = system category
  code        text NOT NULL,                              -- accommodation, accommodation_tax, food, beverage,
                                                          -- room_service_fee, laundry, spa, minibar, transport, ...
  name        text NOT NULL,
  revenue_group text NOT NULL CHECK (revenue_group IN ('accommodation','fnb','other','tip','payment')),
  vat_rate_bp integer,                                    -- NULL = hotel default
  is_revenue  boolean NOT NULL,                           -- false for tip and payment
  UNIQUE NULLS NOT DISTINCT (hotel_id, code)
);

CREATE TABLE app.folio_entries (
  id              uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id        uuid NOT NULL,
  folio_id        uuid NOT NULL,
  entry_type      text NOT NULL CHECK (entry_type IN ('charge','payment','tip','reversal','adjustment','discount')),
  category_id     uuid NOT NULL REFERENCES app.charge_categories(id),
  description     text NOT NULL,
  quantity        integer NOT NULL DEFAULT 1 CHECK (quantity > 0),
  unit_amount_minor bigint NOT NULL,
  amount_minor    bigint NOT NULL,                        -- signed: charges +, payments/discounts − on the balance
  vat_rate_bp     integer NOT NULL DEFAULT 0,
  vat_minor       bigint NOT NULL DEFAULT 0,              -- VAT contained in amount_minor
  currency        char(3) NOT NULL DEFAULT 'ZAR',
  business_date   date NOT NULL,                          -- hotel-local date
  order_id        uuid,
  payment_id      uuid,
  reverses_entry_id uuid REFERENCES app.folio_entries(id),
  adjustment_id   uuid,
  created_by      uuid,
  created_by_device uuid,
  created_at      timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (hotel_id, folio_id) REFERENCES app.folios(hotel_id, id),
  CHECK (amount_minor = unit_amount_minor * quantity),
  CHECK (entry_type <> 'reversal' OR reverses_entry_id IS NOT NULL)
);
CREATE INDEX folio_entries_folio ON app.folio_entries(folio_id, created_at);
CREATE INDEX folio_entries_reporting ON app.folio_entries(hotel_id, business_date, category_id);

CREATE TABLE app.adjustments (
  id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id          uuid NOT NULL REFERENCES app.hotels(id),
  folio_id          uuid NOT NULL,
  target_entry_id   uuid REFERENCES app.folio_entries(id),
  order_id          uuid,
  original_minor    bigint NOT NULL,
  new_minor         bigint NOT NULL CHECK (new_minor >= 0),
  reason            text NOT NULL CHECK (length(reason) >= 3),
  status            text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
  requested_by      uuid NOT NULL REFERENCES app.users(id),
  requested_at      timestamptz NOT NULL DEFAULT now(),
  decided_by        uuid REFERENCES app.users(id),
  decided_at        timestamptz,
  decision_note     text,
  FOREIGN KEY (hotel_id, folio_id) REFERENCES app.folios(hotel_id, id),
  CHECK (decided_by IS NULL OR decided_by <> requested_by)
);

CREATE TABLE app.discounts (
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
  folio_id      uuid NOT NULL,
  kind          text NOT NULL CHECK (kind IN ('percent','fixed')),
  percent_bp    integer CHECK (percent_bp BETWEEN 1 AND 10000),
  amount_minor  bigint CHECK (amount_minor > 0),
  applies_to    text NOT NULL CHECK (applies_to IN ('accommodation','fnb','other','all')),
  reason        text NOT NULL,
  created_by    uuid NOT NULL REFERENCES app.users(id),
  created_at    timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (hotel_id, folio_id) REFERENCES app.folios(hotel_id, id),
  CHECK ((kind = 'percent') = (percent_bp IS NOT NULL) AND (kind = 'fixed') = (amount_minor IS NOT NULL))
);

-- Read model used by the API, reports and checkout
CREATE VIEW app.folio_balances AS
SELECT f.id AS folio_id, f.hotel_id, f.stay_id,
  sum(e.amount_minor) FILTER (WHERE c.revenue_group = 'accommodation') AS accommodation_minor,
  sum(e.amount_minor) FILTER (WHERE c.revenue_group = 'fnb')           AS fnb_minor,
  sum(e.amount_minor) FILTER (WHERE c.revenue_group = 'other')         AS other_minor,
  sum(e.amount_minor) FILTER (WHERE c.revenue_group = 'tip')           AS tips_minor,
  -sum(e.amount_minor) FILTER (WHERE c.revenue_group = 'payment')      AS paid_minor,
  coalesce(sum(e.amount_minor) FILTER (WHERE c.revenue_group <> 'tip'), 0) AS balance_minor
FROM app.folios f
LEFT JOIN app.folio_entries e ON e.folio_id = f.id
LEFT JOIN app.charge_categories c ON c.id = e.category_id
GROUP BY f.id;
```

**Sign rules:** charges, accommodation tax and tips are positive; payments, discounts and reversals of charges are negative; tips are stored as their own entries so they show on the bill but are excluded from `balance_minor`. Example from the spec: accommodation 517500 + F&B 300000 + laundry 35000 − payments 852500 = balance 0, with tips 100000 shown separately.

## Menu

The menu is configuration: items can be edited or soft-deleted at any time because orders copy what they need at the moment of ordering. Schedules are evaluated in the hotel's time zone.

```sql
CREATE TABLE app.menu_schedules (
  id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id    uuid NOT NULL REFERENCES app.hotels(id),
  name        text NOT NULL,                              -- Breakfast, Lunch, Dinner, 24 hours
  windows     jsonb NOT NULL,                             -- [{"days":[1,2,3,4,5,6,7],"from":"06:00","to":"11:00"}]
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (hotel_id, id)
);

CREATE TABLE app.menu_categories (
  id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id    uuid NOT NULL REFERENCES app.hotels(id),
  name        text NOT NULL,
  sort_order  smallint NOT NULL DEFAULT 0,
  schedule_id uuid,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  deleted_at  timestamptz,
  UNIQUE (hotel_id, id),
  FOREIGN KEY (hotel_id, schedule_id) REFERENCES app.menu_schedules(hotel_id, id)
);

CREATE TABLE app.menu_items (
  id                 uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id           uuid NOT NULL REFERENCES app.hotels(id),
  category_id        uuid NOT NULL,
  station_id         uuid NOT NULL,                       -- preparation_station_id in the build spec
  charge_category_code text NOT NULL DEFAULT 'food' CHECK (charge_category_code IN ('food','beverage')),
  name               text NOT NULL,
  description        text,
  price_minor        bigint NOT NULL CHECK (price_minor >= 0),
  currency           char(3) NOT NULL DEFAULT 'ZAR',
  vat_rate_bp        integer,                             -- NULL = hotel default
  schedule_id        uuid,                                -- overrides the category schedule
  is_available       boolean NOT NULL DEFAULT true,       -- sold-out switch
  dietary_tags       text[] NOT NULL DEFAULT '{}',
  allergens          text[] NOT NULL DEFAULT '{}',
  image_path         text,
  sort_order         smallint NOT NULL DEFAULT 0,
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now(),
  deleted_at         timestamptz,
  version            integer NOT NULL DEFAULT 1,
  UNIQUE (hotel_id, id),
  FOREIGN KEY (hotel_id, category_id) REFERENCES app.menu_categories(hotel_id, id),
  FOREIGN KEY (hotel_id, station_id)  REFERENCES app.kitchen_stations(hotel_id, id),
  FOREIGN KEY (hotel_id, schedule_id) REFERENCES app.menu_schedules(hotel_id, id),
  CHECK (allergens <@ ARRAY['gluten','crustaceans','egg','fish','peanuts','soy','dairy','tree_nuts',
                           'celery','mustard','sesame','sulphites','lupin','molluscs']::text[]),
  CHECK (dietary_tags <@ ARRAY['vegetarian','vegan','halaal','kosher','gluten_free']::text[])
);
CREATE INDEX menu_items_category ON app.menu_items(hotel_id, category_id) WHERE deleted_at IS NULL;

CREATE TABLE app.menu_modifier_groups (
  id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id    uuid NOT NULL REFERENCES app.hotels(id),
  name        text NOT NULL,                              -- Cooking, Extras, Sides
  min_select  smallint NOT NULL DEFAULT 0,
  max_select  smallint NOT NULL DEFAULT 1,
  created_at  timestamptz NOT NULL DEFAULT now(),
  deleted_at  timestamptz,
  UNIQUE (hotel_id, id),
  CHECK (min_select >= 0 AND max_select >= min_select)
);

CREATE TABLE app.menu_modifiers (                         -- options inside a group
  id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id          uuid NOT NULL,
  group_id          uuid NOT NULL,
  name              text NOT NULL,                        -- Medium rare, Extra cheese
  price_delta_minor bigint NOT NULL DEFAULT 0 CHECK (price_delta_minor >= 0),
  is_available      boolean NOT NULL DEFAULT true,
  sort_order        smallint NOT NULL DEFAULT 0,
  deleted_at        timestamptz,
  UNIQUE (hotel_id, id),
  FOREIGN KEY (hotel_id, group_id) REFERENCES app.menu_modifier_groups(hotel_id, id) ON DELETE CASCADE
);

CREATE TABLE app.menu_item_modifiers (                    -- which groups an item offers
  hotel_id    uuid NOT NULL,
  item_id     uuid NOT NULL,
  group_id    uuid NOT NULL,
  sort_order  smallint NOT NULL DEFAULT 0,
  PRIMARY KEY (item_id, group_id),
  FOREIGN KEY (hotel_id, item_id)  REFERENCES app.menu_items(hotel_id, id),
  FOREIGN KEY (hotel_id, group_id) REFERENCES app.menu_modifier_groups(hotel_id, id)
);
```

## Orders and deliveries

An order snapshots names, prices, VAT and modifiers at the moment it is placed, so later menu changes never alter it. Item rows carry their own station and preparation status, which is how one order splits across the kitchen, bar and dessert station.

```sql
CREATE TABLE app.order_number_sequences (               -- gap-tolerant per-hotel counter
  hotel_id     uuid PRIMARY KEY REFERENCES app.hotels(id),
  next_number  bigint NOT NULL DEFAULT 10001
);

CREATE TABLE app.orders (
  id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id          uuid NOT NULL REFERENCES app.hotels(id),
  number            bigint NOT NULL,
  stay_id           uuid NOT NULL,
  room_id           uuid NOT NULL,
  room_number       text NOT NULL,                        -- snapshot
  device_id         uuid,                                 -- placing tablet
  placed_by_user    uuid,                                 -- if staff placed it for the guest
  late_reason       text,                                 -- staff order entered after the fact
  status            text NOT NULL CHECK (status IN ('PENDING_APPROVAL','NEW','ACCEPTED','PREPARING','READY',
                                       'ASSIGNED','PICKED_UP','DELIVERED','CLOSED','DECLINED','CANCELLED')),
  payment_method    text NOT NULL DEFAULT 'room_charge' CHECK (payment_method IN ('room_charge','card_terminal','cash')),
  special_instructions text CHECK (length(special_instructions) <= 500),
  subtotal_minor    bigint NOT NULL CHECK (subtotal_minor >= 0),
  fee_minor         bigint NOT NULL DEFAULT 0 CHECK (fee_minor >= 0),
  total_minor       bigint NOT NULL,
  vat_minor         bigint NOT NULL DEFAULT 0,
  currency          char(3) NOT NULL DEFAULT 'ZAR',
  needs_approval    boolean NOT NULL DEFAULT false,
  approved_by       uuid REFERENCES app.users(id),
  approved_at       timestamptz,
  decline_reason    text,
  posted_to_folio   boolean NOT NULL DEFAULT false,
  locked_at         timestamptz,                          -- set on ACCEPTED; amounts frozen from here
  accepted_at       timestamptz,
  ready_at          timestamptz,
  closed_at         timestamptz,
  idempotency_key   uuid NOT NULL,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (hotel_id, id),
  UNIQUE (hotel_id, number),
  UNIQUE (hotel_id, idempotency_key),
  FOREIGN KEY (hotel_id, stay_id) REFERENCES app.stays(hotel_id, id),
  FOREIGN KEY (hotel_id, room_id) REFERENCES app.rooms(hotel_id, id),
  CHECK (total_minor = subtotal_minor + fee_minor)
);
CREATE INDEX orders_active ON app.orders(hotel_id, status)
  WHERE status NOT IN ('CLOSED','DECLINED','CANCELLED');
CREATE INDEX orders_stay ON app.orders(stay_id, created_at);

CREATE TABLE app.order_items (
  id                 uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id           uuid NOT NULL,
  order_id           uuid NOT NULL,
  menu_item_id       uuid,                                -- reference only; may later be deleted
  station_id         uuid NOT NULL,
  name               text NOT NULL,                       -- snapshot
  description        text,                                -- snapshot
  charge_category_code text NOT NULL,                     -- food | beverage, snapshot
  unit_price_minor   bigint NOT NULL CHECK (unit_price_minor >= 0),   -- incl. modifier deltas
  quantity           integer NOT NULL CHECK (quantity BETWEEN 1 AND 99),
  line_total_minor   bigint NOT NULL,
  vat_rate_bp        integer NOT NULL,
  vat_minor          bigint NOT NULL,
  note               text CHECK (length(note) <= 200),
  prep_status        text NOT NULL DEFAULT 'PENDING' CHECK (prep_status IN ('PENDING','PREPARING','READY')),
  ready_at           timestamptz,
  ready_by           uuid,
  FOREIGN KEY (hotel_id, order_id)   REFERENCES app.orders(hotel_id, id),
  FOREIGN KEY (hotel_id, station_id) REFERENCES app.kitchen_stations(hotel_id, id),
  CHECK (line_total_minor = unit_price_minor * quantity)
);
CREATE INDEX order_items_station ON app.order_items(hotel_id, station_id, prep_status);

CREATE TABLE app.order_item_modifiers (
  id                 uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id           uuid NOT NULL,
  order_item_id      uuid NOT NULL REFERENCES app.order_items(id),
  modifier_id        uuid,
  group_name         text NOT NULL,                       -- snapshot
  name               text NOT NULL,                       -- snapshot
  price_delta_minor  bigint NOT NULL DEFAULT 0
);

CREATE TABLE app.order_status_history (
  id           bigint GENERATED ALWAYS AS IDENTITY,
  hotel_id     uuid NOT NULL,
  order_id     uuid NOT NULL,
  from_status  text,
  to_status    text NOT NULL,
  actor_user   uuid,
  actor_device uuid,
  note         text,
  created_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
CREATE INDEX order_status_history_order ON app.order_status_history(order_id, created_at);

CREATE TABLE app.deliveries (
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id      uuid NOT NULL,
  order_id      uuid NOT NULL UNIQUE,
  assigned_to   uuid REFERENCES app.users(id),
  assigned_by   uuid REFERENCES app.users(id),
  assigned_at   timestamptz,
  picked_up_at  timestamptz,
  delivered_at  timestamptz,
  released_count smallint NOT NULL DEFAULT 0,
  FOREIGN KEY (hotel_id, order_id) REFERENCES app.orders(hotel_id, id),
  CHECK (picked_up_at IS NULL OR assigned_at IS NOT NULL),
  CHECK (delivered_at IS NULL OR picked_up_at IS NOT NULL)
);
```

The allowed status transitions are enforced in the service layer and again by trigger `app.orders_guard_transition` (see Row-level security and triggers), which also rejects any change to `subtotal_minor`, `fee_minor` or `total_minor` once `locked_at` is set.

## Payments, tips and invoices

A payment records what the guest handed over; allocations say which folio it settled; a tip row records the excess the guest chose to give. Invoices are numbered without gaps per hotel and never change after issue.

```sql
CREATE TABLE app.payments (
  id                      uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id                uuid NOT NULL REFERENCES app.hotels(id),
  folio_id                uuid NOT NULL,
  order_id                uuid,                           -- set when paid at the door
  method                  text NOT NULL CHECK (method IN ('room_charge','card_terminal','cash','eft','gateway')),
  status                  text NOT NULL CHECK (status IN ('pending','paid','partial','failed','refunded')),
  amount_due_minor        bigint NOT NULL CHECK (amount_due_minor >= 0),
  amount_received_minor   bigint NOT NULL CHECK (amount_received_minor >= 0),
  tip_amount_minor        bigint NOT NULL DEFAULT 0 CHECK (tip_amount_minor >= 0),
  currency                char(3) NOT NULL DEFAULT 'ZAR',
  provider                text,                           -- NULL for manual terminal; 'yoco', 'peach' later
  provider_reference      text,                           -- terminal approval code
  external_transaction_id text,
  recorded_by             uuid REFERENCES app.users(id),
  recorded_by_device      uuid,
  occurred_at             timestamptz NOT NULL DEFAULT now(),   -- earlier than created_at for late entries
  late_reason             text,
  CHECK (occurred_at >= created_at - interval '72 hours'),
  CHECK (late_reason IS NOT NULL OR occurred_at >= created_at - interval '10 minutes'),
  idempotency_key         uuid NOT NULL,
  created_at              timestamptz NOT NULL DEFAULT now(),
  UNIQUE (hotel_id, idempotency_key),
  FOREIGN KEY (hotel_id, folio_id) REFERENCES app.folios(hotel_id, id),
  CHECK (tip_amount_minor = greatest(0, amount_received_minor - amount_due_minor)),
  CHECK (method <> 'card_terminal' OR provider_reference ~ '^[A-Za-z0-9-]{4,20}$')
);
CREATE UNIQUE INDEX payments_one_per_order ON app.payments(order_id)
  WHERE order_id IS NOT NULL AND status IN ('paid','partial');

CREATE TABLE app.payment_allocations (
  id             uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id       uuid NOT NULL,
  payment_id     uuid NOT NULL REFERENCES app.payments(id),
  folio_entry_id uuid NOT NULL REFERENCES app.folio_entries(id),   -- the payment entry it created
  amount_minor   bigint NOT NULL CHECK (amount_minor > 0),
  created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.tips (
  id             uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id       uuid NOT NULL,
  payment_id     uuid NOT NULL UNIQUE REFERENCES app.payments(id),
  folio_entry_id uuid NOT NULL REFERENCES app.folio_entries(id),
  amount_minor   bigint NOT NULL CHECK (amount_minor > 0),
  staff_user_id  uuid REFERENCES app.users(id),           -- who received it
  confirmed_by   uuid NOT NULL REFERENCES app.users(id),
  confirmed_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.invoice_sequences (                       -- gap-free: row locked FOR UPDATE inside checkout
  hotel_id     uuid NOT NULL REFERENCES app.hotels(id),
  year         smallint NOT NULL,
  next_number  integer NOT NULL DEFAULT 1,
  PRIMARY KEY (hotel_id, year)
);

CREATE TABLE app.invoices (
  id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id          uuid NOT NULL REFERENCES app.hotels(id),
  folio_id          uuid NOT NULL,
  number            text NOT NULL,                        -- GEH-2026-000123
  kind              text NOT NULL CHECK (kind IN ('tax_invoice','abridged_tax_invoice','guest_statement','credit_note')),
  credits_invoice_id uuid REFERENCES app.invoices(id),
  issued_at         timestamptz NOT NULL DEFAULT now(),
  supplier          jsonb NOT NULL,                       -- hotel name, address, VAT no. as at issue
  recipient         jsonb NOT NULL,                       -- guest or company, VAT no., PO, traveller as at issue
  totals            jsonb NOT NULL,                       -- by category, VAT, tips, payments, balance
  currency          char(3) NOT NULL DEFAULT 'ZAR',
  pdf_path          text,
  pdf_sha256        bytea,
  created_by        uuid REFERENCES app.users(id),
  UNIQUE (hotel_id, number),
  FOREIGN KEY (hotel_id, folio_id) REFERENCES app.folios(hotel_id, id),
  CHECK ((kind = 'credit_note') = (credits_invoice_id IS NOT NULL))
);

CREATE TABLE app.invoice_items (
  id             uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id       uuid NOT NULL,
  invoice_id     uuid NOT NULL REFERENCES app.invoices(id),
  folio_entry_id uuid REFERENCES app.folio_entries(id),
  line_no        smallint NOT NULL,
  category       text NOT NULL,
  description    text NOT NULL,
  quantity       integer NOT NULL,
  amount_minor   bigint NOT NULL,
  vat_rate_bp    integer NOT NULL,
  vat_minor      bigint NOT NULL,
  UNIQUE (invoice_id, line_no)
);
```

**Invoice kind** is chosen at checkout: `guest_statement` when the hotel is not VAT-registered; otherwise `tax_invoice` or `abridged_tax_invoice` by the thresholds configured from the Security and Compliance spec. Supplier and recipient details are copied into the invoice so later edits to the hotel or company profile cannot change an issued document.

**Daily close.** One row per hotel and business day holds what finance entered and when the day was reviewed; the figures it compares against are always recomputed from folio entries and payments.

```sql
CREATE TABLE app.daily_closes (
  hotel_id                     uuid NOT NULL REFERENCES app.hotels(id),
  business_date                date NOT NULL,
  terminal_batch_total_minor   bigint CHECK (terminal_batch_total_minor >= 0),
  cash_counted_minor           bigint CHECK (cash_counted_minor >= 0),
  card_recorded_minor          bigint,                  -- snapshot at review time
  cash_recorded_minor          bigint,                  -- snapshot at review time
  flags                        jsonb NOT NULL DEFAULT '[]',
  notes                        text,
  reviewed_by                  uuid REFERENCES app.users(id),
  reviewed_at                  timestamptz,
  PRIMARY KEY (hotel_id, business_date)
);
```

## Integrations, events, idempotency and audit

These tables let the platform keep promises across failures: the outbox guarantees an event leaves only after its transaction commits, the idempotency store makes retries safe, and the audit log is append-only.

```sql
CREATE TABLE app.api_keys (
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
  name          text NOT NULL,
  environment   text NOT NULL CHECK (environment IN ('sandbox','production')),
  prefix        text NOT NULL UNIQUE,                     -- first 8 chars, shown in the UI: dyk_live_3f9a…
  secret_hash   bytea NOT NULL,                           -- SHA-256 of the full key
  scopes        text[] NOT NULL,                          -- permission codes the key may use
  created_by    uuid NOT NULL REFERENCES app.users(id),
  created_at    timestamptz NOT NULL DEFAULT now(),
  last_used_at  timestamptz,
  usage_count   bigint NOT NULL DEFAULT 0,
  revoked_at    timestamptz
);

CREATE TABLE app.webhooks (
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id      uuid NOT NULL REFERENCES app.hotels(id),
  url           text NOT NULL CHECK (url LIKE 'https://%'),
  events        text[] NOT NULL,
  secret_enc    bytea NOT NULL,                           -- encrypted; needed to sign
  status        text NOT NULL DEFAULT 'active' CHECK (status IN ('active','disabled')),
  failure_count integer NOT NULL DEFAULT 0,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.webhook_deliveries (
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id      uuid NOT NULL,
  webhook_id    uuid NOT NULL REFERENCES app.webhooks(id),
  event_id      uuid NOT NULL,
  attempt       smallint NOT NULL,
  status_code   smallint,
  error         text,
  next_attempt_at timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.notifications (                          -- email log and in-app notifications
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id      uuid REFERENCES app.hotels(id),
  channel       text NOT NULL CHECK (channel IN ('in_app','email','push','sms','whatsapp')),
  template      text NOT NULL,                            -- guest_bill, staff_invite, password_reset, ...
  recipient     text NOT NULL,                            -- user id or email; PII
  subject_ref   jsonb NOT NULL DEFAULT '{}',              -- {"invoice_id": "..."}
  status        text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','sent','failed','read')),
  provider_message_id text,
  error         text,
  created_at    timestamptz NOT NULL DEFAULT now(),
  sent_at       timestamptz
);

CREATE TABLE app.event_seq (                              -- per-hotel realtime sequence
  hotel_id  uuid PRIMARY KEY REFERENCES app.hotels(id),
  last_seq  bigint NOT NULL DEFAULT 0
);

CREATE TABLE app.event_outbox (
  id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
  hotel_id      uuid REFERENCES app.hotels(id),
  seq           bigint,                                   -- assigned in the same transaction
  type          text NOT NULL,                            -- ORDER_READY, RESET_ROOM_SESSION, ...
  channels      text[] NOT NULL,
  payload       jsonb NOT NULL,                           -- ids and numbers only, no PII
  created_at    timestamptz NOT NULL DEFAULT now(),
  published_at  timestamptz,
  attempts      smallint NOT NULL DEFAULT 0
);
CREATE INDEX event_outbox_pending ON app.event_outbox(created_at) WHERE published_at IS NULL;
CREATE INDEX event_outbox_replay ON app.event_outbox(hotel_id, seq);

CREATE TABLE app.idempotency_keys (
  principal_key  text NOT NULL,                           -- 'user:<id>' | 'device:<id>' | 'apikey:<id>'
  key            uuid NOT NULL,
  method         text NOT NULL,
  path           text NOT NULL,
  request_hash   bytea NOT NULL,                          -- SHA-256 of canonical JSON body
  status         text NOT NULL CHECK (status IN ('in_progress','completed')),
  response_code  smallint,
  response_body  jsonb,
  created_at     timestamptz NOT NULL DEFAULT now(),
  expires_at     timestamptz NOT NULL DEFAULT now() + interval '24 hours',
  PRIMARY KEY (principal_key, key)
);

CREATE TABLE app.audit_logs (
  id            bigint GENERATED ALWAYS AS IDENTITY,
  hotel_id      uuid,                                     -- NULL for platform-level actions
  actor_type    text NOT NULL CHECK (actor_type IN ('user','device','api_key','system','platform')),
  actor_id      uuid,
  actor_label   text NOT NULL,                            -- 'Naledi K. (General Manager)' as at the time
  action        text NOT NULL,                            -- stay.check_out, folio.adjust, menu.price_change, ...
  entity_type   text NOT NULL,
  entity_id     uuid,
  old_value     jsonb,
  new_value     jsonb,
  reason        text,
  ip            inet,
  device_id     uuid,
  request_id    text,
  created_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
CREATE INDEX audit_logs_hotel ON app.audit_logs(hotel_id, created_at DESC);
CREATE INDEX audit_logs_entity ON app.audit_logs(entity_type, entity_id);

CREATE TABLE app.pii_columns (                            -- catalogue used by export, anonymise, retention
  table_name   text NOT NULL,
  column_name  text NOT NULL,
  category     text NOT NULL CHECK (category IN ('identity','contact','government_id','free_text')),
  anonymise_to text NOT NULL,                             -- 'null' | 'redacted' | 'hash'
  PRIMARY KEY (table_name, column_name)
);
```

## Row-level security, triggers and helpers

The API connects as role `diyneco_api`, which cannot bypass RLS. For every request it opens a transaction and runs `SET LOCAL app.hotel_id`, `app.actor_user` and `app.actor_device`, so a query that forgets its `hotel_id` filter still sees only the current hotel. Financial tables are append-only at the grant level and again by trigger.

**Roles and exposure**

| Role | Used by | Rights |
| --- | --- | --- |
| `diyneco_owner` | Alembic migrations only | Owns schema `app`; never used by the running API |
| `diyneco_api` | FastAPI request handlers | `SELECT, INSERT` on all tables; `UPDATE` only on mutable tables; no `DELETE` on financial tables; RLS forced |
| `diyneco_worker` | Outbox, email, PDF, retention jobs | Same as API plus `UPDATE` on `event_outbox`, `notifications`, `webhook_deliveries` |
| `diyneco_platform` | Admin endpoints | `EXECUTE` on aggregate functions only; no direct table access |
| `anon`, `authenticated` | Supabase defaults | `REVOKE ALL` on schema `app`; schema `app` is not exposed through Supabase's REST API |

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Time-ordered UUID (RFC 9562 version 7)
CREATE FUNCTION app.uuid_v7() RETURNS uuid LANGUAGE plpgsql VOLATILE AS $$
DECLARE
  ts bigint := floor(extract(epoch FROM clock_timestamp()) * 1000);
  b  bytea  := gen_random_bytes(16);
BEGIN
  b := set_byte(b, 0, ((ts >> 40) & 255)::int);
  b := set_byte(b, 1, ((ts >> 32) & 255)::int);
  b := set_byte(b, 2, ((ts >> 24) & 255)::int);
  b := set_byte(b, 3, ((ts >> 16) & 255)::int);
  b := set_byte(b, 4, ((ts >> 8)  & 255)::int);
  b := set_byte(b, 5, (ts & 255)::int);
  b := set_byte(b, 6, (get_byte(b, 6) & 15) | 112);   -- version 7
  b := set_byte(b, 8, (get_byte(b, 8) & 63) | 128);   -- RFC variant
  RETURN encode(b, 'hex')::uuid;
END $$;

CREATE FUNCTION app.current_hotel_id() RETURNS uuid LANGUAGE sql STABLE AS $$
  SELECT nullif(current_setting('app.hotel_id', true), '')::uuid
$$;

-- Tenant isolation on every table that has hotel_id
DO $$
DECLARE t text;
BEGIN
  FOR t IN
    SELECT c.table_name FROM information_schema.columns c
    JOIN information_schema.tables x ON x.table_schema = c.table_schema AND x.table_name = c.table_name
    WHERE c.table_schema = 'app' AND c.column_name = 'hotel_id' AND x.table_type = 'BASE TABLE'
      AND c.table_name NOT IN ('roles','charge_categories','feature_flags','audit_logs')
  LOOP
    EXECUTE format('ALTER TABLE app.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE app.%I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format($p$CREATE POLICY tenant_isolation ON app.%I
                     USING (hotel_id = app.current_hotel_id())
                     WITH CHECK (hotel_id = app.current_hotel_id())$p$, t);
  END LOOP;
END $$;

-- Shared catalogues: system rows (hotel_id NULL) readable by all, hotel rows only by that hotel
ALTER TABLE app.roles ENABLE ROW LEVEL SECURITY;
CREATE POLICY roles_visible ON app.roles
  USING (hotel_id IS NULL OR hotel_id = app.current_hotel_id())
  WITH CHECK (hotel_id = app.current_hotel_id());
ALTER TABLE app.charge_categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY categories_visible ON app.charge_categories
  USING (hotel_id IS NULL OR hotel_id = app.current_hotel_id())
  WITH CHECK (hotel_id = app.current_hotel_id());
ALTER TABLE app.audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY audit_hotel ON app.audit_logs
  USING (hotel_id = app.current_hotel_id())
  WITH CHECK (hotel_id IS NULL OR hotel_id = app.current_hotel_id());

-- Append-only enforcement
CREATE FUNCTION app.forbid_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'table % is append-only', TG_TABLE_NAME USING ERRCODE = 'P0001';
END $$;

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['folio_entries','payments','payment_allocations','tips',
                           'invoices','invoice_items','audit_logs','order_status_history']
  LOOP
    EXECUTE format('CREATE TRIGGER %I_append_only BEFORE UPDATE OR DELETE ON app.%I
                    FOR EACH ROW EXECUTE FUNCTION app.forbid_change()', t, t);
    EXECUTE format('REVOKE UPDATE, DELETE, TRUNCATE ON app.%I FROM diyneco_api, diyneco_worker', t);
  END LOOP;
END $$;

-- No entries on a closed folio
CREATE FUNCTION app.folio_must_be_open() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF (SELECT status FROM app.folios WHERE id = NEW.folio_id) <> 'open' THEN
    RAISE EXCEPTION 'folio % is closed', NEW.folio_id USING ERRCODE = 'P0002';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER folio_entries_open BEFORE INSERT ON app.folio_entries
  FOR EACH ROW EXECUTE FUNCTION app.folio_must_be_open();

-- Order state machine, amount lock and status history
CREATE FUNCTION app.order_transition_allowed(f text, t text) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT (f, t) IN (VALUES
    ('PENDING_APPROVAL','NEW'), ('PENDING_APPROVAL','DECLINED'),
    ('NEW','ACCEPTED'), ('NEW','CANCELLED'), ('ACCEPTED','PREPARING'), ('ACCEPTED','CANCELLED'),
    ('PREPARING','READY'), ('READY','ASSIGNED'), ('ASSIGNED','READY'),
    ('ASSIGNED','PICKED_UP'), ('PICKED_UP','DELIVERED'), ('DELIVERED','CLOSED'))
$$;

CREATE FUNCTION app.orders_guard_transition() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.locked_at IS NOT NULL AND
     (NEW.subtotal_minor, NEW.fee_minor, NEW.total_minor, NEW.vat_minor, NEW.stay_id, NEW.room_id)
     IS DISTINCT FROM
     (OLD.subtotal_minor, OLD.fee_minor, OLD.total_minor, OLD.vat_minor, OLD.stay_id, OLD.room_id) THEN
    RAISE EXCEPTION 'order % amounts are locked', OLD.number USING ERRCODE = 'P0003';
  END IF;
  IF NEW.status IS DISTINCT FROM OLD.status THEN
    IF NOT app.order_transition_allowed(OLD.status, NEW.status) THEN
      RAISE EXCEPTION 'order % cannot move % -> %', OLD.number, OLD.status, NEW.status USING ERRCODE = 'P0004';
    END IF;
    INSERT INTO app.order_status_history (hotel_id, order_id, from_status, to_status, actor_user, actor_device)
    VALUES (NEW.hotel_id, NEW.id, OLD.status, NEW.status,
            nullif(current_setting('app.actor_user', true), '')::uuid,
            nullif(current_setting('app.actor_device', true), '')::uuid);
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END $$;
CREATE TRIGGER orders_guard BEFORE UPDATE ON app.orders
  FOR EACH ROW EXECUTE FUNCTION app.orders_guard_transition();

-- Pairing runs before any hotel context exists, so it goes through one narrow definer function
CREATE FUNCTION app.redeem_pairing(p_code_hash bytea) RETURNS TABLE (pairing_id uuid, hotel_id uuid)
LANGUAGE sql SECURITY DEFINER SET search_path = app AS $$
  UPDATE app.device_pairings SET used_at = now()
  WHERE code_hash = p_code_hash AND used_at IS NULL AND expires_at > now()
  RETURNING id, hotel_id
$$;
REVOKE ALL ON FUNCTION app.redeem_pairing(bytea) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.redeem_pairing(bytea) TO diyneco_api;
```

The service maps SQLSTATE `P0001`–`P0004` to `INVALID_TRANSITION` or `INTERNAL_ERROR` and logs them as security events, because the API layer should have stopped those writes first.

## Indexing, partitioning, retention and performance

The hot paths are the kitchen board, the guest tablet and checkout; each is served by an index that starts with `hotel_id` or a stay or folio id, so query cost depends on one hotel's activity, not the whole platform's.

**Hot queries and the index that serves them**

| Query | Index | Target p95 |
| --- | --- | --- |
| Kitchen board: active items for a station | `order_items_station (hotel_id, station_id, prep_status)` + `orders_active` | 30 ms |
| Guest session: active stay for a room | `stays_one_live_per_room (room_id)` partial unique | 5 ms |
| Guest orders for a stay | `orders_stay (stay_id, created_at)` | 10 ms |
| Folio balance at checkout | `folio_entries_folio (folio_id, created_at)` | 20 ms |
| Daily revenue report | `folio_entries_reporting (hotel_id, business_date, category_id)` | 300 ms for one month |
| Device check on every tablet call | primary key + `credential_hash` lookup, cached 60 s in process | 2 ms |
| Outbox drain | `event_outbox_pending` partial | 10 ms |

**Partitioning:** `audit_logs` and `order_status_history` are range-partitioned by month on `created_at`. A scheduled job creates partitions 3 months ahead. Old partitions are detached and archived to encrypted object storage after the retention period, never dropped while still in it.

**Retention**

| Data | Kept | Then |
| --- | --- | --- |
| Folio entries, payments, tips, invoices | At least 5 years after the stay ends (tax records) | Archived; amounts kept, personal fields anonymised |
| Guest personal fields | `guest_data_retention_days` after last stay (default 1,825) | Anonymised per `pii_columns` |
| Audit logs | 7 years | Partition archived |
| Order status history | 2 years online | Partition archived |
| Idempotency keys | 24 hours | Deleted hourly |
| Event outbox | 7 days after publish | Deleted daily |
| Sessions, one-time tokens | 30 days after expiry | Deleted daily |
| Device heartbeats | Only `last_seen_at` is stored | — |

**Scale assumptions for v1 sizing:** 500 hotels, 25,000 rooms, 150,000 orders a month, 2 million folio entries a year. Single Postgres primary with one read replica for reports; no sharding needed at this size. Revisit when any hotel-scoped query on a hot path exceeds twice its target p95.

## Migrations and seed data

Every schema change is an Alembic migration reviewed like code, applied by CI to staging first, and written so the previous API version keeps working while it runs.

**Migration rules**

1. One migration per pull request, named `YYYYMMDD_HHMM_<short_description>`, with both `upgrade` and `downgrade`. A downgrade that would lose data raises instead of running.
2. Expand, then contract: add the new column or table, deploy code that writes both, backfill in batches of 5,000 rows, switch reads, and drop the old column in a later release.
3. No locking changes on hot tables in one step: create indexes `CONCURRENTLY`, add `NOT NULL` via a `CHECK ... NOT VALID` constraint then `VALIDATE`, and set `lock_timeout = '3s'` in every migration.
4. Never edit or reorder a migration that has reached staging.
5. Every migration that adds a table with `hotel_id` must also add its RLS policy; a CI check fails the build if any `app` table with `hotel_id` lacks one.
6. Financial tables get the append-only trigger in the same migration that creates them.
7. Permission codes and system roles are seeded by migration, so every environment has the same catalogue.

**Seed data**

| Environment | Seeded |
| --- | --- |
| All | Permission catalogue, system roles and their permissions, system charge categories, plans |
| Development | Two demo hotels (Grand Example Hotel, Seabreeze Lodge), rooms, menus, stations, demo staff with PIN 1234, one paired demo tablet per hotel |
| Staging | Development seed plus a load-test hotel with 500 rooms; refreshed weekly from scripts, never from production data |
| Production | Catalogue seeds only. Demo data is never loaded, and the demo PIN does not exist outside development |

Production data is never copied into lower environments. Bug reproduction uses synthetic data or an anonymised extract approved by the platform owner.
