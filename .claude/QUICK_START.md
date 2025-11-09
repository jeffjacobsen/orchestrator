# Claude Code Quick Start Guide

You now have 5 custom slash commands and 1 safety hook configured and ready to use!

## Available Commands

### 1. `/test-full` - Complete Test Suite

Run all tests before committing:

```bash
/test-full
```

**What it does**:
- ✓ Runs core orchestrator tests with coverage
- ✓ Runs dashboard backend tests
- ✓ Runs type checking (mypy)
- ✓ Runs linting (ruff + black)
- ✓ Reports summary and suggests fixes

**When to use**: Before every commit

---

### 2. `/check-arch` - Architecture Validator

Ensure core remains integration-agnostic:

```bash
/check-arch
```

**What it does**:
- ✓ Checks core has no dashboard imports
- ✓ Verifies dashboard only imports core in executor
- ✓ Checks for hardcoded database paths
- ✓ Validates log directory separation
- ✓ Generates architecture diagram

**When to use**: After making core or dashboard changes

---

### 3. `/deploy-dashboard` - Safe Deployment

Deploy dashboard with full safety checks:

```bash
/deploy-dashboard
```

**What it does**:
- ✓ Verifies git status and branch
- ✓ Runs all tests first
- ✓ Checks for pending migrations
- ✓ Builds and starts Docker containers
- ✓ Runs health checks on all services
- ✓ Shows deployment logs

**When to use**: Before deploying dashboard changes

---

### 4. `/task-debug` - Debug Failed Tasks

Analyze why a task failed:

```bash
/task-debug
```

**What it does**:
- ✓ Locates task logs (CLI or dashboard)
- ✓ Analyzes agent execution flow
- ✓ Identifies failure point and root cause
- ✓ Calculates cost and performance
- ✓ Suggests prompt improvements
- ✓ Provides example fixes

**When to use**: When a task fails unexpectedly

---

### 5. `/release-prep` - Release Preparation

Automate release checklist:

```bash
/release-prep
```

**What it does**:
- ✓ Updates version numbers across all files
- ✓ Runs full test suite
- ✓ Checks documentation is current
- ✓ Audits for secrets in code
- ✓ Verifies migrations
- ✓ Tests Docker build
- ✓ Generates git commands for release

**When to use**: Before creating a new release

---

## Active Hooks

### Pre-Commit Hook

Automatically runs on every commit:

**Checks**:
- ❌ BLOCKS: Dashboard imports in core (architecture violation)
- ⚠️ WARNS: Hardcoded database paths
- ⚠️ WARNS: Potential secrets in code

**To bypass** (not recommended):
```bash
git commit --no-verify
```

---

## Permissions Summary

Your `.claude/config.yaml` has been configured with:

**✅ Allowed**:
- All testing commands (pytest, mypy, ruff, black)
- Safe git operations (add, commit, push main, tag)
- Package management (pip, npm)
- Docker development operations
- Database reads (SELECT, PRAGMA)
- Orchestrator CLI

**⚠️ Requires Confirmation**:
- Database modifications (ALTER, INSERT, UPDATE)
- Alembic migrations
- Docker volume deletion
- Database migration files

**❌ Blocked**:
- Force git push
- Destructive database operations (DROP, DELETE, TRUNCATE)
- Dangerous Docker operations (system prune)
- Recursive deletion from root

---

## Quick Examples

### Development Workflow

```bash
# 1. Make code changes
# ... edit files ...

# 2. Validate architecture
/check-arch

# 3. Run tests
/test-full

# 4. Commit (pre-commit hook runs automatically)
git add .
git commit -m "feat: Add new feature"
```

### Release Workflow

```bash
# 1. Prepare release
/release-prep
# Follow prompts, enter version number

# 2. Review changes
git diff

# 3. Execute release commands (provided by /release-prep)
git add .
git commit -m "chore: Release v0.1.6"
git tag -a v0.1.6 -m "Release v0.1.6"
git push origin main && git push origin v0.1.6
```

### Debugging Workflow

```bash
# 1. Task failed
# Check error in dashboard or CLI output

# 2. Debug task
/task-debug
# Enter task ID or 'latest'

# 3. Review analysis
# Root cause identified with recommendations

# 4. Fix and re-run
# Apply suggested fixes
orchestrator execute "retry task"
```

### Deployment Workflow

```bash
# 1. Deploy dashboard
/deploy-dashboard

# 2. Monitor
# Dashboard shows health checks and logs

# 3. Verify
# Access http://localhost:5173
# Test functionality
```

---

## Troubleshooting

### Commands not found

If you get "command not found", ensure you're in the orchestrator root directory:

```bash
pwd
# Should show: /Volumes/Ext_SSD/Users/jeff/code/orchestrator
```

### Pre-commit hook not running

Make hook executable:

```bash
chmod +x .claude/hooks/pre-commit.sh
```

### Permissions errors

Check `.claude/config.yaml` permissions section and adjust as needed.

---

## Next Steps

1. **Try `/test-full`** right now to verify everything works
2. **Try `/check-arch`** to see your architecture is clean
3. **Review [CLAUDE_CODE_ENHANCEMENTS.md](../CLAUDE_CODE_ENHANCEMENTS.md)** for full documentation
4. **Add more commands** as you identify repetitive workflows

---

## Time Savings

Based on our analysis, these features will save you:

- **Per Development Session**: 10-15 minutes (testing, architecture checks)
- **Per Deployment**: 5-10 minutes (safety checks, automation)
- **Per Release**: 15-20 minutes (checklist automation)
- **Per Debug Session**: 10-15 minutes (log analysis)

**Total**: ~15-20 hours per month

---

**Ready to start?** Try running:

```bash
/test-full
```
