# OPSINTEL --- DATA, INGESTION, ANALYTICS & KPI SPECIFICATION

**Document ID:** OPSINTEL-DATA-004\
**Version:** 1.0\
**Status:** Authoritative Data & Analytics Specification\
**Parent:** `01_MASTER_ARCHITECTURE_AND_PRODUCT_BLUEPRINT.md`\
**Functional Parent:** `02_FUNCTIONAL_REQUIREMENTS_AND_WORKFLOWS.md`\
**UI Parent:** `03_UI_UX_AND_DASHBOARD_SPECIFICATION.md`

------------------------------------------------------------------------

# 0. DOCUMENT PURPOSE

This document removes ambiguity from the data and analytics layer.

Antigravity MUST NOT invent:

-   data schemas;
-   KPI formulas;
-   status mappings;
-   SLA calculations;
-   OHI weights;
-   anomaly definitions;
-   trend definitions;
-   relationship logic;
-   synthetic data behavior.

If a requirement is not explicitly defined here, the implementation
agent must first look for an existing project decision/documentation
entry before making a new architectural decision.

If still undefined, the agent must document the assumption in
`DECISIONS.md` and keep the implementation configurable rather than
silently hard-coding an arbitrary rule.

------------------------------------------------------------------------

# 1. DATA ARCHITECTURE

The canonical pipeline is:

``` text
SOURCE FILE
   ↓
PARSER
   ↓
CLASSIFIER
   ↓
COLUMN MAPPER
   ↓
VALIDATOR
   ↓
NORMALIZER
   ↓
DEDUPLICATOR
   ↓
RELATIONSHIP VALIDATOR
   ↓
CANONICAL DATA MODEL
   ↓
DATABASE
   ↓
ANALYTICS ENGINE
   ↓
KPI / TREND / ANOMALY / CORRELATION
   ↓
EVIDENCE MODEL
   ↓
DASHBOARD / AI / REPORTS
```

No dashboard, report, or AI feature should bypass the canonical
analytics layer.

------------------------------------------------------------------------

# 2. DATA SOURCE STRATEGY

## V1 implemented source

Manual file upload.

Supported:

-   CSV;
-   XLSX;
-   JSON where practical.

## Future sources

-   ServiceNow;
-   Jira;
-   REST API;
-   database;
-   other ITSM tools.

Future integrations must implement the same canonical data contract.

------------------------------------------------------------------------

# 3. CANONICAL DATA DOMAINS

OPSINTEL uses five primary domains:

``` text
Incident
Problem
Change
Service
SLA
```

Optional supporting entities:

``` text
AssignmentGroup
Category
BusinessUnit
DataSource
IngestionJob
Report
AIInsight
```

------------------------------------------------------------------------

# 4. CANONICAL ID RULES

Every primary business entity must have a stable identifier.

Examples:

``` text
INC0012345
PRB001245
CHG001981
SVC_PAYMENT
SLA00123
```

IDs are stored as strings.

Do not convert IDs to integers.

Preserve leading zeroes.

------------------------------------------------------------------------

# 5. INCIDENT CANONICAL SCHEMA

Required:

``` text
incident_id: string
service_id: string
priority: enum/string
status: enum/string
created_at: datetime
```

Recommended:

``` text
severity
category
subcategory
acknowledged_at
resolved_at
resolution_time_hours
sla_target_hours
sla_status
reopened
assignment_group
problem_id
change_id
description
resolution_notes
```

------------------------------------------------------------------------

# 6. INCIDENT FIELD DEFINITIONS

## incident_id

Unique incident identifier.

Required.

## service_id

Canonical service reference.

Required for service analytics.

## priority

Normalized:

``` text
P1
P2
P3
P4
```

If source uses numeric priority, map it using a configurable mapping.

## status

Normalize source states to:

``` text
OPEN
IN_PROGRESS
PENDING
RESOLVED
CLOSED
CANCELLED
```

Unknown states must be retained as source values and flagged.

## created_at

Incident creation timestamp.

Required.

## acknowledged_at

Timestamp when incident was acknowledged.

Optional.

## resolved_at

Resolution timestamp.

