from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.database import get_db
from backend.core.models import User, SyncState, IntegrationFailure, WebhookEvent
from backend.api.v1.endpoints.auth import (
    get_current_user,
    require_permission,
    get_admin_user,
    get_analyst_user
)
from backend.integrations.servicenow.client import ServiceNowClient
from backend.integrations.servicenow.sync import ServiceNowSyncEngine
from backend.integrations.servicenow.webhooks import ServiceNowWebhookReceiver
from backend.integrations.servicenow.metrics import metrics
from backend.integrations.servicenow.exceptions import ServiceNowError, ServiceNowValidationError

router = APIRouter()

# ============================================================================
# Request & Response Schemas
# ============================================================================

class SyncRequest(BaseModel):
    full_sync: bool = False

class WritebackRequest(BaseModel):
    updates: Dict[str, Any]

class WebhookResponse(BaseModel):
    status: str
    event_id: str
    entity_name: Optional[str] = None
    entity_id: Optional[str] = None
    counts: Optional[Dict[str, int]] = None
    timestamp: str


# ============================================================================
# Status & Diagnostics Endpoints
# ============================================================================

@router.get("/status")
def get_servicenow_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.read"))
):
    """
    Returns non-sensitive configuration state, active connectivity summary,
    sync status across entities, and cumulative telemetry metrics.
    """
    client = ServiceNowClient()
    sync_states = db.query(SyncState).filter(SyncState.connector_name == "servicenow").all()
    
    entity_states = {
        s.entity_name: {
            "status": s.status,
            "last_successful_sync": s.last_successful_sync.isoformat() if s.last_successful_sync else None,
            "last_attempted_sync": s.last_attempted_sync.isoformat() if s.last_attempted_sync else None,
            "records_fetched": s.records_fetched,
            "records_inserted": s.records_inserted,
            "records_updated": s.records_updated,
            "records_failed": s.records_failed,
            "error_summary": s.error_summary
        }
        for s in sync_states
    }

    recent_failures_count = db.query(IntegrationFailure).filter(
        IntegrationFailure.connector_name == "servicenow",
        IntegrationFailure.status == "FAILED"
    ).count()

    recent_webhooks_count = db.query(WebhookEvent).filter(
        WebhookEvent.connector_name == "servicenow"
    ).count()

    return {
        "connector": "servicenow",
        "config": client.auth.get_status_summary(),
        "entities": entity_states,
        "metrics": metrics.get_summary(),
        "unresolved_failures_count": recent_failures_count,
        "total_webhooks_processed": recent_webhooks_count
    }


@router.post("/test-connection")
def test_servicenow_connection(
    current_user: User = Depends(require_permission("integration.manage"))
):
    """
    Actively tests API connectivity and authentication against the configured ServiceNow instance.
    Protected by 'integration.manage' permission (Admin only).
    """
    client = ServiceNowClient()
    return client.test_connection()


# ============================================================================
# Synchronization Endpoints
# ============================================================================

@router.post("/sync")
def trigger_sync_all(
    req: SyncRequest = SyncRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.sync"))
):
    """
    Triggers full or incremental synchronization across all ITSM entities.
    Protected by 'integration.sync' permission (Admin, Analyst).
    """
    engine = ServiceNowSyncEngine()
    if not engine.client.auth.is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ServiceNow instance is not configured. Configure credentials in environment first."
        )
    try:
        return engine.sync_all(db, full_sync=req.full_sync, actor_username=current_user.username)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"ServiceNow synchronization failed: {str(exc)}"
        )


@router.post("/sync/{entity}")
def trigger_sync_entity(
    entity: str,
    req: SyncRequest = SyncRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.sync"))
):
    """
    Triggers synchronization for a specific entity ('service', 'problem', 'change', 'incident', 'sla').
    Protected by 'integration.sync' permission (Admin, Analyst).
    """
    engine = ServiceNowSyncEngine()
    if not engine.client.auth.is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ServiceNow instance is not configured. Configure credentials in environment first."
        )
    try:
        return engine.sync_entity(db, entity_name=entity, full_sync=req.full_sync, actor_username=current_user.username)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"ServiceNow sync failed for entity '{entity}': {str(exc)}"
        )


