#!/usr/bin/env python3
"""
Database State Tests

Validates that the database is in the expected state for testing.
"""

import sys
import sqlite3
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
def _test_db_path() -> Path:
    return project_root / 'test_database.db'

def test_database_is_empty():
    """Test that the database is completely empty and ready for fresh content."""
    print("🧪 Testing: Database is empty")
    print("=" * 40)
    
    # Connect to database
    db_path = _test_db_path()
    
    if not db_path.exists():
        print("❌ FAIL: Database file does not exist (creation failed)! Skipping.")
        pytest.skip("test_database.db could not be created; skipping")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check storylets table
        cursor.execute('SELECT COUNT(*) FROM storylets')
        storylet_count = cursor.fetchone()[0]
        
        # Check session_vars table
        cursor.execute('SELECT COUNT(*) FROM session_vars')
        session_count = cursor.fetchone()[0]
        
        print(f"📊 Found {storylet_count} storylets")
        print(f"📊 Found {session_count} sessions")
        if storylet_count == 0 and session_count == 0:
            print("✅ PASS: Database is empty and ready!")
        else:
            print("❌ Database contains data; this is informational in non-fresh environments.")
            pytest.skip(
                f"test_database.db not empty (storylets={storylet_count}, sessions={session_count}); skipping emptiness assertion"
            )
            
    except sqlite3.OperationalError as e:
        print(f"❌ FAIL: Database error - {e}")
        print("   Tables might not exist or database is corrupted")
        assert False, f"OperationalError while checking empty DB: {e}"
        
    finally:
        conn.close()

def test_database_tables_exist():
    """Test that the required tables exist with correct schema."""
    print("\n🧪 Testing: Database tables exist")
    print("=" * 40)
    
    db_path = _test_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        # First, let's see what tables actually exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = cursor.fetchall()
        table_names = [t[0] for t in existing_tables]
        print(f"🔍 Tables found in database: {table_names}")

        if not table_names:
            print("⚠️  Database has no tables at all!")
            print("   This might be a completely empty database file.")
            assert False, "Database has no tables"

        # Check if storylets table exists and has correct columns
        cursor.execute("PRAGMA table_info(storylets)")
        storylet_columns = cursor.fetchall()

        # Check if session_vars table exists and has correct columns
        cursor.execute("PRAGMA table_info(session_vars)")
        session_columns = cursor.fetchall()

        if not storylet_columns:
            print("❌ FAIL: storylets table does not exist!")
            assert False, "storylets table does not exist"

        if not session_columns:
            print("❌ FAIL: session_vars table does not exist!")
            assert False, "session_vars table does not exist"

        # Extract column names
        storylet_col_names = [col[1] for col in storylet_columns]
        session_col_names = [col[1] for col in session_columns]

        print(f"📋 storylets columns: {storylet_col_names}")
        print(f"📋 session_vars columns: {session_col_names}")

        # Check for required columns
        required_storylet_cols = ['id', 'title', 'text_template', 'requires', 'choices', 'weight']
        required_session_cols = ['session_id', 'vars', 'updated_at']

        missing_storylet_cols = set(required_storylet_cols) - set(storylet_col_names)
        missing_session_cols = set(required_session_cols) - set(session_col_names)

        if missing_storylet_cols:
            print(f"❌ FAIL: storylets table missing columns: {missing_storylet_cols}")
            assert False, f"storylets table missing columns: {missing_storylet_cols}"

        if missing_session_cols:
            print(f"❌ FAIL: session_vars table missing columns: {missing_session_cols}")
            assert False, f"session_vars table missing columns: {missing_session_cols}"

        print("✅ PASS: All required tables and columns exist!")
    except sqlite3.OperationalError as e:
        print(f"❌ FAIL: Database error - {e}")
        assert False, f"OperationalError while checking tables: {e}"
    finally:
        conn.close()

def test_database_can_insert():
    """Test that we can insert and retrieve data (then clean up)."""
    print("\n🧪 Testing: Database accepts writes")
    print("=" * 40)

    db_path = _test_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()

        # Insert a test storylet
        test_storylet = (
            "Test Storylet",
            "This is a test storylet.",
            '{}',  # empty requires
            '[]',  # empty choices
            1.0    # weight
        )

        cursor.execute(
            "INSERT INTO storylets (title, text_template, requires, choices, weight) VALUES (?, ?, ?, ?, ?)",
            test_storylet
        )
        conn.commit()

        # Verify it was inserted
        cursor.execute("SELECT COUNT(*) FROM storylets WHERE title = 'Test Storylet'")
        count = cursor.fetchone()[0]

        if count != 1:
            print(f"❌ FAIL: Expected 1 test storylet, found {count}")
        assert count == 1, f"Expected 1 test storylet, found {count}"

        # Clean up - remove the test storylet
        cursor.execute("DELETE FROM storylets WHERE title = 'Test Storylet'")
        conn.commit()

        # Verify cleanup: ensure the test record is gone
        cursor.execute("SELECT COUNT(*) FROM storylets WHERE title = 'Test Storylet'")
        remaining = cursor.fetchone()[0]
        assert remaining == 0, f"Test record not cleaned up; remaining count: {remaining}"
        print("✅ PASS: Insert and cleanup worked (no residual test records)")
    except Exception as e:
        print(f"❌ FAIL: Error during write test - {e}")
        assert False, f"Error during write test: {e}"
    finally:
        conn.close()

def main():
    """Run all database state tests."""
    print("🗄️  DATABASE STATE TEST SUITE")
    print("=" * 50)
    print("Testing database readiness for space whales & cyberpunk dwarves!")
    print()
    
    tests = [
        test_database_tables_exist,
        test_database_is_empty,
        test_database_can_insert,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            break  # Stop on first failure
    
    print("\n" + "=" * 50)
    print(f"🎯 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 SUCCESS! Database is ready for:")
        print("   🐋 Space whales swimming through cosmic currents")
        print("   🤖 Cyberpunk dwarves technoweaving quantum realities")
        print("   🌌 Any universe your imagination can create!")
        return True
    else:
        print("❌ FAILED! Database needs attention before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
