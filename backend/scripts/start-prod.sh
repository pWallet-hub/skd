#!/bin/sh
# Production entrypoint — everything a deployment needs happens here, inside Docker:
#   1. database migrations   2. storage buckets   3. demo data (optional)   4. API server
set -e
alembic upgrade head
python -m app.scripts.init_storage
if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  # Fictional demo data: loads into an empty database, refreshes itself when the demo-data
  # version changes, and never touches a database that contains real (non-demo) accounts.
  python -m app.scripts.seed --auto
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${WEB_CONCURRENCY:-4}" --proxy-headers --forwarded-allow-ips="*"
