# OPSINTEL --- FUNCTIONAL REQUIREMENTS & END-TO-END WORKFLOWS

**Document ID:** OPSINTEL-FUNC-002\
**Version:** 1.0\
**Status:** Authoritative Functional Specification\
**Parent:** `01_MASTER_ARCHITECTURE_AND_PRODUCT_BLUEPRINT.md`

------------------------------------------------------------------------

# 1. PURPOSE

This document defines exactly **what OPSINTEL must do** from a user's
perspective and from the system's perspective.

It converts the high-level architecture into:

-   functional requirements;
-   user journeys;
-   screen behavior;
-   workflow states;
-   inputs;
-   outputs;
-   business rules;
-   acceptance criteria;
-   failure behavior;
-   automation behavior;
-   demo behavior.

This document exists specifically to prevent Antigravity from making
assumptions about how the product should behave.

------------------------------------------------------------------------

# 2. PRODUCT OBJECTIVE

OPSINTEL must automate operational reporting across:

-   incidents;
-   problems;
-   changes;
-   services;
-   SLA/service performance.

The POC must demonstrate that a user can provide operational data once
and then allow the system to perform the majority of the reporting
lifecycle automatically.

------------------------------------------------------------------------

# 3. CORE FUNCTIONAL PROMISE

The core workflow is:

``` text
USER
  |
  | Upload operational files
  v
INGESTION
  |
  v
VALIDATION
  |
  v
MAPPING
  |
  v
NORMALIZATION
  |
  v
PROCESSING
  |
  v
ANALYTICS
  |
  +------------------+
  |                  |
  v                  v
DASHBOARD           AI
  |                  |
  |                  v
  |              INSIGHTS
  |                  |
  +---------+--------+
            |
            v
       REPORT ENGINE
            |
      +-----+-----+
      |     |     |
    DAILY WEEKLY MONTHLY
      |     |     |
      +-----+-----+
            |
            v
        SCHEDULER
            |
            v
      NOTIFICATION
```

------------------------------------------------------------------------

# 4. FUNCTIONAL REQUIREMENT PRIORITY

Use these priorities:

-   **P0** = mandatory for POC
-   **P1** = important, implement if practical
-   **P2** = future enhancement

All P0 requirements must be completed before the POC is considered
complete.

------------------------------------------------------------------------

# 5. P0 FUNCTIONAL REQUIREMENTS

## FR-001 --- File Upload

The system SHALL allow users to upload operational files.

Supported:

-   CSV;
-   XLSX;
-   JSON where practical.

The upload interface SHALL support drag-and-drop and file selection.

------------------------------------------------------------------------

## FR-002 --- Multiple File Upload

The user SHALL be able to upload multiple files in one operation.

Example:

``` text
incidents.csv
problems.csv
changes.csv
services.csv
sla.csv
```

------------------------------------------------------------------------

## FR-003 --- Dataset Classification

The system SHALL attempt to identify the dataset type.

Possible types:

``` text
INCIDENT
PROBLEM
CHANGE
SERVICE
SLA
UNKNOWN
```

Classification may use:

-   filename;
-   sheet name;
-   column names;
-   schema similarity.

------------------------------------------------------------------------

## FR-004 --- Classification Confidence

For automatic classification, the system SHOULD display confidence.

Example:

``` text
incidents.xlsx
Detected: Incident
Confidence: 96%
```

If confidence is too low, the system SHALL ask the user to select the
type.

------------------------------------------------------------------------

# 6. UPLOAD WORKFLOW

## User action

User selects files.

## System action

1.  Receive files.
2.  Validate extension.
3.  Validate size.
4.  Generate safe storage names.
5.  Create ingestion job.
6.  Parse files.
7.  Classify datasets.
8.  Present validation/mapping screen.

------------------------------------------------------------------------

# 7. FILE SECURITY REQUIREMENTS

The system SHALL:

-   reject unsupported extensions;
-   enforce configurable maximum file size;
-   sanitize filenames;
-   prevent path traversal;
-   never execute uploaded content;
-   store uploads outside source-code directories.

Secrets SHALL never be stored in uploaded files or logs.

------------------------------------------------------------------------

# 8. COLUMN MAPPING

If source columns differ from the canonical model, the user SHALL see a
mapping interface.

