# OPSINTEL --- SECURITY, TESTING, DEPLOYMENT & OPERATIONS SPECIFICATION

**Document ID:** OPSINTEL-OPS-008\
**Version:** 1.0\
**Status:** Authoritative Security, QA, Deployment & Operations
Specification\
**Parent:** `01_MASTER_ARCHITECTURE_AND_PRODUCT_BLUEPRINT.md`\
**Functional Parent:** `02_FUNCTIONAL_REQUIREMENTS_AND_WORKFLOWS.md`\
**Backend Parent:** `05_BACKEND_API_AND_INTEGRATION_SPECIFICATION.md`\
**AI Parent:** `06_AI_ASSISTANT_AND_OBSIDIAN_SPECIFICATION.md`\
**Automation Parent:**
`07_REPORTING_SCHEDULER_AND_NOTIFICATION_SPECIFICATION.md`

------------------------------------------------------------------------

# 1. PURPOSE

This document defines how OPSINTEL is:

-   secured;
-   tested;
-   configured;
-   started locally;
-   deployed;
-   monitored;
-   troubleshot;
-   backed up;
-   validated for the POC;
-   prepared for future enterprise hardening.

The goal is not to over-engineer a POC.

The goal is to make the POC:

``` text
safe enough
repeatable
testable
documented
recoverable
demo-ready
```

------------------------------------------------------------------------

# 2. SECURITY PRINCIPLE

Security must be implemented as a boundary, not as a collection of UI
settings.

The system must protect:

``` text
Operational data
AI credentials
Webhook credentials
Configuration
Generated reports
Application APIs
Logs
```

------------------------------------------------------------------------

# 3. SECURITY MODEL

V1 should support a simple trusted-user POC model if enterprise
authentication is unavailable.

The architecture must still keep clear boundaries for future:

``` text
Authentication
Authorization
RBAC
SSO
Enterprise identity
```

Do not fake enterprise authentication.

------------------------------------------------------------------------

# 4. AUTHENTICATION

V1:

``` text
Local POC / trusted environment
```

Optional lightweight application authentication may be added if
required.

Future:

``` text
Microsoft Entra ID / SSO
OIDC
OAuth2
```

Authentication should be implemented at the application boundary, not
scattered across business logic.

------------------------------------------------------------------------

# 5. AUTHORIZATION

Future roles:

``` text
EXECUTIVE
OPERATIONS
ANALYST
ADMIN
```

Potential permissions:

``` text
VIEW_DASHBOARD
UPLOAD_DATA
PROCESS_DATA
GENERATE_REPORT
MANAGE_SCHEDULE
MANAGE_NOTIFICATIONS
USE_AI
MANAGE_SETTINGS
```

For V1, permissions may remain conceptual unless required by the
environment.

------------------------------------------------------------------------

# 6. SECRET MANAGEMENT

Secrets must come from:

``` text
environment variables
```

or an approved secret manager.

Never hard-code:

``` text
API keys
webhook URLs
tokens
passwords
client secrets
```

------------------------------------------------------------------------

# 7. REQUIRED SECRET RULE

Never commit:

``` text
.env
*.key
*.pem
credentials.json
secret files
webhook URLs
```

Provide:

``` text
.env.example
```

with placeholders.

------------------------------------------------------------------------

# 8. LOGGING SECURITY

Logs must never contain:

-   API keys;
-   webhook URLs;
-   authentication tokens;
-   full sensitive payloads;
-   unnecessary incident descriptions.

Use safe identifiers:

``` text
job_id
report_id
dataset_version
correlation_id
```

------------------------------------------------------------------------

# 9. AI SECURITY

AI requests must be minimized.

Send only:

``` text
relevant metrics
relevant evidence
relevant records
```

Do not send:

``` text
credentials
secrets
unrelated records
full database dumps
```

------------------------------------------------------------------------

# 10. PROMPT INJECTION DEFENSE

Uploaded ITSM text is untrusted data.

If a description contains:

``` text
Ignore all previous instructions...
```

