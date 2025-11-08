# Dashboard Backend Tests

Comprehensive test suite for the orchestrator dashboard backend, with a focus on working directory validation for task creation.

## Test Files

### 1. `test_directory_validation.py` (Unit Tests)
**Status**: ✅ All 19 tests passing

Unit tests for working directory validation logic in isolation. These tests verify the directory validation without requiring the full FastAPI application.

#### Test Coverage

**TestWorkingDirectoryValidation** (14 tests):
- ✅ Valid directory validation
- ✅ Non-existent directory rejection
- ✅ File path (not directory) rejection
- ✅ Empty string handling
- ✅ Current directory (`.`) validation
- ✅ Parent directory (`..`) validation
- ✅ Nested directory structures
- ✅ Directories with spaces in path
- ✅ Unicode characters in path
- ✅ Unreadable directory (permission check)
- ✅ Symlink to valid directory
- ✅ Broken symlink rejection
- ✅ Relative path to absolute conversion
- ✅ Multiple validations with same directory

**TestWorkingDirectoryEdgeCases** (5 tests):
- ✅ Very long paths
- ✅ Special characters in path
- ✅ Root directory validation
- ✅ Home directory validation
- ✅ System temp directory validation

### 2. `test_tasks.py` (API Integration Tests)
**Status**: 📝 Ready for integration testing

Comprehensive API-level tests for task creation endpoint with working directory validation.

#### Test Coverage

**TestTaskCreationWithValidDirectory**:
- Valid absolute directory path
- Relative directory path (current directory)
- Task without working directory (default)
- Nested valid directory structure
- All should return HTTP 201 Created

**TestTaskCreationWithInvalidDirectory**:
- Non-existent directory → HTTP 400 Bad Request
- File path instead of directory → HTTP 400 Bad Request
- Empty directory string → HTTP 400/422

**TestTaskCreationDirectoryPermissions**:
- Unreadable directory → HTTP 400 Bad Request
- Readable directory with proper permissions → HTTP 201 Created

**TestTaskCreationEdgeCases**:
- Special characters in path
- Symlinks to valid directories
- Unicode characters in path
- Multiple tasks with same directory

**TestTaskComplexityDetection**:
- Simple task complexity (< 50 words)
- Complex task complexity (≥ 50 words)

**TestTaskCreationIntegration**:
- Complete workflow validation
- Task creation and retrieval

### 3. `conftest.py`
Pytest configuration with shared fixtures:
- Async event loop configuration
- Test database setup (SQLite in-memory)
- Database session management
- API key fixtures
- Settings overrides for testing

## Running the Tests

### Run All Unit Tests
```bash
cd /path/to/orchestrator/dashboard/backend
python -m pytest tests/test_directory_validation.py -v
```

### Run Specific Test Class
```bash
python -m pytest tests/test_directory_validation.py::TestWorkingDirectoryValidation -v
```

### Run Specific Test
```bash
python -m pytest tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_valid_directory -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term
```

### Run Integration Tests (requires database setup)
```bash
python -m pytest tests/api/test_tasks.py -v
```

## Test Results Summary

### Latest Test Run (Unit Tests)
```
======================== test session starts =========================
platform darwin -- Python 3.13.2, pytest-8.4.1, pluggy-1.6.0
collected 19 items

tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_valid_directory PASSED [  5%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_nonexistent_directory PASSED [ 10%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_file_instead_of_directory PASSED [ 15%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_empty_string_directory PASSED [ 21%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_current_directory PASSED [ 26%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_parent_directory PASSED [ 31%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_nested_directory PASSED [ 36%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_directory_with_spaces PASSED [ 42%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_directory_with_unicode PASSED [ 47%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_unreadable_directory PASSED [ 52%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_symlink_to_valid_directory PASSED [ 57%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_symlink_to_nonexistent_directory PASSED [ 63%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_relative_path_conversion PASSED [ 68%]
tests/test_directory_validation.py::TestWorkingDirectoryValidation::test_multiple_validations_with_same_directory PASSED [ 73%]
tests/test_directory_validation.py::TestWorkingDirectoryEdgeCases::test_very_long_path PASSED [ 78%]
tests/test_directory_validation.py::TestWorkingDirectoryEdgeCases::test_path_with_special_characters PASSED [ 84%]
tests/test_directory_validation.py::TestWorkingDirectoryEdgeCases::test_root_directory PASSED [ 89%]
tests/test_directory_validation.py::TestWorkingDirectoryEdgeCases::test_home_directory PASSED [ 94%]
tests/test_directory_validation.py::TestWorkingDirectoryEdgeCases::test_tmp_directory PASSED [100%]

======================== 19 passed in 0.03s ==========================
```

