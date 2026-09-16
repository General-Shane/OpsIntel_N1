# OPSINTEL --- BACKEND, API & INTEGRATION SPECIFICATION

**Document ID:** OPSINTEL-BACKEND-005\
**Version:** 1.0\
**Status:** Authoritative Backend & Integration Specification\
**Parent:** `01_MASTER_ARCHITECTURE_AND_PRODUCT_BLUEPRINT.md`\
**Functional Parent:** `02_FUNCTIONAL_REQUIREMENTS_AND_WORKFLOWS.md`\
**Data Parent:** `04_DATA_INGESTION_ANALYTICS_AND_KPI_SPECIFICATION.md`

------------------------------------------------------------------------

# 1. PURPOSE

This document defines how the OPSINTEL backend must be structured and
how the frontend, analytics engine, AI layer, reporting engine,
scheduler, notification providers, and future ITSM connectors
communicate.

It is intentionally explicit.

The implementation agent must not invent a different backend
architecture merely because another structure is easier to generate.

------------------------------------------------------------------------

# 2. BACKEND RESPONSIBILITY

The backend is the authoritative application layer for:

-   ingestion;
-   validation;
-   normalization;
-   persistence;
-   analytics;
-   AI orchestration;
-   report generation;
-   scheduling;
-   notifications;
-   configuration;
-   system health.

The frontend must never access the database directly.

------------------------------------------------------------------------

# 3. TECHNOLOGY

V1:

``` text
Python
FastAPI
Pydantic
SQLAlchemy
SQLite
Pandas
NumPy
APScheduler
```

Optional:

``` text
httpx
openpyxl
python-multipart
```

For PDF generation use a maintainable server-side renderer such as:

``` text
WeasyPrint
```

or another approved HTML-to-PDF solution.

The exact library may be selected during implementation if documented in
`DECISIONS.md`.

------------------------------------------------------------------------

# 4. PACKAGE STRUCTURE

Recommended:

``` text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── ingestion.py
│   │   │   ├── dashboard.py
│   │   │   ├── incidents.py
│   │   │   ├── problems.py
│   │   │   ├── changes.py
│   │   │   ├── services.py
│   │   │   ├── insights.py
│   │   │   ├── assistant.py
│   │   │   ├── reports.py
│   │   │   ├── scheduler.py
│   │   │   ├── notifications.py
│   │   │   ├── data_sources.py
│   │   │   └── settings.py
│   │   └── dependencies.py
│   │
│   ├── schemas/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   │   ├── ingestion/
│   │   ├── analytics/
│   │   ├── ai/
│   │   ├── reporting/
│   │   ├── scheduling/
│   │   └── notifications/
│   │
│   ├── analytics/
│   ├── integrations/
│   │   ├── teams.py
│   │   ├── slack.py
│   │   ├── servicenow.py
│   │   └── base.py
│   │
│   ├── database/
│   └── utils/
│
├── tests/
└── requirements.txt
```

The implementation may refine the exact folder names, but
responsibilities must remain separated.

------------------------------------------------------------------------

# 5. LAYERING

Use this logical flow:

``` text
HTTP Route
    ↓
Request Schema
    ↓
Application Service
    ↓
Domain/Analytics Logic
    ↓
Repository
    ↓
Database
```

For integrations:

``` text
Application Service
    ↓
Provider Interface
    ↓
Provider Implementation
```

Do not put business logic directly into route handlers.

------------------------------------------------------------------------

# 6. ROUTE RESPONSIBILITY

Routes should:

-   receive HTTP requests;
-   validate input;
-   call services;
-   return response schemas;
-   translate known application exceptions.

Routes should NOT:

-   calculate MTTR;
-   calculate OHI;
-   build SQL-heavy business logic;
-   call LLMs directly;
-   send Teams messages directly;
-   contain report-generation algorithms.

------------------------------------------------------------------------

# 7. CONFIGURATION

Use environment variables.

Required structure:

``` text
APP_ENV
APP_NAME
APP_VERSION

DATABASE_URL

AI_PROVIDER
AI_MODEL
AI_API_KEY

TEAMS_WEBHOOK_URL
SLACK_WEBHOOK_URL

TIMEZONE

UPLOAD_MAX_MB
UPLOAD_DIRECTORY
REPORT_DIRECTORY

LOG_LEVEL
```

Provide:

``` text
.env.example
```

Never commit:

``` text
.env
```

------------------------------------------------------------------------

# 8. CONFIGURATION VALIDATION

At application startup:

1.  load configuration;
2.  validate required values;
3.  determine optional provider availability;
4.  expose non-secret system status.

Example:

``` text
Database: READY
AI: NOT CONFIGURED
Teams: NOT CONFIGURED
Slack: READY
Scheduler: READY
```

Never expose secret values.

------------------------------------------------------------------------

# 9. DATABASE

V1:

``` text
SQLite
```

Use SQLAlchemy or equivalent repository abstraction.

Database URL must be configurable.

Future:

``` text
PostgreSQL
```

No frontend code should depend on SQLite-specific behavior.

------------------------------------------------------------------------

# 10. CORE MODELS

Minimum models:

``` text
Incident
Problem
Change
Service
SLARecord

IngestionJob
DatasetVersion
Report
ReportExecution
Schedule
NotificationExecution
AIInsight
```

------------------------------------------------------------------------

# 11. INGESTION API

## POST `/api/v1/ingestion/upload`

Purpose:

Upload one or more files.

Request:

``` text
multipart/form-data
files[]
```

Response:

``` json
{
  "job_id": "JOB-001",
  "status": "UPLOADED",
  "files": [
    {
      "filename": "incidents.csv",
      "detected_type": "INCIDENT",
      "confidence": 0.96
    }
  ]
}
```

------------------------------------------------------------------------

# 12. INGESTION VALIDATION API

## POST `/api/v1/ingestion/{job_id}/validate`

Purpose:

Validate and classify uploaded data.

Response should contain:

``` text
job status
dataset classifications
column mappings
quality summary
warnings
errors
```

------------------------------------------------------------------------

# 13. COLUMN MAPPING API

## POST `/api/v1/ingestion/{job_id}/mapping`

Request concept:

``` json
{
  "mappings": [
    {
      "source_column": "Incident Number",
      "canonical_field": "incident_id"
    }
  ]
}
```

Response:

``` text
mapping status
validation result
```

------------------------------------------------------------------------

# 14. PROCESS API

## POST `/api/v1/ingestion/{job_id}/process`

Purpose:

Process validated datasets.

Expected sequence:

``` text
normalize
→ deduplicate
→ relationship validation
→ persistence
→ dataset version
→ analytics refresh
→ AI insight refresh
```

Response:

``` json
{
  "job_id": "JOB-001",
  "status": "COMPLETED",
  "dataset_version": "DATASET-001"
}
```

------------------------------------------------------------------------

# 15. INGESTION STATUS API

## GET `/api/v1/ingestion/{job_id}`

Returns:

``` text
job
status
current_stage
progress if measurable
file results
row counts
warnings
errors
dataset version
```

------------------------------------------------------------------------

# 16. INGESTION HISTORY API

## GET `/api/v1/ingestion/jobs`

Query:

``` text
page
page_size
status
date_from
date_to
```

Returns paginated jobs.

------------------------------------------------------------------------

# 17. DASHBOARD API

## GET `/api/v1/dashboard/overview`

Query:

``` text
period_start
period_end
service_ids
priorities
statuses
criticalities
```

Returns:

``` text
OHI
KPI cards
trends
service health
risk matrix data
incident heatmap data
top insights
automation status
last refresh
```

------------------------------------------------------------------------

# 18. DASHBOARD RESPONSE PRINCIPLE

Return data optimized for visualization.

Do not force the frontend to calculate:

``` text
delta
trend
OHI
risk
```

The backend should provide these.

------------------------------------------------------------------------

# 19. INCIDENT API

## GET `/api/v1/incidents`

Parameters:

``` text
page
page_size
search
service_id
priority
status
date_from
date_to
sort_by
sort_order
```

------------------------------------------------------------------------

# 20. INCIDENT DETAIL API

