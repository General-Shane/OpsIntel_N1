import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import Base
import backend.core.database as db_module
from backend.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_URL = "sqlite:///./test_integration_beacon.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": settings.BEACON_API_KEY}

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    original_engine = db_module.engine
    original_session = db_module.SessionLocal
    
    db_module.engine = test_engine
    db_module.SessionLocal = TestSessionLocal
    
    def override_get_db():
        try:
            db = TestSessionLocal()
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[db_module.get_db] = override_get_db
    
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    import scripts.generate_data as gen_module
    gen_original_engine = gen_module.engine
    gen_original_session = gen_module.SessionLocal
    gen_module.engine = test_engine
    gen_module.SessionLocal = TestSessionLocal
    
    gen_module.generate_data(seed=123)
    
    yield
    
    Base.metadata.drop_all(bind=test_engine)
    db_module.engine = original_engine
    db_module.SessionLocal = original_session
    gen_module.engine = gen_original_engine
    gen_module.SessionLocal = gen_original_session
    app.dependency_overrides.clear()
    
    import os
    if os.path.exists("./test_integration_beacon.db"):
        try:
            os.remove("./test_integration_beacon.db")
        except PermissionError:
            pass

def test_beacon_unauthorized_access_rejected():
    """Verify that requests without API key or with invalid API key are rejected with 401."""
    res_no_key = client.get("/api/v1/integration/beacon/v1/health-context")
    assert res_no_key.status_code == 401
    
    res_bad_key = client.get("/api/v1/integration/beacon/v1/health-context", headers={"X-API-Key": "invalid-key"})
    assert res_bad_key.status_code == 401

def test_beacon_health_context():
    res = client.get("/api/v1/integration/beacon/v1/health-context", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["contract"] == "opsintel-beacon-integration"
    assert data["schema_version"] == "1.0"
    assert "health" in data
    assert "incidents_summary" in data
    assert "sla_summary" in data
    assert "problem_summary" in data

def test_beacon_active_incidents():
    res = client.get("/api/v1/integration/beacon/v1/active-incidents?limit=20", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["contract"] == "opsintel-beacon-integration"
    assert "incidents" in data
    assert len(data["incidents"]) >= 0

def test_beacon_incident_context():
    raw_res = client.get("/api/v1/analytics/raw/incidents?limit=5")
    assert raw_res.status_code == 200
    incidents = raw_res.json()
    assert len(incidents) > 0
    sample_id = incidents[0]["id"]
    
    res = client.get(f"/api/v1/integration/beacon/v1/incident-context/{sample_id}", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["incident_id"] == sample_id
    assert "service" in data
    assert "change_correlation" in data
    assert "diagnostic_vectors" in data

def test_beacon_problem_intelligence():
    res = client.get("/api/v1/integration/beacon/v1/problem-intelligence", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "aging_distribution" in data
    assert "root_cause_hypotheses" in data
    assert "recurring_incident_clusters" in data

def test_beacon_service_health():
    res = client.get("/api/v1/integration/beacon/v1/service-health", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["total_services"] == 5
    assert len(data["services"]) == 5

def test_beacon_executive_brief():
    res = client.get("/api/v1/integration/beacon/v1/executive-brief", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "executive_summary_narrative" in data
    assert "key_risk_factors" in data
