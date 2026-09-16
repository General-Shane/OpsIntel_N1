# OPSINTEL --- UI/UX & DASHBOARD DESIGN SPECIFICATION

**Document ID:** OPSINTEL-UI-003\
**Version:** 1.0\
**Status:** Authoritative UI/UX Specification\
**Parent:** `01_MASTER_ARCHITECTURE_AND_PRODUCT_BLUEPRINT.md`\
**Functional Parent:** `02_FUNCTIONAL_REQUIREMENTS_AND_WORKFLOWS.md`

------------------------------------------------------------------------

# 1. PURPOSE

This document defines the visual and interaction contract for OPSINTEL.

It exists to prevent Antigravity from creating a generic dashboard.

The interface must feel like a **premium enterprise Operations
Intelligence Command Center**.

The UI must communicate:

-   operational health;
-   urgency;
-   trends;
-   risk;
-   relationships;
-   AI intelligence;
-   automation;
-   reporting maturity.

This is not a decorative specification. Every major visual component
must be connected to real application data.

------------------------------------------------------------------------

# 2. PRIMARY UI OBJECTIVE

A senior stakeholder opening OPSINTEL should understand the operational
situation within approximately 10 seconds.

The first screen must answer:

1.  What is our overall health?
2.  Is health improving or deteriorating?
3.  What is causing concern?
4.  Which services are at risk?
5.  What should I investigate?
6.  What does AI recommend?

------------------------------------------------------------------------

# 3. DESIGN PERSONALITY

OPSINTEL should look:

-   futuristic;
-   intelligent;
-   enterprise-grade;
-   premium;
-   calm;
-   analytical;
-   trustworthy.

It should NOT look:

-   like a gaming dashboard;
-   like a cyberpunk website;
-   like a crypto application;
-   excessively neon;
-   excessively animated;
-   like a default admin template.

The visual language should suggest:

> Mission control for IT operations.

------------------------------------------------------------------------

# 4. DESIGN PRINCIPLES

## 4.1 Data First

Visual effects must never compete with operational information.

## 4.2 Executive First

Important information appears before detailed information.

## 4.3 Progressive Disclosure

Show summary first; expose detail through drill-down.

## 4.4 Consistency

The same metric must look and behave consistently everywhere.

## 4.5 Trust

Every important insight should be traceable to evidence.

## 4.6 Motion With Purpose

Animation communicates:

-   loading;
-   state change;
-   focus;
-   transition;
-   confirmation.

Do not animate everything.

------------------------------------------------------------------------

# 5. COLOR SYSTEM

Use CSS variables/design tokens.

Suggested palette:

``` text
--bg-primary:        #071018
--bg-secondary:      #0B1620
--surface-primary:   #101E2A
--surface-secondary: #142534
--border:            #243746

--text-primary:      #F4F7FA
--text-secondary:    #A7B5C2
--text-muted:        #6F8190

--accent-primary:    #39C6FF
--accent-secondary:  #6E7BFF

--success:           #35D07F
--warning:           #F5B942
--critical:          #FF5C6C
```

These are starting design tokens, not values to scatter through
components.

------------------------------------------------------------------------

# 6. COLOR USAGE RULES

Use blue/cyan for:

-   primary actions;
-   selected navigation;
-   neutral intelligence;
-   interactive highlights.

Use green for:

-   healthy;
-   successful;
-   improved.

Use amber for:

-   warning;
-   watch;
-   moderate risk.

Use red for:

-   critical;
-   failed;
-   breached;
-   severe risk.

Do not use red merely as decoration.

------------------------------------------------------------------------

# 7. TYPOGRAPHY

Recommended:

``` text
Primary font:
Inter

Optional display font:
Inter / Geist / equivalent modern sans-serif
```

Hierarchy:

``` text
Page title:        28–32px
Section title:     18–22px
Card title:        13–15px
KPI value:         26–36px
Body:              14–15px
Secondary:         12–13px
Tiny metadata:     11–12px
```

Use weight rather than excessive font size.

------------------------------------------------------------------------

# 8. SPACING SYSTEM

Use an 8-point spacing system.

