"""POV-seed: an arriving inhabitant's storylets seeded INTO the frame, origin=inferred (item 10)."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from fastapi import HTTPException

from src.api.author import seed_pov, generate_frame
from src.services.llm_service import generate_pov_seed, _frame_location_names
from src.models.schemas import POVSeedRequest, WorldDescription
from src.database import SessionLocal
from src.models import Storylet, WorldFrame

POV = "a Tester Apprentice freshly arrived"


def _clear():
    s = SessionLocal()
    s.query(WorldFrame).delete()
    s.query(Storylet).filter(Storylet.title.like("Arrival:%")).delete(synchronize_session=False)
    s.commit()
    s.close()


def test_seed_pov_requires_a_frame():
    """With no frame, seeding is a 400 — accretion order is frame, then seed."""
    _clear()
    s = SessionLocal()
    try:
        with pytest.raises(HTTPException) as exc:
            seed_pov(POVSeedRequest(pov=POV, count=2), db=s)
        assert exc.value.status_code == 400
    finally:
        s.close()
        _clear()


def test_seed_pov_seeds_inferred_storylets_within_frame():
    """After a frame exists, seeding adds storylets tagged inferred, set in a frame location."""
    _clear()
    s = SessionLocal()
    try:
        # Establish a frame first.
        generate_frame(WorldDescription(description="A small world for POV-seed checks", theme="testing"), db=s)
        frame_row = s.query(WorldFrame).order_by(WorldFrame.version.desc()).first()
        frame_locations = set(_frame_location_names(frame_row.frame))

        result = seed_pov(POVSeedRequest(pov=POV, count=2), db=s)
        assert result["success"] is True
        assert result["seeded"] >= 1
        # Seeded storylets are inferred from the grounded frame.
        assert all(st["origin"] == "inferred" for st in result["storylets"])
        # And they sit within an existing frame location.
        for st in result["storylets"]:
            loc = st["requires"].get("location")
            if loc is not None:
                assert loc in frame_locations
    finally:
        s.close()
        _clear()


def test_generate_pov_seed_offline_uses_frame_location():
    """The offline generator seeds at least one storylet anchored to a frame location."""
    frame = {"locations": [{"name": "canopy_commons"}, {"name": "root_warrens"}]}
    seeds = generate_pov_seed(frame, POV, count=2)
    assert len(seeds) >= 1
    assert seeds[0]["requires"]["location"] in {"canopy_commons", "root_warrens"}
