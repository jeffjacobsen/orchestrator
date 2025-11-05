# Agent Workflow Order

## Proper Agent Sequence

The orchestrator follows a specific order when spawning specialized agents to ensure proper research, planning, implementation, testing, and review:

```
1. ANALYST  → Research & Analysis
2. PLANNER  → Task Planning & Decomposition
3. BUILDER  → Implementation
4. TESTER   → Testing & Validation
5. REVIEWER → Quality Review
```

## Why This Order?

### 1. ANALYST (First)
**Purpose:** Research requirements and analyze existing codebase

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

### 2. PLANNER (Second)
**Purpose:** Create implementation plans and tasks

**Responsibilities:**
- Break down complex tasks into manageable subtasks
- Create clear execution plans with dependencies
- Estimate effort and identify potential challenges
- Coordinate between different agent roles
- Base plans on Analyst's research

**Example Tasks:**
- "Create implementation plan based on analysis"
- "Create a fix plan based on root cause analysis"
- "Create review plan with checklist and priorities"
- "Create documentation plan with structure and coverage"

### 3. BUILDER (Third)
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

### 4. TESTER (Fourth)
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

### 5. REVIEWER (Fifth/Final)
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

### Feature Implementation
```python
[
    ANALYST  → "Research requirements and analyze existing codebase",
    PLANNER  → "Create implementation plan based on analysis",
    BUILDER  → "Implement the feature following the plan",
    TESTER   → "Write and run tests for the new feature",
    REVIEWER → "Review that implementation follows the plan and meets quality standards",
]
```

### Bug Fix
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

### 1. Research Before Planning
The Analyst must gather all necessary information before the Planner can create an effective plan. Planning without research leads to incomplete or incorrect plans.

### 2. Plan Before Building
The Builder needs a clear plan from the Planner to implement correctly. Building without a plan leads to code that may not meet requirements or follow best practices.

### 3. Build Before Testing
The Tester needs implemented code to test. Testing validates that the Builder followed the plan correctly.

### 4. Review After Implementation
The Reviewer verifies that the entire workflow followed the plan and meets quality standards. This is the final quality gate.

### 5. Sequential Execution
Each agent builds on the work of the previous agent. This creates a clear chain of responsibility and ensures quality at each step.

## Default Behavior

When no specific roles are detected in a prompt, the orchestrator defaults to:
```python
[AgentRole.ANALYST, AgentRole.PLANNER, AgentRole.BUILDER]
```

This ensures that even simple tasks benefit from proper research and planning.

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
2. **Efficiency**: Less rework because plans are based on proper research
3. **Traceability**: Clear chain from requirements → plan → implementation → tests → review
4. **Accountability**: Each agent has a specific role and responsibility
5. **Consistency**: Standard workflow across all task types
6. **Best Practices**: Ensures research and planning before implementation

## Anti-Patterns to Avoid

❌ **Building before planning**
- Results in code that doesn't meet requirements
- Leads to extensive rework

❌ **Planning before research**
- Creates incomplete or incorrect plans
- Wastes time on invalid approaches

❌ **Reviewing before testing**
- Misses functional issues that tests would catch
- Inefficient use of reviewer time

❌ **Skipping the Analyst**
- Plans are based on assumptions rather than facts
- Higher likelihood of implementing the wrong solution

## Summary

The proper agent order ensures:
1. Work is researched before planning
2. Plans are created before implementation
3. Code is implemented before testing
4. Everything is tested before review
5. Review validates the entire chain

This creates a robust, efficient workflow where each agent's output is validated by the next agent in the sequence.
