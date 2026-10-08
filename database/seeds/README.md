# Seeds

Catalogue data (permissions, system roles, charge categories, plans) is seeded by Alembic migration `0010` in every environment.

Development-only demo data is created by `backend/scripts/seed_dev.py`. It refuses to run unless `APP_ENV=development`.
