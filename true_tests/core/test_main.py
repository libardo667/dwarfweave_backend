"""Tests for main FastAPI application."""

import pytest
import requests
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"


def test_health_check_endpoint():
    """Test GET /health returns {'ok': True} and valid ISO 8601 UTC timestamp from running server."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
    except requests.ConnectionError:
        pytest.fail("Server is not running at http://localhost:8000. Please start the FastAPI server before running this test.")
    
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert "time" in data
    assert data["ok"] is True
    timestamp_str = data["time"]
    assert timestamp_str.endswith("Z"), "Timestamp should end with 'Z' for UTC"
    timestamp_without_z = timestamp_str[:-1]
    try:
        parsed_time = datetime.fromisoformat(timestamp_without_z)
        now = datetime.now(timezone.utc)
        time_diff = abs((now - parsed_time).total_seconds())
        assert time_diff < 60, "Health check timestamp should be recent"
    except ValueError as e:
        pytest.fail(f"Invalid ISO 8601 timestamp format: {timestamp_str}, error: {e}")


def test_health_check_response_content_type():
    """Test health check returns JSON content type from running server."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
    except requests.ConnectionError:
        pytest.fail("Server is not running at http://localhost:8000. Please start the FastAPI server before running this test.")
    assert response.headers["content-type"] == "application/json"


def test_health_check_consistent_format():
    """Test health check returns consistent response format across multiple calls to running server."""
    try:
        responses = [requests.get(f"{BASE_URL}/health", timeout=3) for _ in range(3)]
    except requests.ConnectionError:
        pytest.fail("Server is not running at http://localhost:8000. Please start the FastAPI server before running this test.")
    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["time"], str)
        assert data["time"].endswith("Z")
