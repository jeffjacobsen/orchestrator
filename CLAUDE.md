# Claude AI Assistant Reference

This file provides context for Claude AI assistants working on the Orchestrator project.

## Project Overview

**Claude Multi-Agent Orchestrator** - A library-first Python framework for orchestrating multiple Claude agents with intelligent task decomposition and comprehensive observability.

**Current Version**: v0.1.5 (2025-11-08)
**Status**: Feature-complete dashboard, shifting focus to core orchestrator production readiness

## Core Architecture Principles

### 1. Library-First Design

The orchestrator core (`src/orchestrator/`) is **completely independent** of any specific UI, API, or monitoring system.

```
✅ CORRECT: Dashboard imports orchestrator
❌ WRONG: Orchestrator imports dashboard

Core Orchestrator (src/orchestrator/)
    ↑
    │ imports (one-way only)
    │
Dashboard (dashboard/)
```

**Critical Rule**: Dependencies flow **up** only. Core never imports from dashboard or integrations.

### 2. The Product vs. The Sample

- **Product**: Core orchestrator library (`src/orchestrator/`)
- **Sample**: Web dashboard (`dashboard/`) - one possible way to use the library

**When working on features**:
- Dashboard features → modify `dashboard/`
- Core logic → modify `src/orchestrator/`
- NEVER add dashboard dependencies to core

### 3. Integration-Agnostic Core

The orchestrator should work with:
- Web dashboards (like the included one)
- CLI (already implemented)
- GitHub Issues automation
- Telegram/Slack bots
- Message queues (RabbitMQ, Redis, Kafka)
- Custom APIs

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for examples.

## Current Focus (v0.1.5 → v1.0)

### ✅ Dashboard: Feature Complete

The dashboard is done for v1.0:
- Real-time monitoring and workflow tracking
- Task execution and management
- Task history with comprehensive filtering
- Agent log viewing
- Cost and duration tracking

**No more dashboard features** until core is production-ready.

### 🎯 Priority: Core Orchestrator Production Readiness

Focus areas (in order):

1. **Testing & Reliability**
   - Core orchestrator unit tests (target: >80% coverage)
   - Integration tests for workflows
   - Error scenario testing
   - Performance benchmarks

2. **Error Handling & Recovery**
   - Graceful degradation
   - Automatic retry logic
   - Better error messages
   - Crash recovery

3. **Code Quality & Documentation**
   - Inline documentation
   - Troubleshooting guides
   - Input validation

## Key Files Reference

### Core Documentation
- [README.md](README.md) - Main project documentation
- [ROADMAP.md](ROADMAP.md) - Feature roadmap and priorities
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Architecture reference
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Integration patterns
- [WORKFLOW_ORDER.md](WORKFLOW_ORDER.md) - Workflow design patterns

### Core Implementation
- `src/orchestrator/core/orchestrator.py` - Main Orchestrator class
- `src/orchestrator/core/agent_manager.py` - CRUD operations for agents
- `src/orchestrator/workflow/planner.py` - Task decomposition with AI
- `src/orchestrator/workflow/executor.py` - Workflow execution
- `src/orchestrator/workflow/context_parser.py` - Context optimization
- `src/orchestrator/observability/monitor.py` - Real-time monitoring

### Dashboard (Reference Implementation)
- `dashboard/backend/app/api/v1/tasks.py` - Task API endpoints
- `dashboard/backend/app/services/orchestrator_executor.py` - Wrapper around core
- `dashboard/frontend/src/components/TaskList.tsx` - Active tasks UI
- `dashboard/frontend/src/components/TaskHistory.tsx` - Task history with filters

## Development Guidelines

### When to Modify Core (`src/orchestrator/`)

✅ **DO modify core for**:
- Adding new agent roles or capabilities
- Improving workflow planning logic
- Enhancing observability (that works for all integrations)
- Bug fixes and performance improvements
- Testing and error handling
- Context management improvements

❌ **DON'T modify core for**:
- Dashboard-specific features
- UI/UX changes
- API endpoint modifications
- Database schema changes specific to one integration

### When to Modify Dashboard (`dashboard/`)

✅ **DO modify dashboard for**:
- UI improvements (if critical)
- Bug fixes
- Performance optimizations
- Minor UX enhancements

