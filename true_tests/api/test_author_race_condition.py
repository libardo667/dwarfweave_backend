import sys
import os
import pytest

# Ensure project src/ is importable when running tests from true_tests/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sqlalchemy.exc import IntegrityError
from src.api.author import author_commit
from src.models.schemas import SuggestResp, StoryletIn
from src.database import SessionLocal
from src.models import Storylet


def test_author_commit_handles_integrityerror(monkeypatch):
    session = SessionLocal()
    try:
        # Clean up any existing test rows
        session.query(Storylet).filter(Storylet.title.in_(['Race Title 1', 'Race Title 2'])).delete()
        session.commit()

        payload = SuggestResp(storylets=[
            StoryletIn(title='Race Title 1', text_template='a', requires={}, choices=[], weight=1.0),
            StoryletIn(title='Race Title 2', text_template='b', requires={}, choices=[], weight=1.0),
        ])

        # Make flush fail on the second call to simulate a race/IntegrityError
        call = {'n': 0}
        orig_flush = session.flush

        def flaky_flush():
            call['n'] += 1
            if call['n'] == 2:
                # IntegrityError expects an "orig" exception; provide a simple Exception
                raise IntegrityError('mock', {}, Exception('mock'))
            return orig_flush()

        monkeypatch.setattr(session, 'flush', flaky_flush)

        # Should not raise
        result = author_commit(payload, db=session)
        assert 'added' in result

        # After handling IntegrityError, exactly one of the two titles should be present
        rows1 = session.query(Storylet).filter(Storylet.title == 'Race Title 1').all()
        rows2 = session.query(Storylet).filter(Storylet.title == 'Race Title 2').all()

        assert len(rows1) + len(rows2) == 1

    finally:
        # Clean up
        session.query(Storylet).filter(Storylet.title.in_(['Race Title 1', 'Race Title 2'])).delete()
        session.commit()
        session.close()
