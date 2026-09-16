import os
import sys
import time
import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import app
from backend.core.database import Base
import backend.core.database as db_module
from backend.core.models import (
    User,
    Role,
    Permission,
    Service,
    Incident,
    Problem,
    Change,
    SLARecord,
    AuditEvent,
    SyncState,
    IntegrationFailure,
    WebhookEvent
)
from backend.core.security import bootstrap_security, hash_password, create_access_token
from backend.config import settings
from backend.integrations.servicenow import (
    ServiceNowAuthProvider,
    ServiceNowClient,
    ServiceNowSyncEngine,
    ServiceNowWebhookReceiver,
    mask_secret,
    metrics,
    compute_hmac_sha256,
    sn_to_opsintel_incident,
    sn_to_opsintel_problem,
    sn_to_opsintel_change,
    sn_to_opsintel_service,
    sn_to_opsintel_sla,
    opsintel_to_sn_incident,
    opsintel_to_sn_problem,
    opsintel_to_sn_change
)
from backend.integrations.servicenow.exceptions import (
    ServiceNowAuthError,
    ServiceNowRateLimitError,
    ServiceNowTransientError,
    ServiceNowPermanentError,
    ServiceNowNotFoundError,
    ServiceNowValidationError
)

TEST_DB_URL = "sqlite:///./test_stage8_sn.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_stage8_test_env():
    original_engine = db_module.engine
    original_session = db_module.SessionLocal

    db_module.engine = test_engine
    db_module.SessionLocal = TestSessionLocal

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_module.get_db] = override_get_db

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Bootstrap users and RBAC
    db = TestSessionLocal()
    bootstrap_security(db)
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    db_module.engine = original_engine
    db_module.SessionLocal = original_session
    app.dependency_overrides.clear()

    if os.path.exists("./test_stage8_sn.db"):
        try:
            os.remove("./test_stage8_sn.db")
        except PermissionError:
            pass


def get_auth_token(username: str) -> str:
    db = TestSessionLocal()
    user = db.query(User).filter(User.username == username).first()
    token = create_access_token(
        subject=user.username,
        role=user.roles[0].name if user.roles else "VIEWER",
        user_id=user.id,
        roles=[r.name for r in user.roles],
        token_version=user.token_version
    )
    db.close()
    return token


# ============================================================================
# 1. Authentication & Configuration Tests
# ============================================================================

def test_auth_missing_credentials_reported_not_configured():
    provider = ServiceNowAuthProvider(instance_url=None, username=None, password=None)
    assert not provider.is_configured
    status = provider.get_status_summary()
    assert not status["is_configured"]
    assert status["instance_url"] == "Not Configured"

    with pytest.raises(ServiceNowAuthError):
        provider.get_auth_headers()


def test_auth_basic_headers_generation():
    provider = ServiceNowAuthProvider(
        instance_url="https://dev12345.service-now.com",
        auth_mode="basic",
        username="admin",
        password="SecretPassword123"
    )
    assert provider.is_configured
    headers = provider.get_auth_headers()
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Basic ")


def test_auth_token_headers_generation():
    provider = ServiceNowAuthProvider(
        instance_url="https://dev12345.service-now.com",
        auth_mode="token",
        token="secret-token-xyz"
    )
    assert provider.is_configured
    headers = provider.get_auth_headers()
    assert headers["Authorization"] == "Bearer secret-token-xyz"


def test_auth_secret_masking_never_leaks_plaintext():
    masked = mask_secret("super_sensitive_api_key_123456789")
    assert "sensitive" not in masked
    assert masked.startswith("supe...")
    assert masked.endswith("6789")
    assert mask_secret(None) == "Not Configured"
    assert mask_secret("short") == "********"


# ============================================================================
# 2. HTTP Client Resiliency, Pagination & Rate Limiting Tests (Mocked)
# ============================================================================

