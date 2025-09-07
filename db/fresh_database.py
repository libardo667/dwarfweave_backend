#!/usr/bin/env python3
"""
Simple database wipe - creates a new database file with a different name.

This bypasses file locking issues by creating a fresh database.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent  # Go up from db/ to project root
sys.path.insert(0, str(project_root))

from src.database import create_tables

def create_fresh_database():
    """Create a completely fresh database."""
    print("🚀 CREATING FRESH DATABASE")
    print("=" * 40)
    
    # Create new database with timestamp
    import time
    new_db_name = f'dwarfweave_fresh_{int(time.time())}.db'
    
    # Create the new database with proper table creation
    new_engine = create_engine(f'sqlite:///{new_db_name}', future=True)
    
    # Import and create all tables - exactly like the main app does
    from src.database import Base
    from src.models import Storylet, SessionVars  # Import models to register them
    Base.metadata.create_all(new_engine)
    
    print(f"✅ Created fresh database: {new_db_name}")
    print("📋 Created tables: storylets, session_vars")
    
    # Verify it's empty
    conn = sqlite3.connect(new_db_name)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM storylets')
    storylet_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM session_vars')
    session_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"📊 Verified: {storylet_count} storylets, {session_count} sessions")
    
    # Rename to replace the old one
    if os.path.exists('dwarfweave.db'):
        backup_name = f'dwarfweave_old_{int(time.time())}.db'
        print(f"📦 Moving old database to: {backup_name}")
        try:
            os.rename('dwarfweave.db', backup_name)
            os.rename(new_db_name, 'dwarfweave.db')
            print("✅ Successfully replaced database!")
        except OSError:
            print("⚠️  Could not replace locked database file")
            print(f"   Your fresh database is ready as: {new_db_name}")
            print("   Manual steps:")
            print("   1. Close Twine/stop servers")
            print(f"   2. Rename {new_db_name} to dwarfweave.db")
            print("   3. Restart your applications")
            return new_db_name
    else:
        os.rename(new_db_name, 'dwarfweave.db')
        print("✅ Created dwarfweave.db successfully!")
    
    return 'dwarfweave.db'

if __name__ == "__main__":
    from sqlalchemy import create_engine
    
    print("🗑️  FRESH DATABASE CREATOR")
    print("This creates a clean database, avoiding file locks")
    print("=" * 50)
    
    result = create_fresh_database()
    
    print("\n🎉 SUCCESS! Database is ready for:")
    print("   🐋 Space whales swimming through the cosmos")
    print("   🤖 Cyberpunk dwarves technoweaving quantum realities")
    print("   🌌 Any universe your imagination can create!")
    
    if result != 'dwarfweave.db':
        print(f"\n⚠️  Database created as: {result}")
        print("   Rename this to 'dwarfweave.db' when ready")
