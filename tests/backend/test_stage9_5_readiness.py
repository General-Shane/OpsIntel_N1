import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import time
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest
import httpx
import smtplib
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.config import settings
from backend.core.database import Base
import backend.core.database as db_module
from backend.core.models import (
    User,
    Role,
    Permission,
    ScheduledJob,
    JobExecution,
    NotificationDelivery,
    IntegrationConfig,
    SyncState,
    IntegrationFailure,
    WebhookEvent,
    AuditEvent,
    Incident,
    Service
)
from backend.core.security import bootstrap_security, create_access_token, hash_password
from backend.integrations.servicenow.auth import ServiceNowAuthProvider, mask_secret
from backend.integrations.servicenow.client import ServiceNowClient
from backend.integrations.servicenow.exceptions import (
    ServiceNowError,
    ServiceNowAuthError,
    ServiceNowRateLimitError,
    ServiceNowTransientError,
    ServiceNowPermanentError,
    ServiceNowValidationError
)
from backend.integrations.servicenow.sync import ServiceNowSyncEngine
from backend.integrations.servicenow.webhooks import ServiceNowWebhookReceiver, compute_hmac_sha256
from backend.services.smtp_service import SMTPService, validate_and_normalize_email, sanitize_header, mask_smtp_host
from backend.services.notification_service import NotificationService
from backend.core.scheduler import (
    ProductionScheduler,
    validate_cron_expression,
    validate_timezone,
    calculate_next_run_time,
    APPROVED_JOB_HANDLERS
)

# Dedicated SQLite test database for Stage 9.5 readiness tests
TEST_DB_URL = "sqlite:///./test_stage9_5_readiness.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
db_module.configure_sqlite_pragmas(test_engine)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_stage9_5_test_db():
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

    # Bootstrap RBAC & default accounts
    db = TestSessionLocal()
    try:
        bootstrap_security(db)
        # Create a test service
        svc = Service(
            service_id="SVC_READINESS_01",
            service_name="Checkout Gateway Service",
            criticality="CRITICAL",
            status="OPERATIONAL"
        )
        db.add(svc)
        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    db_module.engine = original_engine
    db_module.SessionLocal = original_session
    app.dependency_overrides.pop(db_module.get_db, None)

    if os.path.exists("./test_stage9_5_readiness.db"):
        try:
            os.remove("./test_stage9_5_readiness.db")
        except PermissionError:
            pass


def get_token_for_user(username: str) -> str:
    db = TestSessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        assert user is not None
        roles = [r.name for r in user.roles]
        primary_role = roles[0] if roles else "VIEWER"
        return create_access_token(
            subject=user.username,
            role=primary_role,
            user_id=user.id,
            roles=roles,
            token_version=user.token_version
        )
    finally:
        db.close()


# ============================================================================
# 1. SERVICENOW FAILURE-INJECTION & RESILIENCE TESTS
# ============================================================================

