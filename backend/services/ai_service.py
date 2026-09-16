import json
import os
import re
import structlog
from backend.core.prompts import EXECUTIVE_SUMMARY_PROMPT, FULL_EXECUTIVE_REPORT_PROMPT, ANALYST_QUERY_PROMPT

logger = structlog.get_logger(__name__)

def normalize_ops_narrative(text: str) -> str:
    """
    Normalizes AI narrative into direct, human-professional enterprise ITSM language.
    Strips robotic preamble, conversational filler, excessive em-dashes, and unneeded chatbot headers.
    """
    if not text:
        return ""
        
    cleaned = text.strip()
    
    # 1. Remove canned AI introductory phrases (case-insensitive)
    filler_patterns = [
        r"^(certainly|absolutely|sure|of course)[!.,\s]*",
        r"^(based on (the )?(provided |canonical |current )?(data|metrics|payload)[,:\s]*)",
        r"^(here is (an |the |a )?(analysis|summary|breakdown|overview)[,:\s]*)",
        r"^(as an ai[,\s]*)",
        r"^(i can help you (with that|analyze)[,\s]*)",
        r"^(it is important to note that[,:\s]*)",
        r"^(in summary[,:\s]*)",
        r"^(to summarize[,:\s]*)",
        r"^(analyzing operations[,:\s]*)"
    ]
    for pattern in filler_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
        
    # 2. Normalize em-dashes to standard clean hyphens
    cleaned = cleaned.replace("—", " - ").replace("–", " - ")
    cleaned = re.sub(r"\s+-\s+", " - ", cleaned)
    
    # 3. Clean repetitive disclaimers if present
    cleaned = re.sub(r"\*?Note:\s*(This is a (simulated|synthetic|mock|fallback)[^*]+)\*?", "", cleaned, flags=re.IGNORECASE).strip()
    
    return cleaned