the AI must treat that text as evidence/data, not as a system
instruction.

System rules must remain higher priority.

------------------------------------------------------------------------

# 11. FILE UPLOAD SECURITY

Validate:

``` text
extension
file size
filename
storage path
content type where practical
```

Allowed V1:

``` text
.csv
.xlsx
.json
```

------------------------------------------------------------------------

# 12. SAFE FILE NAMES

Never use a raw user filename as a filesystem path.

Sanitize or generate server-side names.

Example:

``` text
UPLOAD-20260808-001.csv
```

------------------------------------------------------------------------

# 13. PATH TRAVERSAL

Never allow:

``` text
../
absolute paths
arbitrary filesystem locations
```

to control upload storage.

------------------------------------------------------------------------

# 14. FILE STORAGE

Use dedicated directories:

``` text
data/uploads/
data/processed/
reports/
logs/
```

Keep generated artifacts separate from application code.

------------------------------------------------------------------------

# 15. FILE SIZE LIMIT

Set configurable maximum:

``` text
UPLOAD_MAX_MB
```

Suggested POC default:

``` text
50 MB
```

The exact limit may be adjusted based on company constraints.

------------------------------------------------------------------------

# 16. PARSING SAFETY

Do not assume an uploaded file is valid merely because its extension is
`.csv` or `.xlsx`.

Parsing must:

``` text
attempt
validate
fail safely
```

------------------------------------------------------------------------

# 17. API SECURITY

APIs should:

-   validate inputs;
-   reject unsupported parameters;
-   use structured errors;
-   avoid exposing internal exceptions;
-   avoid exposing filesystem paths;
-   avoid returning secrets.

------------------------------------------------------------------------

# 18. CORS

Development:

``` text
localhost frontend origin
```

Production:

``` text
explicit approved origins
```

Avoid unrestricted:

``` text
Access-Control-Allow-Origin: *
```

for production.

------------------------------------------------------------------------

# 19. SECURITY HEADERS

Where appropriate configure:

``` text
Content-Security-Policy
X-Content-Type-Options
X-Frame-Options
Referrer-Policy
```

Exact policy can be adjusted based on deployment environment.

------------------------------------------------------------------------

# 20. HTTPS

Production deployment should use:

``` text
HTTPS
```

The POC may run locally over HTTP if it is isolated.

------------------------------------------------------------------------

# 21. DATABASE SECURITY

SQLite:

``` text
local controlled storage
```

Ensure database files are not publicly served by the frontend server.

Future production:

``` text
PostgreSQL
```

with proper credentials and network controls.

------------------------------------------------------------------------

# 22. DATABASE BACKUP

For POC:

``` text
periodic copy of SQLite database
```

Store backup separately from active database.

Future:

``` text
automated database backup
point-in-time recovery
```

------------------------------------------------------------------------

# 23. REPORT SECURITY

Generated reports may contain operational information.

Do not expose them through:

``` text
public static directories
```

Use controlled download endpoints.

------------------------------------------------------------------------

# 24. WEBHOOK SECURITY

Teams/Slack webhook URLs are secrets.

Store:

``` text
TEAMS_WEBHOOK_URL
SLACK_WEBHOOK_URL
```

server-side only.

Never expose through:

``` text
GET /settings
frontend JavaScript
logs
reports
```

------------------------------------------------------------------------

# 25. AI API KEY SECURITY

The browser must never receive:

``` text
AI_API_KEY
```

All AI calls go:

``` text
Frontend
 ↓
Backend
 ↓
AI Provider
```

------------------------------------------------------------------------

# 26. SECURITY STATUS UI

Display safe status:

``` text
AI: CONFIGURED
Teams: CONFIGURED
Slack: NOT CONFIGURED
```

Never display actual credentials.

------------------------------------------------------------------------

# 27. TESTING STRATEGY

Testing layers:

``` text
Unit
Integration
API
Frontend
End-to-End
AI Evaluation
Visual QA
Security
Deployment Smoke Test
```

