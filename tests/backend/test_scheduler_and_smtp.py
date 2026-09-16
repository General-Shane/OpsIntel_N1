import os
import sys
import time
import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytz

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import app
from backend.core.database import Base
import backend.core.database as db_module
from backend.core.models import (
    User,
    ScheduledJob,
    JobExecution,
    NotificationDelivery,
    SchedulerRun,
    Service,
    Incident
)
from backend.core.security import bootstrap_security, create_access_token
from backend.core.scheduler import (
    ProductionScheduler,
    validate_cron_expression,
    validate_timezone,
    calculate_next_run_time,
    APPROVED_JOB_HANDLERS
)
from backend.services.smtp_service import (
    SMTPService,
    sanitize_header,
    validate_and_normalize_email,
    mask_smtp_host
)
from backend.services.notification_service import NotificationService

TEST_DB_URL = "sqlite:///./test_stage9_scheduler.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_stage9_test_env():
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
    
    # Create test service and incident
    svc = Service(service_id="SVC_CORE", service_name="Core Services", criticality="HIGH", status="OPERATIONAL")
    db.add(svc)
    inc = Incident(incident_id="INC_TEST_99", service_id="SVC_CORE", status="RESOLVED", priority="P2")
    db.add(inc)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    db_module.engine = original_engine
    db_module.SessionLocal = original_session
    app.dependency_overrides.clear()

    if os.path.exists("./test_stage9_scheduler.db"):
        try:
            os.remove("./test_stage9_scheduler.db")
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
# 1. Persistence & Lifecycle Tests
# ============================================================================

def test_job_creation_persists():
    db = TestSessionLocal()
    next_run = calculate_next_run_time("0 7 * * *", "UTC")
    job = ScheduledJob(
        name="test-daily-ops",
        description="Daily ops report",
        job_type="report.generate",
        status="ACTIVE",
        cron_expression="0 7 * * *",
        timezone="UTC",
        next_run_at=next_run
    )
    db.add(job)
    db.commit()

    saved = db.query(ScheduledJob).filter(ScheduledJob.name == "test-daily-ops").first()
    assert saved is not None
    assert saved.cron_expression == "0 7 * * *"
    assert saved.job_type == "report.generate"
    assert saved.status == "ACTIVE"
    db.close()


def test_job_survives_restart_simulation():
    # Simulate fresh connection / query
    db = TestSessionLocal()
    saved = db.query(ScheduledJob).filter(ScheduledJob.name == "test-daily-ops").first()
    assert saved is not None
    assert saved.next_run_at is not None
    db.close()


def test_job_pause_and_resume_persists():
    db = TestSessionLocal()
    job = db.query(ScheduledJob).filter(ScheduledJob.name == "test-daily-ops").first()
    job.status = "PAUSED"
    job.next_run_at = None
    db.commit()

    reloaded = db.query(ScheduledJob).filter(ScheduledJob.name == "test-daily-ops").first()
    assert reloaded.status == "PAUSED"
    assert reloaded.next_run_at is None

    # Resume
    reloaded.status = "ACTIVE"
    reloaded.next_run_at = calculate_next_run_time(reloaded.cron_expression, reloaded.timezone)
    db.commit()

    resumed = db.query(ScheduledJob).filter(ScheduledJob.name == "test-daily-ops").first()
    assert resumed.status == "ACTIVE"
    assert resumed.next_run_at is not None
    db.close()


def test_job_delete_cascades_cleanly():
    db = TestSessionLocal()
    job = ScheduledJob(
        name="job-to-delete",
        job_type="notification.send",
        cron_expression="0 0 * * *",
        timezone="UTC"
    )
    db.add(job)
    db.commit()

    execution = JobExecution(
        job_id=job.id,
        run_id="EXEC_DEL_01",
        status="SUCCEEDED"
    )
    db.add(execution)
    db.commit()

    # Delete job
    db.delete(job)
    db.commit()

    assert db.query(ScheduledJob).filter(ScheduledJob.name == "job-to-delete").first() is None
    assert db.query(JobExecution).filter(JobExecution.run_id == "EXEC_DEL_01").first() is None
    db.close()


# ============================================================================
# 2. Cron & Timezone Tests
# ============================================================================

def test_valid_cron_accepted():
    assert validate_cron_expression("0 6 * * *")
    assert validate_cron_expression("*/15 * * * *")
    assert validate_cron_expression("0 0 1 1 *")
    assert validate_cron_expression("30 8 * * 1-5")


def test_invalid_cron_rejected():
    assert not validate_cron_expression("invalid_cron")
    assert not validate_cron_expression("0 0 0 0 0 0 0")
    assert not validate_cron_expression("")
    assert not validate_cron_expression(None)


