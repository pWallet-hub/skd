# Demo guide — presenting SmartKids

A 15–20 minute walkthrough that shows every role using the app the way real users would.
All data is **fictional**. Every demo account uses the password **`SmartKids123!`** (the login
page also has one-click demo buttons).

## Before the meeting (5 minutes)

1. Make sure the deployment has `SEED_DEMO_DATA=true` and `DEMO_MODE=true` (see
   [deployment.md](deployment.md)). To start from a clean, known state, run
   `python -m app.scripts.seed` in the backend terminal (this **resets** all demo data).
2. Sign in as **admin** → *Settings* → *Demo mode*: check it is **On**, then click **Generate**
   once or twice so the dashboards show activity from "today".
3. Open the app in two browser windows (or one normal + one private window) so you can switch
   between a parent and a staff member quickly.

While demo mode is on, the fictional families keep using the app every few minutes: new reports,
recoveries, growth checks, vaccinations, milestones and occasional new sign-ups. Dashboards refresh
automatically every 30 seconds, so numbers visibly grow during the presentation.

## Demo accounts

| Account | Role | Story |
|---|---|---|
| `parent@example.com` | Parent (Aline) | Two children: **Keza** (4 y, attends the school with the demo cluster) and **Ganza** (9 months, measles–rubella vaccine due) |
| `analyst@example.com` | Analyst | Investigates community signals, drafts alerts |
| `reviewer@example.com` | Health reviewer | Reviews reports, approves alerts (four-eyes rule) |
| `reviewer2@example.com` | Health reviewer | Second reviewer — approve alerts written by `reviewer@` |
| `institution@example.com` | Partner institution | Aggregated, read-only insights |
| `admin@example.com` | Administrator | Users, places, content, settings, audit log, system health |
| `parent2…parent30@example.com` | Other parents | Other families in the demo community |

## Script

### 1. A new family joins (2 min) — *self-registration*
- From the login page: **Create a family account** → fill the form → you land on an empty family dashboard.
- Point out **Sign up with Google** (marked *soon* — placeholder for the next phase).
- **Add child** → name, date of birth, school, interests (photo optional — stored privately).

### 2. A parent's everyday use (5 min) — sign in as **Parent (Aline)**
- **Family dashboard**: children with badges (*1 vaccine due*, *milestone check-in*), recent reports, notifications.
- Open **Ganza** → yellow banner "Measles–Rubella 1 is due":
  - **Vaccinations** tab → *Mark given* → the badge disappears.
  - **Growth** tab → height/weight charts → *Add measurement*.
  - **Milestones** tab → "Sits without support" → *Done* 🎉.
- **Health card (QR)** → *Create QR code* → scan it with a phone (or open the link): a read-only
  card a nurse can see at the clinic, which **expires** automatically.
- **Report a concern** → pick symptoms → submit → **Notifications** shows a confirmation and
  **guidance** matched to the symptoms (e.g. hydration advice for diarrhea).
- **Find care** → nearest health facilities on a map, with call and directions buttons.
- **Guidance** → reviewed articles by category.

### 3. Community intelligence (4 min) — sign in as **Analyst**
- **Overview**: families, reports this week, open signals; reports-per-day chart; top concerns. *Export CSV* (de-identified).
- **Map**: toggle layers — report clusters, schools, health facilities, infrastructure, signals.
- **Signals** → the open *gastrointestinal* signal at **Umucyo Primary School**: reports vs expected baseline.
  - *Start review* (a note is required) → *Confirm concern* → *Draft community alert*, target the school.
- Show the **Resolved** tab: a past respiratory investigation with its full audit trail and published alert.

### 4. Health professional review (3 min) — sign in as **Health reviewer**
- **Report review**: incoming parent reports with age and area only (no child names) → *Confirm*
  (the parent receives a "Your report was reviewed" notification).
- **Alerts**: approve the analyst's alert → *Publish* → switch to the parent window → the alert
  appears in Aline's notifications (if Keza's school was targeted).
- Point out the **four-eyes rule**: a reviewer cannot approve an alert they wrote themselves.

### 5. Partner institution (1 min) — sign in as **Institution**
- Same overview and map, **read-only** and aggregated; small groups are hidden for privacy.

### 6. Running the platform (3 min) — sign in as **Admin**
- **Admin dashboard**: users by role, sign-ins, live **system status** (database, Redis, SeaweedFS, workers), storage usage, recent activity.
- **Users**: search/filter, add a staff account (temporary password), deactivate, reset password.
- **Places**: add a school or clinic by clicking on the map.
- **Content**: publish the draft article "Safe sleep for babies".
- **Settings**: tune signal detection and privacy thresholds; **Demo mode**.
- **Audit log**: everything you just did, with who/when.

## Key messages for the PO

- Parent reports are **observations, not diagnoses**; only health professionals confirm.
- Signals are **prompts for human review**, never automatic outbreak declarations.
- Alerts need **a second person's approval** before families are notified.
- Community statistics are **de-identified**; small groups are suppressed.
- Child photos are **private**; health-card QR links are **time-limited**.

## Features inspired by similar apps

| Feature | Common in |
|---|---|
| Vaccination schedule with due/overdue reminders | Digital immunization cards & national e-health apps |
| Developmental milestone checklist by age | Child development trackers (e.g. milestone tracker apps) |
| Growth charts (height/weight over time) | Pediatric growth apps, clinic growth cards |
| QR health card shared with a clinic, time-limited | Digital vaccination certificates / health passports |
| Symptom report → instant guidance | Symptom-checker and telehealth apps |
| Find nearby care with directions | Health-facility finder apps |
| Community alerts with human approval | Public-health early-warning systems |
| Sign in with Google (placeholder) | Most consumer apps — planned for the next phase |
