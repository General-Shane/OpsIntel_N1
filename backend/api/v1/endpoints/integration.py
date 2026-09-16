from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
import json

from backend.core.database import get_db
from backend.services.analytics_service import AnalyticsService
from backend.services.ai_service import AIService
from backend.core.models import Incident, Service, Problem, Change, SLARecord
from backend.config import settings

router = APIRouter()

# ============================================================================
# Beacon API Key Security Dependency
# ============================================================================

def verify_beacon_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Query(None)
):
    """
    Validates that incoming Beacon requests supply the authorized API key
    via X-API-Key header, Authorization Bearer token, or api_key query parameter.
    """
    provided_key = x_api_key or api_key
    if not provided_key and authorization and authorization.startswith("Bearer "):
        provided_key = authorization.split("Bearer ")[1].strip()

    expected_key = settings.BEACON_API_KEY
    if not provided_key or provided_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Beacon API Key. Access denied to AI Incident Commander integration endpoints."
        )
    return provided_key


# ============================================================================
# Beacon Integration Contracts (Schema v1.0)
# ============================================================================

@router.get("/beacon/v1/health-context", dependencies=[Depends(verify_beacon_api_key)])
def get_beacon_health_context(db: Session = Depends(get_db)):
    """
    Beacon AI Agent Incident Commander Integration Contract:
    Provides deterministic, machine-readable operational health and SLA governance telemetry.
    """
    analytics = AnalyticsService(db)
    kpis = analytics.get_global_kpis()
    health = analytics.get_health_score()
    
    return {
        "contract": "opsintel-beacon-integration",
        "schema_version": "1.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "health": {
            "score": health.get("health_score", 0),
            "status": health.get("status", "UNKNOWN"),
            "breakdown": health.get("breakdown", {})
        },
        "incidents_summary": {
            "total_incidents": kpis.get("incidents", {}).get("total_incidents", 0),
            "open_incidents": kpis.get("incidents", {}).get("open_incidents", 0),
            "active_p1_critical": kpis.get("incidents", {}).get("p1_incidents", 0),
            "active_p2_high": kpis.get("incidents", {}).get("p2_incidents", 0),
            "mttr_hours": kpis.get("incidents", {}).get("mttr_hours", 0.0)
        },
        "sla_summary": {
            "compliance_rate_percent": kpis.get("slas", {}).get("compliance_rate_percent", 0.0),
            "total_evaluated": kpis.get("slas", {}).get("total_slas", 0),
            "breached_count": kpis.get("slas", {}).get("breached_slas", 0)
        },
        "problem_summary": {
            "problem_backlog": kpis.get("problems", {}).get("problem_backlog", 0),
            "average_age_days": kpis.get("problems", {}).get("average_age_days", 0.0)
        },
        "change_summary": {
            "success_rate_percent": kpis.get("changes", {}).get("success_rate_percent", 0.0),
            "failed_changes": kpis.get("changes", {}).get("failed_changes", 0)
        }
    }


@router.get("/beacon/v1/active-incidents", dependencies=[Depends(verify_beacon_api_key)])
def get_beacon_active_incidents(limit: int = 50, db: Session = Depends(get_db)):
    """
    Beacon Integration: Active P1/P2/P3 operational incidents with correlated change metadata.
    """
    analytics = AnalyticsService(db)
    raw_incidents = analytics.get_raw_incidents(limit=limit)
    correlations = analytics.get_correlations(hours=24)
    corr_map = {c["incident_id"]: c for c in correlations}
    
    active = [inc for inc in raw_incidents if inc.get("status") not in ["RESOLVED", "CLOSED"]]
    
    enriched = []
    for inc in active:
        inc_id = inc.get("id")
        corr = corr_map.get(inc_id)
        enriched.append({
            "incident_id": inc_id,
            "title": inc.get("title"),
            "priority": inc.get("priority"),
            "status": inc.get("status"),
            "service_name": inc.get("service"),
            "created_at_utc": inc.get("created"),
            "correlated_change": {
                "change_id": corr["change_id"],
                "time_diff_hours": corr["time_diff_hours"],
                "change_completed_at": corr["change_completed_at"]
            } if corr else None
        })
        
    return {
        "contract": "opsintel-beacon-integration",
        "schema_version": "1.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_active_count": len(enriched),
        "incidents": enriched
    }


