# CatchYu / FishRadar

[中文](README.md) ｜ [English]

`CatchYu` is a Xianyu monitoring and analysis system with two product surfaces:

- `CatchYu` tenant portal: create monitoring tasks, view scan results, configure tenant notifications
- `CatchYu Console` admin portal: tenants, activation codes, account pool, logs, and platform settings

The current system is multi-tenant and uses `MySQL` as the only runtime database.

## What It Does

- Tenant login, registration, activation-code redemption, and expiry control
- Admin-managed AI entitlement per tenant
- Monitoring tasks with AI mode or keyword mode
- Result pages with export, blacklist, filtering, and admin reanalysis
- AI account pool with text/image capability routing and failover
- Database-backed account states, prompts, tasks, results, and failure guard state
- Admin-controlled notification channels for tenants
- Scheduled execution, failure circuit breaking, and log retention

## Runtime Data Placement

### Stored in MySQL

- Tasks
- Results
- Price snapshots
- Prompt documents and per-task prompt snapshots
- Account-state primary data
- Users, tenants, sessions, activation codes
- AI account pool
- Tenant notification settings
- Task failure-guard state
- Platform-level business settings
  - notifications
  - rotation
  - AI runtime flags
  - failure-guard thresholds

### Still filesystem-based

- `logs/` for runtime logs
- `images/` for downloaded images and task temporary images
- `state/` as runtime compatibility output for Playwright
- `dist/` for frontend build output
- `static/` for static assets

Legacy notes:

- `config.json`, `SQLite`, and runtime prompt files are no longer primary runtime dependencies
- `jsonl/` and `price_history/` remain only for legacy import or troubleshooting

## Stack

- Backend: `FastAPI`
- Frontend: `Vue 3 + Vite`
- Task execution: isolated Python subprocesses running `spider_v2.py`
- Browser automation: `Playwright`
- Database: `MySQL` only

See also:

- [docs/architecture.md](/Users/life2you/vibeCodes/github/FishRadar/docs/architecture.md)
- [docs/operations.md](/Users/life2you/vibeCodes/github/FishRadar/docs/operations.md)
- [docs/multi-tenant-portal-foundation.md](/Users/life2you/vibeCodes/github/FishRadar/docs/multi-tenant-portal-foundation.md)

## Quick Start

### Requirements

- Python `3.10+`
- Node.js `20+`
- MySQL `8+`
- Playwright with Chromium

### Required environment settings

This version requires `MySQL`.

AI analysis is no longer configured through a single global `.env` AI account.  
Instead, sign in as admin and configure AI providers in `Platform Settings -> AI Account Pool`.

Startup-level variables that still matter:

| Variable | Description | Required |
|------|------|------|
| `APP_DATABASE_URL` | MySQL connection string | Yes |
| `SERVER_PORT` | App port, default `8000` | No |
| `WEB_USERNAME` / `WEB_PASSWORD` | Initial admin bootstrap credentials | No |
| `RUN_HEADLESS` | Playwright headless mode | No |
| `LOGIN_IS_EDGE` | Local browser channel preference | No |

Business-level settings are already stored in MySQL and should not be maintained long-term in `.env`.

## Local Development

### Backend

```bash
python -m src.app
```

or:

```bash
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd web-ui
npm install
npm run dev
```

### One-shot startup

```bash
bash start.sh
```

## Docker

```bash
cp .env.example .env
docker compose up --build -d
docker compose logs -f app
docker compose down
```

Default URLs:

- Web: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`

The compose file starts MySQL 8 by default and the image already includes Chromium.

## First-Time Setup

1. Start the service and sign in as admin
2. Import Xianyu account-state JSON in `Account Pool Management`
3. Configure AI accounts in `Platform Settings -> AI Account Pool`
4. Manage tenants, activation codes, and AI access in `Tenant Management`
5. Sign in as a tenant and create monitoring tasks

## Role Boundaries

### Admin

- platform overview
- tenant management
- account pool management
- logs
- platform settings
- view tasks and results per tenant

### Tenant

- task workspace
- result intelligence page
- notification center

Tenants do not see admin-only capabilities and do not see data from other tenants.

## AI Routing

The runtime no longer uses one global AI account.

- `AI + image analysis enabled` → choose from image-capable AI accounts
- `AI + image analysis disabled` → choose from text-capable AI accounts
- if one provider fails, the runtime falls back to the next eligible account

Each task stores its own prompt snapshot, so tasks do not share one mutable runtime prompt.

## Task Consistency

- A task process loads task data once when the process starts
- The current scan run keeps using that startup snapshot
- If a task is edited while it is running:
  - the current run keeps using the old configuration
  - the next run uses the updated configuration

This prevents mid-run prompt drift.

## Common Commands

### Tests

```bash
pytest
```

Targeted:

```bash
pytest tests/integration/test_api_settings.py
```

### Frontend build

```bash
cd web-ui && npm run build
```

### Cleanup test databases

```bash
bash scripts/cleanup_test_dbs.sh
```

By default it preserves:

- `fishradar_feature_time_test`

and removes other `fishradar*` test databases.
