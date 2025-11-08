# Workflow Planning Architecture: The Planning Agent Approach

**Date**: 2025-11-06
**Context**: Dashboard Phase 2 complete, moving to orchestrator intelligence optimization
**Decision Point**: How should the orchestrator determine workflows?

---

## Executive Summary

**RECOMMENDATION**: Introduce a **dedicated PLANNER agent** as the first step in the orchestrator workflow, separate from the TaskPlanner component.

**Key Insight from Multi-Agent Orchestration principles**:
> "The orchestrator doesn't do the work—it delegates to specialized agents. Each agent has a dedicated, specific focus."

The current `TaskPlanner` (template-based) should be **replaced** by a **PLANNER agent** that:
1. Analyzes the task using Claude's reasoning
2. Determines the optimal workflow dynamically
3. Identifies what context each agent needs
4. Decides parallel vs sequential execution
5. Sets scope/constraints per agent (e.g., "simple testing only")

---

## Why a PLANNER Agent (Not Enhanced TaskPlanner)

### Current Problem: Template-Based Planning is Inflexible

**Current Architecture** ([src/orchestrator/workflow/planner.py](../src/orchestrator/workflow/planner.py)):
```python
class TaskPlanner:
    def plan_task(self, task_id: str, description: str, task_type: str):
        # Uses hardcoded templates
        if task_type == "feature_implementation":
            return ["ANALYST", "PLANNER", "BUILDER", "TESTER", "REVIEWER"]
        elif task_type == "documentation":
            return ["ANALYST", "PLANNER", "DOCUMENTER", "REVIEWER"]
```

**Problems**:
1. ❌ Cannot adapt to task nuances ("create square function" still gets full workflow)
2. ❌ Cannot skip agents based on context (PLANNER not needed if ANALYST already created structure)
3. ❌ Cannot determine parallel execution opportunities
4. ❌ Cannot scope agent work (TESTER does full suite for trivial tasks)
5. ❌ Hard to maintain (every workflow variation requires code changes)

### Core Principle: "Protected Context Windows"

From Multi-Agent Orchestration:
> "The orchestrator doesn't always observe all logs—it would blow its own context window. Must selectively monitor summaries and status checks."

**Applying this principle**:
- The **orchestrator** should NOT do complex analysis itself
- The **orchestrator** creates a **PLANNER agent** to analyze the task
- The **PLANNER agent** has full context to reason about workflow
- The **orchestrator** receives a structured plan and executes it

This **protects the orchestrator's context** while enabling intelligent planning.

---

## Recommended Architecture: Three-Tier System

### Tier 1: Orchestrator (Task Decomposition & Lifecycle)
**Responsibility**: High-level workflow management
**Location**: `WorkflowExecutor` + `AgentManager`

**Does**:
- Receives user task description
- Creates PLANNER agent with task context
- Receives workflow plan from PLANNER
- Executes workflow (sequential/parallel based on plan)
- Monitors agent status
- Cleans up agents (CRUD pattern)

**Does NOT**:
- Analyze task complexity
- Determine which agents to use
- Decide agent scope/constraints
- Hold full task context (delegates to PLANNER)

### Tier 2: PLANNER Agent (Intelligent Workflow Design)
**Responsibility**: Task analysis and workflow planning
**Role**: AgentRole.PLANNER (but different from current usage!)

**System Prompt**:
```
You are a workflow planning specialist. Analyze tasks and create optimal agent workflows.

INPUTS:
- Task description
- Task type (feature_implementation, bug_fix, documentation, etc.)
- Working directory structure
- Available agent roles: ANALYST, BUILDER, TESTER, REVIEWER, DOCUMENTER

ANALYSIS FRAMEWORK:
1. Complexity Assessment
   - Simple: Single file, <50 lines, straightforward logic
   - Medium: Multiple files, <200 lines, some complexity
   - Complex: Architecture changes, >200 lines, multiple systems

2. Scope Determination
   - What needs analysis vs direct implementation?
   - What's already provided vs needs research?
   - What can be parallelized?

3. Agent Selection Criteria
   - ANALYST: Only if research/exploration needed (not for trivial tasks)
   - BUILDER: Always for implementation
   - TESTER: Scope based on complexity (simple = basic validation only)
   - REVIEWER: Skip for trivial changes
   - DOCUMENTER: Only if documentation is primary deliverable

4. Context Passing Strategy
   - For outputs >5KB: Recommend file-based passing
   - For structured data: Define expected format
   - For simple handoffs: Direct text passing

OUTPUT FORMAT (JSON):
{
  "workflow": [
    {
      "agent_role": "BUILDER",
      "scope": "Create a simple function to square a number. Write minimal implementation only.",
      "constraints": ["single_file", "no_dependencies"],
      "execution_mode": "sequential",
      "estimated_tokens": 30000
    },
    {
      "agent_role": "TESTER",
      "scope": "Write 2-3 basic tests to verify core functionality. DO NOT create comprehensive test suite.",
      "constraints": ["basic_validation_only", "happy_path_plus_one_edge_case"],
      "execution_mode": "sequential",
      "estimated_tokens": 40000,
      "depends_on": ["BUILDER"]
    }
  ],
  "total_estimated_cost": 0.08,
  "complexity": "simple",
  "rationale": "Task is trivial (single math function). Skipping ANALYST (no research needed), limiting TESTER to basic validation."
}
```

