import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import settings

# Determine database dialect
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
is_postgres = settings.DATABASE_URL.startswith("postgresql") or settings.DATABASE_URL.startswith("postgres")

# Engine options per dialect
if is_sqlite:
    engine_kwargs = {
        "connect_args": {"check_same_thread": False, "timeout": 15}
    }
elif is_postgres:
    engine_kwargs = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
        "pool_pre_ping": True,
        "pool_recycle": 3600
    }
else:
    engine_kwargs = {}

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

def configure_sqlite_pragmas(target_engine):
    """
    Configures SQLite Write-Ahead Logging (WAL), foreign keys, and busy timeout
    to allow concurrent reads and writes without database lock errors.
    """
    @event.listens_for(target_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

if is_sqlite:
    configure_sqlite_pragmas(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency for yielding database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
