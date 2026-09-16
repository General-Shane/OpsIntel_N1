# OPSINTEL — MASTER HANDOVER & CONTINUATION SPECIFICATION

**Document ID:** OPSINTEL-DOC-MASTER-HANDOVER  
**Date:** September 16, 2026  
**Status:** AUTHORITATIVE ACTIVE MASTER HANDOVER  
**Classification:** `READY WITH ENVIRONMENT BLOCKERS`  
**Target Environment:** Enterprise IT Operations Intelligence (Capgemini NOC & Executive Suite)  

---

## 1. Project Overview

**OPSINTEL** (OPSINTEL Enterprise Operations Intelligence) is an enterprise-grade IT Operations Intelligence platform designed to provide:
- Executive operational visibility and health index scoring
- Incident intelligence and MTTR telemetry
- Root Cause Analysis (RCA) and correlated change tracking
- Problem management intelligence, aging buckets, and recurring cluster detection
- Change management governance, velocity tracking, and failure/rollback telemetry
- Service-level agreement (SLA) breach prediction and compliance monitoring
- AI-synthesized operational reporting (Daily, Weekly, Monthly) in Markdown and PDF
- Multi-channel notification delivery (Corporate SMTP/TLS, Slack, Microsoft Teams)
- Distributed durable job scheduling with database lease-locking and retry backoff
- Bi-directional ServiceNow integration (Table API, mappings, webhooks, dead-letter queue, write-back)
- External AI Agent / Beacon Incident Commander integration contracts (Schema v1.0)
- Immutable operational audit logging and enterprise role-based access control (RBAC)

The project is actively transitioning from an executive proof-of-concept (POC) into a hardened, production-grade enterprise system.

---

## 2. Current Architecture

OPSINTEL operates as a decoupled, multi-tier client-server architecture:

```
+-----------------------------------------------------------------------------------+
|                            FRONTEND (React 19 + Vite)                             |
|  - Dual Theme: Capgemini Executive Light & NOC Dark Mode                          |
|  - Dashboards: Overview, Incidents, Problems, Changes, SLAs, Services             |
|  - Governance: Scheduler Management, Notification Center, ServiceNow Integration  |
|  - AI Assistant: AIChatDrawer, Root Cause Analysis, Executive Report Viewer       |
+-----------------------------------------------------------------------------------+
                                         |
                       HTTP / REST & WebSockets (Port 8000)
                                         v
+-----------------------------------------------------------------------------------+
|                             BACKEND (FastAPI API V1)                              |
|  - /api/v1/auth & /admin (RBAC, JWT, Lockout, Token Versioning)                   |
|  - /api/v1/analytics (KPIs, Service Health, MTTR, Aging, Correlations)            |
|  - /api/v1/reports & /notifications (Markdown/PDF synthesis, SMTP, Webhooks)       |
|  - /api/v1/scheduler (Durable Jobs, Concurrency Lease Locks, Retry Engine)        |
|  - /api/v1/integrations/servicenow (Table API, Mappings, Webhooks, DLQ)           |
|  - /api/v1/integrations/beacon (Incident Commander Schema v1.0 Telemetry)         |
|  - /api/v1/ai (Gemini SDK / Deterministic Fallback Engine)                        |
+-----------------------------------------------------------------------------------+
                                         |
                                SQLAlchemy 2.0 ORM
                                         v
+-----------------------------------------------------------------------------------+
|                        DATABASE & PERSISTENCE (Alembic)                           |
|  - Production Target: PostgreSQL 14+ (QueuePool, 20 connections)                  |
|  - Local Dev/Test Target: SQLite with WAL mode, busy_timeout=5000, FKs ON         |
|  - Schema Chain: aa751ab79fa1 -> 28087f9366b3 -> 4784e9b065f8 (HEAD)              |
|  - Tables: 18 Core Tables (Identity, ITSM, Sync, Scheduler, Audit)                |
+-----------------------------------------------------------------------------------+
```

---

## 3. Technology Stack

