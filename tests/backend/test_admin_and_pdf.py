import os
import sys
import shutil
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import app
from backend.core.database import Base
import backend.core.database as db_module
from backend.api.v1.endpoints.auth import get_admin_user, get_current_user
from backend.config import settings

TEST_DB_URL = "sqlite:///./test_admin_pdf.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_env():
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
    app.dependency_overrides[get_admin_user] = lambda: {"username": "admin", "role": "admin"}
    app.dependency_overrides[get_current_user] = lambda: {"username": "admin", "role": "admin"}

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    import scripts.generate_data as gen_module
    gen_original_engine = gen_module.engine
    gen_original_session = gen_module.SessionLocal
    gen_module.engine = test_engine
    gen_module.SessionLocal = TestSessionLocal
    gen_module.generate_data(seed=42)

    yield

    Base.metadata.drop_all(bind=test_engine)
    db_module.engine = original_engine
    db_module.SessionLocal = original_session
    gen_module.engine = gen_original_engine
    gen_module.SessionLocal = gen_original_session
    app.dependency_overrides.clear()

    if os.path.exists("./test_admin_pdf.db"):
        try:
            os.remove("./test_admin_pdf.db")
        except PermissionError:
            pass

def test_pdf_download_endpoint():
    # 1. Trigger report generation
    gen_res = client.post("/api/v1/reports/generate?period=daily")
    assert gen_res.status_code == 200
    report_id = gen_res.json()["report_id"]

    # 2. Test PDF download endpoint
    pdf_res = client.get(f"/api/v1/reports/{report_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 0

def test_admin_purge_reports():
    res = client.post("/api/v1/admin/purge-reports")
    assert res.status_code == 200
    assert "purged_count" in res.json()

def test_admin_clear_scheduler_history():
    res = client.post("/api/v1/admin/clear-scheduler-history")
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"

def test_admin_reseed_and_remove_all_data():
    # Test re-seed data (non-blocking)
    reseed_res = client.post("/api/v1/admin/reseed-data")
    assert reseed_res.status_code == 200
    data = reseed_res.json()
    assert data["status"] in ["IN_PROGRESS", "SUCCESS"]

    # Test reseed status endpoint
    status_res = client.get("/api/v1/admin/reseed-status")
    assert status_res.status_code == 200
    assert "status" in status_res.json()

    # Test remove all data
    remove_res = client.post("/api/v1/admin/remove-all-data")
    assert remove_res.status_code == 200
    assert remove_res.json()["status"] == "SUCCESS"

