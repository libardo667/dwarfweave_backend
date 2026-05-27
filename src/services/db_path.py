"""Shared SQLite path resolution for services that open the DB file directly.

Precedence: an explicit non-default argument wins, then `DW_DB_PATH`, then the
pytest test DB, then the default. Centralized so there is one place to change the
default name (see major 03, which renames `worldweaver.db` -> `dwarfweave.db`).
"""

import os


def resolve_db_path(db_path: str = 'dwarfweave.db') -> str:
    """Resolve which SQLite file a direct-DB service should open."""
    if db_path and db_path != 'dwarfweave.db':
        return db_path
    env_db = os.getenv('DW_DB_PATH')
    if env_db:
        return env_db
    return 'test_database.db' if os.getenv('PYTEST_CURRENT_TEST') else 'dwarfweave.db'