### Backend
- **Language & Runtime:** Python 3.10+ / 3.12 64-bit
- **Web Framework:** FastAPI (Asynchronous lifespan, Pydantic V2 settings/schemas)
- **ASGI Server:** Uvicorn (`backend.main:app`)
- **ORM & Database:** SQLAlchemy 2.0, Alembic (Linear schema migrations)
- **Security & Crypto:** Passlib (Bcrypt), PyJWT (HS256 with token version invalidation), Cryptography (HMAC-SHA256 webhook signatures)
- **Scheduling:** Custom Distributed `ProductionScheduler` with lease-locking and `croniter`/`pytz` timezone calculations
- **Report & Document Generation:** ReportLab (Two-pass dynamic header/footer `NumberedCanvas` PDF synthesis)
- **AI / LLM Integration:** `google.genai` / `google.generativeai` candidate fallback pipeline with deterministic fallback synthesizers
- **Logging & Telemetry:** `structlog` (JSON structured logging with secret masking, zero raw `print()` statements)

### Frontend
- **Runtime:** Node.js 20.18+
- **Build Tool:** Vite 8 (with `@rolldown/binding-win32-x64-msvc` on Windows)
- **UI Framework:** React 19, TypeScript
- **Styling:** Vanilla CSS design tokens (`frontend/src/index.css`) with Capgemini branding palette and NOC dark mode
- **Visualizations:** Recharts (Area, Bar, Line, Pie, ResponsiveContainer)
- **Icons:** Lucide React
- **HTTP Client:** Axios (Custom interceptor client at `frontend/src/api/client.ts`)

---

## 4. Repository Structure

```
OpsIntel-main/
├── .env                                # Environment variable configuration (Ignored in VCS)
├── alembic.ini                         # Alembic database migration configuration
├── alembic/
│   └── versions/                       # Linear migration chain (Stage 7 -> Stage 8 -> Stage 9)
├── backend/
│   ├── api/v1/
│   │   ├── endpoints/                  # FastAPI REST endpoints
│   │   │   ├── admin.py                # User management & data maintenance
│   │   │   ├── ai.py                   # Chat and RCA endpoints
│   │   │   ├── analytics.py            # KPI, service, incident, problem, change queries
│   │   │   ├── auth.py                 # JWT login, token refresh, password changes
│   │   │   ├── health.py               # Application health and liveness
│   │   │   ├── ingestion.py            # Manual CSV dataset upload
│   │   │   ├── integration.py          # Beacon AI Agent integration (Schema v1.0)
│   │   │   ├── notifications.py        # SMTP configuration & delivery history
│   │   │   ├── reports.py              # Report generation, download, and dispatch
│   │   │   ├── scheduler.py            # Job CRUD, execution history, manual retry/cancel
│   │   │   ├── servicenow.py           # ServiceNow sync, test, errors, writeback, webhooks
│   │   │   └── websockets.py           # Real-time WebSocket incident ticker
│   │   └── router.py                   # Central API v1 router mounting
│   ├── config.py                       # Pydantic Settings with env parsing and secret masking
│   ├── core/
│   │   ├── database.py                 # Engine, SessionLocal, Base, WAL configuration
│   │   ├── errors.py                   # Global exception handlers
│   │   ├── logging.py                  # Structlog JSON formatting and sanitization
│   │   ├── models.py                   # 18 SQLAlchemy 3NF models
│   │   ├── prompts.py                  # AI system prompts and templates
│   │   ├── scheduler.py                # Distributed lease-locking production scheduler
│   │   └── security.py                 # RBAC matrix, bcrypt hashing, JWT issuance
│   ├── integrations/
│   │   └── servicenow/                 # Enterprise ServiceNow Table API connector
│   │       ├── auth.py                 # Basic, Token, OAuth2 exchange and secret masking
│   │       ├── client.py               # Table API HTTP client with rate limiting & backoff
│   │       ├── exceptions.py           # Domain exceptions (Auth, RateLimit, Transient, Permanent)
│   │       ├── mappings.py             # Bi-directional field maps & normalizers
│   │       ├── metrics.py              # Connector telemetry
│   │       ├── rate_limit.py           # Token bucket rate limiter & retry backoff
│   │       ├── sync.py                 # Two-way sync engine with DLQ and audit trail
│   │       └── webhooks.py             # HMAC-SHA256 signature verification & replay filter
│   ├── main.py                         # FastAPI lifespan, CORS, middleware, and startup hooks
│   └── services/
│       ├── ai_service.py               # AI report narrative, RCA, and query assistant
│       ├── analytics_service.py        # ITSM analytics, KPIs, aging buckets, correlations
│       ├── ingestion_service.py        # CSV parsing, validation, and table ingestion
│       ├── notification_service.py     # Multi-channel dispatcher (SMTP, Slack, Teams)
│       ├── pdf_service.py              # ReportLab executive PDF generator
│       ├── reporting_service.py        # 10-section operational report synthesizer
│       └── smtp_service.py             # Enterprise SMTP transport with STARTTLS & MIME
├── docs/                               # Authoritative technical documentation
├── frontend/
│   ├── package.json                    # Frontend dependencies and scripts
│   ├── vite.config.ts                  # Vite build configuration
│   └── src/
│       ├── api/client.ts               # Axios base configuration
│       ├── components/                 # React UI views
│       │   ├── admin/                  # Admin user management & Integrations view
│       │   ├── ai/                     # AI Chat Drawer & RCA modal
│       │   ├── auth/                   # Login view & authentication forms
│       │   ├── changes/                # Change management analytics view
│       │   ├── common/                 # Theme toggle, badges, UI widgets
│       │   ├── dashboard/              # Executive Overview dashboard & health score
│       │   ├── incidents/              # Incident management table & details
│       │   ├── ingestion/              # CSV file upload & validation console
│       │   ├── layout/                 # TopNav, Sidebar, AppLayout
│       │   ├── notifications/          # Notification center & SMTP delivery audit
│       │   ├── problems/               # Problem management intelligence & root cause
│       │   ├── profile/                # User profile & security credentials
│       │   ├── reports/                # Executive Report viewer & PDF exporter
│       │   ├── scheduler/              # Scheduled jobs registry & execution audit
│       │   ├── service/                # Service catalog & health scorecard
│       │   └── sla/                    # SLA performance & breach tracking
│       ├── contexts/                   # AuthContext, ThemeContext, WebSocketContext
│       └── index.css                   # Global Capgemini CSS design system tokens
├── scripts/
│   ├── generate_data.py                # Deterministic synthetic ITSM dataset generator
│   └── verify_e2e.py                   # Automated end-to-end integration validation
└── tests/
    ├── backend/                        # 13 backend test suites (107 tests)
    └── scripts/                        # Dataset generator deterministic tests (1 test)
```