Example:

``` text
Source Column       OPSINTEL Field
----------------------------------
Incident Number     incident_id
Opened              created_at
Closed              resolved_at
Priority            priority
Service             service_id
```

The system SHOULD automatically suggest mappings.

The user SHALL be able to change mappings.

------------------------------------------------------------------------

# 9. REQUIRED MAPPING STATES

``` text
AUTO-MAPPED
USER-CORRECTED
UNMAPPED
INVALID
```

Critical unmapped fields must prevent processing.

Optional fields may produce warnings.

------------------------------------------------------------------------

# 10. VALIDATION WORKFLOW

After mapping:

``` text
Mapped dataset
     |
     v
Schema validation
     |
     v
Type validation
     |
     v
Business validation
     |
     v
Relationship validation
     |
     v
Quality score
```

------------------------------------------------------------------------

# 11. VALIDATION RULES

Validate:

### Structure

-   expected fields;
-   recognized field types.

### Values

-   priority;
-   status;
-   severity;
-   risk;
-   percentages.

### Dates

-   valid format;
-   created \<= resolved;
-   planned start \<= planned end;
-   no impossible negative durations.

### Relationships

-   incident.service exists;
-   problem.service exists;
-   change.service exists;
-   incident.problem exists when populated;
-   incident.change exists when populated.

### Duplicates

Detect duplicate primary IDs.

------------------------------------------------------------------------

# 12. VALIDATION RESULT

Show:

``` text
DATA QUALITY
94 / 100

Rows
5,248

Valid
5,112

Warnings
121

Errors
15
```

Provide expandable details.

------------------------------------------------------------------------

# 13. VALIDATION DECISION

Three possible outcomes:

### PASS

No critical errors.

### PASS WITH WARNINGS

Warnings exist but processing is allowed.

### BLOCKED

Critical errors prevent processing.

The user must understand why processing is blocked.

------------------------------------------------------------------------

# 14. INGESTION JOB

Every upload/process cycle creates a job.

Required fields:

``` text
job_id
status
started_at
completed_at
files_count
rows_read
rows_processed
rows_rejected
warnings
errors
```

------------------------------------------------------------------------

# 15. INGESTION STATUS UI

Show a visible pipeline:

``` text
UPLOAD
  ✓

CLASSIFY
  ✓

VALIDATE
  ✓

NORMALIZE
  ✓

PROCESS
  ●

ANALYZE
  ○

READY
  ○
```

The current stage must be visually obvious.

------------------------------------------------------------------------

# 16. NORMALIZATION

All input datasets must be converted to the canonical OPSINTEL model.

Example:

``` text
External schema
      |
      v
Canonical schema
```

Analytics only operate on canonical data.

------------------------------------------------------------------------

# 17. DEDUPLICATION

The system SHALL detect duplicate records using primary identifiers.

Default behavior:

-   exact duplicate → remove/ignore;
-   conflicting duplicate → flag for review;
-   duplicate with newer update → retain according to documented rule.

The chosen rule must be documented.

------------------------------------------------------------------------

# 18. PROCESSING

Once validation passes:

``` text
Normalize
↓
Deduplicate
↓
Validate relationships
↓
Persist
↓
Refresh analytics
↓
Mark completed
```

Processing should be observable to the user.

------------------------------------------------------------------------

# 19. POST-PROCESS AUTOMATION

After successful processing, the system SHALL automatically:

1.  refresh KPI calculations;
2.  refresh trends;
3.  refresh service health;
4.  refresh anomaly detection;
5.  refresh correlation analysis;
6.  generate/update AI insights;
7.  invalidate stale dashboard cache/state if used;
8.  make updated data available to the dashboard.

The user should not need to restart the application.

------------------------------------------------------------------------

# 20. DASHBOARD REFRESH REQUIREMENT

This is a critical POC requirement.

Example:

``` text
Dataset A
   ↓
Process
   ↓
Dashboard A

Dataset B
   ↓
Process
   ↓
Dashboard B
```

The displayed numbers MUST change according to the processed dataset.

Hard-coded final KPI values are not acceptable.

------------------------------------------------------------------------

# 21. REPORTING PERIODS

Global period options:

``` text
Today
Yesterday
Last 7 Days
Last 30 Days
This Week
Previous Week
This Month
Previous Month
Custom Range
```

