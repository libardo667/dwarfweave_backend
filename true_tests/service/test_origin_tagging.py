"""Provenance tagging on the storylet primitive (item 02).

grounded = hand-authored (seeds) · inferred = healer-derived · assumed = default/LLM.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database import SessionLocal
from src.models import Storylet
from src.models.schemas import StoryletIn


def _cleanup(title):
    s = SessionLocal()
    s.query(Storylet).filter(Storylet.title == title).delete()
    s.commit()
    s.close()


def test_model_default_origin_is_assumed():
    title = "Origin Default Probe"
    _cleanup(title)
    s = SessionLocal()
    try:
        st = Storylet(title=title, text_template="x", requires={}, choices=[], weight=1.0)
        s.add(st)
        s.commit()
        s.refresh(st)
        assert st.origin == "assumed"
    finally:
        s.close()
        _cleanup(title)


def test_storylet_in_schema_defaults_assumed():
    assert StoryletIn(title="t", text_template="x").origin == "assumed"


def test_smoother_insert_is_inferred():
    from src.services.story_smoother import StorySmoother
    title = "Inferred Probe Storylet"
    _cleanup(title)
    try:
        StorySmoother()._insert_storylet({
            "title": title, "text_template": "x",
            "requires": {}, "choices": [], "weight": 1.0,
        })
        s = SessionLocal()
        row = s.query(Storylet).filter(Storylet.title == title).first()
        s.close()
        assert row is not None and row.origin == "inferred"
    finally:
        _cleanup(title)
