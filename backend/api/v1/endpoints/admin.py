import os
import glob
import subprocess
import sys
import threading
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models import (
    Service,
    Incident,
    Problem,
    Change,
    SLARecord,
    SchedulerRun,
    JobExecution,
    NotificationDelivery,
    IngestionJob,
    DatasetVersion,
    User,
    Role,
    Permission
)
from backend.core.security import hash_password, verify_password, bootstrap_security
from backend.config import settings

router = APIRouter()

# ============================================================================
# Admin User Management Pydantic Schemas
# ============================================================================

class UserAdminListItem(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    is_active: bool
    roles: List[str]
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime


class CreateUserRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    roles: List[str] = ["VIEWER"]
    is_active: bool = True


class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


class ResetPasswordRequest(BaseModel):
    new_password: str


# ============================================================================
# Admin User Management Endpoints
# ============================================================================

@router.get("/users", response_model=List[UserAdminListItem])
def list_users(db: Session = Depends(get_db)):
    """
    Lists all persistent user accounts, their roles, and current security status.
    """
    users = db.query(User).all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "display_name": u.display_name or u.username,
            "is_active": u.is_active,
            "roles": [r.name for r in u.roles],
            "last_login_at": u.last_login_at,
            "failed_login_attempts": u.failed_login_attempts,
            "locked_until": u.locked_until,
            "created_at": u.created_at
        })
    return result


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(req: CreateUserRequest, db: Session = Depends(get_db)):
    """
    Creates a new user account with hashed password and assigned roles.
    """
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{req.username}' already exists."
        )

    if req.email and db.query(User).filter(User.email == req.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{req.email}' is already registered."
        )

    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters in length."
        )

    # Resolve roles
    roles_in_db = db.query(Role).filter(Role.name.in_([r.upper() for r in req.roles])).all()
    if not roles_in_db:
        # Default to VIEWER if invalid
        viewer_role = db.query(Role).filter(Role.name == "VIEWER").first()
        roles_in_db = [viewer_role] if viewer_role else []

    new_user = User(
        username=req.username,
        email=req.email,
        display_name=req.display_name or req.username,
        password_hash=hash_password(req.password),
        is_active=req.is_active,
        token_version=1
    )
    new_user.roles = roles_in_db
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "status": "SUCCESS",
        "message": f"User '{new_user.username}' created successfully.",
        "user_id": new_user.id
    }


@router.get("/users/{user_id}")
def get_user_detail(user_id: str, db: Session = Depends(get_db)):
    """
    Retrieves detailed account information for a specific user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name or user.username,
        "is_active": user.is_active,
        "roles": [r.name for r in user.roles],
        "permissions": user.permission_names,
        "failed_login_attempts": user.failed_login_attempts,
        "locked_until": user.locked_until,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }


@router.put("/users/{user_id}")
def update_user(user_id: str, req: UpdateUserRequest, db: Session = Depends(get_db)):
    """
    Updates user display name, email, active status, and role assignments.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Safeguard: prevent disabling the last active admin
    if req.is_active is False and "ADMIN" in [r.name.upper() for r in user.roles]:
        admin_count = db.query(User).join(User.roles).filter(Role.name == "ADMIN", User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot disable the last active administrator account."
            )

    if req.display_name is not None:
        user.display_name = req.display_name

    if req.email is not None:
        user.email = req.email

    if req.is_active is not None:
        user.is_active = req.is_active
        if not req.is_active:
            user.token_version += 1  # Revoke tokens when disabled

    if req.roles is not None:
        roles_in_db = db.query(Role).filter(Role.name.in_([r.upper() for r in req.roles])).all()
        if roles_in_db:
            user.roles = roles_in_db
            user.token_version += 1  # Invalidate tokens when roles change

    db.commit()
    return {"status": "SUCCESS", "message": f"User '{user.username}' updated successfully."}


