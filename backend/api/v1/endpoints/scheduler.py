import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.database import get_db
from backend.core.models import ScheduledJob, JobExecution, SchedulerRun, User
from backend.core.scheduler import (
    scheduler,
    validate_cron_expression,
    validate_timezone,
    calculate_next_run_time,
    APPROVED_JOB_HANDLERS
)
from backend.api.v1.endpoints.auth import (
    get_current_user,
    require_permission
)

router = APIRouter()

# ============================================================================
# Schemas
# ============================================================================

class JobCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    job_type: str = Field(..., description="Must be an approved job type")
    cron_expression: str = Field(..., description="Standard 5-part cron syntax")
    timezone: str = Field("UTC", description="Valid IANA timezone (e.g. UTC, America/New_York)")
    payload: Optional[Dict[str, Any]] = None
    max_retries: int = Field(3, ge=0, le=10)
    retry_delay_seconds: int = Field(60, ge=5, le=3600)
    concurrency_policy: str = Field("FORBID", description="FORBID | ALLOW | REPLACE")
    enabled: bool = True

class JobUpdateRequest(BaseModel):
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    max_retries: Optional[int] = None
    retry_delay_seconds: Optional[int] = None
    concurrency_policy: Optional[str] = None
    status: Optional[str] = None

# ============================================================================
# Status & Diagnostics
# ============================================================================

@router.get("/status")
def get_scheduler_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.read"))
):
    """Returns runtime health status, worker metadata, and active job metrics."""
    total_jobs = db.query(ScheduledJob).count()
    active_jobs = db.query(ScheduledJob).filter(ScheduledJob.status == "ACTIVE").count()
    running_executions = db.query(JobExecution).filter(JobExecution.status == "RUNNING").count()
    retrying_executions = db.query(JobExecution).filter(JobExecution.status == "RETRYING").count()

    return {
        "status": "RUNNING" if scheduler.is_running else "STOPPED",
        "worker_id": scheduler.worker_id,
        "poll_interval_seconds": scheduler.poll_interval,
        "lease_duration_seconds": scheduler.lease_duration,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "running_executions": running_executions,
        "retrying_executions": retrying_executions,
        "approved_handlers": APPROVED_JOB_HANDLERS
    }


# ============================================================================
# Job Registry CRUD Endpoints
# ============================================================================

@router.get("/jobs")
def list_scheduled_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.read"))
):
    """Lists all persistent scheduled jobs."""
    jobs = db.query(ScheduledJob).order_by(ScheduledJob.created_at.desc()).all()
    results = []
    for j in jobs:
        payload = json.loads(j.payload_json) if j.payload_json else {}
        results.append({
            "id": j.id,
            "name": j.name,
            "description": j.description,
            "job_type": j.job_type,
            "status": j.status,
            "cron_expression": j.cron_expression,
            "timezone": j.timezone,
            "payload": payload,
            "owner_username": j.owner.username if j.owner else None,
            "next_run_at": j.next_run_at.isoformat() if j.next_run_at else None,
            "last_run_at": j.last_run_at.isoformat() if j.last_run_at else None,
            "last_success_at": j.last_success_at.isoformat() if j.last_success_at else None,
            "last_failure_at": j.last_failure_at.isoformat() if j.last_failure_at else None,
            "max_retries": j.max_retries,
            "retry_delay_seconds": j.retry_delay_seconds,
            "concurrency_policy": j.concurrency_policy,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "updated_at": j.updated_at.isoformat() if j.updated_at else None,
        })
    return results


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
def create_scheduled_job(
    req: JobCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.manage"))
):
    """Registers a new persistent scheduled job."""
    # 1. Validate Job Type
    if req.job_type not in APPROVED_JOB_HANDLERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job_type '{req.job_type}'. Approved types: {list(APPROVED_JOB_HANDLERS.keys())}"
        )

    # 2. Validate Cron Expression
    if not validate_cron_expression(req.cron_expression):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cron_expression '{req.cron_expression}'."
        )

    # 3. Validate Timezone
    try:
        norm_tz = validate_timezone(req.timezone)
    except ValueError as tz_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(tz_err))

    # 4. Check Unique Name
    existing = db.query(ScheduledJob).filter(ScheduledJob.name == req.name.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scheduled job with name '{req.name}' already exists."
        )

    next_run = calculate_next_run_time(req.cron_expression, norm_tz) if req.enabled else None

    job = ScheduledJob(
        name=req.name.strip(),
        description=req.description,
        job_type=req.job_type,
        status="ACTIVE" if req.enabled else "PAUSED",
        cron_expression=req.cron_expression.strip(),
        timezone=norm_tz,
        payload_json=json.dumps(req.payload) if req.payload else None,
        owner_user_id=current_user.id,
        next_run_at=next_run,
        max_retries=req.max_retries,
        retry_delay_seconds=req.retry_delay_seconds,
        concurrency_policy=req.concurrency_policy.upper() if req.concurrency_policy in ("FORBID", "ALLOW", "REPLACE") else "FORBID"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "status": "CREATED",
        "id": job.id,
        "name": job.name,
        "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None
    }


