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
