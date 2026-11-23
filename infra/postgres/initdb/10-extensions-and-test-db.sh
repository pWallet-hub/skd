#!/bin/sh
# Runs once, when the database volume is first created.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
  CREATE EXTENSION IF NOT EXISTS postgis;
  CREATE DATABASE ${POSTGRES_TEST_DB:-smartkids_test};
SQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${POSTGRES_TEST_DB:-smartkids_test}" <<-SQL
  CREATE EXTENSION IF NOT EXISTS postgis;
SQL
