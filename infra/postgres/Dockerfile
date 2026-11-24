# PostGIS with first-boot scripts baked in (PostGIS extension + test database),
# and a wrapper that keeps the role password in sync with POSTGRES_PASSWORD on every start.
FROM postgis/postgis:16-3.4
COPY initdb /docker-entrypoint-initdb.d
COPY sync-password.sh /usr/local/bin/sync-password.sh
RUN chmod +x /docker-entrypoint-initdb.d/*.sh /usr/local/bin/sync-password.sh
ENTRYPOINT ["/usr/local/bin/sync-password.sh"]
# Healthy = accepting connections AND password synced (see sync-password.sh).
HEALTHCHECK --interval=5s --timeout=5s --start-period=20s --retries=30 \
  CMD pg_isready -q -U "$POSTGRES_USER" -d "$POSTGRES_DB" && test -f /tmp/password-synced
CMD ["postgres"]
