"""Pydantic models for API schemas."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field, field_validator


class NextReq(BaseModel):
    """Request model for getting next storylet."""
    session_id: str
    vars: Dict[str, Any]


class ChoiceOut(BaseModel):
    """Response model for storylet choices."""
    label: str
    set: Dict[str, Any] = {}


class NextResp(BaseModel):
    """Response model for next storylet."""
    text: str
    choices: List[ChoiceOut]
    vars: Dict[str, Any]


class StoryletIn(BaseModel):
    """Input model for creating storylets."""
    title: str = Field(..., max_length=200)
    text_template: str
    requires: Dict[str, Any] = Field(default_factory=dict)
    choices: List[Dict[str, Any]] = Field(default_factory=list)
    weight: float = 1.0
    
    # Accept both {"label", "set"} and {"text", "set_vars"}; normalize to label/set
    @field_validator('choices', mode='before')
    @classmethod
    def _normalize_choices(cls, v):
        out = []
        for c in (v or []):
            label = (c.get("label") or c.get("text") or "Continue")
            set_obj = (c.get("set") or c.get("set_vars") or {})
            out.append({"label": label, "set": set_obj})
        return out


class SuggestReq(BaseModel):
    """Request model for suggesting storylets."""
    n: int = Field(default=3, ge=1, le=20, description="Number of storylets to suggest (1-20)")
    themes: List[str] = Field(default_factory=list)
    bible: Dict[str, Any] = Field(default_factory=dict)


class SuggestResp(BaseModel):
    """Response model for suggested storylets."""
    storylets: List[StoryletIn]


class GenerateStoryletRequest(BaseModel):
    """Request to generate storylets with AI assistance."""
    count: int = Field(default=3, ge=1, le=15, description="Number of storylets to generate (1-15)")
    themes: List[str] = Field(default_factory=list, description="Themes to incorporate")
    intelligent: bool = Field(default=True, description="Use intelligent analysis")


class WorldDescription(BaseModel):
    """Request model for generating a complete world from user description."""
    description: str = Field(..., min_length=10, max_length=5000, description="Detailed description of your story world")
    theme: str = Field(..., min_length=3, max_length=100, description="Main theme or genre")
    player_role: str = Field(default="adventurer", description="What role does the player take?")
    key_elements: List[str] = Field(default_factory=list, description="Important world elements, locations, or concepts")
    tone: str = Field(default="adventure", description="Story tone: adventure, horror, comedy, epic, etc.")
    storylet_count: int = Field(default=15, ge=5, le=50, description="Number of storylets to generate")