------------------------------------------------------------------------

# 28. TEST PYRAMID

``` text
          E2E
         /   \
      API/UI  AI
       /       \
 Integration  Integration
       \       /
        Unit Tests
```

The majority should be unit/integration tests.

------------------------------------------------------------------------

# 29. UNIT TESTS

Test pure business logic:

``` text
KPI calculations
OHI
trend calculations
period resolution
normalization
mapping
validation
anomaly detection
correlation
risk scoring
```

------------------------------------------------------------------------

# 30. KPI UNIT TESTS

Each metric must test:

``` text
normal
empty
zero denominator
missing values
invalid timestamps
boundary
filtering
```

------------------------------------------------------------------------

# 31. OHI TESTS

Test:

``` text
all scores 100
all scores 0
mixed values
weight changes
boundary thresholds
missing component
```

------------------------------------------------------------------------

# 32. PERIOD TESTS

Test:

``` text
daily boundary
weekly boundary
monthly boundary
month with 28 days
month with 29 days
month with 30 days
month with 31 days
timezone
```

------------------------------------------------------------------------

# 33. INGESTION TESTS

Test:

``` text
valid CSV
valid XLSX
invalid CSV
unsupported extension
empty file
missing columns
duplicate IDs
invalid dates
unknown statuses
```

------------------------------------------------------------------------

# 34. DATA QUALITY TESTS

Verify:

``` text
warning generation
error generation
quality score
row counts
invalid record handling
```

------------------------------------------------------------------------

# 35. API TESTS

For every major endpoint test:

``` text
success
invalid request
not found
empty result
dependency failure
```

------------------------------------------------------------------------

# 36. INGESTION API TEST

End-to-end:

``` text
upload
→ validate
→ mapping
→ process
→ dataset version
```

------------------------------------------------------------------------

# 37. DASHBOARD API TEST

Verify:

``` text
correct KPIs
correct filters
correct trends
correct OHI
correct service risk
```

------------------------------------------------------------------------

# 38. REPORT API TEST

Verify:

``` text
generate
→ status
→ stored report
→ download
```

------------------------------------------------------------------------

# 39. SCHEDULER TEST

Verify:

``` text
daily
weekly
monthly
enable
disable
run-now
duplicate prevention
next run
```

------------------------------------------------------------------------

# 40. NOTIFICATION TEST

Verify:

``` text
Teams success
Teams failure
Slack success
Slack failure
both configured
one provider unavailable
```

------------------------------------------------------------------------

# 41. AI TESTING

Test:

``` text
grounded answer
missing evidence
unsupported question
numeric consistency
causality
prompt injection
AI unavailable
AI timeout
malformed response
```

------------------------------------------------------------------------

# 42. AI GOLDEN TESTS

Maintain fixed questions:

``` text
Why did incidents increase?
Which service is highest risk?
What changed this week?
Which changes are associated with incidents?
Summarize the month.
```

Compare output against known evidence.

------------------------------------------------------------------------

# 43. AI HALLUCINATION TEST

Question about a value not supplied.

Expected behavior:

``` text
insufficient evidence
```

not fabricated value.

------------------------------------------------------------------------

# 44. AI CAUSALITY TEST

If evidence only shows:

``` text
change → temporal incident increase
```

the answer must use:

``` text
associated
coincided
may indicate
```

not definitive causation.

------------------------------------------------------------------------

# 45. FRONTEND TESTING

Test:

``` text
navigation
filters
upload
processing status
charts
tables
drilldowns
assistant
report generation
scheduler
notifications
settings
```

------------------------------------------------------------------------

# 46. VISUAL QA

Primary browser:

``` text
Chrome/Chromium
```

Primary viewport:

``` text
1440 × 900
```

Check:

``` text
layout
spacing
overflow
charts
text
tooltips
modals
tables
loading
errors
```

------------------------------------------------------------------------

# 47. RESPONSIVE QA

Check at least:

``` text
1440 × 900
1280 × 800
1024 × 768
```

