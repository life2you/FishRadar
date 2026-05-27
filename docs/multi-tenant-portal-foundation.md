# Multi-Tenant Portal Status

This document no longer describes a “phase 1 foundation”.  
It reflects the current multi-tenant state of the project.

## Current Product Split

### Admin portal

`CatchYu Console` is the platform-facing UI.

Admins can:

- view platform overview
- manage tenants
- generate and manage activation codes
- control tenant AI entitlement
- manage account-state pool
- review logs
- manage platform settings
- review tenant-scoped tasks and results

### Tenant portal

`CatchYu` is the tenant-facing UI.

Tenants can:

- sign in with their own credentials
- activate workspace access through activation codes
- create and manage their own monitoring tasks
- view only their own result pages
- configure only the notification channels allowed by the platform

## Current Isolation Model

### Authentication

- users are stored in MySQL
- sessions are stored in MySQL
- tenant membership is stored in MySQL

### Data ownership

The main business tables now carry tenant ownership where relevant:

- tasks
- result items
- price snapshots

Tenant-facing APIs filter data by `tenant_id`.

### Realtime behavior

Websocket messages are scoped so tenant-facing updates do not broadcast global platform data.

## Access Rules

### Admin

Allowed areas:

- dashboard
- tenants
- accounts
- logs
- settings
- tenant-scoped task/result inspection

### Tenant

Allowed areas:

- tasks
- results
- notifications

If a tenant is not activated or has expired access, the tenant is limited to the activation flow.

## Activation and Access

Tenants can be controlled by:

- status
- activation requirement
- activation code duration
- access expiry time
- AI entitlement

This makes it possible to operate the tenant portal as a gated SaaS-style workspace rather than a shared back office.

## AI Entitlement

Tenant AI capability is controlled by the admin side.

If a tenant does not have AI access:

- tenant task creation hides AI-only controls
- AI mode is not available as a usable path
- tasks remain limited to keyword-based strategies

## Notification Entitlement

The platform controls which notification channels tenants may use.

Tenants can only configure channels that are globally opened for tenant usage.

## Operational Outcome

Compared with the earlier architecture, the system is now much closer to a real multi-tenant product:

- separate tenant experience
- separate admin experience
- tenant data isolation
- database-backed tenant/auth/session state
- controllable tenant access lifecycle

What still remains intentionally platform-level:

- browser runtime behavior
- startup environment variables
- logs and image artifacts as filesystem runtime outputs