The period must be passed to backend analytics.

------------------------------------------------------------------------

# 22. OVERVIEW DASHBOARD REQUIREMENTS

The Overview page SHALL answer:

1.  What is the current operational health?
2.  What changed?
3.  Which KPI moved?
4.  Which services are at risk?
5.  What incidents/problems/changes are driving the situation?
6.  What does AI recommend?

------------------------------------------------------------------------

# 23. OVERVIEW KPI CARDS

Minimum:

``` text
Total Incidents
Open Incidents
P1/P2 Incidents
Problems
Problem Backlog
Changes
Change Success Rate
SLA Compliance
MTTR
Availability
Critical Services
```

Each card SHOULD show:

``` text
Current
Previous
Delta
Direction
Status
```

------------------------------------------------------------------------

# 24. OPERATIONS HEALTH INDEX

Show:

``` text
OHI
82
HEALTHY
```

Also show component scores:

``` text
Incident Health
Problem Health
Change Health
Service Health
SLA Health
```

Clicking the OHI should explain how it was calculated.

------------------------------------------------------------------------

# 25. INCIDENT WORKFLOW

User selects Incidents.

System displays:

-   summary KPIs;
-   trend;
-   priority distribution;
-   service distribution;
-   SLA;
-   incident table.

User can:

-   search;
-   filter;
-   sort;
-   paginate;
-   open detail.

------------------------------------------------------------------------

# 26. INCIDENT DETAIL

Show:

``` text
Incident ID
Priority
Severity
Status
Service
Created
Acknowledged
Resolved
MTTR
SLA
Problem
Change
Description
Resolution
```

Related entities SHALL be clickable where practical.

------------------------------------------------------------------------

# 27. PROBLEM WORKFLOW

User opens Problems.

Display:

-   total;
-   open;
-   resolved;
-   backlog;
-   aging;
-   oldest problem;
-   recurring incidents.

User can:

-   filter;
-   search;
-   open detail.

------------------------------------------------------------------------

# 28. PROBLEM DETAIL

Show:

``` text
Problem ID
Priority
Status
Service
Age
Root Cause
Known Error
Related Incidents
Related Changes
Resolution Notes
```

------------------------------------------------------------------------

# 29. CHANGE WORKFLOW

Display:

-   total changes;
-   success rate;
-   failures;
-   rollbacks;
-   emergency changes;
-   change-related incidents;
-   risk.

------------------------------------------------------------------------

# 30. CHANGE DETAIL

Show:

``` text
Change ID
Type
Risk
Status
Service
Planned Start
Planned End
Completion
Success
Rollback
Related Incidents
Related Problem
```

------------------------------------------------------------------------

# 31. SERVICE WORKFLOW

Service view SHALL show:

``` text
Service
Criticality
Availability
SLA
Incidents
P1/P2
Problems
Changes
Health
```

------------------------------------------------------------------------

# 32. SERVICE DETAIL

Clicking a service should reveal a service-specific operational view.

Example:

``` text
Payment Service

Health: AT RISK

Availability: 98.4%
Incidents: 42
P1: 4
SLA: 92.8%
Open Problems: 3
Changes: 12
Failed Changes: 2
```

------------------------------------------------------------------------

# 33. INTERACTIVE FILTERS

Global filters should include where applicable:

-   date;
-   service;
-   priority;
-   status;
-   criticality;
-   category.

Changing a filter should update relevant visualizations and KPI cards.

------------------------------------------------------------------------

# 34. DRILL-DOWN

A dashboard metric should lead to the records behind it where practical.

Example:

``` text
P1 Incidents = 7
       ↓
click
       ↓
filtered incident list
```

This creates trust in the dashboard.

------------------------------------------------------------------------

# 35. AI INSIGHT GENERATION

After analytics refresh, the system SHALL evaluate whether meaningful
insights exist.

Potential insight categories:

``` text
INCIDENT_SPIKE
SLA_DEGRADATION
SERVICE_RISK
PROBLEM_BACKLOG
CHANGE_RISK
RECURRING_ISSUE
AVAILABILITY_DEGRADATION
```

------------------------------------------------------------------------

# 36. AI INSIGHT FORMAT

Each insight should contain:

``` text
Title
Severity
Description
Confidence
Evidence
Affected Service
Recommendation
Timestamp
```

------------------------------------------------------------------------

# 37. AI INSIGHT EXAMPLE

``` text
Payment Service Incident Spike

Severity:
HIGH

Confidence:
89%

Evidence:
Incident volume increased 42%.
P1 incidents increased from 2 to 4.
SLA compliance declined to 92.8%.
Two recent changes were associated with incident activity.

Recommendation:
Review the two recent changes and prioritize the recurring Payment Service problem.
```

The numerical evidence must come from analytics.

------------------------------------------------------------------------

# 38. AI ASSISTANT

The assistant SHALL be accessible from the main application.

Suggested prompts:

``` text
Why did incidents increase this week?

Which service has the highest operational risk?

Why did SLA compliance decline?

What changed compared with last week?

Which changes are associated with incidents?

Summarize this month's operations.

What should management prioritize?
```

------------------------------------------------------------------------

# 39. AI ASSISTANT RESPONSE CONTRACT

Responses SHOULD contain:

``` text
Answer
Evidence
Reasoning summary
Recommendation
```

Do not expose hidden chain-of-thought.

Provide concise business reasoning instead.

------------------------------------------------------------------------

# 40. AI ASSISTANT FAILURE

If AI is unavailable:

``` text
AI Assistant unavailable.
Showing deterministic operational analysis where possible.
```

Do not show a fabricated LLM answer.

------------------------------------------------------------------------

# 41. REPORT GENERATION

User can manually trigger:

``` text
Generate Daily
Generate Weekly
Generate Monthly
```

The same report service is used by the scheduler.

------------------------------------------------------------------------

# 42. DAILY REPORT

Purpose:

> What needs attention today?

Sections:

1.  Executive Summary
2.  OHI
3.  Incident Activity
4.  P1/P2
5.  SLA Breaches
6.  Problems
7.  Changes
8.  Service Health
9.  AI Insights
10. Recommendations

------------------------------------------------------------------------

# 43. WEEKLY REPORT

Purpose:

> What happened this week and why?

Sections:

1.  Executive Summary
2.  Week-over-week comparison
3.  Incident trends
4.  Problem trends
5.  Change performance
6.  Service health
7.  SLA
8.  Recurring issues
9.  Risks
10. AI Insights
11. Recommendations

------------------------------------------------------------------------

# 44. MONTHLY REPORT

Purpose:

> What is the organization's operational position?

Sections:

1.  Executive Summary
2.  OHI
3.  KPI scorecard
4.  Incident performance
5.  Problem performance
6.  Change performance
7.  Service availability
8.  SLA performance
9.  Major issues
10. Trends
11. Risks
12. AI Insights
13. Recommendations

------------------------------------------------------------------------

# 45. REPORT OUTPUT

Required:

-   HTML;
-   PDF.

Reports must be professional and executive-ready.

------------------------------------------------------------------------

# 46. REPORT HISTORY

The Reports page SHALL display:

``` text
Type
Period
Generated
Status
View
Download
```

Statuses:

``` text
GENERATING
COMPLETED
FAILED
```

------------------------------------------------------------------------

# 47. SCHEDULER

Scheduler must support:

### Daily

Configurable time.

### Weekly

Configurable weekday and time.

### Monthly

Configurable day and time.

Timezone must be configurable.

------------------------------------------------------------------------

# 48. SCHEDULER UI

Display:

``` text
Daily
Enabled
Next Run: ...

Weekly
Enabled
Next Run: ...

Monthly
Enabled
Next Run: ...
```

------------------------------------------------------------------------

# 49. MANUAL DEMO TRIGGER

For the stakeholder demo, the user should NOT wait for a real scheduled
time.

Provide:

``` text
Generate Now
Send Test Notification
```

The explanation should be:

> "The scheduler normally performs this automatically. I'm triggering
> the same workflow manually so you can see the result immediately."

------------------------------------------------------------------------

# 50. SCHEDULER WORKFLOW

``` text
Schedule fires
      ↓
Determine reporting period
      ↓
Run report service
      ↓
Validate report
      ↓
Store report
      ↓
Send notification
      ↓
Record execution
```

------------------------------------------------------------------------

# 51. NOTIFICATION WORKFLOW

