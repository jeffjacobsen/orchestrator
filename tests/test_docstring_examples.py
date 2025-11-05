"""
Comprehensive tests for validating docstring examples in key orchestrator functions.

This test suite verifies that all required docstring examples have been properly
implemented following Google-style format with realistic usage patterns.
"""

import ast
import inspect
import re
import pytest
from typing import List, Dict, Any


def extract_docstring(source_code: str, function_name: str) -> str:
    """Extract docstring from a function in source code."""
    tree = ast.parse(source_code)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                docstring = ast.get_docstring(node)
                return docstring if docstring else ""

    return ""


def count_examples_in_docstring(docstring: str) -> int:
    """Count the number of examples in a docstring."""
    # Look for markdown code blocks
    code_block_pattern = r'```python\s*\n(.*?)```'
    code_blocks = re.findall(code_block_pattern, docstring, re.DOTALL)

    # Count doctest-style examples (>>> format)
    doctest_examples = len(re.findall(r'>>>', docstring))

    # Count explicit example markers like "Example 1:", "Example 2:", etc.
    example_markers = len(re.findall(r'Example \d+:', docstring))

    # Count implicit example sections (lines ending with : followed by blank line and >>>)
    implicit_examples = len(re.findall(r':\s*\n\s*\n\s*>>>', docstring))

    # Return the maximum count found
    return max(len(code_blocks), doctest_examples, example_markers, implicit_examples)


def validate_google_style_docstring(docstring: str) -> Dict[str, Any]:
    """Validate that a docstring follows Google-style format."""
    validation = {
        'has_summary': False,
        'has_args_section': False,
        'has_returns_section': False,
        'has_examples_section': False,
        'has_raises_section': False,
        'example_count': 0,
    }

    if not docstring:
        return validation

    lines = docstring.split('\n')

    # Check for summary (first non-empty line)
    for line in lines:
        if line.strip():
            validation['has_summary'] = True
            break

    # Check for sections
    validation['has_args_section'] = 'Args:' in docstring
    validation['has_returns_section'] = 'Returns:' in docstring
    validation['has_examples_section'] = 'Examples:' in docstring or 'Example:' in docstring
    validation['has_raises_section'] = 'Raises:' in docstring

    # Count examples
    validation['example_count'] = count_examples_in_docstring(docstring)

    return validation


class TestOrchestratorExecuteDocstring:
    """Test suite for Orchestrator.execute() docstring examples."""

    @pytest.fixture
    def orchestrator_source(self):
        """Load the orchestrator source code."""
        with open('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/orchestrator.py', 'r') as f:
            return f.read()

    def test_execute_has_docstring(self, orchestrator_source):
        """Test that execute() method has a docstring."""
        docstring = extract_docstring(orchestrator_source, 'execute')
        assert docstring, "execute() method should have a docstring"
        assert len(docstring) > 100, "Docstring should be comprehensive (>100 chars)"

    def test_execute_follows_google_style(self, orchestrator_source):
        """Test that execute() docstring follows Google-style format."""
        docstring = extract_docstring(orchestrator_source, 'execute')
        validation = validate_google_style_docstring(docstring)

        assert validation['has_summary'], "Docstring should have a summary"
        assert validation['has_args_section'], "Docstring should have Args section"
        assert validation['has_returns_section'], "Docstring should have Returns section"
        assert validation['has_examples_section'], "Docstring should have Examples section"

    def test_execute_has_workflow_examples(self, orchestrator_source):
        """Test that execute() has example workflow demonstrations."""
        docstring = extract_docstring(orchestrator_source, 'execute')

        # Should have multiple examples (at least 5 as per requirements)
        validation = validate_google_style_docstring(docstring)
        assert validation['example_count'] >= 5, \
            f"execute() should have at least 5 examples, found {validation['example_count']}"

    def test_execute_includes_key_example_types(self, orchestrator_source):
        """Test that execute() includes key example types."""
        docstring = extract_docstring(orchestrator_source, 'execute')

        # Check for specific example types mentioned in requirements
        assert 'feature' in docstring.lower() or 'implementation' in docstring.lower(), \
            "Should include feature implementation example"
        assert 'bug' in docstring.lower() or 'fix' in docstring.lower(), \
            "Should include bug fix workflow example"
        assert 'sequential' in docstring.lower() or 'parallel' in docstring.lower(), \
            "Should include workflow execution pattern examples"

    def test_execute_has_realistic_code_examples(self, orchestrator_source):
        """Test that execute() has realistic, runnable code examples."""
        docstring = extract_docstring(orchestrator_source, 'execute')

        # Look for both markdown code blocks and doctest-style examples
        code_blocks = re.findall(r'```python\s*\n(.*?)```', docstring, re.DOTALL)
        doctest_lines = [line for line in docstring.split('\n') if '>>>' in line]

        # Should have examples in either format
        assert len(code_blocks) >= 1 or len(doctest_lines) >= 3, \
            "Should have code examples (markdown blocks or doctest format)"

        # Check that examples include common patterns
        combined_examples = docstring.lower()
        assert 'orchestrator' in combined_examples, "Examples should use orchestrator"
        assert 'await' in combined_examples, "Examples should show async/await usage"