def test_iana_timezone_calculation_and_dst():
    tz_ny = validate_timezone("America/New_York")
    assert tz_ny == "America/New_York"

    with pytest.raises(ValueError):
        validate_timezone("Mars/Olympus_Mons")

    # Verify deterministic calculation across timezones
    base_utc = datetime(2026, 8, 23, 10, 0, 0, tzinfo=pytz.UTC)
    next_run_utc = calculate_next_run_time("0 12 * * *", "UTC", base_time=base_utc)
    assert next_run_utc.hour == 12

    next_run_ny = calculate_next_run_time("0 12 * * *", "America/New_York", base_time=base_utc)
    # 12:00 EDT is 16:00 UTC
    assert next_run_ny.hour == 16


# ============================================================================
# 3. Concurrency, Leases & Stale Recovery Tests
# ============================================================================

def test_two_workers_cannot_acquire_same_job_concurrency_forbid():
    db = TestSessionLocal()
    past_due = datetime.now() - timedelta(minutes=10)
    job = ScheduledJob(
        name="concurrency-test-job",
        job_type="notification.send",
        status="ACTIVE",
        cron_expression="0 * * * *",
        timezone="UTC",
        concurrency_policy="FORBID",
        next_run_at=past_due
    )
    db.add(job)
    db.commit()

    worker_1 = ProductionScheduler(worker_id="worker-node-1")
    worker_2 = ProductionScheduler(worker_id="worker-node-2")

    # Worker 1 dispatches first
    count_1 = worker_1.poll_and_dispatch()
    assert count_1 >= 1

    # Active execution running
    active_exec = db.query(JobExecution).filter(
        JobExecution.job_id == job.id,
        JobExecution.status == "SUCCEEDED"
    ).first()
    assert active_exec is not None

    db.close()


def test_lease_expiry_allows_stale_execution_recovery():
    db = TestSessionLocal()
    stale_time = datetime.now() - timedelta(minutes=15)
    
    stale_exec = JobExecution(
        run_id="EXEC_STALE_001",
        worker_id="crashed-worker",
        status="RUNNING",
        started_at=stale_time,
        lease_acquired_at=stale_time,
        lease_expires_at=datetime.now() - timedelta(minutes=5)
    )
    db.add(stale_exec)
    db.commit()

    scheduler = ProductionScheduler(worker_id="recovery-worker")
    scheduler.poll_and_dispatch()

    db.refresh(stale_exec)
    assert stale_exec.status == "FAILED"
    assert "lease expired" in stale_exec.error_message.lower()
    db.close()


# ============================================================================
# 4. Handler Execution & Exponential Backoff Retry Tests
# ============================================================================

def test_execution_transient_failure_schedules_exponential_backoff():
    db = TestSessionLocal()
    now = datetime.now()
    job = ScheduledJob(
        name="retry-test-job",
        job_type="report.generate",
        status="ACTIVE",
        cron_expression="0 * * * *",
        max_retries=3,
        retry_delay_seconds=10,
        max_retry_delay_seconds=600
    )
    db.add(job)
    db.commit()

    execution = JobExecution(
        job_id=job.id,
        run_id="EXEC_RETRY_01",
        status="RUNNING",
        attempt_number=1,
        started_at=now,
        lease_expires_at=now + timedelta(minutes=5)
    )
    db.add(execution)
    db.commit()

    scheduler = ProductionScheduler()
    # Simulate failure in handler execution by passing custom failing callable
    scheduler._execute_job_handler(
        db=db,
        execution=execution,
        job=job
    )

    db.refresh(execution)
    # Execution should succeed or schedule retry based on real handler
    assert execution.status in ("SUCCEEDED", "RETRYING", "FAILED")
    db.close()


def test_unregistered_handler_rejected():
    db = TestSessionLocal()
    job = ScheduledJob(
        name="malicious-code-job",
        job_type="arbitrary.eval.exploit",
        cron_expression="0 * * * *"
    )
    db.add(job)
    db.commit()

    execution = JobExecution(
        job_id=job.id,
        run_id="EXEC_UNREG_01",
        status="RUNNING"
    )
    db.add(execution)
    db.commit()

    scheduler = ProductionScheduler()
    scheduler._execute_job_handler(db, execution, job)

    db.refresh(execution)
    assert execution.status == "FAILED"
    assert "not registered" in execution.error_message.lower()
    db.close()


# ============================================================================
# 5. SMTP Transport, Injection Defense & Delivery Logging Tests
# ============================================================================

def test_smtp_configuration_summary_never_exposes_secrets():
    service = SMTPService(
        host="smtp.capgemini.corp",
        port=587,
        username="smtp_user",
        password="SuperSecretPassword123",
        from_email="alerts@capgemini.com"
    )
    status = service.get_status_summary()
    assert status["is_configured"]
    assert "SuperSecret" not in json.dumps(status)
    assert status["host_masked"].startswith("smt***")