❌ **DON'T modify dashboard for**:
- Core orchestration logic (belongs in core)
- Agent behavior (belongs in core)
- Workflow planning (belongs in core)
- New analytics features (deferred to post-v1.0)

### Testing Philosophy

- **Unit tests** for core orchestrator logic
- **Integration tests** for workflows
- **Error scenario tests** for reliability
- **Performance benchmarks** for optimization

Testing is the **#1 priority** for v1.0.

## Common Workflows

### Adding a New Agent Role

1. Add role to `src/orchestrator/core/types.py` (AgentRole enum)
2. Add system prompt to `src/orchestrator/core/prompts.py`
3. Update workflow templates in `src/orchestrator/workflow/planner.py`
4. Add tests
5. Update documentation

### Improving Workflow Planning

1. Modify `src/orchestrator/workflow/planner.py`
2. Test with various task complexities
3. Validate context optimization works
4. Update WORKFLOW_ORDER.md documentation

### Adding Dashboard UI Feature

1. Check: Is this critical for v1.0? (Probably not)
2. If yes: Add component to `dashboard/frontend/src/components/`
3. Add API endpoint if needed in `dashboard/backend/app/api/v1/`
4. Test in isolation
5. **DO NOT** modify core orchestrator

## Version History (Quick Reference)

- **v0.1.0** (2025-11-05) - Initial release with SDK refactoring
- **v0.1.1** (2025-11-05) - Dogfooding improvements, 77% context reduction
- **v0.1.2** (2025-11-05) - Progress bars and real-time tracking
- **v0.1.3** (2025-11-05) - ANALYST workflow optimization
- **v0.1.4** (2025-11-06) - Dashboard Phase 1 complete
- **v0.1.5** (2025-11-07) - Dashboard Phase 2 + Task History complete
- **v1.0.0** (Planned) - Production ready with comprehensive testing

## Key Metrics & Goals

### Current Performance
- Simple tasks: ~56-66K tokens, $0.06-0.07
- Context reduction: 77% vs baseline (113K → 26K tokens)
- Smart workflow selection working effectively

### v1.0 Goals
- **>80% test coverage** on core orchestrator
- **Comprehensive error handling** with recovery
- **Production deployment** guide
- **Performance benchmarks** established

## Quick Commands

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=orchestrator --cov-report=html

# Type checking
mypy src/orchestrator

# Linting
ruff check src/orchestrator
```

### CLI Usage
```bash
# Execute a task
orchestrator execute "Task description"

# Show status
orchestrator status

# List agents
orchestrator list-agents

# Get task details
orchestrator task-details <task-id>
```

### Dashboard
```bash
# Start dashboard (development)
cd dashboard
docker-compose up -d

# Access at http://localhost:5173
# API docs at http://localhost:8000/api/docs
```

## Important Notes for Claude Assistants

1. **Dashboard is feature-complete** - Don't suggest new analytics features
2. **Focus on core orchestrator** - Testing, reliability, error handling
3. **Maintain library-first design** - Never add dashboard dependencies to core
4. **Prioritize testing** - Every new feature needs tests
5. **Read PROJECT_STRUCTURE.md** - Understand the architecture before modifying

## Questions to Ask

Before implementing a feature, ask:

1. **Does this belong in core or dashboard?**
   - Core: Affects all integrations
   - Dashboard: Only affects web UI

2. **Is this critical for v1.0?**
   - Yes: Testing, error handling, reliability
   - No: Advanced analytics, UI polish, new features

3. **Does this break the library-first design?**
   - Check: Does core import dashboard? (Should be NO)
   - Check: Can this work without dashboard? (Should be YES)

4. **Does this have tests?**
   - If no: Add tests first
   - If yes: Verify coverage is >80%

## Resources

- **Main repo**: (git remote -v)
- **Issues**: GitHub Issues (if applicable)
- **Documentation**: See docs/ directory
- **Examples**: See examples/ directory
- **Integration examples**: INTEGRATION_GUIDE.md

---

**Last Updated**: 2025-11-08
**For**: Claude AI assistants working on Orchestrator
**Remember**: Core orchestrator is the product. Dashboard is a sample. Testing is priority #1.
