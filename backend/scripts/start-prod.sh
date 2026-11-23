#!/bin/sh
# Production entrypoint.
set -e
alembic upgrade head
python -m app.scripts.init_storage
if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  # Fictional demo data for presentations. Never overwrites an existing database.
  python -m app.scripts.seed --if-empty
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${WEB_CONCURRENCY:-4}" --proxy-headers --forwarded-allow-ips="*"
