import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.core.models import Problem, Service, User, AuditEvent, Incident
from backend.api.v1.endpoints.auth import (
    get_current_user,
    require_permission
)

router = APIRouter()

# ============================================================================
# Schemas
# ============================================================================

class ProblemCreate(BaseModel):
    service_id: str
    title: str
    description: Optional[str] = None
    priority: str = Field(default="P2", pattern="^(P1|P2|P3|P4)$")
    category: Optional[str] = "Infrastructure"
    assignment_group: Optional[str] = "Tier-3 Operations"
    owner_user_id: Optional[str] = None
    target_resolution_days: Optional[int] = 14

class ProblemStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(OPEN|INVESTIGATING|KNOWN_ERROR|RESOLVED|CLOSED)$")

class ProblemInvestigationUpdate(BaseModel):
    root_cause_category: Optional[str] = None
    root_cause_text: Optional[str] = None
    workaround: Optional[str] = None
    kedb_status: Optional[str] = Field(None, pattern="^(NONE|DRAFT|PUBLISHED)$")

class ProblemAssignUpdate(BaseModel):
    owner_user_id: Optional[str] = None
    assignment_group: Optional[str] = None

class ProblemResolveRequest(BaseModel):
    resolution: str
    root_cause_category: Optional[str] = None
    root_cause_text: Optional[str] = None
    workaround: Optional[str] = None
    kedb_status: Optional[str] = "PUBLISHED"

class AuditEventItem(BaseModel):
    id: str
    actor_username: Optional[str]
    action: str
    timestamp_utc: datetime
    old_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None

# ============================================================================
# Helpers
# ============================================================================

