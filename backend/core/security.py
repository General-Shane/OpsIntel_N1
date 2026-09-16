import os
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional, List
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from backend.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# ============================================================================
# Token Schemas
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    roles: List[str] = []
    permissions: List[str] = []
    user_id: str
    username: str
    display_name: Optional[str] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None
    roles: List[str] = []
    token_version: int = 1
    exp: Optional[int] = None


# ============================================================================
# Password Hashing & Verification
# ============================================================================

def hash_password(password: str) -> str:
    """Generates a secure salted bcrypt hash for a plaintext password."""
    return pwd_context.hash(password)

def get_password_hash(password: str) -> str:
    """Alias for hash_password to maintain backward compatibility."""
    return hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT Token Generation & Verification
# ============================================================================

def create_access_token(
    subject: Union[str, Any],
    role: str,
    user_id: Optional[str] = None,
    roles: Optional[List[str]] = None,
    token_version: int = 1,
    expires_delta: Optional[timedelta] = None
) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "user_id": str(user_id) if user_id else str(subject),
        "role": role,
        "roles": roles or [role],
        "token_version": token_version
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )


# ============================================================================
# Security Bootstrap: Permissions, Roles & Users
# ============================================================================

DEFAULT_PERMISSIONS = [
    {"name": "dashboard.read", "description": "View executive operational dashboard and telemetry"},
    {"name": "incidents.read", "description": "View operational incidents and change correlations"},
    {"name": "incidents.manage", "description": "Triage, escalate, and manage operational incidents"},
    {"name": "problems.read", "description": "View problem management intelligence and aging"},
    {"name": "problems.manage", "description": "Manage root-cause investigations and corrective tasks"},
    {"name": "changes.read", "description": "View release governance and deployment history"},
    {"name": "changes.approve", "description": "Approve change requests and participate in CAB voting"},
    {"name": "sla.read", "description": "View SLA compliance targets and breach countdowns"},
    {"name": "reports.read", "description": "View executive operations reports and summaries"},
    {"name": "reports.generate", "description": "Trigger executive report compilation and PDF export"},
    {"name": "ai.chat", "description": "Query interactive AI Operations Analyst"},
    {"name": "scheduler.read", "description": "View scheduled pipeline execution history and status"},
    {"name": "scheduler.manage", "description": "Create, modify, pause, resume, or delete scheduled jobs"},
    {"name": "scheduler.execute", "description": "Trigger manual/ad-hoc execution of scheduled jobs"},
    {"name": "scheduler.history", "description": "View detailed execution logs, traces, and retry status"},
    {"name": "notifications.read", "description": "View multi-channel notification dispatches"},
    {"name": "notifications.manage", "description": "Configure notification webhooks, SMTP, and channels"},
    {"name": "users.read", "description": "View user accounts and role assignments"},
    {"name": "users.manage", "description": "Create, modify, and disable user accounts and roles"},
    {"name": "integration.read", "description": "View integration connectors, sync status, metrics, and error logs"},
    {"name": "integration.manage", "description": "Configure integration settings and test connectivity"},
    {"name": "integration.sync", "description": "Trigger manual full and incremental data synchronization"},
    {"name": "integration.writeback", "description": "Perform controlled two-way data write-back to external systems"},
    {"name": "system.admin", "description": "Full platform administration, reseeding, and data purge"},
]

ROLE_PERMISSION_MATRIX = {
    "ADMIN": [p["name"] for p in DEFAULT_PERMISSIONS],
    "ANALYST": [
        "dashboard.read", "incidents.read", "incidents.manage", "problems.read",
        "problems.manage", "changes.read", "sla.read", "reports.read",
        "reports.generate", "ai.chat", "scheduler.read", "scheduler.history",
        "scheduler.execute", "notifications.read",
        "integration.read", "integration.sync"
    ],
    "VIEWER": [
        "dashboard.read", "incidents.read", "problems.read", "changes.read",
        "sla.read", "reports.read", "scheduler.read", "notifications.read", "integration.read"
    ]
}

def bootstrap_security(db: Session):
    """
    Initializes persistent permissions, roles, and default bootstrap users in the database.
    Idempotent and safe to run on every startup or test initialization.
    """
    from backend.core.models import Permission, Role, User

    # 1. Sync Permissions
    perm_map = {}
    existing_perms = {p.name: p for p in db.query(Permission).all()}
    for p_def in DEFAULT_PERMISSIONS:
        if p_def["name"] not in existing_perms:
            new_p = Permission(name=p_def["name"], description=p_def["description"])
            db.add(new_p)
            db.flush()
            perm_map[p_def["name"]] = new_p
        else:
            perm_map[p_def["name"]] = existing_perms[p_def["name"]]

    # 2. Sync Roles
    role_map = {}
    existing_roles = {r.name: r for r in db.query(Role).all()}
    for r_name, p_names in ROLE_PERMISSION_MATRIX.items():
        if r_name not in existing_roles:
            new_r = Role(name=r_name, description=f"Standard {r_name} Role")
            new_r.permissions = [perm_map[pn] for pn in p_names if pn in perm_map]
            db.add(new_r)
            db.flush()
            role_map[r_name] = new_r
        else:
            r = existing_roles[r_name]
            # Ensure permissions are up to date
            r.permissions = [perm_map[pn] for pn in p_names if pn in perm_map]
            role_map[r_name] = r

    # 3. Bootstrap Default Users
    bootstrap_users = [
        {
            "username": settings.OPSINTEL_BOOTSTRAP_ADMIN_USERNAME,
            "password": settings.OPSINTEL_BOOTSTRAP_ADMIN_PASSWORD,
            "email": "admin@opsintel.internal",
            "display_name": "System Administrator",
            "role": "ADMIN"
        },
        {
            "username": settings.OPSINTEL_BOOTSTRAP_VIEWER_USERNAME,
            "password": settings.OPSINTEL_BOOTSTRAP_VIEWER_PASSWORD,
            "email": "viewer@opsintel.internal",
            "display_name": "Executive Viewer",
            "role": "VIEWER"
        },
        {
            "username": settings.OPSINTEL_BOOTSTRAP_ANALYST_USERNAME,
            "password": settings.OPSINTEL_BOOTSTRAP_ANALYST_PASSWORD,
            "email": "analyst@opsintel.internal",
            "display_name": "Operations Analyst",
            "role": "ANALYST"
        }
    ]

    for u_def in bootstrap_users:
        user = db.query(User).filter(User.username == u_def["username"]).first()
        if not user:
            new_user = User(
                username=u_def["username"],
                email=u_def["email"],
                display_name=u_def["display_name"],
                password_hash=hash_password(u_def["password"]),
                is_active=True,
                token_version=1
            )
            if u_def["role"] in role_map:
                new_user.roles = [role_map[u_def["role"]]]
            db.add(new_user)

    db.commit()
