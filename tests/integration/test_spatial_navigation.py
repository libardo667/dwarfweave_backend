"""Integration tests for Spatial Navigation endpoints.

Uses FastAPI TestClient to exercise the API without a running server.
"""

from typing import Dict, Optional
from fastapi.testclient import TestClient

from main import app


def _first_accessible_direction(directions: Dict[str, Optional[dict]]) -> Optional[str]:
    for name, info in directions.items():
        if info and info.get("accessible"):
            return name
    return None


def test_spatial_assign_and_navigate():
    # Use context manager to ensure startup/shutdown runs and resources close promptly
    with TestClient(app) as client:
        # Assign spatial positions
        r = client.post("/api/spatial/assign-positions")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        assert data.get("positions_assigned", 0) >= 1

        # Initialize a session and set a starting location
        session_id = "test_spatial_session"
        r = client.post(
            "/api/next",
            json={"session_id": session_id, "vars": {"location": "forest"}},
        )
        assert r.status_code == 200, r.text

        # Get navigation options
        r = client.get(f"/api/spatial/navigation/{session_id}")
        assert r.status_code == 200, r.text
        nav = r.json()
        assert "directions" in nav
        directions = nav["directions"]

        # Try moving using JSON body
        move_dir = _first_accessible_direction(directions) or next(iter(directions.keys()))
        r = client.post(f"/api/spatial/move/{session_id}", json={"direction": move_dir})
        # Movement might be blocked; we only assert that the request is well-formed
        assert r.status_code in (200, 403, 404), r.text

        # Try moving using query parameter (backward compatibility)
        r = client.post(f"/api/spatial/move/{session_id}?direction={move_dir}")
        assert r.status_code in (200, 403, 404), r.text