---

## 5. Completed Stages

- **Stage 6: Security & Identity Foundation (`PRODUCTION-READY`)**
  - Persistent User, Role, and Permission relational models.
  - Pre-seeded roles: `ADMIN`, `ANALYST`, `VIEWER`.
  - Bcrypt password hashing (`cost=12`).
  - JWT token issuance with embedded `token_version` for instant session revocation.
  - Brute-force account lockout (5 failed attempts = 15-minute freeze).
  - Admin protection safeguards (cannot delete or revoke last active admin).
  - Beacon API key protection for agent integrations.

- **Stage 7: Enterprise ITSM Relational Data Model (`PRODUCTION-READY`)**
  - 3NF relational schema covering Services, Incidents, Problems, Changes, SLAs, and Audit Events.
  - Foreign key cascades (`ondelete="CASCADE"` for executions, `RESTRICT` for services).
  - Operational indexing on priority, status, timestamps, and foreign keys.
  - Linear Alembic migration `aa751ab79fa1`.
  - Deterministic synthetic data generator (`scripts/generate_data.py`).

- **Stage 8: Live ServiceNow Connector & Ingestion Layer (`VERIFIED MOCK / BLOCKED LIVE`)**
  - Enterprise ServiceNow Table API connector supporting Basic, Token, and OAuth2.
  - Token bucket rate limiter (10 RPS) and exponential backoff retry.
  - HTTP 429 `Retry-After` header extraction and random jitter.
  - Dead-letter queue (`integration_failures`) for unparseable remote records.
  - Inbound webhook receiver with HMAC-SHA256 signature verification and 300s replay drift window.
  - Controlled two-way write-back guarded by `integration.writeback` permission and immutable `AuditEvent` logging.
  - Linear Alembic migration `28087f9366b3`.

- **Stage 9: Production Scheduler & Real SMTP Delivery (`VERIFIED MOCK / BLOCKED LIVE`)**
  - Distributed database lease-locking scheduler on `job_executions` (`lease_expires_at`).
  - Strict concurrency policy (`FORBID` prevents duplicate runs).
  - Automatic stale worker recovery (recovers crashed worker executions to `FAILED`).
  - Approved handler registry whitelist (`APPROVED_JOB_HANDLERS`).
  - Real SMTP transport with STARTTLS (port 587) and SSL (port 465).
  - CRLF and header injection defense on subjects and recipients.
  - Dual-part MIME multipart with binary PDF attachments.
  - Linear Alembic migration `4784e9b065f8` (Head).

