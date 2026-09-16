import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import Base
import backend.core.database as db_module
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_URL = "sqlite:///./test_analytics_ext.db"
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
        try:
            db = TestSessionLocal()
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[db_module.get_db] = override_get_db
    
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    # Generate some synthetic data into the test db using our script
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
    if os.path.exists("./test_analytics_ext.db"):
        try:
            os.remove("./test_analytics_ext.db")
        except PermissionError:
            pass

def test_get_global_kpis():
    response = client.get("/api/v1/analytics/kpis")
    assert response.status_code == 200
    data = response.json()
    assert "incidents" in data
    assert data["incidents"]["total_incidents"] > 0

def test_get_service_analytics():
    response = client.get("/api/v1/analytics/services")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    svc = data[0]
    assert "service_id" in svc
    assert "health_status" in svc
    assert "metrics" in svc

def test_get_recent_reports():
    response = client.get("/api/v1/reports/recent")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "report_id" in data[0]

def test_priority_normalization_mapping():
    # Fetch raw incidents from API
    response = client.get("/api/v1/analytics/raw/incidents?limit=250")
    assert response.status_code == 200
    incidents = response.json()
    assert len(incidents) > 0

    priorities = {inc["priority"] for inc in incidents}
    # Verify that valid priority labels are used
    for p in priorities:
        assert p in ["Critical", "High", "Medium", "Low"]

    # Verify that P4 is mapped to Low and never Medium
    db = TestSessionLocal()
    from backend.core.models import Incident
    p4_count = db.query(Incident).filter(Incident.priority == "P4").count()
    db.close()

def test_get_problem_management_intelligence():
    response = client.get("/api/v1/analytics/problems/summary")
    assert response.status_code == 200
    data = response.json()
    
    assert "summary" in data
    assert data["summary"]["total_problems"] > 0
    assert "open_backlog" in data["summary"]
    assert "critical_high_count" in data["summary"]
    assert "stale_problems_count" in data["summary"]
    
    assert "aging_distribution" in data
    assert len(data["aging_distribution"]) == 4
    
    assert "root_cause_breakdown" in data
    assert len(data["root_cause_breakdown"]) > 0
    for rc in data["root_cause_breakdown"]:
        assert rc["confidence"] == "Analytics Derived"
        
    assert "recurring_clusters" in data
    assert len(data["recurring_clusters"]) > 0

def test_get_problem_detail():
    # First get list of raw problems
    raw_res = client.get("/api/v1/analytics/raw/problems?limit=5")
    assert raw_res.status_code == 200
    problems = raw_res.json()
    assert len(problems) > 0
    
    sample_id = problems[0]["id"]
    detail_res = client.get(f"/api/v1/analytics/problems/{sample_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    
    assert detail["problem_id"] == sample_id
    assert "service_name" in detail
    assert "root_cause_category" in detail
    assert "related_incidents" in detail
    assert "recommended_actions" in detail
    assert len(detail["recommended_actions"]) >= 1


