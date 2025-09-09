#!/usr/bin/env python3
"""
True Test Runner for DwarfWeave Backend.

This is the organized test runner for task-based unit tests created from 
the consolidated task analysis. These tests focus on specific functionality 
improvements and bug fixes identified in the codebase review.

Structure:
- true_tests/: Clean, focused unit tests based on identified tasks
- Organized by component and priority
- Clear pass/fail reporting with task correlation
"""

import sys
import os
import subprocess
from pathlib import Path
import pytest
import time

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_test(test_path, description, task_id=None):
    """Run a single test file with enhanced reporting."""
    task_info = f" (Task: {task_id})" if task_id else ""
    print(f"\n🧪 Running: {description}{task_info}")
    print("=" * 50)
    
    try:
        start_time = time.time()
        result_code = pytest.main([test_path, "-q"])
        duration = time.time() - start_time

        if result_code == 0:
            print(f"✅ {description} - PASSED ({duration:.2f}s)")
        else:
            print(f"❌ {description} - FAILED ({duration:.2f}s)")
        return result_code == 0
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def run_core_tests():
    """Run core application tests."""
    print("🏗️  RUNNING CORE APPLICATION TESTS")
    print("=" * 60)
    
    core_tests = [
        ("true_tests/core/test_main.py", "Health Check Endpoint", "main-005"),
    ]
    
    results = []
    for test_path, description, task_id in core_tests:
        if os.path.exists(test_path):
            results.append(run_test(test_path, description, task_id))
        else:
            print(f"⚠️  Test file not found: {test_path}")
            results.append(False)
    
    return all(results)

def run_api_tests():
    """Run API-related tests."""
    print("\n🌐 RUNNING API TESTS")
    print("=" * 60)
    
    api_tests = [
        ("true_tests/api/test_game_cache_cleanup.py", "Game API Cache Cleanup", "game-003"),
        ("true_tests/api/test_author_validation.py", "Author Input Validation", "author-002"),
        # Add more API tests here as they are created
    ]
    
    results = []
    for test_path, description, task_id in api_tests:
        if os.path.exists(test_path):
            results.append(run_test(test_path, description, task_id))
        else:
            print(f"⚠️  Test file not found: {test_path}")
            results.append(False)
    
    return all(results)

def run_database_tests():
    """Run database-related tests."""
    print("\n🗃️  RUNNING DATABASE TESTS")
    print("=" * 60)
    
    database_tests = [
        ("true_tests/database/test_environment_logic.py", "Database Environment Tests", "database-005"),
        # Add more database tests here as they are created
    ]
    
    results = []
    for test_path, description, task_id in database_tests:
        if os.path.exists(test_path):
            results.append(run_test(test_path, description, task_id))
        else:
            print(f"⚠️  Test file not found: {test_path}")
            results.append(False)
    
    return all(results)

def run_service_tests():
    """Run service layer tests."""
    print("\n🔧 RUNNING SERVICE TESTS")
    print("=" * 60)
    
    service_tests = [
        ("true_tests/service/test_seed_data.py", "Seed Data Tests", "seed-005"),
        # Add more service tests here as they are created
    ]
    
    results = []
    for test_path, description, task_id in service_tests:
        if os.path.exists(test_path):
            results.append(run_test(test_path, description, task_id))
        else:
            print(f"⚠️  Test file not found: {test_path}")
            results.append(False)
    
    return all(results)

def print_test_summary(category_results):
    """Print a comprehensive test summary."""
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_categories = len(category_results)
    passed_categories = sum(1 for result in category_results.values() if result)
    
    for category, passed in category_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{category:.<30} {status}")
    
    print("-" * 60)
    print(f"Categories: {passed_categories}/{total_categories} passed")
    
    if all(category_results.values()):
        print("🎉 ALL TESTS PASSED! Task implementations are working correctly!")
    else:
        print("❌ Some test categories failed. Check output above for details.")
    
    print("=" * 60)

def main():
    """Main test runner with category selection."""
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        test_type = "all"
    
    print("🚀 DWARFWEAVE BACKEND - TRUE TEST SUITE")
    print("=" * 60)
    print("Task-based unit tests for systematic code improvements")
    
    category_results = {}
    
    if test_type in ["core", "all"]:
        category_results["Core"] = run_core_tests()
    
    if test_type in ["api", "all"]:
        category_results["API"] = run_api_tests()
    
    if test_type in ["database", "all"]:
        category_results["Database"] = run_database_tests()
    
    if test_type in ["service", "all"]:
        category_results["Service"] = run_service_tests()
    
    print_test_summary(category_results)
    
    print("\nUsage:")
    print("  python run_true_tests.py         # Run all test categories")
    print("  python run_true_tests.py core    # Run core application tests")
    print("  python run_true_tests.py api     # Run API tests")
    print("  python run_true_tests.py database # Run database tests")
    print("  python run_true_tests.py service # Run service tests")

if __name__ == "__main__":
    main()
