"""Main game API routes with Advanced State Management."""

import logging
import traceback
from typing import Any, Dict, List, cast
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SessionVars, Storylet
from ..models.schemas import NextReq, NextResp, ChoiceOut
from ..services.game_logic import pick_storylet, render
from ..services.state_manager import AdvancedStateManager

router = APIRouter()

# Cache for state managers (in production, use Redis or similar)
_state_managers: Dict[str, AdvancedStateManager] = {}


def get_state_manager(session_id: str, db: Session) -> AdvancedStateManager:
    """Get or create a state manager for the session."""
    if session_id not in _state_managers:
        manager = AdvancedStateManager(session_id)
        
        # Load existing state from database if available
        row = db.get(SessionVars, session_id)
        if row is not None and row.vars is not None:
            # Convert old vars format to new state format
            legacy_vars = cast(Dict[str, Any], row.vars or {})
            manager.variables.update(legacy_vars)
            
            # Initialize some defaults for better gameplay
            manager.variables.setdefault("name", "Adventurer")
            manager.variables.setdefault("danger", 0)
            manager.variables.setdefault("has_pickaxe", True)
            
        _state_managers[session_id] = manager
        
    return _state_managers[session_id]


def _norm_choices(c: Dict[str, Any]) -> ChoiceOut:
    """Normalize choice dictionary to ChoiceOut model."""
    label = c.get("label") or c.get("text") or "Continue"
    set_obj = c.get("set") or c.get("set_vars") or {}
    return ChoiceOut(label=label, set=set_obj)


@router.post('/next', response_model=NextResp)
def api_next(payload: NextReq, db: Session = Depends(get_db)):
    """Get the next storylet for a session with Advanced State Management."""
    # Get the advanced state manager
    state_manager = get_state_manager(payload.session_id, db)
    
    # Update state with any new variables from client
    for key, value in (payload.vars or {}).items():
        state_manager.set_variable(key, value)
    
    # Get full contextual variables for storylet evaluation
    contextual_vars = state_manager.get_contextual_variables()
    
    # Pick a storylet using enhanced condition evaluation
    story = pick_storylet_enhanced(db, state_manager)
    
    if story is None:
        text = "🕯️ The tunnel is quiet. Nothing compelling meets the eye."
        choices = [ChoiceOut(label='Wait', set={})]
        
        # Add some contextual flavor based on state
        if state_manager.environment.danger_level > 3:
            text = "⚠️ The air feels heavy with danger. Perhaps it's wise to wait and listen."
        elif state_manager.environment.time_of_day == "night":
            text = "🌙 The darkness is deep. Something stirs in the shadows, but nothing approaches."
        
        out = NextResp(text=text, choices=choices, vars=contextual_vars)
    else:
        # Render text with full contextual variables
        text = render(cast(str, story.text_template), contextual_vars)
        choices = [_norm_choices(c) for c in cast(List[Dict[str, Any]], story.choices or [])]
        out = NextResp(text=text, choices=choices, vars=contextual_vars)
    
    # Save enhanced state back to database
    save_state_to_db(state_manager, db)
    
    return out


def pick_storylet_enhanced(db: Session, state_manager: AdvancedStateManager) -> Storylet | None:
    """Enhanced storylet picking using the new state manager."""
    all_storylets = db.query(Storylet).all()
    eligible = []
    
    for storylet in all_storylets:
        requirements = cast(Dict[str, Any], storylet.requires or {})
        if state_manager.evaluate_condition(requirements):
            eligible.append(storylet)
    
    if not eligible:
        return None
    
    # Use existing weight-based selection
    import random
    weights = [max(0.0, cast(float, s.weight or 0.0)) for s in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]


def save_state_to_db(state_manager: AdvancedStateManager, db: Session):
    """Save the enhanced state back to the database."""
    session_id = state_manager.session_id
    
    # Get or create session vars row
    row = db.get(SessionVars, session_id)
    if row is None:
        row = SessionVars(session_id=session_id, vars={})
        db.add(row)
    
    # For now, save just the basic variables (could extend to save full state)
    row.vars = state_manager.variables  # type: ignore
    db.commit()


@router.get('/state/{session_id}')
def get_state_summary(session_id: str, db: Session = Depends(get_db)):
    """Get a comprehensive summary of the session state."""
    state_manager = get_state_manager(session_id, db)
    return state_manager.get_state_summary()


@router.post('/state/{session_id}/relationship')
def update_relationship(session_id: str, entity_a: str, entity_b: str, 
                       changes: Dict[str, float], memory: str | None = None,
                       db: Session = Depends(get_db)):
    """Update a relationship between entities."""
    state_manager = get_state_manager(session_id, db)
    relationship = state_manager.update_relationship(entity_a, entity_b, changes, memory)
    save_state_to_db(state_manager, db)
    
    return {
        "relationship": f"{entity_a}-{entity_b}",
        "disposition": relationship.get_overall_disposition(),
        "trust": relationship.trust,
        "respect": relationship.respect,
        "interaction_count": relationship.interaction_count
    }


@router.post('/state/{session_id}/item')
def add_item_to_inventory(session_id: str, item_id: str, name: str, 
                         quantity: int = 1, properties: Dict[str, Any] | None = None,
                         db: Session = Depends(get_db)):
    """Add an item to the player's inventory."""
    state_manager = get_state_manager(session_id, db)
    item = state_manager.add_item(item_id, name, quantity, properties or {})
    save_state_to_db(state_manager, db)
    
    return {
        "item_id": item.id,
        "name": item.name,
        "quantity": item.quantity,
        "condition": item.condition,
        "available_actions": item.get_available_actions(state_manager.get_contextual_variables())
    }


@router.post('/state/{session_id}/environment')
def update_environment(session_id: str, changes: Dict[str, Any],
                      db: Session = Depends(get_db)):
    """Update environmental conditions."""
    state_manager = get_state_manager(session_id, db)
    state_manager.update_environment(changes)
    save_state_to_db(state_manager, db)
    
    return {
        "environment": {
            "time_of_day": state_manager.environment.time_of_day,
            "weather": state_manager.environment.weather,
            "danger_level": state_manager.environment.danger_level,
            "mood_modifiers": state_manager.environment.get_mood_modifier()
        }
    }
