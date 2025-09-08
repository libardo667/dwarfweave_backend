#!/usr/bin/env python3
"""Test compass navigation after spatial fixes."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db
from src.services.spatial_navigator import SpatialNavigator

def test_compass_navigation():
    """Test the compass navigation system."""
    print("🧭 Testing Compass Navigation System")
    print("=" * 40)
    
    db = next(get_db())
    spatial_nav = SpatialNavigator(db)
    
    print("📍 Available storylets with positions:")
    for sid, pos in spatial_nav.storylet_positions.items():
        print(f"  Storylet {sid}: ({pos.x}, {pos.y})")
    
    if spatial_nav.storylet_positions:
        first_id = list(spatial_nav.storylet_positions.keys())[0]
        print(f"\n🧭 Testing compass navigation from storylet {first_id}:")
        print("-" * 40)
        
        nav = spatial_nav.get_directional_navigation(first_id)
        for direction, target in nav.items():
            if target:
                title = target["title"]
                pos = target["position"]
                print(f"  {direction:10}: {title} at ({pos['x']}, {pos['y']})")
            else:
                print(f"  {direction:10}: None")
        
        print("\n🗺️ Spatial map data:")
        map_data = spatial_nav.get_spatial_map_data()
        print(f"  Total storylets: {len(map_data['storylets'])}")
        print(f"  Bounds: {map_data['bounds']}")
        
        print("\n✅ Compass navigation test completed!")
        
    else:
        print("⚠️ No storylets have spatial positions yet")
        print("   This could mean:")
        print("   1. No world has been generated")
        print("   2. Spatial assignment didn't work")
        print("   3. Database doesn't have spatial columns")

if __name__ == "__main__":
    test_compass_navigation()
