"""Pytest configuration to ensure tests use an isolated test database."""

import os
import os.path
import pytest

# Point the app to the test DB as early as possible (on import),
# so any imports of src.database during collection use test DB.
os.environ["DW_DB_PATH"] = "test_database.db"
os.environ.setdefault("DW_FAST_TEST", "1")


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_test_database():

    # Remove any prior test DB
    if os.path.exists("test_database.db"):
        try:
            os.remove("test_database.db")
        except PermissionError:
            pass

    # Import after env var is set so engine binds to test DB
    from src.database import Base, engine, SessionLocal

    # Create all tables (fresh)
    Base.metadata.create_all(engine)

    yield

    # Teardown: close sessions and remove file
    try:
        SessionLocal.remove()  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        if os.path.exists("test_database.db"):
            os.remove("test_database.db")
    except PermissionError:
        pass
