# Architecture Decision Records (ADRs)

Every meaningful architectural decision will be recorded here.

## ADR-001 — Use SQLite for POC
- **Context:** The POC needs a lightweight, local database without heavy infrastructure requirements.
- **Decision:** Use SQLite.
- **Status:** Approved (Module 01)

## ADR-002 — Reporting Scheduler
- **Context:** The system must generate reports automatically on daily, weekly, and monthly schedules.
- **Decision:** Use APScheduler for V1.
- **Status:** Approved (Module 07)

## ADR-003 — AI Architecture
- **Context:** AI must not hallucinate authoritative operational metrics.
- **Decision:** Implement an evidence-first architecture where deterministic analytics feed structured evidence to the AI.
- **Status:** Approved (Module 06)