def test_client_successful_table_query(monkeypatch):
    mock_records = [
        {"sys_id": "sys_inc_001", "number": "INC001001", "short_description": "Database High CPU"},
        {"sys_id": "sys_inc_002", "number": "INC001002", "short_description": "Payment Gateway Timeout"}
    ]

    def mock_request(self, method, url, **kwargs):
        return httpx.Response(200, json={"result": mock_records}, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    provider = ServiceNowAuthProvider(
        instance_url="https://dev12345.service-now.com",
        auth_mode="basic",
        username="admin",
        password="password"
    )
    client = ServiceNowClient(auth_provider=provider)
    records = client.get_table_records("incident", limit=10)
    assert len(records) == 2
    assert records[0]["number"] == "INC001001"


def test_client_pagination(monkeypatch):
    call_count = 0

    def mock_request(self, method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        params = kwargs.get("params", {})
        offset = params.get("sysparm_offset", 0)
        
        if offset == 0:
            batch = [{"sys_id": f"id_{i}", "number": f"INC{i}"} for i in range(10)]
        elif offset == 10:
            batch = [{"sys_id": f"id_{i}", "number": f"INC{i}"} for i in range(10, 15)]
        else:
            batch = []
        return httpx.Response(200, json={"result": batch}, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    provider = ServiceNowAuthProvider(
        instance_url="https://dev12345.service-now.com",
        auth_mode="basic",
        username="admin",
        password="password"
    )
    client = ServiceNowClient(auth_provider=provider)
    all_records = client.get_all_table_records("incident", max_records=20, page_size=10)
    assert len(all_records) == 15
    assert call_count == 2


def test_client_429_rate_limit_retry(monkeypatch):
    attempts = 0

    def mock_request(self, method, url, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "0.1"}, text="Too Many Requests", request=httpx.Request(method, url))
        return httpx.Response(200, json={"result": [{"sys_id": "1", "number": "INC1"}]}, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    provider = ServiceNowAuthProvider(
        instance_url="https://dev12345.service-now.com",
        auth_mode="basic",
        username="admin",
        password="password"
    )
    client = ServiceNowClient(auth_provider=provider, max_retries=2, backoff_base=1.1)
    records = client.get_table_records("incident")
    assert attempts == 2
    assert len(records) == 1


def test_client_401_auth_failure_raises(monkeypatch):
    def mock_request(self, method, url, **kwargs):
        return httpx.Response(401, text="User Not Authenticated", request=httpx.Request(method, url))

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    provider = ServiceNowAuthProvider(
        instance_url="https://dev12345.service-now.com",
        auth_mode="basic",
        username="admin",
        password="bad_password"
    )
    client = ServiceNowClient(auth_provider=provider)
    with pytest.raises(ServiceNowAuthError):
        client.get_table_records("incident")


# ============================================================================
# 3. Field Normalization & Mapping Tests
# ============================================================================

def test_incident_mapping_with_nested_reference_objects():
    raw = {
        "sys_id": "9c5738542f201110a",
        "number": "INC0099881",
        "short_description": "Network latency anomaly detected",
        "description": "Ping times spiked to 450ms across us-east.",
        "state": "2",
        "priority": "1",
        "urgency": "1",
        "impact": "1",
        "category": "Network",
        "subcategory": "Router",
        "assignment_group": {"link": "https://.../group/123", "value": "grp_net_01", "display_value": "Network Operations"},
        "cmdb_ci": {"link": "https://.../ci/999", "value": "SVC_PAYMENT", "display_value": "Payment Gateway"},
        "problem_id": {"value": "PRB001100"},
        "rfc": "CHG005500",
        "opened_at": "2026-08-22 10:15:30",
        "work_start": "2026-08-22 10:20:00"
    }

    mapped = sn_to_opsintel_incident(raw)
    assert mapped["external_id"] == "9c5738542f201110a"
    assert mapped["incident_id"] == "INC0099881"
    assert mapped["status"] == "IN_PROGRESS"
    assert mapped["priority"] == "P1"
    assert mapped["service_id"] == "SVC_PAYMENT"
    assert mapped["assignment_group"] == "Network Operations"
    assert mapped["problem_id"] == "PRB001100"
    assert mapped["related_change_id"] == "CHG005500"
    assert isinstance(mapped["opened_at"], datetime)


def test_problem_mapping_and_reverse():
    raw = {
        "sys_id": "prb_sys_777",
        "number": "PRB00777",
        "short_description": "Memory leak in auth session cache",
        "problem_state": "103",
        "priority": "2",
        "cmdb_ci": "SVC_AUTH",
        "u_root_cause_category": "Software Defect",
        "cause_notes": "Unbounded hash map retained dead tokens.",
        "work_around": "Restart worker pods every 6 hours.",
        "known_error": "true"
    }

    mapped = sn_to_opsintel_problem(raw)
    assert mapped["problem_id"] == "PRB00777"
    assert mapped["status"] == "KNOWN_ERROR"
    assert mapped["kedb_status"] == "PUBLISHED"
    assert mapped["root_cause_category"] == "Software Defect"

    # Reverse mapping for writeback
    update_dict = {"status": "RESOLVED", "resolution": "Patched eviction policy in v2.4.1"}
    sn_payload = opsintel_to_sn_problem(update_dict)
    assert sn_payload["state"] == "104"
    assert sn_payload["fix_notes"] == "Patched eviction policy in v2.4.1"


def test_change_mapping_and_reverse():
    raw = {
        "sys_id": "chg_sys_555",
        "number": "CHG00555",
        "short_description": "Deploy Auth Cache Fix",
        "state": "-2",
        "type": "emergency",
        "risk": "1",
        "cab_approval": "approved",
        "cmdb_ci": "SVC_AUTH",
        "change_plan": "Helm upgrade --set tag=2.4.1",
        "backout_plan": "Helm rollback auth 1"
    }

    mapped = sn_to_opsintel_change(raw)
    assert mapped["change_id"] == "CHG00555"
    assert mapped["change_type"] == "EMERGENCY"
    assert mapped["risk_level"] == "HIGH"
    assert mapped["status"] == "IN_PROGRESS"
    assert mapped["cab_status"] == "APPROVED"

    sn_payload = opsintel_to_sn_change({"status": "COMPLETED", "close_notes": "Deployment verified"})
    assert sn_payload["state"] == "3"
    assert sn_payload["close_notes"] == "Deployment verified"


# ============================================================================
# 4. Ingestion, Idempotency & Incremental Sync Tests
# ============================================================================

def test_sync_idempotency_repeated_sync_no_duplicates():
    db = TestSessionLocal()
    engine = ServiceNowSyncEngine()

    raw_services = [
        {"sys_id": "svc_sys_01", "name": "Payment Gateway", "u_service_id": "SVC_PAYMENT", "criticality": "1"}
    ]
    raw_incidents = [
        {"sys_id": "inc_sys_01", "number": "INC99001", "short_description": "DB Spike", "cmdb_ci": "SVC_PAYMENT", "priority": "1"}
    ]

    # Ingest Pass 1
    engine.ingest_services(db, raw_services, actor_username="test_sync")
    engine.ingest_incidents(db, raw_incidents, actor_username="test_sync")

    count1 = db.query(Incident).filter(Incident.external_id == "inc_sys_01").count()
    assert count1 == 1

    # Ingest Pass 2 (Same record with updated description)
    raw_incidents[0]["short_description"] = "DB Spike - Resolved"
    raw_incidents[0]["state"] = "6"
    engine.ingest_incidents(db, raw_incidents, actor_username="test_sync")

    count2 = db.query(Incident).filter(Incident.external_id == "inc_sys_01").count()
    assert count2 == 1  # IDEMPOTENT: No duplicate row created

    inc = db.query(Incident).filter(Incident.external_id == "inc_sys_01").first()
    assert inc.title == "DB Spike - Resolved"
    assert inc.status == "RESOLVED"

    # Verify Audit Events logged
    audits = db.query(AuditEvent).filter(AuditEvent.entity_id == "INC99001").all()
    assert len(audits) >= 2
    assert audits[0].action == "SERVICENOW_IMPORT"
    assert audits[1].action == "SERVICENOW_UPDATE"

    db.close()


def test_sync_engine_orchestration_all_entities(monkeypatch):
    db = TestSessionLocal()

    mock_db = {
        "cmdb_ci_service": [{"sys_id": "svc_10", "name": "Catalog Service", "u_service_id": "SVC_CATALOG"}],
        "problem": [{"sys_id": "prb_10", "number": "PRB0010", "short_description": "Memory leak", "cmdb_ci": "SVC_CATALOG"}],
        "change_request": [{"sys_id": "chg_10", "number": "CHG0010", "short_description": "Patch Memory", "cmdb_ci": "SVC_CATALOG"}],
        "incident": [{"sys_id": "inc_10", "number": "INC0010", "short_description": "High Latency", "cmdb_ci": "SVC_CATALOG"}],
        "task_sla": [{"sys_id": "sla_10", "u_sla_id": "SLA_10", "task": "INC0010", "cmdb_ci": "SVC_CATALOG"}]
    }

    def mock_request(self, method, url, **kwargs):
        for table, records in mock_db.items():
            if f"/api/now/table/{table}" in url:
                return httpx.Response(200, json={"result": records}, request=httpx.Request(method, url))
        return httpx.Response(200, json={"result": []}, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    provider = ServiceNowAuthProvider(
        instance_url="https://dev12345.service-now.com",
        auth_mode="basic",
        username="admin",
        password="password"
    )
    client = ServiceNowClient(auth_provider=provider)
    engine = ServiceNowSyncEngine(client=client)

    result = engine.sync_all(db, full_sync=True, actor_username="admin")
    assert result["status"] == "SUCCESS"
    assert result["total_inserted"] == 5

    # Verify SyncState records
    sync_states = db.query(SyncState).all()
    assert len(sync_states) >= 5
    for s in sync_states:
        assert s.status == "SUCCESS"
        assert s.records_inserted >= 1

    db.close()


# ============================================================================
# 5. Inbound Webhook Receiver & Replay Protection Tests
# ============================================================================

def test_webhook_valid_signature_ingests_record_and_audits():
    db = TestSessionLocal()
    receiver = ServiceNowWebhookReceiver(webhook_secret="test-webhook-secret-2026")

    payload = {
        "event_id": "SN-EVT-99001",
        "idempotency_key": "IDEM-KEY-99001",
        "event_type": "incident.created",
        "entity_name": "incident",
        "record": {
            "sys_id": "webhook_inc_001",
            "number": "INC99881",
            "short_description": "Webhook P1 Alert",
            "priority": "1",
            "cmdb_ci": "SVC_PAYMENT",
            "state": "1"
        }
    }

    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_hmac_sha256(raw_bytes, "test-webhook-secret-2026")
    timestamp_hdr = str(time.time())

    res = receiver.process_webhook(
        db=db,
        raw_body=raw_bytes,
        signature_header=f"sha256={sig}",
        timestamp_header=timestamp_hdr
    )

    assert res["status"] == "PROCESSED"
    assert res["event_id"] == "SN-EVT-99001"

    # Verify record in DB
    inc = db.query(Incident).filter(Incident.external_id == "webhook_inc_001").first()
    assert inc is not None
    assert inc.title == "Webhook P1 Alert"

    # Verify WebhookEvent logged
    evt = db.query(WebhookEvent).filter(WebhookEvent.event_id == "SN-EVT-99001").first()
    assert evt is not None
    assert evt.status == "PROCESSED"

    # Replay Protection: Second execution with same idempotency key must be ignored
    res_replay = receiver.process_webhook(
        db=db,
        raw_body=raw_bytes,
        signature_header=f"sha256={sig}",
        timestamp_header=timestamp_hdr
    )
    assert res_replay["status"] == "DUPLICATE_IGNORED"

    db.close()


def test_webhook_invalid_signature_rejected():
    db = TestSessionLocal()
    receiver = ServiceNowWebhookReceiver(webhook_secret="test-webhook-secret-2026")

    raw_bytes = b'{"event_id": "fake", "record": {}}'
    with pytest.raises(ServiceNowValidationError) as exc_info:
        receiver.process_webhook(
            db=db,
            raw_body=raw_bytes,
            signature_header="sha256=invalid_signature_hex",
            timestamp_header=str(time.time())
        )
    assert "signature" in str(exc_info.value).lower()
    db.close()


def test_webhook_expired_timestamp_rejected():
    db = TestSessionLocal()
    receiver = ServiceNowWebhookReceiver(webhook_secret="test-webhook-secret-2026", timestamp_tolerance_seconds=60)

    raw_bytes = b'{"event_id": "expired"}'
    sig = compute_hmac_sha256(raw_bytes, "test-webhook-secret-2026")
    old_timestamp = str(time.time() - 500)  # 500 seconds ago (>60s tolerance)

    with pytest.raises(ServiceNowValidationError) as exc_info:
        receiver.process_webhook(
            db=db,
            raw_body=raw_bytes,
            signature_header=sig,
            timestamp_header=old_timestamp
        )
    assert "timestamp" in str(exc_info.value).lower()
    db.close()


# ============================================================================
# 6. Controlled Write-Back Tests
# ============================================================================

def test_controlled_writeback_incident(monkeypatch):
    db = TestSessionLocal()
    
    # Create incident with external_id
    svc = db.query(Service).first() or Service(service_id="SVC_TEST", service_name="Test", criticality="HIGH")
    db.add(svc)
    db.flush()

    inc = Incident(
        incident_id="INC-WRITEBACK-01",
        external_id="sn_sys_wb_01",
        title="Payment Latency",
        priority="P2",
        status="IN_PROGRESS",
        service_id=svc.service_id
    )
    db.add(inc)
    db.commit()

    called_patch = False
    def mock_request(self, method, url, **kwargs):
        nonlocal called_patch
        if method == "PATCH" and "sn_sys_wb_01" in url:
            called_patch = True
            return httpx.Response(200, json={"result": {"state": "6", "close_notes": "Resolved by SRE"}}, request=httpx.Request(method, url))
        return httpx.Response(200, json={"result": {}}, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    provider = ServiceNowAuthProvider(
        instance_url="https://dev12345.service-now.com",
        auth_mode="basic",
        username="admin",
        password="password"
    )
    client = ServiceNowClient(auth_provider=provider)
    engine = ServiceNowSyncEngine(client=client)

    admin_user = db.query(User).filter(User.username == "admin").first()
    res = engine.writeback_entity(
        db=db,
        entity_name="incident",
        entity_id="INC-WRITEBACK-01",
        updates={"status": "RESOLVED", "resolution_notes": "Resolved by SRE"},
        actor_user=admin_user
    )

    assert res["status"] == "SUCCESS"
    assert called_patch

    # Check local DB updated
    db.refresh(inc)
    assert inc.status == "RESOLVED"
    assert inc.resolution_notes == "Resolved by SRE"

    # Check AuditEvent generated
    audit = db.query(AuditEvent).filter(
        AuditEvent.entity_id == "INC-WRITEBACK-01",
        AuditEvent.action == "OPSI_WRITEBACK"
    ).first()
    assert audit is not None
    assert audit.actor_username == "admin"

    db.close()


# ============================================================================
# 7. RBAC & Protected Endpoints Tests
# ============================================================================

def test_rbac_viewer_can_view_status_but_cannot_sync_or_writeback():
    viewer_token = get_auth_token("viewer")
    headers = {"Authorization": f"Bearer {viewer_token}"}

    # Viewer CAN view status
    res_status = client.get("/api/v1/integrations/servicenow/status", headers=headers)
    assert res_status.status_code == 200

    # Viewer CANNOT trigger sync
    res_sync = client.post("/api/v1/integrations/servicenow/sync", headers=headers, json={"full_sync": False})
    assert res_sync.status_code == 403

    # Viewer CANNOT perform writeback
    res_wb = client.post("/api/v1/integrations/servicenow/writeback/incident/INC1", headers=headers, json={"updates": {}})
    assert res_wb.status_code == 403

    # Viewer CANNOT test connection
    res_test = client.post("/api/v1/integrations/servicenow/test-connection", headers=headers)
    assert res_test.status_code == 403


def test_rbac_analyst_can_sync_but_cannot_writeback_or_manage():
    analyst_token = get_auth_token("analyst")
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # Analyst CAN view status
    res_status = client.get("/api/v1/integrations/servicenow/status", headers=headers)
    assert res_status.status_code == 200

    # Analyst CANNOT test connection (manage permission required)
    res_test = client.post("/api/v1/integrations/servicenow/test-connection", headers=headers)
    assert res_test.status_code == 403

    # Analyst CANNOT perform writeback
    res_wb = client.post("/api/v1/integrations/servicenow/writeback/incident/INC1", headers=headers, json={"updates": {}})
    assert res_wb.status_code == 403


def test_rbac_admin_full_integration_access():
    admin_token = get_auth_token("admin")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin CAN test connection
    res_test = client.post("/api/v1/integrations/servicenow/test-connection", headers=headers)
    assert res_test.status_code == 200

    # Admin CAN get sync status
    res_sync_st = client.get("/api/v1/integrations/servicenow/sync-status", headers=headers)
    assert res_sync_st.status_code == 200

    # Admin CAN get error logs
    res_err = client.get("/api/v1/integrations/servicenow/errors", headers=headers)
    assert res_err.status_code == 200
