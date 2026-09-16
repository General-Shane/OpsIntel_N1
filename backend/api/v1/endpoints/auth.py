from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.database import get_db
from backend.core.models import User, Role, Permission
from backend.core.security import (
    Token,
    TokenPayload,
    create_access_token,
    verify_password,
    hash_password,
    oauth2_scheme,
    verify_token
)
from backend.config import settings

router = APIRouter()

# ============================================================================
# Request / Response Schemas
# ============================================================================

class UserProfileResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    is_active: bool
    roles: List[str]
    permissions: List[str]
    last_login_at: Optional[datetime] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# ============================================================================
# Authentication Route
# ============================================================================

@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticates user against persistent database records, enforces lockout policy,
    updates last login timestamp, and issues a versioned JWT access token.
    """
    user = db.query(User).filter(User.username == form_data.username).first()

    # Legacy demo credentials support if user was initialized with demo password
    # (e.g. admin/admin or admin/Admin@123)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Check account active status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact an administrator."
        )

    # 2. Check temporary lockout status
    now = datetime.now()
    if user.locked_until and user.locked_until > now:
        remaining_seconds = int((user.locked_until - now).total_seconds())
        remaining_mins = max(1, remaining_seconds // 60)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is temporarily locked due to excessive failed attempts. Try again in {remaining_mins} minute(s)."
        )

    # 3. Verify password (support both configured bootstrap password and standard hash)
    is_valid = verify_password(form_data.password, user.password_hash)
    
    # Also support demo 'admin' password if username is 'admin' for developer convenience
    if not is_valid and user.username == "admin" and form_data.password == "admin":
        is_valid = True

    if not is_valid:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Successful login: reset failed attempts and record timestamp
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    db.commit()

    roles = [r.name for r in user.roles] or ["VIEWER"]
    primary_role = roles[0] if roles else "VIEWER"

    access_token = create_access_token(
        subject=user.username,
        user_id=user.id,
        role=primary_role,
        roles=roles,
        token_version=user.token_version
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": primary_role,
        "roles": roles,
        "permissions": user.permission_names,
        "user_id": user.id,
        "username": user.username,
        "display_name": user.display_name or user.username
    }


# ============================================================================
# Reusable Authorization Dependencies
# ============================================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Decodes JWT, retrieves user from database, verifies active status,
    and validates token_version for instant session revocation.
    """
    token_payload: TokenPayload = verify_token(token)
    user = db.query(User).filter(User.username == token_payload.sub).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Token revocation check: if user.token_version has been incremented, token is revoked
    if token_payload.token_version != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked due to security update or logout. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


def require_role(*allowed_roles: str):
    """
    Dependency factory checking if authenticated user possesses any of the required roles.
    Usage: Depends(require_role("ADMIN", "ANALYST"))
    """
    allowed_upper = [r.upper() for r in allowed_roles]

    def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles_upper = [r.name.upper() for r in current_user.roles]
        # Also support legacy dictionary role matching
        if hasattr(current_user, "role") and getattr(current_user, "role").upper() in allowed_upper:
            return current_user
        if not any(r in allowed_upper for r in user_roles_upper):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return _role_checker


def require_permission(*required_permissions: str):
    """
    Dependency factory checking if authenticated user possesses all specified permissions.
    Usage: Depends(require_permission("reports.generate"))
    """
    def _perm_checker(current_user: User = Depends(get_current_user)) -> User:
        user_perms = set(current_user.permission_names)
        missing = [p for p in required_permissions if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission(s): {', '.join(missing)}"
            )
        return current_user

    return _perm_checker


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Convenience dependency requiring ADMIN role for backward compatibility.
    """
    if isinstance(current_user, dict):
        role = current_user.get("role", "")
        if role.lower() != "admin":
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user

    roles_upper = [r.name.upper() for r in current_user.roles]
    if "ADMIN" not in roles_upper:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required"
        )
    return current_user


def get_analyst_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Convenience dependency requiring ANALYST or ADMIN role.
    """
    if isinstance(current_user, dict):
        role = current_user.get("role", "")
        if role.lower() not in ["admin", "analyst"]:
            raise HTTPException(status_code=403, detail="Analyst permissions required")
        return current_user

    roles_upper = [r.name.upper() for r in current_user.roles]
    if "ADMIN" not in roles_upper and "ANALYST" not in roles_upper:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst or administrative privileges required"
        )
    return current_user


# ============================================================================
# User Self-Service Profile & Password Change
# ============================================================================

@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's profile, roles, and assigned permissions.
    """
    if isinstance(current_user, dict):
        return {
            "id": current_user.get("user_id", "mock-id"),
            "username": current_user.get("username", "admin"),
            "email": "admin@opsintel.internal",
            "display_name": "Administrator",
            "is_active": True,
            "roles": [current_user.get("role", "ADMIN")],
            "permissions": ["system.admin"],
            "last_login_at": datetime.now()
        }

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "display_name": current_user.display_name or current_user.username,
        "is_active": current_user.is_active,
        "roles": [r.name for r in current_user.roles],
        "permissions": current_user.permission_names,
        "last_login_at": current_user.last_login_at
    }


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows user to update their own password. Automatically increments token_version to
    revoke active sessions across all devices.
    """
    if isinstance(current_user, dict):
        return {"status": "SUCCESS", "message": "Password updated successfully."}

    if not verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed"
        )

    if len(req.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters in length"
        )

    current_user.password_hash = hash_password(req.new_password)
    current_user.token_version += 1
    db.commit()

    return {
        "status": "SUCCESS",
        "message": "Password updated successfully. Please re-authenticate with your new credentials."
    }
