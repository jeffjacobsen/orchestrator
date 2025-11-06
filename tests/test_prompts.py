"""
Tests for agent role system prompts.

This test suite validates that system prompts are properly configured
for each agent role and include appropriate guidance.
"""

import pytest
from orchestrator.core.prompts import (
    ROLE_PROMPTS,
    get_role_prompt,
    get_analyst_prompt_with_context,
    get_custom_prompt,
    get_complexity_aware_analyst_prompt,
)
from orchestrator.core.types import AgentRole


class TestRolePrompts:
    """Test base role prompts."""

    def test_all_roles_have_prompts(self):
        """All agent roles should have defined system prompts."""
        for role in AgentRole:
            assert role in ROLE_PROMPTS, f"Missing prompt for role: {role.value}"

    def test_analyst_prompt_includes_efficiency_guidance(self):
        """ANALYST prompt should include efficiency guidelines."""
        prompt = ROLE_PROMPTS[AgentRole.ANALYST]

        # Check for efficiency keywords
        assert "efficiency" in prompt.lower() or "focused" in prompt.lower()
        assert "targeted" in prompt.lower() or "concise" in prompt.lower()

        # Check for anti-over-analysis guidance
        assert "avoid" in prompt.lower() or "don't" in prompt.lower()

    def test_analyst_prompt_discourages_over_analysis(self):
        """ANALYST prompt should discourage exhaustive research."""
        prompt = ROLE_PROMPTS[AgentRole.ANALYST]

        # Should mention not doing too much
        prompt_lower = prompt.lower()
        assert any(keyword in prompt_lower for keyword in [
            "over-analysis", "exhaustive", "phd thesis", "just enough"
        ])

    def test_planner_prompt_includes_responsibilities(self):
        """PLANNER prompt should include core responsibilities."""
        prompt = ROLE_PROMPTS[AgentRole.PLANNER]

        assert "decomposition" in prompt.lower() or "break down" in prompt.lower()
        assert "plan" in prompt.lower()
        assert "subtask" in prompt.lower() or "task" in prompt.lower()

    def test_builder_prompt_includes_implementation_guidance(self):
        """BUILDER prompt should include implementation guidance."""
        prompt = ROLE_PROMPTS[AgentRole.BUILDER]

        assert "implement" in prompt.lower() or "code" in prompt.lower()
        assert "clean" in prompt.lower() or "quality" in prompt.lower()
        assert "pattern" in prompt.lower() or "convention" in prompt.lower()

    def test_tester_prompt_includes_testing_guidance(self):
        """TESTER prompt should include testing guidance."""
        prompt = ROLE_PROMPTS[AgentRole.TESTER]

        assert "test" in prompt.lower()
        assert "edge case" in prompt.lower() or "failure" in prompt.lower()
        assert "coverage" in prompt.lower()

    def test_reviewer_prompt_includes_review_guidance(self):
        """REVIEWER prompt should include review guidance."""
        prompt = ROLE_PROMPTS[AgentRole.REVIEWER]

        assert "review" in prompt.lower()
        assert "security" in prompt.lower() or "quality" in prompt.lower()
        assert "feedback" in prompt.lower()

    def test_prompts_are_not_empty(self):
        """All prompts should have substantial content."""
        for role, prompt in ROLE_PROMPTS.items():
            assert len(prompt) > 50, f"Prompt for {role.value} is too short"
            assert prompt.strip() != "", f"Prompt for {role.value} is empty"


class TestGetRolePrompt:
    """Test get_role_prompt function."""

    def test_get_analyst_prompt(self):
        """Getting ANALYST prompt should return correct prompt."""
        prompt = get_role_prompt(AgentRole.ANALYST)
        assert prompt == ROLE_PROMPTS[AgentRole.ANALYST]
        assert "ANALYST" in prompt

    def test_get_planner_prompt(self):
        """Getting PLANNER prompt should return correct prompt."""
        prompt = get_role_prompt(AgentRole.PLANNER)
        assert prompt == ROLE_PROMPTS[AgentRole.PLANNER]
        assert "PLANNER" in prompt

    def test_get_builder_prompt(self):
        """Getting BUILDER prompt should return correct prompt."""
        prompt = get_role_prompt(AgentRole.BUILDER)
        assert prompt == ROLE_PROMPTS[AgentRole.BUILDER]
        assert "BUILDER" in prompt

    def test_get_custom_prompt_fallback(self):
        """Unknown roles should fallback to CUSTOM prompt."""
        # Even though all roles are defined, test the fallback logic
        prompt = get_role_prompt(AgentRole.CUSTOM)
        assert prompt == ROLE_PROMPTS[AgentRole.CUSTOM]


