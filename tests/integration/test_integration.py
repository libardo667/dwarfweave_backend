#!/usr/bin/env python3
"""Test the integrated spatial coordinate assignment."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db
from src.services.spatial_navigator import SpatialNavigator
from src.models import Storylet
import json

def test_integration():
    """Test the integrated spatial coordinate assignment."""
    print("🧪 Testing Integrated Spatial Coordinate Assignment")
    print("=" * 55)
    
    db = next(get_db())
    
    # Test 1: Check auto_assign_coordinates with specific IDs
    print("1️⃣ Testing auto_assign_coordinates with specific storylet IDs")
    
    # Find some storylets without coordinates
    storylets_without_coords = db.query(Storylet).filter(
        (Storylet.spatial_x.is_(None)) | (Storylet.spatial_y.is_(None))
    ).limit(3).all()
    
    if storylets_without_coords:
        storylet_ids = [s.id for s in storylets_without_coords]
        print(f"   Found {len(storylet_ids)} storylets without coordinates: {storylet_ids}")
        
        # Test the auto-assignment
        updates = SpatialNavigator.auto_assign_coordinates(db, storylet_ids)
        print(f"   ✅ Updated {updates} storylets with coordinates")
    else:
        print("   ℹ️ All storylets already have coordinates")
    
    # Test 2: Test ensure_all_coordinates
    print("\n2️⃣ Testing ensure_all_coordinates (bulk operation)")
    total_updates = SpatialNavigator.ensure_all_coordinates(db)
    print(f"   ✅ Ensured coordinates for {total_updates} storylets")
    
    # Test 3: Check final state
    print("\n3️⃣ Final State Analysis")
    
    storylets_with_locations = db.query(Storylet).filter(
        Storylet.requires.isnot(None)
    ).all()
    
    locations_found = 0
    coordinates_assigned = 0
    
    for storylet in storylets_with_locations:
        try:
            requires = json.loads(storylet.requires) if storylet.requires else {}
            location = requires.get('location')
            
            if location:
                locations_found += 1
                if storylet.spatial_x is not None and storylet.spatial_y is not None:
                    coordinates_assigned += 1
                    print(f"   📍 {storylet.title[:30]:30} | {location:20} | ({storylet.spatial_x:3}, {storylet.spatial_y:3})")
                else:
                    print(f"   ❌ {storylet.title[:30]:30} | {location:20} | No coordinates")
        except:
            continue
    
    print(f"\n📊 Summary:")
    print(f"   Storylets with locations: {locations_found}")
    print(f"   Storylets with coordinates: {coordinates_assigned}")
    print(f"   Coverage: {100 * coordinates_assigned / locations_found if locations_found > 0 else 0:.1f}%")
    
    if coordinates_assigned == locations_found:
        print(f"✅ Perfect! All storylets with locations have coordinates!")
    else:
        print(f"⚠️ {locations_found - coordinates_assigned} storylets still need coordinates")
    
    print(f"\n🎉 Integration test completed!")

if __name__ == "__main__":
    test_integration()
