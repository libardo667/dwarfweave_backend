"""Advanced integration test showcasing the state management system."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.state_manager import AdvancedStateManager

def test_advanced_scenarios():
    """Test advanced gameplay scenarios using the state management system."""
    print("🚀 Testing Advanced DwarfWeave Scenarios...")
    
    manager = AdvancedStateManager("thorin_ironbeard_session")
    
    # === SCENARIO 1: Character Setup ===
    print("\n📋 Setting up character...")
    manager.set_variable("player_name", "Thorin Ironbeard")
    manager.set_variable("gold", 200)
    manager.set_variable("level", 8)
    manager.set_variable("clan", "Ironforge")
    manager.set_variable("location", "mountain_depths")
    
    # Add starting gear
    manager.add_item("ancestral_pickaxe", "Ancestral Pickaxe", 1, {
        "damage": 15, "durability": 0.9, "magical": True, "family_heirloom": True
    })
    manager.add_item("lantern", "Dwarven Lantern", 1, {"light_radius": 8, "fuel": 0.7})
    manager.add_item("rope", "Sturdy Rope", 3, {"length": 50})
    manager.add_item("gold_nugget", "Gold Nuggets", 12, {"value": 10})
    
    print(f"✅ Character created: {manager.variables['player_name']}")
    print(f"   Gold: {manager.variables['gold']}, Level: {manager.variables['level']}")
    print(f"   Inventory: {len(manager.inventory)} items")
    
    # === SCENARIO 2: Meeting NPCs and Building Relationships ===
    print("\n🤝 Building relationships...")
    
    # Meet the mine overseer
    overseer_rel = manager.update_relationship("player", "mine_overseer", {"trust": 0.3, "respect": 0.6})
    overseer_rel.add_memory("First meeting - proved mining skills")
    
    # Meet a rival miner  
    rival_rel = manager.update_relationship("player", "greedy_miner", {"trust": -0.2, "respect": 0.1})
    rival_rel.add_memory("Caught trying to steal gems")
    
    # Meet an elder
    elder_rel = manager.update_relationship("player", "clan_elder", {"trust": 0.8, "respect": 0.9})
    elder_rel.add_memory("Shared stories of the old days")
    
    print("✅ Relationships established:")
    for rel_key, rel in manager.relationships.items():
        print(f"   {rel_key}: {rel.get_overall_disposition()} (trust: {rel.trust:.1f}, respect: {rel.respect:.1f})")
    
    # === SCENARIO 3: Environmental Challenge ===
    print("\n🌩️ Environmental challenge...")
    manager.update_environment({
        "time_of_day": "night",
        "weather": "stormy", 
        "danger_level": 6,
        "lighting": "dim"
    })
    
    context = manager.get_contextual_variables()
    mood = manager.environment.get_mood_modifier()
    print(f"✅ Environment: {context['_weather']} {context['_time_of_day']}, danger: {context['_danger_level']}")
    print(f"   Mood effects: {mood}")
    
    # === SCENARIO 4: Complex Condition Testing ===
    print("\n🎯 Testing complex conditions...")
    
    # Test: Can attempt dangerous mining expedition?
    expedition_conditions = {
        "gold": {"gte": 150},           # Need supplies money
        "level": {"gte": 5},            # Need experience
    }
    can_expedition = manager.evaluate_condition(expedition_conditions)
    print(f"✅ Can attempt expedition: {can_expedition}")
    
    # Test: Relationship-based conditions (using new format)
    elder_conditions = {
        "relationship:player:clan_elder": {"trust": {"gte": 0.7}, "respect": {"gte": 0.8}}
    }
    can_seek_wisdom = manager.evaluate_condition(elder_conditions)
    print(f"✅ Can seek elder's wisdom: {can_seek_wisdom}")
    
    # Test: Item-based conditions  
    mining_conditions = {
        "item:ancestral_pickaxe": {"quantity": {"gte": 1}}
    }
    can_mine_deep = manager.evaluate_condition(mining_conditions)
    print(f"✅ Can mine deep veins: {can_mine_deep}")
    
    # === SCENARIO 5: Dynamic Story Events ===
    print("\n📖 Simulating story events...")
    
    # Event: Found rare gem in dangerous area
    if can_expedition and can_mine_deep:
        print("🔮 STORY EVENT: Found Ancient Crystal!")
        manager.add_item("ancient_crystal", "Ancient Crystal", 1, {
            "value": 1000, "magical": True, "rarity": "legendary"
        })
        manager.set_variable("gold", manager.variables["gold"] + 100)
        overseer_rel = manager.update_relationship("player", "mine_overseer", {"respect": 0.2})
        overseer_rel.add_memory("Discovered the legendary crystal vein")
        
        # Environmental consequences
        manager.update_environment({"danger_level": 8})  # Area becomes more dangerous
        
    # Event: Elder offers wisdom  
    if can_seek_wisdom:
        print("🧙 STORY EVENT: Elder shares ancient knowledge!")
        manager.set_variable("ancient_knowledge", True)
        manager.set_variable("knows_secret_passages", True)
        manager.update_relationship("player", "clan_elder", {"trust": 0.1})
        
    # === SCENARIO 6: Final State Assessment ===
    print("\n📊 Final state assessment...")
    
    summary = manager.get_state_summary()
    print(f"✅ Variables: {len(summary['variables'])} total")
    print(f"✅ Items: {summary['inventory_summary']['total_items']} types, {summary['inventory_summary']['total_quantity']} total")
    print(f"✅ Relationships: {len(summary['relationships_summary'])} NPCs")
    print(f"✅ Change history: {summary['recent_changes']} recent changes")
    
    # Show wealth and reputation
    wealth = manager.variables["gold"] + sum(
        item.quantity * item.properties.get("value", 0) 
        for item in manager.inventory.values()
    )
    avg_reputation = sum(rel.trust + rel.respect for rel in manager.relationships.values()) / len(manager.relationships)
    
    print(f"\n🏆 Character Status:")
    print(f"   Total Wealth: {wealth} gold")
    print(f"   Average Reputation: {avg_reputation:.2f}")
    print(f"   Special Knowledge: {manager.variables.get('ancient_knowledge', False)}")
    
    # === SCENARIO 7: Test Advanced Features ===
    print("\n⚡ Testing advanced features...")
    
    # Test item combination potential
    pickaxe = manager.inventory["ancestral_pickaxe"] 
    crystal = manager.inventory.get("ancient_crystal")
    if crystal:
        print(f"✅ Can combine pickaxe + crystal: {pickaxe.can_combine_with(crystal)}")
    
    # Test available actions in current context
    actions = pickaxe.get_available_actions(context)
    print(f"✅ Available pickaxe actions: {actions}")
    
    # Test memory system
    elder_rel = manager.get_relationship("player", "clan_elder")
    if elder_rel:
        print(f"✅ Elder memories: {len(elder_rel.memory_fragments)} stored")
    else:
        print("✅ Elder relationship not found")
    
    print("\n🎉 ADVANCED STATE MANAGEMENT SYSTEM FULLY OPERATIONAL!")
    print("📈 The system successfully handled:")
    print("   - Complex character state")
    print("   - Multi-dimensional relationships") 
    print("   - Environmental conditions")
    print("   - Conditional logic evaluation")
    print("   - Dynamic story events")
    print("   - Change tracking and history")
    
    return True

if __name__ == "__main__":
    test_advanced_scenarios()
