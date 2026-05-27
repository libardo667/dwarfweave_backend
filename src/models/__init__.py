"""Database models."""

from datetime import datetime
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, func
from ..database import Base


class Storylet(Base):
    """Model for interactive fiction storylets."""
    __tablename__ = 'storylets'
    
    id = Column(Integer, primary_key=True)
    # Title should be unique to prevent accidental duplicate storylets
    title = Column(String(200), nullable=False, unique=True)
    text_template = Column(Text, nullable=False)
    requires = Column(JSON, default=dict)
    choices = Column(JSON, default=list)
    weight = Column(Float, default=1.0)
    spatial_x = Column(Integer, nullable=True)  # X coordinate for spatial navigation
    spatial_y = Column(Integer, nullable=True)  # Y coordinate for spatial navigation
    origin = Column(String(16), nullable=False, server_default="assumed")  # provenance: grounded | inferred | assumed (item 02)


class SessionVars(Base):
    """Model for storing session variables."""
    __tablename__ = 'session_vars'

    session_id = Column(String(64), primary_key=True)
    vars = Column(JSON, default=dict)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class WorldFrame(Base):
    """The world bible as data — the coherence anchor generation seeds INTO (item 10).

    A frame holds the world's *bones*, not storylets:
      - **lore** — tone, premise, locations, factions, entities, tensions (narrative
        pressure; the loom fuel an LLM authors).
      - **laws** — systemic dynamics (``{name, rule, variable, origin}``). Some laws are
        system-injected (``origin="system"``), so they hold beyond any single authoring
        agent's control — the "drunken cats" principle: emergent outcomes nobody wrote.

    Versioned: a frame iterates as the world updates. Re-generation writes a NEW row at
    ``version+1`` and keeps prior rows as history; the current frame is the highest
    version. The frame is ``grounded`` provenance — the bedrock storylets are inferred
    against.
    """
    __tablename__ = 'world_frames'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    frame = Column(JSON, default=dict)  # the bible blob: lore + laws
    origin = Column(String(16), nullable=False, server_default="grounded")
    created_at = Column(DateTime, server_default=func.now())
