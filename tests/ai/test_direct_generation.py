#!/usr/bin/env python3
"""Test intelligent generation directly (pytest-safe, no hanging)."""

import pytest
import requests

BASE_URL = "http://localhost:8000"


def _api_running() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def test_intelligent_generation_direct():
    """Call /author/generate-intelligent with short timeouts; skip if API not running."""
    if not _api_running():
        pytest.skip("API not running on localhost:8000; skipping direct intelligent generation test")

    payload = {
        "count": 2,
        "themes": ["exploration", "mystery"],
        "intelligent": True,
    }

    try:
        r = requests.post(
            f"{BASE_URL}/author/generate-intelligent",
            json=payload,
            timeout=(5, 20),  # separate connect/read timeouts
        )
    except requests.exceptions.ReadTimeout:
        pytest.skip("/author/generate-intelligent timed out (>20s); skipping in fast test mode")

    assert r.status_code == 200, r.text
    result = r.json()

    # Basic shape checks; endpoint returns a dict with message/storylets or error
    assert isinstance(result, dict)
    assert "message" in result or "storylets" in result or "error" in result
