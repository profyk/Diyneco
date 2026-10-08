"""identity and access: users, MFA, sessions, permissions, roles, memberships, invitations

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-08 17:02
"""

import alembic_helpers as h
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        CREATE TABLE app.users (
          id               uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          email            citext NOT NULL UNIQUE,
          name             text NOT NULL,
          password_hash    text,
          email_verified_at timestamptz,
          is_platform      boolean NOT NULL DEFAULT false,
          status           text NOT NULL DEFAULT 'active' CHECK (status IN ('invited','active','locked','deactivated')),
          failed_logins    integer NOT NULL DEFAULT 0,
          failed_window_start timestamptz,                      -- DECISIONS G10
          locked_until     timestamptz,
          last_login_at    timestamptz,
          created_at       timestamptz NOT NULL DEFAULT now(),
          updated_at       timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE app.mfa_factors (
          id            uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          user_id       uuid NOT NULL REFERENCES app.users(id),
          kind          text NOT NULL CHECK (kind IN ('totp')),
          secret_enc    bytea NOT NULL,
          confirmed_at  timestamptz,
          last_used_step bigint,
          created_at    timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX mfa_factors_user ON app.mfa_factors(user_id);

        -- DECISIONS G8: the 10 one-time recovery codes, hashed
        CREATE TABLE app.mfa_recovery_codes (
          id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          user_id     uuid NOT NULL REFERENCES app.users(id),
          code_hash   bytea NOT NULL UNIQUE,
          used_at     timestamptz,
          created_at  timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX mfa_recovery_codes_user ON app.mfa_recovery_codes(user_id) WHERE used_at IS NULL;

        -- DECISIONS G9: wrapped data-encryption keys ('platform' or a hotel id)
        CREATE TABLE app.data_keys (
          scope        text PRIMARY KEY,
          wrapped_key  bytea NOT NULL,
          kms_key_id   text NOT NULL,
          created_at   timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE app.sessions (
          id              uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          user_id         uuid NOT NULL REFERENCES app.users(id),
          family_id       uuid NOT NULL,
          active_hotel_id uuid REFERENCES app.hotels(id),         -- hotel this session is signed in to (G11);
                                                                  -- sessions are per user, not tenant rows
          refresh_hash    bytea NOT NULL UNIQUE,
          device_id       uuid,
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
        CREATE INDEX sessions_family ON app.sessions(family_id);

        CREATE TABLE app.permissions (
          code        text PRIMARY KEY,
          scope       text NOT NULL CHECK (scope IN ('hotel','platform')),
          description text NOT NULL,
          sensitive   boolean NOT NULL DEFAULT false
        );

        CREATE TABLE app.roles (
          id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id    uuid REFERENCES app.hotels(id),
          code        text NOT NULL,
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
          pin_hash       text,
          pin_failed     integer NOT NULL DEFAULT 0,
          pin_failed_window_start timestamptz,                  -- DECISIONS G10
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

        CREATE TABLE app.one_time_tokens (
          token_hash  bytea PRIMARY KEY,
          user_id     uuid NOT NULL REFERENCES app.users(id),
          purpose     text NOT NULL CHECK (purpose IN ('password_reset','email_verify')),
          expires_at  timestamptz NOT NULL,
          used_at     timestamptz
        );
        """
    )
    h.updated_at("users")
    h.updated_at("roles")

    h.shared_catalogue_rls("roles", "roles_visible")
    h.tenant_rls("hotel_users")
    h.tenant_rls("user_roles")
    h.tenant_rls("invitations")
    # role_permissions has no hotel_id: rows follow their role's visibility, and only the
    # current hotel's own (custom) roles can be changed (DECISIONS G6).
    op.execute("ALTER TABLE app.role_permissions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE app.role_permissions FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY role_permissions_visible ON app.role_permissions "
        "USING (EXISTS (SELECT 1 FROM app.roles r WHERE r.id = role_id)) "
        "WITH CHECK (EXISTS (SELECT 1 FROM app.roles r WHERE r.id = role_id "
        "AND r.hotel_id = app.current_hotel_id()))"
    )
    # A user role must be a system role or the same hotel's custom role (G6).
    h.shared_ref("user_roles", "role_id", "roles")

    h.read_only("permissions")
    h.read_only("platform_user_roles")
    h.read_only("data_keys", roles="diyneco_worker")
    for t in ("users", "mfa_factors", "mfa_recovery_codes", "sessions", "roles",
              "hotel_users", "invitations", "one_time_tokens"):
        h.mutable(t)
    # Replace-style endpoints (PUT /staff/{id}/roles, PATCH /roles/{id}) delete link rows.
    op.execute("GRANT DELETE ON app.role_permissions, app.user_roles TO diyneco_api")
    # Retention jobs (G14).
    op.execute("GRANT DELETE ON app.sessions, app.one_time_tokens TO diyneco_worker")

    # Login lists a user's hotels before any hotel is selected (DECISIONS G4).
    op.execute(
        """
        CREATE FUNCTION app.user_memberships(p_user_id uuid)
        RETURNS TABLE (hotel_id uuid, hotel_name text, hotel_status text, hotel_user_id uuid,
                       perms_version integer, role_codes text[])
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT h.id, h.name, h.status, hu.id, hu.perms_version,
                 coalesce(array_agg(r.code ORDER BY r.code) FILTER (WHERE r.id IS NOT NULL), '{}')
          FROM app.hotel_users hu
          JOIN app.hotels h ON h.id = hu.hotel_id
          LEFT JOIN app.user_roles ur ON ur.hotel_user_id = hu.id
          LEFT JOIN app.roles r ON r.id = ur.role_id
          WHERE hu.user_id = p_user_id AND hu.status = 'active' AND h.status <> 'closed'
          GROUP BY h.id, h.name, h.status, hu.id, hu.perms_version
          ORDER BY h.name
        $$;
        REVOKE ALL ON FUNCTION app.user_memberships(uuid) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.user_memberships(uuid) TO diyneco_api;

        -- Invitation acceptance arrives with only the emailed token, before any hotel is
        -- known. Returns the hotel so the API can set its tenant context (G4).
        CREATE FUNCTION app.invitation_lookup(p_token_hash bytea)
        RETURNS TABLE (invitation_id uuid, hotel_id uuid)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
          SELECT i.id, i.hotel_id FROM app.invitations i
          WHERE i.token_hash = p_token_hash AND i.accepted_at IS NULL AND i.cancelled_at IS NULL
            AND i.expires_at > now()
        $$;
        REVOKE ALL ON FUNCTION app.invitation_lookup(bytea) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.invitation_lookup(bytea) TO diyneco_api;
        """
    )


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("users")
    op.execute("DROP FUNCTION IF EXISTS app.invitation_lookup(bytea)")
    op.execute("DROP FUNCTION IF EXISTS app.user_memberships(uuid)")
    h.drop_tables(
        "one_time_tokens", "invitations", "platform_user_roles", "user_roles", "hotel_users",
        "role_permissions", "roles", "permissions", "sessions", "data_keys",
        "mfa_recovery_codes", "mfa_factors", "users",
    )
