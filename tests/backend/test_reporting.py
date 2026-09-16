import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.database import Base
from backend.services.reporting_service import ReportingService
from backend.config import settings
import shutil

TEST_DB_URL = "sqlite:///./test_reporting.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module", autouse=True)
def setup_test_env():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    # Generate some synthetic data
    import scripts.generate_data as gen_module
    gen_original_engine = gen_module.engine
    gen_original_session = gen_module.SessionLocal
    gen_module.engine = test_engine
    gen_module.SessionLocal = TestSessionLocal
    gen_module.generate_data(seed=123)
    
    # Ensure test reports dir is clean
    reports_dir = os.path.join(settings.PROJECT_ROOT, "reports")
    if os.path.exists(reports_dir):
        shutil.rmtree(reports_dir)
        
    yield
    
    Base.metadata.drop_all(bind=test_engine)
    gen_module.engine = gen_original_engine
    gen_module.SessionLocal = gen_original_session
    if os.path.exists("./test_reporting.db"):
        try:
            os.remove("./test_reporting.db")
        except PermissionError:
            pass
    if os.path.exists(reports_dir):
        try:
            shutil.rmtree(reports_dir)
        except PermissionError:
            pass

def test_generate_report():
    db = TestSessionLocal()
    service = ReportingService(db)
    
    filepath = service.generate_report()
    
    assert os.path.exists(filepath)
    assert filepath.endswith(".md")
    assert "ops_report_" in filepath
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "# OPSINTEL Daily" in content
    assert "Operational Intelligence Report" in content
    assert ("Operational Summary" in content or "Executive Summary" in content)
    assert ("Recommended Corrective Actions" in content or "Remediation Roadmap" in content)
    assert ("Service Health" in content or "Service Fleet Telemetry" in content)
    
    db.close()

