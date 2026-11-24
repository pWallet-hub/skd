# Deployment

**`compose.yaml` is the production stack.** Local development adds `compose.override.yaml`
on top of it — Docker Compose loads that file automatically on your machine, while Coolify (which
passes `-f compose.yaml` explicitly) never sees it. So the same repository is safe to deploy
without any special settings.

Why `compose.yaml` works on hosted platforms:

- **No bind mounts.** Config for nginx, PostgreSQL and SeaweedFS is baked into small images
  (`infra/*/Dockerfile`). Platforms such as Coolify build from git but do not have the repository
  files on the host, so a bind mount like `./infra/seaweedfs/s3.json` turns into an empty
  directory and the service fails.
- **SeaweedFS credentials come from env vars** (`S3_ACCESS_KEY`, `S3_SECRET_KEY`); the S3 config is
  generated at start-up by `infra/seaweedfs/generate-s3-config.sh`.
- **One public service.** Only `frontend` receives traffic (port 80). It serves the web app and
  forwards `/api` and file requests to the backend and SeaweedFS. No host ports are published;
  the platform's proxy adds TLS.

## Coolify

1. **New resource → Public/Private repository →** select the repo and branch `main`.
2. **Build pack:** `Docker Compose`. **Docker Compose location:** `/compose.yaml` (the default).
3. **Environment variables** (Coolify lists them after it reads the file). Required:

   | Variable            | Example / how to generate                         |
   |---------------------|---------------------------------------------------|
   | `PUBLIC_BASE_URL`   | `https://smartkids.example.org` (your domain, no trailing slash) |
   | `SECRET_KEY`        | `openssl rand -hex 32`                            |
   | `POSTGRES_PASSWORD` | `openssl rand -hex 24`                            |
   | `S3_SECRET_KEY`     | `openssl rand -hex 24`                            |

   For a demo, also set `DEMO_MODE=true` (demo families keep generating activity) and
   `SEED_DEMO_DATA=true`. Demo data then loads automatically into an empty database **and
   refreshes itself on deploy whenever its version changes** — but only while every account is a
   demo account (`@example.com`). As soon as a real person registers, it is never touched again.

   Optional: `S3_ACCESS_KEY`, `S3_BUCKET_PUBLIC`, `S3_BUCKET_PRIVATE`, `WEB_CONCURRENCY`,
   `VITE_MAP_TILE_URL` (tile server for the map), `SMTP_*`, and the `SIGNAL_*` defaults.
4. **Domains:** set the domain on the **`frontend`** service only, e.g. `https://smartkids.example.org`
   (it listens on port 80, Coolify's default). Leave the other services without a domain. It
   must match `PUBLIC_BASE_URL` exactly (scheme and host), otherwise signed image URLs will not verify.
5. **Deploy.** Every start runs, inside Docker: database migrations → storage buckets → demo
   data (if enabled) → API server. No terminal steps are needed.
6. *(Demo only)* To reset the demo data later, run `python -m app.scripts.seed` in the `backend`
   terminal in Coolify — **never on a real production database** (it wipes data).

After changing `S3_SECRET_KEY` you must redeploy both `seaweedfs` and the backend services.

## Any other Docker host

```bash
cp .env.example .env.production   # fill in the required values above
docker compose -f compose.yaml --env-file .env.production up -d --build
```

Put a TLS-terminating proxy (Caddy, Traefik, nginx) in front of the `frontend` service, or add a
`ports: ["80:80"]` mapping to it.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `dependency failed to start: container seaweedfs… is unhealthy` | `S3_SECRET_KEY` missing, or an old commit that bind-mounted `s3.json`. Check the seaweedfs logs. |
| `Bind for 0.0.0.0:8000 failed: port is already allocated` | The dev override was deployed. Make sure the compose file is `compose.yaml` and you are on the latest commit; production publishes no host ports. |
| `dependency failed to start: container backend… is unhealthy` | Check the backend logs. `password authentication failed` was caused by a database volume created with an older password; the `db` image now re-applies `POSTGRES_PASSWORD` on every start (`infra/postgres/sync-password.sh`), so just redeploy. |
| Login fails / `405 Not Allowed` on `/api/...` | The domain points at a service that doesn't forward `/api`. Put the domain on `frontend` (latest commit) and redeploy. |
| `required variable … is missing a value` | Set that variable in the platform's environment settings. |
| Images return `403` / `SignatureDoesNotMatch` | `PUBLIC_BASE_URL` does not exactly match the domain in the browser. |
| Map is blank | The tile server blocked the request; set `VITE_MAP_TILE_URL` to your tile provider and redeploy. |

## Backups

Persisted volumes: `postgres_data` (database), `seaweedfs_data` (all uploaded files), `redis_data`
(queue only, safe to lose). Back up the first two, e.g. with Coolify's scheduled database backups
for PostgreSQL and a volume backup for SeaweedFS.

## Google sign-in (placeholder)

The login and registration pages show **Continue with Google**, and `POST /api/v1/auth/google`
returns `501 Not Implemented`. To implement it later:

1. Create an OAuth client in Google Cloud Console (Web application); add the site URL as an
   authorised JavaScript origin. Set `GOOGLE_CLIENT_ID`.
2. Frontend: load Google Identity Services and send the returned ID token (credential) to
   `/api/v1/auth/google`.
3. Backend: verify it with `google-auth` (`id_token.verify_oauth2_token`), check the audience and
   `email_verified`, then sign in the matching user or create a **parent** account and return the
   usual token pair. Staff accounts stay admin-created.