## GET `/api/v1/incidents/{incident_id}`

Return:

``` text
incident
related problem
related change
service
SLA
```

------------------------------------------------------------------------

# 21. INCIDENT SUMMARY API

## GET `/api/v1/incidents/summary`

Return:

``` text
total
open
resolved
P1
P2
MTTR
SLA
reopen rate
trend
```

------------------------------------------------------------------------

# 22. PROBLEM API

## GET `/api/v1/problems`

Filters:

``` text
search
service_id
priority
status
age_bucket
```

------------------------------------------------------------------------

# 23. PROBLEM DETAIL API

## GET `/api/v1/problems/{problem_id}`

Return:

``` text
problem
related incidents
related changes
service
aging
```

------------------------------------------------------------------------

# 24. PROBLEM SUMMARY API

## GET `/api/v1/problems/summary`

Return:

``` text
total
open
resolved
backlog
average age
oldest
recurring
trend
```

------------------------------------------------------------------------

# 25. CHANGE API

## GET `/api/v1/changes`

Filters:

``` text
search
service_id
status
risk
change_type
date_from
date_to
```

------------------------------------------------------------------------

# 26. CHANGE DETAIL API

## GET `/api/v1/changes/{change_id}`

Return:

``` text
change
service
associated incidents
associated problems
correlation information
```

------------------------------------------------------------------------

# 27. CHANGE SUMMARY API

## GET `/api/v1/changes/summary`

Return:

``` text
total
successful
failed
success rate
rollback rate
emergency rate
associated incidents
trend
```

------------------------------------------------------------------------

# 28. SERVICE API

## GET `/api/v1/services`

Filters:

``` text
search
criticality
health_status
sort
```

Return:

``` text
service health summary
```

------------------------------------------------------------------------

# 29. SERVICE DETAIL API

## GET `/api/v1/services/{service_id}`

Return:

``` text
service
health
availability
SLA
incidents
problems
changes
trends
insights
```

------------------------------------------------------------------------

# 30. SERVICE HEALTH API

## GET `/api/v1/services/health`

Return visualization-ready:

``` text
service_id
service_name
criticality
health_score
health_status
availability
sla
incident_count
problem_count
change_count
```

------------------------------------------------------------------------

# 31. AI INSIGHTS API

## GET `/api/v1/insights`

Filters:

``` text
severity
type
service_id
date_from
date_to
```

------------------------------------------------------------------------

# 32. AI INSIGHT DETAIL API

## GET `/api/v1/insights/{insight_id}`

Return:

``` text
title
severity
type
confidence
description
evidence
affected_service
recommendation
created_at
```

------------------------------------------------------------------------

# 33. AI ASSISTANT API

## POST `/api/v1/assistant/query`

Request:

``` json
{
  "question": "Why did incidents increase this week?",
  "context": {
    "period_start": "2026-08-01",
    "period_end": "2026-08-08",
    "service_id": null
  }
}
```

Response:

``` json
{
  "answer": "...",
  "evidence": [],
  "recommendations": [],
  "ai_status": "AVAILABLE"
}
```

------------------------------------------------------------------------

# 34. AI ASSISTANT REQUEST FLOW

``` text
HTTP request
 ↓
validate question
 ↓
detect relevant intent
 ↓
retrieve relevant metrics
 ↓
calculate deterministic evidence
 ↓
build AI evidence packet
 ↓
call AI provider
 ↓
validate AI response
 ↓
return structured answer
```

------------------------------------------------------------------------

# 35. AI PROVIDER INTERFACE

Create:

``` text
AIProvider
```

Methods conceptually:

``` text
generate()
health_check()
```

Implementation:

``` text
ConfiguredAIProvider
FallbackAIProvider
```

------------------------------------------------------------------------

# 36. AI PROVIDER SELECTION

Configuration:

``` text
AI_PROVIDER=...
```

The rest of the application should not care which provider is active.

------------------------------------------------------------------------

# 37. AI FALLBACK

If no provider:

``` text
FallbackAIProvider
```

must return clearly labelled deterministic summaries where useful.

Example:

``` text
AI Status: FALLBACK
```