``` text
4px
8px
16px
24px
32px
40px
48px
64px
```

Avoid arbitrary spacing values where possible.

------------------------------------------------------------------------

# 9. BORDER RADIUS

Suggested:

``` text
Small controls: 8px
Cards: 12–16px
Large panels: 16–20px
Pills: 999px
```

Avoid excessive rounded-card styling.

------------------------------------------------------------------------

# 10. SHADOWS

Use subtle shadows.

Do not create heavy floating cards everywhere.

The hierarchy should primarily come from:

-   contrast;
-   spacing;
-   borders;
-   typography.

------------------------------------------------------------------------

# 11. APPLICATION SHELL

Desktop layout:

``` text
┌─────────────────────────────────────────────────────────────┐
│ TOP BAR                                                     │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  SIDEBAR     │              MAIN CONTENT                    │
│              │                                              │
│              │                                              │
│              │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 12. SIDEBAR

Navigation:

``` text
OPSINTEL
────────────────

Overview

OPERATIONS
Incidents
Problems
Changes
Services

INTELLIGENCE
AI Insights
AI Assistant

REPORTING
Reports

SYSTEM
Data Ingestion
Data Sources
Settings
```

Use icons plus labels.

Collapsed mode may be supported later.

------------------------------------------------------------------------

# 13. SIDEBAR BEHAVIOR

Active item:

-   accent indicator;
-   stronger text;
-   subtle surface highlight.

Hover:

-   subtle background;
-   no excessive animation.

The sidebar should remain stable during navigation.

------------------------------------------------------------------------

# 14. TOP BAR

Top bar should include:

Left:

``` text
Page title
Optional breadcrumb
```

Right:

``` text
Data status
Last refresh
AI status
Notifications
User/profile placeholder
```

Example:

``` text
Operations Overview                 Data Updated 2m ago
                                    AI ● Online
```

------------------------------------------------------------------------

# 15. GLOBAL DATA STATUS

Display a compact status indicator.

Example:

``` text
● Data Ready
```

or:

``` text
● Processing
```

or:

``` text
! Data Quality Warning
```

Clicking it can open the latest ingestion summary.

------------------------------------------------------------------------

# 16. PAGE CONTAINER

Desktop content:

``` text
max-width: 1600px
margin: auto
padding: 24–32px
```

On large monitors, content should not stretch indefinitely.

------------------------------------------------------------------------

# 17. OVERVIEW PAGE

The Overview is the primary demo screen.

Structure:

``` text
Page Header
Global Filters

Operations Health
KPI Row

Trend Section
Risk / Service Section

Operational Correlation
AI Insights

Recent Reports / Automation Status
```

------------------------------------------------------------------------

# 18. PAGE HEADER

Example:

``` text
Operations Overview
Enterprise IT Operations Intelligence

Last processed:
08 Aug 2026, 10:42 AM

[Generate Report]
[Upload Data]
```

Do not overload the header.

------------------------------------------------------------------------

# 19. GLOBAL FILTER BAR

Filters:

``` text
Period
Service
Priority
Status
Criticality
```

Example:

``` text
Period: Last 30 Days
Service: All
Priority: All
Status: All
```

Include:

``` text
Reset Filters
```

------------------------------------------------------------------------

# 20. OPERATIONS HEALTH HERO

This is the visual anchor.

Example:

``` text
┌─────────────────────────────────────────────────────┐
│ OPERATIONS HEALTH                                   │
│                                                     │
│             82                                      │
│           HEALTHY                                   │
│                                                     │
│ Incident   84   Problem   78   Change   86          │
│ Service    88   SLA       79                         │
│                                                     │
│ ▲ 3.2% vs previous period                           │
└─────────────────────────────────────────────────────┘
```

Use a radial/donut or circular health visualization.

------------------------------------------------------------------------

# 21. OHI VISUALIZATION

The OHI visualization should:

-   clearly display 0--100;
-   show status;
-   show change;
-   expose component scores;
-   support hover/tooltip;
-   support click-to-detail.

Do not rely solely on color.

Include text:

``` text
82
HEALTHY
```

------------------------------------------------------------------------

# 22. KPI CARDS

Recommended cards:

``` text
Incidents
P1 / P2
MTTR
Problems
Change Success
SLA Compliance
Availability
Critical Services
```

Each card:

``` text
Label
Current value
Delta
Trend icon
Small sparkline
```

Example:

``` text
INCIDENTS