**Benefits**:
- ✅ Uses Claude's reasoning to adapt to task nuances
- ✅ Can skip agents intelligently
- ✅ Can scope agent work appropriately
- ✅ Can identify parallel execution opportunities
- ✅ Easy to refine via prompt engineering (no code changes)

### Tier 3: Execution Agents (ANALYST, BUILDER, TESTER, etc.)
**Responsibility**: Execute focused work based on plan
**Receives from PLANNER**: Scoped instructions and constraints

**Example** - Before vs After:

**Before** (template-based):
```python
# TESTER always gets generic prompt
TESTER_PROMPT = "Test the implementation thoroughly with comprehensive test suite"
# Result: 159K tokens for trivial function
```

**After** (PLANNER-scoped):
```python
# PLANNER determines scope
planner_output = {
    "agent_role": "TESTER",
    "scope": "Write 2-3 basic tests only. DO NOT create comprehensive suite.",
    "constraints": ["basic_validation_only"]
}

# TESTER receives scoped prompt
TESTER_PROMPT = f"{planner_output['scope']}\n\nConstraints: {planner_output['constraints']}"
# Result: ~40K tokens (75% reduction)
```

---

## Integration with Existing Components

### What Changes:

**1. TaskPlanner → PLANNER Agent** ([src/orchestrator/workflow/planner.py](../src/orchestrator/workflow/planner.py))

**Old**:
```python
class TaskPlanner:
    def plan_task(self, description: str, task_type: str) -> OrchestratorTask:
        # Template-based
        if task_type == "feature_implementation":
            subtasks = self._create_feature_workflow()
```

**New**:
```python
class TaskPlanner:
    async def plan_task(self, description: str, task_type: str, working_dir: str) -> OrchestratorTask:
        # Create PLANNER agent
        planner_agent = await self.agent_manager.create_agent(
            agent_id=f"planner_{task_id}",
            role=AgentRole.PLANNER,
            custom_instructions="Workflow Planning Specialist"
        )

        # Give PLANNER the task analysis prompt
        planning_prompt = self._build_planning_prompt(description, task_type, working_dir)

        # PLANNER returns structured workflow plan
        plan_json = await planner_agent.execute(planning_prompt)

        # Parse and return OrchestratorTask
        return self._parse_plan(plan_json, task_id, description)
```

**2. WorkflowExecutor - Use PLANNER's scope** ([src/orchestrator/workflow/executor.py](../src/orchestrator/workflow/executor.py))

**Old**:
```python
# Generic agent creation
agent = await self.agent_manager.create_agent(
    agent_id=agent_id,
    role=subtask["role"],
    custom_instructions=subtask["description"]  # Generic description
)
```

**New**:
```python
# Use PLANNER's scoped instructions
agent = await self.agent_manager.create_agent(
    agent_id=agent_id,
    role=subtask["role"],
    custom_instructions=subtask["scope"],  # Specific scope from PLANNER
    metadata={"constraints": subtask["constraints"]}
)
```

**3. Agent System Prompts - Respect Constraints** ([src/orchestrator/config/prompts.py](../src/orchestrator/config/prompts.py))

Add constraint awareness:
```python
def get_agent_prompt(role: AgentRole, constraints: List[str] = None) -> str:
    base_prompt = AGENT_PROMPTS[role]

    if constraints:
        constraint_text = "\n\nCONSTRAINTS:\n" + "\n".join(f"- {c}" for c in constraints)
        base_prompt += constraint_text

    return base_prompt
```

### What Stays the Same:

- ✅ Agent roles (ANALYST, BUILDER, TESTER, REVIEWER, DOCUMENTER)
- ✅ AgentManager (CRUD operations)
- ✅ WorkflowExecutor (sequential/parallel execution)
- ✅ Progress tracking (DashboardProgressTracker)
- ✅ Agent monitoring and observability

---

## Handling Greenfield vs Complex Projects

### For Simple Tasks (Current Focus)
**Flow**: Orchestrator → PLANNER agent → Execution agents → Cleanup

**PLANNER analyzes**:
- "Create function to square a number" → Simple
- Workflow: `[BUILDER, TESTER(scoped)]`
- Skip: ANALYST, REVIEWER
- TESTER scope: "Basic validation only"

