"""menu: schedules, categories, items, modifier groups and options

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-08 17:05
"""

import alembic_helpers as h
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

TABLES = ("menu_schedules", "menu_categories", "menu_items", "menu_modifier_groups",
          "menu_modifiers", "menu_item_modifiers")


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    op.execute(
        """
        CREATE TABLE app.menu_schedules (
          id          uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id    uuid NOT NULL REFERENCES app.hotels(id),
          name        text NOT NULL,
          windows     jsonb NOT NULL,
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
          station_id         uuid NOT NULL,
          charge_category_code text NOT NULL DEFAULT 'food' CHECK (charge_category_code IN ('food','beverage')),
          name               text NOT NULL,
          description        text,
          price_minor        bigint NOT NULL CHECK (price_minor >= 0),
          currency           char(3) NOT NULL DEFAULT 'ZAR',
          vat_rate_bp        integer,
          schedule_id        uuid,
          is_available       boolean NOT NULL DEFAULT true,
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
          name        text NOT NULL,
          min_select  smallint NOT NULL DEFAULT 0,
          max_select  smallint NOT NULL DEFAULT 1,
          created_at  timestamptz NOT NULL DEFAULT now(),
          deleted_at  timestamptz,
          UNIQUE (hotel_id, id),
          CHECK (min_select >= 0 AND max_select >= min_select)
        );

        CREATE TABLE app.menu_modifiers (
          id                uuid PRIMARY KEY DEFAULT app.uuid_v7(),
          hotel_id          uuid NOT NULL,
          group_id          uuid NOT NULL,
          name              text NOT NULL,
          price_delta_minor bigint NOT NULL DEFAULT 0 CHECK (price_delta_minor >= 0),
          is_available      boolean NOT NULL DEFAULT true,
          sort_order        smallint NOT NULL DEFAULT 0,
          deleted_at        timestamptz,
          UNIQUE (hotel_id, id),
          FOREIGN KEY (hotel_id, group_id) REFERENCES app.menu_modifier_groups(hotel_id, id) ON DELETE CASCADE
        );

        CREATE TABLE app.menu_item_modifiers (
          hotel_id    uuid NOT NULL,
          item_id     uuid NOT NULL,
          group_id    uuid NOT NULL,
          sort_order  smallint NOT NULL DEFAULT 0,
          PRIMARY KEY (item_id, group_id),
          FOREIGN KEY (hotel_id, item_id)  REFERENCES app.menu_items(hotel_id, id),
          FOREIGN KEY (hotel_id, group_id) REFERENCES app.menu_modifier_groups(hotel_id, id)
        );
        """
    )
    for t in ("menu_schedules", "menu_categories", "menu_items"):
        h.updated_at(t)
    for t in TABLES:
        h.tenant_rls(t)
    for t in ("menu_schedules", "menu_categories", "menu_items", "menu_modifier_groups", "menu_modifiers"):
        h.mutable(t)
    op.execute("GRANT DELETE ON app.menu_item_modifiers TO diyneco_api")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '3s'")
    h.refuse_if_data("menu_items")
    h.drop_tables(*reversed(TABLES))
