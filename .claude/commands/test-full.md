---
description: Run complete test suite (core + dashboard + type checks)
---

Run the complete test suite for the orchestrator project.

**Current Status**:
- Core orchestrator: 199 tests, 51% coverage
- Dashboard backend: 35 tests, 100% pass rate
- Type hints: 100% coverage on public APIs

**Priority**: Improve core orchestrator coverage from 51% → 80% target

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
cd dashboard/backend && pytest tests/ -v && cd ../..
```

**Expected**: 35 tests passing (working directory validation)

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
   - Core: X/199 passed
   - Dashboard: X/35 passed
   - Total: X/234 tests

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
