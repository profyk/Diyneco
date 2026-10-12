"""legal: versioned legal documents published by the platform, and who accepted which

DECISIONS D70, docs/ARCHITECTURE-GLOBAL.md section 4.
- legal_documents (control plane, no hotel): kind, optional country, version, title and text.
  Drafts can be edited; a published version is frozen (trigger) and is replaced only by
  publishing a newer one. A new platform permission, platform.legal.manage, publishes.
- legal_acceptances (per hotel, append-only, RLS): which person accepted which version, when
  and from where. Kept for the life of the account.

Revision ID: 0023
Revises: 0022
Create Date: 2026-10-11 15:00
"""

from alembic import op

import alembic_helpers as h

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE app.legal_documents (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          kind          text NOT NULL CHECK (kind IN ('terms', 'privacy', 'dpa', 'acceptable_use', 'guest_terms', 'guest_privacy')),
          country       char(2) CHECK (country ~ '^[A-Z]{2}$'),   -- NULL: applies everywhere
          version       integer NOT NULL CHECK (version > 0),
          title         text NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
          body          text NOT NULL CHECK (length(body) BETWEEN 1 AND 200000),
          summary       text CHECK (length(summary) <= 2000),     -- what changed, shown on acceptance
          status        text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
          effective_at  timestamptz,
          published_at  timestamptz,
          published_by  uuid REFERENCES app.users(id),
          created_by    uuid REFERENCES app.users(id),
          created_at    timestamptz NOT NULL DEFAULT now(),
          updated_at    timestamptz NOT NULL DEFAULT now(),
          UNIQUE NULLS NOT DISTINCT (kind, country, version),
          CHECK ((status = 'published') = (published_at IS NOT NULL))
        );
        CREATE INDEX legal_documents_current ON app.legal_documents (kind, country, version DESC)
          WHERE status = 'published';

        CREATE FUNCTION app.legal_documents_freeze() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            IF OLD.status = 'published' THEN
              RAISE EXCEPTION 'published legal documents cannot be deleted' USING ERRCODE = 'P0001';
            END IF;
            RETURN OLD;
          END IF;
          IF OLD.status = 'published' THEN
            RAISE EXCEPTION 'published legal documents are frozen; publish a new version' USING ERRCODE = 'P0001';
          END IF;
          NEW.updated_at := now();
          RETURN NEW;
        END $$;
        CREATE TRIGGER legal_documents_freeze BEFORE UPDATE OR DELETE ON app.legal_documents
          FOR EACH ROW EXECUTE FUNCTION app.legal_documents_freeze();
        GRANT UPDATE, DELETE ON app.legal_documents TO diyneco_api;

        CREATE TABLE app.legal_acceptances (
          id           uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id     uuid NOT NULL REFERENCES app.hotels(id),
          document_id  uuid NOT NULL REFERENCES app.legal_documents(id),
          user_id      uuid NOT NULL REFERENCES app.users(id),
          accepted_at  timestamptz NOT NULL DEFAULT now(),
          ip           inet,
          user_agent   text CHECK (length(user_agent) <= 500),
          UNIQUE (hotel_id, document_id, user_id)
        );
        CREATE INDEX legal_acceptances_user ON app.legal_acceptances (hotel_id, user_id);

        INSERT INTO app.permissions (code, scope, description, sensitive)
          VALUES ('platform.legal.manage', 'platform', 'Draft and publish legal documents', true);
        INSERT INTO app.role_permissions (role_id, permission_code)
          SELECT id, 'platform.legal.manage' FROM app.roles WHERE hotel_id IS NULL AND code = 'platform_super_admin';
        """
    )
    h.tenant_rls("legal_acceptances")
    h.append_only("legal_acceptances")


def downgrade() -> None:
    h.refuse_if_data("legal_acceptances")
    op.execute(
        """
        DELETE FROM app.role_permissions WHERE permission_code = 'platform.legal.manage';
        DELETE FROM app.permissions WHERE code = 'platform.legal.manage';
        DROP TABLE IF EXISTS app.legal_acceptances;
        DROP TABLE IF EXISTS app.legal_documents;
        DROP FUNCTION IF EXISTS app.legal_documents_freeze();
        """
    )