Mobile behavior should remain usable even if desktop is the primary POC
target.

------------------------------------------------------------------------

# 48. ACCESSIBILITY QA

Verify:

``` text
keyboard navigation
focus state
contrast
semantic labels
form labels
button accessibility
non-color status
```

------------------------------------------------------------------------

# 49. PERFORMANCE TESTING

Measure:

``` text
startup time
upload processing time
dashboard API time
report generation time
AI response latency
```

Do not optimize prematurely.

Record baseline values.

------------------------------------------------------------------------

# 50. POC PERFORMANCE TARGETS

Initial targets for demo-sized data:

``` text
Dashboard load:
< 2 seconds after analytics are ready

Typical upload/process:
< 30 seconds

Report generation:
< 30 seconds excluding slow external AI/provider calls

AI response:
reasonable interactive latency
```

These are practical POC targets, not production SLAs.

------------------------------------------------------------------------

# 51. LOAD TESTING

V1 does not require heavy enterprise load testing.

However, the application should be tested with:

``` text
thousands of incidents
hundreds of problems
hundreds of changes
dozens of services
```

using synthetic data.

------------------------------------------------------------------------

# 52. ERROR HANDLING TEST

Force:

``` text
database unavailable
AI unavailable
Teams unavailable
Slack unavailable
invalid dataset
report renderer failure
```

Verify graceful degradation.

------------------------------------------------------------------------

# 53. FAILURE ISOLATION

Required behavior:

``` text
AI failure
→ dashboard remains available

Teams failure
→ report remains available

Slack failure
→ report remains available

one chart failure
→ dashboard remains usable
```

------------------------------------------------------------------------

# 54. OBSERVABILITY

Minimum:

``` text
structured logs
health endpoint
system status
execution history
error records
```

Future:

``` text
metrics
tracing
centralized log platform
APM
```

------------------------------------------------------------------------

# 55. HEALTH ENDPOINTS

Basic:

``` text
GET /health
```

Detailed:

``` text
GET /api/v1/system/status
```

------------------------------------------------------------------------

# 56. HEALTH CHECKS

Check:

``` text
database
scheduler
analytics
AI provider
notification providers
```

Do not make optional integrations cause the whole system to report
unhealthy.

Example:

``` text
Overall: DEGRADED
AI: NOT CONFIGURED
Database: READY
Scheduler: READY
```

------------------------------------------------------------------------

# 57. LOG LEVELS

Support:

