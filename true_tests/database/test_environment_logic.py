"""Tests for database environment variable logic."""

import pytest
import os
from unittest.mock import patch
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestDatabaseEnvironmentLogic:
    """Test suite for database environment variable logic (Task: database-005)."""
    
    def setup_method(self):
        """Clear any existing database module imports before each test."""
        # Clear the module from sys.modules to force re-import with new env vars
        modules_to_clear = []
        for module_name in sys.modules:
            if 'src.database' in module_name or module_name == 'src.database':
                modules_to_clear.append(module_name)
        
        for module_name in modules_to_clear:
            del sys.modules[module_name]
    
    @patch.dict(os.environ, {"DW_DB_PATH": "custom_database.db"}, clear=False)
    def test_custom_db_path_environment_variable(self):
        """Test that DW_DB_PATH environment variable is respected."""
        # Import database module with mocked environment
        from src.database import db_file, engine
        
        assert db_file == "custom_database.db"
        assert "custom_database.db" in str(engine.url)
    
    @patch.dict(os.environ, {"DW_DB_PATH": "/absolute/path/to/database.db"}, clear=False)
    def test_absolute_db_path_environment_variable(self):
        """Test that absolute DW_DB_PATH is handled correctly."""
        from src.database import db_file, engine
        
        assert db_file == "/absolute/path/to/database.db"
        assert "/absolute/path/to/database.db" in str(engine.url)
    
    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_something"}, clear=False)
    def test_pytest_environment_uses_test_database(self):
        """Test that pytest environment defaults to test_database.db."""
        # Ensure DW_DB_PATH is not set
        if "DW_DB_PATH" in os.environ:
            del os.environ["DW_DB_PATH"]
        
        from src.database import db_file, engine
        
        assert db_file == "test_database.db"
        assert "test_database.db" in str(engine.url)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_production_environment_uses_worldweaver_db(self):
        """Test that production environment defaults to worldweaver.db."""
        # Clear both DW_DB_PATH and PYTEST_CURRENT_TEST
        env_copy = os.environ.copy()
        env_copy.pop("DW_DB_PATH", None)
        env_copy.pop("PYTEST_CURRENT_TEST", None)
        
        with patch.dict(os.environ, env_copy, clear=True):
            from src.database import db_file, engine
            
            assert db_file == "worldweaver.db"
            assert "worldweaver.db" in str(engine.url)
    
    @patch.dict(os.environ, {"DW_DB_PATH": "priority_test.db", "PYTEST_CURRENT_TEST": "test_something"}, clear=False)
    def test_dw_db_path_takes_priority_over_pytest(self):
        """Test that DW_DB_PATH takes priority over PYTEST_CURRENT_TEST."""
        from src.database import db_file, engine
        
        assert db_file == "priority_test.db"
        assert "priority_test.db" in str(engine.url)
    
    @patch.dict(os.environ, {"DW_DB_PATH": ""}, clear=False)
    def test_empty_dw_db_path_falls_back_to_defaults(self):
        """Test that empty DW_DB_PATH falls back to default logic."""
        # Set empty DW_DB_PATH and no PYTEST_CURRENT_TEST
        env_copy = os.environ.copy()
        env_copy["DW_DB_PATH"] = ""
        env_copy.pop("PYTEST_CURRENT_TEST", None)
        
        with patch.dict(os.environ, env_copy, clear=True):
            from src.database import db_file, engine
            
            assert db_file == "worldweaver.db"
            assert "worldweaver.db" in str(engine.url)
    
    def test_database_engine_configuration(self):
        """Test that database engine is configured correctly regardless of filename."""
        from src.database import engine
        
        # Verify SQLite URL format
        assert str(engine.url).startswith("sqlite:///")
        
        # Verify engine configuration - connect_args is passed during creation
        # We can verify the engine was created properly by checking it can connect
        try:
            with engine.connect() as conn:
                assert conn is not None
        except Exception as e:
            pytest.fail(f"Engine configuration failed: {e}")
    
    def test_session_local_configuration(self):
        """Test that SessionLocal is configured correctly."""
        from src.database import SessionLocal
        
        # SessionLocal is a scoped_session, so we need to check the underlying sessionmaker
        # Get the underlying sessionmaker from the scoped session
        session_factory = SessionLocal.session_factory
        
        # Verify session configuration
        assert session_factory.kw.get("autoflush") is False
        assert session_factory.kw.get("autocommit") is False
    
    def test_get_db_generator_function(self):
        """Test that get_db function works as expected."""
        from src.database import get_db
        
        # Test that get_db returns a generator
        db_gen = get_db()
        assert hasattr(db_gen, '__next__')
        
        # Test that we can get a session
        try:
            session = next(db_gen)
            assert session is not None
            
            # Test that the session is a SQLAlchemy Session
            from sqlalchemy.orm import Session
            assert isinstance(session, Session)
            
            # Clean up properly
            try:
                db_gen.close()
            except (StopIteration, GeneratorExit):
                pass  # Normal generator cleanup
        except StopIteration:
            pytest.fail("get_db generator should yield a session")
    
    @patch.dict(os.environ, {"DW_DB_PATH": "test_env_integration.db"}, clear=False)
    def test_environment_integration_with_create_tables(self):
        """Test that create_tables works with different database configurations."""
        from src.database import create_tables, engine
        
        # This should not raise an exception
        try:
            create_tables()
            # Verify the database file would be created with correct name
            assert "test_env_integration.db" in str(engine.url)
        except Exception as e:
            pytest.fail(f"create_tables failed with environment configuration: {e}")
    
    def test_multiple_environment_scenarios(self):
        """Test various environment combinations to ensure robust behavior."""
        test_scenarios = [
            # (DW_DB_PATH, PYTEST_CURRENT_TEST, expected_db_file)
            ("custom.db", None, "custom.db"),
            ("", "test_file", "worldweaver.db"),  # Empty DW_DB_PATH
            (None, "test_file", "test_database.db"),  # No DW_DB_PATH, pytest active
            (None, None, "worldweaver.db"),  # Production scenario
            ("relative/path/db.sqlite", None, "relative/path/db.sqlite"),
            ("/absolute/path/db.sqlite", "test", "/absolute/path/db.sqlite"),
        ]
        
        for dw_db_path, pytest_test, expected_db in test_scenarios:
            # Clear existing imports
            modules_to_clear = [name for name in sys.modules if 'src.database' in name]
            for module_name in modules_to_clear:
                del sys.modules[module_name]
            
            # Set up environment
            env_vars = {}
            if dw_db_path is not None:
                env_vars["DW_DB_PATH"] = dw_db_path
            if pytest_test is not None:
                env_vars["PYTEST_CURRENT_TEST"] = pytest_test
            
            with patch.dict(os.environ, env_vars, clear=True):
                from src.database import db_file
                assert db_file == expected_db, f"Failed for DW_DB_PATH={dw_db_path}, PYTEST={pytest_test}"
