# Agent Workflow Order

## Proper Agent Sequence

The orchestrator follows a specific order when spawning specialized agents to ensure proper planning, implementation, testing, and review. The ANALYST is only used when detailed research is needed:

```
1. ANALYST  → Research & Analysis (only when detailed research is needed)
2. PLANNER  → Task Planning & Decomposition
3. BUILDER  → Implementation
4. TESTER   → Testing & Validation
5. REVIEWER → Quality Review
```

## Why This Order?

### 1. ANALYST (Optional - Only When Detailed Research Is Needed)
**Purpose:** Research requirements and analyze existing codebase when detailed investigation is required

**When to Use:**
- Complex features requiring codebase analysis
- Bug investigations needing root cause analysis
- Tasks requiring research of existing patterns and solutions
- When understanding dependencies and constraints is critical

**When to Skip:**
- Simple, well-defined tasks
- Quick fixes with obvious solutions
- Tasks where the requirements are already clear

**Responsibilities:**
- Investigate and understand the problem space
- Research existing solutions and patterns
- Analyze current codebase structure
- Identify constraints and dependencies
- Gather all information needed for planning

**Example Tasks:**
- "Research requirements and analyze existing codebase"
- "Investigate and analyze the root cause of the bug"
- "Analyze code changes and identify areas to review"
- "Research and understand component behavior, APIs, and usage"

### 2. PLANNER (First or Second)
**Purpose:** Create implementation plans and tasks

**Responsibilities:**
- Break down complex tasks into manageable subtasks
- Create clear execution plans with dependencies
- Estimate effort and identify potential challenges
- Coordinate between different agent roles
- Base plans on Analyst's research (when Analyst is used)

**Example Tasks:**
- "Create implementation plan based on analysis"
- "Create a fix plan based on root cause analysis"
- "Create review plan with checklist and priorities"
- "Create documentation plan with structure and coverage"

### 3. BUILDER (Second or Third)
**Purpose:** Implement code following the plan

**Responsibilities:**
- Write clean, maintainable code
- Follow existing code patterns and conventions
- Implement features based on Planner's specifications
- Follow the plan created by Planner
- Focus on correctness and quality

**Example Tasks:**
- "Implement the feature following the plan"
- "Implement the fix following the plan"
- "Implement components based on Planner's design"

### 4. TESTER (Third or Fourth)
**Purpose:** Write and run tests

**Responsibilities:**
- Write comprehensive tests
- Validate functionality against requirements
- Identify edge cases and failure modes
- Ensure test coverage and quality
- Run tests and report results

**Example Tasks:**
- "Write and run tests for the new feature"
- "Test the fix and add regression tests"
- "Verify test coverage is adequate"

### 5. REVIEWER (Final)
**Purpose:** Verify code follows the plan and meets quality standards

**Responsibilities:**
- Review code against the Planner's specifications
- Check for bugs, security issues, and best practices
- Provide constructive feedback
- Ensure code meets quality standards
- Verify the plan was followed correctly

**Example Tasks:**
- "Review that implementation follows the plan and meets quality standards"
- "Review that the fix follows the plan and resolves the issue"
- "Review code following the plan for quality, security, and best practices"
- "Review documentation for accuracy and completeness"

## Workflow Templates

### Simple Feature Implementation (No Research Needed)
```python
[
    PLANNER  → "Create implementation plan for the feature",
    BUILDER  → "Implement the feature following the plan",
    TESTER   → "Write and run tests for the new feature",
    REVIEWER → "Review that implementation follows the plan and meets quality standards",
]
```

### Complex Feature Implementation (Research Required)
```python
[
    ANALYST  → "Research requirements and analyze existing codebase",
    PLANNER  → "Create implementation plan based on analysis",
    BUILDER  → "Implement the feature following the plan",
    TESTER   → "Write and run tests for the new feature",
    REVIEWER → "Review that implementation follows the plan and meets quality standards",
]
```

### Simple Bug Fix (Obvious Solution)
```python
[
    PLANNER  → "Create a fix plan for the bug",
    BUILDER  → "Implement the fix following the plan",
    TESTER   → "Test the fix and add regression tests",
    REVIEWER → "Review that the fix follows the plan and resolves the issue",
]
```

### Complex Bug Fix (Investigation Required)
```python
[
    ANALYST  → "Investigate and analyze the root cause of the bug",
    PLANNER  → "Create a fix plan based on root cause analysis",
    BUILDER  → "Implement the fix following the plan",
    TESTER   → "Test the fix and add regression tests",
    REVIEWER → "Review that the fix follows the plan and resolves the issue",
]
```

