"""website: the public marketing site at www.diyneco.com, managed in the admin panel

DECISIONS D83 (user request). Control-plane tables (no hotel, so no RLS), written only by
Diyneco staff with platform.website.manage and read publicly through /site endpoints.
- site_settings (one row): site name, languages (default and enabled), navigation, footer,
  contact details, social links, default SEO, search-engine verification, analytics choice
  and the address that receives leads.
- site_entries: pages and blog posts per language. Edits go to `draft`; publishing copies the
  draft to `published` and records a version. An entry and its translations share a
  translation_key, so search engines are told about every language version (hreflang).
- site_entry_versions (append-only): every published version, for history and rollback.
- site_media: images uploaded by staff, re-encoded on the server (metadata dropped) and
  served from the API at stable public addresses.
- site_redirects: old addresses sent to new ones (301 or 302).
- site_leads: demo and contact requests from the site, with the consent text shown. Only the
  follow-up status and notes change; a lead can be erased on request (POPIA).
- site_page_views (aggregates only): views and distinct visitors per day, path, language and
  referrer host. No cookies, no IP address and no visitor id are stored.
New permissions platform.website.manage and platform.leads.read; a Website editor role.

Revision ID: 0032
Revises: 0031
Create Date: 2026-10-14 12:00
"""

from alembic import op

import alembic_helpers as h

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None

TABLES = (
    "site_page_views",
    "site_leads",
    "site_redirects",
    "site_entry_versions",
    "site_entries",
    "site_media",
    "site_settings",
)