If configured:

``` text
Report completed
      ↓
NotificationService
      ↓
Teams / Slack
```

Notification contains:

``` text
Report Type
Period
OHI
Top Insight
Report Reference
```

------------------------------------------------------------------------

# 52. NOTIFICATION FAILURE

If Teams/Slack fails:

``` text
Report = COMPLETED
Notification = FAILED
```

The user can still download the report.

------------------------------------------------------------------------

# 53. DATA SOURCE WORKFLOW

The UI SHALL distinguish current and future sources.

Current:

``` text
Manual Upload
CONNECTED
```

Future:

``` text
ServiceNow
PLANNED
Jira
PLANNED
```

Do not simulate successful live connections.

------------------------------------------------------------------------

# 54. SERVICE NOW FUTURE WORKFLOW

Future conceptual flow:

``` text
Connect ServiceNow
      ↓
Test Connection
      ↓
Authenticate
      ↓
Select datasets
      ↓
Schedule synchronization
      ↓
Automatic ingestion
```

This is future architecture, not a V1 dependency.

------------------------------------------------------------------------

# 55. RESET DEMO DATA

Provide a controlled demo reset.

Action:

``` text
Reset to Demo Dataset
```

Expected behavior:

1.  confirm action;
2.  clear/reset demo data according to defined policy;
3.  regenerate known dataset;
4.  process it;
5.  refresh dashboard;
6.  regenerate baseline insights.

------------------------------------------------------------------------

# 56. EMPTY STATE

If no data exists:

Do not show misleading zeros as if data were processed.

Show:

``` text
No operational data loaded.

Upload your ITSM files to begin.
```

Provide:

``` text
Upload Data
Generate Demo Dataset
```

------------------------------------------------------------------------

# 57. LOADING STATE

For long operations:

Show:

-   current stage;
-   progress where measurable;
-   elapsed time;
-   status.

Do not freeze the interface.

------------------------------------------------------------------------

# 58. ERROR STATE

Errors must explain:

-   what failed;
-   why if known;
-   what the user can do next.

Example:

``` text
Processing failed.

15 rows contain invalid incident dates.

Review validation results and correct the source file.
```

------------------------------------------------------------------------

# 59. API ERROR CONTRACT

Use a consistent error structure.

Conceptually:

``` json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Dataset contains invalid dates.",
    "details": []
  }
}
```

------------------------------------------------------------------------

# 60. SEARCH REQUIREMENTS

Search must support:

-   incident ID;
-   problem ID;
-   change ID;
-   service name.

Search should be server-side for large datasets.

------------------------------------------------------------------------

# 61. TABLE REQUIREMENTS

Tables must support:

-   pagination;
-   search;
-   filtering;
-   sorting where useful;
-   empty state;
-   loading state;
-   error state.

Do not render thousands of records simultaneously if avoidable.

------------------------------------------------------------------------

# 62. REPORT PERIOD CONSISTENCY

Daily:

``` text
current day
vs previous comparable day
```

Weekly:

``` text
current week
vs previous week
```

Monthly:

``` text
current month
vs previous month
```

The period calculation logic must be centralized.

------------------------------------------------------------------------

# 63. REPORT CONSISTENCY

Dashboard and report metrics must originate from the same analytics
service.

A stakeholder should never see:

``` text
Dashboard SLA = 92.8%
Report SLA = 91.4%
```

for the same dataset and period because of duplicate formulas.

------------------------------------------------------------------------

# 64. DEMO DATA REQUIREMENTS

Synthetic data must make the dashboard visually meaningful.

It should contain:

-   healthy services;
-   warning services;
-   critical services;
-   normal incident periods;
-   incident spikes;
-   SLA breaches;
-   problem backlog;
-   successful changes;
-   failed changes;
-   related change/incident patterns.

------------------------------------------------------------------------

# 65. USER JOURNEY --- FIRST RUN

``` text
Open application
      ↓
No data
      ↓
Empty state
      ↓
Generate Demo Data OR Upload Data
      ↓
Validation
      ↓
Processing
      ↓
Dashboard
```

------------------------------------------------------------------------

# 66. USER JOURNEY --- REAL FILE DEMO