### Code Review
```python
[
    ANALYST  → "Analyze code changes and identify areas to review",
    PLANNER  → "Create review plan with checklist and priorities",
    REVIEWER → "Review code following the plan for quality, security, and best practices",
    TESTER   → "Verify test coverage is adequate",
]
```

### Documentation
```python
[
    ANALYST  → "Research and understand component behavior, APIs, and usage",
    PLANNER  → "Create documentation plan with structure and coverage",
    DOCUMENTER → "Write comprehensive documentation following the plan",
    REVIEWER → "Review documentation for accuracy and completeness",
]
```

## Key Principles

### 1. Use Research Only When Needed
The Analyst should only be used for complex tasks requiring detailed investigation. For simple, well-defined tasks, skip directly to planning. This saves time and reduces unnecessary context usage.

### 2. Research Before Planning (When Analyst Is Used)
When detailed research is needed, the Analyst must gather all necessary information before the Planner can create an effective plan. Planning without research leads to incomplete or incorrect plans.

### 3. Plan Before Building
The Builder needs a clear plan from the Planner to implement correctly. Building without a plan leads to code that may not meet requirements or follow best practices.

### 4. Build Before Testing
The Tester needs implemented code to test. Testing validates that the Builder followed the plan correctly.

### 5. Review After Implementation
The Reviewer verifies that the entire workflow followed the plan and meets quality standards. This is the final quality gate.

### 6. Sequential Execution
Each agent builds on the work of the previous agent. This creates a clear chain of responsibility and ensures quality at each step.

## Default Behavior

When no specific roles are detected in a prompt, the orchestrator defaults to:
```python
[AgentRole.PLANNER, AgentRole.BUILDER]
```

For simple tasks, this provides the necessary planning and implementation without unnecessary research overhead. The Analyst is only included when the task explicitly requires detailed research or investigation.

## Example Workflow

```python
# User prompt: "Add user authentication"

# 1. Analyst researches
→ Finds existing auth patterns in codebase
→ Identifies security requirements
→ Analyzes current user model structure

# 2. Planner creates plan
→ Task 1: Update user model with auth fields
→ Task 2: Implement login/logout endpoints
→ Task 3: Add JWT token generation
→ Task 4: Create auth middleware

# 3. Builder implements
→ Follows plan step by step
→ Writes code according to Planner's specifications
→ Uses patterns identified by Analyst

# 4. Tester validates
→ Tests login flow
→ Tests token validation
→ Tests edge cases (invalid credentials, expired tokens)
→ Verifies security requirements

# 5. Reviewer verifies
→ Checks implementation against plan
→ Validates security best practices
→ Confirms all tests pass
→ Approves or requests changes
```

## Benefits of This Order

1. **Quality**: Each step builds on validated work from previous steps
2. **Efficiency**: Research only when needed reduces context usage and speeds up simple tasks
3. **Flexibility**: Workflows adapt to task complexity
4. **Traceability**: Clear chain from requirements → plan → implementation → tests → review
5. **Accountability**: Each agent has a specific role and responsibility
6. **Consistency**: Standard workflow across all task types
7. **Best Practices**: Ensures proper research (when needed) and planning before implementation

## Anti-Patterns to Avoid

❌ **Building before planning**
- Results in code that doesn't meet requirements
- Leads to extensive rework

❌ **Planning before research (when research is needed)**
- Creates incomplete or incorrect plans
- Wastes time on invalid approaches

❌ **Reviewing before testing**
- Misses functional issues that tests would catch
- Inefficient use of reviewer time

❌ **Using Analyst for simple tasks**
- Wastes time and context on unnecessary research
- Reduces efficiency for straightforward implementations

❌ **Skipping Analyst for complex tasks**
- Plans are based on assumptions rather than facts
- Higher likelihood of implementing the wrong solution

## Summary

The proper agent order ensures:
1. Research is only performed when detailed investigation is needed
2. Plans are created before implementation (with or without prior research)
3. Code is implemented before testing
4. Everything is tested before review
5. Review validates the entire chain

This creates a robust, efficient workflow where:
- Simple tasks can move quickly from planning to implementation
- Complex tasks benefit from thorough research and analysis
- Each agent's output is validated by the next agent in the sequence
- Context usage is optimized by avoiding unnecessary research steps
