#!/usr/bin/env python3
"""
Test the world generation functionality
"""

import sys
import requests
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_world_generation():
    """Test the world generation API endpoint."""
    print("🌍 Testing World Generation API")
    print("=" * 50)
    
    # Test data for space whales
    space_whale_world = {
        "description": "A vast cosmos where ancient space whales swim through stellar currents, carrying entire civilizations on their backs. These magnificent creatures navigate between stars using quantum resonance, and their songs can be heard across light-years. The player is a Star Navigator, learning to communicate with these cosmic leviathans.",
        "theme": "cosmic space whales",
        "player_role": "Star Navigator",
        "key_elements": ["space whales", "stellar currents", "quantum resonance", "whale songs", "cosmic civilizations"],
        "tone": "wonder",
        "storylet_count": 8
    }
    
    # Test data for cyberpunk dwarves
    cyberpunk_dwarf_world = {
        "description": "Deep beneath the neon-lit surface cities, cyberpunk dwarves operate quantum techno-forges in vast underground networks. They weave digital spells through neural interfaces while maintaining ancient clan traditions. Corporate megadwarfs rule the depths while rebel hackers fight for digital freedom using mystical coding techniques passed down through generations.",
        "theme": "cyberpunk quantum technoweaving dwarves",
        "player_role": "techno-weaver",
        "key_elements": ["quantum forges", "neural interfaces", "digital spells", "clan traditions", "corporate megadwarfs", "rebel hackers"],
        "tone": "gritty cyberpunk",
        "storylet_count": 8
    }
    
    base_url = "http://localhost:8000"
    
    for world_name, world_data in [("Space Whales", space_whale_world), ("Cyberpunk Dwarves", cyberpunk_dwarf_world)]:
        print(f"\n🧪 Testing: {world_name}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{base_url}/author/generate-world",
                json=world_data,
                timeout=60  # World generation can take time
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS: {result['message']}")
                print(f"📊 Created: {result['storylets_created']} storylets")
                print(f"🎭 Theme: {result['theme']}")
                print(f"👤 Player Role: {result['player_role']}")
                
                if result.get('storylets'):
                    print(f"\n📚 Sample Storylets:")
                    for i, storylet in enumerate(result['storylets'][:2], 1):
                        print(f"   {i}. {storylet['title']}")
                        print(f"      {storylet['text_template'][:80]}...")
                        print(f"      Choices: {len(storylet['choices'])}")
                        
            else:
                print(f"❌ FAILED: HTTP {response.status_code}")
                print(f"   Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ FAILED: Could not connect to server")
            print("   Make sure the FastAPI server is running: uvicorn app:app --reload")
            
        except Exception as e:
            print(f"❌ FAILED: {e}")

def main():
    """Run world generation tests."""
    print("🚀 WORLD GENERATION TEST SUITE")
    print("Testing the new dynamic world creation system!")
    print()
    
    test_world_generation()
    
    print("\n" + "=" * 50)
    print("🎯 Test completed!")
    print("\nNext steps:")
    print("1. 🖥️  Start server: uvicorn app:app --reload")
    print("2. 🧪 Run this test to verify world generation")
    print("3. 🎮 Build the Twine interface for user input")
    print("4. 🌌 Generate amazing worlds!")

if __name__ == "__main__":
    main()
