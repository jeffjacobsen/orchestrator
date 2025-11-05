# Changelog

All notable changes to the Claude Multi-Agent Orchestrator project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2025-11-05

Progress bars implementation for real-time visibility during agent operations.

### Added

**Progress Tracking System**
- Real-time progress bars with Rich library for terminal display
- `ProgressTracker` class with live display updates
- Visual workflow step indicators showing progression (○ → ✓)
- Agent activity monitoring (thinking, tool calls, completion)
- Real-time cost accumulation display
- Elapsed time tracking
- Active/completed agent counters

**Infrastructure**
- Progress callback system in `Agent` class for event reporting
- Progress callback integration in `WorkflowExecutor` for both sequential and parallel execution
- Bridge functions connecting agent lifecycle events to progress display
- `enable_progress_display` parameter in `Orchestrator` class (default: True)

**User Experience**
- Progress panels show during long-running operations
- Visual confirmation that work is happening (addresses critical dogfooding finding)
- No more "black box" execution during 5+ minute agent phases
- Zero performance impact when disabled

### Changed
- `Orchestrator.__init__()` now accepts `enable_progress_display` parameter
- `WorkflowExecutor.__init__()` now accepts optional `ProgressTracker` parameter
- Workflow execution now extracts and displays step names in progress UI

## [0.1.1] - 2025-11-05

Dogfooding improvements from self-improvement experiment.

### Added

**Type Hints & Documentation**
- Comprehensive type hints on all public methods (mypy compatible)
- Google-style docstrings with realistic code examples
- 47 type hint validation tests
- 62 docstring validation tests

**Agent File Logging**
- JSONL format logs for each agent: `prompt.txt`, `text.txt`, `tools.jsonl`, `summary.jsonl`
- `AgentLogger` class for structured agent-level logging
- Debugging support for agent conversations

**Smart Workflow Selection**
- Task complexity estimation based on keywords and word count
- Simplified workflow templates that skip Analyst for simple tasks
- 77% context reduction (113K → 26K tokens) for simple tasks
- Complexity-based template routing

### Changed
- `TaskPlanner.plan_task()` now uses complexity estimation to select optimal workflow
- Simple tasks use streamlined 2-step workflows (Builder → Tester)
- Complex tasks continue to use full 5-step workflows (Analyst → Planner → Builder → Tester → Reviewer)

### Fixed
- Context management optimization preventing over-analysis
- Reduced cache read token usage for simple tasks

## [0.1.0] - 2025-11-05

Initial release of the Claude Multi-Agent Orchestrator system.

### Added

**Core Functionality**
- Claude Code SDK integration for seamless agent management
- Multi-agent orchestration system with CRUD operations for agents
- Parallel and sequential execution modes for workflow optimization
- SQLite persistence for tasks and agents
- Comprehensive ROADMAP.md with detailed enhancement plans and priorities
- CHANGELOG.md for version tracking

**Agent System**
- Specialized agent roles: Planner, Builder, Reviewer, Analyst, Tester, Documenter
- Full agent lifecycle management (Create, Read, Update, Delete)
- Context management with automatic tracking and warnings
- Agent forking and cloning capabilities

**CLI Commands**
- `orchestrator init` - Initialize configuration with interactive prompts
- `orchestrator execute` - Execute tasks with customizable task types and modes
- `orchestrator status` - Show comprehensive orchestrator status
- `orchestrator list-agents` - List active agents with filtering
- `orchestrator list-tasks` - List all tasks
- `orchestrator agent-details` - Get detailed agent information
- `orchestrator task-details` - Get detailed task information
- `orchestrator clean` - Clean up old completed/failed agents and tasks (with dry-run)
- `orchestrator cost-report` - Generate cost analysis reports (table/JSON formats)

**Observability & Monitoring**
- Real-time monitoring system with metrics collection
- Cost and performance tracking (per-agent and fleet-wide)
- File operations tracking (consumed vs produced)
- Structured logging system
- Rich terminal output with colors, tables, and formatting
- Comprehensive status reporting with breakdowns by agent and role