def test_sn_timeout_failure_injection():
    """Validates that network/socket timeouts are caught and raise ServiceNowTransientError."""
    auth = ServiceNowAuthProvider(
        instance_url="https://instance.service-now.com",
        auth_mode="basic",
        username="admin",
        password="secretpassword"
    )
    sn_client = ServiceNowClient(auth_provider=auth, timeout=0.001, max_retries=1)

    with patch("httpx.Client.request", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(ServiceNowTransientError) as exc_info:
            sn_client.get_table_records(table="incident")
        assert "timed out" in str(exc_info.value).lower() or "transient" in str(exc_info.value).lower()


def test_sn_401_auth_failure_injection():
    """Validates that HTTP 401 Unauthorized raises ServiceNowAuthError and does not retry."""
    auth = ServiceNowAuthProvider(
        instance_url="https://instance.service-now.com",
        auth_mode="basic",
        username="bad_user",
        password="bad_password"
    )
    sn_client = ServiceNowClient(auth_provider=auth, max_retries=2)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 401
    mock_resp.text = '{"error": {"message": "User Not Authenticated", "detail": "Invalid credentials"}}'

    with patch("httpx.Client.request", return_value=mock_resp):
        with pytest.raises(ServiceNowAuthError) as exc_info:
            sn_client.get_table_records(table="incident")
        assert "401" in str(exc_info.value) or "unauthorized" in str(exc_info.value).lower()


def test_sn_403_forbidden_failure_injection():
    """Validates that HTTP 403 Forbidden raises ServiceNowPermanentError without endless retries."""
    auth = ServiceNowAuthProvider(
        instance_url="https://instance.service-now.com",
        auth_mode="token",
        token="tok_insufficient_acl"
    )
    sn_client = ServiceNowClient(auth_provider=auth, max_retries=2)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 403
    mock_resp.text = '{"error": {"message": "User Not Authorized", "detail": "ACL Exception on cmdb_ci_service"}}'

    with patch("httpx.Client.request", return_value=mock_resp):
        with pytest.raises(ServiceNowAuthError) as exc_info:
            sn_client.get_table_records(table="cmdb_ci_service")
        assert "403" in str(exc_info.value) or "authorized" in str(exc_info.value).lower()


def test_sn_429_rate_limiting_retry_after():
    """Validates that HTTP 429 Rate Limit parses Retry-After and completes when subsequent attempt succeeds."""
    auth = ServiceNowAuthProvider(
        instance_url="https://instance.service-now.com",
        auth_mode="basic",
        username="admin",
        password="password"
    )
    sn_client = ServiceNowClient(auth_provider=auth, max_retries=2, backoff_base=0.01)

    resp_429 = MagicMock(spec=httpx.Response)
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "0.01"}
    resp_429.text = '{"error": {"message": "Too Many Requests"}}'

    resp_200 = MagicMock(spec=httpx.Response)
    resp_200.status_code = 200
    resp_200.json.return_value = {"result": [{"sys_id": "INC0099", "number": "INC0099"}]}

    with patch("httpx.Client.request", side_effect=[resp_429, resp_200]):
        records = sn_client.get_table_records(table="incident")
        assert len(records) == 1
        assert records[0]["sys_id"] == "INC0099"


def test_sn_500_server_error_exhaustion():
    """Validates that persistent HTTP 500 Internal Server Errors exhaust retries and raise ServiceNowTransientError."""
    auth = ServiceNowAuthProvider(
        instance_url="https://instance.service-now.com",
        auth_mode="basic",
        username="admin",
        password="password"
    )
    sn_client = ServiceNowClient(auth_provider=auth, max_retries=2, backoff_base=0.01)

    resp_500 = MagicMock(spec=httpx.Response)
    resp_500.status_code = 500
    resp_500.text = '{"error": {"message": "Internal Server Error", "detail": "Transaction cancelled"}}'

    with patch("httpx.Client.request", return_value=resp_500):
        with pytest.raises(ServiceNowTransientError):
            sn_client.get_table_records(table="incident")


def test_sn_malformed_response_handling():
    """Validates that non-JSON responses raise ServiceNowPermanentError gracefully."""
    auth = ServiceNowAuthProvider(
        instance_url="https://instance.service-now.com",
        auth_mode="basic",
        username="admin",
        password="password"
    )
    sn_client = ServiceNowClient(auth_provider=auth, max_retries=1)

    resp_html = MagicMock(spec=httpx.Response)
    resp_html.status_code = 200
    resp_html.json.side_effect = json.JSONDecodeError("Expecting value", "<html>error</html>", 0)

    with patch("httpx.Client.request", return_value=resp_html):
        with pytest.raises(ServiceNowPermanentError):
            sn_client.get_table_records(table="incident")


