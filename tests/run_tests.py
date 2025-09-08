#!/usr/bin/env python3
"""
Test runner for WorldWeaver AI System.

This script runs different categories of tests:
- AI tests: Core AI functionality
- Integration tests: Full system integration
- All tests: Everything together
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_test(test_path, description):
    """Run a single test file."""
    print(f"\n🧪 Running: {description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            [sys.executable, test_path], capture_output=False, cwd=project_root
        )
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
        else:
            print(f"❌ {description} - FAILED")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def run_ai_tests():
    """Run all AI-related tests."""
    print("🤖 RUNNING AI TESTS")
    print("=" * 60)
    
    ai_tests = [
        ("tests/ai/test_basic_llm.py", "Basic LLM Functionality"),
        ("tests/ai/test_direct_generation.py", "Direct Generation Test"),
        ("tests/ai/test_intelligent_ai.py", "Full Intelligent AI System"),
    ]
    
    results = []
    for test_path, description in ai_tests:
        if os.path.exists(test_path):
            results.append(run_test(test_path, description))
        else:
            print(f"⚠️  Test file not found: {test_path}")
            results.append(False)
    
    return all(results)

def run_integration_tests():
    """Run integration tests."""
    print("\n🔧 RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    integration_tests = [
        ("tests/integration/test_state_management_basic.py", "State Management - Basic Functions"),
        ("tests/integration/test_state_management_advanced.py", "State Management - Advanced Scenarios"),
        ("tests/integration/test_phase1_final_validation.py", "State Management - Final Validation"),
        ("tests/integration/test_ai_setup.py", "AI Integration Setup"),
        ("tests/integration/test_auto_improvement.py", "Auto Improvement System"),
    ]
    
    results = []
    for test_path, description in integration_tests:
        if os.path.exists(test_path):
            results.append(run_test(test_path, description))
        else:
            print(f"⚠️  Test file not found: {test_path}")
            results.append(False)
    
    return all(results)

def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        test_type = "all"
    
    print("🚀 WORLDWEAVER AI TEST SUITE")
    print("=" * 60)
    
    if test_type in ["ai", "all"]:
        ai_passed = run_ai_tests()
    else:
        ai_passed = True
    
    if test_type in ["integration", "all"]:
        integration_passed = run_integration_tests()
    else:
        integration_passed = True
    
    print("\n" + "=" * 60)
    if ai_passed and integration_passed:
        print("🎉 ALL TESTS PASSED! System is ready!")
    else:
        print("❌ Some tests failed. Check output above.")
    print("=" * 60)
    
    print("\nUsage:")
    print("  python tests/run_tests.py        # Run all tests")
    print("  python tests/run_tests.py ai     # Run AI tests only")
    print("  python tests/run_tests.py integration  # Run integration tests only")

if __name__ == "__main__":
    main()
