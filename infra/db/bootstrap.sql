-- Diyneco database bootstrap. Run once per cluster as a superuser:
--
--   psql -h localhost -U postgres -d postgres -f infra/db/bootstrap.sql \
--        -v owner_password=... -v api_password=... -v worker_password=...
--
-- Safe to re-run: existing roles get their password and attributes reset,
-- existing databases are left alone.
--
-- diyneco_owner   owns schema app and runs migrations. BYPASSRLS so that the narrow
--                 SECURITY DEFINER functions it owns (redeem_pairing, user_memberships,
--                 outbox claim, ensure_partitions) can work before a hotel is known.
--                 Never used by the running API. (DECISIONS.md G3)
-- diyneco_api     FastAPI request handlers. Not superuser, no BYPASSRLS.
-- diyneco_worker  Outbox, email and maintenance jobs. Not superuser, no BYPASSRLS.
-- diyneco_platform Platform admin access; no grants until Phase 7. (G19)

\set ON_ERROR_STOP on

SELECT format('CREATE ROLE %I', r) FROM unnest(ARRAY['diyneco_owner','diyneco_api','diyneco_worker','diyneco_platform']) AS r
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r)
\gexec

ALTER ROLE diyneco_owner    LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB BYPASSRLS   PASSWORD :'owner_password';
ALTER ROLE diyneco_api      LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS PASSWORD :'api_password';
ALTER ROLE diyneco_worker   LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS PASSWORD :'worker_password';
ALTER ROLE diyneco_platform NOLOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS;

-- Every session of these roles resolves app tables and extension functions the same way.
ALTER ROLE diyneco_owner  SET search_path = app, extensions;
ALTER ROLE diyneco_api    SET search_path = app, extensions;
ALTER ROLE diyneco_worker SET search_path = app, extensions;

SELECT format('CREATE DATABASE %I OWNER diyneco_owner ENCODING ''UTF8'' TEMPLATE template0', d)
FROM unnest(ARRAY['diyneco','diyneco_test']) AS d
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = d)
\gexec

REVOKE ALL ON DATABASE diyneco FROM PUBLIC;
REVOKE ALL ON DATABASE diyneco_test FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE diyneco, diyneco_test TO diyneco_api, diyneco_worker;

\connect diyneco
REVOKE ALL ON SCHEMA public FROM PUBLIC;
\connect diyneco_test
REVOKE ALL ON SCHEMA public FROM PUBLIC;
