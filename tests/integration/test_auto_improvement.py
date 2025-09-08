"""
Test Auto-Improvement Integration
Verifies that the auto-improvement system works across all storylet creation endpoints.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_author_commit_improvement():
    """Test that auto-improvement runs when committing storylets."""
    print("🧪 Testing author commit with auto-improvement...")
    
    storylets_data = {
        "storylets": [
            {
                "title": "Test Isolated Location",
                "text_template": "You find yourself in a strange place with no obvious exits.",
                "requires": {"location": "Test Island"},
                "choices": [
                    {"label": "Look around", "set": {"observation": 1}}
                ],
                "weight": 1.0
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/author/commit", json=storylets_data)
    result = response.json()
    
    print(f"✅ Added {result.get('added', 0)} storylets")
    assert 'auto_improvements' in result, "Expected auto_improvements in response"

def test_world_generation_improvement():
    """Test that auto-improvement runs during world generation."""
    print("\n🧪 Testing world generation with auto-improvement...")
    
    world_data = {
        "description": "A small testing realm with basic locations",
        "theme": "test realm",
        "player_role": "tester",
        "key_elements": ["testing", "validation"],
        "tone": "analytical",
        "storylet_count": 5
    }
    
    response = requests.post(f"{BASE_URL}/author/generate-world", json=world_data)
    result = response.json()
    
    print(f"✅ Generated {result.get('storylets_created', 0)} storylets")
    assert 'auto_improvements' in result, "Expected auto_improvements in world generation response"

def test_populate_improvement():
    """Test that auto-improvement runs during population."""
    print("\n🧪 Testing storylet population with auto-improvement...")
    
    response = requests.post(f"{BASE_URL}/author/populate?target_count=3")
    result = response.json()
    
    assert result.get('success'), f"Population failed: {result}"
    print(f"✅ Added {result.get('added', 0)} storylets")
    assert 'auto_improvements' in result, "Expected auto_improvements in population response"

def main():
    """Run all auto-improvement tests."""
    print("🔬 Auto-Improvement Integration Tests")
    print("=" * 50)
    
    tests = [
        test_author_commit_improvement,
        test_world_generation_improvement,
        test_populate_improvement
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All auto-improvement tests passed!")
    else:
        print("⚠️  Some tests failed - check the implementation")

if __name__ == "__main__":
    main()