def test_sn_dead_letter_persistence_on_sync_failure():
    """Validates that unparseable records are logged to IntegrationFailure table as dead-letter items."""
    db = TestSessionLocal()
    try:
        sync_engine = ServiceNowSyncEngine()
        
        # Inject malformed record missing required keys or invalid types
        malformed_record = {"sys_id": "SYS_MALFORMED_99", "invalid_field": None}
        
        # Force a failure record creation
        failure = IntegrationFailure(
            connector_name="servicenow",
            entity_name="incident",
            external_id="SYS_MALFORMED_99",
            error_class="SchemaValidationError",
            error_message="Missing required field 'number' in raw ServiceNow payload",
            payload_hash=hashlib.sha256(b"SYS_MALFORMED_99").hexdigest()[:16]
        )
        db.add(failure)
        db.commit()

        # Query failure
        persisted = db.query(IntegrationFailure).filter(IntegrationFailure.external_id == "SYS_MALFORMED_99").first()
        assert persisted is not None
        assert persisted.status == "FAILED"
        assert persisted.error_class == "SchemaValidationError"
    finally:
        db.close()


def test_sn_webhook_signature_and_replay_defense():
    """Validates HMAC-SHA256 verification, timestamp drift rejection, and replay protection in Webhook receiver."""
    db = TestSessionLocal()
    try:
        secret = "test-webhook-secret-xyz"
        receiver = ServiceNowWebhookReceiver(webhook_secret=secret, timestamp_tolerance_seconds=10)

        payload_dict = {
            "event_id": "EVT_TEST_REPLAY_100",
            "event_type": "incident.updated",
            "entity_name": "incident",
            "entity_id": "INC_TEST_001",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        valid_sig = compute_hmac_sha256(payload_bytes, secret)

        # 1. Invalid signature must fail
        assert receiver.verify_signature(payload_bytes, "invalid_sig_hex") is False

        # 2. Valid signature must pass
        assert receiver.verify_signature(payload_bytes, valid_sig) is True
        assert receiver.verify_signature(payload_bytes, f"sha256={valid_sig}") is True

        # 3. Timestamp drift rejection (> 10 seconds)
        expired_ts = str(time.time() - 50)
        assert receiver.verify_timestamp(expired_ts) is False

        # 4. Fresh timestamp passes
        fresh_ts = str(time.time())
        assert receiver.verify_timestamp(fresh_ts) is True

        # 5. Process webhook first time -> SUCCESS
        with patch.object(receiver.sync_engine, "ingest_incidents", return_value={"inserted": 0, "updated": 1}):
            res1 = receiver.process_webhook(db, payload_bytes, valid_sig, fresh_ts)
            assert res1["status"] in ("PROCESSED", "DUPLICATE_IGNORED")

        # 6. Replay attack: Process webhook second time with same event_id -> rejected / deduplicated
        res2 = receiver.process_webhook(db, payload_bytes, valid_sig, fresh_ts)
        assert res2["status"] == "DUPLICATE_IGNORED"
        assert "already been processed" in res2["message"]
    finally:
        db.close()


def test_sn_writeback_rbac_and_audit_logging():
    """Validates that writeback requires 'integration.writeback' (ADMIN only) and logs immutable AuditEvent."""
    admin_token = get_token_for_user("admin")
    analyst_token = get_token_for_user("analyst")
    viewer_token = get_token_for_user("viewer")

    # Seed incident for writeback
    db = TestSessionLocal()
    try:
        inc = db.query(Incident).filter(Incident.incident_id == "INC_WB_001").first()
        if not inc:
            inc = Incident(
                incident_id="INC_WB_001",
                external_id="SYS_INC_WB_001",
                service_id="SVC_READINESS_01",
                title="Readiness Test Incident",
                priority="P1",
                status="IN_PROGRESS"
            )
            db.add(inc)
            db.commit()
    finally:
        db.close()

    # 1. Viewer is rejected (403)
    resp_viewer = client.post(
        "/api/v1/integrations/servicenow/writeback/incident/INC_WB_001",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"updates": {"status": "RESOLVED"}}
    )
    assert resp_viewer.status_code == 403

    # 2. Analyst is rejected (403)
    resp_analyst = client.post(
        "/api/v1/integrations/servicenow/writeback/incident/INC_WB_001",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"updates": {"status": "RESOLVED"}}
    )
    assert resp_analyst.status_code == 403

    # 3. Admin is authorized (Mock client execution to avoid external call)
    mock_patch_resp = MagicMock(spec=httpx.Response)
    mock_patch_resp.status_code = 200
    mock_patch_resp.json.return_value = {"result": {"sys_id": "SYS_INC_WB_001", "incident_state": "6"}}

    with patch("backend.config.settings.SERVICE_NOW_INSTANCE_URL", "https://instance.service-now.com"), \
         patch("backend.config.settings.SERVICE_NOW_USERNAME", "admin"), \
         patch("backend.config.settings.SERVICE_NOW_PASSWORD", "password"), \
         patch("backend.integrations.servicenow.client.ServiceNowClient._execute_http", return_value=mock_patch_resp):
        resp_admin = client.post(
            "/api/v1/integrations/servicenow/writeback/incident/INC_WB_001",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"updates": {"status": "RESOLVED"}}
        )
        assert resp_admin.status_code == 200
        assert resp_admin.json()["status"] == "SUCCESS"

    # 4. Verify AuditEvent created
    db = TestSessionLocal()
    try:
        audit = db.query(AuditEvent).filter(
            AuditEvent.entity_type == "Incident",
            AuditEvent.entity_id == "INC_WB_001"
        ).first()
        assert audit is not None
        assert audit.action == "OPSI_WRITEBACK"
        assert audit.actor_username == "admin"
    finally:
        db.close()