- **Stage 9.5: Production Validation & Readiness (`COMPLETE & VERIFIED`)**
  - 21 dedicated failure-injection tests in `test_stage9_5_readiness.py`.
  - 100% backend test pass rate: **108 / 108 tests passed**.
  - Zero unmasked secrets across APIs, logs, and exception handlers.
  - 100% structured logging via `structlog`.

---

## 6. Current Readiness & Environmental Classification

Final Architectural Classification:
# **`READY WITH ENVIRONMENT BLOCKERS`**

The codebase, database schemas, API contracts, frontend interfaces, and mock integration layers are production-tested. External corporate environments are categorized as:
1. **Live ServiceNow Instance:** `ENVIRONMENT-BLOCKED` (Requires corporate ServiceNow tenant URL and credentials).
2. **Corporate SMTP Relay:** `ENVIRONMENT-BLOCKED` (Requires corporate mail relay server and TLS credentials).

---

## 7. Environment Requirements

### Minimum Runtime Requirements
- **Python:** Version 3.10 to 3.12 (64-bit)
- **Node.js:** Version 20.18+ (tested with Vite 8)
- **Operating System:** Windows, Linux (Ubuntu 22.04+), or macOS

### Required Environment Variables (`.env`)
```bash
# General
PROJECT_NAME="OPSINTEL Enterprise Operations Intelligence"
ENVIRONMENT="development" # Set to "production" in prod
SECRET_KEY="<generate_secure_random_64_char_key>"
DATABASE_URL="sqlite:///./opsintel.db" # In production: postgresql://user:pass@host:5432/opsintel

# Default Bootstrap Credentials
OPSINTEL_BOOTSTRAP_ADMIN_USERNAME="admin"
OPSINTEL_BOOTSTRAP_ADMIN_PASSWORD="<strong_admin_password>"
OPSINTEL_BOOTSTRAP_VIEWER_USERNAME="viewer"
OPSINTEL_BOOTSTRAP_VIEWER_PASSWORD="<strong_viewer_password>"
OPSINTEL_BOOTSTRAP_ANALYST_USERNAME="analyst"
OPSINTEL_BOOTSTRAP_ANALYST_PASSWORD="<strong_analyst_password>"

# Beacon Agent Security
BEACON_API_KEY="opsintel-beacon-dev-key-2026"

# ServiceNow Integration (Stage 8)
SERVICE_NOW_INSTANCE_URL="https://devXXXXX.service-now.com"
SERVICE_NOW_AUTH_MODE="basic" # "basic" | "oauth2" | "token"
SERVICE_NOW_USERNAME="admin"
SERVICE_NOW_PASSWORD="<servicenow_password>"
SERVICE_NOW_WEBHOOK_SECRET="<webhook_signing_secret>"
SERVICE_NOW_RATE_LIMIT_RPS=10.0

# SMTP & Notifications (Stage 9)
SMTP_HOST="smtp.company.com"
SMTP_PORT=587
SMTP_USER="notifications@company.com"
SMTP_PASSWORD="<smtp_relay_password>"
SMTP_USE_TLS=True
SMTP_MOCK_MODE=True # Set to False when live corporate relay is reachable

# AI Engine (Optional)
GEMINI_API_KEY="<gemini_api_key>"
```

---

## 8. Database Architecture & Alembic State

- **Current Head:** `4784e9b065f8`
- **Migration History:**
  1. `aa751ab79fa1`: Initial Stage 7 ITSM models (`services`, `problems`, `changes`, `incidents`, `sla_records`, `audit_events`, `users`, `roles`, `permissions`, `user_roles`, `role_permissions`).
  2. `28087f9366b3`: Stage 8 ServiceNow integration models (`integration_configs`, `sync_states`, `integration_failures`, `webhook_events`).
  3. `4784e9b065f8`: Stage 9 Distributed Scheduler and SMTP delivery models (`scheduled_jobs`, `job_executions`, `notification_deliveries`).

---

## 9. Authentication & RBAC

