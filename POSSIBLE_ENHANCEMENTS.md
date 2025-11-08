# Possible Enhancements

This document outlines potential improvements and features that could enhance the orchestrator system based on analysis of the current architecture.

## Architecture Principles

**IMPORTANT**: All enhancements must maintain the orchestrator's library-first, integration-agnostic design:

- ✅ **DO**: Add features to orchestrator core that work with any integration
- ✅ **DO**: Use callbacks, events, and hooks for extensibility
- ✅ **DO**: Keep dashboard as one possible monitoring solution
- ❌ **DON'T**: Add dashboard-specific code to orchestrator core
- ❌ **DON'T**: Assume users will use the sample dashboard
- ❌ **DON'T**: Create tight coupling between core and any specific UI/API

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for architectural patterns and examples of integrating the orchestrator with custom systems (GitHub Issues, Telegram, Slack, custom APIs, etc.).

## 1. CLI Task Database Integration

**Status**: Not Implemented
**Priority**: Medium
**Complexity**: Medium

### Problem

Tasks executed via the CLI (`orchestrator execute "..."`) are currently NOT stored in the dashboard database. This creates a split between:
- **CLI tasks**: Logged to `/agent_logs/{task_id}/` but not in database
- **Dashboard tasks**: Both logged to `/dashboard/backend/agent_logs/{task_id}/` AND stored in database

### Impact

- No unified view of all task executions
- CLI task metrics (cost, duration) not visible in dashboard
- Task History page only shows dashboard-executed tasks
- Analytics and reporting incomplete

### Technical Details

**Why this happens**:
- CLI uses orchestrator directly ([src/orchestrator/core/orchestrator.py](src/orchestrator/core/orchestrator.py))
- Dashboard API wraps orchestrator with database persistence ([dashboard/backend/app/services/orchestrator_executor.py](dashboard/backend/app/services/orchestrator_executor.py))
- The orchestrator core has no knowledge of the database

**Evidence**:
```bash
# CLI task executed at 08:55
Task ID: 803a350b-117b-4fbc-88f2-7b695ce95e6d

# Database query shows only 6 tasks, none with that ID
sqlite3 orchestrator.db "SELECT id FROM tasks ORDER BY created_at DESC LIMIT 5;"
# Returns: older tasks from Nov 6-7, not the CLI task from Nov 8
```

### Possible Solutions

#### Option 1: Shared Database (Recommended)
Make the dashboard database accessible from the CLI orchestrator:

**Pros**:
- Single source of truth for all tasks
- Complete analytics across CLI and dashboard
- Consistent logging location

**Cons**:
- Requires database dependency in CLI
- Need to ensure database file path is configurable
- Potential concurrency issues if CLI and dashboard access simultaneously

**Implementation**:
```python
# In src/orchestrator/core/orchestrator.py
from orchestrator.storage.database import Database

class Orchestrator:
    def __init__(self, ..., db_path: Optional[str] = None):
        # Optional database integration
        if db_path:
            self.db = Database(db_path)
        else:
            self.db = None

    async def execute(self, ...):
        # Create task record if database enabled
        if self.db:
            task_id = await self.db.create_task(...)

        # ... execute workflow ...

        # Update task with results
        if self.db:
            await self.db.update_task(task_id, results)
```

#### Option 2: Separate Log Directories
Keep them separate but document the difference clearly:

**Pros**:
- Simpler, no code changes needed
- Clear separation of concerns
- No concurrency issues

**Cons**:
- Incomplete analytics
- Confusing for users
- Duplicate log infrastructure

### Recommendations

1. **Short-term**: Document the current behavior in README
2. **Long-term**: Implement Option 1 (Shared Database) with:
   - Environment variable `ORCHESTRATOR_DB_PATH` for CLI
   - Default to dashboard database location if exists
   - Graceful fallback if database unavailable

---

## 2. Extended Thinking Integration

**Status**: Infrastructure Ready, Feature Not Enabled
**Priority**: High
**Complexity**: Low

### Current Status

The logging infrastructure is **correctly implemented** and ready to capture Extended Thinking:

**Evidence from code**:
```python
# agent_logger.py:115-116 - ThinkingBlock detection
elif isinstance(block, ThinkingBlock):
    self._log_thinking_block(block)

# agent_logger.py:138-142 - Logging implementation
def _log_thinking_block(self, block: ThinkingBlock) -> None:
    """Log thinking block"""
    with open(self.text_file, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] THINKING:\n")
        f.write(f"{block.thinking}\n\n")
```

**Why no thinking logs appear**:
- Extended Thinking is NOT enabled in agent configurations
- Without enabling this feature, Claude doesn't emit ThinkingBlocks
- The infrastructure is ready, just needs activation

### Implementation

To enable Extended Thinking, add to agent options:

```python
# In src/orchestrator/core/agent.py

def _build_options(self) -> dict:
    """Build SDK client options"""
    options = {
        "model": self.config.model,
        "system": self.config.system_prompt,
        # ... existing options ...

        # Enable Extended Thinking
        "thinking": {
            "type": "enabled",
            "budget_tokens": 10000  # Adjust based on task complexity
        }
    }
    return options
```

### Benefits

1. **Transparency**: See Claude's reasoning process
2. **Debugging**: Understand why agents made certain decisions
3. **Quality**: Identify where agents struggle or succeed
4. **Learning**: Study how agents approach problems

### Where Thinking Would Appear

```
{agent_logs}/{task_id}/{agent_id}_{agent_name}_{timestamp}/text.txt
```

