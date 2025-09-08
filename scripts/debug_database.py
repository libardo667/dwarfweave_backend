#!/usr/bin/env python3
"""Debug database state for spatial analysis."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db
from sqlalchemy import text
import json

def debug_database_state():
    """Check the current state of storylets in the database."""
    print("📊 Database State Analysis")
    print("=" * 40)
    
    db = next(get_db())
    result = db.execute(text('SELECT id, title, spatial_x, spatial_y, requires FROM storylets'))
    
    print("📚 All storylets:")
    storylets_with_coords = 0
    storylets_with_locations = 0
    
    for row in result.fetchall():
        id_val, title, x, y, requires_json = row
        
        # Parse requires
        try:
            requires = json.loads(requires_json) if requires_json else {}
        except:
            requires = {}
        
        location = requires.get('location', 'None')
        coords_str = f"({x}, {y})" if x is not None and y is not None else "None"
        
        print(f"  ID {id_val:2}: {title[:30]:30} | Coords: {coords_str:8} | Location: {location}")
        
        if x is not None and y is not None:
            storylets_with_coords += 1
        if location != 'None':
            storylets_with_locations += 1
    
    print(f"\n📈 Summary:")
    print(f"  Storylets with coordinates: {storylets_with_coords}")
    print(f"  Storylets with locations:   {storylets_with_locations}")
    
    # Check if we need to run spatial assignment
    if storylets_with_locations > 0 and storylets_with_coords == 0:
        print(f"\n⚠️  Found {storylets_with_locations} storylets with location requirements but no coordinates!")
        print(f"    This suggests spatial assignment didn't run properly during world generation.")
    elif storylets_with_locations > storylets_with_coords:
        print(f"\n⚠️  Found {storylets_with_locations - storylets_with_coords} storylets that need coordinate assignment.")
    else:
        print(f"\n✅ Spatial assignment appears to be working correctly.")

if __name__ == "__main__":
    debug_database_state()
