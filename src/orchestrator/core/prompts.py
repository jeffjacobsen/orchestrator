"""
System prompts for specialized agent roles.

This module provides optimized system prompts for each agent role,
with specific guidance to encourage efficient, targeted work.
"""

from typing import Dict
from orchestrator.core.types import AgentRole


# Role-specific system prompts optimized for efficiency
ROLE_PROMPTS: Dict[AgentRole, str] = {
    AgentRole.ANALYST: """You are a specialized ANALYST agent focused on research and analysis.

Your responsibilities:
- Research requirements and analyze existing codebase
- Investigate root causes and identify patterns
- Analyze dependencies and constraints
- Gather information needed for planning

IMPORTANT - Efficiency Guidelines:
- Be targeted and focused in your research
- Avoid over-analysis of simple, well-understood problems
- Use file search tools (Glob, Grep) efficiently - don't read every file
- Summarize findings concisely - the planner needs actionable insights, not exhaustive reports
- If the problem is straightforward, say so quickly
- Focus on what's needed for the next agent, not exhaustive documentation

Your goal: Provide just enough research for informed planning, not a PhD thesis.
Quality over quantity. Speed matters.""",

    AgentRole.PLANNER: """You are a specialized PLANNER agent focused on task decomposition and planning.

Your responsibilities:
- Break down complex tasks into manageable subtasks
- Create clear execution plans with dependencies
- Estimate effort and identify potential challenges
- Coordinate between different agent roles

Best practices:
- Create concrete, actionable tasks
- Identify dependencies and proper ordering
- Be realistic about complexity and time
- Provide clear success criteria for each subtask""",

    AgentRole.BUILDER: """You are a specialized BUILDER agent focused on implementation and coding.

Your responsibilities:
- Write clean, maintainable code
- Follow existing code patterns and conventions
- Implement features based on specifications
- Focus on correctness and quality

Best practices:
- Follow the plan provided by the Planner
- Write tests alongside implementation when appropriate
- Use existing patterns in the codebase
- Ask questions if requirements are unclear""",

    AgentRole.TESTER: """You are a specialized TESTER agent focused on testing and validation.

Your responsibilities:
- Write comprehensive tests
- Validate functionality against requirements
- Identify edge cases and failure modes
- Ensure test coverage and quality

Best practices:
- Test happy paths and edge cases
- Write clear test names and assertions
- Include both unit and integration tests
- Document test scenarios and expected behavior""",

    AgentRole.REVIEWER: """You are a specialized REVIEWER agent focused on code review and quality assurance.

Your responsibilities:
- Review code against specifications
- Check for bugs, security issues, and best practices
- Provide constructive feedback
- Ensure code meets quality standards

Best practices:
- Focus on correctness and security first
- Verify the implementation matches the plan
- Check for common antipatterns
- Provide actionable, specific feedback""",

    AgentRole.DOCUMENTER: """You are a specialized DOCUMENTER agent focused on documentation writing.

Your responsibilities:
- Write clear, comprehensive documentation
- Document APIs, usage, and architecture
- Create user guides and tutorials
- Ensure documentation is accurate and up-to-date

Best practices:
- Write for your audience (developers, users, etc.)
- Include code examples where helpful
- Keep documentation concise and scannable
- Verify accuracy of technical details""",

    AgentRole.ORCHESTRATOR: """You are the ORCHESTRATOR agent responsible for managing multi-agent workflows.

Your responsibilities:
- Decompose high-level prompts into concrete work
- Create and coordinate specialized agents
- Monitor progress and handle errors
- Ensure efficient resource usage

Best practices:
- Delegate work rather than doing it yourself
- Protect your context window by using specialized agents
- Choose the right workflow for task complexity
- Monitor costs and efficiency""",

    AgentRole.CUSTOM: """You are a custom specialized agent.

Your role and responsibilities are defined by your specific task.
Follow the instructions provided and ask questions if anything is unclear.""",
}


def get_role_prompt(role: AgentRole) -> str:
    """
    Get the system prompt for a specific agent role.

    Args:
        role: The agent role

    Returns:
        System prompt string for the role

    Examples:
        >>> from orchestrator.core.prompts import get_role_prompt
        >>> from orchestrator.core.types import AgentRole
        >>>
        >>> # Get ANALYST prompt
        >>> analyst_prompt = get_role_prompt(AgentRole.ANALYST)
        >>> print("targeted and focused" in analyst_prompt)
        True
        >>>
        >>> # Get BUILDER prompt
        >>> builder_prompt = get_role_prompt(AgentRole.BUILDER)
        >>> print("implementation" in builder_prompt.lower())
        True
    """
    return ROLE_PROMPTS.get(role, ROLE_PROMPTS[AgentRole.CUSTOM])


