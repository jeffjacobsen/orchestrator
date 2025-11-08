# Pre-Release Checklist

This document outlines critical checks before pushing code for initial users.

## ✅ Completed

### Code Quality
- [x] **Architecture verified clean** - Core orchestrator has zero dashboard dependencies
- [x] **Database schema applied** - `total_cost` and `duration_seconds` columns exist
- [x] **Test files removed** - No `hello.py` or other test artifacts
- [x] **No secrets exposed** - Verified no API keys, tokens, or passwords in code

### Documentation
- [x] **README.md updated** - Library-first design emphasized
- [x] **INTEGRATION_GUIDE.md created** - Comprehensive integration examples
- [x] **PROJECT_STRUCTURE.md created** - Architecture and contribution guidelines
- [x] **POSSIBLE_ENHANCEMENTS.md created** - Future features documented

### Features
- [x] **Cost tracking implemented** - Backend aggregates agent costs to cents
- [x] **Duration tracking implemented** - Wall clock time from start to completion
- [x] **Task History enhanced** - Cost and duration filters/sorting/display
- [x] **Database migration created** - Alembic migration for schema changes

## ⚠️ Important Notes for Initial Users

### 1. Database Migration Required

Users with existing databases need to run:

```bash
cd dashboard/backend
sqlite3 orchestrator.db < migration_fix.sql
```

**migration_fix.sql**:
```sql
-- Add cost and duration columns if they don't exist
ALTER TABLE tasks ADD COLUMN total_cost INTEGER DEFAULT 0;
ALTER TABLE tasks ADD COLUMN duration_seconds INTEGER DEFAULT 0;

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS ix_tasks_total_cost ON tasks(total_cost);
CREATE INDEX IF NOT EXISTS ix_tasks_duration_seconds ON tasks(duration_seconds);
```

**Or use Alembic** (if properly installed):
```bash
cd dashboard/backend
alembic upgrade head
```

### 2. Environment Setup

Users need to ensure:

**Dashboard users**:
```bash
cd dashboard
docker-compose up -d
# Or manual setup:
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

**CLI-only users**:
```bash
pip install -e .
orchestrator init
```

### 3. Known Limitations

- **CLI tasks NOT in dashboard database** - CLI and dashboard use separate log directories
  - See POSSIBLE_ENHANCEMENTS.md for integration options
- **Extended Thinking not enabled** - Infrastructure ready but feature not activated
  - See POSSIBLE_ENHANCEMENTS.md for implementation guide
- **Existing tasks have 0 cost/duration** - Only new tasks will have metrics
  - Historical tasks won't be updated retroactively

## 🔧 Manual Testing Performed

### Backend
- [x] Database schema verified with `PRAGMA table_info(tasks)`
- [x] API endpoints tested with cost/duration parameters
- [x] Migration file created and structure validated

### Frontend
- [x] Cost and duration columns added to Task History
- [x] Filter inputs added for cost and duration ranges
- [x] Formatting functions tested ($X.XX, Xm Ys)
- [x] TypeScript types updated

### Integration
- [x] Dashboard backend imports orchestrator correctly
- [x] No circular dependencies detected
- [x] Orchestrator core remains independent

## 📋 Recommended User Testing

Initial users should test:

1. **Fresh Installation**
   ```bash
   git clone <repo>
   pip install -e .
   orchestrator execute "test task"
   ```

2. **Dashboard Setup**
   ```bash
   cd dashboard
   docker-compose up -d
   # Open http://localhost:5173
   # Create a task via UI
   # Verify cost and duration appear
   ```

3. **Custom Integration**
   ```python
   from orchestrator import Orchestrator
   # Follow examples in INTEGRATION_GUIDE.md
   ```

## 🚨 Breaking Changes

### None in this release!

This release adds features without breaking existing functionality:
- New database columns have default values
- API is backward compatible (new parameters are optional)
- CLI behavior unchanged
- Dashboard is optional

## 📦 What's New in v0.1.5

### Major Features
1. **Cost and Duration Tracking**
   - Aggregates agent costs and execution time
   - Stores in database for analytics
   - Filters and sorts in Task History

2. **Enhanced Documentation**
   - INTEGRATION_GUIDE.md with real-world examples
   - PROJECT_STRUCTURE.md for contributors
   - POSSIBLE_ENHANCEMENTS.md for roadmap

3. **Architecture Clarity**
   - Emphasized library-first design
   - Documented clean separation of concerns
   - Provided integration patterns

### Bug Fixes
- None (this is a feature release)

### Technical Improvements
- Database schema migration for metrics
- TypeScript type updates
- API endpoint enhancements

## 🎯 Target Audience

This release is ready for:
- ✅ **Early adopters** who want to experiment
- ✅ **Developers** who want to integrate with their own systems
- ✅ **Power users** who need cost tracking and analytics
- ⚠️ **NOT production-ready** - still in active development

## 🔒 Security Considerations

### Before Users Deploy

**Critical**: Users must:
1. **Change default secrets** in `.env`:
   ```bash
   SECRET_KEY=change-this-to-a-secure-random-string
   API_KEY=change-this-to-a-secure-api-key
   ```

2. **Restrict access** if exposing dashboard:
   - Use firewall rules
   - Add authentication (Phase 5 feature)
   - Use HTTPS in production

3. **Review permissions** for working directories:
   - Orchestrator can read/write files
   - Limit to specific project directories
   - Don't run with elevated privileges

### Included in README

The following warnings should be in README:

```markdown
## Security Notice