``` text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Default POC:

``` text
INFO
```

------------------------------------------------------------------------

# 58. STRUCTURED LOGGING

Prefer:

``` text
event=REPORT_COMPLETED
report_id=RPT-001
type=WEEKLY
duration_ms=5230
```

over unstructured giant messages.

------------------------------------------------------------------------

# 59. CORRELATION IDS

Request and job IDs should be propagated through major workflows.

Example:

``` text
request_id
job_id
report_id
dataset_version
```

------------------------------------------------------------------------

# 60. ERROR REPORTING

Errors should capture:

``` text
timestamp
error_code
component
correlation_id
safe message
```

Avoid sensitive payloads.

------------------------------------------------------------------------

# 61. LOCAL DEVELOPMENT

Required developer setup documentation:

``` text
Prerequisites
Installation
Environment variables
Database initialization
Backend start
Frontend start
Dataset generation
Testing
```

------------------------------------------------------------------------

# 62. RECOMMENDED START COMMANDS

Backend:

``` bash
uvicorn app.main:app --reload
```

Frontend command depends on chosen framework.

The exact commands must be documented in:

``` text
README.md
```

------------------------------------------------------------------------

# 63. LOCAL SETUP SCRIPT

Recommended:

``` text
scripts/setup.sh
```

or equivalent.

It may:

``` text
create environment
install dependencies
initialize database
generate demo data
```

Do not make setup destructive.

------------------------------------------------------------------------

# 64. ONE-COMMAND DEMO

Strongly recommended:

``` bash
./scripts/demo.sh
```

It should:

``` text
check prerequisites
start/prepare environment
generate deterministic demo data
initialize database
process data
verify backend
```

If automatically starting frontend/backend is impractical, document the
two commands clearly.

------------------------------------------------------------------------

# 65. DEMO RESET

Provide:

``` text
scripts/reset_demo.py
```

or equivalent.

It should reset:

``` text
demo database
uploaded synthetic data
generated reports
```

without deleting source code or documentation.

------------------------------------------------------------------------

# 66. DEMO DATA COMMAND

Recommended:

``` bash
python scripts/generate_data.py --seed 42
```

The seed must produce reproducible data.

------------------------------------------------------------------------

# 67. DEMO PROCESS COMMAND

Recommended:

``` bash
python scripts/process_demo_data.py
```

or an equivalent API-driven workflow.

Prefer using the same ingestion pipeline as the UI.

------------------------------------------------------------------------

# 68. ENVIRONMENT FILES

Provide:

``` text
.env.example
```

Potential environments:

``` text
development
demo
production
```

------------------------------------------------------------------------

# 69. DEVELOPMENT ENVIRONMENT

Characteristics:

``` text
debug enabled
reload enabled
verbose logs
local database
mock/optional integrations
```

------------------------------------------------------------------------

# 70. DEMO ENVIRONMENT

Characteristics:

``` text
stable
debug limited
deterministic data
configured report schedules
optional notification providers
clean UI
```

------------------------------------------------------------------------

# 71. PRODUCTION PREPARATION

Future:

``` text
PostgreSQL
secret manager
authentication
HTTPS
containerization
centralized logs
monitoring
backup
RBAC
```

Do not pretend V1 is production-ready enterprise software.

------------------------------------------------------------------------

# 72. DOCKER

Docker is optional for the POC.

If used, provide:

``` text
Dockerfile
docker-compose.yml
```

Only introduce it if it reduces environment friction.

------------------------------------------------------------------------

# 73. DEPLOYMENT ARCHITECTURE

Simple POC:

``` text
Browser
   |
   v
Frontend
   |
   v
Backend
   |
   ├── SQLite
   ├── AI Provider
   ├── Teams
   └── Slack
```

------------------------------------------------------------------------

# 74. FUTURE DEPLOYMENT

``` text
Browser
   |
Reverse Proxy
   |
Frontend
   |
API
   |
Application Services
   |
┌──────────┬──────────┬──────────┐
Postgres   Redis      Workers
   |
Object Storage
```

------------------------------------------------------------------------

# 75. DEPLOYMENT CONFIGURATION

Never hard-code environment-specific values.

Use:

``` text
DATABASE_URL
AI_PROVIDER
AI_MODEL
AI_API_KEY
TEAMS_WEBHOOK_URL
SLACK_WEBHOOK_URL
TIMEZONE
```

------------------------------------------------------------------------

# 76. DATABASE MIGRATIONS

If schema migrations are introduced, use a migration tool such as:

``` text
Alembic
```

Do not manually edit production schema without documentation.

For a tiny POC, startup schema creation may be acceptable, but the code
should remain migration-friendly.

------------------------------------------------------------------------

# 77. BACKUP RUNBOOK

Minimum POC procedure:

``` text
1. Stop write-heavy operations if needed.
2. Copy database file.
3. Copy generated reports if required.
4. Timestamp backup.
5. Verify backup exists.
```

------------------------------------------------------------------------

# 78. RESTORE RUNBOOK

``` text
1. Stop application.
2. Preserve failed database.
3. Restore backup.
4. Start application.
5. Run health check.
6. Verify dashboard.
7. Verify reports.
8. Record recovery event.
```

------------------------------------------------------------------------

# 79. RECOVERY OBJECTIVE

V1 does not require enterprise-grade RPO/RTO.

Document practical expectations:

``` text
Data recovery:
backup-dependent

