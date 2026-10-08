"""platform and tenancy: plans, hotels, hotel_settings, subscriptions, feature_flags

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-08 17:01
"""

import alembic_helpers as h
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        CREATE TABLE app.plans (
          id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          code              text NOT NULL UNIQUE,                -- starter, professional, enterprise
          name              text NOT NULL,
          monthly_price_minor bigint NOT NULL CHECK (monthly_price_minor >= 0),
          currency          char(3) NOT NULL DEFAULT 'ZAR',
          limits            jsonb NOT NULL DEFAULT '{}',
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
          address       jsonb NOT NULL DEFAULT '{}',
          phone         text,
          email         text,
          logo_path     text,
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
        """
    )
    for t in ("plans", "hotels", "hotel_settings", "subscriptions", "feature_flags"):
        h.updated_at(t)

    # hotels has no hotel_id column; its own id is the tenant key (DECISIONS G2).
    h.tenant_rls("hotels", column="id")
    h.tenant_rls("hotel_settings")
    h.tenant_rls("subscriptions")
    # feature_flags: readable (global + own hotel), never written by the app roles (G7).
    op.execute("ALTER TABLE app.feature_flags ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE app.feature_flags FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY flags_visible ON app.feature_flags FOR SELECT "
        "USING (hotel_id IS NULL OR hotel_id = app.current_hotel_id())"
    )

    h.read_only("plans")
    h.read_only("feature_flags")
    h.mutable("hotels")
    h.mutable("hotel_settings")
    h.mutable("subscriptions")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("hotels")
    h.drop_tables("feature_flags", "subscriptions", "hotel_settings", "hotels", "plans")
