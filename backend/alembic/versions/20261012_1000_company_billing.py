"""company billing: Diyneco's own identity as the seller, and effective-dated tax rates

DECISIONS D72 (subscription billing brief of 2026-10-12, section 2 and 7).
- company_settings (control plane, exactly one row): legal and trading name, registration
  number, addresses, billing contacts, logo, VAT registration (a registered company must have
  a VAT number and an effective date), invoice and credit note prefixes and numbering, payment
  terms, bank details and payment instructions. Seeded with the names and country only;
  registration, VAT and bank details stay empty until verified details are entered.
- tax_rates (control plane): one row per country, category and effective date. The rate in
  force on a day is the latest row on or before it, so a change is a new row and history is
  never rewritten. Rows are append-only, except that a rate not yet in force can be withdrawn.
  Seeded with South Africa's standard VAT rate (15% since 1 April 2018, VAT Act s7(1)(a)); it
  applies only while the company is VAT-registered.
- New platform permission platform.company.manage (Super Admin): edits both, with step-up.

Revision ID: 0025
Revises: 0024
Create Date: 2026-10-12 10:00
"""

from alembic import op

import alembic_helpers as h

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        r"""
        CREATE TABLE app.company_settings (
          id                   boolean PRIMARY KEY DEFAULT true CHECK (id),
          legal_name           text NOT NULL CHECK (length(legal_name) BETWEEN 2 AND 200),
          trading_name         text NOT NULL CHECK (length(trading_name) BETWEEN 1 AND 120),
          registration_number  text CHECK (length(registration_number) <= 40),
          country              char(2) NOT NULL,
          currency             char(3) NOT NULL,
          timezone             text NOT NULL,
          registered_address   jsonb NOT NULL DEFAULT '{}',
          business_address     jsonb NOT NULL DEFAULT '{}',
          billing_email        citext,
          billing_phone        text CHECK (length(billing_phone) <= 30),
          logo_path            text,
          vat_registered       boolean NOT NULL DEFAULT false,
          vat_number           text CHECK (length(vat_number) <= 30),
          vat_effective_date   date,
          invoice_prefix       text NOT NULL DEFAULT 'INV' CHECK (invoice_prefix ~ '^[A-Z0-9]{1,10}$'),
          credit_note_prefix   text NOT NULL DEFAULT 'CN' CHECK (credit_note_prefix ~ '^[A-Z0-9]{1,10}$'),
          number_padding       integer NOT NULL DEFAULT 6 CHECK (number_padding BETWEEN 4 AND 10),
          number_reset         text NOT NULL DEFAULT 'never' CHECK (number_reset IN ('never', 'yearly')),
          payment_terms_days   integer NOT NULL DEFAULT 7 CHECK (payment_terms_days BETWEEN 0 AND 90),
          bank_details         jsonb NOT NULL DEFAULT '{}',
          payment_instructions text CHECK (length(payment_instructions) <= 2000),
          version              integer NOT NULL DEFAULT 1,
          updated_at           timestamptz NOT NULL DEFAULT now(),
          updated_by           uuid REFERENCES app.users(id),
          CHECK (invoice_prefix <> credit_note_prefix),
          CHECK (NOT vat_registered OR (vat_number IS NOT NULL AND vat_effective_date IS NOT NULL))
        );
        INSERT INTO app.company_settings (legal_name, trading_name, country, currency, timezone)
          VALUES ('Diyneco Tech (Pty) Ltd', 'Diyneco', 'ZA', 'ZAR', 'Africa/Johannesburg');
        REVOKE INSERT, DELETE, TRUNCATE ON app.company_settings FROM diyneco_api, diyneco_worker;
        GRANT UPDATE ON app.company_settings TO diyneco_api;

        CREATE TABLE app.tax_rates (
          id              uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          country         char(2) NOT NULL,
          tax_name        text NOT NULL CHECK (length(tax_name) BETWEEN 2 AND 30),
          category        text NOT NULL CHECK (category IN ('standard', 'zero_rated', 'exempt')),
          rate_bp         integer NOT NULL CHECK (rate_bp BETWEEN 0 AND 10000),
          effective_from  date NOT NULL,
          reason          text NOT NULL CHECK (length(reason) BETWEEN 3 AND 500),
          created_by      uuid REFERENCES app.users(id),
          created_at      timestamptz NOT NULL DEFAULT now(),
          UNIQUE (country, category, effective_from),
          CHECK (category = 'standard' OR rate_bp = 0)
        );
        INSERT INTO app.tax_rates (country, tax_name, category, rate_bp, effective_from, reason) VALUES
          ('ZA', 'VAT', 'standard', 1500, '2018-04-01',
           'South African standard VAT rate, 15% from 1 April 2018 (VAT Act s7(1)(a)).');

        -- History is never rewritten: no updates, and only a rate not yet in force can be withdrawn.
        CREATE FUNCTION app.tax_rates_guard() RETURNS trigger
        LANGUAGE plpgsql SET search_path = app, extensions, pg_temp AS $$
        BEGIN
          IF TG_OP = 'UPDATE' THEN
            RAISE EXCEPTION 'tax rates are append-only' USING ERRCODE = 'insufficient_privilege';
          END IF;
          IF OLD.effective_from <= current_date THEN
            RAISE EXCEPTION 'a tax rate already in force cannot be removed' USING ERRCODE = 'insufficient_privilege';
          END IF;
          RETURN OLD;
        END $$;
        CREATE TRIGGER tax_rates_guard BEFORE UPDATE OR DELETE ON app.tax_rates
          FOR EACH ROW EXECUTE FUNCTION app.tax_rates_guard();
        GRANT DELETE ON app.tax_rates TO diyneco_api;
        REVOKE INSERT, DELETE ON app.tax_rates FROM diyneco_worker;

        INSERT INTO app.permissions (code, scope, description, sensitive)
          VALUES ('platform.company.manage', 'platform', 'Edit Diyneco''s company, VAT and tax settings', true);
        INSERT INTO app.role_permissions (role_id, permission_code)
          SELECT id, 'platform.company.manage' FROM app.roles WHERE hotel_id IS NULL AND code = 'platform_super_admin';
        """
    )
    h.updated_at("company_settings")


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM app.role_permissions WHERE permission_code = 'platform.company.manage';
        DELETE FROM app.permissions WHERE code = 'platform.company.manage';
        DROP TABLE IF EXISTS app.tax_rates;
        DROP FUNCTION IF EXISTS app.tax_rates_guard();
        DROP TABLE IF EXISTS app.company_settings;
        """
    )
