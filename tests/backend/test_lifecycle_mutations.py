import os
import sys
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import app
from backend.core.database import Base, get_db
import backend.core.database as db_module
from backend.core.models import (
    User, Role, Service, Problem, Change, Incident, SLARecord, AuditEvent
)
from backend.core.security import bootstrap_security, create_access_token

TEST_DB_URL = "sqlite:///./test_lifecycle_mutations.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
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

    app.dependency_overrides[get_db] = override_get_db

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()
    bootstrap_security(db)

    # Seed test service
    test_svc = Service(
        service_id="SVC_LIFECYCLE_TEST",
        service_name="Lifecycle Verification Service",
        criticality="CRITICAL",
        status="OPERATIONAL"
    )
    db.add(test_svc)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    db_module.engine = original_engine
    db_module.SessionLocal = original_session
    app.dependency_overrides.clear()

    if os.path.exists("./test_lifecycle_mutations.db"):
        try:
            os.remove("./test_lifecycle_mutations.db")
        except PermissionError:
            pass

def _get_auth_headers(role: str) -> dict:
    db = TestSessionLocal()
    user = db.query(User).filter(User.username == role.lower()).first()
    db.close()
    token = create_access_token(
        subject=user.username,
        role=role.upper(),
        user_id=user.id,
        roles=[role.upper()]
    )
    return {"Authorization": f"Bearer {token}"}

# ============================================================================
# Problem Lifecycle Tests
# ============================================================================

