import os
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from backend.config import settings
from backend.core.database import get_db
from backend.core.models import NotificationDelivery, User
from backend.services.smtp_service import smtp_service, validate_and_normalize_email
from backend.api.v1.endpoints.auth import require_permission

router = APIRouter()

# ============================================================================
# Schemas
# ============================================================================

class WebhookConfigRequest(BaseModel):
    slack_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None

class EmailTestRequest(BaseModel):
    recipient: str = Field(..., description="Target email address for test message")
    subject: Optional[str] = "OPSINTEL SMTP Delivery Test"
    message: Optional[str] = "This is a test operational notification dispatched from the OPSINTEL Enterprise Operations Center."

# ============================================================================
# SMTP & Multi-Channel Delivery Endpoints
# ============================================================================

@router.get("/email/status")
def get_email_status(
    current_user: User = Depends(require_permission("notifications.read"))
):
    """
    Returns non-sensitive SMTP configuration state and delivery transport mode.
    Never exposes passwords or authentication secrets.
    """
    return smtp_service.get_status_summary()


@router.post("/email/test")
def send_test_email(
    req: EmailTestRequest,
    current_user: User = Depends(require_permission("notifications.manage"))
):
    """
    Dispatches a sanitized test email to verify SMTP/TLS transport connectivity.
    Protected by 'notifications.manage' permission.
    """
    try:
        norm_email = validate_and_normalize_email(req.recipient)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

    try:
        result = smtp_service.send_email(
            recipients=[norm_email],
            subject=req.subject or "OPSINTEL SMTP Delivery Test",
            text_body=req.message or "OPSINTEL test notification."
        )
        return {
            "status": "SUCCESS",
            "delivery_result": result,
            "recipient": norm_email
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SMTP test dispatch failed: {str(exc)}"
        )


@router.get("/deliveries")
def list_notification_deliveries(
    limit: int = 50,
    channel: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notifications.read"))
):
    """Returns persistent audit records of all outbound notifications across Email, Slack, and Teams."""
    query = db.query(NotificationDelivery)
    if channel:
        query = query.filter(NotificationDelivery.channel == channel.upper())

    deliveries = query.order_by(NotificationDelivery.created_at.desc()).limit(limit).all()
    return [
        {
            "id": d.id,
            "execution_id": d.execution_id,
            "job_id": d.job_id,
            "channel": d.channel,
            "recipient": d.recipient,
            "subject": d.subject,
            "status": d.status,
            "provider_message_id": d.provider_message_id,
            "attempt_count": d.attempt_count,
            "sent_at": d.sent_at.isoformat() if d.sent_at else None,
            "error_message": d.error_message,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in deliveries
    ]


# ============================================================================
# Existing Webhook Configuration Endpoints
# ============================================================================

@router.get("/config")
def get_webhook_config():
    """
    Returns current Webhook configuration status from environment.
    """
    slack_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    teams_url = os.environ.get("TEAMS_WORKFLOW_HOOK_URL", "") or os.environ.get("TEAMS_WEBHOOK_URL", "")
    
    return {
        "slack_webhook_url": slack_url,
        "teams_webhook_url": teams_url,
        "slack_configured": bool(slack_url and slack_url.strip()),
        "teams_configured": bool(teams_url and teams_url.strip())
    }


@router.post("/config")
def save_webhook_config(req: WebhookConfigRequest):
    """
    Saves Slack and Teams Webhook URLs directly to the root .env file and updates current environment variables.
    """
    env_path = os.path.join(settings.PROJECT_ROOT, ".env")
    
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()

    if req.slack_webhook_url is not None:
        env_vars["SLACK_WEBHOOK_URL"] = req.slack_webhook_url.strip()
        os.environ["SLACK_WEBHOOK_URL"] = req.slack_webhook_url.strip()

    if req.teams_webhook_url is not None:
        env_vars["TEAMS_WORKFLOW_HOOK_URL"] = req.teams_webhook_url.strip()
        os.environ["TEAMS_WORKFLOW_HOOK_URL"] = req.teams_webhook_url.strip()

    # Rewrite .env file
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("# OPSINTEL CONFIGURATION\n")
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

    return {
        "status": "SUCCESS",
        "message": "Notification configuration saved successfully.",
        "slack_configured": bool(os.environ.get("SLACK_WEBHOOK_URL")),
        "teams_configured": bool(os.environ.get("TEAMS_WORKFLOW_HOOK_URL"))
    }
