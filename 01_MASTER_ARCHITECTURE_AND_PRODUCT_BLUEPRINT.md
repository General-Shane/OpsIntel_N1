# OPSINTEL --- MASTER AUTONOMOUS POC BUILD SPECIFICATION

## Version

V1.0 --- Complete POC Build Contract

## Purpose

This document is the single source of truth for building the complete
OPSINTEL POC in Google Antigravity.

The goal is not to produce a static dashboard or a collection of mock
screens.

The goal is to build a **working, end-to-end, automated AI-powered IT
operations reporting platform** that can ingest
incident/problem/change/service data from files, process it, display the
processed results dynamically on an executive dashboard, generate
daily/weekly/monthly reports, schedule those reports automatically, and
provide an AI assistant and AI-driven operational insights.

------------------------------------------------------------------------

# 1. ROLE OF THE ANTIGRAVITY AGENT

Act as the complete senior engineering team:

-   Chief Solution Architect
-   Technical Product Manager
-   Senior Full-Stack Engineer
-   Python/FastAPI Engineer
-   React/TypeScript Engineer
-   Data Engineer
-   Analytics Engineer
-   AI Engineer
-   Automation Engineer
-   Reporting Engineer
-   UI/UX Engineer
-   QA Engineer
-   Documentation Engineer
-   DevOps Engineer

The user is the product owner and demo owner.

The agent owns implementation quality.

Do not merely explain what should be built. Build it.

Do not stop after planning.

Do not create a fake frontend.

Do not use hard-coded dashboard values except for clearly labelled UI
placeholders during development. Final demo data must flow through the
actual ingestion/processing/backend pipeline.

------------------------------------------------------------------------

# 2. NON-NEGOTIABLE BUSINESS REQUIREMENT

The business requirement is:

> Automated daily, weekly and monthly operations report. Design and
> implement automated operational reporting that consolidate incident,
> problem, change and service management metrics into executive ready
> reports, significantly reducing manual effort while improving
> reporting consistency and timeliness.

The finished POC must demonstrate all of the following:

1.  Incident management consolidation.
2.  Problem management consolidation.
3.  Change management consolidation.
4.  Service management consolidation.
5.  SLA/operational metrics.
6.  File-based data ingestion.
7.  Automatic processing.
8.  Dynamic dashboard refresh after processing.
9.  Executive-ready visual reporting.
10. Daily report generation.
11. Weekly report generation.
12. Monthly report generation.
13. Automatic scheduling.
14. Report history.
15. AI-generated executive summary.
16. AI-generated operational insights.
17. AI recommendations.
18. AI assistant for interactive questions.
19. Evidence-grounded AI responses.
20. Synthetic dataset generation.
21. Data validation.
22. Error handling.
23. Browser-verifiable working UI.
24. Persistent project documentation/memory.
25. A complete end-to-end demo flow.

------------------------------------------------------------------------

# 3. PRODUCT NAME

Product name:

# OPSINTEL

Subtitle:

**AI Operations Intelligence & Automated Reporting**

Suggested positioning:

> Transform fragmented ITSM operational data into automated,
> explainable, executive-ready intelligence.

------------------------------------------------------------------------

# 4. CORE USER JOURNEY

The most important workflow is:

``` text
USER
  |
  | Upload files
  v
DATA INGESTION
  |
  v
FILE VALIDATION
  |
  v
DATA NORMALIZATION
  |
  v
DATA QUALITY CHECK
  |
  v
DATA STORAGE
  |
  v
KPI / ANALYTICS ENGINE
  |
  +-------------------+
  |                   |
  v                   v
DASHBOARD          AI ENGINE
  |                   |
  |                   v
  |              INSIGHTS
  |                   |
  |              RECOMMENDATIONS
  |                   |
  +---------+---------+
            |
            v
      REPORT ENGINE
            |
     +------+------+------+
     |      |             |
    DAILY  WEEKLY       MONTHLY
     |      |             |
     +------+------+------+
            |
            v
       REPORT HISTORY
            |
            v
      AUTOMATED DELIVERY
      / NOTIFICATION
```

The uploaded data must actually travel through this pipeline.

------------------------------------------------------------------------

# 5. INPUT MODEL

V1 must support file-based ingestion because the user may not have
direct Microsoft Graph or ServiceNow API access.

The application must support at least:

-   CSV
-   XLSX/Excel
-   JSON where practical

The ingestion UI should allow users to upload:

-   Incident file
-   Problem file
-   Change file
-   Service file
-   SLA file

Also support a single multi-sheet Excel workbook where practical.

The system should detect the source type using:

1.  filename
2.  column names
3.  sheet names
4.  optional user selection

If automatic classification is uncertain, show a mapping step instead of
silently importing incorrect data.

------------------------------------------------------------------------

# 6. FILE INGESTION UX

Create a dedicated Data Ingestion page.

It should show:

## Upload Area

-   Drag and drop
-   Browse files
-   Supported file types
-   File size guidance
-   Upload progress

## Dataset Classification

For each uploaded file show:

-   filename
-   detected type
-   confidence
-   number of rows
-   columns detected
-   validation status

## Column Mapping

If the input column names differ from the canonical schema, provide a
mapping UI.

Example:

``` text
Source column       Canonical field
------------------------------------------------
Incident Number     -> incident_id
Priority            -> priority
Opened Date         -> created_at
Closed Date         -> resolved_at
Configuration Item  -> service_id
```

Provide automatic mapping suggestions.

Allow manual correction.

## Validation Result

Show:

-   valid rows
-   invalid rows
-   missing fields
-   duplicate rows
-   invalid dates
-   invalid references
-   warnings
-   errors

The user must be able to continue only when critical validation errors
are resolved or explicitly accepted.