### Roles & Permissions Matrix
| Permission Name | Description | ADMIN | ANALYST | VIEWER |
| :--- | :--- | :---: | :---: | :---: |
| `reports.read` | View generated reports | Yes | Yes | Yes |
| `reports.generate` | Trigger on-demand report synthesis | Yes | Yes | No |
| `reports.download` | Download PDF report binaries | Yes | Yes | Yes |
| `analytics.read` | View dashboards and raw ITSM data | Yes | Yes | Yes |
| `ai.chat` | Query interactive AI operations assistant | Yes | Yes | Yes |
| `ai.rca` | Trigger Root Cause Analysis generation | Yes | Yes | No |
| `ingestion.upload` | Upload CSV dataset batches | Yes | Yes | No |
| `integration.read` | View ServiceNow & Beacon integration status | Yes | Yes | Yes |
| `integration.sync` | Trigger manual ServiceNow synchronization | Yes | Yes | No |
| `integration.manage` | Update integration configuration | Yes | No | No |
| `integration.writeback` | Push local updates back to ServiceNow | Yes | No | No |
| `scheduler.read` | View scheduled jobs and execution history | Yes | Yes | Yes |
| `scheduler.manage` | Register, update, or delete scheduled jobs | Yes | No | No |
| `scheduler.execute` | Manually execute or retry scheduled jobs | Yes | Yes | No |
| `notifications.read` | View notification channels and delivery audit | Yes | Yes | Yes |
| `notifications.manage` | Configure SMTP, Slack, Teams channels | Yes | No | No |
| `admin.users.manage` | User account lifecycle and password reset | Yes | No | No |
| `admin.data.purge` | Purge reports, reset data, clear history | Yes | No | No |

---

## 10. ServiceNow Integration Architecture

- **Connector Location:** `backend/integrations/servicenow/`
- **Authentication Providers:** `BasicAuth`, `TokenAuth`, `OAuth2ClientCredentials` (with token caching and auto-refresh).
- **Rate Limiting:** Token Bucket rate limiter capped at 10 requests/sec with jittered exponential backoff.
- **Bi-directional Synchronization:** Maps `incident`, `problem`, `change_request`, `cmdb_ci_service`, and `task_sla` tables to OPSINTEL entities.
- **Dead-Letter Queue:** Schema anomalies or sync exceptions persist to `integration_failures` for review and retry via `/api/v1/integrations/servicenow/errors/{id}/retry`.
- **Inbound Webhooks:** HMAC-SHA256 signature verification on `X-ServiceNow-Signature` with 300-second timestamp drift tolerance and `idempotency_key` deduplication.
- **Write-back:** Admin-only controlled push to ServiceNow with mandatory `AuditEvent` generation.

---

## 11. Distributed Scheduler Architecture

- **Engine Location:** `backend/core/scheduler.py`
- **Lease Locking:** Database-backed execution leases on `job_executions` (`lease_acquired_at`, `lease_expires_at = now + 300s`, `worker_id`).
- **Concurrency Policies:** `FORBID` (skips duplicate triggers if a job is currently `RUNNING`), `ALLOW` (permits concurrent executions).
- **Approved Handlers Whitelist:**
  - `report.generate`: Triggers `ReportingService.generate_report()`
  - `notification.send`: Dispatches notifications via `NotificationService`
  - `executive.digest`: Compiles executive operational KPIs and dispatches summary
  - `servicenow.sync`: Invokes `ServiceNowSyncEngine.sync_all()`
- **Stale Worker Recovery:** Automatically detects orphaned executions from crashed nodes past lease expiry and marks them `FAILED` (`LeaseTimeoutError`).

---

## 12. Notifications & SMTP Architecture

- **Service Location:** `backend/services/smtp_service.py` & `backend/services/notification_service.py`
- **Transport Security:** STARTTLS on port 587, direct SSL/TLS on port 465.
- **Security Defenses:** Strict CRLF header injection rejection (`\r`, `\n`) on all email fields.
- **Attachments:** Automatic generation and attachment of ReportLab PDF executive briefs.
- **Delivery Audit:** Every dispatch attempt (Email, Slack, Teams) writes to `notification_deliveries` with status (`SENT`, `FAILED`), timestamps, and provider message IDs.
- **Mock Mode:** When `SMTP_MOCK_MODE=True`, messages are recorded in an in-memory queue without attempting live socket connections.

---

## 13. AI Architecture & Grounding State