### For Complex Brownfield Tasks
**Flow**: Orchestrator → PLANNER agent → Execution agents (possibly ANALYST first) → Cleanup

**PLANNER analyzes**:
- "Refactor authentication system to use OAuth2" → Complex
- Workflow: `[ANALYST, ARCHITECT, BUILDER, TESTER(comprehensive), REVIEWER]`
- ANALYST: Research current implementation
- ARCHITECT: Design migration plan (NEW role if needed)
- Execution mode: Some parallel (tests can run while documenting)

### For Greenfield Projects (Future Enhancement)
**Option 1: PLANNER agent with richer context**
```
Task: "Build a SaaS project management tool"
PLANNER analyzes:
- Recognizes greenfield project
- Asks clarifying questions (via orchestrator → user)
- Creates multi-phase plan:
  Phase 1: Architecture
  Phase 2: Backend MVP
  Phase 3: Frontend MVP
  Phase 4: Integration
```

**Option 2: Separate Planning Frontend (PRPGen-style)**

Per your spec-generation-research.md, for MAJOR greenfield projects:

1. User uses **planning frontend** (separate app/UI)
2. Frontend asks Spec-Kit style questions (9 taxonomy categories)
3. Frontend performs PRP-style context engineering
4. Frontend generates **detailed specification document**
5. User submits spec to **orchestrator** as task description
6. PLANNER agent receives rich spec, creates workflow from it

**Benefit**: Separation of concerns
- **Planning Frontend**: Human-in-the-loop, visual UI, comprehensive elicitation
- **Orchestrator PLANNER**: Receives spec, creates tactical agent workflow
- Orchestrator stays focused on execution, not requirements gathering

---

## Migration Path: Phase 3 Implementation

### Phase 1: PLANNER Agent Core (Week 1)

**Tasks**:
1. Create PLANNER agent system prompt with analysis framework
2. Modify TaskPlanner to invoke PLANNER agent
3. Update WorkflowExecutor to use PLANNER's scoped instructions
4. Add constraint passing to agent creation

**Success Criteria**:
- PLANNER agent successfully analyzes simple tasks
- Scoped instructions reduce TESTER token usage by 50%+
- Dashboard shows PLANNER as first step in workflow

### Phase 2: Smart Scope & Skip Logic (Week 2)

**Tasks**:
1. Enhance PLANNER prompt with skip logic
2. Implement constraint system in agent prompts
3. Add parallel execution detection
4. File-based output recommendations for large context

**Success Criteria**:
- Simple tasks skip unnecessary agents
- TESTER respects complexity constraints
- PLANNER identifies parallel opportunities

### Phase 3: Learning & Optimization (Week 3)

**Tasks**:
1. Track PLANNER's estimates vs actual costs
2. Feed actual execution data back to PLANNER
3. Refine PLANNER prompt based on outcomes
4. Build "common patterns" library

**Success Criteria**:
- PLANNER's cost estimates within 20% accuracy
- Workflow efficiency improves over time
- Dashboard shows cost predictions

---

## Addressing Your Specific Questions

### Q1: "Should the orchestrator analyze the task or delegate to a specialized agent?"

**A**: **Delegate to PLANNER agent**

**Rationale**:
- Aligns with core principle: "Orchestrator delegates work, doesn't do it itself"
- Protects orchestrator's context window
- PLANNER agent can use full Claude reasoning capacity
- Easy to refine via prompt engineering
- Maintains CRUD pattern (PLANNER is temporary, deleted after planning)

### Q2: "For greenfield projects, should we ask users questions?"

**A**: **Two-tier approach**

**Small-to-Medium Projects**: PLANNER agent asks clarifying questions
```python
# PLANNER can request clarification
planner_output = {
    "status": "needs_clarification",
    "questions": [
        {
            "category": "tech_stack",
            "question": "Which framework: Next.js, React+Node, or Django?",
            "options": ["next", "react_node", "django"]
        }
    ]
}

# Orchestrator pauses, asks user, feeds answers back to PLANNER
```

**Large/Complex Projects**: Use **separate planning frontend** (PRPGen approach)
- Visual wizard for comprehensive elicitation
- Spec-Kit's 9-category taxonomy
- PRP-style context engineering
- Output: Detailed specification
- Feed specification to orchestrator as enriched task description

**Benefit**: Right tool for the job - orchestrator handles tactical workflows, frontend handles strategic planning

### Q3: "How to avoid refactoring agents every time workflow needs improvement?"

**A**: **Prompt engineering + structured outputs**

**Key Architecture Decisions**:

1. **PLANNER defines scope via prompts**, not code
   - Change PLANNER's system prompt → workflows change
   - No code refactoring needed