Never claim:

``` text
AI-generated
```

if an LLM was not used.

------------------------------------------------------------------------

# 38. REPORT API

## POST `/api/v1/reports/generate`

Request:

``` json
{
  "report_type": "WEEKLY",
  "period_start": "2026-08-01",
  "period_end": "2026-08-08"
}
```

Response:

``` json
{
  "report_id": "RPT-001",
  "status": "GENERATING"
}
```

------------------------------------------------------------------------

# 39. REPORT STATUS API

## GET `/api/v1/reports/{report_id}`

Returns:

``` text
report metadata
status
period
file references
AI status
notification status
```

------------------------------------------------------------------------

# 40. REPORT HISTORY API

## GET `/api/v1/reports`

Filters:

``` text
type
status
date_from
date_to
```

Pagination required.

------------------------------------------------------------------------

# 41. REPORT DOWNLOAD API

## GET `/api/v1/reports/{report_id}/download`

Must securely return the generated report.

Do not expose filesystem paths.

------------------------------------------------------------------------

# 42. REPORT PREVIEW API

## GET `/api/v1/reports/{report_id}/preview`

Return HTML or a safe preview representation.

------------------------------------------------------------------------

# 43. SCHEDULER API

## GET `/api/v1/scheduler`

Return:

``` text
daily schedule
weekly schedule
monthly schedule
enabled status
next run
timezone
last execution
```

------------------------------------------------------------------------

# 44. UPDATE SCHEDULE API

## PUT `/api/v1/scheduler/{schedule_type}`

Types:

``` text
DAILY
WEEKLY
MONTHLY
```

Request example:

``` json
{
  "enabled": true,
  "hour": 8,
  "minute": 0,
  "weekday": "MONDAY",
  "day_of_month": 1
}
```

Only relevant fields need to be used for each schedule type.

------------------------------------------------------------------------

# 45. SCHEDULER EXECUTION API

## POST `/api/v1/scheduler/{schedule_type}/run-now`

Purpose:

Trigger the same production report workflow immediately for
demo/testing.

Do not create a separate demo-only reporting algorithm.

------------------------------------------------------------------------

# 46. NOTIFICATION API

## POST `/api/v1/notifications/test`

Request:

``` json
{
  "provider": "TEAMS"
}
```

or:

``` json
{
  "provider": "SLACK"
}
```

------------------------------------------------------------------------

# 47. NOTIFICATION STATUS API

## GET `/api/v1/notifications/status`

Return:

``` text
Teams configured
Slack configured
last send
last error
```

Never return webhook secrets.

------------------------------------------------------------------------

# 48. DATA SOURCE API

## GET `/api/v1/data-sources`

Return:

``` text
Manual Upload
ServiceNow
Jira
```

with:

``` text
status
implemented
configured
```

Example:

``` json
{
  "name": "ServiceNow",
  "status": "PLANNED",
  "implemented": false,
  "configured": false
}
```

------------------------------------------------------------------------

# 49. SERVICE NOW ADAPTER

Create interface:

``` text
ITSMDataSource
```

Methods:

``` text
test_connection()
fetch_incidents()
fetch_problems()
fetch_changes()
fetch_services()
fetch_sla()
```

V1 implementation:

``` text
FileDataSource
```

ServiceNow adapter may remain unconfigured/planned.

------------------------------------------------------------------------

# 50. SERVICE NOW RULE

Do not implement a fake ServiceNow connection.

If credentials/configuration are absent:

``` text
NOT CONFIGURED
```

If implementation is only architectural:

``` text
PLANNED
```

------------------------------------------------------------------------

# 51. TEAMS ADAPTER

Create:

``` text
NotificationProvider
```

Implementation:

``` text
TeamsWebhookProvider
```

Method:

``` text
send_report_notification(report)
```

------------------------------------------------------------------------

# 52. SLACK ADAPTER

Implementation:

``` text
SlackWebhookProvider
```

Method:

``` text
send_report_notification(report)
```

------------------------------------------------------------------------

# 53. NOTIFICATION PAYLOAD

Example conceptual content:

``` text
OPSINTEL Weekly Operations Report

Period:
01 Aug – 08 Aug

OHI:
82 — HEALTHY

Top Risk:
Payment Service

Key Insight:
Incident volume increased 42%.

Report:
Available in OPSINTEL
```

Do not put huge report content into the notification.

------------------------------------------------------------------------

# 54. HEALTH API

## GET `/health`

Return:

``` json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

------------------------------------------------------------------------

# 55. SYSTEM STATUS API

## GET `/api/v1/system/status`

Return:

``` text
database
analytics
AI
scheduler
Teams
Slack
last ingestion
last report
```

------------------------------------------------------------------------

# 56. API VERSIONING

All application APIs should use:

``` text
/api/v1/
```

This makes future evolution easier.

------------------------------------------------------------------------

# 57. RESPONSE ENVELOPE

Use consistent response structures where practical.

Success:

``` json
{
  "data": {},
  "meta": {}
}
```

For simple endpoints, a direct object may be acceptable if consistency
is preserved.

------------------------------------------------------------------------

# 58. ERROR CONTRACT

Standard:

``` json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Dataset validation failed.",
    "details": []
  }
}
```

------------------------------------------------------------------------

# 59. ERROR CODES

Suggested:

``` text
VALIDATION_FAILED
FILE_NOT_SUPPORTED
FILE_TOO_LARGE
MAPPING_REQUIRED
INGESTION_FAILED
PROCESSING_FAILED
DATA_NOT_FOUND
REPORT_GENERATION_FAILED
AI_UNAVAILABLE
AI_REQUEST_FAILED
SCHEDULE_INVALID
NOTIFICATION_FAILED
CONFIGURATION_MISSING
INTERNAL_ERROR
```

------------------------------------------------------------------------

# 60. HTTP STATUS CODES

Use appropriate status codes:

``` text
200 OK
201 Created
202 Accepted
400 Bad Request
404 Not Found
409 Conflict
422 Validation Error
500 Internal Server Error
503 Service Unavailable
```

------------------------------------------------------------------------

# 61. ASYNCHRONOUS OPERATIONS

Operations that may take noticeable time:

-   ingestion;
-   analytics refresh;
-   report generation;
-   AI processing.

Should use job/status patterns rather than blocking the browser
unnecessarily.

------------------------------------------------------------------------

# 62. JOB ARCHITECTURE

Conceptually:

``` text
Job
├── id
├── type
├── status
├── started_at
├── completed_at
├── progress
├── result
└── error
```

V1 may use in-process execution with job persistence.

Future production can move to distributed workers.

------------------------------------------------------------------------

# 63. SCHEDULER ARCHITECTURE

Use APScheduler.

The scheduler should invoke:

``` text
ReportService.generate_scheduled_report()
```

It must not duplicate report calculations.

------------------------------------------------------------------------

# 64. APPLICATION STARTUP

On startup:

``` text
load config
 ↓
initialize logging
 ↓
initialize database
 ↓
run schema checks/migrations
 ↓
initialize providers
 ↓
initialize scheduler
 ↓
register routes
 ↓
start application
```

------------------------------------------------------------------------

# 65. APPLICATION SHUTDOWN

On shutdown:

``` text
stop scheduler
close database resources
flush logging
release resources
```

------------------------------------------------------------------------

# 66. DATABASE REPOSITORIES

Repositories should abstract persistence.

Examples:

``` text
IncidentRepository
ProblemRepository
ChangeRepository
ServiceRepository
SLARepository
ReportRepository
InsightRepository
IngestionJobRepository
ScheduleRepository
```

------------------------------------------------------------------------

# 67. REPOSITORY RULE

Repositories should not contain executive business logic.

Example:

Good:

``` text
get_incidents_by_period()
```

Bad:

``` text
calculate_ohI_and_decide_if_service_is_bad()
```

Business calculations belong in analytics/services.

------------------------------------------------------------------------

# 68. APPLICATION SERVICES

Recommended:

``` text
IngestionService
AnalyticsService
DashboardService
InsightService
AssistantService
ReportService
SchedulerService
NotificationService
DataSourceService
SystemStatusService
```

------------------------------------------------------------------------

# 69. ANALYTICS SERVICE

Should expose high-level operations:

``` text
get_overview()
get_incident_summary()
get_problem_summary()
get_change_summary()
get_service_health()
get_ohi()
get_trends()
get_anomalies()
get_correlations()
```

------------------------------------------------------------------------

# 70. DASHBOARD SERVICE

The dashboard service should compose analytics outputs.

It should not reimplement metrics.

------------------------------------------------------------------------

# 71. REPORT SERVICE

The report service:

``` text
gets period
 ↓
