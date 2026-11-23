# Developer guide

## Daily workflow

```bash
make up            # start (or rebuild) the stack
make logs s=backend
make test          # backend tests
make lint          # ruff + eslint + tsc
make format        # auto-format backend
make shell         # bash inside the backend container
make db-shell      # psql
make down          # stop
make reset         # stop AND delete all data volumes (database, files)
```

Code is bind-mounted into the containers: the API reloads on save (uvicorn `--reload`) and the
web app hot-reloads (Vite HMR). You do not need Python or Node installed locally.

After changing `backend/requirements*.txt` or `frontend/package.json`, run `make build` (or `make up`).

## Database changes

1. Edit / add a model in `backend/app/models/` (and import it in `models/__init__.py`).
2. `make migration m="describe the change"` — generates a file in `backend/alembic/versions/`.
3. Review the generated file, then `make migrate`.

Enums are stored as `VARCHAR` (see `models/enums.py`), so adding an enum value needs no migration.

## Adding an API endpoint

1. Schema(s) in `app/schemas/<domain>.py`.
2. Business logic in `app/services/<domain>.py` if it is more than simple CRUD.
3. Route in `app/api/routes/<domain>.py`; protect with a role dependency from `app/api/deps.py`
   (`CurrentUser`, `ParentUser`, `HealthTeamUser`, `InsightUser`, `ReviewerUser`, `AdminUser`).
4. Register new routers in `app/api/router.py`.
5. Test in `backend/tests/`.
6. Add the TypeScript type in `frontend/src/api/types.ts`.

## Working with files (SeaweedFS)

Use `app/core/storage.py`:

```python
key = upload_file(file.file, filename=..., content_type=..., visibility="private", prefix="children/42")
url = file_url(key, "private")    # short-lived signed URL
```

Use `"public"` only for non-sensitive content. Store the **key** in the database, never the URL.

## Tests

Tests run inside the backend container against a separate database (`POSTGRES_TEST_DB`,
created on first boot by `infra/postgres/initdb`). The schema is recreated each session and
tables are truncated after every test.

## Naming conventions

| Thing                  | Convention                         | Example                      |
|------------------------|------------------------------------|------------------------------|
| Docker services        | role name, lowercase               | `backend`, `db`, `worker`    |
| DB tables              | plural snake_case                  | `symptom_reports`            |
| Python modules         | snake_case, one domain per file    | `services/surveillance.py`   |
| API paths              | plural nouns, kebab-case           | `/api/v1/notifications/read-all` |
| Env vars               | UPPER_SNAKE, grouped by service    | `S3_BUCKET_PRIVATE`          |
| React components/pages | PascalCase, `*Page.tsx` for routes | `ReportSymptomsPage.tsx`     |
| Branches               | `feature/…`, `fix/…`, `chore/…`    | `feature/growth-charts`      |
| Commits                | Conventional Commits               | `feat(signals): add CUSUM`   |

## Production

See [deployment.md](deployment.md). Deploy `compose.prod.yaml` (standalone), never `compose.yaml`.
