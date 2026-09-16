import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    AuditEvent
)
from backend.core.security import bootstrap_security, hash_password
from backend.config import settings
import scripts.generate_data as gen_module

TEST_DB_URL = "sqlite:///./test_stage7_itsm.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_stage7_test_env():
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

    gen_original_engine = gen_module.engine
    gen_original_session = gen_module.SessionLocal
    gen_module.engine = test_engine
    gen_module.SessionLocal = TestSessionLocal

    gen_module.generate_data(seed=777)

    yield

    Base.metadata.drop_all(bind=test_engine)
    db_module.engine = original_engine
    db_module.SessionLocal = original_session
    gen_module.engine = gen_original_engine
    gen_module.SessionLocal = gen_original_session
    app.dependency_overrides.clear()

    if os.path.exists("./test_stage7_itsm.db"):
        try:
            os.remove("./test_stage7_itsm.db")
        except PermissionError:
            pass


# ============================================================================
# 1. Model Structure & Field Verification Tests
# ============================================================================

def test_service_enterprise_model():
    db = TestSessionLocal()
    svc = db.query(Service).filter(Service.service_id == "SVC_PAYMENT").first()
    assert svc is not None
    assert svc.service_name == "Payment Gateway"
    assert svc.criticality == "CRITICAL"
    assert svc.description is not None
    assert svc.support_group == "Tier-3 Payments SRE"
    assert svc.status == "OPERATIONAL"
    assert len(svc.incidents) > 0
    assert len(svc.problems) > 0
    assert len(svc.changes) > 0
    assert len(svc.sla_records) > 0
    db.close()


def test_problem_enterprise_model_and_lifecycle():
    db = TestSessionLocal()
    prb = db.query(Problem).first()
    assert prb is not None
    assert prb.problem_id.startswith("PRB")
    assert prb.status in ["OPEN", "INVESTIGATING", "KNOWN_ERROR", "RESOLVED", "CLOSED"]
    assert prb.root_cause_category is not None
    assert prb.service is not None
    assert prb.created_at is not None
    db.close()


def test_change_enterprise_model_and_governance():
    db = TestSessionLocal()
    chg = db.query(Change).first()
    assert chg is not None
    assert chg.change_id.startswith("CHG")
    assert chg.change_type in ["NORMAL", "STANDARD", "EMERGENCY"]
    assert chg.risk_level in ["LOW", "MEDIUM", "HIGH"]
    assert chg.status in ["COMPLETED", "FAILED", "REQUESTED", "APPROVED", "DRAFT"]
    assert chg.service is not None
    assert chg.created_at is not None
    db.close()


def test_incident_enterprise_model():
    db = TestSessionLocal()
    inc = db.query(Incident).first()
    assert inc is not None
    assert inc.incident_id.startswith("INC")
    assert inc.priority in ["P1", "P2", "P3", "P4"]
    assert inc.status in ["NEW", "IN_PROGRESS", "RESOLVED", "CLOSED", "OPEN"]
    assert inc.service is not None
    assert inc.created_at is not None
    db.close()


def test_sla_enterprise_model():
    db = TestSessionLocal()
    sla = db.query(SLARecord).first()
    assert sla is not None
    assert sla.sla_id.startswith("SLA_")
    assert sla.target_hours > 0
    assert sla.actual_hours >= 0
    assert isinstance(sla.breached, bool)
    assert sla.service is not None
    db.close()


def test_audit_event_creation_and_query():
    db = TestSessionLocal()
    admin_user = db.query(User).filter(User.username == "admin").first()
    event = AuditEvent(
        actor_user_id=admin_user.id if admin_user else None,
        actor_username="admin",
        entity_type="Incident",
        entity_id="INC10000",
        action="ESCALATE",
        old_state_json='{"priority": "P2"}',
        new_state_json='{"priority": "P1"}',
        correlation_id="AUDIT_TEST_001"
    )
    db.add(event)
    db.commit()

    saved = db.query(AuditEvent).filter(AuditEvent.correlation_id == "AUDIT_TEST_001").first()
    assert saved is not None
    assert saved.entity_type == "Incident"
    assert saved.action == "ESCALATE"
    assert saved.actor_username == "admin"
    db.close()


# ============================================================================
# 2. Relational Links & Cross-Entity Navigations
# ============================================================================

def test_incident_problem_change_relationships():
    db = TestSessionLocal()
    # Find incident linked to problem and change
    linked_inc = db.query(Incident).filter(Incident.problem_id.isnot(None)).first()
    assert linked_inc is not None
    assert linked_inc.problem is not None
    assert linked_inc.problem.problem_id == linked_inc.problem_id

    # Find change linked to service
    chg = db.query(Change).filter(Change.service_id == "SVC_PAYMENT").first()
    assert chg is not None
    assert chg.service.service_id == "SVC_PAYMENT"

    # User relationships
    admin = db.query(User).filter(User.username == "admin").first()
    assert admin is not None
    assert hasattr(admin, "owned_services")
    assert hasattr(admin, "assigned_incidents")
    assert hasattr(admin, "owned_problems")
    db.close()


# ============================================================================
# 3. Analytics & Beacon API Compatibility Tests
# ============================================================================

def test_analytics_raw_incidents_compatibility():
    res = client.get("/api/v1/analytics/raw/incidents?limit=25")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 25
    item = data[0]
    assert "id" in item
    assert "title" in item
    assert "priority" in item
    assert "status" in item
    assert "service" in item
    assert "created" in item


def test_analytics_raw_problems_compatibility():
    res = client.get("/api/v1/analytics/raw/problems?limit=25")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 25
    item = data[0]
    assert "id" in item
    assert "title" in item
    assert "status" in item
    assert "priority" in item
    assert "service" in item
    assert "root_cause_category" in item
    assert "age_days" in item
    assert "created" in item


def test_analytics_raw_changes_compatibility():
    res = client.get("/api/v1/analytics/raw/changes?limit=25")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 25
    item = data[0]
    assert "id" in item
    assert "title" in item
    assert "type" in item
    assert "status" in item
    assert "risk" in item
    assert "service" in item
    assert "created" in item


def test_problem_detail_endpoint_compatibility():
    raw_res = client.get("/api/v1/analytics/raw/problems?limit=5")
    assert raw_res.status_code == 200
    prbs = raw_res.json()
    sample_prb_id = prbs[0]["id"]

    res = client.get(f"/api/v1/analytics/problems/{sample_prb_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["problem_id"] == sample_prb_id
    assert "service_name" in data
    assert "root_cause_category" in data
    assert "related_incidents" in data
    assert "recommended_actions" in data


def test_beacon_integration_contract_preservation():
    headers = {"X-API-Key": settings.BEACON_API_KEY}
    res = client.get("/api/v1/integration/beacon/v1/health-context", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["contract"] == "opsintel-beacon-integration"
    assert data["schema_version"] == "1.0"
    assert "health" in data
    assert "incidents_summary" in data
    assert "sla_summary" in data
    assert "problem_summary" in data
    assert "change_summary" in data
