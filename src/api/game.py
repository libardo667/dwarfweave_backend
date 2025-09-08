"""Main game API routes with Advanced State Management and Spatial Navigation."""

import logging
import traceback
from typing import Any, Dict, List, cast
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from fastapi import Body, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SessionVars, Storylet
from ..models.schemas import NextReq, NextResp, ChoiceOut
from ..services.game_logic import pick_storylet, render
from ..services.state_manager import AdvancedStateManager
from ..services.spatial_navigator import SpatialNavigator, DIRECTIONS

router = APIRouter()

# Cache for state managers and spatial navigators (in production, use Redis or similar)
_state_managers: Dict[str, AdvancedStateManager] = {}
_spatial_navigators: Dict[str, SpatialNavigator] = {}


def get_spatial_navigator(db: Session) -> SpatialNavigator:
    """Get or create a spatial navigator."""
    # Use a single navigator per database connection
    db_key = str(id(db))
    if db_key not in _spatial_navigators:
        # Pass the SQLAlchemy session directly
        _spatial_navigators[db_key] = SpatialNavigator(db)
    return _spatial_navigators[db_key]


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


@router.post('/cleanup-sessions')
def cleanup_old_sessions(db: Session = Depends(get_db)):
    """Clean up sessions older than 24 hours."""
    from datetime import datetime, timedelta
    from sqlalchemy import text
    
    try:
        # Calculate cutoff time (24 hours ago)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Count sessions to be deleted
        count_result = db.execute(
            text("SELECT COUNT(*) FROM session_vars WHERE updated_at < :cutoff"),
            {"cutoff": cutoff_time}
        ).scalar()
        
        # Ensure count_result is not None
        sessions_to_delete = count_result or 0
        
        # Delete old sessions
        result = db.execute(
            text("DELETE FROM session_vars WHERE updated_at < :cutoff"),
            {"cutoff": cutoff_time}
        )
        
        db.commit()
        
        # Clear state manager cache for deleted sessions
        global _state_managers
        sessions_to_remove = []
        
        # Remove sessions from cache that correspond to deleted database entries
        # This is a simple heuristic - in production you'd want more precise matching
        cache_sessions = list(_state_managers.keys())
        for i, session_id in enumerate(cache_sessions):
            if i < sessions_to_delete:  # Remove roughly the same number as deleted from DB
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            _state_managers.pop(session_id, None)
        
        logging.info(f"🧹 Cleaned up {sessions_to_delete} old sessions")
        
        return {
            "success": True,
            "sessions_removed": sessions_to_delete,
            "message": f"Cleaned up {sessions_to_delete} sessions older than 24 hours"
        }
        
    except Exception as e:
        db.rollback()
        logging.error(f"❌ Session cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Session cleanup failed: {str(e)}")


@router.get('/spatial/navigation/{session_id}')
def get_spatial_navigation(session_id: str, db: Session = Depends(get_db)):
    """Get 8-directional navigation options from current location."""
    try:
        state_manager = get_state_manager(session_id, db)
        spatial_nav = get_spatial_navigator(db)
        
        # Get current storylet ID
        current_location = state_manager.get_variable("location", "start")
        
        # Get current storylet by location
        current_storylet = db.query(Storylet).filter(
            Storylet.requires.contains(f'"location": "{current_location}"')
        ).first()
        
        if not current_storylet:
            return {"error": "Current location not found", "directions": {}}
        
        # Get the actual ID value from the SQLAlchemy model
        current_id = cast(int, current_storylet.id)
        
        # Get directional navigation options
        directions = spatial_nav.get_directional_navigation(current_id)
        
        # Filter by player requirements
        player_vars = state_manager.get_contextual_variables()
        available_directions = {}
        
        for direction, target in directions.items():
            if target is None:
                available_directions[direction] = None
            else:
                can_access = spatial_nav.can_move_to_direction(
                    current_id, direction, player_vars
                )
                available_directions[direction] = {
                    **target,
                    "accessible": can_access,
                    "reason": "Requirements not met" if not can_access else None
                }
        
        return {
            "current_location": current_location,
            "current_storylet": {
                "id": current_id,
                "title": current_storylet.title,
                "position": spatial_nav.storylet_positions.get(current_id)
            },
            "directions": available_directions
        }
        
    except Exception as e:
        logging.error(f"❌ Spatial navigation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Navigation failed: {str(e)}")