- **Service Location:** `backend/services/ai_service.py`
- **Model Pipeline:** Tries `google.genai` then `google.generativeai` with fallback candidate models (`gemini-3.5-flash`, `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`).
- **Deterministic Synthesis:** When no API key is present or quota is exceeded, generates structured, metric-accurate Markdown reports and executive summaries based on actual database KPIs.
- **Normalizer:** `normalize_ops_narrative()` strips conversational AI filler, robotic preambles, and em-dash clutter.
- **Current Limitation / Future Work:**
  - AI responses do NOT yet cite exact operational record IDs (e.g. `INC10402`, `PRB001004`) with verifiable data timestamps.
  - No persistent database-backed AI conversation memory or user session retention table exists.

---

## 14. Beacon / Multi-Agent Integration Architecture

- **Endpoints:** `backend/api/v1/endpoints/integration.py` (`/api/v1/integration/beacon/v1/...`)
- **Authentication:** `verify_beacon_api_key` checks `X-API-Key` header against `settings.BEACON_API_KEY`.
- **Contract Version:** Schema v1.0 machine-readable JSON contracts:
  - `/health-context`: Global operational health index, SLA compliance, and MTTR telemetry.
  - `/active-incidents`: Active P1/P2/P3 incidents enriched with correlated change IDs (<24h deployment window).
  - `/incident-context/{id}`: Detailed triage dossier with correlated changes, active problem IDs, and diagnostic vectors.
  - `/problem-intelligence`: Backlog aging distribution, root cause breakdown, and recurring incident clusters.
  - `/service-health`: Fleet health breakdown per enterprise service.
  - `/executive-brief`: Executive summary narrative with risk factor bullets.
- **Current Limitation / Future Work:**
  - Read-only queries only. No mutating action execution (e.g., automated rollback, incident reassignment, problem creation).
  - No granular agent identity or audit event persistence for Beacon API queries.

---

## 15. Frontend Architecture & Design Language

- **Design System:** Authoritative Capgemini corporate theme specified in `docs/OPSINTEL_CAPGEMINI_DESIGN_SYSTEM.md` and implemented in `frontend/src/index.css`.
- **Themes Supported:** Capgemini Light, NOC Dark, and System Auto.
- **Primary Views:**
  - `DashboardView.tsx`: Global health score, KPI cards, real-time incident ticker, 14-day trends.
  - `IncidentsView.tsx`: Incident registry, search, priority filters, CSV export.
  - `ProblemsView.tsx`: Problem management intelligence, 4-tier aging bar chart, root cause breakdown, detail drawer.
  - `ChangesView.tsx`: Change velocity, type breakdown pie chart, risk indicator badges.
  - `SLAView.tsx`: SLA compliance rate, breached contract table, countdown timers.
  - `ServiceCatalogView.tsx`: Fleet scorecard, service criticality, health badges.
  - `SchedulerView.tsx`: Scheduled jobs table, create job modal, pause/resume, execution audit logs.
  - `NotificationsView.tsx`: Channel configuration, masked SMTP status, delivery history log.
  - `IntegrationsView.tsx`: ServiceNow sync controls, entity sync stats, dead-letter failure queue with retry.
  - `AdminView.tsx`: Persistent user account management, password reset, token revocation, data reseed/wipe.
  - `ExecutiveReportView.tsx`: Generated Markdown reports viewer with PDF download link.

---

## 16. Formal Use-Case Traceability & Current Status

