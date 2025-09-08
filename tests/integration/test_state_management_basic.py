"""Quick integration test to verify our state management system works."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.state_manager import AdvancedStateManager
from tests.test_database import reset_test_database, cleanup_test_database

def test_basic_functionality():
    """Test basic functionality of the state management system."""
    print("🧪 Testing Advanced State Management System...")
    
    # Setup clean test database
    reset_test_database()
    
    try:
        # Create manager
        manager = AdvancedStateManager("test_session")
        print("✅ State manager created")
        
        # Test variables
        manager.set_variable("player_name", "Thorin")
        manager.set_variable("gold", 150)
        assert manager.variables["player_name"] == "Thorin"
        assert manager.variables["gold"] == 150
        print("✅ Variable management works")
        
        # Test inventory
        sword = manager.add_item("sword", "Iron Sword", 1, {"damage": 10})
        assert "sword" in manager.inventory
        assert manager.inventory["sword"].name == "Iron Sword"
        print("✅ Inventory management works")
        
        # Test relationships
        rel = manager.update_relationship("player", "merchant", {"trust": 0.5})
        assert rel.trust == 0.5
        print("✅ Relationship management works")
        
        # Test environment
        manager.update_environment({"weather": "stormy", "danger_level": 5})
        assert manager.environment.weather == "stormy"
        assert manager.environment.danger_level == 5
        print("✅ Environment management works")
        
        # Test contextual variables
        context = manager.get_contextual_variables()
        assert context["player_name"] == "Thorin"
        assert context["gold"] == 150
        assert context["inventory_count"] == 1  # Using non-underscore version
        assert context["weather"] == "stormy"   # Using non-underscore version
        print("✅ Contextual variables work")
        
        # Test condition evaluation (simple format)
        assert manager.evaluate_condition({"gold": 150}) == True  # Exact match
        assert manager.evaluate_condition({"gold": 200}) == False  # Different value
        print("✅ Basic condition evaluation works")
        
        # Test advanced condition evaluation
        assert manager.evaluate_condition({"gold": {"gte": 100}}) == True  # 150 >= 100
        assert manager.evaluate_condition({"gold": {"lt": 200}}) == True   # 150 < 200
        assert manager.evaluate_condition({"gold": {"gt": 200}}) == False  # 150 > 200
        print("✅ Advanced condition evaluation works")
        
        # Test state summary
        summary = manager.get_state_summary()
        assert "inventory" in summary           # Using new format
        assert "relationships" in summary       # Using new format  
        assert "environment" in summary
        print("✅ State summary works")

        print("\n🎉 ALL BASIC TESTS PASSED! State Management System is working correctly!")
        print("\nKey Findings:")
        print("- Variables accessed via manager.variables[key]")
        print("- Conditions support both exact values and operator dicts")
        print("- Contextual vars have underscore prefixes for computed values")
        print("- State summary has specific key names")
        # No return; asserts above validate behavior
    finally:
        # Always cleanup test database
        cleanup_test_database()

if __name__ == "__main__":
    test_basic_functionality()
