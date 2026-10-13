-- Diyneco database bootstrap for a Supabase project (DECISIONS D81). The Supabase version of
-- infra/db/bootstrap.sql: Supabase has one database (`postgres`), no true superuser, and owns
-- the `extensions` and `public` schemas. Run once per project as the `postgres` role, by the
-- Migrate workflow (action "prepare") or by hand:
--
--   psql "postgresql://postgres.<project-ref>:<password>@<pooler host>:5432/postgres" \
--        -f infra/db/supabase-bootstrap.sql \
--        -v owner_password=... -v api_password=... -v worker_password=...
--
-- Safe to re-run: roles get their password and attributes reset; nothing is dropped.
--
-- diyneco_owner    owns schema app and runs migrations (BYPASSRLS for its narrow SECURITY
--                  DEFINER functions, DECISIONS G3). Never used by the running API.
-- diyneco_api      FastAPI request handlers. No BYPASSRLS.
-- diyneco_worker   Outbox, email and maintenance jobs. No BYPASSRLS.
-- diyneco_platform Platform admin functions' owner (G19). No login.

\set ON_ERROR_STOP on

SELECT format('CREATE ROLE %I', r) FROM unnest(ARRAY['diyneco_owner','diyneco_api','diyneco_worker','diyneco_platform']) AS r
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r)
\gexec

ALTER ROLE diyneco_owner    LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB BYPASSRLS   PASSWORD :'owner_password';
ALTER ROLE diyneco_api      LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS PASSWORD :'api_password';
ALTER ROLE diyneco_worker   LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS PASSWORD :'worker_password';
ALTER ROLE diyneco_platform NOLOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS;

ALTER ROLE diyneco_owner  SET search_path = app, extensions;
ALTER ROLE diyneco_api    SET search_path = app, extensions;
ALTER ROLE diyneco_worker SET search_path = app, extensions;

-- The owner creates schema app; the app roles only connect.
GRANT CONNECT, CREATE, TEMPORARY ON DATABASE postgres TO diyneco_owner;
GRANT CONNECT, TEMPORARY ON DATABASE postgres TO diyneco_api, diyneco_worker;

-- Supabase's extensions schema belongs to Supabase: create what the migrations use here, as
-- postgres, and let Diyneco's roles call the functions.
CREATE EXTENSION IF NOT EXISTS pgcrypto  WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS citext    WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS pg_trgm   WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS btree_gin WITH SCHEMA extensions;
GRANT USAGE ON SCHEMA extensions TO diyneco_owner, diyneco_api, diyneco_worker;

-- Alembic keeps its version table in public. Tables the owner creates there get none of
-- Supabase's default grants to anon/authenticated (those follow tables created by postgres).
GRANT USAGE, CREATE ON SCHEMA public TO diyneco_owner;