Example:
```
[2025-11-08T08:55:35.978232] AssistantMessage:
I'll create a simple hello world function in a new file called hello.py.

[2025-11-08T08:55:37.123456] THINKING:
I need to consider where to create this file. The user didn't specify a location,
so I should check the current working directory first. I'll use the Write tool
to create the file with a proper docstring and main guard...

[2025-11-08T08:55:41.110584] AssistantMessage:
I've created a new file called `hello.py` with a simple hello world function...
```

### Configuration Options

Different thinking budgets for different agent types:

```python
THINKING_BUDGETS = {
    AgentRole.ANALYST: 15000,   # More thinking for research
    AgentRole.PLANNER: 12000,   # More thinking for planning
    AgentRole.BUILDER: 8000,    # Less thinking for implementation
    AgentRole.REVIEWER: 10000,  # Moderate thinking for review
    AgentRole.TESTER: 5000,     # Minimal thinking for testing
}
```

### Recommendations

1. **Start small**: Enable with 5000-10000 token budget
2. **Monitor costs**: Extended Thinking increases API costs
3. **Analyze logs**: Review thinking quality before expanding
4. **Adjust per role**: Different agents need different thinking budgets
5. **Make configurable**: Add to environment variables or CLI flags

---

## 3. Unified Log Directory

**Status**: Not Implemented
**Priority**: Low
**Complexity**: Low

### Problem

Currently there are two separate log directories:
- CLI logs: `/agent_logs/{task_id}/`
- Dashboard logs: `/dashboard/backend/agent_logs/{task_id}/`

This creates confusion and makes log analysis more difficult.

### Solution

Configure both CLI and dashboard to use the same log directory:

```python
# In src/orchestrator/core/config.py
AGENT_LOGS_DIR = os.getenv("AGENT_LOGS_DIR", "/path/to/unified/agent_logs")

# In dashboard/backend/app/core/config.py
agent_logs_dir: str = Field(
    default="../../../agent_logs",  # Points to orchestrator root
    alias="AGENT_LOGS_DIR"
)
```

### Benefits

- Single location for all agent logs
- Easier debugging and analysis
- Dashboard can display CLI task logs
- Consistent log structure

---

## 4. Task Cost and Duration Visualization

**Status**: Partially Implemented
**Priority**: High
**Complexity**: Medium

### Current Status

✅ **Implemented**:
- Database fields for `total_cost` and `duration_seconds`
- API filtering and sorting by cost/duration
- Task History table displays cost and duration
- Formatting functions for display ($X.XX, Xm Ys)

❌ **Not Yet Implemented**:
- Visual charts/graphs for cost trends over time
- Cost breakdown by agent type
- Duration distribution histograms
- Budget alerts and thresholds

### Possible Enhancements

#### Phase 3.1: Basic Charts
- Line chart: Cost over time
- Bar chart: Cost by task type
- Pie chart: Cost distribution by agent role

#### Phase 3.2: Advanced Analytics
- Cost per token analysis
- Duration vs complexity correlation
- Efficiency metrics (cost per task completion)
- Budget tracking and alerts

#### Phase 3.3: Predictive Features
- Estimated cost before task execution
- Duration predictions based on historical data
- Budget recommendations

---

## 5. Real-time Thinking Display

**Status**: Not Implemented
**Priority**: Medium
**Complexity**: Medium

### Concept

Once Extended Thinking is enabled, create a real-time viewer in the dashboard to display agent reasoning as it happens.

### Features

- WebSocket streaming of thinking blocks
- Syntax highlighting for code reasoning
- Collapsible thinking sections
- Filter by agent or time range
- Export thinking logs for analysis

### Implementation Considerations

- Requires WebSocket support (already implemented)
- May increase bandwidth for streaming thoughts
- Privacy/security: thinking may contain sensitive info
- UI complexity: need good UX for long thought streams

---

## 6. Task Templates and Presets

**Status**: Not Implemented
**Priority**: Medium
**Complexity**: Low

### Concept

Allow users to save and reuse task configurations:

```json
{
  "name": "Weekly Code Review",
  "description": "Review all PRs from the past week",
  "task_type": "code_review",
  "include_analyst": "no",
  "working_directory": "/path/to/repo",
  "schedule": "weekly"
}
```

### Features

- Save common task configurations
- One-click task execution from templates
- Share templates with team
- Schedule recurring tasks

---

## 7. Multi-Project Support

**Status**: Not Implemented
**Priority**: Low
**Complexity**: High

### Concept

Support multiple projects with separate:
- Working directories
- Agent configurations
- Cost tracking
- Database schemas

### Features

- Project switching in dashboard
- Per-project analytics
- Cross-project comparisons
- Project-specific agent templates

---

## Implementation Priority

### High Priority (Immediate Value)
1. ✅ Cost and Duration Tracking (Completed v0.1.5)
2. 🔄 Extended Thinking Integration (Easy, high value)

### Medium Priority (Next Quarter)
3. CLI Task Database Integration (Unified analytics)
4. Task Cost Visualization (Better insights)
5. Real-time Thinking Display (Better observability)

### Low Priority (Future Consideration)
6. Unified Log Directory (Nice to have)
7. Task Templates (Convenience feature)
8. Multi-Project Support (Enterprise feature)

---

## Contributing

If you're interested in implementing any of these enhancements:

1. Open an issue to discuss the approach
2. Reference this document in your PR
3. Update this document as features are implemented
4. Move completed items to CHANGELOG.md

---

**Last Updated**: 2025-11-08
**Version**: 0.1.5
