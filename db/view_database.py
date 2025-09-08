"""
Database viewer script to inspect storylets and session data.
"""

import sqlite3
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

def view_storylets():
    """Display all storylets in a readable format."""
    conn = sqlite3.connect('worldweaver.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, text_template, requires, choices, weight FROM storylets ORDER BY id")
    storylets = cursor.fetchall()
    
    print(f"\n📚 Found {len(storylets)} storylets in database:")
    print("=" * 80)
    
    for storylet in storylets:
        id, title, text_template, requires, choices, weight = storylet
        
        print(f"\n🆔 ID: {id}")
        print(f"📖 Title: {title}")
        print(f"📝 Text: {text_template[:100]}{'...' if len(text_template) > 100 else ''}")
        print(f"⚖️  Weight: {weight}")
        
        # Parse and display requirements
        try:
            req_data = json.loads(requires) if requires else {}
            if req_data:
                print(f"📋 Requires: {req_data}")
        except:
            print(f"📋 Requires: {requires}")
        
        # Parse and display choices
        try:
            choice_data = json.loads(choices) if choices else []
            if choice_data:
                print(f"🎯 Choices ({len(choice_data)}):")
                for i, choice in enumerate(choice_data, 1):
                    label = choice.get('label') or choice.get('text', 'Unknown')
                    print(f"   {i}. {label}")
        except:
            print(f"🎯 Choices: {choices}")
        
        print("-" * 40)
    
    conn.close()

def view_sessions():
    """Display session data."""
    conn = sqlite3.connect('worldweaver.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT session_id, vars, updated_at FROM session_vars ORDER BY updated_at DESC")
    sessions = cursor.fetchall()
    
    print(f"\n👥 Found {len(sessions)} sessions:")
    print("=" * 50)
    
    for session in sessions:
        session_id, vars_json, updated_at = session
        
        print(f"\n🆔 Session: {session_id}")
        print(f"🕐 Updated: {updated_at}")
        
        try:
            vars_data = json.loads(vars_json) if vars_json else {}
            print(f"📊 Variables: {vars_data}")
        except:
            print(f"📊 Variables: {vars_json}")
        
        print("-" * 25)
    
    conn.close()

def analyze_storylet_connections():
    """Analyze how storylets connect to each other."""
    conn = sqlite3.connect('worldweaver.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, requires, choices FROM storylets")
    storylets = cursor.fetchall()
    
    print(f"\n🔗 Storylet Connection Analysis:")
    print("=" * 60)
    
    # Track variables that are set and required
    variables_set = set()
    variables_required = set()
    location_flow = {}
    
    for storylet in storylets:
        id, title, requires, choices = storylet
        
        # Analyze requirements
        try:
            req_data = json.loads(requires) if requires else {}
            for key in req_data.keys():
                variables_required.add(key)
                if key == 'location':
                    if key not in location_flow:
                        location_flow[key] = {'required_by': [], 'set_by': []}
                    location_flow[key]['required_by'].append(title)
        except:
            pass
        
        # Analyze what variables are set by choices
        try:
            choice_data = json.loads(choices) if choices else []
            for choice in choice_data:
                set_data = choice.get('set', {})
                for key in set_data.keys():
                    variables_set.add(key)
        except:
            pass
    
    print(f"\n📊 Variable Usage:")
    print(f"   Variables required by storylets: {sorted(variables_required)}")
    print(f"   Variables set by choices: {sorted(variables_set)}")
    
    missing_setters = variables_required - variables_set
    unused_setters = variables_set - variables_required
    
    if missing_setters:
        print(f"\n⚠️  Variables required but never set: {sorted(missing_setters)}")
    if unused_setters:
        print(f"\n💡 Variables set but never required: {sorted(unused_setters)}")
    
    conn.close()

def main():
    """Main menu for database viewer."""
    print("🗄️  WorldWeaver Database Viewer")
    print("=" * 40)
    print("1. View all storylets")
    print("2. View sessions")
    print("3. Analyze storylet connections")
    print("4. All of the above")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice in ["1", "4"]:
        view_storylets()
    
    if choice in ["2", "4"]:
        view_sessions()
    
    if choice in ["3", "4"]:
        analyze_storylet_connections()
    
    print("\n✨ Done!")

if __name__ == "__main__":
    main()
