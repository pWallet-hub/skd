# PostGIS with first-boot scripts baked in (PostGIS extension + test database).
FROM postgis/postgis:16-3.4
COPY initdb /docker-entrypoint-initdb.d
RUN chmod +x /docker-entrypoint-initdb.d/*.sh
