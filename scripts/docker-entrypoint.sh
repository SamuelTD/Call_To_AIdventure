#!/bin/sh
set -eu

if [ "${SKIP_DATA_DB_SETUP:-false}" != "true" ]; then
  uv run python db/sqlite/setup_db.py --reset
fi

uv run python src/django/manage.py migrate --noinput

exec "$@"