1,248

▲ 13.0%

────╮
    ╰────
```

------------------------------------------------------------------------

# 23. KPI CARD INTERACTION

Hover:

-   reveal more context.

Click:

-   navigate to relevant detail page;
-   preserve current filters where practical.

------------------------------------------------------------------------

# 24. SPARKLINES

Use sparklines for quick trend context.

Do not include axes for tiny sparklines.

The user should be able to hover for exact values.

------------------------------------------------------------------------

# 25. INCIDENT TREND CHART

Use a line/area chart.

X-axis:

``` text
time
```

Y-axis:

``` text
incident count
```

Optional series:

``` text
Total
P1
P2
```

Allow series toggling.

------------------------------------------------------------------------

# 26. INCIDENT HEATMAP

A unique visualization should show:

``` text
Day of Week
     ×
Hour / Time Bucket
```

Color intensity represents incident volume.

This helps identify operational patterns.

Tooltip:

``` text
Tuesday
14:00–15:00
37 incidents
```

------------------------------------------------------------------------

# 27. SERVICE HEALTH MATRIX

Create a matrix:

``` text
                    SLA       Availability    Incidents
Payment             92%          98.4%           42
Identity             99%          99.8%            8
Orders               96%          99.1%           17
```

Use status indicators.

Clicking a service opens service detail.

------------------------------------------------------------------------

# 28. RISK MATRIX

Create an operational risk scatter plot.

X-axis:

``` text
Incident Volume
```

Y-axis:

``` text
SLA / Service Health
```

Bubble size:

``` text
Business Criticality
```

This creates a visually distinctive executive chart.

------------------------------------------------------------------------

# 29. CHANGE IMPACT VIEW

Show relationship between:

``` text
Changes
    ↓
Incident Activity
```

Possible visualization:

-   timeline;
-   connected nodes;
-   impact bands.

Example:

``` text
CHANGE-142
09:00
   │
   ├──── incident spike
   │
   └──── service degradation
```

This should be clearly labelled as association, not proven causation.

------------------------------------------------------------------------

# 30. AI INSIGHT PANEL

The dashboard should show the top 3--5 insights.

Each card:

``` text
[HIGH]

Payment Service Incident Spike

Incident volume +42%.
SLA declined 5.2%.

Confidence 89%

[View Evidence]
[Ask AI]
```

------------------------------------------------------------------------

# 31. AI INSIGHT SEVERITY

Levels:

``` text
CRITICAL
HIGH
MEDIUM
LOW
INFO
```

Use icon + text + color.

Do not communicate severity through color alone.

------------------------------------------------------------------------

# 32. VIEW EVIDENCE

Clicking "View Evidence" should reveal:

``` text
Insight
↓
Metrics
↓
Affected records
↓
Relevant changes/problems
```

This is a major trust feature.

------------------------------------------------------------------------

# 33. AI ASSISTANT

Recommended interaction:

A floating or docked assistant panel.

Collapsed:

``` text
[ ✦ Ask OPSINTEL ]
```

Expanded:

``` text
┌───────────────────────────────┐
│ OPSINTEL AI                   │
│                               │
│ What would you like to know?  │
│                               │
│ > Why did incidents increase? │
│                               │
│ [Ask]                         │
└───────────────────────────────┘
```

------------------------------------------------------------------------

# 34. ASSISTANT QUICK PROMPTS

Provide chips:

``` text
Why did incidents spike?
Top risky service
SLA problems
Change impact
Monthly summary
What should we prioritize?
```

------------------------------------------------------------------------

# 35. AI RESPONSE DESIGN

Do not display a giant wall of text.

Structure:

``` text
Answer

Why:
• Evidence point
• Evidence point
• Evidence point

Recommendation:
...

Evidence:
[View metrics]
```

------------------------------------------------------------------------

# 36. REPORT STATUS WIDGET

Overview can show:

``` text
REPORT AUTOMATION

