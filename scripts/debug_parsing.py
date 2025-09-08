#!/usr/bin/env python3
"""Debug the storylet requirements parsing issue."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db
from sqlalchemy import text
import json

def debug_parsing():
    """Debug why storylet requirements aren't parsing correctly."""
    print("🔍 Debugging Storylet Requirements Parsing")
    print("=" * 50)
    
    db = next(get_db())
    result = db.execute(text("SELECT id, title, requires FROM storylets LIMIT 5"))
    
    for row in result.fetchall():
        storylet_id, title, requires = row
        print(f"\n📚 Storylet: {title}")
        print(f"   ID: {storylet_id}")
        print(f"   requires type: {type(requires)}")
        print(f"   requires value: {repr(requires)}")
        
        if requires:
            try:
                parsed = json.loads(requires)
                print(f"   ✅ Parsed successfully: {parsed}")
                location = parsed.get('location')
                print(f"   📍 Location: {location}")
            except Exception as e:
                print(f"   ❌ Parse error: {e}")
                print(f"   📝 Raw string: {requires}")
        else:
            print(f"   ⚠️ No requirements (None or empty)")
    
    # Now test if any storylets can be matched
    print(f"\n🎮 Current Session Location: 'Tides of Fate'")
    print(f"🔍 Looking for storylets that:")
    print(f"   1. Have no location requirement")
    print(f"   2. Have location = 'Tides of Fate'")
    print(f"   3. Have flexible location requirements")
    
    matching_storylets = []
    all_result = db.execute(text("SELECT id, title, requires FROM storylets"))
    
    for row in all_result.fetchall():
        storylet_id, title, requires = row
        try:
            if not requires:
                matching_storylets.append(f"{title} (no requirements)")
                continue
                
            parsed = json.loads(requires)
            location = parsed.get('location')
            
            if not location:
                matching_storylets.append(f"{title} (no location requirement)")
            elif location == 'Tides of Fate':
                matching_storylets.append(f"{title} (exact match)")
            elif location in ['any_realm', 'any_location', None]:
                matching_storylets.append(f"{title} (flexible: {location})")
                
        except Exception as e:
            print(f"   ⚠️ Parse error for '{title}': {e}")
            continue
    
    print(f"\n🎯 Potentially matching storylets ({len(matching_storylets)}):")
    for match in matching_storylets:
        print(f"   - {match}")
    
    if not matching_storylets:
        print(f"   ❌ No matching storylets found!")
        print(f"   💡 This explains why the fallback is showing.")
        print(f"\n🔧 Possible solutions:")
        print(f"   1. Create a storylet with no location requirement")
        print(f"   2. Create a storylet for location 'Tides of Fate'")
        print(f"   3. Reset session location to match existing storylets")

if __name__ == "__main__":
    debug_parsing()