------------------------------------------------------------------------

# 7. INGESTION PIPELINE

Implement:

``` text
Upload
  |
  v
File parser
  |
  v
Schema detection
  |
  v
Column mapping
  |
  v
Validation
  |
  v
Normalization
  |
  v
Deduplication
  |
  v
Relationship validation
  |
  v
Persistence
  |
  v
Analytics refresh
  |
  v
Dashboard refresh
```

The pipeline should produce an ingestion job record.

Track:

-   job ID
-   started at
-   completed at
-   status
-   files processed
-   rows processed
-   rows rejected
-   warnings
-   errors

------------------------------------------------------------------------

# 8. DATA STORAGE

V1 should be easy to run locally.

Preferred:

-   SQLite for zero-configuration demo mode

Design repository/data-access interfaces so PostgreSQL can later be
used.

Do not make the frontend aware of which database is being used.

Environment variable:

``` text
DATABASE_URL
```

Provide:

``` text
sqlite:///./opsintel.db
```

as a default local configuration if appropriate.

------------------------------------------------------------------------

# 9. CANONICAL DATA MODEL

## INCIDENT

Required/expected concepts:

-   incident_id
-   service_id
-   problem_id
-   change_id
-   priority
-   severity
-   status
-   category
-   subcategory
-   created_at
-   acknowledged_at
-   resolved_at
-   resolution_time
-   sla_target
-   sla_status
-   reopened
-   assignment_group
-   description
-   resolution_notes

Support missing optional fields gracefully.

------------------------------------------------------------------------

## PROBLEM

-   problem_id
-   service_id
-   priority
-   status
-   category
-   created_at
-   resolved_at
-   age_days
-   root_cause
-   known_error
-   incident_count
-   description
-   resolution_notes

------------------------------------------------------------------------

## CHANGE

-   change_id
-   service_id
-   change_type
-   risk_level
-   status
-   created_at
-   planned_start
-   planned_end
-   completed_at
-   successful
-   rollback_required
-   incident_count
-   description

------------------------------------------------------------------------

## SERVICE

-   service_id
-   service_name
-   service_category
-   criticality
-   owner
-   availability
-   sla_target
-   health_status

------------------------------------------------------------------------

## SLA

-   sla_id
-   service_id
-   incident_id
-   target_hours
-   actual_hours
-   breached
-   breach_reason

------------------------------------------------------------------------

## REPORT

-   report_id
-   report_type
-   period_start
-   period_end
-   generated_at
-   status
-   file_path
-   summary

------------------------------------------------------------------------

## AI INSIGHT

-   insight_id
-   report_id
-   title
-   type
-   severity
-   description
-   confidence
-   affected_service
-   evidence
-   recommendation
-   created_at

------------------------------------------------------------------------

## INGESTION JOB

-   job_id
-   started_at
-   completed_at
-   status
-   files_count
-   rows_processed
-   rows_rejected
-   warning_count
-   error_count

------------------------------------------------------------------------

# 10. DATA RELATIONSHIPS

The system must preserve relationships:

``` text
SERVICE
 |
 +---- INCIDENT
 |       |
 |       +---- PROBLEM
 |       |
 |       +---- CHANGE
 |
 +---- PROBLEM
 |
 +---- CHANGE
```

The system must support analysis of:

``` text
Change
  |
  v
Incident
  |
  v
Problem
  |
  v
Service
```

Do not claim causation from simple temporal correlation.

Use language such as:

-   associated with
-   correlated with
-   potentially related
-   likely contributing factor

------------------------------------------------------------------------

# 11. SYNTHETIC DATA GENERATOR

Create a complete reproducible dataset generator.

File:

``` text
scripts/generate_data.py
```

Requirements:

-   deterministic random seed
-   configurable volume
-   configurable date range
-   configurable service count
-   realistic distributions
-   relationships
-   intentional operational scenarios

Generate at minimum:

-   20+ services
-   thousands of incidents
-   hundreds of problems
-   hundreds of changes
-   SLA records

Exact scale may be adjusted for local performance.

The generator must produce a dataset suitable for dashboard and report
demonstrations.

------------------------------------------------------------------------

# 12. SYNTHETIC SCENARIOS

Do not generate purely random data.

Inject these scenarios:

## Scenario 1 --- Payment Service Incident Spike

Normal activity followed by a significant incident increase.

## Scenario 2 --- Authentication Recurrence

Multiple semantically/operationally related incidents over time.

## Scenario 3 --- Change-Associated Incident Cluster

A change is followed by an unusual incident increase on the same
service.

## Scenario 4 --- Service Availability Decline

One critical service shows decreasing availability.

## Scenario 5 --- Problem Backlog Growth

Open problems increase over multiple periods.

## Scenario 6 --- SLA Degradation

SLA compliance falls for one or more services.

The analytics engine must discover these patterns from the generated
records.

Do not simply hard-code the resulting insight text.

------------------------------------------------------------------------

# 13. DATA QUALITY

Implement validation for:

-   required fields
-   dates
-   duplicate IDs
-   orphan references
-   negative durations
-   impossible timelines
-   invalid priorities
-   invalid statuses
-   invalid percentages
-   missing service references
-   malformed rows

Create a data quality score.

Example:

``` text
Data Quality
94 / 100
```

Show:

-   valid
-   warning
-   error

counts.

------------------------------------------------------------------------

# 14. DASHBOARD REQUIREMENT

The dashboard is the primary demo surface.

It must show processed data after ingestion.

Do not show static demo numbers if data has not been processed.

After ingestion:

``` text
Upload
 -> Process
 -> Refresh
 -> Dashboard reflects uploaded dataset
```

The user should be able to demonstrate this live.

------------------------------------------------------------------------

# 15. GLOBAL DASHBOARD STRUCTURE

