"""World FRAME generation: lore + laws as data, system laws beyond the agent (item 10)."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.api.author import generate_frame, get_current_frame
from src.services.llm_service import (
    generate_world_frame,
    _inject_baseline_laws,
    BASELINE_LAWS,
)
from src.models.schemas import WorldDescription
from src.database import SessionLocal
from src.models import WorldFrame

SYSTEM_LAW_NAMES = {law["name"] for law in BASELINE_LAWS}


def _clear_frames():
    s = SessionLocal()
    s.query(WorldFrame).delete()
    s.commit()
    s.close()


def test_offline_frame_has_lore_and_system_laws():
    """The deterministic offline frame still carries lore keys + all system laws."""
    frame = generate_world_frame(
        description="A tidewater reach where the sea is rising and the priests deny it",
        theme="maritime folk-myth",
        tone="weathered",
    )
    for key in ("name", "tone", "premise", "locations", "factions", "entities", "tensions", "laws"):
        assert key in frame, f"frame missing '{key}'"

    law_names = {law["name"] for law in frame["laws"]}
    assert SYSTEM_LAW_NAMES <= law_names, "system baseline laws must always be present"
    # System laws are tagged as beyond-the-agent provenance.
    system_laws = [l for l in frame["laws"] if l["name"] in SYSTEM_LAW_NAMES]
    assert all(l["origin"] == "system" for l in system_laws)


def test_baseline_laws_injected_into_any_frame():
    """Even a frame with no/garbage laws gets the system laws; authored laws are tagged."""
    raw = {"laws": [{"name": "rising_tide", "rule": "the sea climbs each season"}]}
    out = _inject_baseline_laws(raw)
    names = {l["name"] for l in out["laws"]}
    assert SYSTEM_LAW_NAMES <= names
    assert "rising_tide" in names

    authored = next(l for l in out["laws"] if l["name"] == "rising_tide")
    assert authored["origin"] == "authored"


def test_system_laws_win_name_collision():
    """An authored law that squats a reserved system name does not override the system law."""
    raw = {"laws": [{"name": "time_advances", "rule": "fake override", "origin": "authored"}]}
    out = _inject_baseline_laws(raw)
    time_laws = [l for l in out["laws"] if l["name"] == "time_advances"]
    assert len(time_laws) == 1
    assert time_laws[0]["origin"] == "system"
    assert time_laws[0]["rule"] != "fake override"


def test_generate_frame_endpoint_stores_and_versions():
    """generate-frame persists a row and iterates version; get_current_frame returns latest."""
    _clear_frames()
    s = SessionLocal()
    try:
        wd = WorldDescription(description="A small test world for frame checks", theme="testing")

        first = generate_frame(wd, db=s)
        assert first["success"] is True
        assert first["version"] == 1

        second = generate_frame(wd, db=s)
        assert second["version"] == 2, "re-generation must iterate version, not overwrite"

        current = get_current_frame(db=s)
        assert current["version"] == 2
        assert current["frame"] is not None
        # both versions are kept as history
        assert s.query(WorldFrame).count() == 2
    finally:
        s.close()
        _clear_frames()


def test_get_current_frame_empty_world():
    """A world with no frame yet returns a null frame, not an error."""
    _clear_frames()
    s = SessionLocal()
    try:
        result = get_current_frame(db=s)
        assert result["frame"] is None
        assert result["version"] == 0
    finally:
        s.close()
        _clear_frames()