Required for resolved incident MTTR calculation.

## resolution_time_hours

Prefer calculated value from timestamps.

Do not trust a source-provided value if it contradicts timestamps unless
explicitly configured.

------------------------------------------------------------------------

# 7. PROBLEM CANONICAL SCHEMA

Required:

``` text
problem_id
service_id
status
created_at
```

Recommended:

``` text
priority
resolved_at
age_days
root_cause
known_error
incident_count
description
resolution_notes
```

------------------------------------------------------------------------

# 8. PROBLEM STATUS

Normalize to:

``` text
OPEN
INVESTIGATING
KNOWN_ERROR
RESOLVED
CLOSED
CANCELLED
```

------------------------------------------------------------------------

# 9. CHANGE CANONICAL SCHEMA

Required:

``` text
change_id
service_id
change_type
status
risk_level
created_at
```

Recommended:

``` text
planned_start
planned_end
completed_at
successful
rollback_required
incident_count
description
```

------------------------------------------------------------------------

# 10. CHANGE TYPES

Normalize to:

``` text
STANDARD
NORMAL
EMERGENCY
```

If source contains another type, preserve source value and document the
mapping.

------------------------------------------------------------------------

# 11. CHANGE RISK

Normalize to:

``` text
LOW
MEDIUM
HIGH
CRITICAL
```

------------------------------------------------------------------------

# 12. CHANGE SUCCESS DEFINITION

A change is successful when:

``` text
successful = true
AND
rollback_required = false
```

If the source provides an authoritative success state, use it after
normalization.

If success cannot be determined, classify as:

``` text
UNKNOWN
```

Unknown changes must not silently count as successful.

------------------------------------------------------------------------

# 13. SERVICE SCHEMA

Required:

``` text
service_id
service_name
criticality
```

Recommended:

``` text
service_category
owner
availability
sla_target
health_status
```

------------------------------------------------------------------------

# 14. SERVICE CRITICALITY

Normalize to:

``` text
CRITICAL
HIGH
MEDIUM
LOW
```

Criticality affects risk visualization and OHI weighting where
specified.

------------------------------------------------------------------------

# 15. SLA SCHEMA

Required:

``` text
sla_id
service_id
target_hours
actual_hours
breached
```

Recommended:

``` text
incident_id
breach_reason
```

------------------------------------------------------------------------

# 16. SLA COMPLIANCE FORMULA

For a defined reporting period:

``` text
SLA Compliance %
=
(number of SLA-compliant records / total applicable SLA records) × 100
```

Example:

``` text
950 compliant
50 breached

950 / 1000 × 100
= 95%
```

If there are zero applicable SLA records:

``` text
N/A
```

Do not return 100%.

------------------------------------------------------------------------

# 17. INCIDENT METRICS

Required incident metrics:

``` text
Total Incidents
Open Incidents
Resolved Incidents
P1 Incidents
P2 Incidents
MTTR
SLA Compliance
SLA Breach Rate
Reopen Rate
```

------------------------------------------------------------------------

# 18. INCIDENT COUNT

For period P:

``` text
Incident Count =
number of incidents created during P
```

Do not mix created-date and resolved-date logic.

The UI must identify the period basis.

------------------------------------------------------------------------

# 19. OPEN INCIDENTS

At an as-of timestamp:

``` text
created_at <= as_of
AND
(resolved_at is null OR resolved_at > as_of)
```

Use the same as-of definition consistently.

------------------------------------------------------------------------

# 20. P1/P2 COUNT

``` text
P1/P2 =
priority IN (P1, P2)
```

------------------------------------------------------------------------

# 21. MTTR

Mean Time To Resolve:

``` text
MTTR =
sum(resolved_at - created_at)
/
number of resolved incidents
```

Express in hours.

Only resolved incidents in the reporting population count.

------------------------------------------------------------------------

# 22. MTTR EDGE CASES

If:

``` text
resolved incident count = 0
```

return:

``` text
N/A
```

Do not return zero.

If resolved_at \< created_at:

-   flag data quality error;
-   exclude the record from MTTR;
-   report the exclusion.

------------------------------------------------------------------------

# 23. MEDIAN RESOLUTION TIME