| Requirement / Use Case | Description | Frontend | Backend API | Database | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **R1 / R2 / R3 / R4** | Automated Daily/Weekly/Monthly Reporting | `ExecutiveReportView` | `/api/v1/reports/*` | `reports/` storage | **COMPLETE** |
| **R5 / R6 / R7 / R8 / R9** | Operational Metrics (Incidents, Problems, Changes, SLAs, Services) | `DashboardView`, `IncidentsView`, etc. | `/api/v1/analytics/*` | `incidents`, `problems`, `changes`, `sla_records` | **COMPLETE** |
| **R10 / R11** | Consolidation & Executive Reports | `ExecutiveReportView` | `/api/v1/reports/*`, `pdf_service.py` | Local filesystem | **COMPLETE** |
| **R15** | Interactive Operations Dashboard | `DashboardView.tsx` | `/api/v1/analytics/kpis` | SQLite / PostgreSQL | **COMPLETE** |
| **R16 / R17** | Manual CSV Data Upload & Processing | `DataUploadView.tsx` | `/api/v1/ingestion/upload` | `ingestion_jobs` | **COMPLETE** |
| **R18 / R19** | AI Operational Assistant & RCA | `AIChatDrawer.tsx`, RCA Modal | `/api/v1/ai/chat`, `/api/v1/ai/rca` | Ephemeral (Prompt) | **PARTIAL** (No DB memory) |
| **R20** | Distributed Production Scheduler | `SchedulerView.tsx` | `/api/v1/scheduler/*` | `scheduled_jobs`, `job_executions` | **COMPLETE** |
| **R21 / R22** | Slack & Teams Notifications | `NotificationsView.tsx` | `/api/v1/reports/dispatch` | `notification_deliveries` | **COMPLETE** |
| **R23** | ServiceNow Connector & Ingestion | `IntegrationsView.tsx` | `/api/v1/integrations/servicenow/*` | `integration_configs`, `sync_states`, `integration_failures` | **VERIFIED MOCK / BLOCKED LIVE** |
| **R24** | Synthetic Deterministic Data Generation | `AdminView.tsx` (Reseed) | `/api/v1/admin/reseed-data` | `scripts/generate_data.py` | **COMPLETE** |
| **R28** | End-to-End Automation Pipeline | CLI Runner | `scripts/verify_e2e.py` | SQLite / PostgreSQL | **COMPLETE** |
| **ITSM Mutation: Incident Lifecycle** | Create, assign, escalate, resolve incidents | None | None | `incidents` (Read-only via API) | **MISSING** |
| **ITSM Mutation: Problem Lifecycle** | Create, investigate, publish workaround/KEDB, resolve | None (Read-only drawer) | None | `problems` (Read-only via API) | **MISSING** |
| **ITSM Mutation: Change Lifecycle** | Submit change, CAB approval, deploy gate, rollback | None | None | `changes` (Read-only via API) | **MISSING** |

---

## 17. Known Gaps

1. **Interactive ITSM Lifecycle Mutations:**
   - There are currently no REST APIs or UI forms for creating or updating Incidents, Problems, and Changes. Operational records can only enter the system via synthetic generation, CSV upload, or ServiceNow sync.
2. **AI Persistent Memory:**
   - Conversation history is maintained solely in the frontend React state. It is not persisted in a database table (`ai_conversations` or `chat_messages`), meaning conversations are lost upon browser refresh.
3. **AI Evidence Grounding & Auditability:**
   - The AI Assistant currently cites static source labels (`"Incidents DB"`, `"SLA Engine"`). It does not provide verifiable record-level citations, timestamps, or confidence metrics.
4. **Beacon Agent Action Gating:**
   - Beacon integration contracts are strictly read-only telemetry queries. There is no authenticated action execution interface for agents to perform operational interventions.
5. **High-Volume UX Pagination:**
   - Tables in `ChangesView` and `IncidentsView` slice a static number of records (e.g. 50 or 250 records). Server-side pagination, sorting, and date-range filtering are needed for large production datasets.

---

## 18. Known Environment Blockers

1. **Live ServiceNow Tenant (`LIVE_SERVICENOW_VALIDATION = BLOCKED_BY_ENVIRONMENT`):**
   - Requires live corporate ServiceNow instance URL, OAuth client ID/secret or basic auth credentials. Architecture and mock connector tests are 100% verified.
2. **Live Corporate SMTP Relay (`LIVE_SMTP_VALIDATION = BLOCKED_BY_ENVIRONMENT`):**
   - Requires an authenticated corporate SMTP relay endpoint. In-memory mock transport mode and socket exception handling are 100% verified.

---

## 19. Test Status & Verification Baseline

- **Total Backend Tests:** **108 / 108 Passed (100%)**
  - `test_admin_and_pdf.py`: 4 tests passed
  - `test_ai_layer.py`: 2 tests passed
  - `test_analytics.py`: 5 tests passed
  - `test_auth_and_rbac.py`: 14 tests passed
  - `test_health.py`: 2 tests passed
  - `test_ingestion.py`: 1 test passed
  - `test_integration.py`: 6 tests passed (Beacon Schema v1.0)
  - `test_notifications.py`: 1 test passed
  - `test_reporting.py`: 1 test passed
  - `test_scheduler_and_smtp.py`: 18 tests passed
  - `test_servicenow_integration.py`: 20 tests passed
  - `test_stage7_models.py`: 12 tests passed
  - `test_stage9_5_readiness.py`: 21 tests passed
  - `test_generator.py`: 1 test passed (Deterministic repeatability)