@router.get("/jobs/{job_id}")
def get_scheduled_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.read"))
):
    """Retrieves specific scheduled job details."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    payload = json.loads(job.payload_json) if job.payload_json else {}
    return {
        "id": job.id,
        "name": job.name,
        "description": job.description,
        "job_type": job.job_type,
        "status": job.status,
        "cron_expression": job.cron_expression,
        "timezone": job.timezone,
        "payload": payload,
        "owner_username": job.owner.username if job.owner else None,
        "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
        "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None,
        "last_success_at": job.last_success_at.isoformat() if job.last_success_at else None,
        "last_failure_at": job.last_failure_at.isoformat() if job.last_failure_at else None,
        "max_retries": job.max_retries,
        "retry_delay_seconds": job.retry_delay_seconds,
        "concurrency_policy": job.concurrency_policy,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


@router.put("/jobs/{job_id}")
def update_scheduled_job(
    job_id: str,
    req: JobUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.manage"))
):
    """Updates an existing scheduled job."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    if req.cron_expression is not None:
        if not validate_cron_expression(req.cron_expression):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cron expression.")
        job.cron_expression = req.cron_expression.strip()

    if req.timezone is not None:
        try:
            job.timezone = validate_timezone(req.timezone)
        except ValueError as tz_err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(tz_err))

    if req.description is not None:
        job.description = req.description
    if req.payload is not None:
        job.payload_json = json.dumps(req.payload)
    if req.max_retries is not None:
        job.max_retries = max(0, min(10, req.max_retries))
    if req.retry_delay_seconds is not None:
        job.retry_delay_seconds = max(5, req.retry_delay_seconds)
    if req.concurrency_policy is not None and req.concurrency_policy.upper() in ("FORBID", "ALLOW", "REPLACE"):
        job.concurrency_policy = req.concurrency_policy.upper()
    if req.status is not None and req.status.upper() in ("ACTIVE", "PAUSED", "DISABLED", "ERROR"):
        job.status = req.status.upper()

    if job.status == "ACTIVE":
        job.next_run_at = calculate_next_run_time(job.cron_expression, job.timezone)
    else:
        job.next_run_at = None

    job.updated_at = datetime.now()
    db.commit()

    return {"status": "UPDATED", "id": job.id, "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None}


@router.delete("/jobs/{job_id}")
def delete_scheduled_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.manage"))
):
    """Deletes a scheduled job and cascades to executions."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    db.delete(job)
    db.commit()
    return {"status": "DELETED", "id": job_id}


@router.post("/jobs/{job_id}/pause")
def pause_scheduled_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.manage"))
):
    """Pauses a scheduled job."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    job.status = "PAUSED"
    job.next_run_at = None
    job.updated_at = datetime.now()
    db.commit()
    return {"status": "PAUSED", "id": job.id}


@router.post("/jobs/{job_id}/resume")
def resume_scheduled_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.manage"))
):
    """Resumes a paused job and recalculates next run time."""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    job.status = "ACTIVE"
    job.next_run_at = calculate_next_run_time(job.cron_expression, job.timezone)
    job.updated_at = datetime.now()
    db.commit()
    return {"status": "RESUMED", "id": job.id, "next_run_at": job.next_run_at.isoformat()}


