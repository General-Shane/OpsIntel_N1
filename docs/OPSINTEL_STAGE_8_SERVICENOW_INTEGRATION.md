# OPSINTEL — STAGE 8 ARCHITECTURE GUIDE
## Live ServiceNow Integration & Enterprise Ingestion Layer

**Author**: Senior Implementation Engineer  
**Status**: 100% Implemented & Verified  
**Date**: August 2026  
**Audience**: Chief Architect, Integration Engineers, SRE Team, Security Architects  

---

## 1. Executive Summary

Stage 8 transitions OPSINTEL from a standalone synthetic operations dashboard into a production-grade enterprise platform capable of bidirectional synchronization with ServiceNow Table APIs and real-time event streaming via cryptographically verified webhooks.

All components adhere to strict zero-secret-leakage principles, idempotency, rate limiting, exponential backoff, dead-letter failure queuing, immutable audit logging, and role-based access control.

---

## 2. Architecture & Data Flow

```
                      +-----------------------------+
                      |   ServiceNow Instance       |
                      |   (Table API / Webhooks)    |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               | (Outbound Pull)                           | (Inbound Push)
               v                                           v
+-------------------------------+             +-------------------------------+
|  ServiceNowClient             |             |  ServiceNowWebhookReceiver    |
|  - RateLimiter (Token Bucket) |             |  - HMAC-SHA256 Verification   |
|  - Exponential Backoff Retry  |             |  - Timestamp Drift Check (<5m)|
|  - AuthProvider (OAuth2/Basic)|             |  - Replay Key Ledger (Unique) |
+---------------+---------------+             +---------------+---------------+
                |                                             |
                +----------------------+----------------------+
                                       |
                                       v
                     +-----------------------------------+
                     |  ServiceNowSyncEngine             |
                     |  - sn_to_opsintel_* Normalization |
                     |  - Idempotent Ingestion (Upsert)  |
                     |  - Dead-Letter Queue (Failures)   |
                     |  - Immutable AuditEvent Logging   |
                     |  - Controlled Write-Back Engine   |
                     +-----------------+-----------------+
                                       |
                                       v
                     +-----------------------------------+
                     |  Enterprise Relational Storage    |
                     |  - Services, Incidents, Problems, |
                     |    Changes, SLAs, AuditEvents     |
                     |  - IntegrationConfigs, SyncStates |
                     |  - IntegrationFailures, Webhooks  |
                     +-----------------------------------+
```

---

## 3. Core Capabilities & Technical Specifications

### A. Authentication & Secrets Provider (`backend/integrations/servicenow/auth.py`)
- **Authentication Modes**:
  1. `basic`: Standard Base64 encoded `username:password`.
  2. `token`: Static Bearer token header.
  3. `oauth2`: Automated OAuth2 token exchange via `/oauth_token.do` with automatic credential grants (`password` or `client_credentials`) and cached token lifecycle management.
- **Safety & Secret Masking**:
  - `mask_secret()` sanitizes credentials in all API responses and logs.
  - Zero plaintext secrets stored in memory dumps or UI status endpoints.

### B. HTTP Client, Rate Limiting & Resiliency (`backend/integrations/servicenow/client.py`, `rate_limit.py`)
- **Rate Limiting**: Configurable token bucket rate limiter bound by `SERVICE_NOW_RATE_LIMIT_RPS`.
- **429 Handling**: Automatically extracts `Retry-After` header and backs off with randomized jitter.
- **Transient Error Classification**: Automatically retries HTTP 408, 500, 502, 503, 504 and network disconnects up to `SERVICE_NOW_MAX_RETRIES` with exponential backoff base (`SERVICE_NOW_BACKOFF_BASE`).
- **Permanent Errors**: Immediately classifies HTTP 400, 401, 403, 404 into domain exceptions (`ServiceNowAuthError`, `ServiceNowNotFoundError`, `ServiceNowPermanentError`).

### C. Normalization & Bidirectional Mappers (`backend/integrations/servicenow/mappings.py`)
- Robust reference field extraction supporting raw string `sys_id`, display string, or nested JSON object `{"link": "...", "value": "..."}`.
- Flexible datetime parser handling UTC `"YYYY-MM-DD HH:MM:SS"` and ISO 8601 timestamps.
- Explicit priority, status, category, criticality, and CAB approval state mapping across:
  - `incident` <-> `Incident`
  - `problem` <-> `Problem`
  - `change_request` <-> `Change`
  - `cmdb_ci_service` <-> `Service`
  - `task_sla` <-> `SLARecord`

### D. Synchronization & Ingestion Engine (`backend/integrations/servicenow/sync.py`)
- **Idempotency**: Lookup by `external_id` (ServiceNow `sys_id`) first, then business identifier. If existing, performs in-place UPDATE; if new, performs INSERT.
- **Incremental Sync**: Queries ServiceNow with `sys_updated_on >= last_successful_sync` to minimize payload sizes and network overhead.
- **Dead-Letter Queue**: Automatically traps malformed payloads into `integration_failures` with attempt counts, payload hashes, and retry endpoints.
- **Audit Logging**: Appends immutable `AuditEvent` records for every batch mutation and writeback.

### E. Inbound Real-Time Webhook Receiver (`backend/integrations/servicenow/webhooks.py`)
- **HMAC-SHA256 Verification**: Validates `X-ServiceNow-Signature` / `X-Hub-Signature-256` against configured `SERVICE_NOW_WEBHOOK_SECRET`.
- **Timestamp Drift Protection**: Rejects payloads with `X-ServiceNow-Timestamp` older than 300 seconds.
- **Replay Protection**: Stores processed `event_id` and `idempotency_key` in `webhook_events`; duplicate events are immediately ignored.

---

## 4. API Endpoints & RBAC Permissions Matrix

| Endpoint | Method | Required Permission | Allowed Roles | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/integrations/servicenow/status` | `GET` | `integration.read` | Viewer, Analyst, Admin | Status, masked config, sync counters, metrics |
| `/api/v1/integrations/servicenow/test-connection` | `POST` | `integration.manage` | Admin | Active connectivity & latency test |
| `/api/v1/integrations/servicenow/sync` | `POST` | `integration.sync` | Analyst, Admin | Full / Incremental sync all entities |
| `/api/v1/integrations/servicenow/sync/{entity}` | `POST` | `integration.sync` | Analyst, Admin | Sync specific ITSM entity |
| `/api/v1/integrations/servicenow/sync-status` | `GET` | `integration.read` | Viewer, Analyst, Admin | Granular sync state per entity |
| `/api/v1/integrations/servicenow/errors` | `GET` | `integration.read` | Viewer, Analyst, Admin | Dead-letter failure queue |
| `/api/v1/integrations/servicenow/errors/{id}/retry` | `POST` | `integration.sync` | Analyst, Admin | Reprocess failed ingestion record |
| `/api/v1/integrations/servicenow/writeback/{entity}/{id}` | `POST` | `integration.writeback` | Admin | Push state updates to ServiceNow |
| `/api/v1/integrations/servicenow/webhook` | `POST` | *Public / HMAC* | All (Validated via HMAC) | Inbound real-time webhook receiver |

---

## 5. Verification & Test Suite

- **Pytest Suite**: **69 / 69 Tests Passed (100%)**
- **ServiceNow Test Coverage**: `tests/backend/test_servicenow_integration.py` (20 Dedicated Integration Tests)
- **E2E Validation**: `scripts/verify_e2e.py` -> `E2E_OK`
- **Frontend Production Build**: `npm run build` -> Clean bundle, zero TypeScript errors.