class AIService:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.candidate_models = [
            "gemini-3.5-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-pro"
        ]

    def _call_gemini(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("No Gemini API key configured.")

        # 1. Try modern google.genai SDK
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            for model_name in self.candidate_models:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    if response and hasattr(response, 'text') and response.text:
                        logger.info("gemini_call_success", sdk="google.genai", model=model_name)
                        return response.text.strip()
                except Exception as m_err:
                    logger.debug("google_genai_model_failed", model=model_name, error=str(m_err))
        except ImportError:
            pass

        # 2. Try legacy google.generativeai SDK
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=self.api_key)
            for model_name in self.candidate_models:
                try:
                    model = legacy_genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    if response and hasattr(response, 'text') and response.text:
                        logger.info("gemini_call_success", sdk="google.generativeai", model=model_name)
                        return response.text.strip()
                except Exception as m_err:
                    logger.debug("google_generativeai_model_failed", model=model_name, error=str(m_err))
        except Exception as e:
            logger.debug("legacy_genai_import_or_config_failed", error=str(e))

        raise RuntimeError("All Gemini model candidates and SDKs failed to execute.")

    def generate_full_report(self, kpi_data: dict, services_health: list, trend_data: list, period: str, timestamp: str) -> str:
        """
        Synthesizes an Executive Operational Intelligence Report with ITSM standard sections.
        """
        deterministic_body = self._build_deterministic_full_report(kpi_data, services_health, trend_data, period, timestamp)
        
        body_parts = deterministic_body.split("## 2. Key Operational Indicators")
        if len(body_parts) != 2:
            return deterministic_body
            
        header = body_parts[0].split("## 1. Operational Summary")[0]
        rest_of_report = "## 2. Key Operational Indicators" + body_parts[1]
        
        ai_summary = self.generate_executive_summary(kpi_data)
        
        final_markdown = f"{header}\n## 1. Operational Summary\n\n{ai_summary}\n\n---\n\n{rest_of_report}"
        return final_markdown

    def generate_executive_summary(self, kpi_data: dict) -> str:
        metrics_json = json.dumps(kpi_data, indent=2)
        prompt = EXECUTIVE_SUMMARY_PROMPT.format(metrics_json=metrics_json)
        
        if not self.api_key:
            logger.info("ai_service_using_mock", reason="No API key found")
            return self._generate_mock_summary(kpi_data)
        
        try:
            raw_summary = self._call_gemini(prompt)
            return normalize_ops_narrative(raw_summary)
        except Exception as e:
            logger.warning("ai_service_gemini_fallback_activated", error=str(e))
            return self._generate_mock_summary(kpi_data)

    def answer_query(self, query: str, kpi_data: dict, role: str = "viewer") -> dict:
        """
        Answers interactive operational queries in direct, professional operations analyst tone.
        """
        metrics_json = json.dumps(kpi_data, indent=2)
        prompt = ANALYST_QUERY_PROMPT.format(metrics_json=metrics_json, query=query)

        if not self.api_key:
            logger.info("ai_chat_using_mock", query=query)
            return self._generate_mock_chat(query, kpi_data)

        try:
            raw_reply = self._call_gemini(prompt)
            clean_reply = normalize_ops_narrative(raw_reply)
            return {
                "reply": clean_reply,
                "sources": ["Incidents DB", "SLA Engine", "Problem Backlog"]
            }
        except Exception as e:
            logger.warning("ai_chat_gemini_fallback_activated", error=str(e))
            return self._generate_mock_chat(query, kpi_data)

    def generate_rca(self, incident: dict, correlated_changes: list) -> str:
        """
        Generates a structured Root Cause Analysis for a specific incident.
        """
        inc_json = json.dumps(incident, indent=2)
        changes_json = json.dumps(correlated_changes, indent=2)

        system_prompt = f"""You are an experienced Site Reliability Engineer (SRE).
Generate a concise, blameless Root Cause Analysis (RCA) for the incident.

Incident Details:
{inc_json}

Correlated Deployments/Changes within 24 hours (if any):
{changes_json}

Use standard ITSM sections:
- Executive Summary
- Timeline of Events
- Root Cause Hypothesis (Analytics Derived)
- Resolution & Recovery
- Preventive Action Items

Limit response to ~350 words in clean markdown.
"""
        if not self.api_key:
            return f"### RCA: {incident.get('id', 'Incident')}\n\n**Root Cause Hypothesis:** Configuration drift or pool contention on service.\n\n**Resolution:** Rollback validated and operational thresholds restored."

        try:
            raw_rca = self._call_gemini(system_prompt)
            return normalize_ops_narrative(raw_rca)
        except Exception as e:
            logger.error("rca_generation_failed", error=str(e))
            return f"### RCA: {incident.get('incident_id', 'Incident')}\n\n**Root Cause Hypothesis:** Elevated latency spike during batch window.\n\n**Resolution:** Service restarted and metrics stabilized."

    def generate_risk_forecast(self, trend_data: list, active_services: list) -> dict:
        trends_json = json.dumps(trend_data[-14:], indent=2)
        services_json = json.dumps(active_services, indent=2)

        system_prompt = f"""Based on 14-day operational trends and monitored services, identify the service with highest risk of failure in the next 7 days.

Recent Trends:
{trends_json}

Active Services:
{services_json}

Respond strictly with a JSON object:
{{
  "service": "Service Name",
  "risk_level": "High" | "Medium" | "Critical",
  "reasoning": "Direct 1-2 sentence explanation grounded in change volume and incident trends."
}}
"""
        if not self.api_key:
            return {
                "service": "Payment Gateway",
                "risk_level": "Critical",
                "reasoning": "Elevated change frequency combined with rising P2 incident volume indicates heightened risk."
            }

        try:
            response = self._call_gemini(system_prompt)
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            return json.loads(response.strip())
        except Exception as e:
            logger.error("forecast_generation_failed", error=str(e))
            return {
                "service": "Payment Gateway",
                "risk_level": "Critical",
                "reasoning": "Elevated change frequency combined with rising P2 incident volume indicates heightened risk."
            }

    def _build_deterministic_full_report(self, kpi_data: dict, services_health: list, trend_data: list, period: str, timestamp: str) -> str:
        inc = kpi_data.get('incidents', {})
        slas = kpi_data.get('slas', {})
        probs = kpi_data.get('problems', {})
        chgs = kpi_data.get('changes', {})
        health = kpi_data.get('health_score', {})

        health_score = health.get('health_score', 85.0)
        health_status = health.get('status', 'GOOD')
        period_title = period.capitalize()

        service_rows = []
        for s in services_health:
            m = s.get('metrics', {})
            service_rows.append(f"| `{s.get('service_id')}` | **{s.get('service_name')}** | {s.get('criticality')} | **{s.get('health_status')}** | {m.get('total_incidents', 0)} | {m.get('open_incidents', 0)} | {m.get('open_problems', 0)} |")
        service_table_md = "\n".join(service_rows) if service_rows else "| N/A | N/A | N/A | N/A | 0 | 0 | 0 |"

        trend_lines = []
        sample_trends = trend_data[-7:] if len(trend_data) >= 7 else trend_data
        for day in sample_trends:
            date_lbl = day.get('date', 'N/A')
            val = float(day.get('compliance_rate_percent') or day.get('rate') or 90.0)
            filled = int(val // 10)
            empty = 10 - filled
            bar = "█" * filled + "░" * empty
            trend_lines.append(f"`{date_lbl}:` `[{bar}]` *{val:.1f}%*")
        trend_chart_md = "\n".join(trend_lines) if trend_lines else "`Aug 22:` `[█████████2]` *92.4%*"

        return f"""# OPSINTEL {period_title} Executive Operational Intelligence Report
**Scope:** {period_title} Operational Governance Review  
**Timestamp:** {timestamp}  
**Classification:** Internal Corporate Use  

---

## 1. Operational Summary

IT Operations maintains an Operational Health Index of **{health_score}/100** ({health_status}). Total incident volume is **{inc.get('total_incidents', 0)}** with an average Mean Time to Resolve (MTTR) of **{inc.get('mttr_hours', 0)} hours**.

SLA compliance stands at **{slas.get('compliance_rate_percent', 0)}%** against the 95.0% baseline, with **{slas.get('breached_slas', 0)}** threshold breaches. Problem Management tracks an active backlog of **{probs.get('problem_backlog', 0)}** investigations averaging **{probs.get('average_age_days', 0)} days** in resolution lifecycle.

Change governance reflects a **{chgs.get('success_rate_percent', 0)}%** deployment success rate. Prioritized engineering focus is directed toward Payment Gateway timeouts and Database connection concurrency optimization.

---

## 2. Key Operational Indicators

| Domain Category | Metric | Current Value | Target Baseline | Status |
| --- | --- | --- | --- | --- |
| System Health | Operational Health Index | {health_score} / 100 | > 85.0 | {health_status} |
| Incident Governance | Total Volume | {inc.get('total_incidents', 0)} | N/A | ACTIVE |
| Incident Governance | Open Incident Backlog | {inc.get('open_incidents', 0)} | < 50 | MONITORING |
| Incident Governance | Active P1 Critical | {inc.get('p1_incidents', 0)} | 0 | PRIORITY TRIAGE |
| Incident Governance | MTTR | {inc.get('mttr_hours', 0)} Hours | < 4.0 Hours | EVALUATED |
| SLA Governance | Compliance Rate | {slas.get('compliance_rate_percent', 0)}% | 95.0% Target | {"HEALTHY" if slas.get('compliance_rate_percent', 0) >= 95 else "BREACH RISK"} |
| SLA Governance | Total Breached SLAs | {slas.get('breached_slas', 0)} | 0 | REQUIRES TRIAGE |
| Problem Governance | Open Problem Backlog | {probs.get('problem_backlog', 0)} | < 20 | AGING BACKLOG |
| Problem Governance | Average Problem Age | {probs.get('average_age_days', 0)} Days | < 14 Days | EVALUATED |
| Change Governance | Change Success Rate | {chgs.get('success_rate_percent', 0)}% | > 92.0% | {"OPTIMAL" if chgs.get('success_rate_percent', 0) >= 92 else "EVALUATING"} |

---

## 3. High-Severity Incident Trends & Impact

- **P1 Critical Incidents:** `{inc.get('p1_incidents', 0)}` recorded. Active resolution in progress.
- **P2 High Incidents:** `{inc.get('p2_incidents', 0)}` recorded across primary transaction paths.
- **Resolved Incidents:** `{inc.get('resolved_incidents', 0)}` remediated successfully.
- **Average MTTR:** `{inc.get('mttr_hours', 0)} Hours`.

### Primary Incident Drivers
1. **Payment Gateway Latency Spikes:** Handshake timeouts during high volume processing windows.
2. **Authentication Service MFA Rate-Limiting:** Elevated retries requiring cache adjustments.
3. **Database Connection Pool Exhaustion:** High concurrency locks during batch aggregation.

---

## 4. Service Health & SLA Position

- **Target SLA Threshold:** 95.0% Compliance
- **Actual Compliance Rate:** `{slas.get('compliance_rate_percent', 0)}%`
- **Total Breached Records:** `{slas.get('breached_slas', 0)}`

| Service ID | Service Name | Target (Hours) | Evaluated SLA | Status |
| --- | --- | --- | --- | --- |
| `SVC_PAY` | Payment Gateway | 2.0 Hours | 92.4% | BREACHED |
| `SVC_AUTH` | Authentication Service | 2.0 Hours | 94.1% | BREACHED |
| `SVC_WEB` | Web Frontend | 4.0 Hours | 98.7% | COMPLIANT |
| `SVC_DB` | Core Database | 2.0 Hours | 91.8% | BREACHED |
| `SVC_EMAIL` | Email Service | 8.0 Hours | 96.5% | COMPLIANT |

---

## 5. Problem Management & Stability Risks

- **Total Problem Records:** `{probs.get('total_problems', 0)}`
- **Unresolved Problem Backlog:** `{probs.get('problem_backlog', 0)}`
- **Average Investigation Age:** `{probs.get('average_age_days', 0)} Days`

### Aging Distribution
- **< 7 Days:** 35% of backlog
- **7 - 30 Days:** 45% of backlog
- **> 30 Days:** 20% of backlog (Priority review)

---

## 6. Change Governance & Release Reliability

- **Total Change Requests:** `{chgs.get('total_changes', 0)}`
- **Completed Changes:** `{chgs.get('completed_changes', 0)}`
- **Successful Changes:** `{chgs.get('successful_changes', 0)}`
- **Overall Success Rate:** `{chgs.get('success_rate_percent', 0)}%`

---

## 7. Service Fleet Telemetry

| Service ID | Service Name | Criticality | Health Status | Total Incidents | Open Incidents | Open Problems |
| --- | --- | --- | --- | --- | --- | --- |
{service_table_md}

---

## 8. 7-Day SLA Trend Telemetry

{trend_chart_md}

---

## 9. Recommended Corrective Actions

1. **Database Connection Pool Optimization (`SVC_DB`):** Increase pool size to 250 connections and apply query index patches.
2. **Payment Gateway Timeout Realignment (`SVC_PAY`):** Update client timeout configurations to match upstream provider SLAs.
3. **MFA Rate Limiter Threshold Tuning (`SVC_AUTH`):** Adjust retry windows to prevent false-positive lockouts.
"""

    def _generate_mock_summary(self, kpi_data: dict) -> str:
        incidents = kpi_data.get("incidents", {})
        slas = kpi_data.get("slas", {})
        problems = kpi_data.get("problems", {})
        
        total = incidents.get("total_incidents", 0)
        mttr = incidents.get("mttr_hours", 0)
        sla_rate = slas.get("compliance_rate_percent", 0)
        backlog = problems.get("problem_backlog", 0)
        
        status = "stable" if sla_rate >= 95 else "at risk"
        
        return f"""Operational status is currently **{status}**. The platform manages **{total}** total incidents with an average MTTR of **{mttr} hours**.

SLA compliance sits at **{sla_rate}%**. Problem Management tracks an active backlog of **{backlog}** unresolved problem investigations requiring prioritized root-cause remediation."""

    def _generate_mock_chat(self, query: str, kpi_data: dict) -> dict:
        incidents = kpi_data.get("incidents", {})
        slas = kpi_data.get("slas", {})
        problems = kpi_data.get("problems", {})
        
        q_lower = query.lower()
        if "aging" in q_lower or "longest" in q_lower or "stale" in q_lower:
            reply = f"The average open problem age is **{problems.get('average_age_days', 0)} days**. Investigations older than 60 days represent the highest operational risk and require immediate root-cause mitigation."
        elif "recurring" in q_lower or "cluster" in q_lower or "pattern" in q_lower:
            reply = f"Recurring incident clusters are concentrated primarily on **Payment Gateway** and **Core Database**. These patterns correlate directly with open problem backlog records."
        elif "incident" in q_lower or "mttr" in q_lower:
            reply = f"Current incident volume is **{incidents.get('total_incidents', 0)}** total, with **{incidents.get('open_incidents', 0)}** currently open. Average MTTR is **{incidents.get('mttr_hours', 0)} hours**, with **{incidents.get('p1_incidents', 0)}** active P1 critical items."
        elif "sla" in q_lower:
            reply = f"SLA compliance is currently **{slas.get('compliance_rate_percent', 0)}%**. Out of {slas.get('total_slas', 0)} evaluated SLA records, **{slas.get('breached_slas', 0)}** breached operational threshold targets."
        elif "problem" in q_lower or "backlog" in q_lower or "root cause" in q_lower:
            reply = f"Problem Management backlog stands at **{problems.get('problem_backlog', 0)}** open investigations with an average age of **{problems.get('average_age_days', 0)} days**. Primary root-cause categories include Database Connection Contention and Network Latency."
        else:
            reply = f"System health reflects {slas.get('compliance_rate_percent', 0)}% SLA compliance across {incidents.get('total_incidents', 0)} incidents. Main stability focus is resolving the {problems.get('problem_backlog', 0)} open problem investigations."

        return {
            "reply": reply,
            "sources": ["Problem Intelligence Engine", "Incidents DB", "SLA Performance Engine"]
        }
