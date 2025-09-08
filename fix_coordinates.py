#!/usr/bin/env python3
"""Fix spatial coordinates for existing storylets."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db
from src.services.spatial_navigator import SpatialNavigator
from src.services.location_mapper import LocationMapper
from sqlalchemy import text
import json

def fix_spatial_coordinates():
    """Assign coordinates to storylets that have locations but no coordinates."""
    print("🔧 Fixing Spatial Coordinates")
    print("=" * 40)
    
    db = next(get_db())
    
    # Get all storylets without coordinates but with locations
    result = db.execute(text("""
        SELECT id, title, requires 
        FROM storylets 
        WHERE (spatial_x IS NULL OR spatial_y IS NULL) 
        AND requires IS NOT NULL 
        AND requires != '{}'
    """))
    
    storylets_to_fix = []
    for row in result.fetchall():
        id_val, title, requires_json = row
        try:
            requires = json.loads(requires_json) if requires_json else {}
        except:
            requires = {}
        
        location = requires.get('location')
        if location:
            storylets_to_fix.append({
                'id': id_val,
                'title': title,
                'requires': requires,
                'choices': [],  # We don't need choices for coordinate assignment
                'weight': 1.0
            })
    
    if not storylets_to_fix:
        print("✅ No storylets need coordinate fixing!")
        return
    
    print(f"🎯 Found {len(storylets_to_fix)} storylets to fix:")
    for s in storylets_to_fix:
        location = s['requires'].get('location', 'None')
        print(f"  - {s['title']} (location: {location})")
    
    # Use LocationMapper to assign coordinates
    mapper = LocationMapper()
    storylets_with_coords = mapper.assign_coordinates_to_storylets(storylets_to_fix)
    
    # Update database with coordinates
    updates_made = 0
    for storylet_data in storylets_with_coords:
        if 'spatial_x' in storylet_data and 'spatial_y' in storylet_data:
            x, y = storylet_data['spatial_x'], storylet_data['spatial_y']
            storylet_id = storylet_data['id']
            
            db.execute(text("""
                UPDATE storylets 
                SET spatial_x = :x, spatial_y = :y 
                WHERE id = :id
            """), {"x": x, "y": y, "id": storylet_id})
            
            print(f"📍 Updated {storylet_data['title']} -> ({x}, {y})")
            updates_made += 1
    
    if updates_made > 0:
        db.commit()
        print(f"\n✅ Successfully updated {updates_made} storylets with coordinates!")
        
        # Test the spatial navigator now
        print(f"\n🧭 Testing spatial navigation after fixes...")
        spatial_nav = SpatialNavigator(db)
        
        print(f"📍 Storylets with positions: {len(spatial_nav.storylet_positions)}")
        
        if spatial_nav.storylet_positions:
            # Test navigation from first storylet
            first_id = list(spatial_nav.storylet_positions.keys())[0]
            nav = spatial_nav.get_directional_navigation(first_id)
            
            available_directions = sum(1 for target in nav.values() if target is not None)
            print(f"🧭 Available directions from storylet {first_id}: {available_directions}/8")
            
            if available_directions > 0:
                print("✅ Compass navigation is now working!")
                for direction, target in nav.items():
                    if target:
                        title = target["title"]
                        pos = target["position"]
                        print(f"  {direction}: {title} at ({pos['x']}, {pos['y']})")
            else:
                print("⚠️ No storylets found in adjacent positions")
        else:
            print("⚠️ No storylets have positions after update")
    else:
        print("⚠️ No updates were made")

if __name__ == "__main__":
    fix_spatial_coordinates()