**Testing**
- Comprehensive CLI test suite (29 test cases, all passing)
- Mock-based testing using pytest and Click's CliRunner
- Integration tests verifying authentication flow
- Edge case coverage for all CLI commands

**Examples**
- Basic orchestration workflow
- Parallel vs sequential execution comparison
- Specialized agent usage patterns
- Manual agent control (CRUD operations)
- Observability and monitoring demonstrations

### Changed
- **BREAKING**: Removed `api_key` parameter from `Orchestrator` class
- **BREAKING**: CLI no longer requires ANTHROPIC_API_KEY environment variable
- All authentication now handled through Claude Code CLI
- Updated all example files to remove API key usage
- Enhanced `orchestrator init` with helpful messages about CLI authentication

### Fixed
- Replaced deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)` across entire codebase
- Fixed all Pydantic Field default_factory functions to use lambda for timezone-aware datetime
- Fixed JSON serialization in CLI commands (status, task-details, agent-details)
- Cleaned up unused imports (os, sys, dotenv) from CLI module

### Removed
- `get_api_key()` function from CLI (no longer needed)
- API key prompt from `orchestrator init` command
- ANTHROPIC_API_KEY requirement from documentation and configuration

### Technical Details
- **Python**: 3.10+
- **Models**: Claude Sonnet 4.5 (default)
- **Database**: SQLite with aiosqlite
- **CLI Framework**: Click with Rich formatting
- **Testing**: pytest with asyncio support

---

## Version History Summary

### v0.1.2 (Released)
**Focus**: Progress Bars & Real-time Visibility
- Real-time progress tracking for agent operations
- Visual workflow step indicators and activity monitoring
- Cost and time tracking during execution
- Addresses critical dogfooding finding about visibility

### v0.1.1 (Released)
**Focus**: Dogfooding Improvements
- Comprehensive type hints and docstring examples
- Agent file logging for debugging
- Smart workflow selection with context optimization
- 77% context reduction for simple tasks

### v0.1.0 (Released)
**Focus**: Initial Release
- Core orchestrator functionality with Claude Code SDK
- Full CLI implementation with 9 commands
- Comprehensive observability and monitoring
- Production-ready features with CLI authentication

### v0.2.0 (Planned)
**Focus**: Intelligence & Advanced Features
- Interactive mode for agent management
- CSV export functionality
- Real-time monitoring commands (watch, logs, kill)
- Context budget enforcement

### v0.3.0 (Planned)
**Focus**: Intelligence Upgrade
- LLM-based task planning
- Cost prediction system
- Smart agent selection
- Learning from execution history

### v1.0.0 (Planned)
**Focus**: Production Ready
- Comprehensive test coverage
- Enhanced error handling
- Web UI for observability
- Production deployment guides

---

## Migration Guide

### Migrating from API Key Authentication

**Before (v0.1.0)**:
```python
from orchestrator import Orchestrator

orchestrator = Orchestrator(
    api_key="your-api-key",
    enable_monitoring=True
)
```

**After (v0.2.0)**:
```python
from orchestrator import Orchestrator

# API key no longer needed - handled by Claude Code CLI
orchestrator = Orchestrator(
    enable_monitoring=True
)
```

**CLI Changes**:
- Old: Required `.env` file with `ANTHROPIC_API_KEY`
- New: Authentication through Claude Code CLI (no configuration needed)
- The `orchestrator init` command no longer prompts for API key

**Breaking Changes**:
1. Remove `api_key` parameter from all `Orchestrator()` calls
2. Remove `ANTHROPIC_API_KEY` from `.env` files (optional, won't hurt if present)
3. Ensure Claude Code CLI is authenticated

---

## Contributing

When contributing, please:
1. Update this CHANGELOG.md with your changes
2. Follow the format: Added/Changed/Deprecated/Removed/Fixed/Security
3. Reference issue numbers when applicable
4. Keep descriptions clear and concise

---

**Last Updated**: 2025-11-05 (v0.1.2)
