"""Test-specific database configuration."""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from src.database import Base

# Test database setup
TEST_DATABASE_URL = "sqlite:///test_database.db"
test_engine = create_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = scoped_session(sessionmaker(bind=test_engine, autoflush=False, autocommit=False))

def get_test_db() -> Generator[Session, None, None]:
    """Dependency to get test database session."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_test_tables():
    """Create all database tables for testing."""
    Base.metadata.create_all(test_engine)

def drop_test_tables():
    """Drop all test database tables."""
    Base.metadata.drop_all(test_engine)

def reset_test_database():
    """Reset the test database to a clean state without deleting the file."""
    try:
        TestSessionLocal.remove()
    except Exception:
        pass
    # Drop and recreate tables to ensure a clean slate
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    print("🧪 Test database reset and ready")

def cleanup_test_database():
    """Clean up test database after tests (sessions only; file removal handled in conftest)."""
    try:
        TestSessionLocal.remove()
    except Exception:
        pass