Recommended additional metric:

``` text
Median Time To Resolve
```

Median is useful because MTTR can be distorted by extreme incidents.

------------------------------------------------------------------------

# 24. REOPEN RATE

``` text
Reopen Rate =
reopened incidents / resolved incidents × 100
```

If no resolved incidents:

``` text
N/A
```

------------------------------------------------------------------------

# 25. PROBLEM METRICS

Required:

``` text
Total Problems
Open Problems
Resolved Problems
Problem Backlog
Average Problem Age
Oldest Problem
Recurring Problem Count
```

------------------------------------------------------------------------

# 26. PROBLEM BACKLOG

At as-of date:

``` text
status NOT IN (RESOLVED, CLOSED, CANCELLED)
```

and:

``` text
created_at <= as_of
```

------------------------------------------------------------------------

# 27. PROBLEM AGE

For an open problem:

``` text
age_days =
as_of - created_at
```

For resolved problems:

``` text
age_days =
resolved_at - created_at
```

------------------------------------------------------------------------

# 28. CHANGE METRICS

Required:

``` text
Total Changes
Successful Changes
Failed Changes
Change Success Rate
Rollback Count
Emergency Changes
Change-Associated Incidents
```

------------------------------------------------------------------------

# 29. CHANGE SUCCESS RATE

``` text
Change Success Rate =
successful changes / completed/evaluable changes × 100
```

Unknown outcomes must be excluded from the denominator.

------------------------------------------------------------------------

# 30. ROLLBACK RATE

``` text
Rollback Rate =
rollback changes / completed/evaluable changes × 100
```

------------------------------------------------------------------------

# 31. EMERGENCY CHANGE RATE

``` text
Emergency Change Rate =
emergency changes / total changes × 100
```

------------------------------------------------------------------------

# 32. CHANGE-ASSOCIATED INCIDENT

An incident may be considered potentially associated with a change when:

1.  both reference the same service;
2.  the change has a known timestamp;
3.  incident creation occurs within a configurable window around the
    change.

Default demonstration window:

``` text
change completion
to
+24 hours
```

Optional broader analysis:

``` text
-2 hours to +24 hours
```

The result MUST be labelled:

``` text
Potentially Associated
```

not:

``` text
Caused By
```

unless stronger causal evidence exists.

------------------------------------------------------------------------

# 33. SERVICE METRICS

Required:

``` text
Availability
Incident Count
P1/P2 Count
SLA Compliance
Problem Count
Change Count
Failed Change Count
```

------------------------------------------------------------------------

# 34. AVAILABILITY

If service downtime is available:

``` text
Availability % =
((total period duration - downtime) / total period duration) × 100
```

If only incident-derived availability is available, document the
approximation.

Never silently present an approximation as authoritative availability.

------------------------------------------------------------------------

# 35. SLA BREACH RATE

``` text
SLA Breach Rate =
breached records / applicable records × 100
```

------------------------------------------------------------------------

# 36. TREND CALCULATION

Every major KPI must support:

``` text
current
previous
absolute_delta
percentage_delta
direction
```

Direction:

``` text
UP
DOWN
FLAT
```

------------------------------------------------------------------------

# 37. FAVORABLE VS UNFAVORABLE TREND

Do not assume every increase is good.

Examples:

``` text
Incident Count ↑ = usually unfavorable
SLA Compliance ↑ = favorable
Availability ↑ = favorable
Change Success ↑ = favorable
Problem Backlog ↑ = unfavorable
```

The analytics layer should define a `trend_polarity`.

------------------------------------------------------------------------

# 38. PERCENTAGE CHANGE

For previous value P and current value C:

``` text
((C - P) / P) × 100
```

If P = 0:

-   if C = 0 → 0%;
-   if C \> 0 → N/A or "new activity".

Do not produce Infinity.

------------------------------------------------------------------------

# 39. TREND PERIOD CONSISTENCY

Daily reports compare:

``` text
current day
vs comparable previous day
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

The period utility must be centralized.

------------------------------------------------------------------------

# 40. ANOMALY DETECTION

V1 should prioritize explainability.

Preferred methods:

1.  threshold;
2.  rolling baseline;
3.  percentage deviation;
4.  z-score where enough history exists.

Advanced models are optional.

------------------------------------------------------------------------

# 41. SIMPLE INCIDENT ANOMALY RULE

Example configurable rule:

``` text
current period incident volume >
rolling baseline × 1.25
```

then:

``` text
ANOMALY = TRUE
```

The threshold must be configurable.

------------------------------------------------------------------------

# 42. Z-SCORE RULE

Where sufficient historical observations exist:

``` text
z = (current - mean) / standard_deviation
```

Potential anomaly:

``` text
abs(z) >= 2
```

Use a higher threshold such as 3 for stricter detection if appropriate.

------------------------------------------------------------------------

# 43. ANOMALY OUTPUT

Each anomaly should contain:

``` text
metric
entity
period
observed_value
expected_value
deviation
severity
method
evidence
```

Example:

``` text
Payment Service
Incidents
Observed: 42
Expected: 28
Deviation: +50%
Severity: HIGH
Method: Rolling Baseline
```

------------------------------------------------------------------------

# 44. CORRELATION ENGINE

The correlation engine identifies relationships between:

``` text
Change
Incident
Problem
Service
```

It should consider:

-   shared service;
-   time proximity;
-   categorical similarity;
-   repeated relationships.

------------------------------------------------------------------------

# 45. CORRELATION SCORE

Optional score:

``` text
0–100
```

Based on configurable factors.

Example:

``` text
Service Match       40%
Temporal Proximity  40%
Category Similarity 20%
```

This is an analytical association score, not probability of causation.

------------------------------------------------------------------------

# 46. RECURRING INCIDENT LOGIC

An issue can be considered recurring when multiple incidents share:

-   service;
-   category/subcategory;
-   similarity signal;
-   configurable time window.

V1 may use deterministic grouping rather than semantic AI.

Example:

``` text
same service
+
same category
+
within 30 days
+
>= 3 incidents
```

→ recurring pattern.

------------------------------------------------------------------------

# 47. OHI ARCHITECTURE

OHI = Operations Health Index.

Initial weights:

``` text
Incident Health     30%
Problem Health      20%
Change Health       25%
Service Health      15%
SLA Health          10%
```

Total:

``` text
100%
```

Weights must be configurable.

------------------------------------------------------------------------

# 48. INCIDENT HEALTH SCORE

Example normalized factors:

``` text
Incident volume trend
P1/P2 ratio
MTTR
SLA breach rate
```

Higher operational performance = higher score.

The exact component formula must be implemented in one central scoring
function.

------------------------------------------------------------------------

# 49. PROBLEM HEALTH SCORE

Consider:

``` text
Backlog
Average age
Critical problems
Recurring problems
```

Lower backlog/risk = higher score.

------------------------------------------------------------------------

# 50. CHANGE HEALTH SCORE

Consider:

``` text
Change success rate
Rollback rate
Emergency change rate
Change-associated incidents
```

Higher success and lower risk = higher score.

------------------------------------------------------------------------

# 51. SERVICE HEALTH SCORE

Consider:

``` text
Availability
SLA compliance
Incident severity
Problem count
```

Higher health = higher score.

------------------------------------------------------------------------

# 52. SLA HEALTH SCORE

Use:

``` text
SLA compliance
```

and optionally:

``` text
breach severity
```

------------------------------------------------------------------------

# 53. OHI NORMALIZATION

All components must be normalized to:

``` text
0–100
```

Final:

``` text
OHI =
IncidentScore × 0.30
+
ProblemScore × 0.20
+
ChangeScore × 0.25
+
ServiceScore × 0.15
+
SLAScore × 0.10
```

Round only for display.

Keep higher precision internally.

------------------------------------------------------------------------

# 54. OHI STATUS

Default:

``` text
90–100  EXCELLENT
80–89   HEALTHY
70–79   WATCH
50–69   ATTENTION REQUIRED
0–49    CRITICAL
```

Thresholds must be configurable.

------------------------------------------------------------------------

# 55. DATA QUALITY SCORE

Suggested model:

``` text
100
- missing required fields penalty
- invalid value penalty
- relationship penalty
- duplicate penalty
- timeline penalty
```

The implementation must document exact penalty weights.

Do not make the quality score random.

------------------------------------------------------------------------

# 56. DATA QUALITY OUTPUT

``` json
{
  "score": 94,
  "rows_total": 5248,
  "rows_valid": 5112,
  "rows_warning": 121,
  "rows_error": 15
}
```

------------------------------------------------------------------------

# 57. DATA QUALITY SEVERITY

``` text
90–100 Excellent
75–89 Good
60–74 Fair
40–59 Poor
0–39 Critical
```

These thresholds are configurable.

------------------------------------------------------------------------

# 58. DATA QUALITY WARNINGS

Examples:

``` text
Optional service owner missing.
Unknown category mapped to OTHER.
Unknown priority retained.
```

Warnings do not necessarily block processing.

------------------------------------------------------------------------

# 59. DATA QUALITY ERRORS

Examples:

``` text
Missing incident_id.
Duplicate primary key conflict.
resolved_at earlier than created_at.
Invalid required date.
```

Critical errors block processing.

------------------------------------------------------------------------

# 60. UNKNOWN VALUES

Never silently discard unknown source values.

Example:

``` text
source_status = "Waiting Vendor"
```

If not mapped:

``` text
normalized_status = UNKNOWN
source_status = "Waiting Vendor"
```

Record a warning.

------------------------------------------------------------------------

# 61. SOURCE VALUE MAPPING

Mappings should be configuration-driven where practical.

Example:

``` json
{
  "P1": "P1",
  "Critical": "P1",
  "1 - Critical": "P1"
}
```

Do not scatter mappings throughout code.

------------------------------------------------------------------------

# 62. DATE HANDLING

All timestamps must be normalized internally.

Recommended:

``` text
UTC storage
configured display timezone
```

If timezone is absent:

-   assume configured source timezone;
-   record assumption;
-   avoid silently mixing timezones.

------------------------------------------------------------------------

# 63. REPORTING TIMEZONE

Scheduler and report periods must use a configured timezone.

The UI must display the active timezone.

------------------------------------------------------------------------

# 64. NULL HANDLING

Do not convert missing numeric values to zero automatically.

Examples:

``` text
unknown SLA = N/A
unknown availability = N/A
unknown MTTR = N/A
```

Zero means an actual zero.

------------------------------------------------------------------------

# 65. METRIC STATUS

Every metric should conceptually support:

``` text
VALUE
N/A
INSUFFICIENT_DATA
ERROR
```

This prevents misleading dashboards.

------------------------------------------------------------------------

# 66. DATA SNAPSHOT

After successful processing, create a dataset snapshot/version.

Conceptually:

``` text
dataset_version
processed_at
source_files
record_counts
data_quality_score
```

This supports reproducibility.

------------------------------------------------------------------------

# 67. DASHBOARD DATA CONTRACT

The analytics API should return structured snapshots.

Example:

``` json
{
  "period": {
    "start": "2026-08-01",
    "end": "2026-08-08"
  },
  "ohi": {
    "score": 82.4,
    "status": "HEALTHY",
    "delta": 3.2
  },
  "incidents": {
    "total": 1248,
    "p1": 4,
    "p2": 31,
    "mttr_hours": 7.4
  }
}
```

------------------------------------------------------------------------

# 68. ANALYTICS CACHE

Caching is optional in V1.

If implemented, cache keys must include:

``` text
dataset_version
period
filters
metric
```

Stale cache must be invalidated after successful ingestion.

------------------------------------------------------------------------

# 69. SYNTHETIC DATA GENERATOR

The generator is mandatory for the POC.

Location:

``` text
scripts/generate_data.py
```

It must support:

``` text
--seed
--days
--services
--incidents
--problems
--changes
```

where practical.

------------------------------------------------------------------------

# 70. DETERMINISTIC DATA

Given the same:

``` text
seed
configuration
```

the generator should produce the same dataset.

This makes testing reproducible.

------------------------------------------------------------------------

# 71. SYNTHETIC SERVICES

Create approximately:

``` text
20 services
```

Mix:

``` text
Critical
High
Medium
Low
```

Example services:

``` text
Payment
Authentication
Order Management
Customer Portal
Notification
Data Platform
API Gateway
Billing
Reporting
Identity
```

Names should remain clearly synthetic.

------------------------------------------------------------------------

# 72. SYNTHETIC INCIDENT DISTRIBUTION

Generate realistic distributions:

-   many P3/P4;
-   fewer P2;
-   rare P1;
-   different service volumes;
-   realistic resolution durations;
-   realistic open/closed ratios.

Do not make every service identical.

------------------------------------------------------------------------

# 73. SYNTHETIC PROBLEM DISTRIBUTION

Create:

-   open problems;
-   resolved problems;
-   older problems;
-   recurring problems;
-   critical problems.

Problem backlog must be visible.

------------------------------------------------------------------------

# 74. SYNTHETIC CHANGE DISTRIBUTION

Create:

-   standard changes;
-   normal changes;
-   emergency changes;
-   successful changes;
-   failed changes;
-   rollback cases.

Change success should be high but imperfect.

------------------------------------------------------------------------

# 75. SYNTHETIC SLA DATA

Create:

-   compliant cases;
-   breached cases;
-   service-specific variation;
-   more breaches in intentionally degraded services.

------------------------------------------------------------------------

# 76. SCENARIO INJECTION

The generator must support explicit scenarios.

Example:

``` text
scenario=payment_spike
scenario=service_degradation
scenario=change_incident_cluster
scenario=problem_backlog
```

These scenarios should affect the generated records.

------------------------------------------------------------------------

# 77. DEMO SCENARIO --- PAYMENT SPIKE

Generate:

-   increased incidents;
-   some P1/P2;
-   reduced SLA;
-   recent changes;
-   associated problem activity.

The analytics engine should discover the situation.

------------------------------------------------------------------------

# 78. DEMO SCENARIO --- CHANGE IMPACT

Generate:

``` text
Change completed
      ↓
