import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import Base, engine
from backend.config import settings
import scripts.generate_data as gen_data

logger = structlog.get_logger(__name__)

def run_e2e():
    logger.info("e2e_verification_started")
    
    # 1. Reset Database and Generate Data
    logger.info("e2e_database_reset")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    gen_data.generate_data(seed=999)
    
    # 2. Start Test Client (triggers lifespan, including scheduler & RBAC bootstrap)
    logger.info("e2e_testing_endpoints")
    with TestClient(app) as client:
        # Check Health
        res = client.get("/api/v1/system/status")
        assert res.status_code == 200
        logger.info("e2e_health_ok")
        
        # Check Authentication (Database-backed Admin login)
        login_res = client.post("/api/v1/auth/login", data={"username": "admin", "password": settings.OPSINTEL_BOOTSTRAP_ADMIN_PASSWORD})
        assert login_res.status_code == 200
        auth_data = login_res.json()
        assert "access_token" in auth_data
        assert auth_data["role"] == "ADMIN"
        token = auth_data["access_token"]
        admin_headers = {"Authorization": f"Bearer {token}"}
        logger.info("e2e_database_auth_ok", user=auth_data["username"], role=auth_data["role"])
        
        # Check /me profile
        me_res = client.get("/api/v1/auth/me", headers=admin_headers)
        assert me_res.status_code == 200
        assert me_res.json()["username"] == "admin"
        logger.info("e2e_profile_ok")
        
        # Check Admin User Management
        users_res = client.get("/api/v1/admin/users", headers=admin_headers)
        assert users_res.status_code == 200
        assert len(users_res.json()) >= 3
        logger.info("e2e_admin_users_ok", user_count=len(users_res.json()))
        
        # Check Beacon Integration Security
        beacon_unauth = client.get("/api/v1/integration/beacon/v1/health-context")
        assert beacon_unauth.status_code == 401
        
        beacon_auth = client.get("/api/v1/integration/beacon/v1/health-context", headers={"X-API-Key": settings.BEACON_API_KEY})
        assert beacon_auth.status_code == 200
        assert beacon_auth.json()["contract"] == "opsintel-beacon-integration"
        logger.info("e2e_beacon_auth_ok")
        
        # Check KPIs
        res = client.get("/api/v1/analytics/kpis")
        assert res.status_code == 200
        data = res.json()
        assert "incidents" in data
        logger.info("e2e_kpis_ok", total_incidents=data["incidents"]["total_incidents"])
        
        # Check Services
        res = client.get("/api/v1/analytics/services")
        assert res.status_code == 200
        svc_data = res.json()
        assert len(svc_data) > 0
        logger.info("e2e_services_ok", services_count=len(svc_data))
        
        # Check Reports
        res = client.get("/api/v1/reports/recent")
        assert res.status_code == 200
        reports = res.json()
        assert len(reports) > 0
        logger.info("e2e_reports_ok", reports_count=len(reports))
        
        # Stage 8: Check ServiceNow Integration Status
        sn_res = client.get("/api/v1/integrations/servicenow/status", headers=admin_headers)
        assert sn_res.status_code == 200
        sn_data = sn_res.json()
        assert "connector" in sn_data
        logger.info("e2e_servicenow_status_ok", connector=sn_data["connector"])

        # Stage 9: Check Production Scheduler Status
        sched_res = client.get("/api/v1/scheduler/status", headers=admin_headers)
        assert sched_res.status_code == 200
        sched_data = sched_res.json()
        assert sched_data["total_jobs"] >= 4
        logger.info("e2e_scheduler_status_ok", total_jobs=sched_data["total_jobs"], worker=sched_data["worker_id"])

        # Stage 9: Check Scheduled Jobs Registry
        jobs_res = client.get("/api/v1/scheduler/jobs", headers=admin_headers)
        assert jobs_res.status_code == 200
        jobs_list = jobs_res.json()
        assert len(jobs_list) >= 4
        test_job_id = jobs_list[0]["id"]
        logger.info("e2e_scheduled_jobs_registry_ok", jobs_count=len(jobs_list))

        # Stage 9: Check Ad-Hoc Execution Trigger
        exec_res = client.post(f"/api/v1/scheduler/jobs/{test_job_id}/execute", headers=admin_headers)
        assert exec_res.status_code == 200
        assert exec_res.json()["status"] == "TRIGGERED"
        logger.info("e2e_job_execution_trigger_ok", run_id=exec_res.json()["run_id"])

        # Stage 9: Check Execution Log
        runs_res = client.get("/api/v1/scheduler/executions", headers=admin_headers)
        assert runs_res.status_code == 200
        assert len(runs_res.json()) >= 1
        logger.info("e2e_execution_history_ok", executions_count=len(runs_res.json()))

        # Stage 9: Check SMTP Status (Non-sensitive masking)
        smtp_res = client.get("/api/v1/notifications/email/status", headers=admin_headers)
        assert smtp_res.status_code == 200
        assert "host_masked" in smtp_res.json()
        logger.info("e2e_smtp_status_ok", is_configured=smtp_res.json()["is_configured"])

        # Stage 9: Check SMTP Test Email Dispatch
        test_email_res = client.post("/api/v1/notifications/email/test", headers=admin_headers, json={
            "recipient": "lead-sre@capgemini.com",
            "subject": "E2E Automated Verification Test",
            "message": "OPSINTEL Stage 9 E2E Verification Dispatch."
        })
        assert test_email_res.status_code == 200
        logger.info("e2e_smtp_test_dispatch_ok")

        # Stage 9: Check Notification Delivery Audit Log
        deliveries_res = client.get("/api/v1/notifications/deliveries", headers=admin_headers)
        assert deliveries_res.status_code == 200
        assert len(deliveries_res.json()) >= 1
        logger.info("e2e_delivery_audit_log_ok", deliveries_count=len(deliveries_res.json()))

    logger.info("e2e_verification_complete", status="SUCCESS")
    print("E2E_OK")

if __name__ == "__main__":
    try:
        run_e2e()
    except Exception as e:
        logger.error("e2e_verification_failed", error=str(e))
        sys.exit(1)
