---
description: Validate architecture independence and dependency rules
---

Validate the orchestrator architecture follows library-first design:

1. **Core independence check**:
   - Execute: `grep -r "from.*dashboard" src/orchestrator/`
   - Execute: `grep -r "import.*dashboard" src/orchestrator/`
   - If any matches found: CRITICAL ERROR - report violations

2. **Dashboard dependency check**:
   - Execute: `grep -r "from orchestrator" dashboard/backend/app/`
   - Verify imports are ONLY in `services/orchestrator_executor.py`
   - If imports elsewhere, warn about tight coupling

3. **Database separation**:
   - Check for hardcoded paths to dashboard database
   - Verify orchestrator uses configurable paths
   - Execute: `grep -r "dashboard.*\.db" src/orchestrator/`

4. **Log directory separation**:
   - Verify CLI logs to `agent_logs/` (root)
   - Verify dashboard logs to `dashboard/backend/agent_logs/`
   - Check for hardcoded log paths in core

5. **Configuration independence**:
   - Check that orchestrator reads from environment variables
   - Verify no dashboard-specific config in core
   - Execute: `grep -r "DASHBOARD" src/orchestrator/`

6. **Type definitions**:
   - Verify core types are in `src/orchestrator/core/types.py`
   - Check dashboard doesn't define conflicting types
   - Execute: `rg "class Task\(" --type py`

7. **Summary report**:
   - ✅ PASS: No violations
   - ⚠️ WARN: Potential coupling issues
   - ❌ FAIL: Architecture violations found
   - Provide specific fixes for each violation

8. **Generate architecture diagram**:
   - Create Mermaid diagram showing current dependencies
   - Highlight violations in red
