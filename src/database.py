"""Database configuration and setup."""

from typing import Generator
from sqlalchemy import create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, Session

# Database Setup
engine = create_engine('sqlite:///worldweaver.db', future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(engine)
