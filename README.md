# Claude Multi-Agent Orchestrator

A powerful Python framework for orchestrating multiple Claude agents with CRUD operations, intelligent task decomposition, and comprehensive observability.

## Overview

The Multi-Agent Orchestrator implements a new paradigm for agentic engineering: **the rate at which you create and command agents becomes your engineering constraint**. This system enables you to scale compute and impact by deploying specialized agent teams that work in parallel.

### Core Philosophy

> "Stop thinking about what you can do. Start thinking about scaling your agents to do it for you."

The orchestrator treats agents as **temporary, deletable resources** that serve single purposes. Once a job is complete, agents are deleted to free resources. This is the key to managing agents at scale.

## Key Features

### 🎯 The Three Pillars

1. **Orchestrator Agent** - Unified interface to manage your entire fleet
   - Creates, commands, monitors, and deletes agents
   - Decomposes high-level prompts into concrete work
   - Protects its own context by delegating rather than absorbing all work

2. **CRUD for Agents** - Full lifecycle management
   - **Create**: Spawn specialized agents for specific jobs
   - **Read**: Monitor status and results in real-time
   - **Update**: Send messages and maintain conversation context
   - **Delete**: Clean up when work is done

3. **Observability** - Comprehensive monitoring and metrics
   - Real-time performance and cost tracking
   - Files consumed vs produced tracking
   - Agent-level breakdowns with filtering
   - One-click inspection of any agent's work

### 🔧 Specialized Agent Roles

- **Planner**: Task planning and decomposition
- **Builder**: Implementation and coding
- **Reviewer**: Code review and quality assurance
- **Analyst**: Data analysis and research
- **Tester**: Testing and validation
- **Documenter**: Documentation writing

### ⚡ Parallel Execution

Deploy 3x (or more) compute with a single prompt by running agents in parallel:

```python
# Sequential: 3 agents × 10s each = 30s total
# Parallel: 3 agents × 10s each = 10s total

result = await orchestrator.execute(
    prompt="Analyze code quality and suggest improvements",
    execution_mode="parallel"
)
```

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd orchestrator

# Install dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"

# Note: Authentication is handled through Claude Code CLI
# No need to manually configure API keys
```

## Quick Start

### CLI Usage

```bash
# Initialize configuration
orchestrator init

# Execute a task
orchestrator execute "Find and analyze all Python files in the project"

# Execute with specific task type
orchestrator execute "Fix the bug in user authentication" --task-type bug_fix

# Execute in parallel mode
orchestrator execute "Add comprehensive documentation" --mode parallel

# Show status
orchestrator status

# List active agents
orchestrator list-agents

# List all tasks
orchestrator list-tasks

# Get task details
orchestrator task-details <task-id>

# Get agent details
orchestrator agent-details <agent-id>
```

### Python API

```python
import asyncio
from orchestrator import Orchestrator

async def main():
    # Note: API key is not needed - Claude Code SDK uses CLI authentication
    # Create orchestrator
    orchestrator = Orchestrator(
        enable_monitoring=True
    )

    try:
        await orchestrator.start()

        # Execute a high-level task
        result = await orchestrator.execute(
            prompt="Implement a feature to export data to CSV",
            task_type="feature_implementation",
            execution_mode="sequential"
        )

        print(f"Success: {result.success}")
        print(f"Cost: ${result.metrics.total_cost:.4f}")
        print(f"Output: {result.output}")

    finally:
        await orchestrator.stop()

asyncio.run(main())
```

## Architecture

```
orchestrator/
├── core/
│   ├── orchestrator.py      # Main orchestrator class
│   ├── agent_manager.py     # CRUD operations for agents
│   ├── agent.py              # Individual agent wrapper
│   └── types.py              # Type definitions
├── observability/
│   ├── monitor.py            # Real-time monitoring
│   ├── metrics.py            # Metrics collection
│   └── logger.py             # Structured logging
├── storage/
│   ├── database.py           # SQLite persistence
│   └── models.py             # Database models
├── workflow/
│   ├── planner.py            # Task decomposition
│   └── executor.py           # Workflow execution
└── cli/
    └── commands.py           # CLI interface