@router.post("/jobs/{job_id}/execute")
def execute_scheduled_job_now(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.execute"))
):
    """Triggers immediate ad-hoc execution of a registered job."""
    try:
        return scheduler.trigger_ad_hoc_job(job_id=job_id, actor_username=current_user.username)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ============================================================================
# Execution History & Retry Endpoints
# ============================================================================

@router.get("/executions")
def list_job_executions(
    limit: int = 50,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.history"))
):
    """Returns execution run history across all scheduled jobs."""
    query = db.query(JobExecution)
    if status_filter:
        query = query.filter(JobExecution.status == status_filter.upper())
    
    executions = query.order_by(JobExecution.started_at.desc()).limit(limit).all()
    results = []
    for e in executions:
        results.append({
            "id": e.id,
            "job_id": e.job_id,
            "job_name": e.job.name if e.job else "Ad-Hoc / Trigger",
            "job_type": e.job.job_type if e.job else "report.generate",
            "run_id": e.run_id,
            "worker_id": e.worker_id,
            "status": e.status,
            "attempt_number": e.attempt_number,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "finished_at": e.finished_at.isoformat() if e.finished_at else None,
            "next_retry_at": e.next_retry_at.isoformat() if e.next_retry_at else None,
            "error_class": e.error_class,
            "error_message": e.error_message,
            "correlation_id": e.correlation_id,
            "deliveries_count": len(e.deliveries)
        })
    return results


@router.get("/jobs/{job_id}/executions")
def list_job_specific_executions(
    job_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.history"))
):
    """Returns execution history for a specific scheduled job."""
    executions = db.query(JobExecution).filter(
        JobExecution.job_id == job_id
    ).order_by(JobExecution.started_at.desc()).limit(limit).all()

    return [
        {
            "id": e.id,
            "run_id": e.run_id,
            "worker_id": e.worker_id,
            "status": e.status,
            "attempt_number": e.attempt_number,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "finished_at": e.finished_at.isoformat() if e.finished_at else None,
            "error_message": e.error_message,
            "result": json.loads(e.result_json) if e.result_json else None
        }
        for e in executions
    ]


@router.post("/executions/{execution_id}/retry")
def retry_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.execute"))
):
    """Manually retries a failed execution."""
    execution = db.query(JobExecution).filter(JobExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Execution '{execution_id}' not found.")

    execution.status = "RETRYING"
    execution.next_retry_at = datetime.now()
    db.commit()

    return {"status": "QUEUED_FOR_RETRY", "id": execution.id}


@router.post("/executions/{execution_id}/cancel")
def cancel_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("scheduler.manage"))
):
    """Cancels a queued or retrying execution."""
    execution = db.query(JobExecution).filter(JobExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Execution '{execution_id}' not found.")

    execution.status = "CANCELLED"
    execution.finished_at = datetime.now()
    execution.error_message = f"Cancelled by user {current_user.username}"
    db.commit()

    return {"status": "CANCELLED", "id": execution.id}


# ============================================================================
# Legacy Backward Compatibility Endpoints
# ============================================================================

@router.get("/history")
def get_scheduler_history(limit: int = 10, db: Session = Depends(get_db)):
    """
    Backward-compatible history endpoint for existing clients.
    """
    runs = db.query(SchedulerRun).order_by(SchedulerRun.triggered_at.desc()).limit(limit).all()
    results = []
    for r in runs:
        channels = json.loads(r.channels_json) if r.channels_json else {}
        results.append({
            "run_id": r.run_id,
            "period": r.period,
            "triggered_at": r.triggered_at.isoformat() if r.triggered_at else None,
            "status": r.status,
            "filepath": r.filepath,
            "channels": channels
        })
    return results


@router.post("/trigger")
def trigger_scheduled_job(period: str = "daily"):
    """
    Backward-compatible trigger endpoint for immediate background scheduler jobs.
    """
    scheduler._execute_job(period=period)
    return {"status": "TRIGGERED", "period": period}
