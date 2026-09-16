import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(env_path):
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)
    except ImportError:
        pass

class Settings(BaseSettings):
    PROJECT_NAME: str = "OPSINTEL Enterprise IT Operations Intelligence"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./opsintel.db")
    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    GEMINI_API_KEY: Optional[str] = None
    SLACK_WEBHOOK_URL: Optional[str] = None
    TEAMS_WORKFLOW_HOOK_URL: Optional[str] = None
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Auth & Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "b304f58c73024840af7dd9f5188bfb5346067755b76022e38c9c7f66a93b45a9")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # Bootstrap User Defaults
    OPSINTEL_BOOTSTRAP_ADMIN_USERNAME: str = os.getenv("OPSINTEL_BOOTSTRAP_ADMIN_USERNAME", "admin")
    OPSINTEL_BOOTSTRAP_ADMIN_PASSWORD: str = os.getenv("OPSINTEL_BOOTSTRAP_ADMIN_PASSWORD", "Admin@123")
    OPSINTEL_BOOTSTRAP_VIEWER_USERNAME: str = os.getenv("OPSINTEL_BOOTSTRAP_VIEWER_USERNAME", "viewer")
    OPSINTEL_BOOTSTRAP_VIEWER_PASSWORD: str = os.getenv("OPSINTEL_BOOTSTRAP_VIEWER_PASSWORD", "Viewer@123")
    OPSINTEL_BOOTSTRAP_ANALYST_USERNAME: str = os.getenv("OPSINTEL_BOOTSTRAP_ANALYST_USERNAME", "analyst")
    OPSINTEL_BOOTSTRAP_ANALYST_PASSWORD: str = os.getenv("OPSINTEL_BOOTSTRAP_ANALYST_PASSWORD", "Analyst@123")
    
    # Beacon Agent Integration Security
    BEACON_API_KEY: str = os.getenv("BEACON_API_KEY", "opsintel-beacon-dev-key-2026")
    
    # ServiceNow Integration Settings
    SERVICE_NOW_INSTANCE_URL: Optional[str] = os.getenv("SERVICE_NOW_INSTANCE_URL", None)
    SERVICE_NOW_CLIENT_ID: Optional[str] = os.getenv("SERVICE_NOW_CLIENT_ID", None)
    SERVICE_NOW_CLIENT_SECRET: Optional[str] = os.getenv("SERVICE_NOW_CLIENT_SECRET", None)
    SERVICE_NOW_USERNAME: Optional[str] = os.getenv("SERVICE_NOW_USERNAME", None)
    SERVICE_NOW_PASSWORD: Optional[str] = os.getenv("SERVICE_NOW_PASSWORD", None)
    SERVICE_NOW_TOKEN: Optional[str] = os.getenv("SERVICE_NOW_TOKEN", None)
    SERVICE_NOW_AUTH_MODE: str = os.getenv("SERVICE_NOW_AUTH_MODE", "basic") # "basic" | "oauth2" | "token"
    SERVICE_NOW_WEBHOOK_SECRET: Optional[str] = os.getenv("SERVICE_NOW_WEBHOOK_SECRET", "opsintel-sn-webhook-secret-2026")
    SERVICE_NOW_TIMEOUT_SECONDS: float = float(os.getenv("SERVICE_NOW_TIMEOUT_SECONDS", "30.0"))
    SERVICE_NOW_MAX_RETRIES: int = int(os.getenv("SERVICE_NOW_MAX_RETRIES", "3"))
    SERVICE_NOW_BACKOFF_BASE: float = float(os.getenv("SERVICE_NOW_BACKOFF_BASE", "1.5"))
    SERVICE_NOW_RATE_LIMIT_RPS: float = float(os.getenv("SERVICE_NOW_RATE_LIMIT_RPS", "10.0"))
    SERVICE_NOW_CONFLICT_POLICY: str = os.getenv("SERVICE_NOW_CONFLICT_POLICY", "SERVICENOW_WINS") # SERVICENOW_WINS | OPSINTEL_WINS | LAST_WRITE_WINS | MANUAL_REVIEW
    SERVICE_NOW_PAGE_SIZE: int = int(os.getenv("SERVICE_NOW_PAGE_SIZE", "100"))
    SERVICE_NOW_MAX_RECORDS_PER_SYNC: int = int(os.getenv("SERVICE_NOW_MAX_RECORDS_PER_SYNC", "5000"))

    # Stage 9: Production Scheduler & Real SMTP/TLS Settings
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", None)
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME", None)
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", None)
    SMTP_FROM: str = os.getenv("SMTP_FROM", "opsintel-alerts@capgemini.com")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "OPSINTEL Operations Center")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "false").lower() in ("true", "1", "yes")
    SMTP_TIMEOUT_SECONDS: float = float(os.getenv("SMTP_TIMEOUT_SECONDS", "15.0"))
    SMTP_MOCK_MODE: bool = os.getenv("SMTP_MOCK_MODE", "false").lower() in ("true", "1", "yes")
    
    SCHEDULER_POLL_INTERVAL_SECONDS: float = float(os.getenv("SCHEDULER_POLL_INTERVAL_SECONDS", "5.0"))
    SCHEDULER_LEASE_DURATION_SECONDS: int = int(os.getenv("SCHEDULER_LEASE_DURATION_SECONDS", "300"))
    SCHEDULER_WORKER_ID: str = os.getenv("SCHEDULER_WORKER_ID", f"worker-{os.getpid()}")
    SCHEDULER_AUTOSTART: bool = os.getenv("SCHEDULER_AUTOSTART", "true").lower() in ("true", "1", "yes")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
