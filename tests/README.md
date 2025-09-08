# WorldWeaver Test Suite

## Test Structure

### Core Integration Tests (`tests/integration/`)
- `test_state_management_basic.py` - Core state management functionality ✅
- `test_state_management_advanced.py` - Advanced state management features ✅
- `test_phase1_final_validation.py` - Complete Phase 1 validation suite ✅
- `test_ai_setup.py` - AI integration tests
- `test_auto_improvement.py` - Auto improvement system tests

### AI Tests (`tests/ai/`)
- Various AI and LLM integration tests

### Diagnostic Tools (`tests/diagnostic/`)
- `system_summary.py` - System status and health checks
- `test_database_state.py` - Database diagnostic tools

### Test Configuration
- `test_database.py` - Test database isolation setup ✅
- `run_tests.py` - Automated test runner ✅

## Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific test
python tests/integration/test_state_management_basic.py

# Run only integration tests
python tests/run_tests.py integration

# Run only AI tests  
python tests/run_tests.py ai
```

## Test Database

Tests use a separate `test_database.db` to avoid polluting the main database.
The warning "Database file in use, will be cleaned up later" is harmless on Windows.

## Status

✅ **Phase 1 Advanced State Management** - COMPLETE with comprehensive testing
🚀 **Ready for Phase 1 Dynamic Navigation Framework implementation**