gets analytics snapshot
 ↓
gets AI insights
 ↓
renders report
 ↓
validates report
 ↓
stores report
 ↓
returns report metadata
```

------------------------------------------------------------------------

# 72. AI SERVICE

The AI service:

``` text
receives evidence
 ↓
builds prompt
 ↓
calls provider
 ↓
validates response
 ↓
returns structured output
```

------------------------------------------------------------------------

# 73. NOTIFICATION SERVICE

The notification service:

``` text
receives report
 ↓
selects provider
 ↓
sends notification
 ↓
records execution
```

------------------------------------------------------------------------

# 74. PROVIDER ABSTRACTION

External providers must be replaceable.

``` text
AIProvider
NotificationProvider
ITSMDataSource
```

This avoids coupling the whole application to one vendor.

------------------------------------------------------------------------

# 75. HTTP CLIENT RULE

External HTTP calls should:

-   have timeouts;
-   handle connection errors;
-   avoid logging secrets;
-   return structured failures;
-   retry only when safe;
-   not hang the application indefinitely.

------------------------------------------------------------------------

# 76. WEBHOOK SECURITY

Webhook URLs are secrets.

Never:

-   return them through API;
-   display them in UI;
-   log them;
-   commit them;
-   include them in screenshots.

------------------------------------------------------------------------

# 77. AI SECURITY

AI API keys must remain backend-only.

Do not send:

``` text
AI_API_KEY
```

to the frontend.

------------------------------------------------------------------------

# 78. UPLOAD API SECURITY

The API must enforce:

-   file extension allowlist;
-   maximum size;
-   safe filename;
-   safe storage path;
-   parsing timeout/limits where practical.

------------------------------------------------------------------------

# 79. CORS

Configure CORS explicitly.

Development may allow local frontend origin.

Do not use unrestricted wildcard CORS in production configuration.

------------------------------------------------------------------------

# 80. LOGGING

Use structured logs.

Example:

``` text
event=INGESTION_COMPLETED
job_id=JOB-001
dataset_version=DATASET-001
rows=5248
duration_ms=...
```

------------------------------------------------------------------------

# 81. CORRELATION ID

Where practical, generate a request/correlation ID.

Use it across:

``` text
API
service
job
logs
```

This makes debugging easier.

------------------------------------------------------------------------

# 82. AUDITABILITY

Record important actions:

``` text
dataset processed
report generated
schedule changed
notification sent
```

V1 can use application logs and execution tables.

Future production can introduce a formal audit service.

------------------------------------------------------------------------

# 83. API DOCUMENTATION

FastAPI OpenAPI documentation must remain enabled in development.

The repository should also contain:

``` text
docs/API_CONTRACT.md
```

Document major endpoints in human-readable form.

------------------------------------------------------------------------

# 84. API TESTING

Every major endpoint requires:

-   happy-path test;
-   invalid-input test;
-   not-found test where applicable;
-   dependency failure test where applicable.

------------------------------------------------------------------------

# 85. INTEGRATION TESTING

Test:

``` text
upload
→ validate
→ process
→ dashboard
→ report
```

as one end-to-end backend workflow.

------------------------------------------------------------------------

# 86. SCHEDULER TESTING

Test:

-   daily schedule;
-   weekly schedule;
-   monthly schedule;
-   enable/disable;
-   next-run calculation;
-   manual run-now;
-   failed execution.

------------------------------------------------------------------------

# 87. NOTIFICATION TESTING

Test:

``` text
configured provider → success
missing provider → not configured
provider failure → recorded failure
```

Report generation must remain successful even if notification fails.

------------------------------------------------------------------------

# 88. SERVICE NOW TESTING

Because ServiceNow is future scope:

-   test interface contract;
-   test unconfigured state;
-   test placeholder status;
-   do not require live ServiceNow for POC acceptance.

------------------------------------------------------------------------

# 89. BACKEND ERROR ISOLATION

AI failure:

``` text
dashboard remains operational
```

Notification failure:

``` text
report remains available
```

One chart query failure:

``` text
other dashboard sections remain available
```

------------------------------------------------------------------------

# 90. API PERFORMANCE

V1 target:

-   normal dashboard endpoint should respond quickly for demo-sized
    datasets;
-   avoid full-table scans for every frontend request where aggregation
    can be precomputed;
-   paginate detail endpoints.

Exact performance targets can be refined after profiling.

------------------------------------------------------------------------

# 91. DATABASE INDEXING

Add indexes to frequently filtered fields:

``` text
incident_id
service_id
created_at
status
priority

