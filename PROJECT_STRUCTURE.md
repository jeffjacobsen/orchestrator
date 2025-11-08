# Project Structure

This document explains the organization and architecture of the Claude Multi-Agent Orchestrator project.

## Directory Layout

```
orchestrator/
├── src/orchestrator/          # Core orchestrator library (integration-agnostic)
│   ├── core/                  # Core orchestration logic
│   │   ├── orchestrator.py    # Main Orchestrator class
│   │   ├── agent_manager.py   # CRUD operations for agents
│   │   ├── agent.py           # Individual agent wrapper
│   │   ├── prompts.py         # System prompts for agent roles
│   │   └── types.py           # Type definitions
│   ├── workflow/              # Task planning and execution
│   │   ├── planner.py         # Task decomposition
│   │   ├── executor.py        # Workflow execution
│   │   └── context_parser.py  # Context analysis
│   ├── observability/         # Monitoring and logging
│   │   ├── monitor.py         # Real-time monitoring
│   │   ├── metrics.py         # Metrics collection
│   │   └── agent_logger.py    # Structured logging (prompt/text/tools)
│   ├── storage/               # Data persistence (optional)
│   │   ├── database.py        # SQLite persistence
│   │   └── models.py          # Database models
│   └── cli/                   # CLI interface
│       └── commands.py        # Command-line interface
│
├── dashboard/                 # Sample web dashboard (one possible UI)
│   ├── backend/               # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/v1/        # REST API endpoints
│   │   │   │   ├── tasks.py   # Task endpoints
│   │   │   │   ├── agents.py  # Agent endpoints
│   │   │   │   └── websocket.py # WebSocket for real-time updates
│   │   │   ├── core/
│   │   │   │   ├── config.py  # Configuration
│   │   │   │   ├── database.py # Database setup
│   │   │   │   └── security.py # Authentication
│   │   │   ├── models/        # SQLAlchemy models
│   │   │   │   ├── task.py    # Task model
│   │   │   │   └── agent.py   # Agent model
│   │   │   ├── schemas/       # Pydantic schemas
│   │   │   │   ├── task.py    # Task request/response
│   │   │   │   └── agent.py   # Agent request/response
│   │   │   └── services/
│   │   │       └── orchestrator_executor.py # Wrapper around core orchestrator
│   │   ├── alembic/           # Database migrations
│   │   └── tests/             # Backend tests
│   └── frontend/              # React frontend
│       ├── src/
│       │   ├── components/    # UI components
│       │   │   ├── TaskList.tsx
│       │   │   ├── TaskHistory.tsx
│       │   │   ├── AgentList.tsx
│       │   │   └── WorkflowProgress.tsx
│       │   ├── hooks/         # Custom React hooks
│       │   ├── services/      # API client
│       │   └── types/         # TypeScript types
│       └── public/
│
├── tests/                     # Core orchestrator tests
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── examples/                  # Usage examples
│   ├── basic_orchestration.py
│   ├── parallel_execution.py
│   └── integrations/          # Integration examples
│       ├── github_bot.py
│       ├── telegram_bot.py
│       └── slack_app.py
│
├── docs/                      # Documentation
│   └── archive/               # Archived design documents
│
├── agent_logs/                # CLI agent logs (task_id subdirs)
│
├── README.md                  # Main documentation
├── ROADMAP.md                 # Feature roadmap
├── POSSIBLE_ENHANCEMENTS.md   # Potential improvements
├── INTEGRATION_GUIDE.md       # Integration patterns & examples
├── PROJECT_STRUCTURE.md       # This file
├── WORKFLOW_ORDER.md          # Workflow design patterns
└── pyproject.toml             # Python package configuration
```

## Architecture Layers

### Layer 1: Core Orchestrator (src/orchestrator/)

**Purpose**: Reusable library for orchestrating Claude agents

**Key Characteristics**:
- ✅ **Zero dependencies** on any specific UI, API, or monitoring system
- ✅ **Library-first** design - import and use in any Python application
- ✅ **Integration-agnostic** - works with any monitoring/storage solution
- ✅ **Callback-based** - extensible through progress callbacks and events

**When to modify**:
- Adding new agent roles or capabilities
- Improving workflow planning logic
- Enhancing observability features (that work for all integrations)
- Bug fixes and performance improvements

**When NOT to modify**:
- Adding dashboard-specific features
- UI/UX changes
- API endpoint modifications
- Database schema changes specific to one integration

### Layer 2: Sample Dashboard (dashboard/)

**Purpose**: One possible way to monitor and control the orchestrator

