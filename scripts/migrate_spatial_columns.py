#!/usr/bin/env python3
"""
Database Migration: Add Spatial Columns
Adds spatial_x and spatial_y columns to existing storylets table.
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path="worldweaver.db"):
    """Add spatial columns to existing database."""
    
    if not Path(db_path).exists():
        print(f"❌ Database {db_path} does not exist!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(storylets)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'spatial_x' in columns and 'spatial_y' in columns:
            print("✅ Spatial columns already exist!")
            return True
        
        print("🔧 Adding spatial columns to storylets table...")
        
        # Add spatial columns
        if 'spatial_x' not in columns:
            cursor.execute("ALTER TABLE storylets ADD COLUMN spatial_x INTEGER")
            print("  ✅ Added spatial_x column")
        
        if 'spatial_y' not in columns:
            cursor.execute("ALTER TABLE storylets ADD COLUMN spatial_y INTEGER")
            print("  ✅ Added spatial_y column")
        
        conn.commit()
        conn.close()
        
        print("🎉 Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "worldweaver.db"
    migrate_database(db_path)