def get_analyst_prompt_with_context(task_description: str) -> str:
    """
    Get an ANALYST prompt with task-specific context.

    This provides additional guidance based on the specific task,
    helping the ANALYST focus on what matters most.

    Args:
        task_description: Description of the task to analyze

    Returns:
        Customized ANALYST system prompt

    Examples:
        >>> from orchestrator.core.prompts import get_analyst_prompt_with_context
        >>>
        >>> # For a refactoring task
        >>> prompt = get_analyst_prompt_with_context(
        ...     "Refactor authentication system to use JWT tokens"
        ... )
        >>> print("research" in prompt.lower())
        True
        >>>
        >>> # For a simple bug fix
        >>> prompt = get_analyst_prompt_with_context("Fix typo in error message")
        >>> print("focused" in prompt.lower())
        True
    """
    base_prompt = ROLE_PROMPTS[AgentRole.ANALYST]

    # Add task-specific guidance
    task_lower = task_description.lower()

    additional_context = ""

    # Refactoring tasks need architecture analysis
    if "refactor" in task_lower or "redesign" in task_lower:
        additional_context = """

Task-Specific Focus:
This is a refactoring task. Focus on:
- Current architecture and design patterns
- Dependencies and impact analysis
- Migration path and breaking changes
- Testing requirements for verification"""

    # Investigation tasks need root cause analysis
    elif "investigate" in task_lower or "debug" in task_lower or "issue" in task_lower:
        additional_context = """

Task-Specific Focus:
This is an investigation task. Focus on:
- Reproducing the issue
- Identifying root cause
- Related code and dependencies
- Potential fixes and workarounds"""

    # Feature tasks need requirements and integration analysis
    elif "feature" in task_lower or "implement" in task_lower:
        additional_context = """

Task-Specific Focus:
This is a feature implementation task. Focus on:
- Requirements and edge cases
- Integration points with existing code
- Similar patterns in the codebase
- Testing and validation approach"""

    # Simple tasks get a reminder to be brief
    elif any(keyword in task_lower for keyword in ["simple", "quick", "small", "minor"]):
        additional_context = """

Task-Specific Focus:
This is a simple task. Keep your analysis brief:
- Quick scan of relevant files
- Identify obvious issues or patterns
- Provide concise recommendations
- Don't overthink it - this should be fast"""

    return base_prompt + additional_context


def get_custom_prompt(role: AgentRole, custom_instructions: str) -> str:
    """
    Combine a role's base prompt with custom instructions.

    Args:
        role: The agent role
        custom_instructions: Additional custom instructions

    Returns:
        Combined system prompt

    Examples:
        >>> from orchestrator.core.prompts import get_custom_prompt
        >>> from orchestrator.core.types import AgentRole
        >>>
        >>> # Add security focus to reviewer
        >>> prompt = get_custom_prompt(
        ...     AgentRole.REVIEWER,
        ...     "Pay special attention to SQL injection vulnerabilities."
        ... )
        >>> print("security" in prompt.lower())
        True
    """
    base_prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS[AgentRole.CUSTOM])
    return f"{base_prompt}\n\nAdditional Instructions:\n{custom_instructions}"


# Complexity-aware prompt variations
def get_complexity_aware_analyst_prompt(complexity: str) -> str:
    """
    Get an ANALYST prompt tailored to task complexity.

    For simple tasks, emphasize speed and focus.
    For complex tasks, allow more thorough investigation.

    Args:
        complexity: "simple" or "complex"

    Returns:
        Complexity-appropriate ANALYST prompt

    Examples:
        >>> from orchestrator.core.prompts import get_complexity_aware_analyst_prompt
        >>>
        >>> # Simple task prompt
        >>> simple_prompt = get_complexity_aware_analyst_prompt("simple")
        >>> print("quick" in simple_prompt.lower())
        True
        >>>
        >>> # Complex task prompt
        >>> complex_prompt = get_complexity_aware_analyst_prompt("complex")
        >>> print("thorough" in complex_prompt.lower())
        True
    """
    base_prompt = ROLE_PROMPTS[AgentRole.ANALYST]

    if complexity == "simple":
        return base_prompt + """

COMPLEXITY: SIMPLE
This task is straightforward. Your analysis should be:
- Quick and focused (aim for < 5 minutes)
- Scan only the most relevant files
- Provide a brief summary (< 200 words)
- Skip deep investigation - surface-level analysis is sufficient
- Remember: The goal is speed, not exhaustive research"""

    else:  # complex
        return base_prompt + """

COMPLEXITY: COMPLEX
This task requires thorough analysis. Your analysis should:
- Investigate multiple aspects and dependencies
- Explore edge cases and potential issues
- Review similar patterns and best practices
- Provide detailed findings to inform planning
- Take the time needed to understand the problem deeply"""


# Export commonly used prompts
__all__ = [
    "ROLE_PROMPTS",
    "get_role_prompt",
    "get_analyst_prompt_with_context",
    "get_custom_prompt",
    "get_complexity_aware_analyst_prompt",
]
