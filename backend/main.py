from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.core.logging import setup_logging
from backend.core.errors import setup_exception_handlers
from backend.api.v1.router import api_router
from backend.core.scheduler import scheduler
from backend.core.database import engine, Base, SessionLocal
from backend.core.security import bootstrap_security

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database schema & bootstrap RBAC
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        bootstrap_security(db)
    finally:
        db.close()

    scheduler.start()
    yield
    # Shutdown
    scheduler.stop()

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "HEALTHY"}
