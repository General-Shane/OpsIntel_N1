from fastapi import APIRouter, Depends
from backend.api.v1.endpoints.auth import get_admin_user
from backend.api.v1.endpoints import (
    health,
    ingestion,
    analytics,
    reports,
    ai,
    scheduler,
    notifications,
    admin,
    auth,
    websockets,
    integration,
    servicenow,
    problems,
    changes,
    incidents
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="/system/status", tags=["health"])
api_router.include_router(ingestion.router, prefix="/ingest", tags=["ingestion"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(integration.router, prefix="/integration", tags=["integration"])
api_router.include_router(servicenow.router, prefix="/integrations/servicenow", tags=["servicenow"])
api_router.include_router(servicenow.router, prefix="/integration/servicenow", tags=["servicenow"])
api_router.include_router(problems.router, prefix="/problems", tags=["problems"])
api_router.include_router(changes.router, prefix="/changes", tags=["changes"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"], dependencies=[Depends(get_admin_user)])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(websockets.router, prefix="/ws", tags=["websockets"])


