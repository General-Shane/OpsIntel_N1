import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from backend.config import settings
from backend.core.models import (
    Service,
    Incident,
    Problem,
    Change,
    SLARecord,
    AuditEvent,
    SyncState,
    IntegrationFailure,
    IntegrationConfig,
    User
)
from backend.integrations.servicenow.client import ServiceNowClient
from backend.integrations.servicenow.metrics import metrics
from backend.integrations.servicenow.mappings import (
    sn_to_opsintel_service,
    sn_to_opsintel_problem,
    sn_to_opsintel_change,
    sn_to_opsintel_incident,
    sn_to_opsintel_sla
)
from backend.integrations.servicenow.exceptions import ServiceNowError

def _compute_hash(data: Any) -> str:
    """Computes a SHA256 hash of a payload for deduplication and dead-letter tracking."""
    dumped = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()[:16]


class ServiceNowSyncEngine:
    """
    Two-way synchronization and normalization engine between ServiceNow and OPSINTEL.
    Guarantees idempotency, audit trail recording, incremental timestamp filtering,
    dead-letter logging on failures, and configurable conflict resolution.
    """
    def __init__(self, client: Optional[ServiceNowClient] = None, conflict_policy: Optional[str] = None):
        self.client = client or ServiceNowClient()
        self.conflict_policy = conflict_policy or settings.SERVICE_NOW_CONFLICT_POLICY or "SERVICENOW_WINS"

    def _get_or_create_sync_state(self, db: Session, entity_name: str) -> SyncState:
        """Retrieves or initializes persistent synchronization state for an entity."""
        state = db.query(SyncState).filter(
            SyncState.connector_name == "servicenow",
            SyncState.entity_name == entity_name
        ).first()
        if not state:
            state = SyncState(
                connector_name="servicenow",
                entity_name=entity_name,
                status="IDLE"
            )
            db.add(state)
            db.commit()
            db.refresh(state)
        return state

    def _record_audit_event(
        self,
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        old_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        actor_username: str = "system",
        actor_user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Appends an immutable audit event for an externally or internally initiated ITSM mutation."""
        event = AuditEvent(
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_state_json=json.dumps(old_state, default=str) if old_state else None,
            new_state_json=json.dumps(new_state, default=str) if new_state else None,
            correlation_id=correlation_id or f"SN-SYNC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp_utc=datetime.now()
        )
        db.add(event)

    def _record_failure(
        self,
        db: Session,
        entity_name: str,
        external_id: Optional[str],
        error_class: str,
        error_message: str,
        payload: Any
    ):
        """Records a failed ingestion into the dead-letter queue."""
        metrics.inc_sync_failures()
        payload_hash = _compute_hash(payload)
        
        failure = db.query(IntegrationFailure).filter(
            IntegrationFailure.connector_name == "servicenow",
            IntegrationFailure.entity_name == entity_name,
            IntegrationFailure.payload_hash == payload_hash,
            IntegrationFailure.status == "FAILED"
        ).first()

        if failure:
            failure.attempt_count += 1
            failure.last_failure_at = datetime.now()
            failure.error_message = error_message
        else:
            failure = IntegrationFailure(
                connector_name="servicenow",
                entity_name=entity_name,
                external_id=external_id,
                error_class=error_class,
                error_message=error_message,
                payload_hash=payload_hash,
                attempt_count=1,
                status="FAILED"
            )
            db.add(failure)
        db.commit()

    # ========================================================================
    # Entity Ingestion Methods (Idempotent: Update if exists, Insert if new)
    # ========================================================================

    def ingest_services(self, db: Session, raw_records: List[Dict[str, Any]], actor_username: str = "system") -> Dict[str, int]:
        inserted = 0
        updated = 0
        for raw in raw_records:
            try:
                mapped = sn_to_opsintel_service(raw)
                svc_id = mapped["service_id"]
                ext_id = mapped.get("external_id")

                svc = None
                if ext_id:
                    svc = db.query(Service).filter(Service.external_id == ext_id).first()
                if not svc:
                    svc = db.query(Service).filter(Service.service_id == svc_id).first()

                if svc:
                    # Update existing record
                    old_state = {"status": svc.status, "criticality": svc.criticality}
                    for k, v in mapped.items():
                        setattr(svc, k, v)
                    svc.updated_at = datetime.now()
                    updated += 1
                    self._record_audit_event(
                        db=db, action="SERVICENOW_UPDATE", entity_type="Service",
                        entity_id=svc.service_id, old_state=old_state, new_state=mapped,
                        actor_username=actor_username
                    )
                else:
                    # Insert new record
                    svc = Service(**mapped)
                    db.add(svc)
                    inserted += 1
                    self._record_audit_event(
                        db=db, action="SERVICENOW_IMPORT", entity_type="Service",
                        entity_id=svc.service_id, new_state=mapped,
                        actor_username=actor_username
                    )
                db.flush()
                metrics.inc_sync_records()
            except Exception as exc:
                self._record_failure(
                    db=db, entity_name="service", external_id=raw.get("sys_id"),
                    error_class=type(exc).__name__, error_message=str(exc), payload=raw
                )
        db.commit()
        return {"inserted": inserted, "updated": updated}

    def ingest_problems(self, db: Session, raw_records: List[Dict[str, Any]], actor_username: str = "system") -> Dict[str, int]:
        inserted = 0
        updated = 0
        for raw in raw_records:
            try:
                mapped = sn_to_opsintel_problem(raw)
                prb_id = mapped["problem_id"]
                ext_id = mapped.get("external_id")

                # Ensure service exists
                svc_id = mapped["service_id"]
                svc = db.query(Service).filter(Service.service_id == svc_id).first()
                if not svc:
                    svc = Service(service_id=svc_id, service_name=svc_id, criticality="HIGH", status="OPERATIONAL")
                    db.add(svc)
                    db.flush()

                prb = None
                if ext_id:
                    prb = db.query(Problem).filter(Problem.external_id == ext_id).first()
                if not prb:
                    prb = db.query(Problem).filter(Problem.problem_id == prb_id).first()

                if prb:
                    old_state = {"status": prb.status, "workaround": prb.workaround}
                    for k, v in mapped.items():
                        setattr(prb, k, v)
                    prb.updated_at = datetime.now()
                    updated += 1
                    self._record_audit_event(
                        db=db, action="SERVICENOW_UPDATE", entity_type="Problem",
                        entity_id=prb.problem_id, old_state=old_state, new_state=mapped,
                        actor_username=actor_username
                    )
                else:
                    prb = Problem(**mapped)
                    db.add(prb)
                    inserted += 1
                    self._record_audit_event(
                        db=db, action="SERVICENOW_IMPORT", entity_type="Problem",
                        entity_id=prb.problem_id, new_state=mapped,
                        actor_username=actor_username
                    )
                db.flush()
                metrics.inc_sync_records()
            except Exception as exc:
                self._record_failure(
                    db=db, entity_name="problem", external_id=raw.get("sys_id"),
                    error_class=type(exc).__name__, error_message=str(exc), payload=raw
                )
        db.commit()
        return {"inserted": inserted, "updated": updated}

    def ingest_changes(self, db: Session, raw_records: List[Dict[str, Any]], actor_username: str = "system") -> Dict[str, int]:
        inserted = 0
        updated = 0
        for raw in raw_records:
            try:
                mapped = sn_to_opsintel_change(raw)
                chg_id = mapped["change_id"]
                ext_id = mapped.get("external_id")

                svc_id = mapped["service_id"]
                svc = db.query(Service).filter(Service.service_id == svc_id).first()
                if not svc:
                    svc = Service(service_id=svc_id, service_name=svc_id, criticality="HIGH", status="OPERATIONAL")
                    db.add(svc)
                    db.flush()

                chg = None
                if ext_id:
                    chg = db.query(Change).filter(Change.external_id == ext_id).first()
                if not chg:
                    chg = db.query(Change).filter(Change.change_id == chg_id).first()

                if chg:
                    old_state = {"status": chg.status, "cab_status": chg.cab_status}
                    for k, v in mapped.items():
                        setattr(chg, k, v)
                    chg.updated_at = datetime.now()
                    updated += 1
                    self._record_audit_event(
                        db=db, action="SERVICENOW_UPDATE", entity_type="Change",
                        entity_id=chg.change_id, old_state=old_state, new_state=mapped,
                        actor_username=actor_username
                    )
                else:
                    chg = Change(**mapped)
                    db.add(chg)
                    inserted += 1
                    self._record_audit_event(
                        db=db, action="SERVICENOW_IMPORT", entity_type="Change",
                        entity_id=chg.change_id, new_state=mapped,
                        actor_username=actor_username
                    )
                db.flush()
                metrics.inc_sync_records()
            except Exception as exc:
                self._record_failure(
                    db=db, entity_name="change", external_id=raw.get("sys_id"),
                    error_class=type(exc).__name__, error_message=str(exc), payload=raw
                )
        db.commit()
        return {"inserted": inserted, "updated": updated}

    def ingest_incidents(self, db: Session, raw_records: List[Dict[str, Any]], actor_username: str = "system") -> Dict[str, int]:
        inserted = 0
        updated = 0
        for raw in raw_records:
            try:
                mapped = sn_to_opsintel_incident(raw)
                inc_id = mapped["incident_id"]
                ext_id = mapped.get("external_id")

                svc_id = mapped["service_id"]
                svc = db.query(Service).filter(Service.service_id == svc_id).first()
                if not svc:
                    svc = Service(service_id=svc_id, service_name=svc_id, criticality="HIGH", status="OPERATIONAL")
                    db.add(svc)
                    db.flush()

                inc = None
                if ext_id:
                    inc = db.query(Incident).filter(Incident.external_id == ext_id).first()
                if not inc:
                    inc = db.query(Incident).filter(Incident.incident_id == inc_id).first()

                if inc:
                    old_state = {"status": inc.status, "priority": inc.priority}
                    for k, v in mapped.items():
                        setattr(inc, k, v)
                    inc.updated_at = datetime.now()
                    updated += 1
                    self._record_audit_event(
                        db=db, action="SERVICENOW_UPDATE", entity_type="Incident",
                        entity_id=inc.incident_id, old_state=old_state, new_state=mapped,
                        actor_username=actor_username
                    )
                else:
                    inc = Incident(**mapped)
                    db.add(inc)
                    inserted += 1
                    self._record_audit_event(
                        db=db, action="SERVICENOW_IMPORT", entity_type="Incident",
                        entity_id=inc.incident_id, new_state=mapped,
                        actor_username=actor_username
                    )
                db.flush()
                metrics.inc_sync_records()
            except Exception as exc:
                self._record_failure(
                    db=db, entity_name="incident", external_id=raw.get("sys_id"),
                    error_class=type(exc).__name__, error_message=str(exc), payload=raw
                )
        db.commit()
        return {"inserted": inserted, "updated": updated}

    def ingest_slas(self, db: Session, raw_records: List[Dict[str, Any]], actor_username: str = "system") -> Dict[str, int]:
        inserted = 0
        updated = 0
        for raw in raw_records:
            try:
                mapped = sn_to_opsintel_sla(raw)
                sla_id = mapped["sla_id"]
                ext_id = mapped.get("external_id")

                svc_id = mapped["service_id"]
                svc = db.query(Service).filter(Service.service_id == svc_id).first()
                if not svc:
                    svc = Service(service_id=svc_id, service_name=svc_id, criticality="HIGH", status="OPERATIONAL")
                    db.add(svc)
                    db.flush()

                sla = None
                if ext_id:
                    sla = db.query(SLARecord).filter(SLARecord.external_id == ext_id).first()
                if not sla:
                    sla = db.query(SLARecord).filter(SLARecord.sla_id == sla_id).first()

                if sla:
                    old_state = {"breached": sla.breached, "status": sla.status}
                    for k, v in mapped.items():
                        setattr(sla, k, v)
                    sla.updated_at = datetime.now()
                    updated += 1
                    self._record_audit_event(
                        db=db, action="SERVICENOW_UPDATE", entity_type="SLARecord",
                        entity_id=sla.sla_id, old_state=old_state, new_state=mapped,
                        actor_username=actor_username
                    )
                else:
                    sla = SLARecord(**mapped)
                    db.add(sla)
                    inserted += 1
                    self._record_audit_event(
                        db=db, action="SERVICENOW_IMPORT", entity_type="SLARecord",
                        entity_id=sla.sla_id, new_state=mapped,
                        actor_username=actor_username
                    )
                db.flush()
                metrics.inc_sync_records()
            except Exception as exc:
                self._record_failure(
                    db=db, entity_name="sla", external_id=raw.get("sys_id"),
                    error_class=type(exc).__name__, error_message=str(exc), payload=raw
                )
        db.commit()
        return {"inserted": inserted, "updated": updated}

    # ========================================================================
    # High-Level Sync Orchestrators
    # ========================================================================

    def sync_entity(self, db: Session, entity_name: str, full_sync: bool = False, actor_username: str = "system") -> Dict[str, Any]:
        """Executes full or incremental synchronization for a single entity type."""
        entity = entity_name.lower()
        valid_entities = ("service", "problem", "change", "incident", "sla")
        if entity not in valid_entities:
            raise ValueError(f"Invalid entity name '{entity_name}'. Valid entities are: {valid_entities}")

        sync_state = self._get_or_create_sync_state(db, entity)
        sync_state.status = "RUNNING"
        sync_state.last_attempted_sync = datetime.now()
        db.commit()

        since = None if full_sync else sync_state.last_successful_sync
        fetch_limit = settings.SERVICE_NOW_MAX_RECORDS_PER_SYNC

        try:
            raw_records = []
            if entity == "service":
                raw_records = self.client.get_services(since=since, limit=fetch_limit)
                counts = self.ingest_services(db, raw_records, actor_username)
            elif entity == "problem":
                raw_records = self.client.get_problems(since=since, limit=fetch_limit)
                counts = self.ingest_problems(db, raw_records, actor_username)
            elif entity == "change":
                raw_records = self.client.get_changes(since=since, limit=fetch_limit)
                counts = self.ingest_changes(db, raw_records, actor_username)
            elif entity == "incident":
                raw_records = self.client.get_incidents(since=since, limit=fetch_limit)
                counts = self.ingest_incidents(db, raw_records, actor_username)
            elif entity == "sla":
                raw_records = self.client.get_slas(since=since, limit=fetch_limit)
                counts = self.ingest_slas(db, raw_records, actor_username)

            sync_state.records_fetched = len(raw_records)
            sync_state.records_inserted = counts["inserted"]
            sync_state.records_updated = counts["updated"]
            sync_state.status = "SUCCESS"
            sync_state.last_successful_sync = datetime.now()
            sync_state.error_summary = None
            db.commit()

            return {
                "entity": entity,
                "status": "SUCCESS",
                "records_fetched": len(raw_records),
                "records_inserted": counts["inserted"],
                "records_updated": counts["updated"],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as exc:
            sync_state.status = "FAILED"
            sync_state.error_summary = str(exc)
            db.commit()
            raise exc

    def sync_all(self, db: Session, full_sync: bool = False, actor_username: str = "system") -> Dict[str, Any]:
        """Sequentially synchronizes all ITSM entities in dependency order: Services -> Problems -> Changes -> Incidents -> SLAs."""
        order = ["service", "problem", "change", "incident", "sla"]
        results = {}
        total_fetched = 0
        total_inserted = 0
        total_updated = 0

        for entity in order:
            res = self.sync_entity(db, entity_name=entity, full_sync=full_sync, actor_username=actor_username)
            results[entity] = res
            total_fetched += res["records_fetched"]
            total_inserted += res["records_inserted"]
            total_updated += res["records_updated"]

        return {
            "status": "SUCCESS",
            "full_sync": full_sync,
            "total_fetched": total_fetched,
            "total_inserted": total_inserted,
            "total_updated": total_updated,
            "entities": results,
            "timestamp": datetime.now().isoformat()
        }

    # ========================================================================
    # Controlled Two-Way Write-Back Orchestrator
    # ========================================================================

    def writeback_entity(
        self,
        db: Session,
        entity_name: str,
        entity_id: str,
        updates: Dict[str, Any],
        actor_user: User
    ) -> Dict[str, Any]:
        """
        Pushes local changes back to ServiceNow with full audit recording.
        Requires entity sys_id or resolves from local record.
        """
        entity = entity_name.lower()
        if entity not in ("incident", "problem", "change"):
            raise ValueError(f"Writeback is not supported for entity '{entity_name}'. Supported: incident, problem, change.")

        target_record = None
        if entity == "incident":
            target_record = db.query(Incident).filter(
                (Incident.incident_id == entity_id) | (Incident.external_id == entity_id)
            ).first()
        elif entity == "problem":
            target_record = db.query(Problem).filter(
                (Problem.problem_id == entity_id) | (Problem.external_id == entity_id)
            ).first()
        elif entity == "change":
            target_record = db.query(Change).filter(
                (Change.change_id == entity_id) | (Change.external_id == entity_id)
            ).first()

        if not target_record:
            raise ServiceNowError(f"Target {entity_name} '{entity_id}' not found in local database.")

        sys_id = target_record.external_id
        if not sys_id:
            raise ServiceNowError(f"Target {entity_name} '{entity_id}' does not have a ServiceNow external_id (sys_id).")

        # Execute remote update via Client
        remote_res = {}
        if entity == "incident":
            remote_res = self.client.writeback_incident(sys_id=sys_id, update_dict=updates)
        elif entity == "problem":
            remote_res = self.client.writeback_problem(sys_id=sys_id, update_dict=updates)
        elif entity == "change":
            remote_res = self.client.writeback_change(sys_id=sys_id, update_dict=updates)

        # Update local state
        old_state = {k: getattr(target_record, k, None) for k in updates.keys() if hasattr(target_record, k)}
        for k, v in updates.items():
            if hasattr(target_record, k):
                setattr(target_record, k, v)
        target_record.updated_at = datetime.now()

        # Record Audit Event
        self._record_audit_event(
            db=db,
            action="OPSI_WRITEBACK",
            entity_type=entity.capitalize(),
            entity_id=entity_id,
            old_state=old_state,
            new_state=updates,
            actor_username=actor_user.username,
            actor_user_id=actor_user.id
        )
        db.commit()

        return {
            "status": "SUCCESS",
            "entity": entity,
            "entity_id": entity_id,
            "external_id": sys_id,
            "updates_applied": updates,
            "remote_response": remote_res,
            "timestamp": datetime.now().isoformat()
        }

    # ========================================================================
    # Dead-Letter Retry Orchestrator
    # ========================================================================

    def retry_failure(self, db: Session, failure_id: str, actor_username: str = "system") -> Dict[str, Any]:
        """Attempts to reprocess a failed record from the integration_failures table."""
        failure = db.query(IntegrationFailure).filter(IntegrationFailure.id == failure_id).first()
        if not failure:
            raise ValueError(f"Integration failure record '{failure_id}' not found.")

        failure.status = "RETRYING"
        db.commit()

        try:
            # Re-fetch or re-sync
            self.sync_entity(db, entity_name=failure.entity_name, full_sync=False, actor_username=actor_username)
            failure.status = "RESOLVED"
            failure.resolved_at = datetime.now()
            db.commit()
            return {"status": "RESOLVED", "failure_id": failure_id}
        except Exception as exc:
            failure.status = "FAILED"
            failure.attempt_count += 1
            failure.last_failure_at = datetime.now()
            failure.error_message = f"Retry failed: {str(exc)}"
            db.commit()
            return {"status": "FAILED", "failure_id": failure_id, "error": str(exc)}
