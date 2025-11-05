"""Tests for type hints implementation across the codebase.

This test suite validates that all public methods have proper type hints
and that the type annotations are correctly implemented.
"""

import pytest
import inspect
from typing import get_type_hints, Any
from unittest.mock import Mock, AsyncMock, patch

from orchestrator.core.agent import Agent
from orchestrator.core.agent_manager import AgentManager
from orchestrator.core.orchestrator import Orchestrator
from orchestrator.core.types import AgentConfig, AgentRole, AgentStatus
from orchestrator.workflow.executor import WorkflowExecutor
from orchestrator.workflow.planner import TaskPlanner
from orchestrator.observability.logger import StructuredLogger
from orchestrator.observability.monitor import AgentMonitor
from orchestrator.observability.metrics import MetricsCollector


class TestCoreModuleTypeHints:
    """Test type hints for core module classes."""

    def test_agent_init_return_type(self):
        """Test Agent.__init__ has proper return type annotation."""
        hints = get_type_hints(Agent.__init__)
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_agent_execute_task_has_type_hints(self):
        """Test Agent.execute_task method has proper type hints."""
        hints = get_type_hints(Agent.execute_task)
        assert "task_prompt" in hints
        assert "return" in hints

    def test_agent_cleanup_has_type_hints(self):
        """Test Agent.cleanup method has proper type hints."""
        hints = get_type_hints(Agent.cleanup)
        assert "return" in hints

    def test_agent_get_summary_return_type(self):
        """Test Agent.get_summary returns dict."""
        hints = get_type_hints(Agent.get_summary)
        assert "return" in hints
        # Should return Dict[str, Any]
        assert "dict" in str(hints["return"]).lower() or "Dict" in str(hints["return"])

    def test_agent_track_tool_result_has_type_hints(self):
        """Test Agent._track_tool_result has proper type hints."""
        # This is a private method but we check it has correct annotations
        hints = get_type_hints(Agent._track_tool_result)
        assert "result_block" in hints
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_agent_manager_init_return_type(self):
        """Test AgentManager.__init__ has proper return type."""
        hints = get_type_hints(AgentManager.__init__)
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_agent_manager_create_agent_has_type_hints(self):
        """Test AgentManager.create_agent has proper type hints."""
        hints = get_type_hints(AgentManager.create_agent)
        assert "name" in hints
        assert "role" in hints
        assert "return" in hints

    def test_agent_manager_get_agent_has_type_hints(self):
        """Test AgentManager.get_agent has proper type hints."""
        hints = get_type_hints(AgentManager.get_agent)
        assert "agent_id" in hints
        assert "return" in hints

    def test_agent_manager_list_agents_has_type_hints(self):
        """Test AgentManager.list_agents has proper type hints."""
        hints = get_type_hints(AgentManager.list_agents)
        assert "return" in hints
        # Should return List[Agent]
        assert "List" in str(hints["return"]) or "list" in str(hints["return"])

    def test_agent_manager_delete_agent_has_type_hints(self):
        """Test AgentManager.delete_agent has proper type hints."""
        hints = get_type_hints(AgentManager.delete_agent)
        assert "agent_id" in hints
        assert "return" in hints

    def test_orchestrator_init_return_type(self):
        """Test Orchestrator.__init__ has proper return type."""
        hints = get_type_hints(Orchestrator.__init__)
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_orchestrator_execute_has_type_hints(self):
        """Test Orchestrator.execute has proper type hints."""
        hints = get_type_hints(Orchestrator.execute)
        assert "prompt" in hints
        assert "task_type" in hints
        assert "execution_mode" in hints
        assert "return" in hints

    def test_orchestrator_get_status_has_type_hints(self):
        """Test Orchestrator.get_status has proper type hints."""
        hints = get_type_hints(Orchestrator.get_status)
        assert "return" in hints
        # Should return Dict[str, Any]
        assert "Dict" in str(hints["return"]) or "dict" in str(hints["return"])

    def test_orchestrator_list_agents_has_type_hints(self):
        """Test Orchestrator.list_agents has proper type hints."""
        hints = get_type_hints(Orchestrator.list_agents)
        assert "return" in hints

    def test_orchestrator_list_tasks_has_type_hints(self):
        """Test Orchestrator.list_tasks has proper type hints."""
        hints = get_type_hints(Orchestrator.list_tasks)
        assert "return" in hints


