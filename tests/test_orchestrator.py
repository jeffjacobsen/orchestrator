"""Basic tests for the orchestrator system."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from orchestrator import Orchestrator, AgentConfig, AgentRole


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator can be initialized."""
    orchestrator = Orchestrator(
        enable_monitoring=False
    )

    assert orchestrator is not None
    assert orchestrator.agent_manager is not None
    assert orchestrator.planner is not None
    assert orchestrator.executor is not None


@pytest.mark.asyncio
async def test_agent_manager_create_agent():
    """Test agent creation."""
    from orchestrator.core.agent_manager import AgentManager

    manager = AgentManager()

    agent = await manager.create_agent(
        name="Test Agent",
        role=AgentRole.PLANNER,
    )

    assert agent is not None
    assert agent.config.name == "Test Agent"
    assert agent.config.role == AgentRole.PLANNER


@pytest.mark.asyncio
async def test_agent_manager_list_agents():
    """Test listing agents."""
    from orchestrator.core.agent_manager import AgentManager

    manager = AgentManager()

    # Create some agents
    await manager.create_agent("Agent 1", role=AgentRole.PLANNER)
    await manager.create_agent("Agent 2", role=AgentRole.BUILDER)

    # List all agents
    agents = manager.list_agents()
    assert len(agents) == 2

    # Filter by role
    planners = manager.list_agents(role=AgentRole.PLANNER)
    assert len(planners) == 1
    assert planners[0].config.role == AgentRole.PLANNER


@pytest.mark.asyncio
async def test_agent_manager_delete_agent():
    """Test agent deletion."""
    from orchestrator.core.agent_manager import AgentManager

    manager = AgentManager()

    agent = await manager.create_agent("Test Agent", role=AgentRole.PLANNER)
    agent_id = agent.agent_id

    # Delete agent
    deleted = await manager.delete_agent(agent_id)
    assert deleted is True

    # Verify deletion
    agent_after = manager.get_agent(agent_id)
    assert agent_after is None


def test_task_planner_plan_task():
    """Test task planning."""
    from orchestrator.workflow.planner import TaskPlanner

    planner = TaskPlanner()

    task = planner.plan_task(
        task_id="test-task",
        description="Implement a new feature",
        task_type="feature_implementation"
    )

    assert task is not None
    assert task.task_id == "test-task"
    assert task.description == "Implement a new feature"
    assert len(task.subtasks) > 0


def test_task_planner_estimate_complexity():
    """Test complexity estimation."""
    from orchestrator.workflow.planner import TaskPlanner

    planner = TaskPlanner()

    # Simple task
    simple = planner.estimate_task_complexity("Find files")
    assert simple["complexity"] == "simple"
    assert simple["estimated_agents"] == 1

    # Complex task
    complex_desc = " ".join(["word"] * 60)
    complex_task = planner.estimate_task_complexity(complex_desc)
    assert complex_task["complexity"] == "complex"
    assert complex_task["estimated_agents"] == 3


def test_agent_config():
    """Test agent configuration."""
    config = AgentConfig(
        name="Test Agent",
        role=AgentRole.BUILDER,
        model="claude-sonnet-4-5-20250929",
        system_prompt="You are a test agent",
        max_tokens=4096,
    )

    assert config.name == "Test Agent"
    assert config.role == AgentRole.BUILDER
    assert config.model == "claude-sonnet-4-5-20250929"
    assert config.max_tokens == 4096