@router.post("/users/{user_id}/reset-password")
def admin_reset_password(user_id: str, req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Administratively resets a user's password and revokes all their active sessions.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters in length.")

    user.password_hash = hash_password(req.new_password)
    user.token_version += 1  # Revoke all existing tokens
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    return {
        "status": "SUCCESS",
        "message": f"Password for user '{user.username}' reset successfully. All active sessions have been invalidated."
    }


@router.post("/users/{user_id}/revoke-tokens")
def admin_revoke_tokens(user_id: str, db: Session = Depends(get_db)):
    """
    Forces immediate invalidation of all active JWT tokens for the specified user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.token_version += 1
    db.commit()

    return {
        "status": "SUCCESS",
        "message": f"All active sessions and tokens for user '{user.username}' have been invalidated."
    }


@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """
    Deletes a user account with safeguards against deleting the last admin.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if "ADMIN" in [r.name.upper() for r in user.roles]:
        admin_count = db.query(User).join(User.roles).filter(Role.name == "ADMIN", User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last active administrator account."
            )

    db.delete(user)
    db.commit()
    return {"status": "SUCCESS", "message": f"User '{user.username}' deleted successfully."}


# ============================================================================
# Operational Reseed, Purge & Maintenance Endpoints
# ============================================================================

RESEED_LOCK = threading.Lock()
RESEED_STATE = {
    "status": "IDLE",
    "message": "Database is ready.",
    "started_at": None,
    "completed_at": None,
    "error": None
}

def _execute_reseed_background():
    global RESEED_STATE
    with RESEED_LOCK:
        RESEED_STATE["status"] = "IN_PROGRESS"
        RESEED_STATE["message"] = "Generating synthetic operational records..."
        RESEED_STATE["started_at"] = datetime.now().isoformat()
        RESEED_STATE["error"] = None

        try:
            script_path = os.path.join(settings.PROJECT_ROOT, "scripts", "generate_data.py")
            env = os.environ.copy()
            env["PYTHONPATH"] = settings.PROJECT_ROOT

            result = subprocess.run(
                [sys.executable, script_path],
                cwd=settings.PROJECT_ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode != 0:
                raise Exception(result.stderr or "Script returned error code.")

            RESEED_STATE["status"] = "SUCCESS"
            RESEED_STATE["message"] = "Data re-seeding completed! Fresh operational records populated into database."
            RESEED_STATE["completed_at"] = datetime.now().isoformat()
        except Exception as e:
            RESEED_STATE["status"] = "FAILED"
            RESEED_STATE["error"] = str(e)
            RESEED_STATE["message"] = f"Re-seeding failed: {str(e)}"
            RESEED_STATE["completed_at"] = datetime.now().isoformat()

@router.get("/reseed-status")
def get_reseed_status():
    """Returns current status of background data generation / reseeding job."""
    return RESEED_STATE

@router.post("/remove-all-data")
def remove_all_data(db: Session = Depends(get_db)):
    """Wipes all transactional operational data while strictly preserving user identity and RBAC tables."""
    try:
        db.query(NotificationDelivery).delete()
        db.query(JobExecution).delete()
        db.query(SLARecord).delete()
        db.query(Incident).delete()
        db.query(Problem).delete()
        db.query(Change).delete()
        db.query(SchedulerRun).delete()
        db.query(IngestionJob).delete()
        db.query(DatasetVersion).delete()
        db.query(Service).delete()
        db.commit()
        return {
            "status": "SUCCESS",
            "message": "All operational data (incidents, problems, changes, SLAs, services) cleared successfully. User accounts preserved."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove data: {str(e)}")

@router.post("/reseed-data")
def reseed_data(background_tasks: BackgroundTasks, wait: bool = False):
    """Triggers synthetic data generation script non-blocking in background."""
    if RESEED_STATE["status"] == "IN_PROGRESS":
        return {
            "status": "IN_PROGRESS",
            "message": "Data re-seeding is already in progress.",
            "started_at": RESEED_STATE["started_at"]
        }

    if wait:
        _execute_reseed_background()
        if RESEED_STATE["status"] == "FAILED":
            raise HTTPException(status_code=500, detail=RESEED_STATE["error"])
        return RESEED_STATE

    background_tasks.add_task(_execute_reseed_background)
    return {
        "status": "IN_PROGRESS",
        "message": "Data re-seeding initiated in background.",
        "started_at": datetime.now().isoformat()
    }

@router.post("/purge-reports")
def purge_reports():
    """Clears generated Markdown and PDF report files from reports/ directory."""
    reports_dir = os.path.join(settings.PROJECT_ROOT, "reports")
    purged_count = 0
    if os.path.exists(reports_dir):
        files = glob.glob(os.path.join(reports_dir, "*.*"))
        for f in files:
            if f.endswith(".md") or f.endswith(".pdf") or f.endswith(".json"):
                try:
                    os.remove(f)
                    purged_count += 1
                except Exception:
                    pass
    return {
        "status": "SUCCESS",
        "purged_count": purged_count,
        "message": f"Purged {purged_count} generated report documents from reports/ storage directory."
    }

@router.post("/clear-scheduler-history")
def clear_scheduler_history(db: Session = Depends(get_db)):
    """Clears scheduler execution audit history from database."""
    try:
        del_deliveries = db.query(NotificationDelivery).delete()
        del_executions = db.query(JobExecution).delete()
        deleted = db.query(SchedulerRun).delete()
        db.commit()
        return {
            "status": "SUCCESS",
            "deleted_count": deleted + del_executions,
            "message": f"Cleared {deleted + del_executions} scheduler run log records from database."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed clearing scheduler history: {str(e)}")