Daily      ● Enabled
Weekly     ● Enabled
Monthly    ● Enabled

Next report:
Weekly — Monday 08:00
```

Click → Reports.

------------------------------------------------------------------------

# 37. INGESTION PAGE

Layout:

``` text
Header
Upload Zone

Processing Pipeline

Dataset Cards

Validation Summary

Mapping Table

Processing History
```

------------------------------------------------------------------------

# 38. UPLOAD ZONE

Large drop zone:

``` text
┌─────────────────────────────────────────────┐
│                                             │
│       Drop ITSM files here                  │
│                                             │
│       CSV • XLSX • JSON                     │
│                                             │
│       [ Browse Files ]                      │
│                                             │
└─────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 39. UPLOAD FEEDBACK

After selection:

``` text
incidents.xlsx     4.2 MB
✓ Detected Incident

problems.xlsx      1.1 MB
✓ Detected Problem

changes.xlsx       2.3 MB
✓ Detected Change
```

------------------------------------------------------------------------

# 40. VALIDATION SUMMARY UI

Use summary cards:

``` text
Rows
Valid
Warnings
Errors
Quality
```

Then detailed expandable errors.

------------------------------------------------------------------------

# 41. PROCESSING SCREEN

Use a pipeline animation.

``` text
Upload          ✓
Classification  ✓
Validation      ✓
Normalization   ✓
Processing      ●
Analytics       ○
Ready           ○
```

Animation must communicate actual state.

Do not fake progress percentages.

------------------------------------------------------------------------

# 42. INCIDENT PAGE UI

Structure:

``` text
Header
Filters
KPI Cards
Trend
Distribution
Heatmap
Incident Table
```

------------------------------------------------------------------------

# 43. INCIDENT TABLE

Columns:

``` text
ID
Priority
Service
Status
Created
Resolved
MTTR
SLA
Problem
Change
```

Priority/status should use badges.

------------------------------------------------------------------------

# 44. PROBLEM PAGE UI

Structure:

``` text
Header
KPIs
Backlog Trend
Aging Distribution
Recurring Problem View
Problem Table
```

------------------------------------------------------------------------

# 45. PROBLEM AGING VISUAL

Use buckets:

``` text
0–7 days
8–30
31–60
61–90
90+
```

The oldest/problem risk should be visually obvious.

------------------------------------------------------------------------

# 46. CHANGE PAGE UI

Structure:

``` text
Header
KPI Cards
Success/Fails
Risk Distribution
Change → Incident Impact
Change Table
```

------------------------------------------------------------------------

# 47. CHANGE SUCCESS VISUAL

Use a clear ratio:

``` text
SUCCESS
94.2%

Failed 3.1%
Rollback 2.7%
```

------------------------------------------------------------------------

# 48. SERVICE PAGE UI

Use service cards or table.

Each service:

``` text
Name
Health
Criticality
Availability
SLA
Incidents
Problems
Changes
```

Sort by:

-   highest risk;
-   highest criticality;
-   worst SLA;
-   incident volume.

------------------------------------------------------------------------

# 49. SERVICE DETAIL PAGE

Header:

``` text
Payment Service
CRITICAL
```

Then:

``` text
Health
Availability
SLA
Incidents
Problems
Changes
```

Then:

``` text
Incident Trend
SLA Trend
Change Timeline
Related Problems
AI Insights
```

------------------------------------------------------------------------

# 50. AI INSIGHTS PAGE

Use a feed/card layout.

Filters:

``` text
Severity
Type
Service
Period
```

Each card:

``` text
Severity
Title
Summary
Evidence
Confidence
Recommendation
```

------------------------------------------------------------------------

# 51. REPORTS PAGE

Structure:

``` text
Report Header
Automation Controls
Schedule Cards
Report History
```

------------------------------------------------------------------------

# 52. REPORT HISTORY TABLE

Columns:

``` text
Report
Period
Generated
Status
AI
Notification
Actions
```

Actions:

``` text
View
Download PDF
View HTML
Send
```

------------------------------------------------------------------------

# 53. SCHEDULER UI