class _MoveReq(BaseModel):
    direction: str


@router.post('/spatial/move/{session_id}')
def move_in_direction(
    session_id: str,
    payload: dict | None = Body(default=None),
    direction: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    """Move the player in a specific direction."""
    try:
        state_manager = get_state_manager(session_id, db)
        spatial_nav = get_spatial_navigator(db)
        
        # Validate direction from either JSON or query
        if direction is None and payload is not None:
            direction = payload.get('direction')
        
        if direction is None:
            raise HTTPException(status_code=400, detail="Missing 'direction'")
        
        if direction not in DIRECTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid direction: {direction}")
        
        # Get current storylet
        current_location = state_manager.get_variable("location", "start")
        current_storylet = db.query(Storylet).filter(
            Storylet.requires.contains(f'"location": "{current_location}"')
        ).first()
        
        if not current_storylet:
            raise HTTPException(status_code=404, detail="Current location not found")
        
        current_id = cast(int, current_storylet.id)
        
        # Check if movement is allowed
        player_vars = state_manager.get_contextual_variables()
        if not spatial_nav.can_move_to_direction(current_id, direction, player_vars):
            raise HTTPException(status_code=403, detail="Cannot move in that direction")
        
        # Get target storylet
        nav_options = spatial_nav.get_directional_navigation(current_id)
        target = nav_options.get(direction)
        
        if not target:
            raise HTTPException(status_code=404, detail="No location in that direction")
        
        # Update player location
        target_storylet = db.get(Storylet, target['id'])
        if target_storylet is not None and target_storylet.requires is not None:
            requirements = cast(Dict[str, Any], target_storylet.requires)
            new_location = requirements.get('location')
            if new_location:
                state_manager.set_variable("location", new_location)
                save_state_to_db(state_manager, db)
        
        return {
            "success": True,
            "direction": direction,
            "new_location": target['title'],
            "message": f"Moved {direction} to {target['title']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Movement failed: {e}")
        raise HTTPException(status_code=500, detail=f"Movement failed: {str(e)}")


@router.get('/spatial/map')
def get_spatial_map(db: Session = Depends(get_db)):
    """Get the full spatial map data for rendering."""
    try:
        spatial_nav = get_spatial_navigator(db)
        map_data = spatial_nav.get_spatial_map_data()
        
        return {
            "map": map_data,
            "center": {"x": 0, "y": 0},  # Could be player position
            "directions": {
                name: {"symbol": direction.symbol, "dx": direction.dx, "dy": direction.dy}
                for name, direction in DIRECTIONS.items()
            }
        }
        
    except Exception as e:
        logging.error(f"❌ Map generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Map generation failed: {str(e)}")


@router.post('/spatial/assign-positions')
def assign_spatial_positions(db: Session = Depends(get_db)):
    """Assign spatial positions to all storylets (useful after world generation)."""
    try:
        spatial_nav = get_spatial_navigator(db)
        
        # Get all storylets
        storylets = db.query(Storylet).all()
        storylet_data = []
        
        for s in storylets:
            storylet_data.append({
                'title': s.title,
                'choices': cast(List[Dict[str, Any]], s.choices or []),
                'requires': cast(Dict[str, Any], s.requires or {})
            })
        
        # Assign spatial positions
        positions = spatial_nav.assign_spatial_positions(storylet_data)
        
        return {
            "success": True,
            "positions_assigned": len(positions),
            "positions": {
                str(storylet_id): {"x": pos.x, "y": pos.y}
                for storylet_id, pos in positions.items()
            }
        }
        
    except Exception as e:
        logging.error(f"❌ Position assignment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Position assignment failed: {str(e)}")