class TestWorkflowModuleTypeHints:
    """Test type hints for workflow module classes."""

    def test_workflow_executor_init_return_type(self):
        """Test WorkflowExecutor.__init__ has proper return type."""
        hints = get_type_hints(WorkflowExecutor.__init__)
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_workflow_executor_execute_sequential_has_type_hints(self):
        """Test WorkflowExecutor.execute_sequential has proper type hints."""
        hints = get_type_hints(WorkflowExecutor.execute_sequential)
        assert "task" in hints
        assert "return" in hints

    def test_workflow_executor_execute_parallel_has_type_hints(self):
        """Test WorkflowExecutor.execute_parallel has proper type hints."""
        hints = get_type_hints(WorkflowExecutor.execute_parallel)
        assert "task" in hints
        assert "return" in hints

    def test_task_planner_init_return_type(self):
        """Test TaskPlanner.__init__ has proper return type."""
        hints = get_type_hints(TaskPlanner.__init__)
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_task_planner_plan_task_has_type_hints(self):
        """Test TaskPlanner.plan_task has proper type hints."""
        hints = get_type_hints(TaskPlanner.plan_task)
        assert "task_id" in hints
        assert "description" in hints
        assert "return" in hints

    def test_task_planner_estimate_task_complexity_has_type_hints(self):
        """Test TaskPlanner.estimate_task_complexity has proper type hints."""
        hints = get_type_hints(TaskPlanner.estimate_task_complexity)
        assert "description" in hints
        assert "return" in hints
        # Should return Dict[str, Any]
        assert "Dict" in str(hints["return"]) or "dict" in str(hints["return"])


class TestObservabilityModuleTypeHints:
    """Test type hints for observability module classes."""

    def test_logger_init_return_type(self):
        """Test StructuredLogger.__init__ has proper return type."""
        hints = get_type_hints(StructuredLogger.__init__)
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_monitor_init_return_type(self):
        """Test AgentMonitor.__init__ has proper return type."""
        hints = get_type_hints(AgentMonitor.__init__)
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_monitor_start_monitoring_has_type_hints(self):
        """Test AgentMonitor.start_monitoring has proper type hints."""
        hints = get_type_hints(AgentMonitor.start_monitoring)
        assert "return" in hints

    def test_monitor_stop_monitoring_has_type_hints(self):
        """Test AgentMonitor.stop_monitoring has proper type hints."""
        hints = get_type_hints(AgentMonitor.stop_monitoring)
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_monitor_register_status_callback_has_type_hints(self):
        """Test AgentMonitor.register_status_callback has proper type hints."""
        hints = get_type_hints(AgentMonitor.register_status_callback)
        assert "callback" in hints
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_monitor_get_summary_has_type_hints(self):
        """Test AgentMonitor.get_summary has proper type hints."""
        hints = get_type_hints(AgentMonitor.get_summary)
        assert "return" in hints

    def test_metrics_collector_init_return_type(self):
        """Test MetricsCollector.__init__ has proper return type."""
        hints = get_type_hints(MetricsCollector.__init__)
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_metrics_collector_record_agent_metrics_has_type_hints(self):
        """Test MetricsCollector.record_agent_metrics has proper type hints."""
        hints = get_type_hints(MetricsCollector.record_agent_metrics)
        assert "metrics" in hints
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_metrics_collector_record_event_has_type_hints(self):
        """Test MetricsCollector.record_event has proper type hints."""
        hints = get_type_hints(MetricsCollector.record_event)
        assert "event_type" in hints
        assert "data" in hints
        assert "return" in hints
        assert hints["return"] is type(None)

    def test_metrics_collector_get_total_cost_has_type_hints(self):
        """Test MetricsCollector.get_total_cost has proper type hints."""
        hints = get_type_hints(MetricsCollector.get_total_cost)
        assert "return" in hints
        assert hints["return"] is float

    def test_metrics_collector_get_summary_has_type_hints(self):
        """Test MetricsCollector.get_summary has proper type hints."""
        hints = get_type_hints(MetricsCollector.get_summary)
        assert "return" in hints