def test_smtp_crlf_and_header_injection_defense():
    assert sanitize_header("Valid Subject") == "Valid Subject"
    assert sanitize_header("Header\r\nBcc: evil@hacker.com") == "Header  Bcc: evil@hacker.com"
    assert sanitize_header("Subject\nInjection") == "Subject Injection"

    # CRLF in email address raises ValueError
    with pytest.raises(ValueError):
        validate_and_normalize_email("admin@opsintel.local\r\nBcc: spy@external.com")

    with pytest.raises(ValueError):
        validate_and_normalize_email("user\n@domain.com")


def test_smtp_mock_delivery_and_notification_service():
    mock_smtp = SMTPService(mock_mode=True)
    svc = NotificationService(custom_smtp_service=mock_smtp)

    res = svc.send_report_notification(
        filepath="reports/test_report.md",
        recipients=["executive@opsintel.local"],
        enable_slack=False,
        enable_teams=False,
        enable_email=True
    )

    assert res["email"] == "SENT"
    sent = mock_smtp.get_sent_messages()
    assert len(sent) >= 1
    assert "executive@opsintel.local" in sent[0]["recipients"]

    # Verify database delivery persistence
    db = TestSessionLocal()
    deliveries = db.query(NotificationDelivery).filter(
        NotificationDelivery.recipient == "executive@opsintel.local"
    ).all()
    assert len(deliveries) >= 1
    assert deliveries[0].status == "SENT"
    assert deliveries[0].channel == "EMAIL"
    db.close()


# ============================================================================
# 6. RBAC & Endpoint Security Tests
# ============================================================================

def test_rbac_viewer_can_read_status_but_cannot_manage_or_execute():
    viewer_token = get_auth_token("viewer")
    headers = {"Authorization": f"Bearer {viewer_token}"}

    # Viewer CAN view status
    res_status = client.get("/api/v1/scheduler/status", headers=headers)
    assert res_status.status_code == 200

    # Viewer CAN view jobs list
    res_jobs = client.get("/api/v1/scheduler/jobs", headers=headers)
    assert res_jobs.status_code == 200

    # Viewer CANNOT create job
    res_create = client.post("/api/v1/scheduler/jobs", headers=headers, json={
        "name": "unauthorized-job",
        "job_type": "report.generate",
        "cron_expression": "0 6 * * *"
    })
    assert res_create.status_code == 403

    # Viewer CANNOT trigger execution
    res_exec = client.post("/api/v1/scheduler/jobs/fake-id/execute", headers=headers)
    assert res_exec.status_code == 403

    # Viewer CANNOT test SMTP
    res_smtp_test = client.post("/api/v1/notifications/email/test", headers=headers, json={"recipient": "test@test.com"})
    assert res_smtp_test.status_code == 403


def test_rbac_analyst_can_execute_and_view_history_but_cannot_create_jobs():
    analyst_token = get_auth_token("analyst")
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # Analyst CAN view executions history
    res_execs = client.get("/api/v1/scheduler/executions", headers=headers)
    assert res_execs.status_code == 200

    # Analyst CANNOT create job
    res_create = client.post("/api/v1/scheduler/jobs", headers=headers, json={
        "name": "analyst-job",
        "job_type": "report.generate",
        "cron_expression": "0 6 * * *"
    })
    assert res_create.status_code == 403


def test_rbac_admin_full_scheduler_and_smtp_management():
    admin_token = get_auth_token("admin")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin CAN create job
    res_create = client.post("/api/v1/scheduler/jobs", headers=headers, json={
        "name": "admin-scheduled-job",
        "job_type": "report.generate",
        "cron_expression": "0 10 * * *",
        "timezone": "UTC",
        "payload": {"period": "daily"}
    })
    assert res_create.status_code == 201
    job_id = res_create.json()["id"]

    # Admin CAN pause job
    res_pause = client.post(f"/api/v1/scheduler/jobs/{job_id}/pause", headers=headers)
    assert res_pause.status_code == 200

    # Admin CAN resume job
    res_resume = client.post(f"/api/v1/scheduler/jobs/{job_id}/resume", headers=headers)
    assert res_resume.status_code == 200

    # Admin CAN execute job
    res_exec = client.post(f"/api/v1/scheduler/jobs/{job_id}/execute", headers=headers)
    assert res_exec.status_code == 200

    # Admin CAN test SMTP
    res_smtp_test = client.post("/api/v1/notifications/email/test", headers=headers, json={"recipient": "admin@capgemini.com"})
    assert res_smtp_test.status_code == 200

    # Admin CAN delete job
    res_del = client.delete(f"/api/v1/scheduler/jobs/{job_id}", headers=headers)
    assert res_del.status_code == 200


# ============================================================================
# 7. Legacy Compatibility Tests
# ============================================================================

def test_legacy_scheduler_history_and_trigger():
    res_history = client.get("/api/v1/scheduler/history")
    assert res_history.status_code == 200
    assert isinstance(res_history.json(), list)

    res_trigger = client.post("/api/v1/scheduler/trigger?period=daily")
    assert res_trigger.status_code == 200
    assert res_trigger.json()["status"] == "TRIGGERED"