def _problem_to_dict(prb: Problem) -> Dict[str, Any]:
    return {
        "id": prb.id,
        "problem_id": prb.problem_id,
        "title": prb.title,
        "description": prb.description,
        "priority": prb.priority,
        "status": prb.status,
        "category": prb.category,
        "root_cause_category": prb.root_cause_category,
        "root_cause_text": prb.root_cause_text,
        "workaround": prb.workaround,
        "resolution": prb.resolution,
        "kedb_status": prb.kedb_status,
        "service_id": prb.service_id,
        "service_name": prb.service.service_name if prb.service else prb.service_id,
        "owner_user_id": prb.owner_user_id,
        "owner_username": prb.owner.username if prb.owner else None,
        "assignment_group": prb.assignment_group,
        "age_days": round(prb.age_days, 1) if prb.age_days is not None else 0.0,
        "opened_at": prb.opened_at.isoformat() if prb.opened_at else None,
        "resolved_at": prb.resolved_at.isoformat() if prb.resolved_at else None,
        "closed_at": prb.closed_at.isoformat() if prb.closed_at else None,
        "created_at": prb.created_at.isoformat() if prb.created_at else None,
        "updated_at": prb.updated_at.isoformat() if prb.updated_at else None,
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
        entity_type="Problem",
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
def list_problems(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    service_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Paginated query for problems with search and multi-attribute filters.
    """
    query = db.query(Problem)

    if status and status.upper() != "ALL":
        query = query.filter(Problem.status == status.upper())
    if priority and priority.upper() != "ALL":
        query = query.filter(Problem.priority == priority.upper())
    if service_id and service_id.upper() != "ALL":
        query = query.filter(Problem.service_id == service_id)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Problem.problem_id.ilike(s)) |
            (Problem.title.ilike(s)) |
            (Problem.description.ilike(s)) |
            (Problem.root_cause_category.ilike(s))
        )

    total = query.count()
    problems = query.order_by(desc(Problem.opened_at)).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [_problem_to_dict(p) for p in problems]
    }


@router.get("/{problem_id}", response_model=Dict[str, Any])
def get_problem_detail(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves complete problem dossier including linked incidents, corrective actions, and audit trail.
    """
    problem = db.query(Problem).filter(
        (Problem.problem_id == problem_id) | (Problem.id == problem_id)
    ).first()
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")

    # Linked incidents
    linked_incidents = db.query(Incident).filter(Incident.problem_id == problem.problem_id).all()

    # Audit events
    audits = db.query(AuditEvent).filter(
        AuditEvent.entity_type == "Problem",
        AuditEvent.entity_id == problem.problem_id
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

    detail = _problem_to_dict(problem)
    detail["linked_incidents"] = [
        {
            "incident_id": inc.incident_id,
            "title": inc.title,
            "priority": inc.priority,
            "status": inc.status,
            "resolution_time_hours": inc.resolution_time_hours,
            "created_at": inc.created_at.isoformat() if inc.created_at else None
        }
        for inc in linked_incidents
    ]
    detail["audit_trail"] = audit_list
    return detail


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
def create_problem(
    payload: ProblemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("problems.manage"))
):
    """
    Creates a new Problem record in OPEN state and records an immutable AuditEvent.
    """
    # 1. Validate service
    service = db.query(Service).filter(Service.service_id == payload.service_id).first()
    if not service:
        raise HTTPException(status_code=400, detail=f"Service '{payload.service_id}' does not exist.")

    # 2. Generate unique problem_id
    count = db.query(Problem).count()
    problem_id = f"PRB{(count + 1):06d}"
    # Ensure uniqueness
    while db.query(Problem).filter(Problem.problem_id == problem_id).first():
        count += 1
        problem_id = f"PRB{(count + 1):06d}"

    now = datetime.now()
    target_res = now + (payload.target_resolution_days and __import__("datetime").timedelta(days=payload.target_resolution_days) or __import__("datetime").timedelta(days=14))

    new_prb = Problem(
        problem_id=problem_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status="OPEN",
        category=payload.category,
        kedb_status="NONE",
        service_id=payload.service_id,
        owner_user_id=payload.owner_user_id or current_user.id,
        assignment_group=payload.assignment_group,
        age_days=0.0,
        opened_at=now,
        target_resolution_at=target_res,
        created_at=now,
        updated_at=now
    )

    db.add(new_prb)
    db.flush()

    new_state = _problem_to_dict(new_prb)
    _log_audit(db, current_user, "CREATE", problem_id, old_state=None, new_state=new_state)
    db.commit()
    db.refresh(new_prb)

    return _problem_to_dict(new_prb)


@router.patch("/{problem_id}/status", response_model=Dict[str, Any])
def update_problem_status(
    problem_id: str,
    payload: ProblemStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("problems.manage"))
):
    """
    Enforces valid state machine transitions:
    OPEN -> INVESTIGATING -> KNOWN_ERROR -> RESOLVED -> CLOSED
    """
    problem = db.query(Problem).filter(
        (Problem.problem_id == problem_id) | (Problem.id == problem_id)
    ).first()
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")

    old_state = _problem_to_dict(problem)
    new_status = payload.status.upper()
    current_status = problem.status.upper()

    if new_status == current_status:
        return old_state

    # Valid transitions
    allowed_transitions = {
        "OPEN": ["INVESTIGATING", "CLOSED"],
        "INVESTIGATING": ["KNOWN_ERROR", "RESOLVED", "CLOSED"],
        "KNOWN_ERROR": ["RESOLVED", "CLOSED", "INVESTIGATING"],
        "RESOLVED": ["CLOSED", "INVESTIGATING"],
        "CLOSED": ["OPEN"]  # Reopen if necessary
    }

    if new_status not in allowed_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from '{current_status}' to '{new_status}'. Allowed: {allowed_transitions.get(current_status, [])}"
        )

    # Validation rules for destination states
    if new_status == "KNOWN_ERROR" and not problem.workaround:
        raise HTTPException(
            status_code=400,
            detail="Cannot mark as KNOWN_ERROR without documenting a documented workaround."
        )

    if new_status == "RESOLVED":
        if not problem.resolution:
            raise HTTPException(
                status_code=400,
                detail="Cannot resolve problem without a resolution statement. Use /resolve endpoint."
            )

    now = datetime.now()
    problem.status = new_status
    problem.updated_at = now

    if new_status == "RESOLVED" and not problem.resolved_at:
        problem.resolved_at = now
        if problem.opened_at:
            problem.age_days = (now - problem.opened_at).total_seconds() / 86400.0

    if new_status == "CLOSED" and not problem.closed_at:
        problem.closed_at = now

    db.flush()
    new_state = _problem_to_dict(problem)
    _log_audit(db, current_user, f"STATUS_{new_status}", problem.problem_id, old_state=old_state, new_state=new_state)
    db.commit()
    db.refresh(problem)

    return _problem_to_dict(problem)