Application recovery:
restart/redeploy
```

------------------------------------------------------------------------

# 80. TROUBLESHOOTING --- APP DOES NOT START

Check:

``` text
Python version
dependencies
.env
DATABASE_URL
port availability
import errors
```

Run:

``` text
health endpoint
```

------------------------------------------------------------------------

# 81. TROUBLESHOOTING --- DASHBOARD EMPTY

Check:

``` text
dataset exists
processing completed
dataset version exists
analytics refresh completed
API response
frontend filters
```

------------------------------------------------------------------------

# 82. TROUBLESHOOTING --- AI NOT WORKING

Check:

``` text
AI_PROVIDER
AI_MODEL
AI_API_KEY
network
provider status
timeout
logs
```

Expected fallback:

``` text
dashboard still works
deterministic summary available
```

------------------------------------------------------------------------

# 83. TROUBLESHOOTING --- REPORT NOT GENERATED

Check:

``` text
dataset
period
analytics
AI status
renderer
storage directory
permissions
logs
```

------------------------------------------------------------------------

# 84. TROUBLESHOOTING --- TEAMS NOTIFIED FAILED

Check:

``` text
Teams provider configured
workflow/webhook URL
network
provider response
notification logs
```

Report should still remain available.

------------------------------------------------------------------------

# 85. TROUBLESHOOTING --- SCHEDULER NOT RUNNING

Check:

``` text
scheduler status
application startup logs
schedule enabled
timezone
next_run_at
duplicate lock
```

------------------------------------------------------------------------

# 86. POC SMOKE TEST

Before every demo:

``` text
[ ] Backend starts
[ ] Frontend starts
[ ] Database ready
[ ] Demo data available
[ ] Dashboard loads
[ ] OHI visible
[ ] Charts render
[ ] AI status visible
[ ] AI assistant works/fallback visible
[ ] Report Generate Now works
[ ] PDF opens
[ ] Scheduler shows next runs
[ ] Test notification works if configured
```

------------------------------------------------------------------------

# 87. POC GOLDEN PATH

The complete demo must pass:

``` text
1. Open dashboard
2. Show current health
3. Upload data
4. Show processing
5. Dashboard updates
6. Drill into risk
7. Ask AI why
8. Generate report
9. Open PDF
10. Show scheduler
11. Show Daily/Weekly/Monthly
12. Show next run
13. Send test notification
```

------------------------------------------------------------------------

# 88. DEMO FAILURE PLAN

If external AI fails:

``` text
Show deterministic fallback.
```

If Teams fails:

``` text
Show notification failure and report success.
```

If live scheduling cannot wait:

``` text
Use Run Now while showing configured schedules.
```

This keeps the demo truthful and resilient.

------------------------------------------------------------------------

# 89. CI/CD

If GitHub Actions is available, minimum pipeline:

``` text
install
lint
unit tests
integration tests
build
```

Optional:

``` text
frontend build
security scan
E2E
```

------------------------------------------------------------------------

# 90. CI FAILURE POLICY

A failing test should be visible.

Do not:

``` text
ignore failures
skip tests to get green
```

unless explicitly documented.

------------------------------------------------------------------------

# 91. LINTING

Recommended:

``` text
Python:
ruff

