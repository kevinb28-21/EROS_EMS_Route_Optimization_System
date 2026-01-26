"""
Database configuration and session management.
Uses SQLAlchemy 2.0 async patterns.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


def get_engine():
    """Create database engine based on configuration."""
    settings = get_settings()
    
    # Handle SQLite for testing
    if settings.database_url.startswith("sqlite"):
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    
    # PostgreSQL for production
    return create_engine(settings.database_url)


# Create engine and session factory
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency that provides a database session.
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import models to register them with Base
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