``` text
Open application
↓
Data Ingestion
↓
Upload files
↓
Automatic classification
↓
Review mapping
↓
Validation
↓
Process
↓
Processing complete
↓
Dashboard refresh
↓
Investigate
↓
AI analysis
↓
Generate report
↓
Send test notification
```

------------------------------------------------------------------------

# 67. USER JOURNEY --- AUTOMATED REPORT

Normal automated operation:

``` text
Scheduler
↓
Reporting period calculated
↓
Analytics
↓
AI
↓
Report
↓
PDF
↓
Store
↓
Teams/Slack
↓
Execution logged
```

No human interaction is required.

------------------------------------------------------------------------

# 68. USER JOURNEY --- AI ASSISTANT

``` text
User asks question
↓
System interprets question
↓
Retrieves relevant operational metrics
↓
Calculates deterministic values
↓
Builds evidence
↓
AI generates explanation
↓
Assistant returns answer
```

------------------------------------------------------------------------

# 69. USER JOURNEY --- INVESTIGATION

Example:

``` text
Dashboard
 ↓
Payment Service
 ↓
Service detail
 ↓
Incident spike
 ↓
Related changes
 ↓
Related problems
 ↓
AI insight
 ↓
Recommendation
```

This investigation journey should be polished because it is strong for
the stakeholder demo.

------------------------------------------------------------------------

# 70. FUNCTIONAL REQUIREMENT --- NO STATIC DASHBOARD

The final application SHALL NOT depend on static dashboard values.

Any seeded demonstration data must still pass through the same backend
processing path.

------------------------------------------------------------------------

# 71. FUNCTIONAL REQUIREMENT --- NO FAKE AI

If no AI provider is configured, the system must clearly indicate
fallback mode.

It must never pretend that deterministic text came from an LLM.

------------------------------------------------------------------------

# 72. FUNCTIONAL REQUIREMENT --- NO FAKE INTEGRATION

A ServiceNow or Teams integration that is only a UI mock must be
labelled:

``` text
PLANNED
```

or:

``` text
NOT CONFIGURED
```

Never:

``` text
CONNECTED
```

unless the connection was actually established.

------------------------------------------------------------------------

# 73. FUNCTIONAL REQUIREMENT --- AUTOMATION

The POC must demonstrate meaningful automation.

At minimum:

``` text
Automatic processing
Automatic analytics
Automatic AI insight generation
Automatic report generation
Scheduled reports
Automatic notification
```

Manual file upload is the accepted V1 input boundary.

------------------------------------------------------------------------

# 74. FUNCTIONAL REQUIREMENT --- TRACEABILITY

Every major dashboard insight should be traceable to underlying
evidence.

Example:

``` text
AI Insight
   ↓
Evidence
   ↓
KPI
   ↓
Records
```

Where practical, provide a "View Evidence" action.

------------------------------------------------------------------------

# 75. FUNCTIONAL REQUIREMENT --- REPORT TRACEABILITY

Reports should contain:

-   reporting period;
-   generation timestamp;
-   KPI values;
-   source/data refresh context;
-   AI insight evidence where appropriate.

------------------------------------------------------------------------

# 76. FUNCTIONAL REQUIREMENT --- CONFIGURATION

Configuration should be externalized.

Examples:

``` text
DATABASE_URL
AI_PROVIDER
AI_API_KEY
TEAMS_WEBHOOK_URL
SLACK_WEBHOOK_URL
TIMEZONE
UPLOAD_LIMIT
REPORT_OUTPUT_DIR
```

------------------------------------------------------------------------

# 77. P0 ACCEPTANCE CRITERIA

The POC passes functional acceptance only if:

### AC-001

A user can upload ITSM files.

### AC-002

Files are classified.

### AC-003

Columns can be mapped.

### AC-004

Validation works.

### AC-005

Invalid critical data can block processing.

### AC-006

Valid data can be processed.

### AC-007

Dashboard updates from processed data.

### AC-008

Incident analytics work.

### AC-009

Problem analytics work.

### AC-010

Change analytics work.

### AC-011

Service analytics work.

### AC-012

SLA analytics work.

### AC-013

OHI works.

### AC-014

Trends work.

### AC-015

Anomalies work.

### AC-016

Cross-domain relationships work.

### AC-017

AI insights work when configured.

### AC-018

Fallback mode works when AI is unavailable.