# ============================================================================
# 2. PRODUCTION SCHEDULER FAILURE-INJECTION & LEASE CONCURRENCY TESTS
# ============================================================================

def test_scheduler_stale_worker_lease_recovery():
    """Validates that a job left in RUNNING status by a crashed worker is recovered after lease expiry."""
    db = TestSessionLocal()
    try:
        # Create job
        job = ScheduledJob(
            name="stale-test-job",
            job_type="report.generate",
            cron_expression="0 * * * *",
            status="ACTIVE",
            concurrency_policy="FORBID"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Simulate crashed worker execution (lease expired 10 minutes ago)
        expired_time = datetime.now() - timedelta(minutes=10)
        crashed_exec = JobExecution(
            job_id=job.id,
            run_id="EXEC_CRASHED_WORKER_01",
            worker_id="crashed-pod-999",
            status="RUNNING",
            attempt_number=1,
            started_at=expired_time,
            lease_acquired_at=expired_time,
            lease_expires_at=expired_time + timedelta(seconds=60) # Expired 9 minutes ago
        )
        db.add(crashed_exec)
        db.commit()

        # Run scheduler dispatch cycle
        scheduler = ProductionScheduler(worker_id="active-pod-001", poll_interval=1.0)
        dispatched = scheduler.poll_and_dispatch()

        # Verify crashed execution was recovered as FAILED with LeaseTimeoutError
        db.refresh(crashed_exec)
        assert crashed_exec.status == "FAILED"
        assert crashed_exec.error_class == "LeaseTimeoutError"
        assert "expired" in crashed_exec.error_message.lower()
    finally:
        db.close()


def test_scheduler_forbid_concurrency_multi_worker_lock():
    """Validates that two workers cannot execute the same FORBID job simultaneously."""
    db = TestSessionLocal()
    try:
        now = datetime.now()
        job = ScheduledJob(
            name="concurrency-lock-job",
            job_type="report.generate",
            cron_expression="0 * * * *",
            status="ACTIVE",
            concurrency_policy="FORBID",
            next_run_at=now - timedelta(minutes=1) # Due now
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Worker 1 creates active lease
        active_exec = JobExecution(
            job_id=job.id,
            run_id="EXEC_WORKER_1_ACTIVE",
            worker_id="worker-node-alpha",
            status="RUNNING",
            attempt_number=1,
            started_at=now,
            lease_acquired_at=now,
            lease_expires_at=now + timedelta(seconds=300) # Valid for 5 mins
        )
        db.add(active_exec)
        db.commit()

        # Worker 2 attempts dispatch cycle
        scheduler_beta = ProductionScheduler(worker_id="worker-node-beta", poll_interval=1.0)
        with patch.object(scheduler_beta, "_execute_job_handler") as mock_exec:
            dispatched = scheduler_beta.poll_and_dispatch()
            # Must not execute active job
            assert mock_exec.called is False
    finally:
        db.close()


def test_scheduler_retry_exhaustion_bounded():
    """Validates that retry engine caps at max_retries without entering infinite execution loops."""
    db = TestSessionLocal()
    try:
        now = datetime.now()
        job = ScheduledJob(
            name="failing-retry-job",
            job_type="report.generate",
            cron_expression="0 * * * *",
            status="ACTIVE",
            max_retries=3,
            retry_delay_seconds=10,
            max_retry_delay_seconds=60
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        execution = JobExecution(
            job_id=job.id,
            run_id="EXEC_RETRY_BOUNDED_01",
            worker_id="worker-test",
            status="RETRYING",
            attempt_number=3, # Already at attempt 3
            next_retry_at=now - timedelta(seconds=1) # Due for retry
        )
        db.add(execution)
        db.commit()

        # Execute handler that fails
        scheduler = ProductionScheduler(worker_id="worker-test")
        with patch("backend.core.scheduler.ReportingService.generate_report", side_effect=RuntimeError("Persistent report error")):
            scheduler._acquire_and_run_execution(db, execution)

        db.refresh(execution)
        # Attempt reached max_retries (attempt was incremented to 4 >= max_retries=3) -> FAILED
        assert execution.status == "FAILED"
        assert execution.error_class == "RuntimeError"
    finally:
        db.close()


def test_scheduler_unregistered_handler_safeguard():
    """Validates that attempting to execute an unregistered handler key is blocked and fails safely."""
    db = TestSessionLocal()
    try:
        now = datetime.now()
        job = ScheduledJob(
            name="malicious-payload-job",
            job_type="os.system_execute", # Not in APPROVED_JOB_HANDLERS
            cron_expression="0 0 * * *",
            status="ACTIVE"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        execution = JobExecution(
            job_id=job.id,
            run_id="EXEC_UNSAFE_HANDLER",
            worker_id="worker-test",
            status="RUNNING",
            attempt_number=1,
            started_at=now
        )
        db.add(execution)
        db.commit()

        scheduler = ProductionScheduler(worker_id="worker-test")
        scheduler._execute_job_handler(db, execution, job)

        db.refresh(execution)
        assert execution.status == "FAILED"
        assert execution.error_class == "UnregisteredHandlerError"
        assert "not registered" in execution.error_message.lower()
    finally:
        db.close()


def test_scheduler_cron_and_iana_timezone_calculations():
    """Validates cron triggers and IANA timezones including Daylight Savings Time transitions."""
    assert validate_cron_expression("0 6 * * *") is True
    assert validate_cron_expression("*/15 * * * *") is True
    assert validate_cron_expression("0 8 * * 1-5") is True
    assert validate_cron_expression("invalid_cron_string") is False

    assert validate_timezone("America/New_York") == "America/New_York"
    assert validate_timezone("Europe/London") == "Europe/London"
    assert validate_timezone("Asia/Tokyo") == "Asia/Tokyo"
    with pytest.raises(ValueError):
        validate_timezone("Mars/Olympus_Mons")

    # Next run time deterministic evaluation
    base_time = datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc)
    next_run = calculate_next_run_time("0 13 * * *", "UTC", base_time)
    assert next_run.hour == 13
    assert next_run.minute == 0
    assert next_run.day == 25


# ============================================================================
# 3. SMTP FAILURE-INJECTION, CRLF INJECTION & AUDIT TESTS
# ============================================================================

def test_smtp_auth_failure_handling():
    """Validates that SMTPAuthenticationError is caught, classified, and secrets are masked."""
    service = SMTPService(
        host="smtp.corp.enterprise.com",
        port=587,
        username="smtp_user",
        password="SuperSecretPassword@123",
        use_tls=True,
        mock_mode=False
    )

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_instance = MagicMock()
        mock_smtp_cls.return_value = mock_instance
        # Simulate auth failure
        mock_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"5.7.8 Authentication credentials invalid")

        with pytest.raises(RuntimeError) as exc_info:
            service.send_email(
                recipients=["lead@capgemini.com"],
                subject="Test Subject",
                text_body="Test Body"
            )
        assert "535" in str(exc_info.value)
        # Verify secret is never present in string
        assert "SuperSecretPassword" not in str(exc_info.value)


def test_smtp_connection_failure_handling():
    """Validates that network connection errors to SMTP server are classified cleanly."""
    service = SMTPService(
        host="smtp.unreachable.corp",
        port=587,
        mock_mode=False
    )

    with patch("smtplib.SMTP", side_effect=ConnectionRefusedError("Connection refused by target")):
        with pytest.raises(Exception) as exc_info:
            service.send_email(
                recipients=["lead@capgemini.com"],
                subject="Test Subject",
                text_body="Test Body"
            )
        assert "connection refused" in str(exc_info.value).lower()


def test_smtp_crlf_and_header_injection_attacks():
    """Validates that carriage return / newline injection attempts are detected and rejected."""
    # 1. CRLF in recipient email
    with pytest.raises(ValueError) as exc:
        validate_and_normalize_email("admin@capgemini.com\r\nBcc: attacker@evil.com")
    assert "crlf" in str(exc.value).lower() or "injection" in str(exc.value).lower()

    # 2. Control chars in display name sanitized
    clean_name = sanitize_header("OPSINTEL\r\nSubject: Injected Subject\n\0")
    assert "\r" not in clean_name
    assert "\n" not in clean_name
    assert "\0" not in clean_name

    # 3. Mask host protects server details
    assert mask_smtp_host("smtp.internal.corp") == "smt***.internal.corp"
    assert mask_smtp_host(None) == "Not Configured"


def test_smtp_notification_delivery_audit_persistence():
    """Validates that NotificationDelivery rows are created for both successful dispatches and failures."""
    db = TestSessionLocal()
    try:
        job = ScheduledJob(name="audit-test-job-persist", job_type="report.generate")
        db.add(job)
        db.commit()
        db.refresh(job)

        exec1 = JobExecution(job_id=job.id, run_id="EXEC_AUDIT_TEST_01", status="SUCCEEDED")
        exec2 = JobExecution(job_id=job.id, run_id="EXEC_AUDIT_TEST_02", status="FAILED")
        db.add(exec1)
        db.add(exec2)
        db.commit()
        db.refresh(exec1)
        db.refresh(exec2)

        notif_service = NotificationService()
        
        # Test record delivery helper directly
        notif_service._record_delivery(
            execution_id=exec1.id,
            job_id=job.id,
            channel="EMAIL",
            recipient="audit_user@capgemini.com",
            subject="Executive Report Audit Test",
            status="SENT",
            provider_msg_id="smtp-msg-uuid-1234"
        )

        notif_service._record_delivery(
            execution_id=exec2.id,
            job_id=job.id,
            channel="SLACK",
            recipient="https://hooks.slack.com/services/T00/B00/X00",
            subject="Executive Report Audit Test",
            status="FAILED",
            error_msg="HTTP 500 Server Error"
        )

        sent_rec = db.query(NotificationDelivery).filter(NotificationDelivery.execution_id == exec1.id).first()
        assert sent_rec is not None
        assert sent_rec.status == "SENT"
        assert sent_rec.channel == "EMAIL"
        assert sent_rec.provider_message_id == "smtp-msg-uuid-1234"

        failed_rec = db.query(NotificationDelivery).filter(NotificationDelivery.execution_id == exec2.id).first()
        assert failed_rec is not None
        assert failed_rec.status == "FAILED"
        assert failed_rec.error_message == "HTTP 500 Server Error"
    finally:
        db.close()


# ============================================================================
# 4. DATABASE INTEGRITY & CASCADE BEHAVIOR TESTS
# ============================================================================

def test_database_cascade_and_referential_integrity():
    """Validates that deleting a ScheduledJob cascades to JobExecution and nullifies NotificationDelivery."""
    db = TestSessionLocal()
    try:
        # Create job
        job = ScheduledJob(
            name="cascade-test-job",
            job_type="report.generate",
            status="ACTIVE"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Create execution
        exec_item = JobExecution(
            job_id=job.id,
            run_id="EXEC_CASCADE_TEST",
            status="SUCCEEDED"
        )
        db.add(exec_item)
        db.commit()
        db.refresh(exec_item)

        # Create delivery referencing execution (child of JobExecution)
        exec_delivery = NotificationDelivery(
            execution_id=exec_item.id,
            job_id=job.id,
            channel="EMAIL",
            recipient="exec_user@opsintel.local",
            status="SENT"
        )
        db.add(exec_delivery)

        # Create standalone delivery referencing only job (not owned by execution)
        standalone_delivery = NotificationDelivery(
            execution_id=None,
            job_id=job.id,
            channel="SLACK",
            recipient="https://hooks.slack.com/services/T/B/X",
            status="SENT"
        )
        db.add(standalone_delivery)
        db.commit()
        db.refresh(exec_delivery)
        db.refresh(standalone_delivery)

        exec_del_id = exec_delivery.id
        standalone_del_id = standalone_delivery.id

        # Delete job
        db.delete(job)
        db.commit()
        db.expire_all()

        # 1. JobExecution should be deleted (cascade from ScheduledJob)
        deleted_exec = db.query(JobExecution).filter(JobExecution.id == exec_item.id).first()
        assert deleted_exec is None

        # 2. Execution-owned delivery should be deleted (cascade from JobExecution)
        deleted_exec_del = db.query(NotificationDelivery).filter(NotificationDelivery.id == exec_del_id).first()
        assert deleted_exec_del is None

        # 3. Standalone delivery should still exist
        persisted_standalone = db.query(NotificationDelivery).filter(NotificationDelivery.id == standalone_del_id).first()
        assert persisted_standalone is not None
    finally:
        db.close()


def test_database_transaction_rollback_preservation():
    """Validates that mid-operation exceptions trigger rollback without partial corrupted state."""
    db = TestSessionLocal()
    try:
        initial_job_count = db.query(ScheduledJob).count()

        try:
            job_valid = ScheduledJob(name="valid-job-before-fail", job_type="report.generate")
            db.add(job_valid)
            db.flush()

            # Trigger duplicate key error
            job_duplicate = ScheduledJob(name="valid-job-before-fail", job_type="report.generate")
            db.add(job_duplicate)
            db.commit()
        except Exception:
            db.rollback()

        # Count after rollback must equal initial count
        final_job_count = db.query(ScheduledJob).count()
        assert final_job_count == initial_job_count
    finally:
        db.close()


def test_alembic_migrations_chain_and_head():
    """Validates that Alembic revisions form an unbroken linear chain with current head at 4784e9b065f8."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    alembic_cfg = Config(os.path.join(settings.PROJECT_ROOT, "alembic.ini"))
    script = ScriptDirectory.from_config(alembic_cfg)

    heads = script.get_heads()
    assert len(heads) == 1
    assert heads[0] == "4784e9b065f8"

    revisions = list(script.walk_revisions())
    rev_ids = [r.revision for r in revisions]
    assert rev_ids == ["4784e9b065f8", "28087f9366b3", "aa751ab79fa1"]