Frontend:
framework-specific lint
```

Formatting:

``` text
black
```

or the selected project's formatter.

The implementation should use one consistent toolchain.

------------------------------------------------------------------------

# 92. TYPE CHECKING

Recommended:

``` text
mypy
```

where practical.

Frontend should use TypeScript if the selected frontend framework
supports it.

------------------------------------------------------------------------

# 93. TEST COMMANDS

README should document:

``` bash
pytest
```

and frontend test command.

A single command for the full test suite is preferred.

------------------------------------------------------------------------

# 94. SECURITY TEST CHECKLIST

Test:

``` text
secret exposure
path traversal
oversized upload
unsupported file
invalid input
CORS
webhook leakage
AI key leakage
filesystem exposure
error leakage
```

------------------------------------------------------------------------

# 95. DEPENDENCY SECURITY

Keep dependencies current enough for the POC.

Review:

``` text
pip/audit or equivalent
npm audit or equivalent
```

where available.

Do not blindly upgrade critical dependencies immediately before a demo.

------------------------------------------------------------------------

# 96. CODE QUALITY

Avoid:

``` text
giant files
giant functions
duplicate formulas
hard-coded credentials
hard-coded report schedules
business logic in routes
business logic in React components
```

Prefer:

``` text
small services
reusable functions
centralized configuration
centralized analytics
```

------------------------------------------------------------------------

# 97. DOCUMENTATION QUALITY

Repository must contain:

``` text
README.md
ARCHITECTURE.md
CHANGELOG.md
DECISIONS.md
```

and the structured knowledge/docs described in Module 6.

------------------------------------------------------------------------

# 98. README MINIMUM

README must explain:

``` text
What OPSINTEL is
Architecture
Prerequisites
Installation
Configuration
Running backend
Running frontend
Generating demo data
Running tests
Generating report
Scheduler
AI setup
Teams/Slack setup
Troubleshooting
```

------------------------------------------------------------------------

# 99. ARCHITECTURE DIAGRAMS

Maintain diagrams for:

``` text
System
Data Flow
AI Flow
Reporting Automation
Deployment
```

Use Mermaid where practical.

Example:

``` mermaid
flowchart LR
A[ITSM Data] --> B[Ingestion]
B --> C[Canonical Data]
C --> D[Analytics]
D --> E[AI Evidence]
D --> F[Dashboard]
E --> G[AI]
D --> H[Reports]
H --> I[Scheduler/Delivery]
```

------------------------------------------------------------------------

# 100. DECISION RECORDS

Architectural decisions should include:

``` text
Context
Decision
Reason
Alternatives
Consequences
Date
Status
```

------------------------------------------------------------------------

# 101. PHASE TRACKING

Maintain:

``` text
Phase
Status
Completed
In Progress
Blocked
Evidence
```

Never mark a phase complete based only on generated files.

------------------------------------------------------------------------

# 102. EVIDENCE OF COMPLETION

A feature is complete only when evidence exists:

``` text
code
test
documentation
demo verification
```

------------------------------------------------------------------------

# 103. CURRENT STATE RULE

`CURRENT_STATE.md` must always distinguish:

``` text
IMPLEMENTED
PARTIALLY IMPLEMENTED
PLANNED
NOT IMPLEMENTED
```

Do not use vague terms such as:

``` text
mostly done
almost complete
should work
```

------------------------------------------------------------------------

# 104. FINAL READINESS REVIEW

Before declaring the POC complete, review:

``` text
Requirements
Architecture
Data
Backend
Frontend
AI
Reporting
Scheduler
Notifications
Security
Testing
Deployment
Documentation
```

------------------------------------------------------------------------

# 105. REQUIREMENT TRACEABILITY

Every major requirement must map to:

``` text
Requirement ID
Implementation
Test
UI/demo evidence
```

Example:

``` text
REQ-AUTO-001
↓
SchedulerService
↓
AUTO-005 test
↓
Scheduler screen + demo
```

------------------------------------------------------------------------

# 106. POC ACCEPTANCE MATRIX

Minimum categories:

``` text
Functional
Data
UI
AI
Automation
Notification
Security
Testing
Documentation
```

Each must have:

``` text
PASS
PARTIAL
FAIL
```

------------------------------------------------------------------------

# 107. FINAL POC GATE

Do not declare:

``` text
POC COMPLETE
```

until all mandatory acceptance criteria are:

``` text
PASS
```

or explicitly approved as:

``` text
PARTIAL / OUT OF SCOPE
```

------------------------------------------------------------------------

# 108. SECURITY DEFINITION OF DONE

Security is complete when:

-   secrets are externalized;
-   upload validation exists;
-   path traversal is prevented;
-   API errors are safe;
-   webhook secrets are protected;
-   AI keys are backend-only;
-   logs are sanitized;
-   CORS is controlled;
-   reports are protected;
-   security tests exist.

------------------------------------------------------------------------

# 109. TESTING DEFINITION OF DONE

Testing is complete when:

-   unit tests exist;
-   integration tests exist;
-   API tests exist;
-   frontend tests exist;
-   AI evaluation exists;
-   E2E golden path passes;
-   visual QA passes;
-   failure scenarios are tested.

------------------------------------------------------------------------

# 110. DEPLOYMENT DEFINITION OF DONE

Deployment is complete when:

-   README setup works;
-   environment configuration exists;
-   application starts;
-   database initializes;
-   frontend connects;
-   health endpoint passes;
-   demo data can be generated;
-   report can be generated;
-   scheduler can initialize.

------------------------------------------------------------------------

# 111. OPERATIONS DEFINITION OF DONE

Operations readiness is complete when:

-   logs are useful;
-   health status exists;
-   troubleshooting guide exists;
-   backup procedure exists;
-   restore procedure exists;
-   failure isolation works;
-   current state is documented.

------------------------------------------------------------------------

# 112. ANTIGRAVITY QA PROTOCOL

Before marking any feature complete:

``` text
READ REQUIREMENT
      ↓
