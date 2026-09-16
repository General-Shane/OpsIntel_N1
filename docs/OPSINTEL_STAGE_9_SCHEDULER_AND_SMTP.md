# OPSINTEL — Stage 9 Architecture & Implementation Report
## Production Scheduler & Real SMTP Delivery

**Status:** COMPLETE & VERIFIED  
**Stage:** Stage 9 — Production Scheduler & Real SMTP Delivery  
**Authority:** Chief Architect Directive  
**Date:** August 2026  
**Test Suite:** 86 / 86 Backend Tests Passing (100%)  
**E2E Suite:** Automated Verification Script Verified (`status=SUCCESS`, `E2E_OK`)  
**Frontend Bundle:** Compiled & Built (`tsc -b && vite build` — 0 errors)

---

## 1. Executive Summary

Stage 9 transforms OPSINTEL from an in-process background thread scheduler and local file-only report delivery mechanism into a distributed, database-backed **Production Scheduler** and a secure **Enterprise SMTP/TLS Delivery Subsystem**.

All operational scheduled jobs now persist in the database, survive application restarts, operate under distributed lease-based concurrency locking across multi-worker environments, support bounded exponential backoff retries, and execute only registered, security-approved job handlers.

The notification infrastructure now delivers rich MIME multipart emails (Capgemini-styled HTML + clean plain-text fallback) with direct PDF report attachments via authenticated STARTTLS/SSL SMTP transports, guarded by strict CRLF/header injection sanitization and zero credential exposure.

---

## 2. Production Scheduler Architecture

### 2.1 Database Models & Schema
Persisted relational schema generated via Alembic migration `4784e9b065f8_stage9_production_scheduler_and_smtp_.py`:

- **`scheduled_jobs`**:
  - `id` (UUID PK): Unique identifier.
  - `name`, `description`: Job naming and operator documentation.
  - `job_type`: Handler key restricted to approved whitelist (`report.generate`, `notification.send`, `executive.digest`, `servicenow.sync`).
  - `status`: `ACTIVE`, `PAUSED`, `DISABLED`, `ERROR`.
  - `cron_expression`, `timezone`: APScheduler cron evaluation supporting standard 5-field cron syntax and IANA timezones (e.g. `America/New_York`, `UTC`, `Europe/Paris`, `Asia/Kolkata`).
  - `payload_json`: Strict JSON configuration payload (no executable Python bytecode or pickled objects).
  - `next_run_at`, `last_run_at`, `last_success_at`, `last_failure_at`: Deterministic timing telemetry.
  - `max_retries`, `retry_delay_seconds`, `max_retry_delay_seconds`: Bounded retry parameters.
  - `concurrency_policy`: `FORBID` (default), `ALLOW`, `REPLACE`.
  - `timeout_seconds`: Execution timeout boundary.

- **`job_executions`**:
  - `id` (UUID PK): Execution audit row.
  - `job_id`: Foreign key reference to `scheduled_jobs.id` with `CASCADE` on delete.
  - `run_id`: Human-readable identifier (e.g. `EXEC_A020292D5C05`).
  - `worker_id`: Worker pod / thread identifier.
  - `status`: `QUEUED`, `RUNNING`, `SUCCEEDED`, `RETRYING`, `FAILED`, `CANCELLED`, `SKIPPED`.
  - `attempt_number`: Current attempt index.
  - `lease_acquired_at`, `lease_expires_at`: Distributed lease locking fields.
  - `started_at`, `finished_at`: Execution duration tracking.
  - `next_retry_at`: Scheduled retry timestamp.
  - `error_class`, `error_message`: Full diagnostic failure context.
  - `result_json`: Execution output metadata.
  - `correlation_id`: Distributed tracing identifier.

### 2.2 Concurrency, Distributed Lease Locks & Stale Worker Recovery
- **Lease Acquisition**: When a worker attempts to execute a job with `concurrency_policy="FORBID"`, it queries for active executions with `status == "RUNNING"` and `lease_expires_at > now`. If an active lease exists, concurrent execution is blocked.
- **Stale Worker Recovery**: If a worker node crashes mid-execution, its lease expires (`lease_expires_at < now`). The dispatcher automatically detects expired running jobs on each polling cycle, marks the orphaned execution as `FAILED` with `error_class="LeaseTimeoutError"`, and releases the job for subsequent execution or retry.