class TestAgentManagerCreateAgentDocstring:
    """Test suite for AgentManager.create_agent() docstring examples."""

    @pytest.fixture
    def agent_manager_source(self):
        """Load the agent manager source code."""
        with open('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/agent_manager.py', 'r') as f:
            return f.read()

    def test_create_agent_has_docstring(self, agent_manager_source):
        """Test that create_agent() method has a docstring."""
        docstring = extract_docstring(agent_manager_source, 'create_agent')
        assert docstring, "create_agent() method should have a docstring"
        assert len(docstring) > 100, "Docstring should be comprehensive (>100 chars)"

    def test_create_agent_follows_google_style(self, agent_manager_source):
        """Test that create_agent() docstring follows Google-style format."""
        docstring = extract_docstring(agent_manager_source, 'create_agent')
        validation = validate_google_style_docstring(docstring)

        assert validation['has_summary'], "Docstring should have a summary"
        assert validation['has_args_section'], "Docstring should have Args section"
        assert validation['has_returns_section'], "Docstring should have Returns section"
        assert validation['has_examples_section'], "Docstring should have Examples section"

    def test_create_agent_has_configuration_examples(self, agent_manager_source):
        """Test that create_agent() has configuration examples."""
        docstring = extract_docstring(agent_manager_source, 'create_agent')

        # Should have multiple examples (at least 5 as per requirements)
        validation = validate_google_style_docstring(docstring)
        assert validation['example_count'] >= 5, \
            f"create_agent() should have at least 5 examples, found {validation['example_count']}"

    def test_create_agent_includes_config_variations(self, agent_manager_source):
        """Test that create_agent() includes various configuration examples."""
        docstring = extract_docstring(agent_manager_source, 'create_agent')

        # Check for different configuration aspects
        assert 'model' in docstring.lower() or 'opus' in docstring.lower() or 'haiku' in docstring.lower(), \
            "Should include model configuration examples"
        assert 'role' in docstring.lower() or 'planner' in docstring.lower() or 'builder' in docstring.lower(), \
            "Should include role configuration examples"
        assert 'custom' in docstring.lower(), \
            "Should include custom configuration examples"

    def test_create_agent_has_realistic_code_examples(self, agent_manager_source):
        """Test that create_agent() has realistic code examples."""
        docstring = extract_docstring(agent_manager_source, 'create_agent')

        # Look for both markdown code blocks and doctest-style examples
        code_blocks = re.findall(r'```python\s*\n(.*?)```', docstring, re.DOTALL)
        doctest_lines = [line for line in docstring.split('\n') if '>>>' in line]

        # Should have examples in either format
        assert len(code_blocks) >= 1 or len(doctest_lines) >= 3, \
            "Should have code examples (markdown blocks or doctest format)"

        # Check that examples include configuration patterns
        combined_examples = docstring.lower()
        assert 'create_agent' in combined_examples, "Examples should use create_agent method"
        assert 'await' in combined_examples, "Examples should show async/await usage"


