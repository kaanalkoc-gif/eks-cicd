"""
Database connection and session management.
Uses SQLite by default for local dev; Docker Compose uses PostgreSQL.
Set DATABASE_URL to switch backends (same models and Alembic migrations).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that yields a DB session; close after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
