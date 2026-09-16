import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.database import get_db
from backend.core.models import Change, Service, User, AuditEvent, Problem, Incident
from backend.api.v1.endpoints.auth import (
    get_current_user,
    require_permission
)

router = APIRouter()

# ============================================================================
# Schemas
# ============================================================================

class ChangeCreate(BaseModel):
    service_id: str
    title: str
    description: Optional[str] = None
    change_type: str = Field(default="NORMAL", pattern="^(STANDARD|NORMAL|EMERGENCY)$")
    risk_level: str = Field(default="MEDIUM", pattern="^(HIGH|MEDIUM|LOW)$")
    impact: Optional[str] = Field(default="MEDIUM", pattern="^(HIGH|MEDIUM|LOW)$")
    implementation_plan: Optional[str] = None
    rollback_plan: Optional[str] = None
    problem_id: Optional[str] = None
    assignment_group: Optional[str] = "Release Engineering"
    auto_submit_cab: bool = False

class ChangeCabDecision(BaseModel):
    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    comments: Optional[str] = None

class ChangeDeployAction(BaseModel):
    action: str = Field(..., pattern="^(START|COMPLETE)$")

class ChangeRollbackRequest(BaseModel):
    reason: str
    notes: Optional[str] = None

# ============================================================================
# Helpers
# ============================================================================