incident volume increases
      ↓
same service
      ↓
time proximity
```

The correlation engine should identify it.

------------------------------------------------------------------------

# 79. DEMO SCENARIO --- PROBLEM RECURRENCE

Generate multiple incidents with:

-   same service;
-   same category;
-   similar pattern;
-   short time intervals.

The recurring-pattern logic should detect the cluster.

------------------------------------------------------------------------

# 80. DEMO SCENARIO --- SLA DEGRADATION

Generate:

-   increased resolution times;
-   increased breaches;
-   critical service impact.

This should affect:

``` text
SLA score
Service score
OHI
AI insights
```

------------------------------------------------------------------------

# 81. ANALYTICS TEST DATA

Keep a small fixed dataset for unit tests.

Example:

``` text
tests/fixtures/
```

It should include known values where expected outputs can be calculated
manually.

------------------------------------------------------------------------

# 82. KPI UNIT TEST REQUIREMENTS

Every KPI function must have tests for:

-   normal data;
-   empty data;
-   zero denominator;
-   missing data;
-   invalid data;
-   boundary values;
-   period filtering.

------------------------------------------------------------------------

# 83. OHI TEST REQUIREMENTS

Test:

-   all 100 scores;
-   all 0 scores;
-   mixed scores;
-   threshold boundaries;
-   configurable weights;
-   missing component score.

------------------------------------------------------------------------

# 84. TREND TEST REQUIREMENTS

Test:

``` text
100 → 120 = +20%
100 → 80 = -20%
0 → 10 = N/A/new activity
0 → 0 = 0%
```

------------------------------------------------------------------------

# 85. ANOMALY TEST REQUIREMENTS

Test:

-   no anomaly;
-   threshold breach;
-   exactly at threshold;
-   insufficient history;
-   zero standard deviation.

------------------------------------------------------------------------

# 86. CORRELATION TEST REQUIREMENTS

Test:

-   same service + close time;
-   same service + distant time;
-   different service;
-   missing timestamps;
-   missing service.

------------------------------------------------------------------------

# 87. PERIOD TEST REQUIREMENTS

Test:

-   day boundaries;
-   week boundaries;
-   month boundaries;
-   leap year where applicable;
-   timezone boundaries.

------------------------------------------------------------------------

# 88. DATA VERSIONING REQUIREMENT

Every processed dataset should be associated with a version/snapshot
identifier.

Example:

``` text
DATASET-20260808-001
```

Reports should record the dataset version used.

------------------------------------------------------------------------

# 89. REPORT REPRODUCIBILITY

Given:

``` text
dataset_version
report_type
period
configuration
```

the system should be able to reproduce the underlying metrics.

------------------------------------------------------------------------

# 90. AI EVIDENCE CONTRACT

AI should receive evidence such as:

``` json
{
  "period": {},
  "kpis": {},
  "trends": [],
  "anomalies": [],
  "service_risks": [],
  "change_correlations": [],
  "problem_patterns": []
}
```

The evidence builder is responsible for selecting relevant information.

------------------------------------------------------------------------

# 91. AI MUST NOT RECEIVE RAW EVERYTHING

Do not send the entire database to the LLM by default.

Use:

``` text
question
+
relevant evidence
```

This improves:

-   cost;
-   latency;
-   accuracy;
-   privacy;
-   grounding.

------------------------------------------------------------------------

# 92. METRIC CATALOG

The implementation must maintain a machine-readable and human-readable
KPI catalog.

Suggested:

``` text
docs/KPI_DEFINITIONS.md
```

and, where practical:

``` text
backend/analytics/metric_catalog.py
```

The two must remain synchronized.

------------------------------------------------------------------------

# 93. METRIC ID

Each metric should have a stable ID.

Examples:

``` text
INCIDENT_TOTAL
INCIDENT_P1
INCIDENT_MTTR
SLA_COMPLIANCE
CHANGE_SUCCESS_RATE
PROBLEM_BACKLOG
SERVICE_AVAILABILITY
OHI
```

This helps APIs, reports, and AI evidence remain consistent.

------------------------------------------------------------------------

# 94. FILTER CONTRACT

Analytics functions must accept a consistent filter model:

``` text
period
service_ids
priorities
statuses
criticalities
categories
```

Do not create a different filter vocabulary for every page.

------------------------------------------------------------------------

# 95. AGGREGATION RULE

Backend analytics should perform aggregation.

Frontend should receive summarized datasets suitable for visualization.

Do not send thousands of raw records to the browser when a backend
aggregate is sufficient.

------------------------------------------------------------------------

# 96. DATA RETENTION

V1 should keep uploaded and processed data locally unless configured
otherwise.

Retention policy must be configurable.

Do not silently delete operational data.

------------------------------------------------------------------------

# 97. PRIVACY

The POC should be designed assuming uploaded ITSM data may contain
sensitive operational information.

Therefore:

-   do not log record descriptions unnecessarily;
-   do not expose data in client logs;
-   do not send unrelated raw records to AI;
-   keep AI evidence minimal;
-   keep secrets server-side.

------------------------------------------------------------------------

# 98. DATA PIPELINE FAILURE

If parsing fails:

``` text
INGESTION_FAILED
```

If validation fails:

``` text
VALIDATION_FAILED
```

If processing fails:

``` text
PROCESSING_FAILED
```

The job must preserve diagnostic information.

------------------------------------------------------------------------

# 99. PARTIAL PROCESSING

If the implementation supports partial acceptance:

``` text
PARTIAL
```

must clearly show:

``` text
accepted rows
rejected rows
reason
```

Do not silently drop records.

------------------------------------------------------------------------

# 100. DATA CONTRACT GOLDEN RULE

All consumers use canonical data.

``` text
SOURCE
  ↓
