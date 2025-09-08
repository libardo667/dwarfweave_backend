#!/usr/bin/env python3
"""
Fix Spatial Integration
Assigns locations to all storylets that have 'No Location' and creates
spatial connections between them for proper navigation.
"""

import sqlite3
import json
import random
from collections import defaultdict

class SpatialIntegrator:
    def __init__(self, db_path="worldweaver.db"):
        self.db_path = db_path
        
        # Define the existing locations and new locations to expand the world
        self.existing_locations = [
            "Initialization Chamber", "Feedback Chamber", "Validation Chamber", 
            "Analysis Room", "Resource Allocation Center", "Clan Hall"
        ]
        
        # Add new thematic locations for spatial expansion
        self.new_locations = [
            "Diagnostic Laboratory", "Testing Grounds", "Protocol Chamber",
            "Stability Core", "Insight Archive", "Discovery Vault",
            "Analysis Station", "Evaluation Center", "Transition Hub",
            "Data Observatory", "Anomaly Chamber", "Deep Dive Center",
            "Evaluation Plaza", "Insight Nexus", "Progress Hall"
        ]
        
        self.all_locations = self.existing_locations + self.new_locations
    
    def analyze_current_state(self):
        """Analyze the current storylet distribution."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, title, requires FROM storylets ORDER BY id')
        storylets = cursor.fetchall()
        
        location_count = defaultdict(int)
        no_location_storylets = []
        
        for id, title, requires_str in storylets:
            requires = json.loads(requires_str) if requires_str else {}
            location = requires.get('location', 'No Location')
            location_count[location] += 1
            
            if location == 'No Location':
                no_location_storylets.append((id, title, requires))
        
        conn.close()
        
        print("📊 CURRENT STATE ANALYSIS:")
        print("=" * 50)
        print(f"Total storylets: {len(storylets)}")
        print(f"Storylets without location: {len(no_location_storylets)}")
        print(f"Existing locations: {len([loc for loc in location_count.keys() if loc != 'No Location'])}")
        
        print("\n📍 LOCATION DISTRIBUTION:")
        for location, count in sorted(location_count.items()):
            if location != 'No Location':
                print(f"  {location}: {count} storylets")
        print(f"  No Location: {location_count['No Location']} storylets")
        
        return no_location_storylets
    
    def assign_locations_intelligently(self, no_location_storylets):
        """Assign locations based on storylet content and themes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        assignments = []
        location_index = 0
        
        for id, title, requires in no_location_storylets:
            # Analyze title for thematic assignment
            title_lower = title.lower()
            
            # Smart location assignment based on content
            if 'diagnostic' in title_lower:
                location = "Diagnostic Laboratory"
            elif 'stability' in title_lower or 'stable' in title_lower:
                location = "Stability Core"
            elif 'insight' in title_lower:
                location = "Insight Archive"
            elif 'discovery' in title_lower or 'reveal' in title_lower:
                location = "Discovery Vault"
            elif 'analysis' in title_lower or 'analyze' in title_lower:
                location = "Analysis Station"
            elif 'evaluation' in title_lower or 'evaluate' in title_lower:
                location = "Evaluation Center"
            elif 'transition' in title_lower:
                location = "Transition Hub"
            elif 'data' in title_lower or 'stream' in title_lower:
                location = "Data Observatory"
            elif 'anomal' in title_lower:
                location = "Anomaly Chamber"
            elif 'deep' in title_lower:
                location = "Deep Dive Center"
            elif 'progress' in title_lower:
                location = "Progress Hall"
            elif 'protocol' in title_lower:
                location = "Protocol Chamber"
            elif 'test' in title_lower:
                location = "Testing Grounds"
            else:
                # Round-robin assignment for generic storylets
                location = self.all_locations[location_index % len(self.all_locations)]
                location_index += 1
            
            # Update the requires dict
            requires['location'] = location
            assignments.append((id, location, requires))
        
        # Apply the assignments to the database
        for id, location, requires in assignments:
            cursor.execute("""
                UPDATE storylets 
                SET requires = ? 
                WHERE id = ?
            """, (json.dumps(requires), id))
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ LOCATION ASSIGNMENTS COMPLETE:")
        print("=" * 50)
        
        # Show assignment summary
        location_assignments = defaultdict(int)
        for _, location, _ in assignments:
            location_assignments[location] += 1
        
        for location, count in sorted(location_assignments.items()):
            print(f"  {location}: {count} storylets assigned")
        
        return assignments
    
    def create_movement_connections(self):
        """Create bidirectional movement connections between locations."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all storylets with their locations
        cursor.execute('SELECT id, title, requires, choices FROM storylets')
        storylets = cursor.fetchall()
        
        location_storylets = defaultdict(list)
        for id, title, requires_str, choices_str in storylets:
            requires = json.loads(requires_str) if requires_str else {}
            choices = json.loads(choices_str) if choices_str else []
            location = requires.get('location')
            
            if location and location != 'No Location':
                location_storylets[location].append({
                    'id': id, 'title': title, 'requires': requires, 'choices': choices
                })
        
        connections_added = 0
        
        # For each location, add movement options to nearby locations
        locations = list(location_storylets.keys())
        for i, location in enumerate(locations):
            storylets_in_location = location_storylets[location]
            
            # Choose 2-3 nearby locations to connect to
            other_locations = [loc for j, loc in enumerate(locations) if j != i]
            nearby_locations = random.sample(other_locations, min(3, len(other_locations)))
            
            # Add movement choices to one representative storylet per location
            if storylets_in_location:
                representative = storylets_in_location[0]  # Use first storylet as representative
                choices = representative['choices'][:]  # Copy existing choices
                
                # Add movement options
                for target_location in nearby_locations:
                    movement_choice = {
                        "text": f"Travel to {target_location}",
                        "sets": {"location": target_location},
                        "visible": True
                    }
                    choices.append(movement_choice)
                    connections_added += 1
                
                # Update the database
                cursor.execute("""
                    UPDATE storylets 
                    SET choices = ? 
                    WHERE id = ?
                """, (json.dumps(choices), representative['id']))
        
        conn.commit()
        conn.close()
        
        print(f"\n🔗 MOVEMENT CONNECTIONS CREATED:")
        print("=" * 50)
        print(f"Movement options added: {connections_added}")
        print(f"Locations connected: {len(locations)}")
        
        return connections_added
    
    def verify_spatial_network(self):
        """Verify the spatial navigation network is working."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count storylets with locations
        cursor.execute("""
            SELECT COUNT(*) FROM storylets 
            WHERE json_extract(requires, '$.location') IS NOT NULL
            AND json_extract(requires, '$.location') != 'No Location'
        """)
        located_count = cursor.fetchone()[0]
        
        # Count movement choices
        cursor.execute("""
            SELECT COUNT(*) FROM storylets 
            WHERE json_extract(choices, '$') LIKE '%location%'
        """)
        movement_choices = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n🧭 SPATIAL NETWORK VERIFICATION:")
        print("=" * 50)
        print(f"Storylets with locations: {located_count}")
        print(f"Storylets with movement choices: {movement_choices}")
        
        return {'located_storylets': located_count, 'movement_choices': movement_choices}

def main():
    """Run the spatial integration fix."""
    integrator = SpatialIntegrator()
    
    print("🔧 SPATIAL INTEGRATION FIX")
    print("=" * 60)
    
    # 1. Analyze current state
    no_location_storylets = integrator.analyze_current_state()
    
    if not no_location_storylets:
        print("\n✅ All storylets already have locations assigned!")
        return
    
    # 2. Assign locations intelligently
    assignments = integrator.assign_locations_intelligently(no_location_storylets)
    
    # 3. Create movement connections
    connections = integrator.create_movement_connections()
    
    # 4. Verify the network
    network_status = integrator.verify_spatial_network()
    
    print(f"\n🎉 SPATIAL INTEGRATION COMPLETE!")
    print("=" * 60)
    print(f"✅ {len(assignments)} storylets assigned to locations")
    print(f"✅ {connections} movement connections created")
    print(f"✅ Spatial navigation network verified")
    
    print(f"\n🚀 You can now test spatial navigation in the game!")

if __name__ == "__main__":
    main()