⚠️ **IMPORTANT**: This is a development release.

Before deploying:
1. Change all default secrets in `.env`
2. Use authentication (coming in Phase 5)
3. Restrict network access to dashboard
4. Limit file system permissions
5. Review agent prompts for your use case
```

## ✨ Post-Release Communication

### Sample Announcement

```markdown
# Claude Multi-Agent Orchestrator v0.1.5 Released!

New features:
- 📊 Cost and duration tracking for all tasks
- 📚 Comprehensive integration guide with real examples
- 🏗️ Clear architecture documentation
- 🔧 Enhanced Task History with analytics

Key highlights:
- Library-first design - use with ANY system (GitHub, Telegram, Slack, etc.)
- Sample dashboard is optional - build your own integrations
- Complete separation between orchestrator core and UI

Get started:
- CLI: `pip install -e . && orchestrator execute "your task"`
- Dashboard: `cd dashboard && docker-compose up -d`
- Custom: See INTEGRATION_GUIDE.md for examples

⚠️ Early adopter release - not production-ready yet.

Docs: README.md | INTEGRATION_GUIDE.md | PROJECT_STRUCTURE.md
```

## 🐛 Known Issues to Document

1. **Alembic not working via python -m alembic**
   - Workaround: Manual SQL migration provided
   - Fix: Install alembic properly or use docker-compose

2. **CLI tasks not in dashboard**
   - Expected behavior (by design)
   - Fix planned: Optional database integration (see POSSIBLE_ENHANCEMENTS.md)

3. **No thinking logs**
   - Extended Thinking not enabled
   - Fix: Add configuration (see POSSIBLE_ENHANCEMENTS.md)

## 📝 Files to Commit

### New Files
```
INTEGRATION_GUIDE.md
POSSIBLE_ENHANCEMENTS.md
PROJECT_STRUCTURE.md
PRE_RELEASE_CHECKLIST.md (this file)
dashboard/backend/alembic/versions/2025_11_08_0800-c9f8e4a21234_add_cost_and_duration_to_tasks.py
```

### Modified Files
```
README.md
dashboard/backend/app/api/v1/tasks.py
dashboard/backend/app/models/task.py
dashboard/backend/app/schemas/task.py
dashboard/backend/app/services/orchestrator_executor.py
dashboard/frontend/src/components/TaskHistory.tsx
dashboard/frontend/src/types/index.ts
```

### Not to Commit
```
hello.py (test file - deleted)
*.pyc
__pycache__/
node_modules/
.env (secrets)
orchestrator.db (local database)
agent_logs/ (local logs)
```

## ✅ Ready to Push?

**Prerequisites**:
- [ ] All tests pass locally
- [ ] Documentation reviewed
- [ ] No secrets in code
- [ ] Test files removed
- [ ] Version updated if needed

**Final commands**:
```bash
# Review changes
git status
git diff

# Stage files
git add README.md INTEGRATION_GUIDE.md PROJECT_STRUCTURE.md POSSIBLE_ENHANCEMENTS.md
git add dashboard/backend/app/
git add dashboard/frontend/src/
git add dashboard/backend/alembic/versions/

# Commit
git commit -m "feat: Add cost and duration tracking with enhanced documentation

- Add total_cost and duration_seconds to Task model
- Implement metrics aggregation in orchestrator_executor
- Create Task History filters and sorting for cost/duration
- Add INTEGRATION_GUIDE.md with real-world examples
- Add PROJECT_STRUCTURE.md for contributors
- Update POSSIBLE_ENHANCEMENTS.md with architecture principles
- Emphasize library-first design in README

Breaking Changes: None
Migration Required: Yes (add_cost_and_duration_to_tasks.py)"

# Push
git push origin main
```

## 🎉 Success Criteria

Release is successful if users can:
1. ✅ Clone repo and run CLI tasks
2. ✅ Set up dashboard and see cost/duration metrics
3. ✅ Follow INTEGRATION_GUIDE.md to build custom integrations
4. ✅ Understand architecture from PROJECT_STRUCTURE.md
5. ✅ Contribute features using guidelines

---

**Version**: 0.1.5
**Date**: 2025-11-08
**Status**: Ready for initial users
