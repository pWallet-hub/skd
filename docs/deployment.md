# Deployment

Production uses **`compose.prod.yaml`** — a standalone file (not an override). Do **not** deploy
`compose.yaml`: that is the development stack and relies on bind-mounting the source code.

Why `compose.prod.yaml` works on hosted platforms:

- **No bind mounts.** Config for nginx, PostgreSQL and SeaweedFS is baked into small images
  (`infra/*/Dockerfile`). Platforms such as Coolify build from git but do not have the repository
  files on the host, so a bind mount like `./infra/seaweedfs/s3.json` turns into an empty
  directory and the service fails.
- **SeaweedFS credentials come from env vars** (`S3_ACCESS_KEY`, `S3_SECRET_KEY`); the S3 config is
  generated at start-up by `infra/seaweedfs/generate-s3-config.sh`.
- **No host ports.** Only `nginx` serves traffic (port 80); the platform's proxy adds TLS.

## Coolify

1. **New resource → Public/Private repository →** select the repo and branch `main`.
2. **Build pack:** `Docker Compose`. **Docker Compose location:** `/compose.prod.yaml`.
3. **Environment variables** (Coolify lists them after it reads the file). Required:

   | Variable            | Example / how to generate                         |
   |---------------------|---------------------------------------------------|
   | `PUBLIC_BASE_URL`   | `https://smartkids.example.org` (your domain, no trailing slash) |
   | `SECRET_KEY`        | `openssl rand -hex 32`                            |
   | `POSTGRES_PASSWORD` | `openssl rand -hex 24`                            |
   | `S3_SECRET_KEY`     | `openssl rand -hex 24`                            |

   Optional: `S3_ACCESS_KEY`, `S3_BUCKET_PUBLIC`, `S3_BUCKET_PRIVATE`, `WEB_CONCURRENCY`,
   `VITE_MAP_TILE_URL` (tile server for the map), `SMTP_*`, and the `SIGNAL_*` defaults.
4. **Domains:** set the domain on the **`nginx`** service only, e.g. `https://smartkids.example.org:80`
   (`:80` tells Coolify which container port to route to). It must match `PUBLIC_BASE_URL`,
   otherwise signed image URLs will not verify.
5. **Deploy.** First start runs database migrations and creates the storage buckets automatically.
6. *(Optional, demo only)* Load the fictional demo data from the `backend` terminal in Coolify:
   `python -m app.scripts.seed` — **never on a real production database** (it wipes data).

After changing `S3_SECRET_KEY` you must redeploy both `seaweedfs` and the backend services.

## Any other Docker host

```bash
cp .env.example .env.prod   # fill in the required values above
docker compose -f compose.prod.yaml --env-file .env.prod up -d --build
```

Put a TLS-terminating proxy (Caddy, Traefik, nginx) in front of the `nginx` service, or add a
`ports: ["80:80"]` mapping to it.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `dependency failed to start: container seaweedfs… is unhealthy` | Deploying `compose.yaml` instead of `compose.prod.yaml`, or `S3_SECRET_KEY` missing. Check the seaweedfs logs. |
| `required variable … is missing a value` | Set that variable in the platform's environment settings. |
| Images return `403` / `SignatureDoesNotMatch` | `PUBLIC_BASE_URL` does not exactly match the domain in the browser. |
| Map is blank | The tile server blocked the request; set `VITE_MAP_TILE_URL` to your tile provider and redeploy. |

## Backups

Persisted volumes: `postgres_data` (database), `seaweedfs_data` (all uploaded files), `redis_data`
(queue only, safe to lose). Back up the first two, e.g. with Coolify's scheduled database backups
for PostgreSQL and a volume backup for SeaweedFS.
