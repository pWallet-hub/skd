#!/bin/sh
# Production entrypoint.
set -e
alembic upgrade head
python -m app.scripts.init_storage
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${WEB_CONCURRENCY:-4}" --proxy-headers