class TestTaskPlannerPlanTaskDocstring:
    """Test suite for TaskPlanner.plan_task() docstring examples."""

    @pytest.fixture
    def task_planner_source(self):
        """Load the task planner source code."""
        with open('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/planner.py', 'r') as f:
            return f.read()

    def test_plan_task_has_docstring(self, task_planner_source):
        """Test that plan_task() method has a docstring."""
        docstring = extract_docstring(task_planner_source, 'plan_task')
        assert docstring, "plan_task() method should have a docstring"
        assert len(docstring) > 100, "Docstring should be comprehensive (>100 chars)"

    def test_plan_task_follows_google_style(self, task_planner_source):
        """Test that plan_task() docstring follows Google-style format."""
        docstring = extract_docstring(task_planner_source, 'plan_task')
        validation = validate_google_style_docstring(docstring)

        assert validation['has_summary'], "Docstring should have a summary"
        assert validation['has_args_section'], "Docstring should have Args section"
        assert validation['has_returns_section'], "Docstring should have Returns section"
        assert validation['has_examples_section'], "Docstring should have Examples section"

    def test_plan_task_has_decomposition_examples(self, task_planner_source):
        """Test that plan_task() has task decomposition examples."""
        docstring = extract_docstring(task_planner_source, 'plan_task')

        # Should have multiple examples (at least 4 as per requirements)
        validation = validate_google_style_docstring(docstring)
        assert validation['example_count'] >= 4, \
            f"plan_task() should have at least 4 examples, found {validation['example_count']}"

    def test_plan_task_includes_task_types(self, task_planner_source):
        """Test that plan_task() includes different task type examples."""
        docstring = extract_docstring(task_planner_source, 'plan_task')

        # Check for different task types
        assert 'feature' in docstring.lower() or 'implementation' in docstring.lower(), \
            "Should include feature implementation example"
        assert 'bug' in docstring.lower() or 'fix' in docstring.lower(), \
            "Should include bug fix example"
        assert 'subtask' in docstring.lower() or 'decompos' in docstring.lower(), \
            "Should include task decomposition examples"

    def test_plan_task_has_realistic_code_examples(self, task_planner_source):
        """Test that plan_task() has realistic code examples."""
        docstring = extract_docstring(task_planner_source, 'plan_task')

        # Look for both markdown code blocks and doctest-style examples
        code_blocks = re.findall(r'```python\s*\n(.*?)```', docstring, re.DOTALL)
        doctest_lines = [line for line in docstring.split('\n') if '>>>' in line]

        # Should have examples in either format
        assert len(code_blocks) >= 1 or len(doctest_lines) >= 2, \
            "Should have code examples (markdown blocks or doctest format)"

        # Check that examples include planning patterns
        combined_examples = docstring.lower()
        assert 'plan_task' in combined_examples, "Examples should use plan_task method"


