"""Root pytest config: tier the suite so the default run is deterministic.

Marks live tests by location/name so `addopts` (see pytest.ini) can deselect them
by default. Opt in with `pytest -m live_llm` or `pytest -m live_server`.

Note: per-subtree fixtures/env setup live in `tests/conftest.py`; this root file
only classifies collected items (it must be at the root to see `true_tests/` too).
"""

import pytest

_LIVE_LLM_PARTS = ("/tests/ai/", "test_ai_setup", "test_auto_improvement")
_LIVE_SERVER_NAMES = (
    "test_populate_endpoint_target_count_validation",
    "test_suggest_endpoint_with_invalid_n",
    "test_cleanup_endpoint_integration",
)


def pytest_collection_modifyitems(config, items):
    for item in items:
        nodeid = item.nodeid.replace("\\", "/")
        if any(part in nodeid for part in _LIVE_LLM_PARTS):
            item.add_marker(pytest.mark.live_llm)
        if "test_main.py" in nodeid or any(name in nodeid for name in _LIVE_SERVER_NAMES):
            item.add_marker(pytest.mark.live_server)