Create three schedule cards.

## Daily

``` text
Daily Report
Enabled ●
08:00
```

## Weekly

``` text
Weekly Report
Enabled ●
Monday 08:00
```

## Monthly

``` text
Monthly Report
Enabled ●
1st day 08:00
```

Allow enable/disable.

------------------------------------------------------------------------

# 54. MANUAL AUTOMATION DEMO

Buttons:

``` text
Generate Now
Send Test
```

The UI should clearly distinguish:

``` text
Manual Trigger
```

from:

``` text
Scheduled Execution
```

------------------------------------------------------------------------

# 55. DATA SOURCES PAGE

Display:

``` text
DATA SOURCES

Manual Upload
● Connected

ServiceNow
○ Planned

Jira
○ Planned
```

A future integration card can include:

``` text
Connector architecture ready
```

but must not imply a working connection.

------------------------------------------------------------------------

# 56. SETTINGS PAGE

Sections:

``` text
General
AI
Notifications
Scheduler
Data
System
```

------------------------------------------------------------------------

# 57. SETTINGS --- AI

Display:

``` text
Provider
Model
Status
```

Do not expose API keys.

Show:

``` text
Configured
Not Configured
Error
```

------------------------------------------------------------------------

# 58. SETTINGS --- NOTIFICATIONS

Teams:

``` text
Configured / Not Configured
Test
```

Slack:

``` text
Configured / Not Configured
Test
```

Webhook secrets must never be displayed.

------------------------------------------------------------------------

# 59. SETTINGS --- SCHEDULER

Show:

``` text
Timezone
Daily
Weekly
Monthly
```

Include next-run previews.

------------------------------------------------------------------------

# 60. SETTINGS --- DATA

Show:

``` text
Upload Limit
Retention
Current Dataset
Last Processing
```

------------------------------------------------------------------------

# 61. EMPTY STATES

Example:

``` text
No operational data available.

Upload an ITSM dataset or generate the demo dataset.

[Upload Data]
[Generate Demo Data]
```

Empty states must guide the user.

------------------------------------------------------------------------

# 62. ERROR STATES

Example:

``` text
We couldn't process this dataset.

Reason:
12 records have invalid resolution timestamps.

[View Validation Details]
[Upload Corrected File]
```

Avoid technical stack traces in the main UI.

------------------------------------------------------------------------

# 63. LOADING STATES

Use skeletons for normal data loading.

Use progress indicators for long-running workflows.

Do not show an indefinite spinner without context.

------------------------------------------------------------------------

# 64. SUCCESS STATES

Example:

``` text
✓ Processing complete

5,248 records processed.

Dashboard updated.
```

Provide:

``` text
[View Dashboard]
```

------------------------------------------------------------------------

# 65. TOASTS

Use concise notifications.

Examples:

``` text
✓ Dataset processed successfully
✓ Report generated
✓ Schedule updated
✓ Notification sent
```

Errors:

``` text
✕ Report generation failed
```

Do not show sensitive information.

------------------------------------------------------------------------

# 66. MODALS

Use modals only for:

-   confirmation;
-   focused configuration;
-   detail inspection;
-   destructive operations.

Do not put major workflows inside nested modal stacks.

------------------------------------------------------------------------

# 67. RESPONSIVE DESIGN

Desktop is the primary POC target.

Minimum responsive behavior:

### Desktop

Full dashboard.

### Tablet

Collapse grids.

### Mobile

Stack cards and charts.

The application must remain usable.

------------------------------------------------------------------------

# 68. CHART RULES

Every chart must have:

-   title;
-   purpose;
-   tooltip;
-   empty state;
-   loading state;
-   no-data handling.

Axes must have meaningful labels when needed.

------------------------------------------------------------------------

# 69. CHART ACCESSIBILITY

Do not rely exclusively on color.

Use:

-   labels;
-   icons;
-   patterns where appropriate;
-   textual status.

Tooltips must expose exact values.

------------------------------------------------------------------------

# 70. ANIMATION

Recommended:

-   page transitions;
-   card entrance;
-   KPI count-up on first load;
-   subtle chart reveal;
-   pipeline progress;
-   assistant expansion.

