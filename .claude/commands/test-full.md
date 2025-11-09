---
description: Run complete test suite (core + dashboard + type checks)
---

Run the complete test suite for the orchestrator project.

**Current Status**:
- Core orchestrator: 270 tests, 64% coverage ✨
- Dashboard backend: 19 tests, 100% passing ✅
- Type hints: 100% coverage on public APIs
- Storage layer: 95% coverage (was 0%)

**Priority**: Improve core orchestrator coverage from 64% → 80% target

---

## Test Execution

### 1. Core Orchestrator Tests (Priority)

Run with coverage report:
```bash
pytest tests/ -v --cov=src/orchestrator --cov-report=term-missing
```

**Expected**:
- 199 tests passing
- Current coverage: ~51%
- **Target for v1.0**: >80% coverage

**Coverage gaps** (need tests):
- `orchestrator.py`: 34% (critical - main class)
- `executor.py`: 13% (critical - workflow execution)
- `context_parser.py`: 19% (important - context optimization)
- `database.py`: 0% (storage layer)
- `progress.py`: 30% (progress tracking)

### 2. Dashboard Backend Tests

```bash
pytest dashboard/backend/tests -v
```

**Expected**: 19 tests passing (directory validation utilities)

### 3. Type Checking

```bash
mypy src/orchestrator --ignore-missing-imports
```

**Expected**: No errors (type hints are validated by tests)

### 4. Linting

```bash
ruff check src/orchestrator dashboard/backend/app
black --check src/orchestrator dashboard/backend/app
```

**Expected**: Clean (or document any acceptable warnings)

---

## Summary Report

After running all tests, report:

1. **Test Results**:
   - Core: X/270 passed
   - Dashboard: X/19 passed
   - Total: X/289 tests

2. **Coverage**:
   - Current: X%
   - Target: 80%
   - Gap: List critical uncovered modules

3. **Type Checking**: Pass/Fail with error count

4. **Linting**: Pass/Fail with issue count

5. **Next Steps**:
   - If failures: Recommend specific fixes
   - If coverage < 80%: Suggest which modules need tests first
   - If all pass: Confirm code is ready to commit

---

## Coverage Improvement Plan

**Phase 1** (Critical - get to 60%):
- Add integration tests for `orchestrator.py`
- Add workflow execution tests for `executor.py`
- Add context parsing tests for `context_parser.py`

**Phase 2** (Important - get to 70%):
- Add progress tracking tests
- Add monitoring tests
- Add agent lifecycle tests

**Phase 3** (Complete - get to 80%):
- Add database storage tests
- Add edge case tests
- Add error scenario tests

See ROADMAP.md "Testing & Reliability" section for details.
