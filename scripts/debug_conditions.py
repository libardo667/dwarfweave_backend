#!/usr/bin/env python3
"""Debug the condition evaluation in state manager."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db
from src.api.game import get_state_manager
from sqlalchemy import text
import json

def debug_condition_evaluation():
    """Debug why storylet condition evaluation is failing."""
    print("🔍 Debugging Condition Evaluation")
    print("=" * 40)
    
    db = next(get_db())
    
    # Get the current session ID (assume it's '1' or get from db)
    session_result = db.execute(text("SELECT session_id FROM session_vars ORDER BY session_id DESC LIMIT 1"))
    session_row = session_result.fetchone()
    session_id = session_row[0] if session_row else "1"
    
    print(f"📋 Using session ID: {session_id}")
    
    # Get the state manager
    state_manager = get_state_manager(session_id, db)
    
    print(f"🎮 Current state variables:")
    for key, value in state_manager.variables.items():
        print(f"   {key}: {value}")
    
    print(f"\n🧪 Testing condition evaluation for matching storylets:")
    
    # Test the storylets we identified as potentially matching
    test_storylets = [
        ("Call of the Void", '{"location": "any_realm"}'),
        ("Voyage to the Uncharted", '{"location": "any_realm"}'),  
        ("Cosmic Reputation Advantage", '{"location": "any_realm"}'),
        ("Navigating the Unknown", '{}'),  # No requirements
        ("Navigating the Currents", '{}'),  # No requirements
    ]
    
    for title, requires_json in test_storylets:
        print(f"\n📚 Testing: {title}")
        print(f"   Requirements: {requires_json}")
        
        try:
            requirements = json.loads(requires_json)
            result = state_manager.evaluate_condition(requirements)
            print(f"   ✅ Evaluation result: {result}")
            
            # Debug the specific evaluation
            if not result and requirements:
                print(f"   🔍 Detailed evaluation:")
                for req_key, req_value in requirements.items():
                    current_value = state_manager.variables.get(req_key, "NOT_SET")
                    print(f"      {req_key}: required={req_value}, current={current_value}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test actual storylets from database
    print(f"\n🗃️ Testing actual database storylets:")
    result = db.execute(text("""
        SELECT id, title, requires 
        FROM storylets 
        WHERE requires IN ('{}', '{"location": "any_realm"}')
        OR requires IS NULL
        LIMIT 5
    """))
    
    for row in result.fetchall():
        storylet_id, title, requires = row
        print(f"\n📚 DB Storylet: {title} (ID: {storylet_id})")
        print(f"   Requirements: {requires}")
        
        try:
            requirements = json.loads(requires) if requires else {}
            result = state_manager.evaluate_condition(requirements)
            print(f"   ✅ Evaluation result: {result}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    debug_condition_evaluation()