Create a premium dark enterprise dashboard.

Navigation:

``` text
OPSINTEL

Overview

Data Ingestion

Incidents
Problems
Changes
Services

AI Insights

Reports

Settings
```

Top bar:

-   current reporting period
-   last successful data refresh
-   system status
-   data quality
-   user/demo identity if needed

------------------------------------------------------------------------

# 16. EXECUTIVE OVERVIEW

Top section:

# OPERATIONS HEALTH

Display:

``` text
82 / 100
HEALTHY
```

Use a polished radial/circular visualization.

Below it:

-   Incident Health
-   Problem Health
-   Change Health
-   Service Health
-   SLA Health

------------------------------------------------------------------------

# 17. KPI CARDS

Minimum cards:

-   Total Incidents
-   Open Incidents
-   P1/P2 Incidents
-   Problems
-   Changes
-   Change Success Rate
-   SLA Compliance
-   MTTR
-   Availability
-   Critical Services

Each KPI should show:

-   current value
-   previous period
-   change
-   direction
-   status

Example:

``` text
INCIDENTS
1,248
↑ 13%
```

------------------------------------------------------------------------

# 18. UNIQUE VISUALIZATIONS

Do not make the dashboard a wall of generic bar charts.

Implement a visually diverse set.

Required:

## A. Operations Health Ring

Circular/radial OHI.

## B. Incident Trend

Line chart over time.

Show previous period where useful.

## C. Incident Heatmap

Service/day or day/hour distribution.

## D. Service Health Matrix

Rows = services.

Columns:

-   availability
-   incidents
-   P1
-   SLA
-   problems
-   health

## E. Change Impact View

Relationship visualization:

``` text
CHANGE
  |
SERVICE
  |
INCIDENT
  |
PROBLEM
```

## F. Operational Risk View

Visualize risk across:

-   incident
-   problem
-   change
-   service

## G. Top Problem/Service Ranking

Use horizontal bar chart where appropriate.

## H. Trend Cards

Compact sparkline-style trend visualizations.

------------------------------------------------------------------------

# 19. INTERACTIVITY

The dashboard must not be static.

Global filters:

-   date period
-   service
-   priority
-   status
-   criticality

Selecting a service should update relevant dashboard content.

Selecting an incident should show:

-   incident details
-   service
-   problem
-   change
-   SLA
-   timeline

Selecting a problem should show related incidents.

Selecting a change should show related incidents and affected service.

------------------------------------------------------------------------

# 20. INCIDENT MODULE

Page:

``` text
/ incidents
```

Include:

-   total incidents
-   open incidents
-   resolved incidents
-   P1
-   P2
-   MTTR
-   SLA compliance
-   trend
-   priority distribution
-   service distribution
-   incident table

Filters:

-   date
-   priority
-   status
-   service
-   SLA

Detail drawer/page:

-   incident ID
-   description
-   timeline
-   status
-   priority
-   service
-   related problem
-   related change
-   SLA
-   resolution notes

------------------------------------------------------------------------

# 21. PROBLEM MODULE

Include:

-   total problems
-   open problems
-   resolved problems
-   backlog
-   average age
-   oldest problem
-   recurring incidents

Show:

-   service distribution
-   priority distribution
-   aging distribution

Detail:

-   problem
-   root cause
-   known error
-   related incidents
-   related changes
-   service

------------------------------------------------------------------------

# 22. CHANGE MODULE

Include:

-   total changes
-   successful
-   failed
-   rolled back
-   emergency
-   success rate
-   failure rate
-   change-related incidents

Show risk distribution.

Detail:

``` text
Change
 |
 +-- Service
 |
 +-- Related incidents
 |
 +-- Related problem
 |
 +-- Outcome
 |
 +-- Risk
```

------------------------------------------------------------------------

# 23. SERVICE MODULE

Service table/cards:

-   service name
-   criticality
-   availability
-   SLA
-   incident count
-   P1 count
-   problems
-   changes
-   health

Click service for detailed operational view.

------------------------------------------------------------------------

# 24. AI INSIGHTS

Create a dedicated AI Insights page.

Every insight must contain:

-   title
-   severity
-   description
-   confidence
-   evidence
-   affected service
-   recommendation

Example:

``` text
AI INSIGHT

Payment Service showing abnormal incident activity.

Confidence: 89%

Evidence:
- Incident volume +42%
- SLA breaches +17%
- 3 related changes
- 2 recurring problem records

Recommendation:
Review recent changes and prioritize PRB-102.
```

------------------------------------------------------------------------

# 25. AI ASSISTANT

This is a required feature.

Create an interactive AI assistant accessible from the dashboard.

UI:

``` text
Ask Operations AI...

Examples:
"Why did incidents increase this week?"
"Which service is at highest risk?"
"What caused the SLA decline?"
"Summarize this month's operations."
"Which changes are associated with incidents?"
"Show me the worst performing services."
```

The assistant must answer using the application's actual data.

------------------------------------------------------------------------

# 26. AI ASSISTANT ARCHITECTURE

Do NOT blindly send the entire database to an LLM.

Use a controlled pipeline:

``` text
User Question
     |
     v
Intent / Query Understanding
     |
     v
Retrieve relevant structured data
     |
     v
Calculate required metrics deterministically
     |
     v
Build evidence context
     |
     v
LLM
     |
     v
Grounded answer
```

The assistant should be able to answer:

-   KPI questions
-   comparison questions
-   trend questions
-   service questions
-   incident questions
-   problem questions
-   change questions
-   report summaries

------------------------------------------------------------------------

# 27. AI GROUNDING

The AI assistant must not invent facts.

Responses should include evidence when useful.

Example:

``` text
Payment Service has the highest operational risk.

Evidence:
- 42 incidents
- 4 P1 incidents
- 92.8% SLA compliance
- 2 failed changes
```

The numbers must originate from backend analytics.

------------------------------------------------------------------------

# 28. AI FALLBACK

If no LLM API key exists:

The platform remains fully functional.

Use deterministic fallback summaries.

Show a transparent status:

``` text
AI provider unavailable.
Showing deterministic operational analysis.
```

Do not pretend a fake LLM response is generated by an external model.

------------------------------------------------------------------------

# 29. AI USAGE BEYOND THE ASSISTANT

AI should also be used automatically for:

1.  Executive summaries
2.  Operational insight generation
3.  Recommendations
4.  Report narrative generation
5.  Optional classification/mapping assistance
6.  Optional anomaly explanation

The system should use AI where it adds value, not for basic arithmetic.

------------------------------------------------------------------------

# 30. OPERATIONS HEALTH INDEX

Implement deterministic OHI.

Initial weighting:

``` text
Incident Health  30%
Problem Health   20%
Change Health    25%
Service Health   15%
SLA Health       10%
```

Normalize each score to 0--100.

Document the exact formula.

Display:

-   score
-   status
-   component scores
-   explanation

------------------------------------------------------------------------

# 31. INCIDENT ANALYTICS

Calculate:

-   total
-   open
-   resolved
-   P1
-   P2
-   MTTR
-   SLA compliance
-   breach rate
-   reopen rate
-   incident trend
-   service concentration

------------------------------------------------------------------------

# 32. PROBLEM ANALYTICS

Calculate:

-   total
-   open
-   resolved
-   backlog
-   average age
-   oldest problem
-   recurring incidents
-   service concentration
-   priority distribution

------------------------------------------------------------------------

# 33. CHANGE ANALYTICS

Calculate:

-   total
-   success
-   failure
-   success rate
-   failure rate
-   emergency changes
-   rollbacks
-   change-related incidents
-   change risk

------------------------------------------------------------------------

# 34. SERVICE ANALYTICS

Calculate:

-   availability
-   incident count
-   P1/P2
-   SLA compliance
-   problem count
-   change count
-   service health

------------------------------------------------------------------------

# 35. SLA ANALYTICS

Calculate:

-   compliance
-   breaches
-   breach rate
-   performance by service
-   performance by priority
-   trend

------------------------------------------------------------------------

# 36. TREND ENGINE

Every major metric should support:

``` text
current
previous
absolute_change
percentage_change
direction
```

Handle zero values safely.

------------------------------------------------------------------------

# 37. ANOMALY ENGINE

V1 can use deterministic statistical detection:

-   threshold rules
-   rolling average
-   z-score
-   percentage deviation

Optional:

-   Isolation Forest

Detect:

-   incident spikes
-   SLA drops
-   change failures
-   service degradation
-   backlog growth

------------------------------------------------------------------------

# 38. CHANGE-INCIDENT ASSOCIATION

Implement basic correlation.

For each change:

-   affected service
-   incidents before
-   incidents after
-   time window
-   potential association score

Do not claim definitive causality.

------------------------------------------------------------------------

# 39. REPORTING SYSTEM

Create a Report Service.

Inputs:

-   report type
-   start date
-   end date

Report types:

-   daily
-   weekly
-   monthly

------------------------------------------------------------------------

# 40. DAILY REPORT

Purpose:

> What requires attention today?

Sections:

1.  Executive Summary
2.  Operations Health
3.  Incident Activity
4.  P1/P2
5.  SLA Breaches
6.  Problem Activity
7.  Change Activity
8.  Service Health
9.  AI Insights
10. Recommended Actions

------------------------------------------------------------------------

# 41. WEEKLY REPORT

Purpose:

> What happened this week and why?

Sections:

1.  Executive Summary
2.  Week-over-week comparison
3.  Incident trends
4.  Problem trends
5.  Change performance
6.  Service health
7.  SLA performance
8.  Recurring issues
9.  Risks
10. AI insights
11. Recommendations

------------------------------------------------------------------------

# 42. MONTHLY REPORT

Purpose:

> What is the operational health of the organization?

Sections:

1.  Executive Summary
2.  Operations Health
3.  KPI scorecard
4.  Incident performance
5.  Problem performance
6.  Change performance
7.  Service availability
8.  SLA performance
9.  Major issues
10. Major trends
11. Operational risks
12. AI insights
13. Recommendations

------------------------------------------------------------------------

# 43. REPORT OUTPUT

Generate:

-   HTML
-   PDF

Reports should be professionally formatted.

Include:

-   OPSINTEL branding
-   reporting period
-   generation timestamp
-   KPI cards
-   charts
-   executive summary
-   insights
-   recommendations
-   footer

Do not create a plain text dump.

------------------------------------------------------------------------

# 44. REPORT HISTORY

Store generated report metadata.

Reports page must show:

-   report type
-   period
-   generated at
-   status
-   size if available
-   view
-   download

------------------------------------------------------------------------

# 45. AUTOMATIC SCHEDULING

Implement APScheduler.

Default schedules should be configurable.

Recommended:

Daily: - every day at a configurable morning time

Weekly: - configurable weekday

Monthly: - configurable day/time

Do not hard-code timezone assumptions.

Use environment/configuration.

------------------------------------------------------------------------

# 46. MANUAL TRIGGERS

Provide UI buttons:

``` text
Generate Daily Report
Generate Weekly Report
Generate Monthly Report
```

These must execute the same pipeline used by the scheduler.

Do not create two separate report-generation implementations.

------------------------------------------------------------------------

# 47. AUTOMATED REPORT PIPELINE

Single reusable service:

``` text
generate_report(report_type, period)
```

Pipeline:

``` text
Load data
↓
Validate data
↓
Calculate KPIs
↓
Calculate trends
↓
Detect anomalies
↓
Build evidence
↓
Generate AI narrative
↓
Generate recommendations
↓
Render HTML
↓
Generate PDF
↓
Validate output
↓
Persist report
```

------------------------------------------------------------------------

# 48. MICROSOFT TEAMS / SLACK AUTOMATION

The user does NOT have Microsoft Graph access.

Therefore do NOT make Microsoft Graph a required dependency.

Design notification/delivery using a webhook-based abstraction.

Create:

``` text
NotificationService
```

with providers conceptually:

``` text
Email
TeamsWebhook
SlackWebhook
```

For V1:

-   implement a generic webhook provider
-   support Microsoft Teams incoming webhook/workflow webhook if
    available in the user's environment
-   support Slack incoming webhook if available
-   keep credentials in environment variables
-   if webhook configuration is absent, reports still generate and
    remain downloadable

The notification system should send a concise message containing:

-   report type
-   period
-   OHI
-   top insight
-   report link/path where available

Do not require Microsoft Graph.

Do not implement Graph authentication.

------------------------------------------------------------------------

# 49. WEBHOOK CONFIGURATION

Provide configuration such as:

``` text
NOTIFICATION_PROVIDER=none|teams|slack|email
TEAMS_WEBHOOK_URL=
SLACK_WEBHOOK_URL=
```

Never expose webhook secrets in frontend code.

Webhook calls must happen server-side.

------------------------------------------------------------------------

# 50. OBSIDIAN AI / KNOWLEDGE SYSTEM

The user wants to use Obsidian AI.

Do NOT make Obsidian a hard dependency for the application runtime.

Instead create a project knowledge vault/export structure that can be
opened in Obsidian.

Create:

``` text
knowledge/
├── 00_Project/
├── 01_Requirements/
├── 02_Architecture/
├── 03_Data/
├── 04_Analytics/
├── 05_AI/
├── 06_Reports/
├── 07_Decisions/
├── 08_Testing/
└── 09_Future/
```

Where practical, generate Markdown files compatible with Obsidian.

Use internal wiki-style links where useful:

``` text
[[Architecture]]
[[KPI Definitions]]
[[Report Specification]]
[[AI Specification]]
```

The application itself must not depend on Obsidian being installed.

Obsidian is the human/AI knowledge-management layer.

------------------------------------------------------------------------

# 51. OBSIDIAN KNOWLEDGE CONTENT

Maintain useful Markdown knowledge files for:

-   project context
-   architecture
-   requirements
-   KPI definitions
-   AI prompts
-   report templates
-   decisions
-   known issues
-   implementation status
-   demo script
-   future roadmap

Do not duplicate conflicting information.

The repository `/docs` remains the technical source of truth.

The `/knowledge` directory is the Obsidian-friendly knowledge
representation.

------------------------------------------------------------------------

# 52. PROJECT MEMORY

Create:

``` text
docs/status/CURRENT_STATE.md
docs/status/PHASE_STATUS.md
docs/status/TEST_STATUS.md
docs/status/NEXT_ACTIONS.md
```

Update after each meaningful implementation milestone.

------------------------------------------------------------------------

# 53. DOCUMENTATION TREE

Mandatory:

``` text
docs/
├── PROJECT_CONTEXT.md
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── DATA_MODEL.md
├── API_CONTRACT.md
├── KPI_DEFINITIONS.md
├── REPORT_SPECIFICATION.md
├── AI_SPECIFICATION.md
├── UI_SPECIFICATION.md
├── INGESTION_SPECIFICATION.md
├── AUTOMATION_SPECIFICATION.md
├── NOTIFICATION_SPECIFICATION.md
├── OBSIDIAN_KNOWLEDGE_SPECIFICATION.md
├── IMPLEMENTATION_PLAN.md
├── TESTING_STRATEGY.md
├── DECISIONS.md
├── CHANGELOG.md
├── KNOWN_ISSUES.md
├── DEMO_SCRIPT.md
├── FUTURE_ROADMAP.md
└── status/
    ├── CURRENT_STATE.md
    ├── PHASE_STATUS.md
    ├── TEST_STATUS.md
    └── NEXT_ACTIONS.md
```

------------------------------------------------------------------------

# 54. API CONTRACT

Implement REST endpoints.

Health:

``` text
GET /api/health
```

Dashboard:

``` text
GET /api/dashboard/summary
GET /api/dashboard/trends
GET /api/dashboard/health
```

Ingestion:

``` text
POST /api/ingestion/upload
GET /api/ingestion/jobs
GET /api/ingestion/jobs/{job_id}
POST /api/ingestion/{job_id}/process
```

Incidents:

``` text
GET /api/incidents
GET /api/incidents/{id}
```

Problems:

``` text
GET /api/problems
GET /api/problems/{id}
```

Changes:

``` text
GET /api/changes
GET /api/changes/{id}
```

Services:

``` text
GET /api/services
GET /api/services/{id}
```

Insights:

``` text
GET /api/insights
GET /api/insights/{id}
```

Assistant:

``` text
POST /api/assistant/query
```

Reports:

``` text
GET /api/reports
GET /api/reports/{id}
POST /api/reports/generate/daily
POST /api/reports/generate/weekly
POST /api/reports/generate/monthly
```

Notifications:

``` text
POST /api/notifications/test
```

Do not expose secrets.

------------------------------------------------------------------------

# 55. FRONTEND API CONTRACT

All dynamic content must originate from API responses.

Never hard-code final dashboard metrics.

Use typed TypeScript models.

Provide:

-   loading state
-   error state
-   empty state

for API-driven components.

------------------------------------------------------------------------

# 56. TABLES

Large tables must use:

-   pagination
-   sorting where useful
-   filtering
-   search

Do not render massive datasets into the DOM.

------------------------------------------------------------------------

# 57. SEARCH

Provide useful search for:

-   incident ID
-   problem ID
-   change ID
-   service name

------------------------------------------------------------------------

# 58. GLOBAL REPORTING PERIOD

Provide period selector:

-   Today
-   Last 7 days
-   Last 30 days
-   This week
-   This month
-   Custom

The selected period should affect relevant dashboard analytics.

------------------------------------------------------------------------

# 59. DASHBOARD AUTO REFRESH

After ingestion completes:

``` text
ingestion complete
↓
analytics refresh
↓
dashboard refresh
```

The user should not need to restart the application.

Provide a visible:

``` text
Last data refresh:
08 Aug 2026 12:15
```

------------------------------------------------------------------------

# 60. REPORT SCHEDULER STATUS

Reports page or settings should show:

``` text
Daily
Enabled
Next run: ...

Weekly
Enabled
Next run: ...

Monthly
Enabled
Next run: ...
```

Allow configuration where practical.

------------------------------------------------------------------------

# 61. SETTINGS

Settings page can include:

-   reporting schedule
-   notification provider
-   AI provider status
-   data source status
-   data refresh
-   application information

Do not put secrets into editable frontend forms unless securely
designed.

------------------------------------------------------------------------

# 62. LOGGING

Implement structured backend logging.

Log:

-   ingestion
-   analytics execution
-   AI execution
-   report generation
-   scheduler
-   notification
-   errors

Do not log secrets.

------------------------------------------------------------------------

# 63. OBSERVABILITY FOR DEMO

Provide a lightweight system status section:

``` text
Data Engine       ONLINE
Analytics         ONLINE
AI                ONLINE/OFFLINE
Report Engine     ONLINE
Scheduler         ONLINE
Notification      CONFIGURED/NOT CONFIGURED
```

------------------------------------------------------------------------

# 64. ERROR HANDLING

Errors must be graceful.

Frontend:

``` text
Unable to load data.
Retry
```

Backend:

structured error response.

Report:

failed report must be marked failed.

Scheduler:

failed execution must be logged.

------------------------------------------------------------------------

# 65. SECURITY

Even though this is a POC:

-   environment variables for secrets
-   `.env.example`
-   `.gitignore`
-   server-side webhook calls
-   server-side AI API calls
-   input validation
-   file type validation
-   file size validation
-   path traversal protection
-   safe filenames
-   report output directory restrictions
-   no API keys in source

------------------------------------------------------------------------

# 66. FILE UPLOAD SECURITY

Validate:

-   extension
-   MIME type where possible
-   file size
-   filename
-   content parsing

Do not execute uploaded files.

Store uploads in a controlled directory.

------------------------------------------------------------------------

# 67. TESTING

Create tests for:

## Data generator

-   deterministic generation
-   valid relationships
-   scenario presence

## Validation

-   invalid columns
-   missing fields
-   invalid IDs
-   invalid dates

## KPI engine

Test known inputs and expected outputs.

## API

Test major endpoints.

## Reports

Test all three report types.

## Scheduler

Test manual scheduler invocation.

## AI

Test fallback mode.

## Notifications

Test disabled/no-provider behavior.

------------------------------------------------------------------------

# 68. BROWSER QA

Actually launch the application.

Inspect every major route:

-   Overview
-   Ingestion
-   Incidents
-   Problems
-   Changes
-   Services
-   AI Insights
-   Reports
-   Settings

Check:

-   console
-   network errors
-   broken charts
-   overflowing components
-   unreadable text
-   layout
-   responsiveness
-   interactions
-   filters
-   upload flow
-   report generation flow

Fix problems rather than simply documenting them.

------------------------------------------------------------------------

# 69. DEMO FLOW

The final demo must work as follows:

## Step 1

Open OPSINTEL.

Show Overview.

## Step 2

Open Data Ingestion.

Upload:

-   incidents.csv
-   problems.csv
-   changes.csv
-   services.csv
-   sla.csv

## Step 3

Show validation.

## Step 4

Process dataset.

## Step 5

Show ingestion completed.

## Step 6

Return to dashboard.

Dashboard now reflects uploaded data.

## Step 7

Show OHI.

## Step 8

Show incident spike.

## Step 9

Show service health.

## Step 10

Show change → incident relationship.

## Step 11

Show problem relationship.

## Step 12

Open AI Insights.

## Step 13

Ask AI Assistant:

> Why did operational health decline?

## Step 14

Ask:

> Which service is at highest risk?

## Step 15

Generate Daily Report.

## Step 16

Show generated PDF.

## Step 17

Generate Weekly Report.

## Step 18

Generate Monthly Report.

## Step 19

Show scheduler configuration.

## Step 20

Trigger notification test if webhook is configured.

This demonstrates the entire POC.

------------------------------------------------------------------------

# 70. FINAL PRESENTATION STORY

The system should tell this story:

``` text
Raw operational data
        ↓
Automated ingestion
        ↓
Data quality
        ↓
Operational metrics
        ↓
Interactive dashboard
        ↓
Pattern detection
        ↓
AI insights
        ↓
AI assistant
        ↓
Executive reporting
        ↓
Automated scheduling
        ↓
Notification
```

The core message:

> We are not simply generating reports. We are creating an automated
> operational intelligence pipeline.

------------------------------------------------------------------------

# 71. PERFORMANCE TARGET

For the demo dataset:

-   dashboard should load quickly
-   ingestion should provide visible progress
-   report generation should provide status
-   API should not block unnecessarily
-   charts should remain responsive

Do not prematurely optimize.

------------------------------------------------------------------------

# 72. ACCESSIBILITY / USABILITY

Use:

-   readable contrast
-   meaningful labels
-   keyboard-friendly controls where practical
-   clear status indicators
-   tooltips for unfamiliar metrics
-   accessible buttons

------------------------------------------------------------------------

# 73. UI MICRO-INTERACTIONS

Use subtle:

-   hover
-   fade
-   slide
-   count-up
-   chart transition
-   status pulse

Avoid excessive animation.

The design must feel premium and professional.

------------------------------------------------------------------------

# 74. REPORT QUALITY

Executive reports must prioritize:

1.  What happened?
2.  Why does it matter?
3.  What changed?
4.  What is at risk?
5.  What should be done?

Do not dump every record into the report.

------------------------------------------------------------------------

# 75. REPORT NARRATIVE

Example structure:

``` text
Executive Summary

Operational health declined from 84 to 78 during the reporting period.
The primary contributors were increased incidents in the Payment
Service and declining change success.

Key findings:
- Incident volume increased 13%.
- SLA compliance declined 1.1 percentage points.
- Two changes were associated with a significant incident increase.

Recommended actions:
1. Review the associated changes.
2. Prioritize the recurring Payment Service problem.
3. Increase monitoring for the affected service.
```

Numbers must be generated from actual analytics.

------------------------------------------------------------------------

# 76. REPORT COMPARISON

Reports should compare against the appropriate previous period.

Daily:

previous day

Weekly:

previous week

Monthly:

previous month

Show:

-   current
-   previous
-   delta
-   direction

------------------------------------------------------------------------

# 77. REPORT CONSISTENCY

The dashboard and reports must use the same analytics engine.

Do not calculate dashboard KPIs differently from report KPIs.

Single source of truth:

``` text
Analytics Engine
```

------------------------------------------------------------------------

# 78. DATA INGESTION AND DASHBOARD CONTRACT

This is one of the most important requirements.

If the user uploads a new dataset:

``` text
Dataset A
↓
Process
↓
Dashboard A
```

Then uploads dataset B:

``` text
Dataset B
↓
Process
↓
Dashboard B
```

The dashboard must actually change.

Do not merely display pre-generated demo numbers.

------------------------------------------------------------------------

# 79. DEMO RESET

Provide a reset/demo-data function.

Example:

``` text
Reset to Demo Dataset
```

This should safely restore the known demonstration scenario.

------------------------------------------------------------------------

# 80. DOCUMENTATION OF ASSUMPTIONS

Whenever an assumption is made:

Document it.

Examples:

-   OHI weighting
-   SLA interpretation
-   change-impact window
-   report schedule defaults
-   synthetic scenario design

------------------------------------------------------------------------

# 81. FUTURE ROADMAP

Document but DO NOT implement:

## V2

-   PostgreSQL production mode
-   ServiceNow integration
-   advanced anomaly detection
-   forecasting
-   semantic incident clustering
-   advanced change risk scoring
-   RAG
-   operational knowledge graph
-   AI report QA agent
-   executive copilot improvements

## V3

-   autonomous ticket creation
-   remediation workflows
-   event-driven architecture
-   Teams/Slack richer integrations
-   predictive incident prevention
-   autonomous operations

------------------------------------------------------------------------

# 82. DEFINITION OF DONE

The project is NOT complete until:

### Data

-   ingestion works
-   validation works
-   synthetic data generator works
-   relationships work

### Analytics

-   all major KPI groups work
-   OHI works
-   trend engine works
-   anomaly engine works

### Frontend

-   dashboard works
-   pages work
-   charts work
-   filters work
-   drill-down works
-   ingestion UI works
-   AI assistant works
-   reports page works

### AI

-   summary works
-   insights work
-   recommendations work
-   assistant works
-   fallback works
-   grounding works

### Reports

-   daily works
-   weekly works
-   monthly works
-   HTML works
-   PDF works
-   history works

### Automation

-   scheduler works
-   manual triggers work
-   notification abstraction works
-   webhook delivery works if configured

### Documentation

All mandatory docs exist and are current.

### QA

-   tests pass
-   browser QA completed
-   no critical runtime errors
-   no critical console errors

------------------------------------------------------------------------

# 83. REQUIRED DOCUMENTATION FILES

At completion ensure these exist:

``` text
docs/PROJECT_CONTEXT.md
docs/REQUIREMENTS.md
docs/ARCHITECTURE.md
docs/DATA_MODEL.md
docs/API_CONTRACT.md
docs/KPI_DEFINITIONS.md
docs/REPORT_SPECIFICATION.md
docs/AI_SPECIFICATION.md
docs/UI_SPECIFICATION.md
docs/INGESTION_SPECIFICATION.md
docs/AUTOMATION_SPECIFICATION.md
docs/NOTIFICATION_SPECIFICATION.md
docs/OBSIDIAN_KNOWLEDGE_SPECIFICATION.md
docs/IMPLEMENTATION_PLAN.md
docs/TESTING_STRATEGY.md
docs/DECISIONS.md
docs/CHANGELOG.md
docs/KNOWN_ISSUES.md
docs/DEMO_SCRIPT.md
docs/FUTURE_ROADMAP.md
```

And:

``` text
docs/status/CURRENT_STATE.md
docs/status/PHASE_STATUS.md
docs/status/TEST_STATUS.md
docs/status/NEXT_ACTIONS.md
```

------------------------------------------------------------------------

# 84. OBSIDIAN KNOWLEDGE FILES

Generate Obsidian-compatible Markdown knowledge files.

Suggested:

``` text
knowledge/00_Project/Project Overview.md
knowledge/01_Requirements/Business Requirement.md
knowledge/02_Architecture/System Architecture.md
knowledge/03_Data/Data Model.md
knowledge/04_Analytics/KPI Catalog.md
knowledge/05_AI/AI Architecture.md
knowledge/06_Reports/Report Design.md
knowledge/07_Decisions/Architecture Decisions.md
knowledge/08_Testing/Testing Strategy.md
knowledge/09_Future/Future Roadmap.md
```