problem_id
service_id
created_at
status

change_id
service_id
created_at
status
risk_level
```

Do not add indexes blindly; document meaningful ones.

------------------------------------------------------------------------

# 92. TRANSACTION BOUNDARIES

Processing should be transactional where practical.

A dataset should not appear fully processed when only half of its
records were persisted unless the job explicitly supports partial
processing.

------------------------------------------------------------------------

# 93. DATASET PROCESSING TRANSACTION

Preferred:

``` text
begin
 ↓
normalize
 ↓
validate
 ↓
persist
 ↓
dataset version
 ↓
commit
```

Then:

``` text
analytics refresh
```

If persistence fails:

``` text
rollback
```

------------------------------------------------------------------------

# 94. REPORT TRANSACTION

Report metadata should only become:

``` text
COMPLETED
```

after:

-   file generated;
-   file validated;
-   file stored.

------------------------------------------------------------------------

# 95. REPORT VALIDATION

Validate:

-   file exists;
-   non-zero size;
-   expected title;
-   reporting period;
-   required sections;
-   OHI;
-   key metrics.

------------------------------------------------------------------------

# 96. SCHEDULER DUPLICATE PREVENTION

The same scheduled report should not be generated multiple times
unintentionally.

Use an execution identity such as:

``` text
schedule_type
+
period_start
+
period_end
```

before creating a duplicate.

------------------------------------------------------------------------

# 97. IDEMPOTENCY

Where possible:

``` text
same dataset
+
same period
+
same report type
```

should produce a controlled result rather than uncontrolled duplicate
records.

Manual regeneration may intentionally create a new report execution.

------------------------------------------------------------------------

# 98. BACKEND SYSTEM STATUS

System status should distinguish:

``` text
READY
DEGRADED
NOT CONFIGURED
FAILED
```

Example:

``` text
Database       READY
Analytics      READY
AI             NOT CONFIGURED
Scheduler      READY
Teams          NOT CONFIGURED
Slack          READY
```

------------------------------------------------------------------------

# 99. FUTURE PRODUCTION BOUNDARY

Do not build production infrastructure into V1 unless necessary.

Future:

``` text
PostgreSQL
Redis
Celery / worker queue
Object storage
distributed scheduler
authentication
authorization
enterprise secrets manager
centralized observability
```

The architecture should make these replaceable later.

------------------------------------------------------------------------

# 100. BACKEND DEFINITION OF DONE

Backend is complete only when:

-   application starts;
-   database initializes;
-   ingestion API works;
-   validation API works;
-   process API works;
-   dashboard API works;
-   incident APIs work;
-   problem APIs work;
-   change APIs work;
-   service APIs work;
-   AI APIs work/fallback works;
-   report APIs work;
-   scheduler APIs work;
-   notification APIs work;
-   health APIs work;
-   tests pass;
-   API documentation exists;
-   errors are structured;
-   secrets are protected.

------------------------------------------------------------------------

# 101. ACCEPTANCE CRITERIA

### API-001

Backend starts with documented command.

### API-002

Database initializes successfully.

### API-003

Upload endpoint accepts supported files.

### API-004

Validation endpoint returns useful results.

### API-005

Process endpoint creates a dataset version.

### API-006

Dashboard endpoint returns dynamic analytics.

### API-007

Incident endpoints support filtering.

### API-008

Problem endpoints support filtering.

### API-009

Change endpoints support filtering.

### API-010

Service endpoints support health information.

### API-011

AI assistant endpoint works or clearly reports fallback.

### API-012

Report generation endpoint works.

### API-013

Report download works securely.

### API-014

Scheduler configuration works.

### API-015

Run-now works.

### API-016

Notification test works when configured.

### API-017

System health endpoint works.

### API-018

Structured error contract is consistent.

### API-019

No secrets appear in API responses/logs.

### API-020

End-to-end integration test passes.

------------------------------------------------------------------------

# 102. ANTIGRAVITY IMPLEMENTATION PROTOCOL

For every backend feature:

``` text
READ REQUIREMENT
      ↓