class TestWorkflowExecutorDocstrings:
    """Test suite for WorkflowExecutor methods docstring examples."""

    @pytest.fixture
    def workflow_executor_source(self):
        """Load the workflow executor source code."""
        with open('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/executor.py', 'r') as f:
            return f.read()

    def test_execute_sequential_has_docstring(self, workflow_executor_source):
        """Test that execute_sequential() method has a docstring."""
        docstring = extract_docstring(workflow_executor_source, 'execute_sequential')
        assert docstring, "execute_sequential() method should have a docstring"
        assert len(docstring) > 100, "Docstring should be comprehensive (>100 chars)"

    def test_execute_sequential_follows_google_style(self, workflow_executor_source):
        """Test that execute_sequential() docstring follows Google-style format."""
        docstring = extract_docstring(workflow_executor_source, 'execute_sequential')
        validation = validate_google_style_docstring(docstring)

        assert validation['has_summary'], "Docstring should have a summary"
        assert validation['has_args_section'], "Docstring should have Args section"
        assert validation['has_returns_section'], "Docstring should have Returns section"
        assert validation['has_examples_section'], "Docstring should have Examples section"

    def test_execute_sequential_has_examples(self, workflow_executor_source):
        """Test that execute_sequential() has sufficient examples."""
        docstring = extract_docstring(workflow_executor_source, 'execute_sequential')

        # Should have multiple examples
        validation = validate_google_style_docstring(docstring)
        assert validation['example_count'] >= 3, \
            f"execute_sequential() should have at least 3 examples, found {validation['example_count']}"

    def test_execute_sequential_shows_pipeline_pattern(self, workflow_executor_source):
        """Test that execute_sequential() shows pipeline/sequential pattern."""
        docstring = extract_docstring(workflow_executor_source, 'execute_sequential')

        assert 'sequential' in docstring.lower() or 'pipeline' in docstring.lower(), \
            "Should explain sequential execution pattern"
        assert 'order' in docstring.lower() or 'sequence' in docstring.lower(), \
            "Should mention execution order"

    def test_execute_parallel_has_docstring(self, workflow_executor_source):
        """Test that execute_parallel() method has a docstring."""
        docstring = extract_docstring(workflow_executor_source, 'execute_parallel')
        assert docstring, "execute_parallel() method should have a docstring"
        assert len(docstring) > 100, "Docstring should be comprehensive (>100 chars)"

    def test_execute_parallel_follows_google_style(self, workflow_executor_source):
        """Test that execute_parallel() docstring follows Google-style format."""
        docstring = extract_docstring(workflow_executor_source, 'execute_parallel')
        validation = validate_google_style_docstring(docstring)

        assert validation['has_summary'], "Docstring should have a summary"
        assert validation['has_args_section'], "Docstring should have Args section"
        assert validation['has_returns_section'], "Docstring should have Returns section"
        assert validation['has_examples_section'], "Docstring should have Examples section"

    def test_execute_parallel_has_examples(self, workflow_executor_source):
        """Test that execute_parallel() has sufficient examples."""
        docstring = extract_docstring(workflow_executor_source, 'execute_parallel')

        # Should have multiple examples
        validation = validate_google_style_docstring(docstring)
        assert validation['example_count'] >= 3, \
            f"execute_parallel() should have at least 3 examples, found {validation['example_count']}"

    def test_execute_parallel_shows_parallel_pattern(self, workflow_executor_source):
        """Test that execute_parallel() shows parallel execution pattern."""
        docstring = extract_docstring(workflow_executor_source, 'execute_parallel')

        assert 'parallel' in docstring.lower() or 'concurrent' in docstring.lower(), \
            "Should explain parallel execution pattern"
        assert 'independent' in docstring.lower() or 'simultaneous' in docstring.lower(), \
            "Should mention independent execution"

    def test_execute_methods_have_comparison_guidance(self, workflow_executor_source):
        """Test that executor methods provide guidance on when to use each."""
        seq_docstring = extract_docstring(workflow_executor_source, 'execute_sequential')
        par_docstring = extract_docstring(workflow_executor_source, 'execute_parallel')

        # At least one should mention when to use sequential vs parallel
        combined = seq_docstring + par_docstring
        assert 'when to use' in combined.lower() or 'use case' in combined.lower() or \
               'depends on' in combined.lower() or 'independent' in combined.lower(), \
            "Should provide guidance on when to use sequential vs parallel execution"