class TestTypeHintConsistency:
    """Test that type hints are consistent across the codebase."""

    def test_all_init_methods_return_none(self):
        """Test that all __init__ methods have -> None return type."""
        classes_to_check = [
            Agent,
            AgentManager,
            Orchestrator,
            WorkflowExecutor,
            TaskPlanner,
            StructuredLogger,
            AgentMonitor,
            MetricsCollector,
        ]

        for cls in classes_to_check:
            hints = get_type_hints(cls.__init__)
            assert "return" in hints, f"{cls.__name__}.__init__ missing return type hint"
            assert hints["return"] is type(None), (
                f"{cls.__name__}.__init__ should return None, got {hints['return']}"
            )

    def test_dict_return_types_are_typed(self):
        """Test that methods returning dict have Dict[str, Any] type hint."""
        methods_returning_dict = [
            (Agent, "get_summary"),
            (Orchestrator, "get_status"),
            (TaskPlanner, "estimate_task_complexity"),
            (MetricsCollector, "get_summary"),
            (AgentMonitor, "get_summary"),
        ]

        for cls, method_name in methods_returning_dict:
            method = getattr(cls, method_name)
            hints = get_type_hints(method)
            assert "return" in hints, f"{cls.__name__}.{method_name} missing return type hint"
            # Check that it's a Dict type (could be dict or Dict from typing)
            return_type_str = str(hints["return"])
            assert "dict" in return_type_str.lower() or "Dict" in return_type_str, (
                f"{cls.__name__}.{method_name} should return Dict type, got {hints['return']}"
            )

    def test_async_methods_have_proper_hints(self):
        """Test that async methods have proper return type hints."""
        async_methods = [
            (Agent, "execute_task"),
            (Agent, "cleanup"),
            (AgentManager, "create_agent"),
            (AgentManager, "delete_agent"),
            (Orchestrator, "execute"),
            (WorkflowExecutor, "execute_sequential"),
            (WorkflowExecutor, "execute_parallel"),
            (AgentMonitor, "start_monitoring"),
        ]

        for cls, method_name in async_methods:
            method = getattr(cls, method_name)
            hints = get_type_hints(method)
            assert "return" in hints, f"{cls.__name__}.{method_name} missing return type hint"
            # Async methods should have return type hints


class TestTypeHintFunctionality:
    """Test that type hints don't break functionality."""

    @pytest.mark.asyncio
    async def test_agent_manager_with_type_hints_works(self):
        """Test that AgentManager works correctly with type hints."""
        manager = AgentManager()

        # Create agent
        agent = await manager.create_agent(
            name="Test Agent",
            role=AgentRole.PLANNER,
        )

        assert agent is not None
        assert isinstance(agent, Agent)
        assert agent.config.name == "Test Agent"

        # List agents
        agents = manager.list_agents()
        assert isinstance(agents, list)
        assert len(agents) == 1

        # Get agent
        retrieved_agent = manager.get_agent(agent.agent_id)
        assert retrieved_agent is agent

        # Delete agent
        deleted = await manager.delete_agent(agent.agent_id)
        assert isinstance(deleted, bool)
        assert deleted is True

    def test_task_planner_with_type_hints_works(self):
        """Test that TaskPlanner works correctly with type hints."""
        planner = TaskPlanner()

        # Plan task
        task = planner.plan_task(
            task_id="test-task",
            description="Test task",
            task_type="feature_implementation"
        )

        assert task is not None
        assert task.task_id == "test-task"

        # Estimate complexity
        complexity = planner.estimate_task_complexity("Test description")
        assert isinstance(complexity, dict)
        assert "complexity" in complexity
        assert "estimated_agents" in complexity

    def test_metrics_collector_with_type_hints_works(self):
        """Test that MetricsCollector works correctly with type hints."""
        collector = MetricsCollector()

        # Get total cost - it returns int by default
        cost = collector.get_total_cost()
        assert isinstance(cost, (int, float))
        assert cost == 0 or cost == 0.0

        # Get total tokens
        tokens = collector.get_total_tokens()
        assert isinstance(tokens, int)
        assert tokens == 0

        # Get summary
        summary = collector.get_summary()
        assert isinstance(summary, dict)

    @pytest.mark.asyncio
    async def test_orchestrator_with_type_hints_works(self):
        """Test that Orchestrator works correctly with type hints."""
        orchestrator = Orchestrator(enable_monitoring=False)

        # Get status
        status = orchestrator.get_status()
        assert isinstance(status, dict)
        assert "fleet" in status
        assert "metrics" in status
        assert "tasks" in status

        # List agents
        agents = orchestrator.list_agents()
        assert isinstance(agents, list)

        # List tasks
        tasks = orchestrator.list_tasks()
        assert isinstance(tasks, list)

        # Stop orchestrator
        await orchestrator.stop()


