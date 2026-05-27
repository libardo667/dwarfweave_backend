"""Database configuration and setup.

Respects DW_DB_PATH (absolute or relative sqlite file path). During pytest runs,
defaults to test_database.db unless DW_DB_PATH is set.
"""

from typing import Generator
from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, Session
import os

# Database Setup
db_file = os.environ.get("DW_DB_PATH")
if not db_file:
    # If running under pytest, prefer the test DB by default
    db_file = 'test_database.db' if os.environ.get('PYTEST_CURRENT_TEST') else 'dwarfweave.db'

engine = create_engine(f'sqlite:///{db_file}', future=True, connect_args={"check_same_thread": False})
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
    _ensure_origin_column()


def _ensure_origin_column():
    """Additively add storylets.origin to pre-existing DBs (item 02).

    Fresh DBs get the column from create_all; this backfills older DB files.
    Idempotent: a second run hits 'duplicate column' and is ignored.
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE storylets ADD COLUMN origin VARCHAR(16) NOT NULL DEFAULT 'assumed'"
            ))
    except Exception:
        pass  # column already exists
