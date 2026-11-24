#!/bin/bash
# Starts PostgreSQL normally, then makes POSTGRES_PASSWORD authoritative.
#
# Why: the official image only applies POSTGRES_PASSWORD when the data volume is first created.
# If the volume already exists (e.g. after a failed deploy, or after rotating the secret), the
# app would fail with "password authentication failed". Local socket connections inside this
# container are trusted, so we can (re)set the password without knowing the old one.
set -u

# Health marker: the container only reports healthy after the password has been applied.
# /tmp is fresh on every container start, so a stale marker can never exist.
docker-entrypoint.sh "$@" &
pg_pid=$!
trap 'kill -TERM "$pg_pid" 2>/dev/null' TERM INT

user="${POSTGRES_USER:-postgres}"
for _ in $(seq 1 120); do
  if ! kill -0 "$pg_pid" 2>/dev/null; then
    wait "$pg_pid"; exit $?
  fi
  # Wait for the real server (the first-boot temporary server also listens on the socket).
  if pg_isready -q -h /var/run/postgresql -U "$user" -d postgres \
     && psql -h /var/run/postgresql -U "$user" -d postgres -v ON_ERROR_STOP=1 -q \
          -v user="$user" -v pw="${POSTGRES_PASSWORD}" >/dev/null 2>&1 <<'SQL'
ALTER ROLE :"user" WITH PASSWORD :'pw';
SQL
  then
    echo "sync-password: password for role '$user' applied from POSTGRES_PASSWORD"
    touch /tmp/password-synced
    break
  fi
  sleep 1
done

# Keep waiting until PostgreSQL has fully stopped (a trapped signal interrupts `wait`).
status=0
while kill -0 "$pg_pid" 2>/dev/null; do
  wait "$pg_pid"
  status=$?
done
exit "$status"