class TestAnalystPromptWithContext:
    """Test task-specific ANALYST prompt generation."""

    def test_refactoring_task_gets_architecture_focus(self):
        """Refactoring tasks should get architecture-focused prompt."""
        prompt = get_analyst_prompt_with_context("Refactor authentication system")

        assert "refactoring" in prompt.lower()
        assert "architecture" in prompt.lower()
        assert "current" in prompt.lower() or "existing" in prompt.lower()

    def test_investigation_task_gets_root_cause_focus(self):
        """Investigation tasks should get root cause analysis focus."""
        prompt = get_analyst_prompt_with_context("Investigate memory leak issue")

        assert "investigation" in prompt.lower() or "root cause" in prompt.lower()
        assert "issue" in prompt.lower() or "reproduc" in prompt.lower()

    def test_feature_task_gets_requirements_focus(self):
        """Feature tasks should get requirements focus."""
        prompt = get_analyst_prompt_with_context("Implement user authentication feature")

        assert "feature" in prompt.lower()
        assert "requirement" in prompt.lower()
        assert "integration" in prompt.lower()

    def test_simple_task_gets_brief_reminder(self):
        """Simple tasks should get a reminder to be brief."""
        prompt = get_analyst_prompt_with_context("Quick fix for typo")

        assert "simple" in prompt.lower() or "brief" in prompt.lower()
        assert "quick" in prompt.lower() or "fast" in prompt.lower()

    def test_base_prompt_always_included(self):
        """All task-specific prompts should include base ANALYST prompt."""
        descriptions = [
            "Refactor system",
            "Investigate bug",
            "Implement feature",
            "Quick fix",
            "Generic task"
        ]

        base_prompt = ROLE_PROMPTS[AgentRole.ANALYST]

        for desc in descriptions:
            prompt = get_analyst_prompt_with_context(desc)
            assert base_prompt in prompt, f"Base prompt missing for: {desc}"


class TestCustomPrompt:
    """Test custom prompt generation."""

    def test_custom_prompt_includes_base(self):
        """Custom prompts should include base role prompt."""
        custom = "Focus on performance issues"
        prompt = get_custom_prompt(AgentRole.REVIEWER, custom)

        assert ROLE_PROMPTS[AgentRole.REVIEWER] in prompt
        assert custom in prompt

    def test_custom_prompt_formats_correctly(self):
        """Custom prompts should be properly formatted."""
        custom = "Check for SQL injection"
        prompt = get_custom_prompt(AgentRole.REVIEWER, custom)

        assert "Additional Instructions" in prompt
        assert custom in prompt

    def test_custom_prompt_with_multiple_roles(self):
        """Custom prompts work with different roles."""
        custom = "Be extra thorough"

        for role in [AgentRole.ANALYST, AgentRole.BUILDER, AgentRole.TESTER]:
            prompt = get_custom_prompt(role, custom)
            assert custom in prompt
            assert ROLE_PROMPTS[role] in prompt


