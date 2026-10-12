# Diyneco worldwide: data layering and scale

Status: adopted design (DECISIONS D69). What is built today is marked **Built**; the rest is the
agreed path, built when the first hotel outside a region signs up or when load requires it.

## 1. Layers

```
              ┌──────────────────────────── Global control plane ────────────────────────────┐
              │ Tenant directory (hotel id → region, status, plan)   Plans, prices, currencies │
              │ Platform staff, feature flags, legal documents       Billing of hotels         │
              └──────────────┬───────────────────────────────┬────────────────────────────────┘
                             │ routes by hotel id            │ publishes catalogues
        ┌────────────────────┴───────┐        ┌──────────────┴─────────────┐
        │ Regional cell: af-south    │  ...   │ Regional cell: eu-west     │   (us-east, me-central,
        │ API + worker + Postgres +  │        │ API + worker + Postgres +  │    ap-southeast)
        │ object storage + Redis     │        │ object storage + Redis     │
        │ ALL guest and hotel data   │        │ ALL guest and hotel data   │
        └────────────────────────────┘        └────────────────────────────┘
```

- **Cells hold personal and financial data and never share it.** A hotel's guests, stays, bills,
  orders, staff and audit log live only in the cell of the hotel's `data_region`, chosen from
  its country at signup and fixed afterwards (moving a hotel is an operator procedure: export,
  import, verify, switch the directory). This satisfies POPIA, GDPR, the UK GDPR and similar
  residency expectations without per-country databases.
- **The control plane holds no guest data**: tenant directory, plans, platform staff, flags,
  legal document versions and subscription billing. Cells sync the catalogues they need (plans,
  flags, legal versions) read-only.
- **Built:** one cell (`af-south`) plus the control-plane tables in the same database, separated
  by role grants and definer functions (D48). `hotels.data_region` is recorded for every hotel
  now so that splitting into cells later is a data move, not a redesign.

## 2. Tenancy inside a cell

- Every hotel-owned row has `hotel_id`; Postgres RLS on `app.hotel_id` plus repository filters
  (enforced twice, CLAUDE.md). **Built.**
- Identifiers are UUID v7 (time-ordered, globally unique), so rows can move between cells and
  be merged in analytics without collisions. **Built.**
- Large tables are partitioned by time where they grow without bound (audit log, event outbox,
  status history: **Built** for the outbox and audit) and, when a cell passes ~5,000 hotels,
  `orders`, `order_items` and `folio_entries` move to hash partitions on `hotel_id` (32 parts),
  keeping each hotel's rows together.
- Read replicas serve reports and the Admin panel's cross-hotel aggregates; writes stay on the
  primary. Connection pooling per cell (PgBouncer / Supabase pooler, transaction mode).

## 3. Country, money, tax and language

| Concern | Rule | Status |
|---|---|---|
| Country | `hotels.country` (ISO 3166-1) is required at signup; the country catalogue (`GET /countries`) supplies defaults | **Built** |
| Currency | One operating currency per hotel (ISO 4217, minor units), chosen at signup; never converted; plans carry their own billing currency; MRR reported per currency | **Built** (D57) |
| Time | All timestamps `timestamptz` in UTC; business dates and schedules in the hotel's IANA time zone; the platform reports in UTC | **Built** |
| Tax | Tax is VAT/GST/sales-tax style, inclusive or exclusive, per hotel: `tax_label` (VAT, GST, IVA...), rate in basis points, registration number validated by the country's pattern when one is known, otherwise by a general rule | **Built** (D69) |
| Invoices | Sequential, gap-free numbering per hotel and prefix; the simplified ("abridged") invoice threshold applies only where the hotel sets one (South Africa sets R5,000; elsewhere 0 means always a full invoice) | **Built** |
| Language | `hotel_settings.locale` (BCP 47, e.g. `en-ZA`, `fr-FR`) drives number, date and currency formatting on every screen (staff apps and tablets; set from `/auth/me` and the tablet session); interface text uses message catalogues per language, English first | Formatting **Built**; translations next |
| Phone | E.164 stored as entered (`+` and digits) | **Built** |
| Addresses | Free-form lines plus city, region, postal code and country code; no country-specific fields | **Built** |

Tax rates in the country catalogue are suggestions shown at signup; the hotel confirms its own
rate, because rates change and some countries tax by region or product.

## 4. Legal documents

Terms of service, privacy notice, data processing agreement and guest terms are versioned in the
control plane (`legal_documents`, D70). Publishing a version records who published it and when;
merchants must accept the current versions to keep using the Merchant app, guests see the guest
terms and privacy notice on the tablet, and every acceptance (who, which version, when, from
where) is kept for the life of the account. Documents can be published per country when local
law needs different text; otherwise the global version applies.

## 5. Security and keys at scale

- Envelope encryption: one data key per hotel, wrapped by the cell's KMS key (**Built**, D62
  for guest ID numbers); cells never share KMS keys.
- Backups are per cell, encrypted with separate keys, restored in-region; the restore drill runs
  on every CI build (**Built**, D53).
- Edge: TLS everywhere, HSTS and CSP on the web apps (**Built**), WAF and rate limits per IP and
  per hotel at the edge of each cell.

## 6. Scale targets and levers

| Load | Lever |
|---|---|
| 10,000 hotels, 1M rooms | 2–4 cells; each cell one primary (32 vCPU) + 2 replicas |
| Order spikes (breakfast) | stateless API autoscaling; outbox drained by N workers with `SKIP LOCKED` (**Built**) |
| Realtime | WebSocket gateway nodes behind the cell's load balancer, fan-out through Redis pub/sub |
| Images | resized once by the worker (**Built**, D64), served from the CDN with signed URLs |
| Reports | read replicas; daily rollups per hotel per business date |

## 7. What changes when a second cell opens

1. Stand up the cell from `infra/deployment` with its own database, storage, Redis and KMS key.
2. Move the control-plane tables to the control plane database; cells read plans, flags and legal
   versions through a small read-only sync.
3. The tenant directory routes sign-in and API calls: the access token carries the hotel's region
   and each cell refuses tokens for other regions.
4. Signup picks the cell from the country's region.
