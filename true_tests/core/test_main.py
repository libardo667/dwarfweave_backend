"""Tests for main FastAPI application."""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Add parent directory to path to import main
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Test GET /health returns {'ok': True} and valid ISO 8601 UTC timestamp."""
    response = client.get("/health")
    
    # Check status code
    assert response.status_code == 200
    
    # Check response structure
    data = response.json()
    assert "ok" in data
    assert "time" in data
    
    # Check 'ok' is True
    assert data["ok"] is True
    
    # Check timestamp is valid ISO 8601 format with Z suffix
    timestamp_str = data["time"]
    assert timestamp_str.endswith("Z"), "Timestamp should end with 'Z' for UTC"
    
    # Parse the timestamp to ensure it's valid ISO 8601
    # Remove 'Z' and parse
    timestamp_without_z = timestamp_str[:-1]
    try:
        parsed_time = datetime.fromisoformat(timestamp_without_z)
        # Ensure it's recent (within last minute)
        now = datetime.now(timezone.utc)
        time_diff = abs((now - parsed_time).total_seconds())
        assert time_diff < 60, "Health check timestamp should be recent"
    except ValueError as e:
        pytest.fail(f"Invalid ISO 8601 timestamp format: {timestamp_str}, error: {e}")


def test_health_check_response_content_type():
    """Test health check returns JSON content type."""
    response = client.get("/health")
    assert response.headers["content-type"] == "application/json"


def test_health_check_consistent_format():
    """Test health check returns consistent response format across multiple calls."""
    # Make multiple calls
    responses = [client.get("/health") for _ in range(3)]
    
    # All should be successful
    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["time"], str)
        assert data["time"].endswith("Z")