def test_problem_create_and_lifecycle_transitions():
    admin_headers = _get_auth_headers("admin")

    # 1. Create Problem
    create_res = client.post(
        "/api/v1/problems",
        json={
            "service_id": "SVC_LIFECYCLE_TEST",
            "title": "High latency in transaction authorization pool",
            "description": "Thread pool contention causing timeout spikes under heavy volume.",
            "priority": "P2",
            "category": "Performance",
            "assignment_group": "Tier-3 Core SRE"
        },
        headers=admin_headers
    )
    assert create_res.status_code == 201
    prb = create_res.json()
    prb_id = prb["problem_id"]
    assert prb["status"] == "OPEN"
    assert prb["service_id"] == "SVC_LIFECYCLE_TEST"

    # 2. Transition OPEN -> INVESTIGATING
    investigate_res = client.patch(
        f"/api/v1/problems/{prb_id}/status",
        json={"status": "INVESTIGATING"},
        headers=admin_headers
    )
    assert investigate_res.status_code == 200
    assert investigate_res.json()["status"] == "INVESTIGATING"

    # 3. Transition INVESTIGATING -> KNOWN_ERROR without workaround should FAIL (400)
    failed_ke = client.patch(
        f"/api/v1/problems/{prb_id}/status",
        json={"status": "KNOWN_ERROR"},
        headers=admin_headers
    )
    assert failed_ke.status_code == 400

    # 4. Add documented workaround & root cause
    update_inv = client.patch(
        f"/api/v1/problems/{prb_id}/investigation",
        json={
            "root_cause_category": "Database Lock Contention",
            "root_cause_text": "Shared row locks during batch settlement window.",
            "workaround": "Increase connection pool size to 50 and disable table-level locks.",
            "kedb_status": "DRAFT"
        },
        headers=admin_headers
    )
    assert update_inv.status_code == 200
    assert update_inv.json()["workaround"] is not None

    # 5. Now transition to KNOWN_ERROR succeeds
    ke_res = client.patch(
        f"/api/v1/problems/{prb_id}/status",
        json={"status": "KNOWN_ERROR"},
        headers=admin_headers
    )
    assert ke_res.status_code == 200
    assert ke_res.json()["status"] == "KNOWN_ERROR"

    # 6. Resolve Problem with KEDB publishing
    resolve_res = client.post(
        f"/api/v1/problems/{prb_id}/resolve",
        json={
            "resolution": "Applied hotfix HF-802: migrated to optimistic concurrency model.",
            "kedb_status": "PUBLISHED"
        },
        headers=admin_headers
    )
    assert resolve_res.status_code == 200
    resolved_data = resolve_res.json()
    assert resolved_data["status"] == "RESOLVED"
    assert resolved_data["kedb_status"] == "PUBLISHED"
    assert resolved_data["resolved_at"] is not None

    # 7. Check Detail Dossier & Audit Trail
    detail_res = client.get(f"/api/v1/problems/{prb_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["audit_trail"]) >= 4

def test_problem_rbac_boundaries():
    viewer_headers = _get_auth_headers("viewer")
    analyst_headers = _get_auth_headers("analyst")

    # Viewer cannot create problem
    viewer_create = client.post(
        "/api/v1/problems",
        json={
            "service_id": "SVC_LIFECYCLE_TEST",
            "title": "Unauthorized attempt",
            "priority": "P3"
        },
        headers=viewer_headers
    )
    assert viewer_create.status_code == 403

    # Analyst can create problem
    analyst_create = client.post(
        "/api/v1/problems",
        json={
            "service_id": "SVC_LIFECYCLE_TEST",
            "title": "Analyst problem investigation",
            "priority": "P3"
        },
        headers=analyst_headers
    )
    assert analyst_create.status_code == 201

# ============================================================================
# Change Governance & CAB Workflow Tests
# ============================================================================

def test_change_create_and_cab_workflow():
    analyst_headers = _get_auth_headers("analyst")
    viewer_headers = _get_auth_headers("viewer")
    admin_headers = _get_auth_headers("admin")

    # 1. Analyst submits Change Request
    chg_res = client.post(
        "/api/v1/changes",
        json={
            "service_id": "SVC_LIFECYCLE_TEST",
            "title": "Upgrade payment gateway cluster to v3.4",
            "description": "Includes zero-downtime rolling update for PCI-DSS compliance.",
            "change_type": "NORMAL",
            "risk_level": "HIGH",
            "implementation_plan": "1. Deploy canary node; 2. Run smoke tests; 3. Drain and upgrade remaining 3 nodes.",
            "rollback_plan": "Revert DNS pointer to blue cluster snapshot v3.3.",
            "auto_submit_cab": False
        },
        headers=analyst_headers
    )
    assert chg_res.status_code == 201
    chg = chg_res.json()
    chg_id = chg["change_id"]
    assert chg["status"] == "DRAFT"

    # 2. Submit to CAB
    cab_submit = client.post(f"/api/v1/changes/{chg_id}/cab-review", headers=analyst_headers)
    assert cab_submit.status_code == 200
    assert cab_submit.json()["cab_status"] == "PENDING"
    assert cab_submit.json()["status"] == "REQUESTED"

    # 3. Viewer or Analyst cannot approve CAB change (requires changes.approve permission)
    analyst_approve = client.post(
        f"/api/v1/changes/{chg_id}/approve",
        json={"decision": "APPROVED", "comments": "Unauthorized analyst approval"},
        headers=analyst_headers
    )
    assert analyst_approve.status_code == 403

    # 4. Admin approves CAB change
    admin_approve = client.post(
        f"/api/v1/changes/{chg_id}/approve",
        json={"decision": "APPROVED", "comments": "CAB reviewed and approved for Sunday 02:00 UTC maintenance window."},
        headers=admin_headers
    )
    assert admin_approve.status_code == 200
    assert admin_approve.json()["status"] == "APPROVED"
    assert admin_approve.json()["cab_status"] == "APPROVED"

    # 5. Start Deployment
    deploy_start = client.post(
        f"/api/v1/changes/{chg_id}/deploy",
        json={"action": "START"},
        headers=analyst_headers
    )
    assert deploy_start.status_code == 200
    assert deploy_start.json()["status"] == "IN_PROGRESS"
    assert deploy_start.json()["implementation_start"] is not None

    # 6. Complete Deployment
    deploy_done = client.post(
        f"/api/v1/changes/{chg_id}/deploy",
        json={"action": "COMPLETE"},
        headers=analyst_headers
    )
    assert deploy_done.status_code == 200
    assert deploy_done.json()["status"] == "COMPLETED"
    assert deploy_done.json()["successful"] is True

    # 7. Check Detail & Audit Trail
    detail = client.get(f"/api/v1/changes/{chg_id}", headers=admin_headers).json()
    assert len(detail["audit_trail"]) >= 4

def test_change_emergency_rollback():
    admin_headers = _get_auth_headers("admin")

    # Create change directly
    chg = client.post(
        "/api/v1/changes",
        json={
            "service_id": "SVC_LIFECYCLE_TEST",
            "title": "Emergency database patch",
            "change_type": "EMERGENCY",
            "risk_level": "HIGH"
        },
        headers=admin_headers
    ).json()
    chg_id = chg["change_id"]

    # Trigger emergency rollback
    rollback_res = client.post(
        f"/api/v1/changes/{chg_id}/rollback",
        json={
            "reason": "Elevated socket read timeouts detected post-patch on gateway.",
            "notes": "Triggered automated blue/green switch back to v3.3."
        },
        headers=admin_headers
    )
    assert rollback_res.status_code == 200
    res_data = rollback_res.json()
    assert res_data["status"] == "FAILED"
    assert res_data["rollback_required"] is True
    assert res_data["successful"] is False

# ============================================================================
# Incident Lifecycle & SLA Tests
# ============================================================================

def test_incident_lifecycle_and_sla():
    analyst_headers = _get_auth_headers("analyst")

    # 1. Create Incident
    inc_res = client.post(
        "/api/v1/incidents",
        json={
            "service_id": "SVC_LIFECYCLE_TEST",
            "title": "API response latency exceeding 2500ms on payment checkout",
            "priority": "P1",
            "urgency": "HIGH",
            "impact": "HIGH",
            "category": "Performance"
        },
        headers=analyst_headers
    )
    assert inc_res.status_code == 201
    inc = inc_res.json()
    inc_id = inc["incident_id"]
    assert inc["status"] == "NEW"

    # 2. Acknowledge / In Progress
    ack_res = client.patch(
        f"/api/v1/incidents/{inc_id}/status",
        json={"status": "IN_PROGRESS"},
        headers=analyst_headers
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["acknowledged_at"] is not None

    # 3. Resolve Incident
    resolve_res = client.post(
        f"/api/v1/incidents/{inc_id}/resolve",
        json={
            "resolution_code": "FIXED_PERMANENTLY",
            "resolution_notes": "Recycled unresponsive worker processes and refreshed Redis session cache."
        },
        headers=analyst_headers
    )
    assert resolve_res.status_code == 200
    resolved = resolve_res.json()
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolution_time_hours"] is not None

    # 4. Verify SLA Record creation and resolution
    detail = client.get(f"/api/v1/incidents/{inc_id}", headers=analyst_headers).json()
    assert len(detail["sla_records"]) == 1
    sla = detail["sla_records"][0]
    assert sla["target_hours"] == 4.0
    assert sla["status"] == "MET"
    assert len(detail["audit_trail"]) >= 3
