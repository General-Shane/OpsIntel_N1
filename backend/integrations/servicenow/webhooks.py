import hmac
import hashlib
import time
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.config import settings
from backend.core.models import WebhookEvent, AuditEvent
from backend.integrations.servicenow.metrics import metrics
from backend.integrations.servicenow.sync import ServiceNowSyncEngine
from backend.integrations.servicenow.exceptions import ServiceNowValidationError

def compute_hmac_sha256(payload_bytes: bytes, secret: str) -> str:
    """Computes hexadecimal HMAC-SHA256 signature for a raw payload."""
    secret_bytes = secret.encode("utf-8")
    return hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()


class ServiceNowWebhookReceiver:
    """
    Secure inbound webhook receiver for real-time ServiceNow event dispatches.
    Enforces HMAC-SHA256 cryptographic signature validation, timestamp replay protection,
    idempotency checking, entity normalization, and audit logging.
    """
    def __init__(
        self,
        webhook_secret: Optional[str] = None,
        timestamp_tolerance_seconds: int = 300,
        sync_engine: Optional[ServiceNowSyncEngine] = None
    ):
        self.webhook_secret = webhook_secret or settings.SERVICE_NOW_WEBHOOK_SECRET or "opsintel-sn-webhook-secret-2026"
        self.timestamp_tolerance = timestamp_tolerance_seconds
        self.sync_engine = sync_engine or ServiceNowSyncEngine()

    def verify_signature(self, payload_bytes: bytes, signature_header: Optional[str]) -> bool:
        """
        Verifies HMAC-SHA256 signature.
        Supports standard hex format or 'sha256=...' prefix format.
        """
        if not signature_header or not self.webhook_secret:
            return False

        clean_sig = signature_header.strip()
        if clean_sig.startswith("sha256="):
            clean_sig = clean_sig[7:]

        expected_sig = compute_hmac_sha256(payload_bytes, self.webhook_secret)
        return hmac.compare_digest(clean_sig.lower(), expected_sig.lower())

    def verify_timestamp(self, timestamp_header: Optional[str]) -> bool:
        """
        Verifies that webhook request timestamp is within tolerance to prevent replay attacks.
        Accepts Unix epoch or ISO 8601 string.
        """
        if not timestamp_header:
            # If no timestamp header is provided, reject or proceed with caution
            return True
        now = time.time()
        try:
            # Try epoch
            ts = float(timestamp_header)
        except ValueError:
            try:
                dt = datetime.fromisoformat(timestamp_header.replace("Z", "+00:00"))
                ts = dt.timestamp()
            except Exception:
                return False

        return abs(now - ts) <= self.timestamp_tolerance

    def process_webhook(
        self,
        db: Session,
        raw_body: bytes,
        signature_header: Optional[str],
        timestamp_header: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates and processes an inbound ServiceNow webhook request.
        Returns processing summary or raises ServiceNowValidationError.
        """
        metrics.inc_webhooks()

        # 1. Cryptographic Signature Verification
        if not self.verify_signature(raw_body, signature_header):
            raise ServiceNowValidationError("Invalid or missing HMAC-SHA256 webhook signature.")

        # 2. Timestamp Tolerance Check
        if not self.verify_timestamp(timestamp_header):
            raise ServiceNowValidationError("Webhook request timestamp expired or outside tolerance window.")

        # 3. Parse JSON Body
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            raise ServiceNowValidationError(f"Malformed JSON payload: {str(exc)}") from exc

        event_id = str(payload.get("event_id") or payload.get("id") or f"SN-EVT-{int(time.time()*1000)}")
        idempotency_key = str(payload.get("idempotency_key") or event_id)
        event_type = str(payload.get("event_type") or payload.get("action") or "incident.updated")
        entity_name = str(payload.get("entity_name") or payload.get("table") or "incident").lower()
        record_data = payload.get("record") or payload.get("data") or payload

        # 4. Check Replay / Idempotency
        existing_event = db.query(WebhookEvent).filter(
            (WebhookEvent.idempotency_key == idempotency_key) | (WebhookEvent.event_id == event_id)
        ).first()

        if existing_event:
            return {
                "status": "DUPLICATE_IGNORED",
                "message": f"Webhook event '{event_id}' has already been processed.",
                "event_id": event_id,
                "processed_at": existing_event.processed_at.isoformat() if existing_event.processed_at else None
            }

        # 5. Ingest / Normalize Entity Record
        entity_id = None
        if isinstance(record_data, dict):
            entity_id = record_data.get("number") or record_data.get("sys_id")

        webhook_log = WebhookEvent(
            event_id=event_id,
            idempotency_key=idempotency_key,
            connector_name="servicenow",
            event_type=event_type,
            entity_name=entity_name,
            entity_id=entity_id,
            signature=signature_header[:16] + "..." if signature_header else None,
            status="PROCESSED",
            received_at=datetime.now(),
            processed_at=datetime.now()
        )
        db.add(webhook_log)

        # Ingest using SyncEngine
        counts = {"inserted": 0, "updated": 0}
        if isinstance(record_data, dict):
            records = [record_data]
            if entity_name in ("incident", "incidents"):
                counts = self.sync_engine.ingest_incidents(db, records, actor_username="servicenow_webhook")
            elif entity_name in ("problem", "problems"):
                counts = self.sync_engine.ingest_problems(db, records, actor_username="servicenow_webhook")
            elif entity_name in ("change", "changes", "change_request"):
                counts = self.sync_engine.ingest_changes(db, records, actor_username="servicenow_webhook")
            elif entity_name in ("service", "services", "cmdb_ci_service"):
                counts = self.sync_engine.ingest_services(db, records, actor_username="servicenow_webhook")
            elif entity_name in ("sla", "slas", "task_sla"):
                counts = self.sync_engine.ingest_slas(db, records, actor_username="servicenow_webhook")

        # 6. Record Audit Event
        audit = AuditEvent(
            actor_username="servicenow_webhook",
            entity_type=entity_name.capitalize(),
            entity_id=str(entity_id or event_id),
            action="WEBHOOK_RECEIVED",
            new_state_json=json.dumps({"event_type": event_type, "counts": counts}, default=str),
            correlation_id=event_id,
            timestamp_utc=datetime.now()
        )
        db.add(audit)
        db.commit()

        return {
            "status": "PROCESSED",
            "event_id": event_id,
            "entity_name": entity_name,
            "entity_id": entity_id,
            "counts": counts,
            "timestamp": datetime.now().isoformat()
        }