```

## Core Concepts

### The Core Four Management

Every agent is managed through four essential properties:

1. **Context Window** - How much information the agent can work with
2. **Model** - Which AI model powers the agent
3. **Prompt** - The instructions given to the agent
4. **Tools** - What capabilities the agent can execute

Understanding these four leverage points for every agent is fundamental to effective agentic engineering.

### Workflow Pattern

1. **User gives high-level prompt** to the orchestrator
2. **Orchestrator thinks** through the work and creates a plan
3. **Orchestrator spawns specialized agents** in order:
   - **Analyst** researches and analyzes requirements
   - **Planner** creates implementation plans and tasks
   - **Builder** implements code following the plan
   - **Tester** writes and runs tests
   - **Reviewer** verifies code follows the plan
4. **Each agent executes focused work** on its specific task
5. **Orchestrator monitors via status checks** (~15 second intervals)
6. **Agents pass results** to next agent in pipeline
7. **Results are observable** showing consumed/produced files
8. **Orchestrator verifies completion** and deletes temporary agents

### Protected Context Windows

The orchestrator doesn't always observe all logs—it would blow its own context window. Instead:

- Selectively monitors summaries and status checks
- Delegates work rather than consuming full logs
- Same principle applies to all agents: they can't handle everything

## Examples

### Basic Orchestration

```python
# See examples/basic_orchestration.py
result = await orchestrator.execute(
    prompt="Find all Python files and analyze their structure",
    task_type="auto"
)
```

### Specialized Agents Workflow

```python
# See examples/specialized_agents.py
result = await orchestrator.execute_custom_workflow(
    prompt="Add factorial calculation feature",
    roles=[
        AgentRole.SCOUT,      # Find relevant files
        AgentRole.BUILDER,    # Implement feature
        AgentRole.TESTER,     # Write tests
        AgentRole.REVIEWER,   # Review code
    ],
    parallel=False
)
```

### Parallel Execution

```python
# See examples/parallel_execution.py
result = await orchestrator.execute_custom_workflow(
    prompt="Analyze code quality",
    roles=[AgentRole.REVIEWER, AgentRole.ANALYST, AgentRole.TESTER],
    parallel=True  # 3x faster!
)
```

### Manual Agent Control

```python
# See examples/manual_agent_control.py

# CREATE
scout_id = await orchestrator.create_agent(
    role=AgentRole.SCOUT,
    name="My Planner"
)

# READ
details = orchestrator.get_agent_details(scout_id)

# UPDATE (send messages)
response = await orchestrator.send_to_agent(
    scout_id,
    "Find all Python files"
)

# DELETE
await orchestrator.delete_agent(scout_id)
```

### Observability

```python
# See examples/observability_demo.py

# Get comprehensive status
status = orchestrator.get_status()

# Fleet metrics
print(status['fleet'])

# Files consumed vs produced
print(status['monitoring']['files'])

# Per-agent breakdown
agents = orchestrator.list_agents()
for agent in agents:
    print(agent['metrics'])
```

## Task Types

The planner includes templates for common workflows:

- `feature_implementation` - Analyst → Planner → Builder → Tester → Reviewer
- `bug_fix` - Analyst → Planner → Builder → Tester → Reviewer
- `code_review` - Analyst → Planner → Reviewer → Tester
- `documentation` - Analyst → Planner → Documenter → Reviewer
- `auto` - Automatically determine based on prompt
- `custom` - Define your own workflow

## Observability Metrics

### Agent Metrics
- Total cost ($)
- Total tokens (input + output)
- Messages sent
- Tool calls
- Files read/written
- Execution time

### Fleet Metrics
- Total agents (by status, by role)
- Aggregate costs
- Aggregate tokens
- Files consumed vs produced

### Critical Principle

> "If you can't measure it, you can't improve it. If you can't measure it, you can't scale it."

The observability system provides:
- Real-time monitoring of every agent
- Cost and performance tracking
- File consumption/production tracking
- Agent-level inspection with filtering

## Advanced Usage

### Custom Agent Roles

```python
agent = await agent_manager.create_agent(
    name="Custom Specialist",
    role=AgentRole.CUSTOM,
    system_prompt="You are a specialized agent for...",
    max_tokens=8192,
    temperature=0.7
)
```

### Task Dependencies

```python
# Execute subtasks with dependencies
await executor.execute_with_dependencies(
    task=task,
    dependencies={
        1: [0],      # Subtask 1 depends on 0
        2: [0, 1],   # Subtask 2 depends on 0 and 1
        3: [2],      # Subtask 3 depends on 2
    }
)
```

### Database Persistence

```python
from orchestrator.storage import Database