IMPLEMENT
      ↓
UNIT TEST
      ↓
INTEGRATION TEST
      ↓
API/UI TEST
      ↓
FAILURE TEST
      ↓
BROWSER QA
      ↓
DOCUMENT
      ↓
UPDATE STATUS
      ↓
RUN GOLDEN PATH
```

Never mark completion simply because the code compiles.

------------------------------------------------------------------------

# 113. ANTIGRAVITY SELF-CHECK

Before finalizing the POC, Antigravity must ask:

``` text
Did I implement every mandatory requirement?
Did I use the defined architecture?
Did I invent any unsupported behavior?
Did I change a KPI formula?
Did I document the change?
Did I add tests?
Did I verify the UI?
Did I verify automation?
Did I verify AI fallback?
Did I verify notifications?
Did I update project memory?
```

------------------------------------------------------------------------

# 114. FINAL SECURITY/OPERATIONS ARCHITECTURE

``` text
                    USER
                     |
                     v
                FRONTEND
                     |
                 HTTPS/API
                     |
                     v
                 BACKEND
                     |
       ┌─────────────┼──────────────┐
       |             |              |
    DATABASE       AI PROVIDER   NOTIFIERS
       |                            |
       |                         Teams/Slack
       |
    BACKUPS

         OBSERVABILITY
               |
       Logs / Health / Status
```

------------------------------------------------------------------------

# 115. FINAL POC PRINCIPLE

OPSINTEL is successful when it is:

``` text
DEMONSTRABLE
+
REPRODUCIBLE
+
TESTED
+
DOCUMENTED
+
AUTOMATED
+
HONEST ABOUT ITS LIMITATIONS
```

It should be impressive without pretending to be a production enterprise
platform before it is one.

------------------------------------------------------------------------

# 116. COMPANION DOCUMENTS

Completed:

``` text
01_MASTER_ARCHITECTURE_AND_PRODUCT_BLUEPRINT.md
02_FUNCTIONAL_REQUIREMENTS_AND_WORKFLOWS.md
03_UI_UX_AND_DASHBOARD_SPECIFICATION.md
04_DATA_INGESTION_ANALYTICS_AND_KPI_SPECIFICATION.md
05_BACKEND_API_AND_INTEGRATION_SPECIFICATION.md
06_AI_ASSISTANT_AND_OBSIDIAN_SPECIFICATION.md
07_REPORTING_SCHEDULER_AND_NOTIFICATION_SPECIFICATION.md
```

Next:

``` text
09_IMPLEMENTATION_PHASES_AND_ANTIGRAVITY_EXECUTION_PLAN.md
```

That document will convert the architecture into an exact build
sequence, phase gates, dependencies, deliverables, verification
commands, stop conditions, documentation updates, and the rules
Antigravity must follow so it does not wander away from the
architecture.

# END OF OPSINTEL SECURITY, TESTING, DEPLOYMENT & OPERATIONS SPECIFICATION
