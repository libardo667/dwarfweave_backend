"""Tests for game API cache cleanup functionality."""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.game import cleanup_old_sessions, _state_managers
from main import app

client = TestClient(app)


class TestCacheCleanupLogic:
    """Test suite for cache cleanup functionality (Task: game-003)."""
    
    def setup_method(self):
        """Reset state managers cache before each test."""
        global _state_managers
        _state_managers.clear()
    
    def test_cleanup_old_sessions_precise_cache_removal(self):
        """Test that cleanup removes only deleted session IDs from cache."""
        # Setup: Create mock database session
        mock_db = Mock()
        
        # Mock the database query results
        # Simulate 3 sessions that will be deleted
        mock_sessions_result = [
            ("session_1",),
            ("session_2", ),
            ("session_3",)
        ]
        
        # Setup mock execute calls
        mock_db.execute.side_effect = [
            # First call: Get sessions to delete
            Mock(fetchall=Mock(return_value=mock_sessions_result)),
            # Second call: Delete sessions (returns affected rows)
            Mock(rowcount=3)
        ]
        
        # Setup state managers cache with some sessions
        # (including sessions that should NOT be deleted)
        global _state_managers
        _state_managers["session_1"] = Mock()  # Will be deleted
        _state_managers["session_2"] = Mock()  # Will be deleted  
        _state_managers["session_3"] = Mock()  # Will be deleted
        _state_managers["session_4"] = Mock()  # Should remain
        _state_managers["session_5"] = Mock()  # Should remain
        
        # Execute cleanup
        result = cleanup_old_sessions(db=mock_db)
        
        # Verify database operations
        assert mock_db.execute.call_count == 2
        mock_db.commit.assert_called_once()
        
        # Verify precise cache cleanup
        assert "session_1" not in _state_managers  # Removed
        assert "session_2" not in _state_managers  # Removed
        assert "session_3" not in _state_managers  # Removed
        assert "session_4" in _state_managers      # Preserved
        assert "session_5" in _state_managers      # Preserved
        
        # Verify return values
        assert result["success"] is True
        assert result["sessions_removed"] == 3
        assert result["cache_entries_removed"] == 3
        assert "3 sessions older than 24 hours" in result["message"]
    
    def test_cleanup_with_no_sessions_to_delete(self):
        """Test cleanup when no sessions are old enough to delete."""
        mock_db = Mock()
        
        # Mock empty results (no sessions to delete)
        mock_db.execute.side_effect = [
            Mock(fetchall=Mock(return_value=[])),  # No sessions found
            Mock(rowcount=0)  # No rows deleted
        ]
        
        # Setup some cache entries
        global _state_managers
        _state_managers["active_session_1"] = Mock()
        _state_managers["active_session_2"] = Mock()
        
        result = cleanup_old_sessions(db=mock_db)
        
        # Verify no cache entries were removed
        assert len(_state_managers) == 2
        assert "active_session_1" in _state_managers
        assert "active_session_2" in _state_managers
        
        # Verify return values
        assert result["success"] is True
        assert result["sessions_removed"] == 0
        assert result["cache_entries_removed"] == 0
        assert "0 sessions older than 24 hours" in result["message"]
    
    def test_cleanup_cache_entries_not_in_database(self):
        """Test cleanup when cache has entries not in database deletion list."""
        mock_db = Mock()
        
        # Mock database returns only session_1 for deletion
        mock_sessions_result = [("session_1",)]
        mock_db.execute.side_effect = [
            Mock(fetchall=Mock(return_value=mock_sessions_result)),
            Mock(rowcount=1)
        ]
        
        # Setup cache with entries that won't be in database deletion list
        global _state_managers
        _state_managers["session_1"] = Mock()  # Will be deleted (in DB)
        _state_managers["orphaned_session"] = Mock()  # Won't be deleted (not in DB)
        
        result = cleanup_old_sessions(db=mock_db)
        
        # Verify precise cleanup: only DB-deleted sessions removed from cache
        assert "session_1" not in _state_managers
        assert "orphaned_session" in _state_managers  # Preserved
        
        assert result["sessions_removed"] == 1
        assert result["cache_entries_removed"] == 1  # Only 1 removed from cache
    
    def test_cleanup_handles_database_error(self):
        """Test cleanup handles database errors gracefully."""
        from fastapi import HTTPException
        
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            cleanup_old_sessions(db=mock_db)
        
        assert exc_info.value.status_code == 500
        assert "Session cleanup failed" in str(exc_info.value.detail)
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
    
    @patch('src.api.game.logging')
    def test_cleanup_logging_behavior(self, mock_logging):
        """Test that cleanup logs appropriate information."""
        mock_db = Mock()
        
        # Mock successful cleanup of 2 sessions
        mock_sessions_result = [("session_1",), ("session_2",)]
        mock_db.execute.side_effect = [
            Mock(fetchall=Mock(return_value=mock_sessions_result)),
            Mock(rowcount=2)
        ]
        
        # Setup cache with both sessions
        global _state_managers
        _state_managers["session_1"] = Mock()
        _state_managers["session_2"] = Mock()
        
        cleanup_old_sessions(db=mock_db)
        
        # Verify info logging
        mock_logging.info.assert_called_once()
        log_message = mock_logging.info.call_args[0][0]
        assert "🧹 Cleaned up 2 old sessions (2 removed from cache)" in log_message
    
    @patch('src.api.game.logging')
    def test_cleanup_error_logging(self, mock_logging):
        """Test that cleanup logs errors appropriately."""
        from fastapi import HTTPException
        
        mock_db = Mock()
        error_message = "Test database error"
        mock_db.execute.side_effect = Exception(error_message)
        
        with pytest.raises(HTTPException):
            cleanup_old_sessions(db=mock_db)
        
        # Verify error logging
        mock_logging.error.assert_called_once()
        log_message = mock_logging.error.call_args[0][0]
        assert "❌ Session cleanup failed:" in log_message
        assert error_message in log_message
    
    def test_cleanup_cutoff_time_calculation(self):
        """Test that cleanup uses correct 24-hour cutoff time."""
        mock_db = Mock()
        
        # Capture the SQL parameters to verify cutoff time
        captured_params = []
        
        def capture_execute(*args, **kwargs):
            if len(args) > 1:
                captured_params.append(args[1])
            return Mock(fetchall=Mock(return_value=[]))
        
        mock_db.execute.side_effect = capture_execute
        
        # Record time before cleanup
        before_cleanup = datetime.now(UTC)
        
        cleanup_old_sessions(db=mock_db)
        
        # Record time after cleanup
        after_cleanup = datetime.now(UTC)
        
        # Verify cutoff time is approximately 24 hours ago
        assert len(captured_params) >= 1
        cutoff_time = captured_params[0]["cutoff"]
        
        expected_cutoff_start = before_cleanup - timedelta(hours=24)
        expected_cutoff_end = after_cleanup - timedelta(hours=24)
        
        assert expected_cutoff_start <= cutoff_time <= expected_cutoff_end
    
    def test_cleanup_endpoint_integration(self):
        """Test cleanup endpoint through FastAPI test client."""
        # This is more of an integration test, but validates the endpoint works
        import requests
        BASE_URL = "http://localhost:8000"
        try:
            response = requests.post(f"{BASE_URL}/api/admin/cleanup", timeout=3)
        except requests.ConnectionError:
            pytest.fail("Server is not running at http://localhost:8000. Please start the FastAPI server before running this test.")
        
        # Should succeed (even if no sessions to clean)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "sessions_removed" in data
        assert "cache_entries_removed" in data
        assert "message" in data
