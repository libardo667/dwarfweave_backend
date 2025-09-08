"""Spatial navigation system for storylets with 8-directional movement."""

import json
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import text


@dataclass
class Position:
    """Represents a position in 2D space."""
    x: int
    y: int
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass
class Direction:
    """Represents a directional movement."""
    name: str
    dx: int
    dy: int
    symbol: str


# Define the 8 cardinal and intercardinal directions
DIRECTIONS = {
    'north': Direction('north', 0, -1, '↑'),
    'northeast': Direction('northeast', 1, -1, '↗'),
    'east': Direction('east', 1, 0, '→'),
    'southeast': Direction('southeast', 1, 1, '↘'),
    'south': Direction('south', 0, 1, '↓'),
    'southwest': Direction('southwest', -1, 1, '↙'),
    'west': Direction('west', -1, 0, '←'),
    'northwest': Direction('northwest', -1, -1, '↖')
}


class SpatialNavigator:
    """Manages spatial relationships between storylets."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.storylet_positions: Dict[int, Position] = {}
        self.position_storylets: Dict[Position, int] = {}
        self._load_positions()
    
    def _load_positions(self):
        """Load storylet positions from database."""
        try:
            result = self.db.execute(text("""
                SELECT id, spatial_x, spatial_y 
                FROM storylets 
                WHERE spatial_x IS NOT NULL AND spatial_y IS NOT NULL
            """))
            
            for row in result.fetchall():
                storylet_id, x, y = row
                pos = Position(x, y)
                self.storylet_positions[storylet_id] = pos
                self.position_storylets[pos] = storylet_id
                
        except Exception as e:
            print(f"⚠️ Warning: Could not load spatial positions: {e}")
            # Initialize empty if table doesn't have spatial columns yet
            self.storylet_positions = {}
            self.position_storylets = {}
    
    def _ensure_spatial_columns(self):
        """Ensure the database has spatial columns."""
        try:
            self.db.execute(text("""
                ALTER TABLE storylets 
                ADD COLUMN spatial_x INTEGER DEFAULT NULL
            """))
        except:
            pass  # Column probably already exists
        
        try:
            self.db.execute(text("""
                ALTER TABLE storylets 
                ADD COLUMN spatial_y INTEGER DEFAULT NULL
            """))
        except:
            pass  # Column probably already exists
        
        self.db.commit()
    
    def assign_spatial_positions(self, storylets: List[Dict[str, Any]], start_pos: Optional[Position] = None) -> Dict[int, Position]:
        """Assign spatial positions to storylets based on their connections."""
        if start_pos is None:
            start_pos = Position(0, 0)
        
        self._ensure_spatial_columns()
        
        # Clear existing positions for new world generation
        self.storylet_positions.clear()
        self.position_storylets.clear()
        
        # Get storylet IDs
        storylet_map = {}
        cursor = self.db.execute(text("SELECT id, title FROM storylets"))
        for row in cursor.fetchall():
            storylet_map[row[1]] = row[0]  # title -> id mapping
        
        if not storylets:
            return {}
        
        # Start with the first storylet at origin
        starting_storylet = storylets[0]
        starting_id = storylet_map.get(starting_storylet['title'])
        if not starting_id:
            return {}
        
        # Use a spiral placement algorithm to avoid overlaps
        positioned = set()
        to_position = [(starting_id, start_pos)]
        
        while to_position:
            storylet_id, pos = to_position.pop(0)
            
            if storylet_id in positioned:
                continue
            
            # Find a free position near the suggested position
            final_pos = self._find_free_position(pos)
            self._place_storylet(storylet_id, final_pos)
            positioned.add(storylet_id)
            
            # Find connected storylets and suggest positions for them
            connected = self._get_connected_storylets(storylet_id, storylets, storylet_map)
            for connected_id in connected:
                if connected_id not in positioned:
                    # Suggest a position in a spiral around the current position
                    suggested_pos = self._suggest_nearby_position(final_pos)
                    to_position.append((connected_id, suggested_pos))
        
        return self.storylet_positions
    
    def _find_free_position(self, preferred_pos: Position) -> Position:
        """Find the nearest free position to the preferred position."""
        if preferred_pos not in self.position_storylets:
            return preferred_pos
        
        # Spiral outward to find a free position
        for radius in range(1, 20):  # Max search radius
            for angle in range(0, 360, 45):  # Check 8 directions
                x = preferred_pos.x + int(radius * math.cos(math.radians(angle)))
                y = preferred_pos.y + int(radius * math.sin(math.radians(angle)))
                pos = Position(x, y)
                
                if pos not in self.position_storylets:
                    return pos
        
        # Fallback: use a random nearby position
        import random
        offset = random.randint(-10, 10)
        return Position(preferred_pos.x + offset, preferred_pos.y + offset)
    
    def _suggest_nearby_position(self, center: Position) -> Position:
        """Suggest a position near the center for connected storylets."""
        # Use the 8 cardinal directions for natural placement
        directions = list(DIRECTIONS.values())
        import random
        direction = random.choice(directions)
        
        return Position(center.x + direction.dx, center.y + direction.dy)
    
    def _place_storylet(self, storylet_id: int, position: Position):
        """Place a storylet at a specific position."""
        self.storylet_positions[storylet_id] = position
        self.position_storylets[position] = storylet_id
        
        # Update database
        self.db.execute(text("""
            UPDATE storylets 
            SET spatial_x = :x, spatial_y = :y 
            WHERE id = :id
        """), {"x": position.x, "y": position.y, "id": storylet_id})
        self.db.commit()
    
    def _get_connected_storylets(self, storylet_id: int, storylets: List[Dict], storylet_map: Dict[str, int]) -> List[int]:
        """Get storylets that are connected to the given storylet through choices."""
        connected = []
        
        # Find the storylet data
        storylet_data = None
        for s in storylets:
            if storylet_map.get(s['title']) == storylet_id:
                storylet_data = s
                break
        
        if not storylet_data:
            return connected
        
        # Check choices for location changes
        for choice in storylet_data.get('choices', []):
            choice_set = choice.get('set', {})
            if 'location' in choice_set:
                target_location = choice_set['location']
                
                # Find storylets that require this location
                for s in storylets:
                    if s.get('requires', {}).get('location') == target_location:
                        target_id = storylet_map.get(s['title'])
                        if target_id and target_id not in connected:
                            connected.append(target_id)
        
        return connected
    
    def get_directional_navigation(self, current_storylet_id: int) -> Dict[str, Optional[Dict]]:
        """Get available navigation options in 8 directions from current position."""
        if current_storylet_id not in self.storylet_positions:
            return {direction: None for direction in DIRECTIONS.keys()}
        
        current_pos = self.storylet_positions[current_storylet_id]
        navigation = {}
        
        for direction_name, direction in DIRECTIONS.items():
            target_pos = Position(
                current_pos.x + direction.dx,
                current_pos.y + direction.dy
            )
            
            if target_pos in self.position_storylets:
                target_id = self.position_storylets[target_pos]
                
                # Get storylet details
                cursor = self.db.execute(text("""
                    SELECT id, title, text_template, requires 
                    FROM storylets 
                    WHERE id = :target_id
                """), {"target_id": target_id})
                
                row = cursor.fetchone()
                if row:
                    navigation[direction_name] = {
                        'id': row[0],
                        'title': row[1],
                        'text': row[2][:100] + "..." if len(row[2]) > 100 else row[2],
                        'requires': json.loads(row[3]) if row[3] else {},
                        'symbol': direction.symbol,
                        'position': {'x': target_pos.x, 'y': target_pos.y}
                    }
                else:
                    navigation[direction_name] = None
            else:
                navigation[direction_name] = None
        
        return navigation
    
    def can_move_to_direction(self, current_storylet_id: int, direction: str, player_vars: Dict[str, Any]) -> bool:
        """Check if the player can move in the specified direction."""
        nav_options = self.get_directional_navigation(current_storylet_id)
        target = nav_options.get(direction)
        
        if not target:
            return False
        
        # Check requirements
        requirements = target.get('requires', {})
        return self._check_requirements(requirements, player_vars)
    
    def _check_requirements(self, requirements: Dict[str, Any], player_vars: Dict[str, Any]) -> bool:
        """Check if player variables meet the requirements."""
        for req_key, req_value in requirements.items():
            if req_key not in player_vars:
                return False
            
            player_value = player_vars[req_key]
            
            if isinstance(req_value, dict):
                # Handle operators like {'gte': 5}
                for op, val in req_value.items():
                    if op == 'gte' and player_value < val:
                        return False
                    elif op == 'lte' and player_value > val:
                        return False
                    elif op == 'gt' and player_value <= val:
                        return False
                    elif op == 'lt' and player_value >= val:
                        return False
            else:
                # Direct comparison
                if player_value != req_value:
                    return False
        
        return True
    
    def get_spatial_map_data(self) -> Dict[str, Any]:
        """Get data for rendering a spatial map."""
        storylets = []
        
        for storylet_id, position in self.storylet_positions.items():
            cursor = self.db.execute(text("""
                SELECT title, text_template, requires 
                FROM storylets 
                WHERE id = :storylet_id
            """), {"storylet_id": storylet_id})
            
            row = cursor.fetchone()
            if row:
                storylets.append({
                    'id': storylet_id,
                    'title': row[0],
                    'text': row[1][:50] + "..." if len(row[1]) > 50 else row[1],
                    'requires': json.loads(row[2]) if row[2] else {},
                    'position': {'x': position.x, 'y': position.y}
                })
        
        return {
            'storylets': storylets,
            'bounds': self._calculate_bounds()
        }
    
    def _calculate_bounds(self) -> Dict[str, int]:
        """Calculate the bounds of the spatial map."""
        if not self.storylet_positions:
            return {'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0}
        
        positions = list(self.storylet_positions.values())
        return {
            'min_x': min(pos.x for pos in positions),
            'max_x': max(pos.x for pos in positions),
            'min_y': min(pos.y for pos in positions),
            'max_y': max(pos.y for pos in positions)
        }
