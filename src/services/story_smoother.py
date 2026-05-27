"""
Story Smoothing Algorithm
Automatically detects and fixes narrative flow problems in storylet graphs.
"""

import sqlite3
import json
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
import random
import os


class StorySmoother:
    """
    Recursive story graph analyzer and fixer.
    Detects isolated locations, dead-end variables, and navigation bottlenecks,
    then automatically generates fixes.
    """
    
    def __init__(self, db_path: str = 'dwarfweave.db'):
        from .db_path import resolve_db_path
        self.db_path = resolve_db_path(db_path)
        self.storylets = []
        self.locations = set()
        self.location_storylets = defaultdict(list)
        self.location_connections = defaultdict(set)
        self.reverse_connections = defaultdict(set)
        self.variables_required = defaultdict(list)  # var -> storylets that need it
        self.variables_set = defaultdict(list)       # var -> storylets that set it
        self.dead_end_vars = set()
        self.isolated_locations = set()
        self.one_way_connections = set()
        
    def load_storylets(self):
        """Load all storylets from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, text_template, requires, choices, weight 
            FROM storylets
        """)
        
        self.storylets = []
        for row in cursor.fetchall():
            storylet = {
                'id': row[0],
                'title': row[1],
                'text': row[2],
                'requires': json.loads(row[3]) if row[3] else {},
                'choices': json.loads(row[4]) if row[4] else [],
                'weight': row[5]
            }
            self.storylets.append(storylet)
        
        conn.close()
        print(f"📚 Loaded {len(self.storylets)} storylets")
    
    def analyze_graph(self):
        """Analyze the storylet graph for problems."""
        print("🔍 Analyzing storylet graph...")
        
        # Reset analysis data
        self.locations.clear()
        self.location_storylets.clear()
        self.location_connections.clear()
        self.reverse_connections.clear()
        self.variables_required.clear()
        self.variables_set.clear()
        
        # Analyze each storylet
        for storylet in self.storylets:
            # Extract location
            location = storylet['requires'].get('location', 'No Location')
            self.locations.add(location)
            self.location_storylets[location].append(storylet)
            
            # Track variable requirements
            for var, value in storylet['requires'].items():
                if var != 'location':
                    self.variables_required[var].append(storylet)
            
            # Analyze choices for connections and variable setting
            for choice in storylet['choices']:
                choice_sets = choice.get('set', {})
                
                # Track variables being set
                for var, value in choice_sets.items():
                    if var != 'location':
                        self.variables_set[var].append((storylet, choice))
                
                # Track location connections
                new_location = choice_sets.get('location')
                if new_location and new_location != location:
                    self.location_connections[location].add(new_location)
                    self.reverse_connections[new_location].add(location)
        
        self._identify_problems()
    
    def _identify_problems(self):
        """Identify specific problems in the story graph."""
        # Find dead-end variables
        all_set_vars = set(self.variables_set.keys())
        all_required_vars = set(self.variables_required.keys())
        self.dead_end_vars = all_set_vars - all_required_vars
        
        # Find isolated locations (no incoming or outgoing connections)
        self.isolated_locations = set()
        for location in self.locations:
            has_outgoing = len(self.location_connections[location]) > 0
            has_incoming = len(self.reverse_connections[location]) > 0
            
            if not has_outgoing and not has_incoming and location != 'No Location':
                self.isolated_locations.add(location)
        
        # Find one-way connections
        self.one_way_connections = set()
        for from_loc, to_locs in self.location_connections.items():
            for to_loc in to_locs:
                if from_loc not in self.location_connections.get(to_loc, set()):
                    self.one_way_connections.add((from_loc, to_loc))
        
        print(f"⚠️  Found {len(self.dead_end_vars)} dead-end variables")
        print(f"🏝️ Found {len(self.isolated_locations)} isolated locations")
        print(f"➡️  Found {len(self.one_way_connections)} one-way connections")
    
    def generate_exit_choices(self, storylet: Dict, target_locations: List[str]) -> List[Dict]:
        """Generate exit choices for a storylet to connect it to other locations."""
        exit_choices = []
        
        current_location = storylet['requires'].get('location', 'No Location')
        
        for target_location in target_locations:
            if target_location != current_location:
                # Generate thematic choice text based on locations
                choice_text = self._generate_travel_text(current_location, target_location)
                
                exit_choice = {
                    "text": choice_text,
                    "set": {"location": target_location},
                    "condition": None
                }
                exit_choices.append(exit_choice)
        
        return exit_choices
    
    def _generate_travel_text(self, from_loc: str, to_loc: str) -> str:
        """Generic, world-agnostic travel text between locations."""
        generic_travels = [
            f"Travel to {to_loc}",
            f"Journey toward {to_loc}",
            f"Head to {to_loc}",
            f"Move to {to_loc}",
            f"Explore {to_loc}",
        ]
        return random.choice(generic_travels)

    def generate_variable_requirement_storylets(self) -> List[Dict]:
        """Generate new storylets that require the dead-end variables."""
        new_storylets = []
        
        for var in self.dead_end_vars:
            # Find where this variable is set to understand its purpose
            setting_storylets = self.variables_set[var]
            if not setting_storylets:
                continue
            
            # Analyze the variable to create thematic requirements
            storylet_title, storylet_text = self._generate_variable_storylet(var, setting_storylets)
            
            # Choose a location that makes sense for this variable
            target_location = self._choose_location_for_variable(var)
            
            new_storylet = {
                'title': storylet_title,
                'text_template': storylet_text,
                'requires': {
                    'location': target_location,
                    var: 1  # Require the variable to be set
                },
                'choices': [
                    {
                        "text": "Continue your journey",
                        "set": {},
                        "condition": None
                    }
                ],
                'weight': 1.0
            }
            
            new_storylets.append(new_storylet)
            print(f"📝 Generated storylet requiring '{var}' in {target_location}")
        
        return new_storylets
    
    def _generate_variable_storylet(self, var: str, setting_info: List[Tuple]) -> Tuple[str, str]:
        """Generic storylet content derived from the variable name (no baked-in worlds)."""
        title = f'{var.replace("_", " ").title()} Advantage'
        text = f'Your {var.replace("_", " ")} proves beneficial in this situation.'
        return title, text

    def _choose_location_for_variable(self, var: str) -> str:
        """Pick an existing location for a variable-dependent storylet (never invents one)."""
        available_locations = list(self.locations - {'No Location'})
        return random.choice(available_locations) if available_locations else 'No Location'

    def fix_spatial_integration(self, dry_run: bool = False) -> Dict:
        """Place 'No Location' storylets into the world's EXISTING locations and connect
        locations with movement choices.

        World-agnostic (item 03): never invents named locations — it heals whatever world
        it is given instead of importing a foreign one.
        """
        print("Fixing spatial integration...")

        fixes_applied = {'locations_assigned': 0, 'connections_created': 0, 'modified_storylets': []}

        no_location_storylets = [s for s in self.storylets
                                 if s['requires'].get('location', 'No Location') == 'No Location']
        if not no_location_storylets:
            return fixes_applied

        existing_locations = list(self.locations - {'No Location'})
        if not existing_locations:
            # We do not invent locations, so there is nothing to anchor these to.
            return fixes_applied

        for i, storylet in enumerate(no_location_storylets):
            location = existing_locations[i % len(existing_locations)]
            storylet['requires']['location'] = location
            if not dry_run:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE storylets SET requires = ? WHERE id = ?",
                               (json.dumps(storylet['requires']), storylet['id']))
                conn.commit()
                conn.close()
            fixes_applied['locations_assigned'] += 1
            fixes_applied['modified_storylets'].append(storylet['id'])

        # Create movement connections among existing locations.
        if fixes_applied['locations_assigned'] > 0:
            self.load_storylets()
            self.analyze_graph()
            locations = list(self.locations - {'No Location'})
            for location in locations:
                storylets_in_location = self.location_storylets[location]
                if not storylets_in_location:
                    continue
                representative = storylets_in_location[0]
                other_locations = [loc for loc in locations if loc != location]
                nearby_locations = random.sample(other_locations, min(3, len(other_locations)))
                for target_location in nearby_locations:
                    representative['choices'].append({
                        "text": f"Travel to {target_location}",
                        "set": {"location": target_location},
                        "condition": None,
                    })
                    fixes_applied['connections_created'] += 1
                if not dry_run and nearby_locations:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE storylets SET choices = ? WHERE id = ?",
                                   (json.dumps(representative['choices']), representative['id']))
                    conn.commit()
                    conn.close()
                    if representative['id'] not in fixes_applied['modified_storylets']:
                        fixes_applied['modified_storylets'].append(representative['id'])

        return fixes_applied

    def smooth_story(self, dry_run: bool = False) -> Dict:
        """
        Main smoothing algorithm - recursively fix story problems.
        """
        print("🔧 Starting story smoothing algorithm...")
        
        # Load and analyze current state
        self.load_storylets()
        self.analyze_graph()
        
        fixes_applied = {
            'exit_choices_added': 0,
            'variable_storylets_created': 0,
            'bidirectional_connections': 0,
            'spatial_locations_assigned': 0,
            'spatial_connections_created': 0,
            'modified_storylets': []
        }
        
        if dry_run:
            print("🧪 DRY RUN MODE - No changes will be saved")
        
        # NEW: Fix spatial integration issues first
        spatial_fixes = self.fix_spatial_integration(dry_run)
        fixes_applied['spatial_locations_assigned'] = spatial_fixes['locations_assigned']
        fixes_applied['spatial_connections_created'] = spatial_fixes['connections_created']
        fixes_applied['modified_storylets'].extend(spatial_fixes['modified_storylets'])
        
        # Reload and re-analyze after spatial fixes
        if spatial_fixes['locations_assigned'] > 0 or spatial_fixes['connections_created'] > 0:
            self.load_storylets()
            self.analyze_graph()
        
        # Fix 1: Add exit choices to isolated locations
        for location in self.isolated_locations:
            storylets_in_location = self.location_storylets[location]
            
            for storylet in storylets_in_location:
                # Find nearby locations to connect to
                other_locations = list(self.locations - {location, 'No Location'})[:2]
                
                if other_locations:
                    new_choices = self.generate_exit_choices(storylet, other_locations)
                    
                    if not dry_run:
                        self._update_storylet_choices(storylet['id'], storylet['choices'] + new_choices)
                    
                    fixes_applied['exit_choices_added'] += len(new_choices)
                    fixes_applied['modified_storylets'].append(storylet['id'])
                    
                    print(f"✅ Added {len(new_choices)} exit choices to '{storylet['title']}'")
        
        # Fix 2: Create storylets that require dead-end variables
        if self.dead_end_vars:
            new_storylets = self.generate_variable_requirement_storylets()
            
            if not dry_run:
                for new_storylet in new_storylets:
                    self._insert_storylet(new_storylet)
            
            fixes_applied['variable_storylets_created'] = len(new_storylets)
        
        # Fix 3: Add return paths for one-way connections
        for from_loc, to_loc in self.one_way_connections:
            # Find a storylet in to_loc to add a return path
            target_storylets = self.location_storylets[to_loc]
            
            if target_storylets:
                storylet = target_storylets[0]  # Pick first storylet
                return_choice = {
                    "text": f"Return to {from_loc}",
                    "set": {"location": from_loc},
                    "condition": None
                }
                
                if not dry_run:
                    updated_choices = storylet['choices'] + [return_choice]
                    self._update_storylet_choices(storylet['id'], updated_choices)
                
                fixes_applied['bidirectional_connections'] += 1
                fixes_applied['modified_storylets'].append(storylet['id'])
                
                print(f"🔄 Added return path from {to_loc} to {from_loc}")
        
        # Calculate total fixes (excluding the list of modified storylets)
        total_fixes = (fixes_applied['exit_choices_added'] + 
                      fixes_applied['variable_storylets_created'] + 
                      fixes_applied['bidirectional_connections'] +
                      fixes_applied['spatial_locations_assigned'] +
                      fixes_applied['spatial_connections_created'])
        
        print(f"🎉 Story smoothing complete! Applied {total_fixes} fixes")
        return fixes_applied
    
    def _update_storylet_choices(self, storylet_id: int, new_choices: List[Dict]):
        """Update a storylet's choices in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE storylets 
            SET choices = ? 
            WHERE id = ?
        """, (json.dumps(new_choices), storylet_id))
        
        conn.commit()
        conn.close()
    
    def _insert_storylet(self, storylet: Dict):
        """Insert a new storylet into the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO storylets (title, text_template, requires, choices, weight, origin)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            storylet['title'],
            storylet['text_template'],
            json.dumps(storylet['requires']),
            json.dumps(storylet['choices']),
            storylet['weight'],
            storylet.get('origin', 'inferred')
        ))
        
        # Get the ID of the newly inserted storylet
        new_storylet_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Auto-assign spatial coordinates if the storylet has a location
        if new_storylet_id is not None:
            try:
                from sqlalchemy.orm import sessionmaker
                from ..database import engine
                Session = sessionmaker(bind=engine)
                db_session = Session()
                
                from .spatial_navigator import SpatialNavigator
                updates = SpatialNavigator.auto_assign_coordinates(db_session, [new_storylet_id])
                if updates > 0:
                    print(f"📍 Auto-assigned coordinates to new storylet: {storylet['title']}")
                
                db_session.close()
            except Exception as e:
                print(f"⚠️ Warning: Could not auto-assign coordinates to storylet '{storylet['title']}': {e}")
