# Architecture

## Containers

```
                         browser
                            │  http://localhost:8000
                            ▼
                     ┌─────────────┐
                     │    nginx    │  single entry point
                     └──┬───┬───┬──┘
          /api/*        │   │   │   /<bucket>/*  (images/files)
     ┌──────────────────┘   │   └───────────────────────┐
     ▼                      ▼ /*                         ▼
┌──────────┐          ┌──────────┐               ┌─────────────┐
│ backend  │          │ frontend │               │  seaweedfs  │ S3 API :8333
│ FastAPI  │──────────┤  Vite /  │               │ master/vol/ │
└──┬───┬───┘  boto3   │  React   │               │   filer     │
   │   └──────────────┼──────────┼──────────────▶└─────────────┘
   │                  └──────────┘
   │ SQLAlchemy                         ┌──────────┐     ┌───────────┐
   ├───────────────────────────────────▶│    db    │◀────│  worker   │ Celery
   │                                    │ PostGIS  │     │ scheduler │ beat
   │ Celery tasks                       └──────────┘     └─────┬─────┘
   └───────────────────────────────────▶┌──────────┐◀──────────┘
                                        │  redis   │
                                        └──────────┘
```

## Backend layering

`routes → services → models`. Routes handle HTTP, validation (Pydantic schemas) and
authorisation (role dependencies in `api/deps.py`). Business rules that matter for safety
(signal detection, alert recipients, aggregation & suppression) live in `services/` so they
can be tested without HTTP and reused by Celery tasks.

## Roles

| Role              | Can                                                                    |
|-------------------|-------------------------------------------------------------------------|
| `parent`          | manage own children, report symptoms, read guidance, own notifications |
| `health_reviewer` | everything an analyst can + verify reports, approve/retract alerts, publish health content |
| `analyst`         | aggregated analytics, map, signals (review workflow), draft alerts      |
| `institution`     | aggregated analytics, map, signals (read-only)                          |
| `admin`           | everything                                                              |

## Domain model

```
User (role) ─1:N─ Child ─1:N─ GrowthMeasurement
                    │
                    └─1:N─ SymptomReport ─N:M─ Symptom (category)
                              │  (school, area copied at report time)
AdministrativeArea (province › district › sector › cell › village, PostGIS centroid/boundary)
School, HealthFacility, InfrastructureAsset (PostGIS points, linked to an area)

HealthSignal (category + school OR area, window, count, expected, score, status)
   └─1:N─ InvestigationNote (audit trail of status changes)
CommunityAlert (status: draft → pending_approval → approved → published / retracted)
   ├─N:M─ target areas / target schools
   └─1:N─ Notification (one per recipient)
Article (guidance content; public cover images)
```

## Community signal detection

`app/services/surveillance.py`, run hourly by Celery beat and on demand
(`POST /api/v1/signals/detect`).

For each (school, category) and (area, category):

```
window   = last SIGNAL_WINDOW_DAYS days       (default 7)
baseline = SIGNAL_BASELINE_DAYS days before   (default 28)
expected = baseline_count × window/baseline
score    = window_count / max(expected, 1)
signal   if window_count ≥ SIGNAL_MIN_REPORTS (4) and score ≥ SIGNAL_RATIO_THRESHOLD (2.0)
```

Open signals are updated rather than duplicated. Only reports with
`consent_to_aggregate = true` are counted. The method is intentionally simple and explainable;
it can later be replaced (e.g. EARS C1–C3, Poisson/CUSUM, SaTScan-style spatial scan) without
changing the API.

Signal workflow (`TRANSITIONS` in the same file):

```
detected ──▶ under_review ──▶ confirmed ──▶ resolved
    │             │
    └──▶ dismissed ◀┘   (dismissed can be re-opened to under_review)
```

## Administration

- **Audit log** (`audit_logs`, `services/audit.py`): append-only. `audit.record(...)` is staged in
  the same transaction as the change it describes, so a change and its audit entry are committed
  together. Recorded: sign-ins, user create/update/role change/(de)activation/password reset,
  alert lifecycle, signal transitions, report verification, article status changes, place edits,
  settings changes.
- **Runtime settings** (`system_settings`, `services/system_settings.py`): signal-detection
  thresholds and `aggregate_min_cell_size` default to the environment variables and can be
  overridden by admins at `/api/v1/admin/settings/detection`. Detection and analytics always read
  the effective value.
- **System status** (`/api/v1/admin/system`): live checks of PostGIS, Redis, SeaweedFS and Celery
  workers, plus per-bucket object counts and sizes.

## File storage (SeaweedFS)

| Bucket              | Contents                          | Access                                   |
|---------------------|-----------------------------------|------------------------------------------|
| `smartkids-public`  | article covers, learning images   | anonymous read via nginx                 |
| `smartkids-private` | child photos, attachments         | presigned URL (15 min), guardian only    |

Presigned URLs are signed against `PUBLIC_BASE_URL`; nginx forwards the original `Host`
header to SeaweedFS so the signature verifies. Identities are in `infra/seaweedfs/s3.json`.
Buckets are created on backend start (`app/scripts/init_storage.py`).

## Privacy & safety controls

- Aggregates below `AGGREGATE_MIN_CELL_SIZE` are returned as `null` with `suppressed: true`.
- Institutions never get endpoints that return individual reports.
- Parents only ever see their own children (404, not 403, for others' records).
- Location on a report is copied at report time (history is not rewritten if a family moves).
- Every signal status change requires a note; alert approval requires a different person.
