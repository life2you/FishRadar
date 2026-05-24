# Multi-Tenant Portal Foundation

## Goal

Build a tenant portal where tenant users can:

- sign in with their own credentials
- create and manage their own monitoring tasks
- view only their own result pages

Platform admins keep access to the existing full back office:

- dashboard
- tasks
- results
- accounts
- logs
- settings
- prompts

## Phase 1 Scope

This branch starts the foundation layer and intentionally stops short of full tenant data isolation.

Included in phase 1:

- database tables for tenants, users, memberships, and auth sessions
- database-backed login with password hashing and session cookies
- default admin bootstrap from existing `WEB_USERNAME` / `WEB_PASSWORD`
- frontend role-aware auth state
- frontend route and sidebar role filtering
- task schema prepared for tenant ownership through `tenant_id`

Deferred to phase 2:

- task queries filtered by tenant end-to-end
- result queries filtered by tenant end-to-end
- websocket channel isolation by tenant
- tenant user / tenant admin management UI
- account / prompt / logs / images directory partitioning by tenant

## Target Roles

- `admin`
  - full platform access
- `tenant`
  - dashboard, tasks, results only

## Data Model

### tenants

- `id`
- `name`
- `slug`
- `status`
- `created_at`

### users

- `id`
- `username`
- `password_hash`
- `role`
- `status`
- `display_name`
- `created_at`

### user_tenant_memberships

- `id`
- `user_id`
- `tenant_id`
- `membership_role`
- `created_at`

### auth_sessions

- `session_token`
- `user_id`
- `tenant_id`
- `expires_at`
- `created_at`

## Frontend Access Rules

### admin

- `/dashboard`
- `/tasks`
- `/accounts`
- `/results`
- `/logs`
- `/settings`

### tenant

- `/dashboard`
- `/tasks`
- `/results`

## Backend Access Rules

### public

- `POST /auth/status`
- `GET /auth/me`
- `POST /auth/logout`
- `GET /health`

### authenticated

- dashboard
- tasks
- results

### admin only

- accounts
- logs
- settings
- prompts
- login-state

## Notes

- Existing installations continue to work because startup bootstraps one admin user from env credentials.
- Existing tasks and results currently remain global historical data until tenant ownership migration is completed.
- New tenant isolation work should reuse the session and role plumbing introduced in this phase.