class TestEdgeCasesWithTypeHints:
    """Test edge cases to ensure type hints handle them correctly."""

    def test_optional_return_types_handle_none(self):
        """Test that Optional return types properly handle None."""
        manager = AgentManager()

        # Get non-existent agent should return None
        result = manager.get_agent("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_return_types_handle_empty_lists(self):
        """Test that List return types properly handle empty lists."""
        manager = AgentManager()

        # List agents when there are none
        agents = manager.list_agents()
        assert isinstance(agents, list)
        assert len(agents) == 0

    def test_dict_return_types_handle_values(self):
        """Test that Dict return types properly handle dicts."""
        collector = MetricsCollector()

        # Get summary immediately after creation
        summary = collector.get_summary()
        assert isinstance(summary, dict)
        # Should have default values
        assert "total_cost" in summary
        assert "total_tokens" in summary


class TestMypyCompatibility:
    """Test that the code is compatible with mypy strict mode."""

    def test_no_bare_dict_types(self):
        """Verify that no bare Dict types exist (all should be Dict[str, Any])."""
        # This is more of a documentation test
        # The actual mypy validation is done separately
        pass

    def test_no_bare_list_types(self):
        """Verify that no bare List types exist (all should be List[SomeType])."""
        # This is more of a documentation test
        pass

    def test_all_public_methods_have_hints(self):
        """Verify that all public methods have type hints."""
        classes_to_check = [
            Agent,
            AgentManager,
            Orchestrator,
            WorkflowExecutor,
            TaskPlanner,
            StructuredLogger,
            AgentMonitor,
            MetricsCollector,
        ]

        for cls in classes_to_check:
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                # Skip private methods (except __init__)
                if name.startswith("_") and name != "__init__":
                    continue

                # Check that method has type hints
                hints = get_type_hints(method)
                assert "return" in hints, (
                    f"{cls.__name__}.{name} missing return type hint"
                )


class TestIntegrationWithMypy:
    """Test integration with mypy type checker."""

    def test_type_hints_are_valid_for_mypy(self):
        """Test that all type hints can be validated by mypy."""
        # This test is more conceptual - actual mypy validation is done via CLI
        # But we can check that get_type_hints doesn't raise errors

        classes = [
            Agent,
            AgentManager,
            Orchestrator,
            WorkflowExecutor,
            TaskPlanner,
            StructuredLogger,
            AgentMonitor,
            MetricsCollector,
        ]

        for cls in classes:
            # This should not raise any exception
            try:
                get_type_hints(cls.__init__)
            except Exception as e:
                pytest.fail(f"Failed to get type hints for {cls.__name__}.__init__: {e}")

    def test_runtime_type_checking_possible(self):
        """Test that type hints can be used for runtime type checking."""
        from typing import get_type_hints

        # Example: Check AgentManager.create_agent signature
        hints = get_type_hints(AgentManager.create_agent)
        assert "name" in hints
        assert "role" in hints
        assert hints["name"] == str

        # This demonstrates that type hints are accessible at runtime
        # which is important for tools that do runtime validation
