#!/bin/sh
# Development entrypoint: migrate, make sure storage buckets exist, run with auto-reload.
set -e
alembic upgrade head
python -m app.scripts.init_storage
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
