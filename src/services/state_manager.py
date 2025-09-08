"""
Advanced State Management System for WorldWeaver

This module provides sophisticated state tracking capabilities inspired by
successful Twine games like "The Play" (relationships), "Hallowmoor" (inventory),
and environmental storytelling techniques.
"""

from typing import Any, Dict, List, Optional, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class StateChangeType(Enum):
    """Types of state changes for tracking and rollback."""
    SET = "set"
    INCREMENT = "increment" 
    DECREMENT = "decrement"
    APPEND = "append"
    REMOVE = "remove"
    RELATIONSHIP_CHANGE = "relationship_change"
    ITEM_ADD = "item_add"
    ITEM_REMOVE = "item_remove"
    ITEM_MODIFY = "item_modify"


@dataclass
class StateChange:
    """Records a single state change for history tracking."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    change_type: StateChangeType = StateChangeType.SET
    variable: str = ""
    old_value: Any = None
    new_value: Any = None
    context: Dict[str, Any] = field(default_factory=dict)
    storylet_id: Optional[int] = None


@dataclass 
class ItemState:
    """Enhanced item representation with multiple states and properties."""
    id: str
    name: str
    description: str = ""
    quantity: int = 1
    condition: str = "good"  # good, worn, broken, magical, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    location: Optional[str] = None  # where item is stored
    last_used: Optional[datetime] = None
    discovered_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    
    def can_combine_with(self, other: 'ItemState') -> bool:
        """Check if this item can be combined with another."""
        # Basic combination rules - can be extended
        combinable_with = self.properties.get('combinable_with', [])
        return other.id in combinable_with or other.name in combinable_with
    
    def get_available_actions(self, context: Dict[str, Any]) -> List[str]:
        """Get list of actions available with this item in current context."""
        actions = ['examine', 'drop']
        
        # Context-sensitive actions
        location = context.get('location', '')
        if self.properties.get('consumable', False):
            actions.append('use')
        if self.properties.get('equippable', False):
            actions.append('equip')
        if location == 'workshop' and self.properties.get('craftable', False):
            actions.append('craft')
            
        return actions


@dataclass
class RelationshipState:
    """Complex relationship tracking between entities."""
    entity_a: str
    entity_b: str
    trust: float = 0.0      # -100 to 100
    fear: float = 0.0       # 0 to 100  
    attraction: float = 0.0  # -100 to 100
    respect: float = 0.0    # -100 to 100
    familiarity: float = 0.0 # 0 to 100
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    memory_fragments: List[str] = field(default_factory=list)
    
    def get_overall_disposition(self) -> str:
        """Calculate overall relationship disposition."""
        total = self.trust + self.respect + self.attraction - self.fear
        if total > 150: return "devoted"
        elif total > 100: return "friendly" 
        elif total > 50: return "positive"
        elif total > -50: return "neutral"
        elif total > -100: return "hostile"
        else: return "enemy"
    
    def add_memory(self, memory: str, max_memories: int = 10):
        """Add a memory fragment, keeping only recent ones."""
        self.memory_fragments.append(memory)
        if len(self.memory_fragments) > max_memories:
            self.memory_fragments.pop(0)
    
    def update(self, changes: Dict[str, float], memory: Optional[str] = None):
        """Update relationship attributes in batch."""
        for attr, value in changes.items():
            if hasattr(self, attr):
                current = getattr(self, attr)
                setattr(self, attr, current + value)
        
        self.interaction_count += 1
        self.last_interaction = datetime.utcnow()
        
        if memory:
            self.add_memory(memory)


@dataclass
class EnvironmentalState:
    """Environmental factors that affect gameplay."""
    time_of_day: str = "morning"  # morning, afternoon, evening, night
    weather: str = "clear"        # clear, cloudy, rainy, stormy, snowy
    season: str = "spring"        # spring, summer, autumn, winter
    temperature: int = 20         # Celsius
    danger_level: int = 0         # 0-10 scale
    noise_level: int = 0          # 0-10 scale  
    lighting: str = "bright"      # dark, dim, bright, brilliant
    air_quality: str = "fresh"    # fresh, stale, toxic, magical
    
    def get_mood_modifier(self) -> Dict[str, float]:
        """Get mood modifiers based on environment."""
        modifiers = {}
        
        # Weather effects
        if self.weather == "rainy":
            modifiers['melancholy'] = 0.2
        elif self.weather == "stormy": 
            modifiers['tension'] = 0.3
        elif self.weather == "clear":
            modifiers['optimism'] = 0.1
            
        # Time effects
        if self.time_of_day == "night":
            modifiers['fear'] = 0.1
            modifiers['mystery'] = 0.2
        elif self.time_of_day == "morning":
            modifiers['energy'] = 0.1
            
        return modifiers
    
    def update(self, changes: Dict[str, Any]):
        """Update environmental attributes in batch."""
        for attr, value in changes.items():
            if hasattr(self, attr):
                setattr(self, attr, value)


class AdvancedStateManager:
    """
    Sophisticated state management system that tracks:
    - Complex variable relationships
    - Multi-dimensional inventory
    - NPC relationships and memories
    - Environmental conditions
    - State change history
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.variables: Dict[str, Any] = {}
        self.inventory: Dict[str, ItemState] = {}
        self.relationships: Dict[str, RelationshipState] = {}
        self.environment = EnvironmentalState()
        self.change_history: List[StateChange] = []
        self.context_stack: List[Dict[str, Any]] = []
        
        # Performance optimization: cache frequently accessed computations
        self._cached_computations: Dict[str, Any] = {}
        self._cache_expiry: datetime = datetime.utcnow()
        
    def set_variable(self, key: str, value: Any, context: Optional[Dict[str, Any]] = None, 
                    storylet_id: Optional[int] = None) -> Any:
        """Set a variable with full history tracking."""
        old_value = self.variables.get(key)
        
        # Record the change
        change = StateChange(
            change_type=StateChangeType.SET,
            variable=key,
            old_value=old_value,
            new_value=value,
            context=context or {},
            storylet_id=storylet_id
        )
        self.change_history.append(change)
        
        # Apply the change
        self.variables[key] = value
        self._invalidate_cache()
        
        logger.debug(f"Variable '{key}' changed from {old_value} to {value}")
        return value
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a variable value with optional default."""
        return self.variables.get(key, default)
    
    def increment_variable(self, key: str, amount: Union[int, float] = 1, 
                          context: Optional[Dict[str, Any]] = None, storylet_id: Optional[int] = None) -> Any:
        """Increment a numeric variable."""
        current = self.variables.get(key, 0)
        new_value = current + amount
        
        change = StateChange(
            change_type=StateChangeType.INCREMENT,
            variable=key,
            old_value=current,
            new_value=new_value,
            context=context or {},
            storylet_id=storylet_id
        )
        self.change_history.append(change)
        
        self.variables[key] = new_value
        self._invalidate_cache()
        return new_value
    
    def add_item(self, item_id: str, name: str, quantity: int = 1, 
                properties: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> ItemState:
        """Add an item to inventory with full state tracking."""
        if item_id in self.inventory:
            # Item exists, increase quantity
            self.inventory[item_id].quantity += quantity
            item = self.inventory[item_id]
        else:
            # New item
            item = ItemState(
                id=item_id,
                name=name,
                quantity=quantity,
                properties=properties or {}
            )
            self.inventory[item_id] = item
        
        change = StateChange(
            change_type=StateChangeType.ITEM_ADD,
            variable=f"inventory.{item_id}",
            old_value=None,
            new_value=item,
            context=context or {},
        )
        self.change_history.append(change)
        
        logger.debug(f"Added {quantity}x {name} to inventory")
        return item
    
    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """Remove items from inventory. Returns True if any items were removed."""
        if item_id not in self.inventory:
            return False
            
        item = self.inventory[item_id]
        original_quantity = item.quantity
        
        # Allow removing more than available (remove all)
        actual_removed = min(quantity, item.quantity)
        
        old_item = ItemState(**item.__dict__)  # Copy for history
        
        item.quantity -= actual_removed
        if item.quantity <= 0:
            del self.inventory[item_id]
            
        change = StateChange(
            change_type=StateChangeType.ITEM_REMOVE,
            variable=f"inventory.{item_id}",
            old_value=old_item,
            new_value=item if item.quantity > 0 else None,
        )
        self.change_history.append(change)
        
        logger.debug(f"Removed {actual_removed}x {item.name} from inventory")
        return True
    
    def update_relationship(self, entity_a: str, entity_b: str, 
                          changes: Dict[str, float], memory: Optional[str] = None) -> RelationshipState:
        """Update relationship between two entities."""
        # Create a standardized relationship key (alphabetical order)
        rel_key = f"{min(entity_a, entity_b)}:{max(entity_a, entity_b)}"
        
        if rel_key not in self.relationships:
            self.relationships[rel_key] = RelationshipState(entity_a, entity_b)
            
        rel = self.relationships[rel_key]
        old_state = RelationshipState(**rel.__dict__)  # Copy for history
        
        # Apply changes
        for attribute, change_amount in changes.items():
            if hasattr(rel, attribute):
                current_value = getattr(rel, attribute)
                new_value = max(-100, min(100, current_value + change_amount))  # Clamp to -100/100
                setattr(rel, attribute, new_value)
        
        rel.last_interaction = datetime.utcnow()
        rel.interaction_count += 1
        
        if memory:
            rel.add_memory(memory)
            
        change = StateChange(
            change_type=StateChangeType.RELATIONSHIP_CHANGE,
            variable=f"relationship.{rel_key}",
            old_value=old_state,
            new_value=rel,
        )
        self.change_history.append(change)
        
        logger.debug(f"Updated relationship {entity_a}-{entity_b}: {changes}")
        return rel
    
    def get_relationship(self, entity_a: str, entity_b: str) -> Optional[RelationshipState]:
        """Get relationship between two entities."""
        rel_key = f"{min(entity_a, entity_b)}:{max(entity_a, entity_b)}"
        return self.relationships.get(rel_key)
    
    def update_environment(self, changes: Dict[str, Any]):
        """Update environmental conditions."""
        for key, value in changes.items():
            if hasattr(self.environment, key):
                setattr(self.environment, key, value)
        
        self._invalidate_cache()
        logger.debug(f"Updated environment: {changes}")
    
    def evaluate_condition(self, condition: Dict[str, Any]) -> bool:
        """
        Enhanced condition evaluation supporting:
        - Relationship queries: {'relationship:player:npc': {'trust': {'gte': 50}}}
        - Item queries: {'item:sword': {'condition': 'good', 'quantity': {'gte': 1}}}
        - Environmental queries: {'environment': {'weather': 'rainy'}}
        - Complex combinations
        """
        for key, requirements in condition.items():
            
            # Relationship conditions
            if key.startswith('relationship:'):
                _, entity_a, entity_b = key.split(':')
                rel = self.get_relationship(entity_a, entity_b)
                if not rel:
                    return False
                    
                for attr, req in requirements.items():
                    rel_value = getattr(rel, attr, 0)
                    if not self._check_numeric_condition(rel_value, req):
                        return False
                        
            # Item conditions  
            elif key.startswith('item:'):
                _, item_id = key.split(':', 1)
                item = self.inventory.get(item_id)
                if not item:
                    return False
                    
                for attr, req in requirements.items():
                    if attr == 'quantity':
                        if not self._check_numeric_condition(item.quantity, req):
                            return False
                    elif attr == 'condition':
                        if item.condition != req:
                            return False
                    # Add more item attribute checks as needed
                    
            # Environment conditions
            elif key == 'environment':
                for attr, req in requirements.items():
                    env_value = getattr(self.environment, attr, None)
                    if isinstance(req, dict):
                        if not self._check_numeric_condition(env_value, req):
                            return False
                    elif env_value != req:
                        return False
                        
            # Standard variable conditions (existing logic)
            else:
                var_value = self.variables.get(key)
                
                # Special handling for location requirements
                if key == 'location':
                    # Handle flexible location values that should match any location
                    if requirements in ['any_realm', 'any_location', 'anywhere']:
                        # These are flexible location requirements that match any current location
                        continue  # Skip this requirement - it's satisfied
                    elif requirements == 'in_vessel' and var_value in ['start', 'vessel', 'ship', 'craft']:
                        # 'in_vessel' matches vessel-related locations  
                        continue
                    elif var_value == requirements:
                        # Exact location match
                        continue
                    else:
                        # Location requirement not met
                        return False
                elif isinstance(requirements, dict):
                    if not self._check_numeric_condition(var_value, requirements):
                        return False
                else:
                    # For simple numeric comparisons, treat as >= comparison
                    if isinstance(requirements, (int, float)) and isinstance(var_value, (int, float)):
                        if var_value < requirements:
                            return False
                    elif var_value != requirements:
                        return False
                    
        return True
    
    def _check_numeric_condition(self, value: Any, condition: Union[Dict[str, Any], Any]) -> bool:
        """Check numeric conditions like {'gte': 5, 'lt': 10}."""
        if not isinstance(condition, dict):
            return value == condition
            
        for op, target in condition.items():
            if op == 'gte' and not (value is not None and value >= target):
                return False
            elif op == 'gt' and not (value is not None and value > target):
                return False
            elif op == 'lte' and not (value is not None and value <= target):
                return False
            elif op == 'lt' and not (value is not None and value < target):
                return False
            elif op == 'eq' and value != target:
                return False
            elif op == 'ne' and value == target:
                return False
                
        return True
    
    def get_contextual_variables(self) -> Dict[str, Any]:
        """Get all variables plus computed contextual information."""
        cache_key = "contextual_vars"
        if (cache_key in self._cached_computations and 
            datetime.utcnow() < self._cache_expiry):
            return self._cached_computations[cache_key]
        
        # Base variables
        context = dict(self.variables)
        
        # Add computed values
        context['_inventory_count'] = len(self.inventory)
        context['_total_item_quantity'] = sum(item.quantity for item in self.inventory.values())
        context['_relationship_count'] = len(self.relationships)
        context['_time_of_day'] = self.environment.time_of_day
        context['_weather'] = self.environment.weather
        context['_danger_level'] = self.environment.danger_level
        
        # Add non-underscore versions for compatibility
        context['inventory_count'] = len(self.inventory)
        context['total_item_quantity'] = sum(item.quantity for item in self.inventory.values())
        context['relationship_count'] = len(self.relationships)
        context['time_of_day'] = self.environment.time_of_day
        context['weather'] = self.environment.weather
        context['danger_level'] = self.environment.danger_level
        context['inventory_items'] = list(self.inventory.keys())
        context['known_people'] = list(set(rel.entity_a if rel.entity_a != 'player' else rel.entity_b 
                                          for rel in self.relationships.values()))
        
        # Add mood modifiers from environment
        mood_modifiers = self.environment.get_mood_modifier()
        for mood, modifier in mood_modifiers.items():
            context[f'_mood_{mood}'] = modifier
        
        # Cache the result
        self._cached_computations[cache_key] = context
        self._cache_expiry = datetime.utcnow() + timedelta(seconds=30)
        
        return context
    
    def _invalidate_cache(self):
        """Clear cached computations when state changes."""
        self._cached_computations.clear()
        self._cache_expiry = datetime.utcnow()
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of current state."""
        inventory_summary = {
            'total_items': len(self.inventory),
            'total_quantity': sum(item.quantity for item in self.inventory.values()),
            'items': {item_id: {'name': item.name, 'quantity': item.quantity, 'condition': item.condition} 
                     for item_id, item in self.inventory.items()}
        }
        
        relationships_summary = {
            rel_key: {
                'disposition': rel.get_overall_disposition(),
                'trust': rel.trust,
                'respect': rel.respect,
                'interaction_count': rel.interaction_count
            } for rel_key, rel in self.relationships.items()
        }
        
        return {
            'session_id': self.session_id,
            'variables': self.variables,
            'inventory': inventory_summary,  # Add expected key
            'inventory_summary': inventory_summary,  # Keep for backward compatibility
            'relationships': relationships_summary,  # Add expected key
            'relationships_summary': relationships_summary,  # Keep for backward compatibility
            'environment': {
                'time_of_day': self.environment.time_of_day,
                'weather': self.environment.weather,
                'danger_level': self.environment.danger_level,
                'mood_modifiers': self.environment.get_mood_modifier()
            },
            'stats': {
                'total_variables': len(self.variables),
                'total_items': len(self.inventory),
                'total_relationships': len(self.relationships)
            },
            'recent_changes': len([c for c in self.change_history 
                                 if c.timestamp > datetime.utcnow() - timedelta(minutes=5)])
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export complete state for saving/serialization."""
        return {
            'session_id': self.session_id,
            'variables': self.variables,
            'inventory': {item_id: item.__dict__ for item_id, item in self.inventory.items()},
            'relationships': {rel_key: rel.__dict__ for rel_key, rel in self.relationships.items()},
            'environment': self.environment.__dict__,
            'change_history': [change.__dict__ for change in self.change_history[-100:]]  # Keep last 100 changes
        }
    
    def import_state(self, state_data: Dict[str, Any]):
        """Import state from saved data."""
        self.session_id = state_data.get('session_id', self.session_id)
        self.variables = state_data.get('variables', {})
        
        # Reconstruct inventory
        self.inventory = {}
        for item_id, item_data in state_data.get('inventory', {}).items():
            self.inventory[item_id] = ItemState(**item_data)
        
        # Reconstruct relationships
        self.relationships = {}
        for rel_key, rel_data in state_data.get('relationships', {}).items():
            self.relationships[rel_key] = RelationshipState(**rel_data)
        
        # Reconstruct environment
        if 'environment' in state_data:
            self.environment = EnvironmentalState(**state_data['environment'])
        
        # Reconstruct change history
        self.change_history = []
        for change_data in state_data.get('change_history', []):
            change_data['timestamp'] = datetime.fromisoformat(change_data['timestamp'])
            change_data['change_type'] = StateChangeType(change_data['change_type'])
            self.change_history.append(StateChange(**change_data))
        
        self._invalidate_cache()
        logger.info(f"Imported state for session {self.session_id}")
