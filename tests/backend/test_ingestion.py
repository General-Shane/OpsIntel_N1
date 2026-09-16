import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.database import Base
from backend.core.models import Incident, Service

TEST_DB_URL = "sqlite:///./test_ingestion.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    import backend.core.database as db_module
    import backend.api.v1.endpoints.ingestion as ingest_api
    
    original_engine = db_module.engine
    original_session = db_module.SessionLocal
    
    db_module.engine = test_engine
    db_module.SessionLocal = TestSessionLocal
    
    # Overwrite the get_db dependency for the test client
    def override_get_db():
        try:
            db = TestSessionLocal()
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[db_module.get_db] = override_get_db
    
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    # Create test services
    db = TestSessionLocal()
    db.add(Service(service_id="SVC_PAYMENT", service_name="Payments", criticality="CRITICAL"))
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=test_engine)
    db_module.engine = original_engine
    db_module.SessionLocal = original_session
    app.dependency_overrides.clear()
    
    if os.path.exists("./test_ingestion.db"):
        try:
            os.remove("./test_ingestion.db")
        except PermissionError:
            pass

def test_upload_csv():
    csv_content = """incident_id,service_id,priority,status,created_at,resolved_at,resolution_time_hours
INC_TEST_1,SVC_PAYMENT,P1,OPEN,2026-08-01T10:00:00Z,,
INC_TEST_2,SVC_PAYMENT,P2,RESOLVED,2026-08-01T11:00:00Z,2026-08-01T13:00:00Z,2.0
"""
    
    response = client.post(
        "/api/v1/ingest/upload",
        files={"file": ("test.csv", csv_content, "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["result"]["processed"] == 2
    assert data["result"]["success"] == 2
    
    # Check DB
    db = TestSessionLocal()
    inc1 = db.query(Incident).filter(Incident.incident_id == "INC_TEST_1").first()
    assert inc1 is not None
    assert inc1.status == "OPEN"
    
    inc2 = db.query(Incident).filter(Incident.incident_id == "INC_TEST_2").first()
    assert inc2 is not None
    assert inc2.resolution_time_hours == 2.0
    
    # Test upsert (upload again with updated data)
    csv_update = """incident_id,service_id,priority,status,created_at,resolved_at,resolution_time_hours
INC_TEST_1,SVC_PAYMENT,P1,RESOLVED,2026-08-01T10:00:00Z,2026-08-01T14:00:00Z,4.0
"""
    response = client.post(
        "/api/v1/ingest/upload",
        files={"file": ("update.csv", csv_update, "text/csv")}
    )
    assert response.status_code == 200
    
    # Check DB to ensure it was updated not duplicated
    db.expire_all()
    inc1_updated = db.query(Incident).filter(Incident.incident_id == "INC_TEST_1").first()
    assert inc1_updated.status == "RESOLVED"
    assert inc1_updated.resolution_time_hours == 4.0
    
    total_incidents = db.query(Incident).count()
    assert total_incidents == 2 # Did not create a 3rd record
    db.close()
