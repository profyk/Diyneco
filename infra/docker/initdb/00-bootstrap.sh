#!/bin/sh
# Runs once, on first start of an empty data volume.
set -eu
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres -f /bootstrap/bootstrap.sql \
  -v owner_password="$DIYNECO_OWNER_PASSWORD" \
  -v api_password="$DIYNECO_API_PASSWORD" \
  -v worker_password="$DIYNECO_WORKER_PASSWORD"