class TestComplexityAwarePrompt:
    """Test complexity-aware ANALYST prompts."""

    def test_simple_complexity_emphasizes_speed(self):
        """Simple complexity should emphasize speed."""
        prompt = get_complexity_aware_analyst_prompt("simple")

        prompt_lower = prompt.lower()
        assert "quick" in prompt_lower or "fast" in prompt_lower
        assert "simple" in prompt_lower or "straightforward" in prompt_lower
        assert "speed" in prompt_lower or "brief" in prompt_lower

    def test_simple_complexity_sets_time_limit(self):
        """Simple complexity should suggest time limits."""
        prompt = get_complexity_aware_analyst_prompt("simple")

        # Should mention time or word limits
        prompt_lower = prompt.lower()
        assert "minute" in prompt_lower or "word" in prompt_lower

    def test_complex_complexity_allows_thorough_analysis(self):
        """Complex complexity should allow thorough analysis."""
        prompt = get_complexity_aware_analyst_prompt("complex")

        prompt_lower = prompt.lower()
        assert "thorough" in prompt_lower or "detailed" in prompt_lower
        assert "complex" in prompt_lower
        assert "deep" in prompt_lower or "investigate" in prompt_lower

    def test_both_complexities_include_base_prompt(self):
        """Both complexity variants should include base ANALYST prompt."""
        base_prompt = ROLE_PROMPTS[AgentRole.ANALYST]

        simple_prompt = get_complexity_aware_analyst_prompt("simple")
        complex_prompt = get_complexity_aware_analyst_prompt("complex")

        assert base_prompt in simple_prompt
        assert base_prompt in complex_prompt

    def test_prompts_differ_by_complexity(self):
        """Simple and complex prompts should be different."""
        simple_prompt = get_complexity_aware_analyst_prompt("simple")
        complex_prompt = get_complexity_aware_analyst_prompt("complex")

        # They should be different (more than just the base prompt)
        assert simple_prompt != complex_prompt
        assert len(simple_prompt) != len(complex_prompt)


class TestPromptQuality:
    """Test overall prompt quality and consistency."""

    def test_prompts_use_active_voice(self):
        """Prompts should use active, direct language."""
        for role, prompt in ROLE_PROMPTS.items():
            # Should have action verbs
            assert any(verb in prompt.lower() for verb in [
                "focus", "provide", "ensure", "create", "write", "review", "analyze"
            ]), f"Prompt for {role.value} lacks active verbs"

    def test_prompts_are_specific(self):
        """Prompts should be specific, not generic."""
        for role, prompt in ROLE_PROMPTS.items():
            # Should mention specific responsibilities
            assert "responsibilit" in prompt.lower(), \
                f"Prompt for {role.value} doesn't mention responsibilities"

    def test_prompts_avoid_jargon(self):
        """Prompts should be clear and avoid unnecessary jargon."""
        for role, prompt in ROLE_PROMPTS.items():
            # Should be readable (more periods than semicolons)
            assert prompt.count('.') > prompt.count(';'), \
                f"Prompt for {role.value} may have complex sentence structure"

    def test_analyst_prompt_has_clear_sections(self):
        """ANALYST prompt should have clear sections."""
        prompt = ROLE_PROMPTS[AgentRole.ANALYST]

        # Should have sections separated by newlines or headers
        assert "\n" in prompt, "ANALYST prompt should have multiple paragraphs"

        # Should have the key sections
        assert "responsibilities" in prompt.lower() or "responsibility" in prompt.lower()
        assert "important" in prompt.lower() or "guidelines" in prompt.lower()


class TestPromptIntegration:
    """Test integration between different prompt functions."""

    def test_workflow_simple_to_complex(self):
        """Test a complete workflow from simple to complex."""
        # Start with simple task
        simple_desc = "Fix typo in README"
        simple_prompt = get_analyst_prompt_with_context(simple_desc)
        assert "simple" in simple_prompt.lower() or "quick" in simple_prompt.lower()

        # Complex task
        complex_desc = "Refactor entire authentication system"
        complex_prompt = get_analyst_prompt_with_context(complex_desc)
        assert "refactor" in complex_prompt.lower()

        # Prompts should be different
        assert simple_prompt != complex_prompt

    def test_combining_complexity_and_custom(self):
        """Test combining complexity-aware and custom prompts."""
        base_prompt = get_complexity_aware_analyst_prompt("complex")
        custom_prompt = get_custom_prompt(
            AgentRole.ANALYST,
            "Focus on security implications"
        )

        # Both should include the base ANALYST prompt
        analyst_base = ROLE_PROMPTS[AgentRole.ANALYST]
        assert analyst_base in base_prompt
        assert analyst_base in custom_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