### AC-019

AI assistant answers data-grounded questions.

### AC-020

Daily report works.

### AC-021

Weekly report works.

### AC-022

Monthly report works.

### AC-023

PDF output works.

### AC-024

Report history works.

### AC-025

Scheduler works.

### AC-026

Manual report generation works.

### AC-027

Teams/Slack notification works when configured.

### AC-028

Notification failure does not destroy report generation.

### AC-029

Demo dataset can be generated.

### AC-030

Complete demo journey can be performed without restarting the
application.

------------------------------------------------------------------------

# 78. P1 REQUIREMENTS

If time permits:

-   advanced visual drill-down;
-   saved dashboard filters;
-   richer notification formatting;
-   AI-assisted column mapping;
-   configurable OHI weights;
-   report templates;
-   report preview;
-   richer service dependency visualization.

------------------------------------------------------------------------

# 79. P2 REQUIREMENTS

Future:

-   ServiceNow live synchronization;
-   Jira live synchronization;
-   predictive forecasting;
-   semantic incident clustering;
-   RAG;
-   knowledge graph;
-   autonomous remediation;
-   ticket creation;
-   enterprise authentication;
-   production-grade distributed scheduling.

------------------------------------------------------------------------

# 80. FUNCTIONAL DEFINITION OF DONE

A functional area is complete only when:

``` text
UI exists
+
API exists
+
Backend logic exists
+
Database/storage behavior exists
+
Loading state exists
+
Error state exists
+
Empty state exists
+
Test exists
+
Documentation exists
+
Browser behavior verified
```

------------------------------------------------------------------------

# 81. ANTIGRAVITY IMPLEMENTATION RULE

When implementing a requirement:

1.  identify the requirement ID;
2.  identify affected components;
3.  implement backend behavior;
4.  implement API;
5.  implement frontend;
6.  add tests;
7.  verify browser behavior;
8.  update documentation;
9.  update project status.

Do not implement UI-only versions of backend features.

------------------------------------------------------------------------

# 82. FINAL FUNCTIONAL FLOW

The canonical POC workflow is:

``` text
             ┌───────────────┐
             │     USER      │
             └───────┬───────┘
                     │
                     ▼
              Upload ITSM Files
                     │
                     ▼
               Classification
                     │
                     ▼
                Column Mapping
                     │
                     ▼
                  Validation
                     │
             ┌───────┴────────┐
             │                │
          BLOCKED             PASS
             │                │
             ▼                ▼
          Fix Data        Normalize
                              │
                              ▼
                          Deduplicate
                              │
                              ▼
                           Persist
                              │
                              ▼
                           Analyze
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
           KPIs             Trends          Anomalies
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                        AI Evidence
                              │
                              ▼
                         AI Insights
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
             Dashboard                AI Assistant
                 │                         │
                 └────────────┬────────────┘
                              ▼
                        Report Engine
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                  DAILY     WEEKLY    MONTHLY
                    │         │         │
                    └─────────┼─────────┘
                              ▼
                           Storage
                              │
                              ▼
                          Scheduler
                              │
                              ▼
                       Notification
                        /         \
                     Teams       Slack
```

------------------------------------------------------------------------

# 83. FINAL PRODUCT EXPERIENCE

The stakeholder should experience OPSINTEL as:

> "I provide the operational data. The platform does the reporting
> work."

That is the heart of the POC.

The user should not have to:

-   manually calculate KPIs;
-   manually prepare charts;
-   manually write the executive summary;
-   manually repeat the report every week;
-   manually remember the monthly report;
-   manually recreate the same analysis.

The platform automates those activities.

------------------------------------------------------------------------

# 84. DOCUMENT AUTHORITY

This document is the authoritative functional specification.

The next modules must expand the behavior defined here.

Next:

``` text
03_UI_UX_AND_DASHBOARD_SPECIFICATION.md
```

which will define the dashboard at component level, including:

-   exact page structure;
-   layout;
-   visual hierarchy;
-   colors;
-   typography;
-   charts;
-   interactions;
-   states;
-   responsive behavior;
-   animations;
-   component behavior;
-   data shown by every visualization.

# END OF OPSINTEL FUNCTIONAL REQUIREMENTS & END-TO-END WORKFLOWS
