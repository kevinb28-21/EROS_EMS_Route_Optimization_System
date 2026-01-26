"""
Pytest configuration and fixtures.
"""

import pytest
import os

# Set test database URL before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_db():
    """Create a test database session."""
    from app.database import engine, Base, SessionLocal
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield SessionLocal()
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    with TestClient(app) as client:
        yield client
