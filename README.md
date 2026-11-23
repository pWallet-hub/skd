# SmartKids – Smile & Grow

A child-wellbeing platform that connects parents, children, health information, learning
content and community services, and turns voluntary, aggregated reports into
**community-level health signals** that trained people review before anyone is alerted.

> Product vision and scope: [docs/product-vision.md](docs/product-vision.md)
> Architecture: [docs/architecture.md](docs/architecture.md) · Developer guide: [docs/development.md](docs/development.md) · Deployment (Coolify): [docs/deployment.md](docs/deployment.md)

---

## Quick start

You only need **Docker** (with Compose v2) and **make**. Every tool runs in a container.

```bash
make up        # creates .env from .env.example, builds and starts everything
make seed      # loads FICTIONAL demo data (families, schools, a demo cluster)
```

| What                | URL                                  |
|---------------------|--------------------------------------|
| Web app             | http://localhost:8000                |
| API docs (Swagger)  | http://localhost:8000/api/docs       |
| API docs (ReDoc)    | http://localhost:8000/api/redoc      |
| SeaweedFS master UI | http://localhost:9333                |
| Mailpit (dev email) | http://localhost:8025                |
| PostgreSQL          | localhost:5433 (user/pass `smartkids`) |

Demo accounts (password `SmartKids123!`):

| Email                      | Role            | Sees                                    |
|----------------------------|-----------------|-----------------------------------------|
| parent@example.com         | Parent          | Family dashboard, report symptoms       |
| analyst@example.com        | Analyst         | Overview, map, signals, alerts          |
| reviewer@example.com       | Health reviewer | Same as analyst + approves alerts       |
| institution@example.com    | Institution     | Aggregated, read-only insights          |
| admin@example.com          | Admin           | Everything + the Administration area    |

Run `make help` to see every command.

## Administration area (admin role)

| Page            | What it does                                                                 |
|-----------------|------------------------------------------------------------------------------|
| Admin dashboard | Users, sign-ins, reports per day, live status of database/Redis/SeaweedFS/workers, storage usage, recent activity |
| Users           | Search/filter, create staff accounts (temporary password), change role, activate/deactivate, reset password |
| Places          | Add/edit/delete schools, health facilities and infrastructure; pick the location on a map |
| Content         | Write, publish, archive and delete guidance articles; upload cover images     |
| Audit log       | Every sign-in, user change, alert step, signal decision, setting change, with IP |
| Settings        | Tune signal detection thresholds and the privacy minimum group size without a redeploy |

Staff users can also export de-identified aggregates as CSV from the Overview page.

## Tech stack

| Concern           | Tool                                                   | Service name |
|-------------------|--------------------------------------------------------|--------------|
| API               | **FastAPI** (Python 3.12), SQLAlchemy 2, Pydantic v2   | `backend`    |
| Migrations        | Alembic (+ GeoAlchemy2 helpers)                        | `backend`    |
| Database          | PostgreSQL 16 + **PostGIS** 3.4                        | `db`         |
| Background jobs   | Celery worker + Celery beat                            | `worker`, `scheduler` |
| Queue / cache     | Redis 7                                                | `redis`      |
| Images & files    | **SeaweedFS** (S3-compatible API)                      | `seaweedfs`  |
| Web app           | React 18 + TypeScript + Vite, TanStack Query, Leaflet  | `frontend`   |
| Entry point       | Nginx (routes `/api`, files, and the web app)          | `nginx`      |
| Dev email         | Mailpit                                                | `mailpit`    |

## Repository layout

```
.
├── backend/                 FastAPI application
│   ├── app/
│   │   ├── api/             HTTP layer: routes/ (one file per resource) + deps.py (auth, roles)
│   │   ├── core/            config, database, security (JWT/bcrypt), storage (SeaweedFS)
│   │   ├── models/          SQLAlchemy ORM models (one file per domain)
│   │   ├── schemas/         Pydantic request/response models
│   │   ├── services/        business logic (signal detection, analytics, alert fan-out)
│   │   ├── workers/         Celery app + tasks
│   │   └── scripts/         seed data, storage bootstrap
│   ├── alembic/             database migrations
│   ├── tests/               pytest suite (runs against a separate test database)
│   └── Dockerfile           development + production targets
├── frontend/                React web app
│   ├── src/api/             fetch client + shared types
│   ├── src/auth/            auth context (JWT)
│   ├── src/components/      layout + UI primitives
│   ├── src/pages/           one file per screen
│   └── Dockerfile           development + production targets
├── infra/
│   ├── nginx/               edge proxy image (config template baked in)
│   ├── postgres/            PostGIS image + first-boot scripts
│   └── seaweedfs/           SeaweedFS image; S3 identities generated from env
├── docs/                    product vision, architecture, developer guide
├── compose.yaml             local development stack
├── compose.prod.yaml        production stack (standalone — deploy this one)
├── Makefile                 developer commands (make help)
└── .env.example             all configuration, documented
```

## Important product rules (enforced in code)

1. **A parent report is an observation, not a diagnosis.** Reports default to
   `parent_observation`; only a health reviewer can mark one `clinically_confirmed`.
2. **Signals are prompts for human review**, never conclusions. Every status change needs a note.
3. **Alerts follow a four-eyes rule.** A health reviewer who did not write the alert must approve it.
4. **Aggregates are de-identified.** Counts under `AGGREGATE_MIN_CELL_SIZE` are suppressed;
   the map never shows individual children. Partner institutions only get aggregates.
5. **Child images are private.** They live in a private SeaweedFS bucket and are only served via
   short-lived signed URLs to the child's guardian.
6. **Demo data is fictional.** The seeded cluster is not a real health event.
