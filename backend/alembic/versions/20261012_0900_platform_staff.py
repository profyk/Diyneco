"""platform staff: Diyneco staff accounts managed from the admin panel

DECISIONS D71.
- A new platform permission, platform.staff.manage (Super Admin only), invites, changes the
  roles of, deactivates and reactivates platform accounts.
- one_time_tokens gains the purpose 'platform_invite': the link a new platform account uses
  to choose its password (two-step sign-in is then set up at the first sign-in, as before).
- platform_user_roles stays read-only for the app roles; roles change only through
  app.admin_set_platform_roles, which accepts platform roles only and only for platform
  accounts.
- The platform can never lose its last active Super Admin: a deferred constraint trigger on
  users (status) and platform_user_roles (delete) refuses the commit that would do it.

Revision ID: 0024
Revises: 0023
Create Date: 2026-10-12 09:00
"""

from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None

FUNCTIONS = ("app.admin_set_platform_roles(uuid, text[])",)


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE app.one_time_tokens DROP CONSTRAINT one_time_tokens_purpose_check;
        ALTER TABLE app.one_time_tokens ADD CONSTRAINT one_time_tokens_purpose_check
          CHECK (purpose IN ('password_reset', 'email_verify', 'platform_invite'));

        INSERT INTO app.permissions (code, scope, description, sensitive)
          VALUES ('platform.staff.manage', 'platform', 'Manage Diyneco staff accounts and their roles', true);
        INSERT INTO app.role_permissions (role_id, permission_code)
          SELECT id, 'platform.staff.manage' FROM app.roles WHERE hotel_id IS NULL AND code = 'platform_super_admin';

        CREATE FUNCTION app.platform_super_admins_left() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
        BEGIN
          -- Serialises every change that could remove a Super Admin, then counts what is left.
          PERFORM pg_advisory_xact_lock(hashtext('app.platform_super_admins'));
          IF NOT EXISTS (
            SELECT 1 FROM app.users u
            JOIN app.platform_user_roles pur ON pur.user_id = u.id
            JOIN app.roles r ON r.id = pur.role_id
            WHERE u.is_platform AND u.status = 'active'
              AND r.hotel_id IS NULL AND r.code = 'platform_super_admin'
          ) THEN
            RAISE EXCEPTION 'the platform must keep at least one active Super Admin'
              USING ERRCODE = 'check_violation';
          END IF;
          RETURN NULL;
        END $$;

        CREATE CONSTRAINT TRIGGER users_keep_super_admin
          AFTER UPDATE OF status ON app.users DEFERRABLE INITIALLY DEFERRED
          FOR EACH ROW WHEN (OLD.is_platform AND OLD.status = 'active' AND NEW.status <> 'active')
          EXECUTE FUNCTION app.platform_super_admins_left();
        CREATE CONSTRAINT TRIGGER platform_user_roles_keep_super_admin
          AFTER DELETE ON app.platform_user_roles DEFERRABLE INITIALLY DEFERRED
          FOR EACH ROW EXECUTE FUNCTION app.platform_super_admins_left();

        CREATE FUNCTION app.admin_set_platform_roles(p_user uuid, p_roles text[]) RETURNS void
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = app, extensions, pg_temp AS $$
        DECLARE
          wanted uuid[];
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM app.users WHERE id = p_user AND is_platform) THEN
            RAISE EXCEPTION 'not a platform account' USING ERRCODE = 'no_data_found';
          END IF;
          SELECT coalesce(array_agg(id), '{}') INTO wanted FROM app.roles
            WHERE hotel_id IS NULL AND code LIKE 'platform\\_%' AND code = ANY (p_roles);
          IF cardinality(wanted) <> (SELECT count(DISTINCT x) FROM unnest(p_roles) x) THEN
            RAISE EXCEPTION 'unknown platform role' USING ERRCODE = 'invalid_parameter_value';
          END IF;
          DELETE FROM app.platform_user_roles WHERE user_id = p_user AND NOT (role_id = ANY (wanted));
          INSERT INTO app.platform_user_roles (user_id, role_id)
            SELECT p_user, unnest(wanted) ON CONFLICT DO NOTHING;
        END $$;
        """
    )
    for fn in FUNCTIONS:
        op.execute(f"REVOKE ALL ON FUNCTION {fn} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {fn} TO diyneco_api, diyneco_platform")
    op.execute("REVOKE ALL ON FUNCTION app.platform_super_admins_left() FROM PUBLIC")


def downgrade() -> None:
    op.execute(
        """
        DROP FUNCTION IF EXISTS app.admin_set_platform_roles(uuid, text[]);
        DROP TRIGGER IF EXISTS platform_user_roles_keep_super_admin ON app.platform_user_roles;
        DROP TRIGGER IF EXISTS users_keep_super_admin ON app.users;
        DROP FUNCTION IF EXISTS app.platform_super_admins_left();
        DELETE FROM app.role_permissions WHERE permission_code = 'platform.staff.manage';
        DELETE FROM app.permissions WHERE code = 'platform.staff.manage';
        DELETE FROM app.one_time_tokens WHERE purpose = 'platform_invite';
        ALTER TABLE app.one_time_tokens DROP CONSTRAINT one_time_tokens_purpose_check;
        ALTER TABLE app.one_time_tokens ADD CONSTRAINT one_time_tokens_purpose_check
          CHECK (purpose IN ('password_reset', 'email_verify'));
        """
    )