### 2.3 Approved Job Handlers Registry
To prevent arbitrary code execution vulnerabilities, scheduled jobs can only invoke statically registered, type-checked handlers:
1. `report.generate`: Executes `ReportingService.generate_report()` to generate Markdown + Executive PDF, automatically triggering email and webhook dispatch.
2. `notification.send`: Dispatches direct notification payloads across configured channels.
3. `executive.digest`: Generates AI-augmented executive summaries and alerts leadership.
4. `servicenow.sync`: Triggers bi-directional synchronization across Incidents, Problems, Changes, and SLAs.

### 2.4 Bounded Exponential Backoff Retry Engine
- Transient errors calculate `delay = min(retry_delay_seconds * (2 ** (attempt - 1)), max_retry_delay_seconds)`.
- The execution is marked `RETRYING` with `next_retry_at = now + delay`.
- The dispatcher evaluates pending retries on each poll loop, executing retries once `next_retry_at <= now`.
- If `attempt_number > max_retries`, the execution is transitioned to `FAILED`.

---

## 3. Real SMTP & Notification Subsystem

### 3.1 Transport & Security Architecture
- Built [`backend/services/smtp_service.py`](file:///c:/Users/karti/Projects/OpsIntel-main/OpsIntel-main/backend/services/smtp_service.py) supporting:
  - STARTTLS on port 587 or implicit SSL on port 465.
  - Secure credential authentication via environment variables (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_FROM_NAME`).
  - Timeout enforcement (`SMTP_TIMEOUT_SECONDS = 30`).
  - Mock transport mode (`SMTP_MOCK_MODE=true` or missing credentials) for hermetic local testing and offline CI/CD.

### 3.2 CRLF & Header Injection Defense
- Strict regex and RFC-compliant validation:
  ```python
  if any(c in email for c in ['\r', '\n', '\0']):
      raise ValueError(f"Header injection attempt detected in email address: '{email}'")
  ```
- Normalizes and sanitizes display names, subject lines, and recipient lists before MIME header generation.

### 3.3 Executive MIME Multipart & PDF Attachment
- Automatically constructs `multipart/mixed` envelopes with:
  - `multipart/alternative` body containing clean plain text and Capgemini-styled HTML (`#06243D` navy headers, `#0070AD` accent colors, executive KPI cards).
  - `application/pdf` binary attachment (`Content-Disposition: attachment; filename="ops_report_daily_*.pdf"`).

### 3.4 Persistent Notification Delivery Audit Log
- Persisted to `notification_deliveries` table:
  - Tracks `id`, `execution_id`, `job_id`, `channel` (`EMAIL`, `SLACK`, `TEAMS`), `recipient`, `subject`, `status` (`PENDING`, `SENT`, `FAILED`, `SKIPPED`), `provider_message_id`, `attempt_count`, `sent_at`, `error_message`.
  - Audits both scheduled report deliveries and manual/test dispatches.

---

## 4. API Endpoints

### 4.1 Production Scheduler Router (`/api/v1/scheduler`)
- `GET /status`: Returns dispatcher state, active worker ID, uptime, total jobs, active jobs, and execution counters.
- `GET /jobs`: Lists all registered scheduled jobs with run history.
- `POST /jobs`: Registers a new scheduled job (requires `scheduler.manage`).
- `GET /jobs/{job_id}`: Returns details of a single scheduled job.
- `PUT /jobs/{job_id}`: Updates configuration, cron schedule, or payload.
- `DELETE /jobs/{job_id}`: Removes job and cascades deletions cleanly.
- `POST /jobs/{job_id}/pause`: Pauses active job.
- `POST /jobs/{job_id}/resume`: Resumes paused job.
- `POST /jobs/{job_id}/execute`: Triggers immediate ad-hoc execution (requires `scheduler.execute`).
- `GET /executions`: Queries execution history with filtering by `job_id`, `status`, and pagination (requires `scheduler.history`).
- `POST /executions/{execution_id}/retry`: Manually re-queues a failed execution.
- `POST /executions/{execution_id}/cancel`: Cancels an active or queued execution.
- `GET /history`: Backward-compatible legacy history endpoint.
- `POST /trigger`: Backward-compatible legacy report trigger endpoint.

### 4.2 Notification Router (`/api/v1/notifications`)
- `GET /email/status`: Returns masked SMTP configuration (host masked, username masked, credentials never exposed).
- `POST /email/test`: Dispatches a real or mock test email to verify transport (requires `notifications.manage`).
- `GET /deliveries`: Queries outbound delivery audit records (requires `notifications.read`).
- `POST /send`: Dispatches cross-channel alerts (Email, Slack, Teams).
- `GET /config/slack`, `POST /config/slack`: Slack webhook configuration.
- `GET /config/teams`, `POST /config/teams`: Teams webhook configuration.

---

## 5. Security & RBAC Controls

Granular permissions configured in `backend/core/security.py`:
- `scheduler.read`: Granted to `ADMIN`, `ANALYST`, `VIEWER`.
- `scheduler.history`: Granted to `ADMIN`, `ANALYST`.
- `scheduler.execute`: Granted to `ADMIN`, `ANALYST`.
- `scheduler.manage`: Granted to `ADMIN` only.
- `notifications.read`: Granted to `ADMIN`, `ANALYST`, `VIEWER`.
- `notifications.manage`: Granted to `ADMIN` only.

---

## 6. Frontend Enterprise Interface

### 6.1 Production Scheduler Console (`/scheduler`)
- Dual-theme support (Light & NOC Dark Mode).
- **Dispatcher Status Scorecards**: Total Jobs, Active Jobs, 24h Executions, Success Rate.
- **Job Inventory Table**: Job name, handler type badge, cron trigger, timezone, next run countdown, last run status, inline Action menu (Trigger, Pause/Resume, Delete).
- **Register Job Modal**: Job name, handler selector, cron expression validator, IANA timezone selector, max retries, concurrency policy.
- **Execution Log Table**: Run ID, job name, worker ID, attempt count, duration, timestamp, status badge, and one-click Retry action for failed executions.

### 6.2 Delivery & SMTP Center (`/notifications`)
- **Delivery Channels Matrix**: SMTP Email, Slack Incoming Webhooks, Microsoft Teams Connectors.
- **Masked SMTP Diagnostics Card**: Server Host (`s***.internal.corp`), Port, TLS/SSL state, Default From address, transport status.
- **Test Email Dispatch Utility**: Recipient address, subject, message input, live dispatch feedback.
- **Outbound Delivery Audit Stream**: Real-time log of all dispatched emails and webhooks with recipient, status badge, timestamp, and provider error diagnostics.

---

## 7. Verification & Test Evidence

### 7.1 Backend Test Suite Results
Ran full test suite `pytest -v tests/backend/`:
- `tests/backend/test_scheduler_and_smtp.py`: 18/18 PASSED (100%)
- `tests/backend/test_servicenow_integration.py`: 16/16 PASSED (100%)
- `tests/backend/test_stage7_models.py`: 12/12 PASSED (100%)
- `tests/backend/test_auth_and_rbac.py`: 12/12 PASSED (100%)
- `tests/backend/test_analytics.py`: 6/6 PASSED (100%)
- `tests/backend/test_admin_and_pdf.py`: 4/4 PASSED (100%)
- `tests/backend/test_integration.py`: 6/6 PASSED (100%)
- `tests/backend/test_ai_layer.py`: 2/2 PASSED (100%)
- `tests/backend/test_health.py`: 2/2 PASSED (100%)
- `tests/backend/test_notifications.py`: 1/1 PASSED (100%)
- `tests/backend/test_reporting.py`: 1/1 PASSED (100%)
- `tests/backend/test_ingestion.py`: 1/1 PASSED (100%)
- **Total: 86 / 86 PASSED (100%)**

### 7.2 End-to-End Verification (`scripts/verify_e2e.py`)
- Database reset and synthetic data generation: 25,500 incidents, 2,900 problems, 5,003 changes, 11,400 SLAs.
- Database authentication and RBAC verified (`admin` login, `/auth/me`, `/admin/users`).
- Beacon contract verified (`schema_version: "1.0"`).
- ServiceNow integration verified (`/integrations/servicenow/status`).
- Scheduler status verified (`total_jobs: 4`, worker active).
- Ad-hoc job execution triggered (`run_id: EXEC_A020292D5C05`, status: `TRIGGERED`).
- Execution history recorded (`executions_count >= 1`).
- SMTP status queried (`host_masked` verified, secrets protected).
- Test email dispatched via SMTP mock transport.
- Delivery audit stream queried (`deliveries_count >= 1`).
- Result: `status="SUCCESS"`, `E2E_OK`.

### 7.3 Frontend Production Build
- Ran `tsc -b && vite build` in `frontend/`.
- 2,456 modules transformed, assets bundled to `dist/assets/index-*.js` and `dist/assets/index-*.css`.
- Result: 0 TypeScript errors, 0 compilation errors.