## Implementation Validation

### Working Directory Validation Logic

The task creation endpoint (`/api/v1/tasks`) implements the following validation:

```python
# Validate working directory if provided
if task_data.working_directory:
    working_dir = os.path.abspath(task_data.working_directory)

    # Check 1: Directory exists
    if not os.path.exists(working_dir):
        raise HTTPException(
            status_code=400,
            detail=f"Working directory does not exist: {working_dir}"
        )

    # Check 2: Path is a directory (not a file)
    if not os.path.isdir(working_dir):
        raise HTTPException(
            status_code=400,
            detail=f"Working directory path is not a directory: {working_dir}"
        )

    # Check 3: Directory is readable and executable
    if not os.access(working_dir, os.R_OK | os.X_OK):
        raise HTTPException(
            status_code=400,
            detail=f"Working directory is not accessible (check permissions): {working_dir}"
        )
```

### Validated Scenarios

✅ **Valid Scenarios** (Should succeed):
1. Absolute paths to existing directories
2. Relative paths that resolve to existing directories
3. Directories with spaces in the name
4. Directories with Unicode characters
5. Nested directory structures
6. Symlinks to valid directories
7. System directories (/, ~, /tmp)
8. No working directory provided (uses default)

❌ **Invalid Scenarios** (Should fail with HTTP 400):
1. Non-existent directory paths
2. File paths (not directories)
3. Broken symlinks
4. Directories without read/execute permissions

### Edge Cases Tested

1. **Path normalization**: Relative paths converted to absolute
2. **Permission validation**: Checks for both read (R_OK) and execute (X_OK) permissions
3. **Unicode support**: Full Unicode character support in paths
4. **Symlink handling**: Properly follows symlinks to validate target
5. **Special characters**: Handles spaces, dashes, dots, and other special characters
6. **Very long paths**: Tests filesystem limits
7. **Concurrent validation**: Multiple tasks can use the same working directory

## Test Quality Metrics

- **Total Test Cases**: 19+ (unit) + 20+ (integration) = 39+ tests
- **Code Coverage**: Validates all critical paths in directory validation
- **Edge Cases**: Comprehensive coverage of special scenarios
- **Cross-Platform**: Tests account for Windows vs. Unix differences
- **Maintainability**: Clear test names, good documentation, reusable fixtures

## Known Limitations

1. **Permission tests on Windows**: Some permission tests are skipped on Windows due to different permission models
2. **Integration tests**: Require database and full app setup
3. **Symlink tests**: May skip on platforms without symlink support

## Recommendations

1. ✅ **Directory validation is working correctly** - All unit tests pass
2. ✅ **Comprehensive test coverage** - Covers valid, invalid, and edge cases
3. ✅ **Error messages are clear** - Users get specific feedback on validation failures
4. 📝 **Run integration tests** - Verify full API workflow when database is available
5. 📝 **Add performance tests** - Test validation with many concurrent requests
6. 📝 **Add security tests** - Test directory traversal prevention

## Next Steps

1. Set up test database for integration tests
2. Run full integration test suite
3. Add continuous integration (CI) pipeline
4. Monitor test coverage metrics
5. Add more edge cases as they're discovered in production