LOCALE = r"'^[a-z]{2}(-[A-Z]{2})?$'"
SLUG = r"'^([a-z0-9]+(-[a-z0-9]+)*)(/[a-z0-9]+(-[a-z0-9]+)*)*$'"
PATH = r"'^/[A-Za-z0-9/_.~%-]*$'"


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        f"""
        CREATE TABLE app.site_settings (
          id               smallint PRIMARY KEY DEFAULT 1 CHECK (id = 1),
          site_name        text NOT NULL DEFAULT 'Diyneco' CHECK (length(site_name) BETWEEN 1 AND 80),
          base_url         text NOT NULL DEFAULT 'https://www.diyneco.com' CHECK (base_url ~ '^https?://[^/]+$'),
          default_locale   text NOT NULL DEFAULT 'en' CHECK (default_locale ~ {LOCALE}),
          locales          text[] NOT NULL DEFAULT '{{en}}',
          navigation       jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(navigation) = 'array'),
          footer           jsonb NOT NULL DEFAULT '{{}}' CHECK (jsonb_typeof(footer) = 'object'),
          contact          jsonb NOT NULL DEFAULT '{{}}' CHECK (jsonb_typeof(contact) = 'object'),
          social           jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(social) = 'array'),
          seo              jsonb NOT NULL DEFAULT '{{}}' CHECK (jsonb_typeof(seo) = 'object'),
          verification     jsonb NOT NULL DEFAULT '{{}}' CHECK (jsonb_typeof(verification) = 'object'),
          analytics        jsonb NOT NULL DEFAULT '{{"provider": "builtin"}}' CHECK (jsonb_typeof(analytics) = 'object'),
          lead_email       text NOT NULL DEFAULT 'sales@diyneco.com' CHECK (lead_email ~ '^[^@\\s]+@[^@\\s]+$'),
          updated_at       timestamptz NOT NULL DEFAULT now(),
          updated_by       uuid REFERENCES app.users(id),
          CHECK (default_locale = ANY (locales))
        );
        INSERT INTO app.site_settings (id) VALUES (1);

        CREATE TABLE app.site_media (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          filename      text NOT NULL CHECK (length(filename) BETWEEN 1 AND 200),
          alt           text NOT NULL DEFAULT '' CHECK (length(alt) <= 300),
          width         integer NOT NULL CHECK (width > 0),
          height        integer NOT NULL CHECK (height > 0),
          widths        integer[] NOT NULL,                 -- stored WebP copies
          bytes         integer NOT NULL CHECK (bytes > 0),
          storage_key   text NOT NULL UNIQUE,              -- prefix; copies are <key>/<width>.webp
          uploaded_by   uuid REFERENCES app.users(id),
          created_at    timestamptz NOT NULL DEFAULT now(),
          deleted_at    timestamptz
        );

        CREATE TABLE app.site_entries (
          id               uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          kind             text NOT NULL CHECK (kind IN ('page', 'post')),
          locale           text NOT NULL CHECK (locale ~ {LOCALE}),
          slug             text NOT NULL CHECK (slug = '' OR slug ~ {SLUG}),  -- '' is the home page
          translation_key  uuid NOT NULL DEFAULT app.uuid_v7(),
          draft            jsonb NOT NULL CHECK (jsonb_typeof(draft) = 'object'),
          published        jsonb CHECK (published IS NULL OR jsonb_typeof(published) = 'object'),
          version          integer NOT NULL DEFAULT 0 CHECK (version >= 0),  -- last published version
          published_at     timestamptz,           -- first publication; posts are dated by it
          republished_at   timestamptz,           -- last publication (sitemap lastmod)
          created_by       uuid REFERENCES app.users(id),
          updated_by       uuid REFERENCES app.users(id),
          created_at       timestamptz NOT NULL DEFAULT now(),
          updated_at       timestamptz NOT NULL DEFAULT now(),
          deleted_at       timestamptz,
          CHECK (kind = 'page' OR slug <> ''),
          CHECK (published IS NULL OR version > 0)
        );
        CREATE UNIQUE INDEX site_entries_address ON app.site_entries (kind, locale, slug) WHERE deleted_at IS NULL;
        CREATE UNIQUE INDEX site_entries_translation ON app.site_entries (translation_key, locale)
          WHERE deleted_at IS NULL;
        CREATE INDEX site_entries_posts ON app.site_entries (locale, published_at DESC)
          WHERE kind = 'post' AND published IS NOT NULL AND deleted_at IS NULL;

        CREATE TABLE app.site_entry_versions (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          entry_id      uuid NOT NULL REFERENCES app.site_entries(id),
          version       integer NOT NULL CHECK (version > 0),
          content       jsonb NOT NULL,
          published_by  uuid REFERENCES app.users(id),
          published_at  timestamptz NOT NULL DEFAULT now(),
          UNIQUE (entry_id, version)
        );

        CREATE TABLE app.site_redirects (
          id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          from_path   text NOT NULL UNIQUE CHECK (from_path ~ {PATH} AND from_path <> '/'),
          to_path     text NOT NULL CHECK (to_path ~ {PATH} OR to_path ~ '^https://'),
          permanent   boolean NOT NULL DEFAULT true,
          created_by  uuid REFERENCES app.users(id),
          created_at  timestamptz NOT NULL DEFAULT now(),
          CHECK (from_path <> to_path)
        );

        CREATE TABLE app.site_leads (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          kind          text NOT NULL CHECK (kind IN ('demo', 'contact')),
          name          text NOT NULL CHECK (length(name) BETWEEN 1 AND 120),
          email         citext NOT NULL CHECK (length(email) <= 320),
          phone         text CHECK (length(phone) <= 40),
          company       text CHECK (length(company) <= 160),
          rooms         integer CHECK (rooms BETWEEN 1 AND 100000),
          country       char(2) CHECK (country ~ '^[A-Z]{{2}}$'),
          message       text CHECK (length(message) <= 4000),
          locale        text NOT NULL CHECK (locale ~ {LOCALE}),
          source_path   text CHECK (length(source_path) <= 300),
          consent_text  text NOT NULL CHECK (length(consent_text) BETWEEN 1 AND 1000),
          status        text NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'qualified', 'closed', 'spam')),
          notes         text CHECK (length(notes) <= 4000),
          handled_by    uuid REFERENCES app.users(id),
          created_at    timestamptz NOT NULL DEFAULT now(),
          updated_at    timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX site_leads_recent ON app.site_leads (created_at DESC);

        -- Only the follow-up columns of a lead change; what the person sent never does.
        CREATE FUNCTION app.site_leads_guard() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF (NEW.kind, NEW.name, NEW.email, NEW.phone, NEW.company, NEW.rooms, NEW.country, NEW.message,
              NEW.locale, NEW.source_path, NEW.consent_text, NEW.created_at)
             IS DISTINCT FROM
             (OLD.kind, OLD.name, OLD.email, OLD.phone, OLD.company, OLD.rooms, OLD.country, OLD.message,
              OLD.locale, OLD.source_path, OLD.consent_text, OLD.created_at) THEN
            RAISE EXCEPTION 'a lead''s submitted details never change' USING ERRCODE = 'P0001';
          END IF;
          NEW.updated_at := now();
          RETURN NEW;
        END $$;
        CREATE TRIGGER site_leads_guard BEFORE UPDATE ON app.site_leads
          FOR EACH ROW EXECUTE FUNCTION app.site_leads_guard();

        CREATE TABLE app.site_page_views (
          day           date NOT NULL,
          path          text NOT NULL CHECK (length(path) <= 300),
          locale        text NOT NULL CHECK (locale ~ {LOCALE}),
          referrer      text NOT NULL DEFAULT '' CHECK (length(referrer) <= 200),  -- host only
          views         integer NOT NULL DEFAULT 0 CHECK (views >= 0),
          visitors      integer NOT NULL DEFAULT 0 CHECK (visitors >= 0),
          PRIMARY KEY (day, path, locale, referrer)
        );

        INSERT INTO app.permissions (code, scope, description, sensitive) VALUES
          ('platform.website.manage', 'platform', 'Edit and publish the public website', false),
          ('platform.leads.read', 'platform', 'See and follow up demo and contact requests from the website', true);
        INSERT INTO app.roles (code, name, is_system) VALUES ('platform_website_editor', 'Website editor', true);
        INSERT INTO app.role_permissions (role_id, permission_code)
          SELECT r.id, p.code FROM app.roles r
          CROSS JOIN (VALUES ('platform.website.manage'), ('platform.leads.read')) AS p(code)
          WHERE r.hotel_id IS NULL AND r.code IN ('platform_super_admin', 'platform_website_editor');
        """
    )
    for t in ("site_settings", "site_entries", "site_redirects", "site_leads", "site_page_views", "site_media"):
        h.mutable(t)
    h.append_only("site_entry_versions")
    op.execute("GRANT DELETE ON app.site_redirects, app.site_leads TO diyneco_api")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("site_entries", "site_leads")
    op.execute(
        """
        DELETE FROM app.role_permissions WHERE permission_code IN ('platform.website.manage', 'platform.leads.read');
        DELETE FROM app.platform_user_roles WHERE role_id IN
          (SELECT id FROM app.roles WHERE hotel_id IS NULL AND code = 'platform_website_editor');
        DELETE FROM app.roles WHERE hotel_id IS NULL AND code = 'platform_website_editor';
        DELETE FROM app.permissions WHERE code IN ('platform.website.manage', 'platform.leads.read');
        """
    )
    h.drop_tables(*TABLES)
    op.execute("DROP FUNCTION IF EXISTS app.site_leads_guard()")
