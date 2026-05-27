"""Database seeding functionality."""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import Storylet
from ..database import SessionLocal

import json
from pathlib import Path

_WORLD_PACK = Path(__file__).resolve().parents[2] / "worlds" / "starter_mine.json"

def _seed_rows(session: Session) -> None:
    """Seed the database with initial storylets if empty. Runs in the caller's transaction."""
    # If anything here raises, caller's transaction can roll back cleanly.
    if session.query(Storylet).count() > 0:
        return

    data = json.loads(_WORLD_PACK.read_text(encoding="utf-8"))
    seeds = [
        Storylet(
            title=row["title"],
            text_template=row["text_template"],
            requires=row.get("requires", {}),
            choices=row.get("choices", []),
            weight=row.get("weight", 1.0),
            origin="grounded",  # hand-authored world pack (item 02/03)
        )
        for row in data["storylets"]
    ]
    session.add_all(seeds)
    session.flush()


def seed_if_empty_sync(session: Session) -> None:
    """Inline, test-freindly; respsect's caller's transaction."""
    _seed_rows(session)
    
async def seed_if_empty(session: Optional[Session] = None, *, in_background: bool = False) -> None:
    """
    Async wrapper. 
    - if in_background=False: uses provided session inline (test-friendly).
    - if in_background=True: creates its own Session in a worker thread and commits (prod-friendly)
    """
    
    if not in_background:
        assert session is not None, "Provide a Session when running inline."
        return seed_if_empty_sync(session)
    
    import asyncio
    
    def _work():
        # Each background worker gets its own session, then commits, cleans up
        with SessionLocal() as s:
            _seed_rows(s)
            s.commit()
        SessionLocal.remove()
            
    await asyncio.to_thread(_work)