CANONICAL
  ↓
EVERYTHING ELSE
```

Do not build separate source-specific analytics.

------------------------------------------------------------------------

# 101. IMPLEMENTATION GOLDEN RULE

If two screens show the same metric:

``` text
same metric ID
same analytics function
same period logic
```

Only presentation can differ.

------------------------------------------------------------------------

# 102. DOCUMENTATION REQUIREMENTS

Whenever a data rule changes, update:

``` text
docs/KPI_DEFINITIONS.md
docs/DATA_MODEL.md
docs/DECISIONS.md
CHANGELOG.md
```

where applicable.

The agent must not change formulas without recording the change.

------------------------------------------------------------------------

# 103. DATA LAYER DEFINITION OF DONE

Data/analytics implementation is complete only when:

-   canonical schemas exist;
-   parser works;
-   mapping works;
-   validation works;
-   normalization works;
-   database persistence works;
-   synthetic generator works;
-   KPI formulas are tested;
-   trends are tested;
-   anomalies are tested;
-   correlations are tested;
-   OHI is tested;
-   API contracts exist;
-   documentation is updated;
-   dashboard consumes the analytics API.

------------------------------------------------------------------------

# 104. ACCEPTANCE CRITERIA

### DATA-001

CSV upload works.

### DATA-002

XLSX upload works.

### DATA-003

Files are classified.

### DATA-004

Column mapping works.

### DATA-005

Critical validation errors block processing.

### DATA-006

Warnings do not unnecessarily block valid processing.

### DATA-007

Canonical normalization works.

### DATA-008

Duplicate handling works.

### DATA-009

Relationship validation works.

### DATA-010

Dataset version is recorded.

### DATA-011

Incident metrics are correct.

### DATA-012

Problem metrics are correct.

### DATA-013

Change metrics are correct.

### DATA-014

Service metrics are correct.

### DATA-015

SLA metrics are correct.

### DATA-016

Trend calculations are correct.

### DATA-017

Anomaly detection is deterministic.

### DATA-018

Correlation analysis is deterministic.

### DATA-019

OHI is deterministic.

### DATA-020

Synthetic data is reproducible.

### DATA-021

AI receives structured evidence.

### DATA-022

Dashboard and reports use the same metrics.

------------------------------------------------------------------------

# 105. ANTIGRAVITY EXECUTION RULE

For every metric or analytical feature:

``` text
1. Define metric ID
2. Define business meaning
3. Define formula
4. Define required fields
5. Define edge cases
6. Implement function
7. Add unit tests
8. Add API representation
9. Connect dashboard/report
10. Document it
```

Do not skip directly from a business phrase to UI code.

------------------------------------------------------------------------

# 106. FINAL DATA FLOW

``` text
SOURCE FILE
    ↓