Avoid:

-   constant pulsing;
-   excessive particles;
-   distracting background animations.

------------------------------------------------------------------------

# 71. FUTURISTIC EFFECTS

Acceptable:

-   subtle grid;
-   faint radial glow;
-   glass-like surfaces;
-   gradient accents;
-   thin animated progress lines.

Not acceptable:

-   huge neon text;
-   matrix rain;
-   excessive holographic effects;
-   flashy gaming UI.

The goal is:

> futuristic enterprise, not cyberpunk.

------------------------------------------------------------------------

# 72. MICRO-INTERACTIONS

Examples:

KPI card:

``` text
Hover → slight elevation
```

Insight:

``` text
Hover → evidence preview
```

Chart:

``` text
Hover → exact metric
```

Button:

``` text
Hover → subtle accent
```

No interaction should feel slow.

------------------------------------------------------------------------

# 73. PERFORMANCE

Avoid:

-   rendering thousands of table rows;
-   recalculating charts on every mouse movement;
-   unnecessary API requests;
-   large client-side datasets.

Use:

-   pagination;
-   memoization where appropriate;
-   backend aggregation;
-   controlled filters.

------------------------------------------------------------------------

# 74. COMPONENT ARCHITECTURE

Suggested:

``` text
frontend/src/

components/
├── layout/
├── ui/
├── charts/
├── kpi/
├── dashboard/
├── ingestion/
├── incidents/
├── problems/
├── changes/
├── services/
├── insights/
├── assistant/
├── reports/
├── settings/
└── common/
```

------------------------------------------------------------------------

# 75. COMPONENT REUSE

Create reusable components for:

``` text
KpiCard
StatusBadge
TrendIndicator
SectionHeader
FilterBar
DataTable
ChartCard
InsightCard
EmptyState
ErrorState
LoadingState
MetricTooltip
```

Do not duplicate these across pages.

------------------------------------------------------------------------

# 76. DASHBOARD DATA CONTRACT

Frontend components should receive structured data.

Example:

``` json
{
  "metric": "incident_count",
  "current": 1248,
  "previous": 1104,
  "delta_percent": 13.04,
  "direction": "UP",
  "status": "WARNING"
}
```

------------------------------------------------------------------------

# 77. ACCESSIBILITY

Target practical WCAG-aligned behavior:

-   keyboard navigation;
-   visible focus;
-   readable contrast;
-   semantic buttons;
-   labels for form fields;
-   alt text where needed;
-   no color-only meaning.

------------------------------------------------------------------------

# 78. FRONTEND ERROR BOUNDARIES

A failure in one dashboard widget must not crash the entire page.

Example:

``` text
Incident Chart
ERROR

Service Health
WORKING

KPI Cards
WORKING
```

Allow retry where appropriate.

------------------------------------------------------------------------

# 79. DEMO-FIRST DESIGN

The first five minutes of the demo matter.

The recommended flow:

``` text
Overview
 ↓
Upload
 ↓
Processing
 ↓
Overview refresh
 ↓
Risk/service investigation
 ↓
AI insight
 ↓
AI assistant
 ↓
Report
 ↓
Scheduler
 ↓
Send Test
```

Every transition should be fast and visually clear.

------------------------------------------------------------------------

# 80. EXECUTIVE DEMO MOMENTS

Build these moments deliberately.

## Moment 1

Show OHI.

## Moment 2

Show a meaningful incident spike.

## Moment 3

Show the affected service.

## Moment 4

Show related change/problem information.

## Moment 5

Ask AI why it happened.

## Moment 6

Generate executive report.

## Moment 7

Show scheduler.

## Moment 8

Trigger Teams/Slack notification.

These demonstrate the entire value proposition.

------------------------------------------------------------------------

# 81. DO NOT BUILD A STATIC MOCK

Every important visualization must use API data.

If synthetic data is used, it must still flow through:

``` text
generator
→ ingestion/processing
→ database
→ analytics
→ API
→ UI
```

------------------------------------------------------------------------

# 82. UI TEST REQUIREMENTS

Test:

-   navigation;
-   upload;
-   validation;
-   filters;
-   charts;
-   drill-down;
-   AI assistant;
-   report generation;
-   scheduler controls;
-   notification controls;
-   empty states;
-   error states.

------------------------------------------------------------------------

# 83. VISUAL QA

Antigravity must verify:

-   no overlapping cards;
-   no clipped text;
-   no horizontal overflow;
-   consistent spacing;
-   charts fit containers;
-   tooltips are visible;
-   dark theme contrast is readable;
-   loading states do not shift layout excessively.

------------------------------------------------------------------------

# 84. BROWSER QA

At minimum verify:

``` text
Chrome/Chromium
```

Primary demo viewport:

``` text
1440 × 900
```

Also verify a smaller desktop/tablet width.

------------------------------------------------------------------------

# 85. FINAL UI ACCEPTANCE CRITERIA

The UI is accepted only if:

### UI-001

Application looks like one coherent product.

### UI-002

Overview communicates health immediately.

### UI-003

Dashboard values are dynamic.

### UI-004

Upload workflow is understandable.

### UI-005

Processing state is visible.

### UI-006

Incident page works.

### UI-007

Problem page works.

### UI-008

Change page works.

### UI-009

Service page works.

### UI-010

AI insights are visible.

### UI-011

AI assistant is usable.

### UI-012

Reports are accessible.

### UI-013

Scheduler status is visible.

### UI-014

Notification status is visible.

### UI-015

Empty/error/loading states exist.

### UI-016

Charts are interactive.

### UI-017

Drill-down works.

### UI-018

No critical visual defects exist at demo resolution.

------------------------------------------------------------------------

# 86. ANTIGRAVITY UI IMPLEMENTATION RULE

Before implementing any page:

1.  identify its functional requirements;
2.  identify required API data;
3.  define the page information hierarchy;
4.  define loading state;
5.  define empty state;
6.  define error state;
7.  implement reusable components;
8.  connect real API data;
9.  test interactions;
10. perform browser visual QA;
11. update documentation.

Do not build all pages as disconnected visual mockups and connect them
later.

------------------------------------------------------------------------

# 87. DESIGN GOLDEN RULE

Every visual element must answer one of these:

> What happened?

> Is it getting better or worse?

> Where is the risk?

> Why does it matter?

> What should I investigate?

> What should I do next?

If an element answers none of these, it probably does not belong on the
executive dashboard.

------------------------------------------------------------------------

# 88. FINAL UI VISION

OPSINTEL should feel like this:

``` text
                    OPSINTEL
          AI OPERATIONS INTELLIGENCE

                 ┌───────────┐
                 │    82     │
                 │  HEALTHY  │
                 └───────────┘

   INCIDENTS       SLA          CHANGES
    1,248         92.8%         94.2%
    ▲ 13%         ▼ 5.2%        ▲ 1.4%

       INCIDENT TREND
    ╭─────────────────────╮
    │       ╭──╮          │
    │  ╭────╯  ╰───╮      │
    │──╯            ╰───  │
    ╰─────────────────────╯

     SERVICE RISK MATRIX

       AI OPERATIONS INSIGHTS
       ┌─────────────────────┐
       │ HIGH                 │
       │ Payment Service      │
       │ Incident spike ...   │
       │ [View Evidence]      │
       └─────────────────────┘

       [ Ask OPSINTEL AI ]
```

The result should be visually impressive enough for a POC demonstration
while remaining credible as an enterprise product.

------------------------------------------------------------------------

# 89. COMPANION DOCUMENTS

This document depends on:

``` text
01_MASTER_ARCHITECTURE_AND_PRODUCT_BLUEPRINT.md
02_FUNCTIONAL_REQUIREMENTS_AND_WORKFLOWS.md
```

Next:

``` text
04_DATA_INGESTION_ANALYTICS_AND_KPI_SPECIFICATION.md
```

That document will define the canonical schemas, field-by-field data
model, validation rules, KPI formulas, OHI calculation, synthetic
dataset design, anomaly detection, correlation logic, and analytics
contracts.

# END OF OPSINTEL UI/UX & DASHBOARD DESIGN SPECIFICATION
