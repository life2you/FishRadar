# Operations

## Deployment Model

The recommended deployment model is:

- one FastAPI app container
- one MySQL 8 instance
- one Nginx reverse-proxy container for public ingress
- persistent volumes for logs and images

Recommended compose usage:

```bash
docker compose -f docker-compose.yaml -f docker-compose.nginx.yml up --build -d
```

Roles:

- `docker-compose.yaml`: app + MySQL baseline
- `docker-compose.nginx.yml`: reverse proxy overlay for server deployment

Nginx configuration:

- HTTP proxy: [deploy/nginx/default.conf](/Users/life2you/vibeCodes/github/FishRadar/deploy/nginx/default.conf)
- HTTPS example: [deploy/nginx/default-ssl.conf.example](/Users/life2you/vibeCodes/github/FishRadar/deploy/nginx/default-ssl.conf.example)

## Required Startup Settings

These settings should still be managed through `.env`:

- `APP_DATABASE_URL`
- `SERVER_PORT`
- `WEB_USERNAME`
- `WEB_PASSWORD`
- `RUN_HEADLESS`
- `LOGIN_IS_EDGE`
- `STATE_FILE`
- `APP_ENV`
- `AUTH_COOKIE_SECURE`
- login rate limit bootstrap values

Reason:

- they affect process startup, browser channel selection, or bootstrap behavior
- they are not tenant-level or business-level mutable settings

`WEB_USERNAME` and `WEB_PASSWORD` should be treated as initial admin bootstrap credentials rather than long-term business configuration.

## Security Baseline For Public Deployment

Before exposing the system publicly, apply at least:

- HTTPS via Nginx
- `APP_ENV=production`
- non-default `WEB_USERNAME` and `WEB_PASSWORD`
- MySQL not exposed to the public internet
- firewall allowing only `22/80/443` (or your chosen SSH port)

Cookie behavior:

- in production, auth cookies are emitted with `Secure`
- if you stay on plain HTTP, browser login cookies will not behave correctly in production mode
- use HTTPS when `APP_ENV=production`

Login protection:

- `/auth/login` and `/auth/status` are rate-limited by source IP
- defaults are configurable through:
  - `LOGIN_RATE_LIMIT_MAX_ATTEMPTS`
  - `LOGIN_RATE_LIMIT_WINDOW_SECONDS`
  - `LOGIN_RATE_LIMIT_BLOCK_SECONDS`

Admin bootstrap protection:

- production startup rejects an empty database when `WEB_USERNAME / WEB_PASSWORD` still use the default `admin / admin123`
- this behavior is controlled by `ENFORCE_PRODUCTION_ADMIN_BOOTSTRAP_SAFETY`

## Business Settings Now Stored In MySQL

The following settings are now stored in the database and should be managed from the UI or APIs:

- notification settings
- tenant notification channel switches
- rotation settings
- AI runtime settings
- failure guard thresholds
- AI account pool

## First-Time Bootstrap

### 1. Prepare database

Create or provide a MySQL database and set `APP_DATABASE_URL`.

### 2. Start app

Start the app once.  
On startup it will:

- create tables
- apply schema migrations
- bootstrap the admin user
- import some legacy data when present

### 3. Configure admin basics

After sign-in as admin:

- import Xianyu login-state data
- configure AI accounts
- configure notification channels if needed
- review tenant settings

## AI Operations

### Current model

AI providers are managed in the admin UI as pooled accounts.

Each account can be:

- enabled or disabled
- text-capable
- image-capable
- prioritized

### Routing

- text-only tasks use text-capable accounts
- image-analysis tasks use image-capable accounts
- failures fall through to the next candidate

### Operational note

If AI quality changes, check these in order:

1. task prompt snapshot
2. selected AI account capability
3. last AI account test result
4. result reanalysis behavior

## Login-State Operations

Login-state primary data is stored in MySQL.

At runtime:

- account-state data is materialized into temporary JSON files
- Playwright reads those files
- container rebuilds do not destroy the primary login-state data

This means:

- account import/export should be treated as DB-backed operations
- `state/` is no longer the primary source of truth

## Prompt Operations

Prompt documents are now database-backed.

Implications:

- prompt edits do not depend on disk files
- task prompt snapshots survive container rebuilds
- runtime prompt resolution reads from database-backed values

## Task Runtime Behavior

### Snapshot behavior

Each task process loads the task configuration once at startup.

Implications:

- current run stays stable even if the task is edited mid-run
- the next run will pick up changes

### Logs

Task logs are still written to `logs/`.

This is expected and intentional.  
They are runtime artifacts rather than primary business data.

## Failure Guard Operations

Both the failure-guard state and its thresholds are now database-backed.

This means:

- restart-safe failure counters
- restart-safe pause windows
- no more `task-failure-guard.json` runtime dependency

Typical reasons for triggering failure guard:

- no usable login state
- no usable proxy
- repeated runtime failures for the same task

## Cleanup

### Test database cleanup

Use:

```bash
bash scripts/cleanup_test_dbs.sh
```

Default behavior:

- preserve `fishradar_feature_time_test`
- remove other `fishradar*` test databases

### Log cleanup

Task log cleanup still runs on startup based on:

- `TASK_LOG_RETENTION_DAYS`

This remains startup-level behavior.

## What Is No Longer Recommended

Do not rely on these as primary runtime sources:

- `config.json`
- prompt text files
- `state/` as the long-term source of login-state truth
- one global `.env` AI provider account

## Troubleshooting Checklist

### Task shows old AI behavior after task edit

Expected if the task is already running.  
Stop and restart the task, or wait for the next scheduled run.

### AI analysis is skipped

Check:

1. whether the tenant is allowed to use AI
2. whether there is at least one eligible AI account
3. whether the task has a valid prompt snapshot

### Notification test fails

Check:

1. platform notification configuration
2. tenant notification channel visibility
3. tenant-specific notification settings

### Login works but scraping fails

Check:

1. account-state availability in admin account pool
2. whether runtime state files were materialized
3. task logs in `logs/`
