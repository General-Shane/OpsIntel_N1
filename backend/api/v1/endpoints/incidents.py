import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.core.models import Incident, Service, User, AuditEvent, SLARecord, Change, Problem
from backend.api.v1.endpoints.auth import (
    get_current_user,
    require_permission
)

router = APIRouter()

# ============================================================================
# Schemas
# ============================================================================

class IncidentCreate(BaseModel):
    service_id: str
    title: str
    description: Optional[str] = None
    priority: str = Field(default="P3", pattern="^(P1|P2|P3|P4)$")
    urgency: Optional[str] = Field(default="MEDIUM", pattern="^(HIGH|MEDIUM|LOW)$")
    impact: Optional[str] = Field(default="MEDIUM", pattern="^(HIGH|MEDIUM|LOW)$")
    category: Optional[str] = "Application"
    subcategory: Optional[str] = "Service Degradation"
    assignment_group: Optional[str] = "Service Desk Tier-1"
    assigned_user_id: Optional[str] = None
    related_change_id: Optional[str] = None
    problem_id: Optional[str] = None

class IncidentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(NEW|IN_PROGRESS|ON_HOLD|RESOLVED|CLOSED)$")

class IncidentAssignUpdate(BaseModel):
    assigned_user_id: Optional[str] = None
    assignment_group: Optional[str] = None

class IncidentResolveRequest(BaseModel):
    resolution_code: str = Field(default="SOLVED_PERMANENTLY")
    resolution_notes: str

# ============================================================================
# Helpers
# ============================================================================

SLA_TARGET_HOURS = {
    "P1": 4.0,
    "P2": 8.0,
    "P3": 24.0,
    "P4": 48.0
}

def _incident_to_dict(inc: Incident) -> Dict[str, Any]:
    return {
        "id": inc.id,
        "incident_id": inc.incident_id,
        "title": inc.title,
        "description": inc.description,
        "priority": inc.priority,
        "urgency": inc.urgency,
        "impact": inc.impact,
        "status": inc.status,
        "category": inc.category,
        "subcategory": inc.subcategory,
        "service_id": inc.service_id,
        "service_name": inc.service.service_name if inc.service else inc.service_id,
        "assignment_group": inc.assignment_group,
        "assigned_user_id": inc.assigned_user_id,
        "assigned_username": inc.assigned_user.username if inc.assigned_user else None,
        "reporter_user_id": inc.reporter_user_id,
        "reporter_username": inc.reporter_user.username if inc.reporter_user else None,
        "problem_id": inc.problem_id,
        "related_change_id": inc.related_change_id,
        "resolution_code": inc.resolution_code,
        "resolution_notes": inc.resolution_notes,
        "resolution_time_hours": round(inc.resolution_time_hours, 2) if inc.resolution_time_hours is not None else None,
        "opened_at": inc.opened_at.isoformat() if inc.opened_at else None,
        "acknowledged_at": inc.acknowledged_at.isoformat() if inc.acknowledged_at else None,
        "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
        "closed_at": inc.closed_at.isoformat() if inc.closed_at else None,
        "created_at": inc.created_at.isoformat() if inc.created_at else None,
        "updated_at": inc.updated_at.isoformat() if inc.updated_at else None,
    }

def _log_audit(
    db: Session,
    actor: User,
    action: str,
    entity_id: str,
    old_state: Optional[Dict[str, Any]] = None,
    new_state: Optional[Dict[str, Any]] = None
):
    audit = AuditEvent(
        actor_user_id=actor.id if actor else None,
        actor_username=actor.username if actor else "SYSTEM",
        entity_type="Incident",
        entity_id=entity_id,
        action=action,
        old_state_json=json.dumps(old_state, default=str) if old_state else None,
        new_state_json=json.dumps(new_state, default=str) if new_state else None,
        timestamp_utc=datetime.now()
    )
    db.add(audit)

# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=Dict[str, Any])
def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    priority: Optional[str] = None,
    status: Optional[str] = None,
    service_id: Optional[str] = None,
    assigned_user_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Paginated incident list with filtering and search.
    """
    query = db.query(Incident)

    if priority and priority.upper() != "ALL":
        query = query.filter(Incident.priority == priority.upper())
    if status and status.upper() != "ALL":
        query = query.filter(Incident.status == status.upper())
    if service_id and service_id.upper() != "ALL":
        query = query.filter(Incident.service_id == service_id)
    if assigned_user_id:
        query = query.filter(Incident.assigned_user_id == assigned_user_id)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Incident.incident_id.ilike(s)) |
            (Incident.title.ilike(s)) |
            (Incident.description.ilike(s))
        )

    total = query.count()
    incidents = query.order_by(desc(Incident.opened_at)).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [_incident_to_dict(i) for i in incidents]
    }


@router.get("/{incident_id}", response_model=Dict[str, Any])
def get_incident_detail(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detailed incident dossier including SLAs, correlated change, and audit history.
    """
    incident = db.query(Incident).filter(
        (Incident.incident_id == incident_id) | (Incident.id == incident_id)
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    slas = db.query(SLARecord).filter(SLARecord.incident_id == incident.incident_id).all()

    audits = db.query(AuditEvent).filter(
        AuditEvent.entity_type == "Incident",
        AuditEvent.entity_id == incident.incident_id
    ).order_by(desc(AuditEvent.timestamp_utc)).all()

    audit_list = []
    for a in audits:
        audit_list.append({
            "id": a.id,
            "actor_username": a.actor_username,
            "action": a.action,
            "timestamp_utc": a.timestamp_utc.isoformat() if a.timestamp_utc else None,
            "old_state": json.loads(a.old_state_json) if a.old_state_json else None,
            "new_state": json.loads(a.new_state_json) if a.new_state_json else None
        })

    detail = _incident_to_dict(incident)
    detail["sla_records"] = [
        {
            "sla_id": s.sla_id,
            "name": s.name,
            "target_hours": s.target_hours,
            "actual_hours": s.actual_hours,
            "breached": s.breached,
            "status": s.status
        }
        for s in slas
    ]
    detail["audit_trail"] = audit_list
    return detail


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("incidents.manage"))
):
    """
    Logs a new Incident, automatically attaches SLA targets, and writes an AuditEvent.
    """
    # 1. Validate Service
    service = db.query(Service).filter(Service.service_id == payload.service_id).first()
    if not service:
        raise HTTPException(status_code=400, detail=f"Service '{payload.service_id}' does not exist.")

    # 2. Validate related change if provided
    if payload.related_change_id:
        chg = db.query(Change).filter(Change.change_id == payload.related_change_id).first()
        if not chg:
            raise HTTPException(status_code=400, detail=f"Correlated change '{payload.related_change_id}' not found.")

    # 3. Generate unique incident_id
    count = db.query(Incident).count()
    incident_id = f"INC{(count + 1):06d}"
    while db.query(Incident).filter(Incident.incident_id == incident_id).first():
        count += 1
        incident_id = f"INC{(count + 1):06d}"

    now = datetime.now()
    new_inc = Incident(
        incident_id=incident_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        urgency=payload.urgency,
        impact=payload.impact,
        status="NEW",
        category=payload.category,
        subcategory=payload.subcategory,
        service_id=payload.service_id,
        assignment_group=payload.assignment_group,
        assigned_user_id=payload.assigned_user_id,
        reporter_user_id=current_user.id,
        problem_id=payload.problem_id,
        related_change_id=payload.related_change_id,
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db.add(new_inc)
    db.flush()

    # 4. Attach SLA Record
    target_hours = SLA_TARGET_HOURS.get(payload.priority, 24.0)
    sla_record = SLARecord(
        sla_id=f"SLA_INC_{incident_id}",
        name=f"Resolution SLA - {payload.priority}",
        service_id=payload.service_id,
        incident_id=incident_id,
        target_hours=target_hours,
        actual_hours=0.0,
        started_at=now,
        resolution_due_at=now + timedelta(hours=target_hours),
        status="IN_PROGRESS",
        breached=False,
        created_at=now,
        updated_at=now
    )
    db.add(sla_record)
    db.flush()

    new_state = _incident_to_dict(new_inc)
    _log_audit(db, current_user, "CREATE", incident_id, old_state=None, new_state=new_state)
    db.commit()
    db.refresh(new_inc)

    return _incident_to_dict(new_inc)


@router.patch("/{incident_id}/status", response_model=Dict[str, Any])
def update_incident_status(
    incident_id: str,
    payload: IncidentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("incidents.manage"))
):
    """
    Transitions incident status (NEW -> IN_PROGRESS -> ON_HOLD -> RESOLVED -> CLOSED).
    """
    incident = db.query(Incident).filter(
        (Incident.incident_id == incident_id) | (Incident.id == incident_id)
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    old_state = _incident_to_dict(incident)
    new_status = payload.status.upper()
    now = datetime.now()

    if new_status == incident.status:
        return old_state

    # When moving to IN_PROGRESS for the first time, stamp acknowledged_at
    if new_status == "IN_PROGRESS" and not incident.acknowledged_at:
        incident.acknowledged_at = now

    if new_status == "CLOSED" and not incident.closed_at:
        incident.closed_at = now

    incident.status = new_status
    incident.updated_at = now
    db.flush()

    new_state = _incident_to_dict(incident)
    _log_audit(db, current_user, f"STATUS_{new_status}", incident.incident_id, old_state=old_state, new_state=new_state)
    db.commit()
    db.refresh(incident)

    return _incident_to_dict(incident)


@router.patch("/{incident_id}/assign", response_model=Dict[str, Any])
def assign_incident(
    incident_id: str,
    payload: IncidentAssignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("incidents.manage"))
):
    """
    Reassigns incident to a specific user or operational assignment group.
    """
    incident = db.query(Incident).filter(
        (Incident.incident_id == incident_id) | (Incident.id == incident_id)
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    old_state = _incident_to_dict(incident)

    if payload.assigned_user_id is not None:
        user = db.query(User).filter(User.id == payload.assigned_user_id).first()
        if not user:
            raise HTTPException(status_code=400, detail=f"User ID '{payload.assigned_user_id}' not found.")
        incident.assigned_user_id = user.id

    if payload.assignment_group is not None:
        incident.assignment_group = payload.assignment_group

    incident.updated_at = datetime.now()
    db.flush()

    new_state = _incident_to_dict(incident)
    _log_audit(db, current_user, "REASSIGN", incident.incident_id, old_state=old_state, new_state=new_state)
    db.commit()
    db.refresh(incident)

    return _incident_to_dict(incident)


@router.post("/{incident_id}/resolve", response_model=Dict[str, Any])
def resolve_incident(
    incident_id: str,
    payload: IncidentResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("incidents.manage"))
):
    """
    Resolves an incident, computes MTTR resolution time, and evaluates SLA compliance.
    """
    incident = db.query(Incident).filter(
        (Incident.incident_id == incident_id) | (Incident.id == incident_id)
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    old_state = _incident_to_dict(incident)
    now = datetime.now()

    incident.status = "RESOLVED"
    incident.resolution_code = payload.resolution_code
    incident.resolution_notes = payload.resolution_notes
    incident.resolved_at = now

    # Compute MTTR hours
    if incident.opened_at:
        hours = (now - incident.opened_at).total_seconds() / 3600.0
        incident.resolution_time_hours = hours

        # Update SLA Record
        sla = db.query(SLARecord).filter(SLARecord.incident_id == incident.incident_id).first()
        if sla:
            sla.actual_hours = hours
            sla.resolved_at = now
            sla.breached = hours > sla.target_hours
            sla.status = "BREACHED" if sla.breached else "MET"
            sla.updated_at = now

    incident.updated_at = now
    db.flush()

    new_state = _incident_to_dict(incident)
    _log_audit(db, current_user, "RESOLVE", incident.incident_id, old_state=old_state, new_state=new_state)
    db.commit()
    db.refresh(incident)

    return _incident_to_dict(incident)