Use wiki links where helpful.

------------------------------------------------------------------------

# 85. PROJECT STATUS SYSTEM

Maintain:

``` text
CURRENT_STATE.md
```

with:

-   current phase
-   completed phases
-   active features
-   known blockers
-   next action

Maintain:

``` text
PHASE_STATUS.md
```

with a table:

Phase Status Completion Notes ------- -------- ------------ -------

Maintain:

``` text
TEST_STATUS.md
```

with:

-   test suite status
-   last run
-   failures
-   browser QA

Maintain:

``` text
NEXT_ACTIONS.md
```

with prioritized actions.

------------------------------------------------------------------------

# 86. ARCHITECTURE DECISION RECORD

For meaningful decisions:

``` text
ADR
Title
Date
Context
Decision
Alternatives
Reason
Trade-offs
```

------------------------------------------------------------------------

# 87. CHANGELOG

Record:

-   feature additions
-   major changes
-   fixes
-   architectural changes
-   report changes
-   AI changes

------------------------------------------------------------------------

# 88. KNOWN ISSUES

Never hide known issues.

Track:

-   issue
-   severity
-   impact
-   workaround
-   planned fix

------------------------------------------------------------------------

# 89. AGENT BEHAVIOR

When implementing:

1.  Inspect existing workspace.
2.  Read this specification.
3.  Read project documentation.
4.  Determine current phase.
5.  Implement the next incomplete requirement.
6.  Run tests.
7.  Run application.
8.  Inspect browser.
9.  Fix errors.
10. Update documentation.
11. Update status.
12. Continue.

Do not rebuild working components unnecessarily.

Do not overwrite user work without checking it first.

------------------------------------------------------------------------

# 90. WHEN EXISTING CODE EXISTS

Before modifying existing files:

-   inspect them
-   understand their purpose
-   preserve working functionality
-   avoid unnecessary rewrites

If the workspace already contains a partial implementation:

Do not blindly delete it.

First assess:

-   what works
-   what is broken
-   what can be reused
-   what conflicts with this specification

Then integrate or refactor.

------------------------------------------------------------------------

# 91. DEPENDENCY MANAGEMENT

Do not install unnecessary libraries.

Before adding a dependency:

Ask:

-   Is it required?
-   Does an existing dependency already solve this?
-   Is it maintained?
-   Does it introduce unnecessary complexity?

Document significant dependencies.

------------------------------------------------------------------------

# 92. STARTUP EXPERIENCE

The final project should ideally support:

``` text
Backend:
uvicorn backend.app.main:app --reload

Frontend:
npm install
npm run dev
```

Adjust commands to the actual repository.

README must contain exact commands.

------------------------------------------------------------------------

# 93. DEMO DATA COMMAND

Provide a simple command such as:

``` text
python scripts/generate_data.py
```

or equivalent.

------------------------------------------------------------------------

# 94. REPORT DEMO COMMAND

Provide commands or API calls for:

``` text
Generate Daily
Generate Weekly
Generate Monthly
```

------------------------------------------------------------------------

# 95. FINAL BUILD VALIDATION

Before declaring completion:

Run the complete end-to-end scenario:

``` text
Generate demo data
↓
Start backend
↓
Start frontend
↓
Open dashboard
↓
Upload/ingest data
↓
Validate
↓
Process
↓
Dashboard refresh
↓
Inspect analytics
↓
Ask AI assistant
↓
Generate daily report
↓
Generate weekly report
↓
Generate monthly report
↓
Inspect generated PDFs
↓
Test scheduler
↓
Test webhook notification if configured
```

If any stage fails, fix it before completion unless an external
credential/service is genuinely unavailable.

------------------------------------------------------------------------

# 96. FINAL REPORT TO USER

At the end of the implementation, provide:

## Executive Summary

What was built.

## Business Requirement Coverage

A checklist/table mapping each requirement.

## Architecture

Final architecture.

## Technology

Actual stack.

## Data

How synthetic data works.

## AI

AI features and provider configuration.

## Reports

Daily/weekly/monthly behavior.

## Automation

Scheduler and notification behavior.

## Obsidian

Knowledge structure.

## Testing

Tests run and results.

## Browser QA

Pages tested.

## Known Limitations

Honest limitations.

## Future Roadmap

V2/V3.

## Run Instructions

Exact commands.

## Demo Instructions

Exact sequence for the presentation.

------------------------------------------------------------------------

# 97. MOST IMPORTANT SUCCESS CRITERION

The user must be able to stand in front of senior stakeholders and
demonstrate:

> "I upload operational ITSM data. The platform processes it
> automatically. The dashboard updates automatically. I can investigate
> incidents, problems, changes and services. AI explains what is
> happening and recommends actions. The system generates daily, weekly
> and monthly executive reports. Those reports can be automatically
> scheduled and delivered through a webhook-based Teams/Slack workflow.
> The entire process is automated."

If the final application cannot demonstrate this story, the POC is
incomplete.

------------------------------------------------------------------------

# 98. FINAL COMMAND

BEGIN BUILD.

Do not merely plan.

Do not stop after scaffolding.

Do not stop after frontend.

Do not stop after backend.

Do not stop after charts.

Do not stop after AI.

Do not stop after reports.

Complete the end-to-end V1.

Use this specification as the source of truth.

Maintain the documentation and project memory throughout the build.

Build a coherent product.

Test it.

Run it.

Inspect it.

Fix it.

Document it.

Then produce the final completion report.

# END OF MASTER BUILD SPECIFICATION