PARSER
    ↓
CLASSIFIER
    ↓
MAPPER
    ↓
VALIDATOR
    ↓
NORMALIZER
    ↓
DEDUPLICATOR
    ↓
RELATIONSHIP CHECK
    ↓
CANONICAL DATABASE
    ↓
DATASET VERSION
    ↓
ANALYTICS ENGINE
    ↓
┌──────────────┬──────────────┬──────────────┬──────────────┐
│              │              │              │              │
KPI ENGINE  TREND ENGINE  ANOMALY ENGINE  CORRELATION
│              │              │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
                    ↓
              EVIDENCE MODEL
                    ↓
       ┌────────────┼────────────┐
       ↓            ↓            ↓
   DASHBOARD       AI          REPORTS
```

------------------------------------------------------------------------

# 107. FINAL DATA PRINCIPLE

OPSINTEL must never be:

> "An AI that guesses what the ITSM data means."

It must be:

> **"A deterministic operational analytics system with AI layered on top
> to explain, summarize, investigate, and recommend."**

That distinction is fundamental to the credibility of the POC.

------------------------------------------------------------------------

# 108. COMPANION DOCUMENTS

Parent:

``` text
01_MASTER_ARCHITECTURE_AND_PRODUCT_BLUEPRINT.md
```

Functional:

``` text
02_FUNCTIONAL_REQUIREMENTS_AND_WORKFLOWS.md
```

UI:

``` text
03_UI_UX_AND_DASHBOARD_SPECIFICATION.md
```

Next:

``` text
05_BACKEND_API_AND_INTEGRATION_SPECIFICATION.md
```

That document will define the backend package structure, service
boundaries, endpoint-by-endpoint contracts, request/response schemas,
error contracts, repositories, scheduler APIs, notification adapters,
future ServiceNow adapter, and integration rules.

# END OF OPSINTEL DATA, INGESTION, ANALYTICS & KPI SPECIFICATION