@router.get("/sync-status")
def get_sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.read"))
):
    """Returns granular sync states and counters across all managed ITSM entities."""
    sync_states = db.query(SyncState).filter(SyncState.connector_name == "servicenow").all()
    return [
        {
            "entity": s.entity_name,
            "status": s.status,
            "last_successful_sync": s.last_successful_sync.isoformat() if s.last_successful_sync else None,
            "last_attempted_sync": s.last_attempted_sync.isoformat() if s.last_attempted_sync else None,
            "records_fetched": s.records_fetched,
            "records_inserted": s.records_inserted,
            "records_updated": s.records_updated,
            "records_failed": s.records_failed,
            "error_summary": s.error_summary,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None
        }
        for s in sync_states
    ]


# ============================================================================
# Dead-Letter & Error Management Endpoints
# ============================================================================

@router.get("/errors")
def get_integration_errors(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.read"))
):
    """Returns dead-letter queue records for failed ServiceNow ingestion attempts."""
    failures = db.query(IntegrationFailure).filter(
        IntegrationFailure.connector_name == "servicenow"
    ).order_by(IntegrationFailure.last_failure_at.desc()).limit(limit).all()

    return [
        {
            "id": f.id,
            "entity_name": f.entity_name,
            "external_id": f.external_id,
            "error_class": f.error_class,
            "error_message": f.error_message,
            "attempt_count": f.attempt_count,
            "status": f.status,
            "first_failure_at": f.first_failure_at.isoformat() if f.first_failure_at else None,
            "last_failure_at": f.last_failure_at.isoformat() if f.last_failure_at else None,
            "resolved_at": f.resolved_at.isoformat() if f.resolved_at else None
        }
        for f in failures
    ]


@router.post("/errors/{error_id}/retry")
def retry_integration_error(
    error_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.sync"))
):
    """Retries processing of a failed record from the dead-letter queue."""
    engine = ServiceNowSyncEngine()
    try:
        return engine.retry_failure(db, failure_id=error_id, actor_username=current_user.username)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ============================================================================
# Two-Way Write-Back Endpoint
# ============================================================================

@router.post("/writeback/{entity}/{entity_id}")
def writeback_to_servicenow(
    entity: str,
    entity_id: str,
    req: WritebackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.writeback"))
):
    """
    Pushes controlled local ITSM state modifications back into ServiceNow Table API.
    Protected by 'integration.writeback' permission (Admin only).
    """
    engine = ServiceNowSyncEngine()
    if not engine.client.auth.is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ServiceNow instance is not configured. Cannot perform write-back."
        )
    try:
        return engine.writeback_entity(
            db=db,
            entity_name=entity,
            entity_id=entity_id,
            updates=req.updates,
            actor_user=current_user
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except ServiceNowError as sn_err:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(sn_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ============================================================================
# Inbound Webhook Receiver Endpoint
# ============================================================================

@router.post("/webhook", response_model=WebhookResponse)
async def receive_servicenow_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_servicenow_signature: Optional[str] = Header(None, alias="X-ServiceNow-Signature"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_servicenow_timestamp: Optional[str] = Header(None, alias="X-ServiceNow-Timestamp")
):
    """
    Inbound webhook receiver for real-time ServiceNow push notifications.
    Validates HMAC-SHA256 signature, enforces timestamp replay protection,
    processes entity updates idempotently, and logs audit events.
    """
    signature = x_servicenow_signature or x_hub_signature_256
    raw_body = await request.body()

    receiver = ServiceNowWebhookReceiver()
    try:
        result = receiver.process_webhook(
            db=db,
            raw_body=raw_body,
            signature_header=signature,
            timestamp_header=x_servicenow_timestamp
        )
        return result
    except ServiceNowValidationError as val_err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED if "signature" in str(val_err).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing error: {str(exc)}"
        )