@router.get("/beacon/v1/incident-context/{incident_id}", dependencies=[Depends(verify_beacon_api_key)])
def get_beacon_incident_context(incident_id: str, db: Session = Depends(get_db)):
    """
    Beacon Integration: Comprehensive Incident Dossier for AI Incident Commander triage.
    """
    item = db.query(Incident, Service).join(Service, Incident.service_id == Service.service_id).filter(Incident.incident_id == incident_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
        
    inc, svc = item
    analytics = AnalyticsService(db)
    
    # 1. Correlated changes within 24h before incident
    correlations = analytics.get_correlations(hours=24)
    corr = next((c for c in correlations if c["incident_id"] == incident_id), None)
    
    # 2. Associated active problem on same service
    active_problem = db.query(Problem).filter(
        Problem.service_id == inc.service_id,
        Problem.status.in_(["OPEN", "INVESTIGATING"])
    ).first()
    
    # 3. Service SLA performance
    service_slas = db.query(SLARecord).filter(SLARecord.service_id == inc.service_id).all()
    sla_breaches = sum(1 for s in service_slas if s.breached)
    total_svc_slas = len(service_slas)
    svc_compliance = round((1 - (sla_breaches / total_svc_slas)) * 100, 1) if total_svc_slas > 0 else 100.0
    
    return {
        "contract": "opsintel-beacon-integration",
        "schema_version": "1.0",
        "incident_id": inc.incident_id,
        "priority": "Critical" if inc.priority == "P1" else "High" if inc.priority == "P2" else "Medium" if inc.priority == "P3" else "Low",
        "raw_priority": inc.priority,
        "status": inc.status,
        "created_at_utc": inc.created_at.isoformat() + "Z" if hasattr(inc.created_at, "isoformat") else str(inc.created_at),
        "resolution_time_hours": inc.resolution_time_hours,
        "service": {
            "service_id": svc.service_id,
            "service_name": svc.service_name,
            "criticality": svc.criticality,
            "sla_compliance_rate_percent": svc_compliance
        },
        "change_correlation": {
            "correlated": corr is not None,
            "suspect_change_id": corr["change_id"] if corr else None,
            "time_diff_hours": corr["time_diff_hours"] if corr else None,
            "confidence": "High (Deployed <24h on same service)" if corr else "None"
        },
        "associated_problem": {
            "problem_id": active_problem.problem_id if active_problem else None,
            "status": active_problem.status if active_problem else None,
            "age_days": round(active_problem.age_days, 1) if active_problem and active_problem.age_days else None,
            "confidence": "Analytics Derived" if active_problem else "None"
        },
        "diagnostic_vectors": [
            f"Review recent deployments on {svc.service_name}",
            f"Inspect latency / error rate spikes on {svc.service_id}",
            f"Verify SLA target compliance window for {inc.priority} severity"
        ]
    }


@router.get("/beacon/v1/problem-intelligence", dependencies=[Depends(verify_beacon_api_key)])
def get_beacon_problem_intelligence(db: Session = Depends(get_db)):
    """
    Beacon Integration: Problem management backlog, 4-tier aging buckets, and recurring failure clusters.
    """
    analytics = AnalyticsService(db)
    intelligence = analytics.get_problem_management_intelligence()
    
    return {
        "contract": "opsintel-beacon-integration",
        "schema_version": "1.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "summary": intelligence.get("summary", {}),
        "aging_distribution": intelligence.get("aging_distribution", []),
        "root_cause_hypotheses": intelligence.get("root_cause_breakdown", []),
        "top_impacted_services": intelligence.get("top_impacted_services", []),
        "recurring_incident_clusters": intelligence.get("recurring_clusters", [])
    }


@router.get("/beacon/v1/service-health", dependencies=[Depends(verify_beacon_api_key)])
def get_beacon_service_health(db: Session = Depends(get_db)):
    """
    Beacon Integration: Current operational health breakdown per service.
    """
    analytics = AnalyticsService(db)
    services_data = analytics.get_service_health()
    
    return {
        "contract": "opsintel-beacon-integration",
        "schema_version": "1.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_services": len(services_data),
        "services": services_data
    }


@router.get("/beacon/v1/executive-brief", dependencies=[Depends(verify_beacon_api_key)])
def get_beacon_executive_brief(db: Session = Depends(get_db)):
    """
    Beacon Integration: Concise executive operational narrative and attention points.
    """
    analytics = AnalyticsService(db)
    ai_svc = AIService()
    kpis = analytics.get_global_kpis()
    health = analytics.get_health_score()
    
    summary_text = ai_svc.generate_executive_summary(kpis)
    
    return {
        "contract": "opsintel-beacon-integration",
        "schema_version": "1.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "health_score": health.get("health_score", 0),
        "health_status": health.get("status", "UNKNOWN"),
        "executive_summary_narrative": summary_text,
        "key_risk_factors": [
            f"{kpis.get('incidents', {}).get('p1_incidents', 0)} Active P1 Critical Incidents",
            f"{kpis.get('slas', {}).get('breached_slas', 0)} Breached SLA contracts",
            f"{kpis.get('problems', {}).get('problem_backlog', 0)} Unresolved problem backlog records"
        ]
    }