IDENTIFY SERVICE
      ↓
DEFINE SCHEMA
      ↓
DEFINE REPOSITORY
      ↓
IMPLEMENT BUSINESS LOGIC
      ↓
IMPLEMENT ROUTE
      ↓
ADD TESTS
      ↓
CONNECT FRONTEND
      ↓
VERIFY END-TO-END
      ↓
UPDATE DOCUMENTATION
```

Do not create a route before defining what service owns the behavior.

------------------------------------------------------------------------

# 103. DOCUMENTATION UPDATE RULE

Every implementation phase must update:

``` text
docs/
knowledge/
status/
DECISIONS.md
CHANGELOG.md
```

as appropriate.

At minimum, update:

``` text
CURRENT_STATE.md
PHASE_STATUS.md
TEST_STATUS.md
NEXT_ACTIONS.md
```

after each completed phase.

------------------------------------------------------------------------

# 104. FINAL BACKEND ARCHITECTURE

``` text
                     FRONTEND
                         |
                      REST API
                         |
                ┌────────┴────────┐
                │                 │
             ROUTES           SCHEMAS
                │
                ▼
        APPLICATION SERVICES
                |
       ┌────────┼─────────┐
       │        │         │
   INGESTION ANALYTICS    AI
       │        │         │
       │        └────┬────┘
       │             │
       ▼             ▼
   REPOSITORIES   EVIDENCE
       │             │
       ▼             ▼
    DATABASE       REPORT
                     │
              ┌──────┴──────┐
              ▼             ▼
          SCHEDULER     NOTIFICATION
                            │
                       ┌────┴────┐
                       ▼         ▼
                     TEAMS     SLACK
```

------------------------------------------------------------------------

# 105. FINAL BACKEND PRINCIPLE

The backend should behave like the **orchestrator of a reliable
operational intelligence pipeline**.

The frontend asks:

> "Show me the operational state."

The backend determines:

> "Here is the authoritative state, calculated consistently."

The AI asks:

> "How can I explain this evidence?"

The report engine asks:

> "How can I package the same evidence for executives?"

The scheduler asks:

> "When should that process happen?"

The notification service asks:

> "Where should the completed result be delivered?"

No component should secretly perform another component's responsibility.

------------------------------------------------------------------------

# 106. COMPANION DOCUMENTS

Completed:

``` text
01_MASTER_ARCHITECTURE_AND_PRODUCT_BLUEPRINT.md
02_FUNCTIONAL_REQUIREMENTS_AND_WORKFLOWS.md
03_UI_UX_AND_DASHBOARD_SPECIFICATION.md
04_DATA_INGESTION_ANALYTICS_AND_KPI_SPECIFICATION.md
```

Next:

``` text
06_AI_ASSISTANT_AND_OBSIDIAN_SPECIFICATION.md
```

That document will define AI usage in depth, including prompt
architecture, evidence grounding, assistant behavior, AI insight
generation, fallback mode, hallucination controls, AI evaluation,
Obsidian vault structure, project memory, and how AI should help
maintain the project documentation.

# END OF OPSINTEL BACKEND, API & INTEGRATION SPECIFICATION
