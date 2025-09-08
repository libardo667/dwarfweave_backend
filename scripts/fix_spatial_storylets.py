#!/usr/bin/env python3
"""
Quick fix to add location requirements to existing storylets for spatial navigation.
"""

import json
from src.database import SessionLocal
from src.models import Storylet

def fix_spatial_storylets():
    """Add location requirements to storylets to enable spatial navigation."""
    
    with SessionLocal() as db:
        storylets = db.query(Storylet).all()
        print(f"Found {len(storylets)} storylets")
        
        # Define some locations
        locations = [
            "Abyss", "Deep Forest", "Mountain Peak", "Crystal Cave", 
            "Ancient Ruins", "Mystic Grove", "Shadow Realm", "Light Temple"
        ]
        
        location_assignments = {}
        
        # Assign locations based on storylet themes/titles
        for i, storylet in enumerate(storylets):
            title_lower = storylet.title.lower()
            
            # Try to assign based on keywords in title
            if any(word in title_lower for word in ['abyss', 'void', 'dark', 'shadow']):
                location = "Abyss"
            elif any(word in title_lower for word in ['forest', 'tree', 'green', 'nature']):
                location = "Deep Forest"
            elif any(word in title_lower for word in ['mountain', 'peak', 'high', 'summit']):
                location = "Mountain Peak"
            elif any(word in title_lower for word in ['crystal', 'gem', 'cave', 'underground']):
                location = "Crystal Cave"
            elif any(word in title_lower for word in ['ancient', 'old', 'ruin', 'past']):
                location = "Ancient Ruins"
            elif any(word in title_lower for word in ['mystic', 'magic', 'grove', 'sacred']):
                location = "Mystic Grove"
            elif any(word in title_lower for word in ['shadow', 'shade', 'phantom']):
                location = "Shadow Realm"
            elif any(word in title_lower for word in ['light', 'temple', 'holy', 'divine']):
                location = "Light Temple"
            else:
                # Distribute remaining storylets evenly
                location = locations[i % len(locations)]
            
            location_assignments[storylet.id] = location
            
            # Update the storylet's requires field
            current_requires = storylet.requires or {}
            if isinstance(current_requires, str):
                current_requires = json.loads(current_requires)
            
            current_requires['location'] = location
            storylet.requires = current_requires
            
            print(f"  {storylet.id}: {storylet.title[:40]}... -> {location}")
        
        # Add some basic choices that connect locations
        choice_connections = [
            ("Abyss", "Deep Forest", "Escape to the forest"),
            ("Deep Forest", "Mountain Peak", "Climb the mountain"),
            ("Mountain Peak", "Crystal Cave", "Descend into the cave"),
            ("Crystal Cave", "Ancient Ruins", "Explore the ruins"),
            ("Ancient Ruins", "Mystic Grove", "Enter the sacred grove"),
            ("Mystic Grove", "Shadow Realm", "Step into shadows"),
            ("Shadow Realm", "Light Temple", "Seek the light"),
            ("Light Temple", "Abyss", "Return to the depths"),
        ]
        
        # Add reverse connections too
        for source, target, label in choice_connections[:]:
            choice_connections.append((target, source, f"Return to {source}"))
        
        # Update storylets with connecting choices
        for source_loc, target_loc, choice_label in choice_connections:
            # Find a storylet in the source location
            source_storylets = [s for s in storylets 
                              if location_assignments.get(s.id) == source_loc]
            
            if source_storylets:
                storylet = source_storylets[0]  # Use first matching storylet
                
                current_choices = storylet.choices or []
                if isinstance(current_choices, str):
                    current_choices = json.loads(current_choices)
                
                # Add choice that sets location to target
                new_choice = {
                    "label": choice_label,
                    "set": {"location": target_loc}
                }
                
                # Only add if not already present
                if not any(c.get('label') == choice_label for c in current_choices):
                    current_choices.append(new_choice)
                    storylet.choices = current_choices
                    print(f"  Added choice: {storylet.title[:30]}... -> '{choice_label}' -> {target_loc}")
        
        # Commit changes
        db.commit()
        print(f"\n✅ Updated {len(storylets)} storylets with location requirements")
        print("🔗 Added spatial connections between locations")
        print("\n🗺️ Run the spatial map generator again to see the connections!")

if __name__ == "__main__":
    fix_spatial_storylets()
