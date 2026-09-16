from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/kpis")
def get_global_kpis(db: Session = Depends(get_db)):
    """
    Returns the deterministic global KPIs across all IT operations.
    """
    service = AnalyticsService(db)
    return service.get_global_kpis()

@router.get("/services")
def get_service_analytics(db: Session = Depends(get_db)):
    """
    Returns the deterministic analytics broken down by IT Service.
    """
    service = AnalyticsService(db)
    return service.get_service_health()

@router.get("/trends")
def get_operational_trends(days: int = 14, db: Session = Depends(get_db)):
    """
    Returns daily time series operational trends (incidents, changes, problems, SLA compliance).
    """
    service = AnalyticsService(db)
    return service.get_time_series_trends(days=days)

@router.get("/health-score")
def get_operational_health_score(db: Session = Depends(get_db)):
    """
    Returns the overall composite Operational Health Score.
    """
    service = AnalyticsService(db)
    return service.get_health_score()

@router.get("/raw/incidents")
def get_raw_incidents(limit: int = 100, db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_raw_incidents(limit=limit)

@router.get("/raw/changes")
def get_raw_changes(limit: int = 100, db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_raw_changes(limit=limit)

@router.get("/raw/problems")
def get_raw_problems(limit: int = 100, db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_raw_problems(limit=limit)

@router.get("/correlation")
def get_change_incident_correlation(hours: int = 24, db: Session = Depends(get_db)):
    """
    Returns a list of incidents that occurred within X hours of a change on the same service.
    """
    service = AnalyticsService(db)
    return service.get_correlations(hours=hours)

@router.get("/problems/summary")
def get_problem_management_intelligence(db: Session = Depends(get_db)):
    """
    Returns comprehensive Problem Management Intelligence (KPIs, aging distribution,
    root cause breakdown, top impacted services, and recurring clusters).
    """
    service = AnalyticsService(db)
    return service.get_problem_management_intelligence()

@router.get("/problems/{problem_id}")
def get_problem_detail(problem_id: str, db: Session = Depends(get_db)):
    """
    Returns deep operational intelligence and related incidents for a single Problem.
    """
    service = AnalyticsService(db)
    return service.get_problem_detail(problem_id=problem_id)

@router.get("/raw/slas")
def get_raw_slas(limit: int = 100, db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_raw_slas(limit=limit)

