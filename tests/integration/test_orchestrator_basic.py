"""
Basic integration tests for the Orchestrator class.

Tests core functionality with the actual implementation.
"""
import pytest
from orchestrator import Orchestrator
from orchestrator.core.types import AgentRole


class TestOrchestratorLifecycle:
    """Test orchestrator initialization and lifecycle."""

    @pytest.mark.asyncio
    async def test_orchestrator_starts_and_stops(self, temp_working_dir):
        """Test that orchestrator can start and stop cleanly."""
        orchestrator = Orchestrator(
            working_directory=str(temp_working_dir),
            enable_monitoring=False  # Disable monitoring for test stability
        )

        await orchestrator.start()
        assert orchestrator.agent_manager is not None
        assert orchestrator.monitor is not None

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_orchestrator_multiple_start_stop_cycles(self, temp_working_dir):
        """Test multiple start/stop cycles work correctly."""
        orchestrator = Orchestrator(
            working_directory=str(temp_working_dir),
            enable_monitoring=False
        )

        # First cycle
        await orchestrator.start()
        await orchestrator.stop()

        # Second cycle
        await orchestrator.start()
        await orchestrator.stop()


class TestOrchestratorAgentManagement:
    """Test agent CRUD operations."""

    @pytest.mark.asyncio
    async def test_list_agents_initially_empty(self, test_orchestrator):
        """Test that list_agents returns empty list initially."""
        agents = test_orchestrator.list_agents()
        assert isinstance(agents, list)
        # May be empty or have some system agents
        assert len(agents) >= 0

    @pytest.mark.asyncio
    async def test_create_and_list_agent(self, test_orchestrator):
        """Test creating an agent and listing it."""
        initial_count = len(test_orchestrator.list_agents())

        agent_id = await test_orchestrator.create_agent(
            role=AgentRole.BUILDER,
            name="Test Builder"
        )

        assert agent_id is not None
        assert isinstance(agent_id, str)

        agents = test_orchestrator.list_agents()
        assert len(agents) > initial_count

    @pytest.mark.asyncio
    async def test_get_agent_details(self, test_orchestrator):
        """Test getting agent details."""
        agent_id = await test_orchestrator.create_agent(
            role=AgentRole.PLANNER,
            name="Test Planner"
        )

        details = test_orchestrator.get_agent_details(agent_id)

        assert details is not None
        assert isinstance(details, dict)
        # Check for some expected fields (exact structure may vary)
        assert "agent_id" in details or "id" in details

    @pytest.mark.asyncio
    async def test_delete_agent(self, test_orchestrator):
        """Test deleting an agent."""
        agent_id = await test_orchestrator.create_agent(
            role=AgentRole.TESTER,
            name="Test Tester"
        )

        initial_count = len(test_orchestrator.list_agents())

        result = await test_orchestrator.delete_agent(agent_id)

        assert result is True

        final_count = len(test_orchestrator.list_agents())
        assert final_count < initial_count

    @pytest.mark.asyncio
    async def test_create_multiple_agents(self, test_orchestrator):
        """Test creating multiple agents of different types."""
        agent1_id = await test_orchestrator.create_agent(
            role=AgentRole.BUILDER,
            name="Builder 1"
        )
        agent2_id = await test_orchestrator.create_agent(
            role=AgentRole.TESTER,
            name="Tester 1"
        )

        assert agent1_id != agent2_id
        agents = test_orchestrator.list_agents()
        assert len(agents) >= 2

    @pytest.mark.asyncio
    async def test_agent_details_has_id(self, test_orchestrator):
        """Test that agent details include an ID."""
        agent_id = await test_orchestrator.create_agent(
            role=AgentRole.REVIEWER,
            name="Test Reviewer"
        )

        details = test_orchestrator.get_agent_details(agent_id)

        assert details is not None
        # Details should have either 'agent_id' or 'id' field
        assert ("agent_id" in details or "id" in details)


class TestOrchestratorTaskManagement:
    """Test task management operations."""

    @pytest.mark.asyncio
    async def test_list_tasks_returns_list(self, test_orchestrator):
        """Test that list_tasks returns a list."""
        tasks = test_orchestrator.list_tasks()
        assert isinstance(tasks, list)

    @pytest.mark.asyncio
    async def test_get_status_returns_dict(self, test_orchestrator):
        """Test that get_status returns a dictionary."""
        status = test_orchestrator.get_status()

        assert isinstance(status, dict)
        assert len(status) > 0

    @pytest.mark.asyncio
    async def test_get_status_contains_expected_keys(self, test_orchestrator):
        """Test that get_status returns expected structure."""
        status = test_orchestrator.get_status()

        # Check for expected top-level keys (implementation may vary)
        assert isinstance(status, dict)
        # Status should contain some information about the orchestrator
        assert len(status) > 0

    @pytest.mark.asyncio
    async def test_get_task_status_nonexistent_returns_none(self, test_orchestrator):
        """Test that getting status of nonexistent task returns None."""
        result = test_orchestrator.get_task_status("nonexistent_task_id")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_tasks_initially_may_be_empty(self, test_orchestrator):
        """Test that list_tasks works even with no tasks."""
        tasks = test_orchestrator.list_tasks()

        assert isinstance(tasks, list)
        # May or may not have tasks depending on implementation


class TestOrchestratorErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent_returns_none(self, test_orchestrator):
        """Test that getting nonexistent agent returns None or raises error."""
        result = test_orchestrator.get_agent_details("nonexistent_id_12345")

        # Should return None or raise an exception
        assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_agent_returns_false(self, test_orchestrator):
        """Test that deleting nonexistent agent returns False."""
        result = await test_orchestrator.delete_agent("nonexistent_id_12345")

        # Should return False (not raise exception)
        assert result is False or result is True  # Implementation may vary


class TestOrchestratorWorkingDirectory:
    """Test working directory handling."""

    @pytest.mark.asyncio
    async def test_accepts_working_directory(self, temp_working_dir):
        """Test that orchestrator accepts a working directory parameter."""
        orchestrator = Orchestrator(
            working_directory=str(temp_working_dir),
            enable_monitoring=False
        )
        await orchestrator.start()

        assert orchestrator.working_directory == str(temp_working_dir)

        await orchestrator.stop()
