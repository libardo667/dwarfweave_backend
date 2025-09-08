#!/usr/bin/env python3
"""Test the spatial navigation improvements."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.location_mapper import LocationMapper

def test_location_mapping():
    """Test the location mapping functionality."""
    print("🧪 Testing Location Mapping System")
    print("=" * 50)
    
    # Sample storylets like AI would generate
    sample_storylets = [
        {
            'title': 'Welcome to the Forest',
            'text': 'You find yourself in a dense forest.',
            'requires': {'location': 'forest'},
            'choices': [
                {'text': 'Go to the tavern', 'set': {'location': 'tavern'}},
                {'text': 'Head to the mountain', 'set': {'location': 'mountain'}}
            ],
            'weight': 1.0
        },
        {
            'title': 'The Cozy Tavern',
            'text': 'The tavern is warm and welcoming.',
            'requires': {'location': 'tavern'},
            'choices': [
                {'text': 'Visit the market', 'set': {'location': 'market'}},
                {'text': 'Return to forest', 'set': {'location': 'forest'}}
            ],
            'weight': 1.0
        },
        {
            'title': 'Mountain Peak',
            'text': 'You stand atop the mighty mountain.',
            'requires': {'location': 'mountain'},
            'choices': [
                {'text': 'Descend to valley', 'set': {'location': 'valley'}},
                {'text': 'Visit the cave', 'set': {'location': 'cave'}}
            ],
            'weight': 1.0
        },
        {
            'title': 'Bustling Market',
            'text': 'The market square buzzes with activity.',
            'requires': {'location': 'market'},
            'choices': [
                {'text': 'Go to the forge', 'set': {'location': 'forge'}},
                {'text': 'Return to tavern', 'set': {'location': 'tavern'}}
            ],
            'weight': 1.0
        },
        {
            'title': 'Hidden Valley',
            'text': 'A peaceful valley hidden in the mountains.',
            'requires': {'location': 'valley'},
            'choices': [
                {'text': 'Follow the river', 'set': {'location': 'river'}},
                {'text': 'Climb back to mountain', 'set': {'location': 'mountain'}}
            ],
            'weight': 1.0
        }
    ]
    
    # Test the location mapper
    mapper = LocationMapper()
    updated_storylets = mapper.assign_coordinates_to_storylets(sample_storylets)
    
    print("📍 Location Assignments:")
    print("-" * 30)
    
    locations = {}
    for storylet in updated_storylets:
        requires = storylet.get('requires', {})
        location = requires.get('location')
        if location and 'spatial_x' in storylet and 'spatial_y' in storylet:
            x, y = storylet['spatial_x'], storylet['spatial_y']
            locations[location] = (x, y)
            print(f"  {location:15} -> ({x:3}, {y:3})")
    
    print("\n🗺️ Spatial Map:")
    print("-" * 30)
    visualization = mapper.visualize_locations(locations)
    print(visualization)
    
    print("\n✅ Location mapping test completed!")
    
    # Test semantic patterns
    print("\n🧠 Testing Semantic Pattern Recognition:")
    print("-" * 45)
    
    test_locations = [
        'mystical_forest_grove',
        'ancient_mountain_temple', 
        'riverside_tavern',
        'underground_crystal_cave',
        'northern_watchtower',
        'eastern_trading_post',
        'central_town_square'
    ]
    
    for location in test_locations:
        coords = mapper._get_coordinates_for_location(location, set())
        print(f"  {location:25} -> {coords}")
    
    print("\n🎉 All tests completed successfully!")

if __name__ == "__main__":
    test_location_mapping()