- **Frontend Production Build:** Clean build via `npm run build` with zero TypeScript or syntax errors.
- **Alembic Migration Integrity:** Verified at Head `4784e9b065f8`.

---

## 20. Deployment Instructions

### Production Deployment (Linux / Docker / Kubernetes)
```bash
# 1. Clone repository
git clone <repository_url>
cd OpsIntel-main

# 2. Configure environment
cp .env.example .env
# Edit .env with production SECRET_KEY, DATABASE_URL, ServiceNow, and SMTP credentials

# 3. Setup Python Virtual Environment
python3.12 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r requirements.txt

# 4. Run Database Migrations to Head
alembic upgrade head

# 5. Bootstrap Admin Identity & Security Roles
python -c "from backend.core.database import SessionLocal; from backend.core.security import bootstrap_security; db=SessionLocal(); bootstrap_security(db); db.close()"

# 6. Build Frontend Bundle
cd frontend
npm ci
npm run build
cd ..

# 7. Start Production Backend API & Scheduler Workers
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 21. Operational Runbook

| Scenario | Symptom | Action |
| :--- | :--- | :--- |
| **Scheduler Lease Timeout** | Job marked as `RUNNING` past lease expiry. | Scheduler automatically recovers stale lease to `FAILED` after 300s. To manually force recovery, call `/api/v1/scheduler/executions/{id}/cancel`. |
| **ServiceNow Rate Limiting (429)** | High sync concurrency triggers rate limits. | The connector automatically parses `Retry-After` and applies exponential backoff with jitter. If persistent, reduce `SERVICE_NOW_RATE_LIMIT_RPS` in `.env`. |
| **ServiceNow Sync Failure in DLQ** | Record schema mismatch. | View failure details via `GET /api/v1/integrations/servicenow/errors`. Update mapping if needed, then trigger `POST /api/v1/integrations/servicenow/errors/{id}/retry`. |
| **Account Lockout** | User locked out after 5 bad passwords. | Admin unlocks account via `PUT /api/v1/admin/users/{id}` or user waits 15 minutes for automatic expiration. |
| **Session Revocation** | Security incident requiring user logout. | Admin calls `POST /api/v1/admin/users/{id}/revoke-tokens` to increment `token_version`, invalidating all active JWTs for that user. |

---

## 22. Security Considerations

- **Secret Masking:** Structlog and status endpoints strictly mask all passwords, tokens, client secrets, and webhooks. Never expose unmasked secrets.
- **Webhook Authenticity:** ServiceNow inbound webhooks require HMAC-SHA256 signature verification. Requests with timestamp drift >300s or invalid signatures are rejected with HTTP 400.
- **Arbitrary Code Execution Defense:** Scheduler handler keys are validated against `APPROVED_JOB_HANDLERS`. Arbitrary handler strings are rejected with `UnregisteredHandlerError`.
- **CRLF Injection Defense:** Outbound email subjects and recipients are sanitized to prevent SMTP header injection attacks.

---

## 23. Recommended Next Implementation Step

According to the development order specified in Section 21 of the project continuation instructions:
1. **Step 1 (Repository Audit):** Completed and verified.
2. **Step 2 (Master Handover Document):** Completed (`docs/OPSINTEL_MASTER_HANDOVER.md`).
3. **Step 3 (Next Action):** Formal **Use-Case Traceability Audit** & implementation of **Remaining Incomplete Business Workflows**:
   - Problem Management interactive lifecycle (Creation, State transitions, Assignment, Resolution, Audit trail).
   - Change Management interactive lifecycle (CAB workflow, Risk evaluation, Approval, Rollback tracking).
   - Evidence-grounded AI responses with operational data citations and persistent session memory.

---

## 24. Rules for Future AI Agents

1. **Verify Before Changing:** Do not assume a feature exists because of UI mockups or docs. Verify actual backend endpoints, database tables, and tests.
2. **Preserve Existing Contracts:** Never break existing `/api/v1/analytics/*` or `/api/v1/integration/beacon/v1/*` contracts.
3. **Zero Secret Leakage:** Never hardcode secrets, passwords, or tokens. Always use `mask_secret()` for status APIs and structlog processors for logging.
4. **Linear Migrations:** Every database modification must use an Alembic migration chained to the current head (`4784e9b065f8`).
5. **Always Run Tests:** Before declaring any task complete, run the full backend pytest suite and the frontend production build.