def _change_to_dict(chg: Change) -> Dict[str, Any]:
    return {
        "id": chg.id,
        "change_id": chg.change_id,
        "title": chg.title,
        "description": chg.description,
        "change_type": chg.change_type,
        "risk_level": chg.risk_level,
        "impact": chg.impact,
        "status": chg.status,
        "cab_status": chg.cab_status,
        "approval_status": chg.approval_status,
        "implementation_plan": chg.implementation_plan,
        "rollback_plan": chg.rollback_plan,
        "rollback_required": chg.rollback_required,
        "successful": chg.successful,
        "service_id": chg.service_id,
        "service_name": chg.service.service_name if chg.service else chg.service_id,
        "problem_id": chg.problem_id,
        "requester_user_id": chg.requester_user_id,
        "requester_username": chg.requester.username if chg.requester else None,
        "implementer_user_id": chg.implementer_user_id,
        "implementer_username": chg.implementer.username if chg.implementer else None,
        "assignment_group": chg.assignment_group,
        "implementation_start": chg.implementation_start.isoformat() if chg.implementation_start else None,
        "implementation_end": chg.implementation_end.isoformat() if chg.implementation_end else None,
        "completed_at": chg.completed_at.isoformat() if chg.completed_at else None,
        "created_at": chg.created_at.isoformat() if chg.created_at else None,
        "updated_at": chg.updated_at.isoformat() if chg.updated_at else None
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
        entity_type="Change",
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
def list_changes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    change_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    cab_status: Optional[str] = None,
    service_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Paginated query for changes with search, type, risk, and approval filters.
    """
    query = db.query(Change)

    if change_type and change_type.upper() != "ALL":
        query = query.filter(Change.change_type == change_type.upper())
    if risk_level and risk_level.upper() != "ALL":
        query = query.filter(Change.risk_level == risk_level.upper())
    if status and status.upper() != "ALL":
        query = query.filter(Change.status == status.upper())
    if cab_status and cab_status.upper() != "ALL":
        query = query.filter(Change.cab_status == cab_status.upper())
    if service_id and service_id.upper() != "ALL":
        query = query.filter(Change.service_id == service_id)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Change.change_id.ilike(s)) |
            (Change.title.ilike(s)) |
            (Change.description.ilike(s))
        )

    total = query.count()
    changes = query.order_by(desc(Change.created_at)).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [_change_to_dict(c) for c in changes]
    }


@router.get("/{change_id}", response_model=Dict[str, Any])
def get_change_detail(
    change_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns complete change dossier including correlated incidents, linked problem, and CAB approvals.
    """
    change = db.query(Change).filter(
        (Change.change_id == change_id) | (Change.id == change_id)
    ).first()
    if not change:
        raise HTTPException(status_code=404, detail=f"Change '{change_id}' not found.")

    # Correlated incidents
    correlated_incidents = db.query(Incident).filter(Incident.related_change_id == change.change_id).all()

    # Audit events
    audits = db.query(AuditEvent).filter(
        AuditEvent.entity_type == "Change",
        AuditEvent.entity_id == change.change_id
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

    detail = _change_to_dict(change)
    detail["correlated_incidents"] = [
        {
            "incident_id": inc.incident_id,
            "title": inc.title,
            "priority": inc.priority,
            "status": inc.status,
            "created_at": inc.created_at.isoformat() if inc.created_at else None
        }
        for inc in correlated_incidents
    ]
    detail["audit_trail"] = audit_list
    return detail


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
def create_change(
    payload: ChangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new Change Request in DRAFT or REQUESTED state and logs an AuditEvent.
    """
    # 1. Validate service
    service = db.query(Service).filter(Service.service_id == payload.service_id).first()
    if not service:
        raise HTTPException(status_code=400, detail=f"Service '{payload.service_id}' does not exist.")

    # 2. Validate problem if specified
    if payload.problem_id:
        prb = db.query(Problem).filter(Problem.problem_id == payload.problem_id).first()
        if not prb:
            raise HTTPException(status_code=400, detail=f"Linked problem '{payload.problem_id}' does not exist.")

    # 3. Generate unique change_id
    count = db.query(Change).count()
    change_id = f"CHG{(count + 1):06d}"
    while db.query(Change).filter(Change.change_id == change_id).first():
        count += 1
        change_id = f"CHG{(count + 1):06d}"

    now = datetime.now()
    initial_status = "REQUESTED" if payload.auto_submit_cab else "DRAFT"
    cab_status = "PENDING" if payload.auto_submit_cab else "NONE"

    # Standard changes with LOW risk can be pre-approved
    if payload.change_type == "STANDARD" and payload.risk_level == "LOW":
        initial_status = "APPROVED"
        cab_status = "APPROVED"

    new_chg = Change(
        change_id=change_id,
        title=payload.title,
        description=payload.description,
        change_type=payload.change_type,
        risk_level=payload.risk_level,
        impact=payload.impact,
        status=initial_status,
        cab_status=cab_status,
        approval_status="APPROVED" if cab_status == "APPROVED" else "PENDING",
        implementation_plan=payload.implementation_plan,
        rollback_plan=payload.rollback_plan,
        rollback_required=False,
        successful=True,
        service_id=payload.service_id,
        requester_user_id=current_user.id,
        implementer_user_id=None,
        assignment_group=payload.assignment_group,
        problem_id=payload.problem_id,
        created_at=now,
        updated_at=now
    )

    db.add(new_chg)
    db.flush()

    new_state = _change_to_dict(new_chg)
    _log_audit(db, current_user, "CREATE", change_id, old_state=None, new_state=new_state)
    db.commit()
    db.refresh(new_chg)

    return _change_to_dict(new_chg)


@router.post("/{change_id}/cab-review", response_model=Dict[str, Any])
def submit_to_cab(
    change_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits a draft or requested change to the Change Advisory Board (CAB) for formal review.
    """
    change = db.query(Change).filter(
        (Change.change_id == change_id) | (Change.id == change_id)
    ).first()
    if not change:
        raise HTTPException(status_code=404, detail=f"Change '{change_id}' not found.")

    old_state = _change_to_dict(change)
    change.status = "REQUESTED"
    change.cab_status = "PENDING"
    change.approval_status = "PENDING"
    change.updated_at = datetime.now()

    db.flush()
    new_state = _change_to_dict(change)
    _log_audit(db, current_user, "SUBMIT_TO_CAB", change.change_id, old_state=old_state, new_state=new_state)
    db.commit()
    db.refresh(change)

    return _change_to_dict(change)


@router.post("/{change_id}/approve", response_model=Dict[str, Any])
def cab_decision(
    change_id: str,
    payload: ChangeCabDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("changes.approve"))
):
    """
    CAB Approval or Rejection decision. Requires 'changes.approve' permission (ADMIN role).
    """
    change = db.query(Change).filter(
        (Change.change_id == change_id) | (Change.id == change_id)
    ).first()
    if not change:
        raise HTTPException(status_code=404, detail=f"Change '{change_id}' not found.")

    old_state = _change_to_dict(change)
    now = datetime.now()

    if payload.decision == "APPROVED":
        change.status = "APPROVED"
        change.cab_status = "APPROVED"
        change.approval_status = "APPROVED"
    else:
        change.status = "CANCELLED"
        change.cab_status = "REJECTED"
        change.approval_status = "REJECTED"

    change.updated_at = now
    db.flush()

    new_state = _change_to_dict(change)
    _log_audit(
        db,
        current_user,
        f"CAB_{payload.decision}",
        change.change_id,
        old_state=old_state,
        new_state=new_state
    )
    db.commit()
    db.refresh(change)

    return _change_to_dict(change)


@router.post("/{change_id}/deploy", response_model=Dict[str, Any])
def deploy_change(
    change_id: str,
    payload: ChangeDeployAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tracks implementation lifecycle:
    - START: Transitions from APPROVED to IN_PROGRESS and sets implementation_start.
    - COMPLETE: Transitions from IN_PROGRESS to COMPLETED, sets implementation_end and completed_at.
    """
    change = db.query(Change).filter(
        (Change.change_id == change_id) | (Change.id == change_id)
    ).first()
    if not change:
        raise HTTPException(status_code=404, detail=f"Change '{change_id}' not found.")

    old_state = _change_to_dict(change)
    now = datetime.now()

    if payload.action == "START":
        if change.status not in ["APPROVED", "EMERGENCY"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot start deployment. Change must be 'APPROVED' (current: '{change.status}')."
            )
        change.status = "IN_PROGRESS"
        change.implementation_start = now
        change.implementer_user_id = current_user.id
    elif payload.action == "COMPLETE":
        if change.status != "IN_PROGRESS":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot complete deployment. Change is not in 'IN_PROGRESS' (current: '{change.status}')."
            )
        change.status = "COMPLETED"
        change.implementation_end = now
        change.completed_at = now
        change.successful = True

    change.updated_at = now
    db.flush()

    new_state = _change_to_dict(change)
    _log_audit(db, current_user, f"DEPLOY_{payload.action}", change.change_id, old_state=old_state, new_state=new_state)
    db.commit()
    db.refresh(change)

    return _change_to_dict(change)


@router.post("/{change_id}/rollback", response_model=Dict[str, Any])
def record_rollback(
    change_id: str,
    payload: ChangeRollbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes and documents an emergency deployment rollback. Marks change as FAILED.
    """
    change = db.query(Change).filter(
        (Change.change_id == change_id) | (Change.id == change_id)
    ).first()
    if not change:
        raise HTTPException(status_code=404, detail=f"Change '{change_id}' not found.")

    old_state = _change_to_dict(change)
    now = datetime.now()

    change.status = "FAILED"
    change.rollback_required = True
    change.successful = False
    change.implementation_end = now
    change.completed_at = now
    change.updated_at = now

    db.flush()

    new_state = _change_to_dict(change)
    new_state["rollback_reason"] = payload.reason
    new_state["rollback_notes"] = payload.notes

    _log_audit(db, current_user, "ROLLBACK_TRIGGERED", change.change_id, old_state=old_state, new_state=new_state)
    db.commit()
    db.refresh(change)

    return _change_to_dict(change)
