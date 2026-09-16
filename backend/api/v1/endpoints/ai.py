from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.services.analytics_service import AnalyticsService
from backend.services.ai_service import AIService
from backend.api.v1.endpoints.auth import get_current_user

router = APIRouter()

class ChatQuery(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    sources: list[str]

class RcaRequest(BaseModel):
    incident_id: str
    incident_title: str
    incident_priority: str
    incident_service: str
    incident_created: str

class RcaResponse(BaseModel):
    markdown_content: str

@router.post("/chat", response_model=ChatResponse)
def ask_ai_analyst(query: ChatQuery, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Interactive operational analyst query grounded in real-time KPI data.
    """
    analytics = AnalyticsService(db)
    kpis = analytics.get_global_kpis()
    
    ai = AIService()
    result = ai.answer_query(query.message, kpis, role=current_user.role)
    return result

@router.post("/rca", response_model=RcaResponse)
def generate_ai_rca(req: RcaRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Generates a formal RCA for an incident.
    """
    analytics = AnalyticsService(db)
    # Get correlated changes
    correlations = analytics.get_correlations(hours=24)
    correlated_changes = [c for c in correlations if c["incident_id"] == req.incident_id]
    
    incident_data = {
        "id": req.incident_id,
        "title": req.incident_title,
        "priority": req.incident_priority,
        "service": req.incident_service,
        "created": req.incident_created
    }
    
    ai = AIService()
    content = ai.generate_rca(incident=incident_data, correlated_changes=correlated_changes)
    return {"markdown_content": content}

@router.get("/forecast")
def get_risk_forecast(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Generates an AI predictive risk forecast for the next 7 days.
    """
    analytics = AnalyticsService(db)
    trends = analytics.get_time_series_trends(days=14)
    services_health = analytics.get_service_health()
    active_services = [s["service_name"] for s in services_health]
    
    ai = AIService()
    forecast = ai.generate_risk_forecast(trends, active_services)
    return forecast