class TestOverallDocstringQuality:
    """Test suite for overall docstring quality across all key functions."""

    def test_all_key_functions_have_docstrings(self):
        """Test that all 4 key functions have docstrings."""
        files_and_functions = [
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/orchestrator.py', 'execute'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/agent_manager.py', 'create_agent'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/planner.py', 'plan_task'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/executor.py', 'execute_sequential'),
        ]

        for filepath, function_name in files_and_functions:
            with open(filepath, 'r') as f:
                source = f.read()

            docstring = extract_docstring(source, function_name)
            assert docstring, f"{function_name}() in {filepath} should have a docstring"

    def test_all_key_functions_follow_google_style(self):
        """Test that all key functions follow Google-style format."""
        files_and_functions = [
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/orchestrator.py', 'execute'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/agent_manager.py', 'create_agent'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/planner.py', 'plan_task'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/executor.py', 'execute_sequential'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/executor.py', 'execute_parallel'),
        ]

        for filepath, function_name in files_and_functions:
            with open(filepath, 'r') as f:
                source = f.read()

            docstring = extract_docstring(source, function_name)
            validation = validate_google_style_docstring(docstring)

            assert validation['has_summary'], f"{function_name}() should have a summary"
            assert validation['has_examples_section'], f"{function_name}() should have Examples section"

    def test_total_example_count_meets_requirements(self):
        """Test that total number of examples across all functions is substantial."""
        files_and_functions = [
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/orchestrator.py', 'execute'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/agent_manager.py', 'create_agent'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/planner.py', 'plan_task'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/executor.py', 'execute_sequential'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/executor.py', 'execute_parallel'),
        ]

        total_examples = 0
        for filepath, function_name in files_and_functions:
            with open(filepath, 'r') as f:
                source = f.read()

            docstring = extract_docstring(source, function_name)
            validation = validate_google_style_docstring(docstring)
            total_examples += validation['example_count']

        # Should have at least 20 total examples across all functions
        assert total_examples >= 20, \
            f"Should have at least 20 total examples across all key functions, found {total_examples}"

    def test_examples_are_realistic_and_complete(self):
        """Test that examples include realistic imports and usage patterns."""
        files_and_functions = [
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/orchestrator.py', 'execute'),
            ('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/agent_manager.py', 'create_agent'),
        ]

        for filepath, function_name in files_and_functions:
            with open(filepath, 'r') as f:
                source = f.read()

            docstring = extract_docstring(source, function_name)

            # Check for realistic patterns in examples
            code_blocks = re.findall(r'```python\s*\n(.*?)```', docstring, re.DOTALL)
            if code_blocks:
                combined = '\n'.join(code_blocks)

                # Should show imports or object creation
                has_realistic_setup = (
                    'import' in combined.lower() or
                    'orchestrator' in combined.lower() or
                    'manager' in combined.lower() or
                    '=' in combined  # Assignment showing object creation
                )

                assert has_realistic_setup, \
                    f"{function_name}() examples should show realistic setup and usage"


class TestDocstringExamplesAreSyntacticallyValid:
    """Test that code examples in docstrings use proper format."""

    def test_orchestrator_execute_has_doctest_examples(self):
        """Test that Orchestrator.execute() has doctest-style examples."""
        with open('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/orchestrator.py', 'r') as f:
            source = f.read()

        docstring = extract_docstring(source, 'execute')

        # Check for doctest-style examples (>>> format)
        assert '>>>' in docstring, "execute() should have doctest-style examples using >>>"

        # Check that examples show proper usage
        assert 'orchestrator = Orchestrator' in docstring or 'Orchestrator(' in docstring, \
            "Examples should show Orchestrator initialization"
        assert 'await orchestrator.execute' in docstring or 'execute(' in docstring, \
            "Examples should show execute() method usage"

    def test_agent_manager_create_agent_has_doctest_examples(self):
        """Test that AgentManager.create_agent() has doctest-style examples."""
        with open('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/core/agent_manager.py', 'r') as f:
            source = f.read()

        docstring = extract_docstring(source, 'create_agent')

        # Check for doctest-style examples
        assert '>>>' in docstring, "create_agent() should have doctest-style examples using >>>"

        # Check that examples show proper usage
        assert 'create_agent' in docstring, "Examples should show create_agent() usage"
        assert 'await' in docstring, "Examples should show async/await usage"

    def test_task_planner_has_doctest_examples(self):
        """Test that TaskPlanner.plan_task() has doctest-style examples."""
        with open('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/planner.py', 'r') as f:
            source = f.read()

        docstring = extract_docstring(source, 'plan_task')

        # Check for doctest-style examples
        assert '>>>' in docstring, "plan_task() should have doctest-style examples using >>>"

        # Check that examples show proper usage
        assert 'plan_task' in docstring, "Examples should show plan_task() usage"
        assert 'planner' in docstring.lower(), "Examples should show TaskPlanner usage"

    def test_workflow_executor_has_doctest_examples(self):
        """Test that WorkflowExecutor methods have doctest-style examples."""
        with open('/Volumes/Ext_SSD/Users/jeff/code/orchestrator/src/orchestrator/workflow/executor.py', 'r') as f:
            source = f.read()

        for method_name in ['execute_sequential', 'execute_parallel']:
            docstring = extract_docstring(source, method_name)

            # Check for doctest-style examples
            assert '>>>' in docstring, f"{method_name}() should have doctest-style examples using >>>"

            # Check that examples show proper usage
            assert method_name in docstring, f"Examples should show {method_name}() usage"
            assert 'await' in docstring, "Examples should show async/await usage"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "--tb=short"])
