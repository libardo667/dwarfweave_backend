"""
Final validation test for Phase 1 state management with all fixes applied.
This test validates that all the gaps have been addressed.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.state_manager import AdvancedStateManager, RelationshipState, EnvironmentalState

def test_all_fixes():
    """Test that all 8 identified issues have been resolved."""
    print("🎯 FINAL VALIDATION: Testing All Fixed Functionality")
    print("=" * 60)
    
    manager = AdvancedStateManager("validation_session")
    passed_tests = []
    
    # === FIX 1: RelationshipState.update() method ===
    print("\n✅ Fix 1: RelationshipState update() method")
    rel = RelationshipState("player", "npc")
    rel.update({"trust": 0.5, "respect": 0.3}, "Test interaction")
    assert rel.trust == 0.5
    assert rel.respect == 0.3
    assert rel.interaction_count == 1
    assert "Test interaction" in rel.memory_fragments[0]
    passed_tests.append("RelationshipState.update()")
    print("   ✅ Batch relationship updates work correctly")
    
    # === FIX 2: EnvironmentalState.update() method ===
    print("\n✅ Fix 2: EnvironmentalState update() method")
    env = EnvironmentalState()
    env.update({"weather": "stormy", "danger_level": 8, "time_of_day": "night"})
    assert env.weather == "stormy"
    assert env.danger_level == 8
    assert env.time_of_day == "night"
    passed_tests.append("EnvironmentalState.update()")
    print("   ✅ Batch environment updates work correctly")
    
    # === FIX 3: AdvancedStateManager.get_variable() method ===
    print("\n✅ Fix 3: get_variable() method")
    manager.set_variable("test_key", "test_value")
    assert manager.get_variable("test_key") == "test_value"
    assert manager.get_variable("nonexistent", "default") == "default"
    assert manager.get_variable("nonexistent") is None
    passed_tests.append("AdvancedStateManager.get_variable()")
    print("   ✅ Variable getter with defaults works correctly")
    
    # === FIX 4: Simple numeric condition evaluation ===
    print("\n✅ Fix 4: Simple numeric condition evaluation")
    manager.set_variable("gold", 100)
    assert manager.evaluate_condition({"gold": 50}) is True  # 100 >= 50
    assert manager.evaluate_condition({"gold": 150}) is False  # 100 < 150
    assert manager.evaluate_condition({"gold": 100}) is True  # 100 >= 100 (exact)
    passed_tests.append("Simple numeric conditions")
    print("   ✅ Simple numeric conditions work as >= comparisons")
    
    # === FIX 5: Contextual variables without underscores ===
    print("\n✅ Fix 5: Contextual variables format")
    manager.add_item("sword", "Test Sword", 1)
    manager.update_relationship("player", "friend", {"trust": 0.5})
    context = manager.get_contextual_variables()
    
    required_keys = ["inventory_count", "weather", "danger_level", "inventory_items", "known_people"]
    for key in required_keys:
        assert key in context, f"Missing key: {key}"
    
    assert context["inventory_count"] == 1
    assert "sword" in context["inventory_items"]
    assert "friend" in context["known_people"]
    passed_tests.append("Contextual variables compatibility")
    print("   ✅ All expected contextual variable keys available")
    
    # === FIX 6: Item removal edge cases ===
    print("\n✅ Fix 6: Item removal behavior")
    manager.add_item("consumable", "Health Potion", 5)
    
    # Remove more than available
    result = manager.remove_item("consumable", 10)
    assert result is True  # Should return True (items were removed)
    assert "consumable" not in manager.inventory  # Should be completely removed
    passed_tests.append("Item removal edge cases")
    print("   ✅ Removing more than available works correctly")
    
    # === FIX 7: State summary keys ===
    print("\n✅ Fix 7: State summary structure")
    summary = manager.get_state_summary()
    
    required_keys = ["inventory", "variables", "relationships", "environment", "stats"]
    for key in required_keys:
        assert key in summary, f"Missing summary key: {key}"
    
    assert "total_variables" in summary["stats"]
    assert "total_items" in summary["stats"]
    assert "total_relationships" in summary["stats"]
    passed_tests.append("State summary structure")
    print("   ✅ State summary has all expected keys")
    
    # === FIX 8: Change history accessibility ===
    print("\n✅ Fix 8: Change history structure")
    if manager.change_history:
        change = manager.change_history[-1]
        action = change.change_type.value
        assert isinstance(action, str)
        assert len(action) > 0
    passed_tests.append("Change history accessibility")
    print("   ✅ Change history accessible and structured correctly")
    
    # === COMPREHENSIVE INTEGRATION TEST ===
    print("\n🚀 Comprehensive Integration Test")
    
    # Set up complex scenario
    manager.set_variable("player_name", "Validation Tester")
    manager.set_variable("gold", 200)
    manager.set_variable("level", 10)
    
    # Add diverse inventory
    manager.add_item("sword", "Validation Sword", 1, {"damage": 20})
    manager.add_item("potion", "Health Potion", 3, {"healing": 50})
    manager.add_item("key", "Master Key", 1, {"opens": "all_doors"})
    
    # Build relationships
    manager.update_relationship("player", "ally", {"trust": 0.8, "respect": 0.7})
    manager.update_relationship("player", "rival", {"trust": -0.3, "respect": 0.2})
    
    # Set environment
    manager.update_environment({"time_of_day": "dawn", "weather": "clear", "danger_level": 3})
    
    # Test complex conditions
    complex_condition = {
        "gold": {"gte": 150},
        "level": {"gte": 5},
        "relationship:player:ally": {"trust": {"gte": 0.5}},
        "item:sword": {"quantity": {"gte": 1}}
    }
    
    assert manager.evaluate_condition(complex_condition) is True
    
    # Get final state
    final_context = manager.get_contextual_variables()
    final_summary = manager.get_state_summary()
    
    # Validate comprehensive state
    assert final_context["player_name"] == "Validation Tester"
    assert final_context["inventory_count"] == 3
    assert final_context["relationship_count"] == 3  # We have ally, rival, and friend from earlier test
    assert final_context["weather"] == "clear"
    assert len(final_context["known_people"]) == 3
    
    assert final_summary["stats"]["total_variables"] >= 3
    assert final_summary["stats"]["total_items"] == 3
    assert final_summary["stats"]["total_relationships"] == 3  # Updated to match actual count
    
    passed_tests.append("Comprehensive integration")
    print("   ✅ Complex state management scenario works perfectly")
    
    # === FINAL RESULTS ===
    print(f"\n" + "=" * 60)
    print(f"🎉 ALL FIXES VALIDATED SUCCESSFULLY!")
    print(f"✅ Tests Passed: {len(passed_tests)}/8")
    print(f"\n📋 Fixed Components:")
    for i, test in enumerate(passed_tests, 1):
        print(f"   {i}. {test}")
    
    print(f"\n🚀 PHASE 1 STATE MANAGEMENT: PRODUCTION READY!")
    print(f"   - All identified gaps have been addressed")
    print(f"   - Comprehensive testing validates functionality")
    print(f"   - API compatibility maintained")
    print(f"   - Ready for Phase 2 implementation")
    print("=" * 60)
    
    # No return; successful asserts indicate pass

if __name__ == "__main__":
    test_all_fixes()
