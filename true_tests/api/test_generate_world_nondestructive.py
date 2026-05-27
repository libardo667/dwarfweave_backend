"""generate-world accretes by default — it must not wipe the existing world (item 10)."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.api.author import generate_world_from_description
from src.models.schemas import WorldDescription
from src.database import SessionLocal
from src.models import Storylet

MARKER = "Preexisting Accretion Marker"


def _cleanup():
    s = SessionLocal()
    s.query(Storylet).filter(Storylet.title == MARKER).delete()
    s.commit()
    s.close()


def test_generate_world_keeps_existing_by_default():
    _cleanup()
    s = SessionLocal()
    try:
        s.add(Storylet(title=MARKER, text_template="x", requires={}, choices=[], weight=1.0))
        s.commit()
        wd = WorldDescription(description="A small test world for accretion checks", theme="testing")
        # reset defaults to False -> generation must ADD, not wipe.
        generate_world_from_description(wd, db=s)
        assert s.query(Storylet).filter(Storylet.title == MARKER).first() is not None
    finally:
        s.close()
        _cleanup()
