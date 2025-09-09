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


class SessionVars(Base):
    """Model for storing session variables."""
    __tablename__ = 'session_vars'
    
    session_id = Column(String(64), primary_key=True)
    vars = Column(JSON, default=dict)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