**Key Characteristics**:
- ✅ **Wraps** the core orchestrator (doesn't modify it)
- ✅ **Optional** - users can ignore this completely
- ✅ **Reference implementation** - shows one way to integrate
- ✅ **Separate database** - doesn't interfere with core

**When to modify**:
- Adding dashboard UI features
- Improving real-time updates
- Database schema for dashboard-specific features
- API endpoints for web UI

**When NOT to modify**:
- Core orchestration logic (belongs in Layer 1)
- Agent behavior (belongs in Layer 1)
- Workflow planning (belongs in Layer 1)

### Layer 3: CLI (src/orchestrator/cli/)

**Purpose**: Command-line interface for direct orchestrator usage

**Key Characteristics**:
- ✅ **Direct access** to orchestrator without any middleware
- ✅ **Simple wrapper** around core functionality
- ✅ **No database** by default (logs to files only)
- ✅ **Fast and lightweight**

### Layer 4: Custom Integrations (your code)

**Purpose**: Your own applications using the orchestrator

**Key Characteristics**:
- ✅ **Import orchestrator** as a library
- ✅ **Use your own** database, API, UI, monitoring
- ✅ **Full control** over how you integrate
- ✅ **Examples provided** in INTEGRATION_GUIDE.md

## Dependency Flow

```
┌─────────────────────────────────────────────┐
│  Your Custom Integration                     │
│  (GitHub bot, Telegram, Slack, etc.)        │
└─────────────────┬───────────────────────────┘
                  │ imports
                  ↓
┌─────────────────────────────────────────────┐
│  Core Orchestrator (src/orchestrator/)      │ ← Library (no dependencies on UI/API)
│  • orchestrator.py                          │
│  • agent_manager.py                         │
│  • workflow/planner.py                      │
│  • observability/monitor.py                 │
└─────────────────┬───────────────────────────┘
                  ↑
                  │ imports (one-way only)
                  │
┌─────────────────────────────────────────────┐
│  Sample Dashboard (dashboard/)              │ ← Optional reference implementation
│  • FastAPI backend                          │
│  • React frontend                           │
│  • orchestrator_executor.py (wrapper)       │
└─────────────────────────────────────────────┘
```

**Critical Rule**: Dependencies flow **up** only. Core orchestrator never imports from dashboard or custom integrations.

## Data Flow

### CLI Execution
```
User → CLI → Core Orchestrator → Agents → File Logs
                                        ↓
                                   agent_logs/{task_id}/
```

### Dashboard Execution
```
User → React UI → FastAPI → orchestrator_executor → Core Orchestrator → Agents
                     ↓                                                    ↓
                  Dashboard DB                                  dashboard/backend/agent_logs/
```

### Custom Integration
```
User → Your App → Core Orchestrator → Agents → Your chosen storage
                                             ↓
                                        Your logging system
```

## File Organization Conventions

### Core Orchestrator Files

**Naming conventions**:
- `orchestrator.py` - Main orchestrator class
- `agent.py` - Single agent wrapper
- `agent_manager.py` - Agent CRUD operations
- `*_planner.py` - Planning/decomposition logic
- `*_executor.py` - Execution logic
- `*_monitor.py` - Monitoring logic

**Import structure**:
```python
# ✅ Good: Imports within orchestrator package
from orchestrator.core.agent import Agent
from orchestrator.workflow.planner import TaskPlanner

# ❌ Bad: Imports from dashboard or external integrations
from dashboard.backend.app.models import Task  # Never do this!
```

### Dashboard Files

**Naming conventions**:
- `*_executor.py` - Wrappers around orchestrator
- `*.py` (in app/api/) - API endpoints
- `*.tsx` - React components
- `*_schema.py` - Pydantic schemas

**Import structure**:
```python
# ✅ Good: Dashboard imports from orchestrator
from orchestrator import Orchestrator
from orchestrator.core.agent_manager import AgentManager

# ✅ Good: Dashboard internal imports
from app.models.task import Task
from app.core.database import get_db
```

## Configuration Management

### Core Orchestrator Configuration

Environment variables (optional):
```bash
# Core orchestrator settings
DEFAULT_MODEL=claude-sonnet-4-5-20250929
ORCHESTRATOR_MAX_PARALLEL_AGENTS=5
MONITOR_INTERVAL_SECONDS=15
ENABLE_COST_TRACKING=true
```

Configuration location: `.env` in project root

### Dashboard Configuration

Environment variables (separate from core):
```bash
# Dashboard-specific settings
DATABASE_URL=sqlite+aiosqlite:///./orchestrator.db
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:5173
```

Configuration location: `dashboard/backend/.env`

### Custom Integration Configuration

You decide! Use environment variables, config files, or hardcoded values.

## Testing Strategy

### Core Orchestrator Tests (`tests/`)

**Focus**:
- Unit tests for core logic
- Integration tests for agent orchestration
- No UI/API testing (that's dashboard-specific)

**Run with**:
```bash
pytest tests/
```

### Dashboard Tests (`dashboard/backend/tests/`)

**Focus**:
- API endpoint tests
- Database schema tests
- UI integration tests

**Run with**:
```bash
cd dashboard/backend
pytest
```

### Custom Integration Tests

You write your own tests for your integration!

## Adding New Features: Decision Tree

```
                   New Feature Request
                          │
                          ↓
          Does it change core orchestration logic?
                    ╱          ╲
                 YES            NO
                  │              │
                  ↓              ↓
        Add to src/orchestrator/   Is it dashboard-specific?
        • Keep integration-agnostic     ╱          ╲
        • Use callbacks for hooks     YES          NO
        • Test with multiple          │            │
          integration types           ↓            ↓
                                 Add to      Add to custom
                                dashboard/   integration or
                                           new example
```

## Quick Reference: Where Does It Go?

| Feature | Location | Why |
|---------|----------|-----|
| New agent role | `src/orchestrator/core/types.py` + `prompts.py` | Core capability |
| New workflow pattern | `src/orchestrator/workflow/planner.py` | Core logic |
| Extended thinking support | `src/orchestrator/core/agent.py` | Core capability |
| Cost tracking | `src/orchestrator/observability/metrics.py` | Core metric |
| Task History UI | `dashboard/frontend/src/components/` | Dashboard feature |
| Cost visualization charts | `dashboard/frontend/src/components/` | Dashboard feature |
| Database schema for tasks | `dashboard/backend/app/models/` | Dashboard persistence |
| GitHub Issues integration | `examples/integrations/github_bot.py` | Custom integration |
| Telegram bot | `examples/integrations/telegram_bot.py` | Custom integration |
| Progress callbacks | `src/orchestrator/core/orchestrator.py` | Core extensibility |
| WebSocket updates | `dashboard/backend/app/api/v1/websocket.py` | Dashboard feature |

## Common Mistakes to Avoid

### ❌ Mistake 1: Adding UI Logic to Core
```python
# Bad: In src/orchestrator/core/orchestrator.py
from dashboard.backend.app.models.task import Task

class Orchestrator:
    def execute(self, prompt: str):
        # Creating dashboard Task record in core
        task = Task(description=prompt)  # Don't do this!
```

**Why wrong**: Core orchestrator should never know about dashboard database schema.

**Correct approach**: Dashboard wraps orchestrator and creates its own records.

### ❌ Mistake 2: Hardcoding Dashboard Dependencies
```python
# Bad: In src/orchestrator/core/agent.py
LOGS_DIR = "/path/to/dashboard/backend/agent_logs"  # Don't hardcode!
```

**Why wrong**: Users who don't use the dashboard can't change this.

**Correct approach**: Make it configurable via constructor or environment variable.

### ❌ Mistake 3: Assuming Dashboard Exists
```python
# Bad: In src/orchestrator/observability/monitor.py
def broadcast_update(self, data):
    websocket_manager.broadcast(data)  # Assumes dashboard WebSocket!
```

**Why wrong**: CLI users and custom integrations don't have WebSocket.

**Correct approach**: Use callbacks that the integration provides.

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| 0.1.5 | 2025-11-08 | Added cost/duration tracking, verified clean architecture |
| 0.1.4 | 2025-11-07 | Dashboard Phase 2 complete |
| 0.1.3 | 2025-11-06 | Task execution and agent log viewer |
| 0.1.0 | 2025-11-05 | Initial release with core orchestrator |

## Contributing

When contributing, please:

1. **Understand the architecture** before making changes
2. **Ask first** if unsure where something belongs
3. **Keep core independent** - no dashboard dependencies
4. **Document integration patterns** for new examples
5. **Test with multiple integrations** when changing core

## Questions?

- "Should this go in core or dashboard?" → See decision tree above
- "Can I add X to the orchestrator?" → Does it work for CLI, dashboard, AND custom integrations?
- "How do I integrate with Y?" → Check INTEGRATION_GUIDE.md for patterns

---

**Remember**: The orchestrator is a library first, dashboard second. Keep it flexible and integration-agnostic!
