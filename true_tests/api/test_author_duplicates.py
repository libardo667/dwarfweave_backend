import sys
import os
import pytest

# Ensure project src/ is importable when running tests from true_tests/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.api.author import author_commit
from src.models.schemas import SuggestResp, StoryletIn
from src.database import SessionLocal
from src.models import Storylet


def test_author_commit_skips_duplicates():
    # Use a fresh session
    session = SessionLocal()
    try:
        # Clean up any storylets with our test title
        session.query(Storylet).filter(Storylet.title == 'Unique Duplicate Test').delete()
        session.commit()

        # First commit: add two storylets, one with the test title
        payload = SuggestResp(storylets=[
            StoryletIn(title='Unique Duplicate Test', text_template='x', requires={}, choices=[], weight=1.0),
            StoryletIn(title='Another Title', text_template='y', requires={}, choices=[], weight=1.0),
        ])
        author_commit(payload, db=session)

        # Second commit: attempt to add the same title again
        payload2 = SuggestResp(storylets=[
            StoryletIn(title='Unique Duplicate Test', text_template='x', requires={}, choices=[], weight=1.0),
        ])
        author_commit(payload2, db=session)

        # Query DB: 'Unique Duplicate Test' should only exist once
        rows = session.query(Storylet).filter(Storylet.title == 'Unique Duplicate Test').all()
        assert len(rows) == 1

    finally:
        # Clean up
        session.query(Storylet).filter(Storylet.title.in_(['Unique Duplicate Test', 'Another Title'])).delete()
        session.commit()
        session.close()
