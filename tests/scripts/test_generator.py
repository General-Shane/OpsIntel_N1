import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.core.database import Base
from backend.core.models import Incident, Problem, Change, SLARecord, Service
from scripts.generate_data import init_db, generate_data

# Use a test database
TEST_DB_URL = "sqlite:///./test_opsintel.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Patch the engine and session in the modules
    import backend.core.database as db_module
    import scripts.generate_data as gen_module
    
    original_engine = db_module.engine
    original_session = db_module.SessionLocal
    
    db_module.engine = test_engine
    db_module.SessionLocal = TestSessionLocal
    gen_module.engine = test_engine
    gen_module.SessionLocal = TestSessionLocal
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=test_engine)
    db_module.engine = original_engine
    db_module.SessionLocal = original_session
    gen_module.engine = original_engine
    gen_module.SessionLocal = original_session
    if os.path.exists("./test_opsintel.db"):
        try:
            os.remove("./test_opsintel.db")
        except PermissionError:
            pass

def test_deterministic_generation():
    # Run first time
    init_db()
    generate_data(42)
    
    db = TestSessionLocal()
    incidents_run1 = db.query(Incident).count()
    problems_run1 = db.query(Problem).count()
    changes_run1 = db.query(Change).count()
    slas_run1 = db.query(SLARecord).count()
    
    # Check that data exists
    assert incidents_run1 > 0
    assert problems_run1 > 0
    assert changes_run1 > 0
    assert slas_run1 > 0
    
    # Check specific spike data
    spike_incidents = db.query(Incident).filter(Incident.incident_id.like("INC80000%")).count()
    assert spike_incidents == 500
    
    # Run second time with same seed
    init_db()
    generate_data(42)
    
    incidents_run2 = db.query(Incident).count()
    problems_run2 = db.query(Problem).count()
    
    # Should be identical
    assert incidents_run1 == incidents_run2
    assert problems_run1 == problems_run2
    
    db.close()