db = Database(Path("orchestrator.db"))
await db.connect()

# Save agent records
await db.save_agent(agent_record)

# Query agents
agents = await db.list_agents(role="scout")

# Analytics
total_cost = await db.get_total_cost()
cost_by_role = await db.get_cost_by_role()
```

## Configuration

Environment variables in `.env`:

```bash
# Optional Configuration
DEFAULT_MODEL=claude-sonnet-4-5-20250929
ORCHESTRATOR_DB_PATH=./orchestrator.db
ORCHESTRATOR_LOG_LEVEL=INFO
ORCHESTRATOR_MAX_PARALLEL_AGENTS=5
MONITOR_INTERVAL_SECONDS=15
ENABLE_COST_TRACKING=true
ENABLE_OBSERVABILITY=true

# Note: ANTHROPIC_API_KEY is no longer required
# Authentication is handled through Claude Code CLI
```

## Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=orchestrator --cov-report=html

# Type checking
mypy src/orchestrator

# Linting
ruff check src/orchestrator
black --check src/orchestrator
```

## Best Practices

### 1. Keep Agent Contexts Focused
```python
# ❌ Bad: One agent doing everything
agent.execute_task("Find files, implement feature, write tests, review code")

# ✅ Good: Specialized agents for each task
scout.execute_task("Find relevant files")
builder.execute_task("Implement feature based on Planner findings")
tester.execute_task("Write tests for new feature")
```

### 2. Use Parallel Execution When Possible
```python
# If tasks are independent, run in parallel
result = await orchestrator.execute_custom_workflow(
    prompt="Analyze codebase",
    roles=[AgentRole.REVIEWER, AgentRole.ANALYST, AgentRole.DOCUMENTER],
    parallel=True  # 3x faster!
)
```

### 3. Clean Up Agents
```python
# The orchestrator does this automatically, but for manual control:
try:
    agent = await orchestrator.create_agent(...)
    result = await agent.execute_task(...)
finally:
    await orchestrator.delete_agent(agent.agent_id)
```

### 4. Monitor Context Usage
```python
agent_details = orchestrator.get_agent_details(agent_id)
usage = agent_details['context_usage']

if usage['usage_percentage'] > 80:
    # Time to wrap up and delete this agent
    await orchestrator.delete_agent(agent_id)
```

## Why This Differs from Sub-Agents

Traditional sub-agent patterns (like the Claude Code SDK's `Task` tool) often lose context or require managing where agents operate. This system maintains:

- **Persistent agent state** - Can interact with agents repeatedly until job is done
- **Explicit control** - Full lifecycle management, not just spawning
- **Specialization** - Agents designed for your specific use case
- **Clear observability** - Know exactly what each agent did and with what resources

## Performance Considerations

### Context Window Management
- Monitor usage with `agent.get_context_window_usage()`
- Delete agents before hitting 80% context usage
- Use multiple focused agents instead of one general agent

### Cost Optimization
- Use parallel execution to minimize wall-clock time
- Clean up agents promptly to avoid unnecessary costs
- Monitor costs in real-time via observability dashboard
- Use appropriate models for each agent's complexity

### Scaling
- The orchestrator can manage dozens of agents simultaneously
- Parallel execution scales linearly with agent count
- SQLite persistence handles thousands of task/agent records
- Monitor system resources and adjust `ORCHESTRATOR_MAX_PARALLEL_AGENTS`

## Roadmap

For detailed feature plans, priorities, and implementation timelines, see [ROADMAP.md](ROADMAP.md).

## License

MIT License - see LICENSE file for details

## Credits

This implementation is inspired by the multi-agent orchestration concepts described in the project documentation, emphasizing:

- Agent specialization and focused contexts
- CRUD patterns for agent lifecycle management
- Observability as a first-class concern
- Scaling compute through intelligent orchestration

---

**Remember**: The future of engineering isn't about how fast you can write prompts—it's about how intelligently you can scale your compute through well-orchestrated agent teams.
