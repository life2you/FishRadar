# Architecture

## Overview

The current system is split into three runtime layers:

1. `FastAPI` web application
2. independent task subprocesses
3. `MySQL` as the only runtime database

At a product level, there are two UIs:

- `CatchYu` tenant portal
- `CatchYu Console` admin portal

## Main Components

### Backend

- entry: [/Users/life2you/vibeCodes/github/FishRadar/src/app.py](/Users/life2you/vibeCodes/github/FishRadar/src/app.py)
- routes: [/Users/life2you/vibeCodes/github/FishRadar/src/api/routes](/Users/life2you/vibeCodes/github/FishRadar/src/api/routes)
- services: [/Users/life2you/vibeCodes/github/FishRadar/src/services](/Users/life2you/vibeCodes/github/FishRadar/src/services)
- persistence: [/Users/life2you/vibeCodes/github/FishRadar/src/infrastructure/persistence](/Users/life2you/vibeCodes/github/FishRadar/src/infrastructure/persistence)

### Frontend

- entry views: [/Users/life2you/vibeCodes/github/FishRadar/web-ui/src/views](/Users/life2you/vibeCodes/github/FishRadar/web-ui/src/views)
- layout and shared UI: [/Users/life2you/vibeCodes/github/FishRadar/web-ui/src/components](/Users/life2you/vibeCodes/github/FishRadar/web-ui/src/components)

### Task Runtime

- task CLI: [/Users/life2you/vibeCodes/github/FishRadar/spider_v2.py](/Users/life2you/vibeCodes/github/FishRadar/spider_v2.py)
- scraper core: [/Users/life2you/vibeCodes/github/FishRadar/src/scraper.py](/Users/life2you/vibeCodes/github/FishRadar/src/scraper.py)
- process manager: [/Users/life2you/vibeCodes/github/FishRadar/src/services/process_service.py](/Users/life2you/vibeCodes/github/FishRadar/src/services/process_service.py)

## Execution Model

### Web app

The FastAPI app is responsible for:

- authentication
- tenant/admin routing
- task CRUD
- settings CRUD
- result browsing and export
- starting and stopping subprocesses
- websocket updates

### Task subprocesses

Each running task is executed as a dedicated Python subprocess.  
The process is started by `ProcessService` and runs `spider_v2.py --task-id <id>`.

The task subprocess:

- loads the task once from MySQL
- resolves runtime login-state files
- resolves the task prompt snapshot
- runs Playwright scraping
- sends each candidate item through keyword logic or AI analysis
- persists results back to MySQL

## Configuration Model

The current configuration model is intentionally split:

### Database-backed business settings

- notification configuration
- rotation configuration
- AI runtime flags
- failure guard thresholds
- AI accounts
- tenant notification channel switches

These are stored in MySQL and are the primary runtime source of truth.

### Environment-backed startup settings

- `APP_DATABASE_URL`
- `SERVER_PORT`
- `RUN_HEADLESS`
- `LOGIN_IS_EDGE`
- `STATE_FILE`

These remain environment variables because they affect process startup or local browser behavior.

## Data Storage Model

### MySQL

Runtime business data now lives in MySQL:

- tasks
- result items
- price snapshots
- prompt documents
- prompt snapshots per task
- account-state primary data
- users / tenants / memberships / sessions
- activation codes
- AI accounts
- tenant notification settings
- task failure guard state
- app metadata / platform settings

### Filesystem

The filesystem is now mainly for runtime artifacts:

- `logs/` for task logs
- `images/` for downloaded or temporary images
- `state/` for compatibility output consumed by Playwright
- `dist/` for frontend build output
- `static/` for static assets

## Multi-Tenant Boundary

### Admin scope

Admin users can access:

- platform overview
- tenant management
- account pool
- logs
- platform settings
- tenant-scoped tasks and results

### Tenant scope

Tenant users can access:

- task workspace
- results page
- notification center

All task and result access is filtered by `tenant_id`.

## AI Routing Model

AI execution now uses the AI account pool instead of one global provider.

Selection rules:

- if `analyze_images=true`, route to image-capable accounts
- if `analyze_images=false`, route to text-capable accounts
- if one account fails, try the next eligible account

Important:

- the AI account does not hold task context
- each analysis call receives the task prompt explicitly
- prompt state is task-scoped, not global

## Task Consistency

When a task process starts, it reads the task snapshot once.

That means:

- the current run uses the startup snapshot consistently
- editing a task mid-run does not change the already-running process
- the next run will use the updated task data

This is intentional to avoid mid-run drift.

## Legacy Status

The following are no longer primary runtime dependencies:

- `config.json` task chain
- runtime prompt files as the main source of truth
- global `.env` AI provider fallback

Legacy directories such as `jsonl/` and `price_history/` remain only for migration or inspection.
