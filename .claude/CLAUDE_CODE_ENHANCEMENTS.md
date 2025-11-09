# Claude Code Feature Enhancements for Orchestrator

Tailored recommendations for Claude Code features that enhance the orchestrator development workflow.

**Impact Priority**: High → Medium → Low
**Time Savings**: Estimated cumulative savings of 15-20 hours per month

---

## Table of Contents

1. [Custom Slash Commands](#1-custom-slash-commands)
2. [Hooks for Safety-Critical Operations](#2-hooks-for-safety-critical-operations)
3. [MCP Server Integrations](#3-mcp-server-integrations)
4. [Permissions Configuration](#4-permissions-configuration)
5. [Subagent Workflows](#5-subagent-workflows)
6. [Implementation Timeline](#implementation-timeline)

---

## 1. Custom Slash Commands

### 1.1 `/test-full` - Complete Test Suite Runner

**Impact**: 🟢 HIGH - Prevents errors before commits
**Time Saved**: 10-15 minutes per development session
**Use Case**: Run comprehensive test suite before committing changes

**Implementation**:

```bash
# File: .claude/commands/test-full.md
---
description: Run complete test suite (core + dashboard + type checks)
---

Run the complete test suite for the orchestrator project:

1. **Core orchestrator tests**:
   - Run: `pytest tests/ -v --cov=orchestrator --cov-report=term-missing`
   - Check coverage is above 70%

2. **Dashboard backend tests**:
   - Change to: `cd dashboard/backend`
   - Run: `pytest tests/ -v`
   - Return to root: `cd ../..`

3. **Type checking**:
   - Run: `mypy src/orchestrator --ignore-missing-imports`

4. **Linting**:
   - Run: `ruff check src/orchestrator dashboard/backend/app`
   - Run: `black --check src/orchestrator dashboard/backend/app`

5. **Summary**:
   - Report which tests passed/failed
   - Show coverage percentage
   - List any type errors or linting issues
   - Recommend fixes if failures occurred

If all tests pass, confirm the code is ready to commit.
```

**Usage Example**:
```
User: /test-full
Claude: Running complete test suite...
  ✓ Core tests: 45/45 passed (coverage: 78%)
  ✓ Dashboard tests: 23/23 passed
  ✓ Type checking: No errors
  ✗ Linting: 3 formatting issues in agent.py

  Fixing formatting issues...
  ✓ All checks passed! Code is ready to commit.
```

---

### 1.2 `/deploy-dashboard` - Full Dashboard Deployment

**Impact**: 🟢 HIGH - Reduces deployment errors
**Time Saved**: 5-10 minutes per deployment
**Use Case**: Safe, tested deployment of dashboard changes

**Implementation**:

```bash
# File: .claude/commands/deploy-dashboard.md
---
description: Deploy dashboard with safety checks and health verification
---

Deploy the dashboard to production with comprehensive safety checks:

1. **Pre-deployment checks**:
   - Verify git status is clean: `git status`
   - If uncommitted changes exist, ask user if they want to commit first
   - Verify current branch: `git branch --show-current`
   - If not on main, ask user if they want to continue

2. **Run tests**:
   - Execute: `cd dashboard/backend && pytest tests/ -v`
   - Execute: `cd ../frontend && npm run build`
   - Return to root: `cd ../..`
   - If tests fail, STOP and report errors

3. **Database migration check**:
   - Check for pending migrations: `cd dashboard/backend && alembic current`
   - If migrations pending, ask user: "Apply migrations? [y/n]"
   - If yes: `alembic upgrade head`

4. **Docker deployment**:
   - Stop existing containers: `cd dashboard && docker-compose down`
   - Build and start: `docker-compose up -d --build`
   - Wait 10 seconds for startup

5. **Health checks**:
   - Test backend: `curl -f http://localhost:8000/health`
   - Test frontend: `curl -f http://localhost:5173`
   - Check WebSocket: `curl -f http://localhost:8000/api/v1/ws/tasks`
   - Report status of each service

6. **Post-deployment verification**:
   - Show logs: `docker-compose logs --tail=50`
   - Ask user: "Deployment successful. Monitor logs? [y/n]"

7. **Summary**:
   - Report deployment time
   - List all services started
   - Provide access URLs
```

**Usage Example**:
```
User: /deploy-dashboard
Claude: Starting dashboard deployment...
  ✓ Git status: clean
  ✓ Tests passed
  ✓ Database migrations: up to date
  ✓ Docker build: complete
  ✓ Health checks: all services healthy

  Dashboard deployed successfully in 45 seconds!
  - Backend: http://localhost:8000/api/docs
  - Frontend: http://localhost:5173
```

---

### 1.3 `/new-migration` - Database Migration Creator

**Impact**: 🟡 MEDIUM - Prevents schema errors
**Time Saved**: 5-8 minutes per migration
**Use Case**: Create and verify database migrations safely

**Implementation**:

```bash
# File: .claude/commands/new-migration.md
---
description: Create new Alembic migration with verification
---

Create a new database migration:

1. **Get migration details**:
   - Ask user: "What changes are you making to the database schema?"
   - Ask user: "Migration name (snake_case):"

2. **Check current state**:
   - Execute: `cd dashboard/backend`
   - Execute: `alembic current` to show current revision
   - Execute: `git diff app/models/` to show model changes

3. **Create migration**:
   - Execute: `alembic revision --autogenerate -m "{user_provided_name}"`
   - Read the generated migration file
   - Analyze upgrade() and downgrade() functions

4. **Safety checks**:
   - Verify no data loss operations (DROP TABLE, DROP COLUMN without backup)
   - Check for missing indexes on foreign keys
   - Verify default values for NOT NULL columns
   - If issues found, warn user and suggest fixes

5. **Create manual SQL fallback**:
   - Generate equivalent SQL file: `migration_{name}.sql`
   - Add to same directory as migration
   - Include both upgrade and downgrade SQL

6. **Test migration**:
   - Ask user: "Test migration on a copy of the database? [y/n]"
   - If yes:
     - `cp orchestrator.db orchestrator_backup.db`
     - `alembic upgrade head`
     - `alembic downgrade -1`
     - `alembic upgrade head`
     - Report if successful

7. **Summary**:
   - Show migration file path
   - Show SQL file path
   - List changes detected
   - Confirm migration is ready
```

**Usage Example**:
```
User: /new-migration
Claude: What changes are you making to the database schema?
User: Adding execution_mode column to tasks table
Claude: Migration name (snake_case):
User: add_execution_mode_to_tasks
Claude: Creating migration...
  ✓ Current revision: c9f8e4a21234
  ✓ Detected changes: 1 column addition
  ✓ Generated: 2025_11_08_1200-add_execution_mode_to_tasks.py
  ✓ Created SQL fallback
  ✗ Warning: Missing default value for new NOT NULL column

  Suggested fix: Add server_default='sequential' to Column()
```

---

### 1.4 `/check-arch` - Architecture Dependency Validator

**Impact**: 🟢 HIGH - Prevents architectural violations
**Time Saved**: Critical - prevents hours of refactoring
**Use Case**: Ensure core orchestrator remains integration-agnostic

**Implementation**:

```bash
# File: .claude/commands/check-arch.md
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
```

**Usage Example**:
```
User: /check-arch
Claude: Validating architecture...
  ✓ Core orchestrator: No dashboard imports
  ✓ Dashboard imports: Only in orchestrator_executor.py
  ✓ Database separation: Correct
  ✗ Found hardcoded path in agent_logger.py:15

  VIOLATION: src/orchestrator/observability/agent_logger.py:15
  Found: LOGS_DIR = "dashboard/backend/agent_logs"
  Fix: Use environment variable or constructor parameter

  Architecture score: 7/8 (87.5%)
```

---

### 1.5 `/release-prep` - Release Preparation Checklist

**Impact**: 🟢 HIGH - Prevents release errors
**Time Saved**: 15-20 minutes per release
**Use Case**: Automated pre-release verification

**Implementation**:

```bash
# File: .claude/commands/release-prep.md
---
description: Complete release preparation checklist with verification
---

Prepare for a new release:

1. **Version verification**:
   - Ask user: "New version number (e.g., 0.1.6):"
   - Check current version in `README.md`, `pyproject.toml`, `dashboard/backend/app/main.py`
   - Verify versions are consistent

2. **Update version numbers**:
   - Update `README.md` line 5
   - Update `pyproject.toml` line 7
   - Update `dashboard/backend/app/main.py` lines 49, 105, 137
   - Execute: `git diff` to show changes

3. **Run full test suite**:
   - Execute: `pytest tests/ -v --cov=orchestrator`
   - Execute: `cd dashboard/backend && pytest tests/`
   - Execute: `mypy src/orchestrator --ignore-missing-imports`
   - All must pass to continue

4. **Documentation check**:
   - Verify `CHANGELOG.md` has entry for new version
   - Check `README.md` has migration instructions if DB schema changed
   - Verify `ROADMAP.md` is updated
   - Check all .md files for broken links

5. **Security audit**:
   - Execute: `grep -r "api[_-]key\|secret\|password\|token" --include="*.py" --include="*.ts"`
   - Verify no secrets in code (only in .env files)
   - Check `.gitignore` includes sensitive files

6. **Migration verification**:
   - List pending migrations: `cd dashboard/backend && alembic current`
   - If migrations exist, verify `migration_fix.sql` is updated
   - Test manual migration: `sqlite3 test.db < migration_fix.sql`

7. **Build verification**:
   - Execute: `pip install -e .`
   - Execute: `orchestrator --version`
   - Test CLI: `orchestrator execute "test task"`

8. **Docker build test**:
   - Execute: `cd dashboard && docker-compose build`
   - Verify no build errors
   - Test startup: `docker-compose up -d`
   - Test health: `curl http://localhost:8000/health`
   - Cleanup: `docker-compose down`

9. **Create release checklist**:
   - Generate markdown checklist of completed items
   - Create git commit message template
   - Create git tag command
   - Create release notes template

10. **Summary**:
    - Show all checks passed/failed
    - Provide git commands to execute:
      ```
      git add .
      git commit -m "chore: Release v{version}"
      git tag -a v{version} -m "Release v{version}: {summary}"
      git push origin main
      git push origin v{version}
      ```
```

**Usage Example**:
```
User: /release-prep
Claude: New version number (e.g., 0.1.6):
User: 0.1.6
Claude: Preparing release v0.1.6...
  ✓ Updated version numbers (3 files)
  ✓ All tests passed (68/68)
  ✓ Documentation current
  ✓ No secrets in code
  ✓ Migration verified
  ✓ Build successful
  ✓ Docker tested

  Ready to release! Execute:
  git add .
  git commit -m "chore: Release v0.1.6"
  git tag -a v0.1.6 -m "Release v0.1.6"
  git push origin main && git push origin v0.1.6
```

---

### 1.6 `/task-debug` - Task Debugging Assistant

**Impact**: 🟡 MEDIUM - Speeds up debugging
**Time Saved**: 10-15 minutes per debug session
**Use Case**: Quickly diagnose task execution failures

**Implementation**:

```bash
# File: .claude/commands/task-debug.md
---
description: Debug failed orchestrator task with log analysis
---

Debug a failed orchestrator task:

1. **Get task ID**:
   - Ask user: "Task ID to debug (or 'latest' for most recent):"
   - If 'latest':
     - Execute: `ls -t agent_logs/ | head -1` for CLI tasks
     - Execute: `sqlite3 dashboard/backend/orchestrator.db "SELECT id FROM tasks ORDER BY created_at DESC LIMIT 1"` for dashboard tasks

2. **Locate logs**:
   - Check CLI logs: `agent_logs/{task_id}/`
   - Check dashboard logs: `dashboard/backend/agent_logs/{task_id}/`
   - Report which location has logs

3. **Analyze task structure**:
   - Read `plan.json` to understand intended workflow
   - List all agent subdirectories
   - Check which agents completed vs. failed

4. **For each agent**:
   - Read `prompt.txt` to see task given to agent
   - Read `text.txt` for agent's thinking and output
   - Read `tools.jsonl` for tool calls made
   - Identify where failure occurred

5. **Common failure patterns**:
   - Check for context window overflow: `grep "context.*limit" */text.txt`
   - Check for tool errors: `grep -i "error\|exception\|failed" */tools.jsonl`
   - Check for timeout: `grep -i "timeout\|timed out" */text.txt`
   - Check for file access issues: `grep -i "permission\|not found" */text.txt`

6. **Cost and performance analysis**:
   - Calculate total tokens used from all agents
   - Calculate total execution time
   - Identify most expensive agent
   - Identify slowest agent

7. **Root cause identification**:
   - Pinpoint exact failure point (agent, line, error)
   - Explain why failure occurred
   - Check if issue is prompt-related, tool-related, or data-related

8. **Recommendations**:
   - Suggest prompt improvements
   - Suggest workflow changes
   - Suggest tool usage improvements
   - Provide example fixed prompt if applicable

9. **Summary report**:
   ```
   Task: {task_id}
   Status: FAILED
   Failed at: BUILDER agent (step 3/5)
   Root cause: File not found error
   Cost: $0.42 (3 agents completed)
   Duration: 145s

   Fix: Update PLANNER prompt to verify file paths exist before BUILDER
   ```
```

**Usage Example**:
```
User: /task-debug
Claude: Task ID to debug (or 'latest' for most recent):
User: latest
Claude: Debugging task 803a350b-117b-4fbc-88f2-7b695ce95e6d...

  Task failed at BUILDER agent (step 3/5)

  Root cause: FileNotFoundError in tool call
  - BUILDER tried to edit src/orchestrator/core/agent.py
  - File path was incorrect (typo: "agnet.py")

  Timeline:
  ✓ PLANNER (45s, $0.12) - Created plan
  ✓ BUILDER started (0s, $0.00)
  ✗ BUILDER failed (23s, $0.08) - File not found

  Recommendation: Add file existence check to PLANNER prompt:
  "Before creating tasks, verify all file paths exist using glob"
```

---

### 1.7 `/docs-sync` - Documentation Synchronization

**Impact**: 🟡 MEDIUM - Prevents documentation drift
**Time Saved**: 5-10 minutes per code change
**Use Case**: Keep documentation in sync with code changes

**Implementation**:

```bash
# File: .claude/commands/docs-sync.md
---
description: Synchronize documentation with recent code changes
---

Synchronize documentation after code changes:

1. **Detect recent changes**:
   - Execute: `git diff main --name-only`
   - Categorize changes:
     - Core orchestrator changes
     - Dashboard changes
     - New features
     - Bug fixes
     - Breaking changes

2. **Check affected documentation**:
   - If `src/orchestrator/core/types.py` changed: Check README.md agent roles
   - If `dashboard/backend/app/models/*.py` changed: Check dashboard/README.md schema docs
   - If `pyproject.toml` changed: Check README.md installation instructions
   - If new examples added: Check README.md examples section
   - If API endpoints changed: Check INTEGRATION_GUIDE.md

3. **Version-specific checks**:
   - If breaking changes: Update ROADMAP.md and CHANGELOG.md
   - If new features: Update POSSIBLE_ENHANCEMENTS.md to move from planned → completed
   - If architecture changes: Update PROJECT_STRUCTURE.md

4. **Documentation updates**:
   - For each outdated doc:
     - Show current content
     - Show what needs updating
     - Ask user: "Update automatically? [y/n]"
     - If yes, make updates

5. **Cross-reference verification**:
   - Check all links in README.md are valid
   - Execute: `grep -o '\[.*\](.*\.md)' README.md | sed 's/.*(\(.*\))/\1/'`
   - Verify each linked file exists
   - Report broken links

6. **Code example verification**:
   - Extract all code blocks from .md files
   - Check if imports are still valid
   - Check if function signatures match current code
   - Report outdated examples

7. **Generate sync report**:
   ```
   Documentation Sync Report
   -------------------------
   ✓ README.md: Current
   ✗ INTEGRATION_GUIDE.md: Outdated (3 sections)
   ✓ PROJECT_STRUCTURE.md: Current
   ✗ dashboard/README.md: Missing new API endpoints

   Suggested updates: 2 files, 5 sections
   Estimated time: 3 minutes
   ```

8. **Auto-update option**:
   - Ask user: "Apply all suggested updates? [y/n]"
   - If yes, update all outdated documentation
```

**Usage Example**:
```
User: /docs-sync
Claude: Analyzing recent changes...

  Detected changes:
  - Added execution_mode to Task model
  - New API endpoint: POST /api/v1/tasks/cancel
  - Updated AgentRole enum (added OPTIMIZER role)

  Documentation affected:
  ✗ README.md - Missing OPTIMIZER role in agent roles section
  ✗ INTEGRATION_GUIDE.md - Missing cancel task example
  ✓ PROJECT_STRUCTURE.md - Current

  Update automatically? [y/n]
User: y
Claude: Updated 2 files (5 sections). Documentation is now in sync.
```

---

### 1.8 `/perf-profile` - Performance Profiler

**Impact**: 🟡 MEDIUM - Identifies bottlenecks
**Time Saved**: 20-30 minutes per optimization session
**Use Case**: Profile and optimize orchestrator performance

**Implementation**:

```bash
# File: .claude/commands/perf-profile.md
---
description: Profile orchestrator performance and identify bottlenecks
---

Profile orchestrator performance:

1. **Setup profiling**:
   - Ask user: "Profile CLI task or dashboard task? [cli/dashboard]"
   - Ask user: "Task type to profile (e.g., feature_implementation):"
   - Install profiling tools if needed: `pip install py-spy memory-profiler`

2. **Run profiled execution**:
   - For CLI:
     ```bash
     py-spy record -o profile.svg -- orchestrator execute "test task" --task-type {type}
     ```
   - For dashboard:
     ```bash
     py-spy record -o profile.svg --pid $(pgrep -f "uvicorn app.main:app")
     ```
     Then trigger task via API

3. **Collect metrics**:
   - Total execution time
   - Time per agent
   - Time per workflow step
   - Database query time
   - File I/O time
   - API call time (to Claude)

4. **Analyze profile data**:
   - Parse `profile.svg` flame graph
   - Identify top 10 slowest functions
   - Calculate percentage of time in:
     - Agent execution
     - Database operations
     - File operations
     - Network calls
     - Overhead (monitoring, logging)

5. **Database performance**:
   - Execute: `sqlite3 orchestrator.db ".timer on" ".schema" "SELECT * FROM tasks LIMIT 1000"`
   - Check query execution times
   - Identify missing indexes
   - Check for N+1 queries

6. **Memory profiling**:
   - Execute: `mprof run orchestrator execute "test task"`
   - Execute: `mprof plot -o memory.png`
   - Identify memory leaks
   - Check peak memory usage

7. **Bottleneck identification**:
   - Rank issues by impact:
     - 🔴 Critical: >30% of execution time
     - 🟡 Medium: 10-30% of execution time
     - 🟢 Minor: <10% of execution time

8. **Optimization recommendations**:
   - For slow database queries: Add indexes, use batch operations
   - For slow file I/O: Cache reads, batch writes
   - For slow API calls: Use parallel execution, optimize prompts
   - For memory issues: Use generators, clear caches

9. **Generate report**:
   ```
   Performance Profile Report
   --------------------------
   Task: feature_implementation
   Total time: 145s

   Time breakdown:
   - ANALYST: 45s (31%) 🔴
   - PLANNER: 20s (14%)
   - BUILDER: 50s (34%) 🔴
   - TESTER: 20s (14%)
   - REVIEWER: 10s (7%)

   Bottlenecks:
   1. ANALYST spending 30s reading files (can cache)
   2. BUILDER making 15 sequential file writes (can batch)
   3. Database: 50 queries for agent updates (can batch)

   Recommended optimizations:
   - Cache file reads in ANALYST
   - Batch file writes in BUILDER
   - Use bulk_update for agent metrics

   Potential speedup: 30-40% (145s → 90s)
   ```
```

**Usage Example**:
```
User: /perf-profile
Claude: Profile CLI task or dashboard task? [cli/dashboard]
User: cli
Claude: Task type to profile:
User: feature_implementation
Claude: Profiling execution...

  Performance Profile:
  Total: 145s

  Top bottlenecks:
  🔴 ANALYST file reads: 30s (21%)
  🔴 BUILDER sequential writes: 25s (17%)
  🟡 Database agent updates: 20s (14%)

  Optimization potential: 35% faster

  Recommendations:
  1. Implement file read cache (saves ~20s)
  2. Batch file writes (saves ~15s)
  3. Use bulk SQL updates (saves ~10s)
```

---

## 2. Hooks for Safety-Critical Operations

### 2.1 Pre-Commit Hook - Architecture Validation

**Impact**: 🟢 HIGH - Prevents architectural violations
**Time Saved**: Critical - prevents hours of debugging

**Implementation**:

```bash
# File: .claude/hooks/pre-commit.sh
#!/bin/bash

echo "🔍 Running pre-commit architecture validation..."

# Check for dashboard imports in core
VIOLATIONS=$(grep -r "from.*dashboard\|import.*dashboard" src/orchestrator/ 2>/dev/null)

if [ -n "$VIOLATIONS" ]; then
    echo "❌ ARCHITECTURE VIOLATION DETECTED!"
    echo ""
    echo "Core orchestrator must not import from dashboard:"
    echo "$VIOLATIONS"
    echo ""
    echo "Please remove these imports. Core must remain integration-agnostic."
    echo ""
    echo "Blocking commit. Fix violations and try again."
    exit 1
fi

# Check for hardcoded database paths
DB_PATHS=$(grep -r "orchestrator\.db" src/orchestrator/ 2>/dev/null | grep -v "test\|example")

if [ -n "$DB_PATHS" ]; then
    echo "⚠️  WARNING: Hardcoded database paths detected:"
    echo "$DB_PATHS"
    echo ""
    echo "Consider using environment variables for database paths."
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for secrets
SECRETS=$(grep -ri "api[_-]key\|secret\|password.*=" src/ dashboard/ --include="*.py" --include="*.ts" | grep -v "\.env\|config\.py\|settings")

if [ -n "$SECRETS" ]; then
    echo "🔐 WARNING: Potential secrets detected:"
    echo "$SECRETS"
    echo ""
    read -p "These look like secrets. Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Architecture validation passed!"
exit 0
```

**Configuration in .claude/config.yaml**:

```yaml
hooks:
  pre-commit:
    script: .claude/hooks/pre-commit.sh
    enabled: true
    description: "Validate architecture and check for secrets"
```

---

### 2.2 Pre-Push Hook - Test Suite Runner

**Impact**: 🟢 HIGH - Prevents broken builds
**Time Saved**: Critical - prevents failed deployments

**Implementation**:

```bash
# File: .claude/hooks/pre-push.sh
#!/bin/bash

echo "🧪 Running pre-push test suite..."

# Run core tests
echo "Running core orchestrator tests..."
pytest tests/ -v --cov=orchestrator --cov-report=term-missing --cov-fail-under=70

if [ $? -ne 0 ]; then
    echo "❌ Core tests failed. Fix tests before pushing."
    exit 1
fi

# Run dashboard tests
echo "Running dashboard backend tests..."
cd dashboard/backend
pytest tests/ -v

if [ $? -ne 0 ]; then
    echo "❌ Dashboard tests failed. Fix tests before pushing."
    cd ../..
    exit 1
fi
cd ../..

# Type checking
echo "Running type checks..."
mypy src/orchestrator --ignore-missing-imports

if [ $? -ne 0 ]; then
    echo "⚠️  Type check warnings detected. Review before pushing."
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ All pre-push checks passed!"
exit 0
```

**Configuration in .claude/config.yaml**:

```yaml
hooks:
  pre-push:
    script: .claude/hooks/pre-push.sh
    enabled: true
    description: "Run full test suite before push"
```

---

### 2.3 Tool Call Hook - Database Operation Safety

**Impact**: 🟡 MEDIUM - Prevents data loss
**Time Saved**: 10-20 minutes recovering from mistakes

**Implementation**:

```yaml
# File: .claude/config.yaml
hooks:
  tool-call:
    enabled: true
    description: "Safety checks for database operations"
    rules:
      - pattern: "DROP TABLE|DELETE FROM|TRUNCATE"
        action: confirm
        message: "⚠️  Destructive database operation detected. Continue?"

      - pattern: "ALTER TABLE.*DROP COLUMN"
        action: confirm
        message: "⚠️  Dropping column. This is irreversible. Continue?"

      - pattern: "docker-compose down -v"
        action: confirm
        message: "⚠️  This will delete all volumes. Continue?"

      - pattern: "rm -rf"
        action: confirm
        message: "⚠️  Recursive delete detected. Continue?"

      - pattern: "git push.*--force"
        action: block
        message: "❌ Force push to main is not allowed. Use /deploy-dashboard instead."
```

---

## 3. MCP Server Integrations

### 3.1 GitHub MCP Server - Issue and PR Management

**Impact**: 🟢 HIGH - Automates issue tracking
**Time Saved**: 15-20 minutes per issue/PR
**Use Case**: Create issues from failed tasks, manage PRs

**Installation**:

```bash
# Install GitHub MCP server
npm install -g @anthropic-ai/mcp-server-github

# Configure in Claude Code
# File: ~/.config/claude-code/mcp.json
{
  "servers": {
    "github": {
      "command": "mcp-server-github",
      "env": {
        "GITHUB_TOKEN": "your-github-token",
        "GITHUB_REPO": "jeffjacobsen/orchestrator"
      }
    }
  }
}
```

**Usage Examples**:

```bash
# File: .claude/commands/create-issue-from-task.md
---
description: Create GitHub issue from failed orchestrator task
---

Create a GitHub issue from a failed task:

1. Ask user: "Task ID that failed:"
2. Read task logs using /task-debug workflow
3. Extract:
   - Task description
   - Failure point
   - Error message
   - Agent logs
4. Create GitHub issue using MCP:
   ```
   Title: Task failed: {task description}

   **Task ID**: {task_id}
   **Failed at**: {agent name} (step {N})
   **Error**: {error message}

   **Reproduction**:
   ```bash
   orchestrator execute "{task description}"
   ```

   **Logs**:
   ```
   {relevant agent logs}
   ```

   **Expected behavior**: Task should complete successfully
   **Actual behavior**: {failure description}

   Labels: bug, orchestrator
   ```
5. Ask user: "Create PR to fix this? [y/n]"
```

---

### 3.2 PostgreSQL MCP Server - Production Database

**Impact**: 🟡 MEDIUM - Enables production deployment
**Time Saved**: 30 minutes setup, ongoing management
**Use Case**: Scale beyond SQLite for production

**Installation**:

```bash
# Install PostgreSQL MCP server
npm install -g @anthropic-ai/mcp-server-postgres

# Configure in Claude Code
# File: ~/.config/claude-code/mcp.json
{
  "servers": {
    "postgres": {
      "command": "mcp-server-postgres",
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://user:pass@localhost:5432/orchestrator"
      }
    }
  }
}
```

**Usage Examples**:

```bash
# File: .claude/commands/migrate-to-postgres.md
---
description: Migrate from SQLite to PostgreSQL for production
---

Migrate to PostgreSQL:

1. **Backup SQLite data**:
   - Execute: `sqlite3 orchestrator.db .dump > backup.sql`

2. **Create PostgreSQL database**:
   - Using MCP: CREATE DATABASE orchestrator;

3. **Update configuration**:
   - Edit `dashboard/backend/.env`:
     ```
     DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/orchestrator
     ```

4. **Update dependencies**:
   - Add to `requirements.txt`: `asyncpg`, `psycopg2-binary`
   - Execute: `pip install asyncpg psycopg2-binary`

5. **Run migrations**:
   - Execute: `cd dashboard/backend && alembic upgrade head`

6. **Migrate data**:
   - For each table:
     - Export from SQLite
     - Transform to PostgreSQL format
     - Import using MCP

7. **Verify migration**:
   - Check row counts match
   - Test queries
   - Verify foreign keys

8. **Update docker-compose.yml**:
   - Add PostgreSQL service
   - Update backend DATABASE_URL
```

---

### 3.3 Prometheus MCP Server - Advanced Metrics

**Impact**: 🟡 MEDIUM - Production monitoring
**Time Saved**: 2-3 hours setup, critical for production
**Use Case**: Track orchestrator metrics in production

**Installation**:

```bash
# Install Prometheus MCP server
npm install -g @anthropic-ai/mcp-server-prometheus

# Configure in Claude Code
# File: ~/.config/claude-code/mcp.json
{
  "servers": {
    "prometheus": {
      "command": "mcp-server-prometheus",
      "env": {
        "PROMETHEUS_URL": "http://localhost:9090"
      }
    }
  }
}
```

**Usage Examples**:

```bash
# File: .claude/commands/setup-metrics.md
---
description: Setup Prometheus metrics for orchestrator
---

Setup production metrics:

1. **Add metrics endpoint to FastAPI**:
   - Install: `pip install prometheus-fastapi-instrumentator`
   - Add to `app/main.py`:
     ```python
     from prometheus_fastapi_instrumentator import Instrumentator

     Instrumentator().instrument(app).expose(app)
     ```

2. **Add custom metrics**:
   - Create `app/metrics.py`:
     ```python
     from prometheus_client import Counter, Histogram, Gauge

     task_total = Counter('orchestrator_tasks_total', 'Total tasks')
     task_duration = Histogram('orchestrator_task_duration_seconds', 'Task duration')
     agent_cost = Histogram('orchestrator_agent_cost_usd', 'Agent cost')
     active_agents = Gauge('orchestrator_active_agents', 'Active agents')
     ```

3. **Update orchestrator_executor.py**:
   - Import metrics
   - Increment counters on task start/complete
   - Record histograms for duration/cost

4. **Create Prometheus config**:
   - File: `prometheus.yml`
   - Add scrape target for orchestrator

5. **Setup Grafana dashboard**:
   - Create dashboard with:
     - Tasks per hour
     - Average task cost
     - Average task duration
     - Agent count over time
     - Error rate
```

---

## 4. Permissions Configuration

**Impact**: 🟢 HIGH - Security and safety
**Time Saved**: Critical - prevents accidents

**Implementation**:

```yaml
# File: .claude/config.yaml
permissions:
  # Allow common development operations
  - bash:
      allow:
        # Testing
        - pytest*
        - mypy*
        - ruff*
        - black*

        # Git operations (safe)
        - git status*
        - git diff*
        - git log*
        - git add*
        - git commit*
        - git push origin main
        - git tag*

        # Package management
        - pip install*
        - npm install*
        - npm run*

        # Docker (development)
        - docker-compose up*
        - docker-compose down
        - docker-compose logs*
        - docker-compose ps*

        # Database operations (read-only)
        - sqlite3*SELECT*
        - sqlite3*PRAGMA*

        # Orchestrator CLI
        - orchestrator*

      deny:
        # Dangerous git operations
        - git push*--force*
        - git reset --hard*
        - git clean -fd*

        # Dangerous Docker operations
        - docker-compose down -v*
        - docker system prune*

        # Destructive database operations
        - sqlite3*DROP*
        - sqlite3*DELETE*
        - sqlite3*TRUNCATE*

        # Dangerous file operations
        - rm -rf*
        - rm -r /*

      confirm:
        # Deployment
        - git push origin v*
        - docker-compose build*

        # Database modifications
        - alembic upgrade*
        - alembic downgrade*
        - sqlite3*ALTER TABLE*
        - sqlite3*INSERT*
        - sqlite3*UPDATE*

  # File operations
  - write:
      allow:
        # Source code
        - src/**/*.py
        - dashboard/**/*.py
        - dashboard/**/*.ts
        - dashboard/**/*.tsx

        # Configuration
        - .claude/**/*
        - .env.example
        - *.md
        - pyproject.toml

        # Tests
        - tests/**/*.py
        - dashboard/backend/tests/**/*.py

      deny:
        # Sensitive files
        - .env
        - .git/**/*
        - **/*.db
        - **/secrets*

      confirm:
        # Database files
        - dashboard/backend/alembic/versions/*.py
        - **/migration*.sql

  # Read permissions (generally open)
  - read:
      allow:
        - "**/*"
      deny:
        - .env
        - **/secrets*
        - ~/.ssh/**/*
```

---

## 5. Subagent Workflows

### 5.1 Full-Stack Feature Implementation

**Impact**: 🟢 HIGH - Automates complete features
**Time Saved**: 2-3 hours per feature

**Usage Example**:

```
User: Implement real-time agent status updates in the dashboard

Claude: I'll launch subagents to implement this full-stack feature:

1. Backend Agent (API):
   - Add WebSocket event: agent_status_update
   - Update orchestrator_executor to emit events
   - Test with pytest

2. Frontend Agent (UI):
   - Add WebSocket listener in useWebSocket hook
   - Update AgentList component to show status
   - Add status badge component

3. Documentation Agent:
   - Update INTEGRATION_GUIDE.md with WebSocket events
   - Update dashboard/README.md with new feature

[Launches 3 parallel subagents]

✓ Backend: Added agent_status_update WebSocket event
✓ Frontend: Real-time status updates working
✓ Documentation: Updated integration guide

Feature complete and tested!
```

---

### 5.2 Database Migration with Testing

**Impact**: 🟡 MEDIUM - Safer migrations
**Time Saved**: 15-20 minutes per migration

**Usage Example**:

```
User: Add priority column to tasks table

Claude: I'll use subagents to safely implement this migration:

1. Schema Agent:
   - Add priority column to Task model
   - Create Alembic migration
   - Generate SQL fallback

2. Testing Agent:
   - Backup database
   - Test upgrade
   - Test downgrade
   - Verify data integrity

3. Documentation Agent:
   - Update PROJECT_STRUCTURE.md
   - Add migration to CHANGELOG.md
   - Update README migration instructions

[Launches 3 sequential subagents]

✓ Schema: Migration created
✓ Testing: Upgrade/downgrade tested successfully
✓ Documentation: Updated

Migration ready to commit!
```

---

## 6. Implementation Timeline

### Week 1: Foundation
- ✅ Create `.claude/commands/` directory
- ✅ Implement `/test-full` command
- ✅ Implement `/check-arch` command
- ✅ Setup pre-commit hook

**Time Investment**: 2 hours
**Immediate Benefit**: Prevent architectural violations

### Week 2: Development Workflow
- ✅ Implement `/deploy-dashboard` command
- ✅ Implement `/new-migration` command
- ✅ Setup pre-push hook
- ✅ Configure permissions

**Time Investment**: 3 hours
**Immediate Benefit**: Safer deployments

### Week 3: Debugging & Monitoring
- ✅ Implement `/task-debug` command
- ✅ Implement `/perf-profile` command
- ✅ Setup GitHub MCP server

**Time Investment**: 4 hours
**Immediate Benefit**: Faster debugging

### Week 4: Production Readiness
- ✅ Implement `/release-prep` command
- ✅ Implement `/docs-sync` command
- ✅ Setup Prometheus MCP server
- ✅ Setup PostgreSQL MCP server

**Time Investment**: 4 hours
**Immediate Benefit**: Production-ready monitoring

---

## Summary: ROI Analysis

| Feature | Time to Implement | Time Saved per Month | ROI Breakeven |
|---------|------------------|---------------------|---------------|
| `/test-full` | 30 min | 4-6 hours | Week 1 |
| `/check-arch` | 30 min | Critical (prevents refactors) | Immediate |
| `/deploy-dashboard` | 45 min | 2-3 hours | Week 2 |
| `/new-migration` | 45 min | 1-2 hours | Week 3 |
| `/task-debug` | 1 hour | 3-4 hours | Week 2 |
| `/release-prep` | 1 hour | 2-3 hours | Week 3 |
| `/docs-sync` | 45 min | 1-2 hours | Week 4 |
| `/perf-profile` | 1.5 hours | 1-2 hours | Week 5 |
| Pre-commit hook | 30 min | Critical (prevents bugs) | Immediate |
| Pre-push hook | 30 min | Critical (prevents broken builds) | Immediate |
| GitHub MCP | 45 min | 2-3 hours | Week 3 |
| Permissions config | 1 hour | Critical (prevents accidents) | Immediate |

**Total Implementation Time**: ~13 hours
**Total Monthly Time Savings**: 15-20+ hours
**Breakeven**: 3-4 weeks

---

## Quick Start

To get started immediately with the highest-impact features:

1. **Create commands directory**:
   ```bash
   mkdir -p .claude/commands .claude/hooks
   ```

2. **Implement `/test-full`** (copy from section 1.1)

3. **Implement `/check-arch`** (copy from section 1.4)

4. **Setup pre-commit hook** (copy from section 2.1)

5. **Configure permissions** (copy from section 4)

These 4 items take ~2 hours and provide immediate value by preventing errors.

---

## Additional Resources

- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [MCP Servers List](https://github.com/anthropics/mcp-servers)
- [Slash Commands Guide](https://docs.claude.com/claude-code/slash-commands)
- [Hooks Guide](https://docs.claude.com/claude-code/hooks)