2. **Agents receive constraints in metadata**
   - Agents check `constraints` array
   - Behavior adapts without agent code changes

3. **Structured outputs from PLANNER**
   - JSON format with schema validation
   - Easy to extend without breaking changes

**Example Evolution**:

```python
# Week 1: PLANNER outputs simple workflow
{
    "workflow": [{"agent_role": "BUILDER", "scope": "..."}]
}

# Week 4: Add cost estimates (PLANNER prompt change only)
{
    "workflow": [{"agent_role": "BUILDER", "scope": "...", "estimated_cost": 0.02}]
}

# Week 8: Add parallel execution (PLANNER prompt change only)
{
    "workflow": [
        {"agent_role": "BUILDER", "execution_group": 1},
        {"agent_role": "DOCUMENTER", "execution_group": 2},  # Can run parallel
        {"agent_role": "TESTER", "execution_group": 2, "depends_on": ["BUILDER"]}
    ]
}
```

**No agent code changes needed** - just PLANNER prompt evolution!

---

## Benefits of PLANNER Agent Approach

### 1. Aligns with Core Principles
- ✅ **Single Interface**: Orchestrator manages, PLANNER plans, agents execute
- ✅ **Focused Specialization**: PLANNER only does planning
- ✅ **CRUD Pattern**: PLANNER created → plans → deleted
- ✅ **Protected Context**: Orchestrator doesn't hold full task analysis

### 2. Solves Current Problems
- ✅ **TESTER Over-Engineering**: PLANNER scopes work appropriately
- ✅ **Inefficient Workflows**: PLANNER skips unnecessary agents
- ✅ **Context Waste**: PLANNER recommends file-based passing

### 3. Enables Future Capabilities
- ✅ **Parallel Execution**: PLANNER identifies opportunities
- ✅ **Cost Prediction**: PLANNER estimates before execution
- ✅ **Learning**: Feed actual metrics back to PLANNER
- ✅ **Human-in-Loop**: PLANNER can ask clarifying questions

### 4. Easy to Refine
- ✅ **Prompt Engineering**: Refine PLANNER via system prompt
- ✅ **No Code Changes**: Workflow evolution via prompt tuning
- ✅ **Dashboard Validation**: See PLANNER's decisions in real-time

---

## Comparison: Template vs Agent-Based Planning

| Dimension | Template (Current) | PLANNER Agent (Proposed) |
|-----------|-------------------|-------------------------|
| **Flexibility** | Low - hardcoded | High - LLM reasoning |
| **Adaptability** | Manual code changes | Prompt refinement |
| **Context Awareness** | None | Full task analysis |
| **Scope Control** | Generic prompts | Specific constraints |
| **Cost Prediction** | Not possible | Estimated per agent |
| **Skip Logic** | Keyword-based | Intelligent analysis |
| **Parallel Detection** | Hardcoded | Dynamic |
| **Learning** | Static | Can improve via feedback |
| **Maintenance** | High - code for each variation | Low - prompt engineering |

---

## Recommended Next Steps

### Immediate (This Week):
1. ✅ Document this architecture (this file)
2. ⏳ Create PLANNER agent system prompt
3. ⏳ Prototype PLANNER integration in TaskPlanner
4. ⏳ Test with dashboard on simple task

### Short Term (Next 2 Weeks):
5. Implement scoped TESTER execution
6. Add constraint system to agent prompts
7. Measure token reduction vs current approach
8. Refine PLANNER prompt based on results

### Medium Term (Next Month):
9. Add parallel execution support
10. Implement file-based context passing
11. Build cost prediction system
12. Create learning feedback loop

### Long Term (Phase 4):
13. Design planning frontend for greenfield projects
14. Integrate Spec-Kit question taxonomy
15. Build PRP-style context engineering
16. Create starter template recommendation system

---

## Conclusion

**The PLANNER agent approach is the optimal path forward because:**

1. ✅ **Architecturally Sound**: Aligns with Multi-Agent Orchestration core principles
2. ✅ **Solves Current Problems**: Addresses TESTER over-engineering, inefficient workflows
3. ✅ **Scales to Complexity**: Works for simple tasks now, greenfield projects later
4. ✅ **Low Maintenance**: Prompt engineering vs code refactoring
5. ✅ **Observable**: Dashboard shows PLANNER's decisions
6. ✅ **Learnable**: Can improve via feedback loops

**Don't**: Try to make the orchestrator smarter with complex template logic

**Do**: Create a specialized PLANNER agent that thinks about workflows so the orchestrator can focus on execution

This is exactly the pattern recommended in Multi-Agent Orchestration:
> "Each agent has a dedicated, specific focus. The orchestrator delegates work rather than doing it all itself."

---

**Status**: ✅ Architecture documented, ready for implementation
**Next**: Create PLANNER agent system prompt and prototype integration