@router.patch("/{problem_id}/investigation", response_model=Dict[str, Any])
def update_problem_investigation(
    problem_id: str,
    payload: ProblemInvestigationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("problems.manage"))
):
    """
    Updates root-cause hypothesis, categories, workaround, and KEDB publishing status.
    """
    problem = db.query(Problem).filter(
        (Problem.problem_id == problem_id) | (Problem.id == problem_id)
    ).first()
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")

    old_state = _problem_to_dict(problem)

    if payload.root_cause_category is not None:
        problem.root_cause_category = payload.root_cause_category
    if payload.root_cause_text is not None:
        problem.root_cause_text = payload.root_cause_text
    if payload.workaround is not None:
        problem.workaround = payload.workaround
    if payload.kedb_status is not None:
        problem.kedb_status = payload.kedb_status

    problem.updated_at = datetime.now()
    db.flush()

    new_state = _problem_to_dict(problem)
    _log_audit(db, current_user, "UPDATE_INVESTIGATION", problem.problem_id, old_state=old_state, new_state=new_state)
    db.commit()
    db.refresh(problem)

    return _problem_to_dict(problem)


@router.patch("/{problem_id}/assign", response_model=Dict[str, Any])
def assign_problem(
    problem_id: str,
    payload: ProblemAssignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("problems.manage"))
):
    """
    Reassigns problem ownership or target engineering assignment group.
    """
    problem = db.query(Problem).filter(
        (Problem.problem_id == problem_id) | (Problem.id == problem_id)
    ).first()
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")

    old_state = _problem_to_dict(problem)

    if payload.owner_user_id is not None:
        user = db.query(User).filter(User.id == payload.owner_user_id).first()
        if not user:
            raise HTTPException(status_code=400, detail=f"User ID '{payload.owner_user_id}' not found.")
        problem.owner_user_id = user.id

    if payload.assignment_group is not None:
        problem.assignment_group = payload.assignment_group

    problem.updated_at = datetime.now()
    db.flush()

    new_state = _problem_to_dict(problem)
    _log_audit(db, current_user, "REASSIGN", problem.problem_id, old_state=old_state, new_state=new_state)
    db.commit()
    db.refresh(problem)

    return _problem_to_dict(problem)


@router.post("/{problem_id}/resolve", response_model=Dict[str, Any])
def resolve_problem(
    problem_id: str,
    payload: ProblemResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("problems.manage"))
):
    """
    Resolves the problem record, records permanent resolution, computes age, and publishes to KEDB.
    """
    problem = db.query(Problem).filter(
        (Problem.problem_id == problem_id) | (Problem.id == problem_id)
    ).first()
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found.")

    old_state = _problem_to_dict(problem)
    now = datetime.now()

    problem.status = "RESOLVED"
    problem.resolution = payload.resolution
    if payload.root_cause_category:
        problem.root_cause_category = payload.root_cause_category
    if payload.root_cause_text:
        problem.root_cause_text = payload.root_cause_text
    if payload.workaround:
        problem.workaround = payload.workaround
    if payload.kedb_status:
        problem.kedb_status = payload.kedb_status

    problem.resolved_at = now
    if problem.opened_at:
        problem.age_days = (now - problem.opened_at).total_seconds() / 86400.0

    problem.updated_at = now
    db.flush()

    new_state = _problem_to_dict(problem)
    _log_audit(db, current_user, "RESOLVE", problem.problem_id, old_state=old_state, new_state=new_state)
    db.commit()
    db.refresh(problem)

    return _problem_to_dict(problem)
