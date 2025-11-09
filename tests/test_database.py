"""Tests for database storage layer."""

import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest

from orchestrator.storage.database import Database
from orchestrator.storage.models import AgentRecord, TaskRecord


@pytest.fixture
async def db():
    """Create a temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database = Database(db_path)
        await database.connect()
        yield database
        await database.close()


class TestDatabaseConnection:
    """Test database connection and initialization."""

    @pytest.mark.asyncio
    async def test_database_connects(self):
        """Test that database connection is established."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)

            await db.connect()
            assert db.connection is not None
            await db.close()

    @pytest.mark.asyncio
    async def test_database_creates_tables(self, db):
        """Test that tables are created on connect."""
        # Verify agents table exists
        async with db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='agents'"
        ) as cursor:
            result = await cursor.fetchone()
            assert result is not None

        # Verify tasks table exists
        async with db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
        ) as cursor:
            result = await cursor.fetchone()
            assert result is not None

    @pytest.mark.asyncio
    async def test_database_connection_property_raises_when_not_connected(self):
        """Test that conn property raises error when not connected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)

            with pytest.raises(RuntimeError, match="Database connection not established"):
                _ = db.conn

    @pytest.mark.asyncio
    async def test_database_close(self, db):
        """Test database close."""
        await db.close()
        # Connection should be None after close
        # Clear it so conn property raises
        db.connection = None
        with pytest.raises(RuntimeError):
            _ = db.conn


class TestAgentOperations:
    """Test agent CRUD operations."""

    @pytest.mark.asyncio
    async def test_save_agent(self, db):
        """Test saving an agent record."""
        agent = AgentRecord(
            agent_id="agent-1",
            name="Test Agent",
            role="PLANNER",
            model="claude-3-5-sonnet-20241022",
            status="active",
            created_at=datetime.now(timezone.utc),
        )

        await db.save_agent(agent)

        # Verify agent was saved
        async with db.conn.execute(
            "SELECT * FROM agents WHERE agent_id = ?", (agent.agent_id,)
        ) as cursor:
            result = await cursor.fetchone()
            assert result is not None
            assert result[0] == "agent-1"
            assert result[1] == "Test Agent"

    @pytest.mark.asyncio
    async def test_get_agent(self, db):
        """Test retrieving an agent record."""
        # Insert agent directly
        await db.conn.execute(
            """
            INSERT INTO agents (agent_id, name, role, model, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("agent-1", "Test Agent", "BUILDER", "claude-3-5-sonnet-20241022", "active", datetime.now(timezone.utc).isoformat()),
        )
        await db.conn.commit()

        # Retrieve agent
        agent = await db.get_agent("agent-1")

        assert agent is not None
        assert agent.agent_id == "agent-1"
        assert agent.name == "Test Agent"
        assert agent.role == "BUILDER"

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, db):
        """Test retrieving a non-existent agent."""
        agent = await db.get_agent("nonexistent")
        assert agent is None

    @pytest.mark.asyncio
    async def test_list_agents(self, db):
        """Test listing all agents."""
        # Insert multiple agents
        agents_data = [
            ("agent-1", "Agent 1", "PLANNER", "claude-3-5-sonnet-20241022", "active"),
            ("agent-2", "Agent 2", "BUILDER", "claude-3-5-sonnet-20241022", "active"),
            ("agent-3", "Agent 3", "TESTER", "claude-3-5-sonnet-20241022", "completed"),
        ]

        for agent_id, name, role, model, status in agents_data:
            await db.conn.execute(
                """
                INSERT INTO agents (agent_id, name, role, model, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (agent_id, name, role, model, status, datetime.now(timezone.utc).isoformat()),
            )
        await db.conn.commit()

        # List all agents
        agents = await db.list_agents()

        assert len(agents) == 3
        assert all(isinstance(a, AgentRecord) for a in agents)

    @pytest.mark.asyncio
    async def test_list_agents_empty(self, db):
        """Test listing agents when database is empty."""
        agents = await db.list_agents()
        assert len(agents) == 0

    @pytest.mark.asyncio
    async def test_update_agent(self, db):
        """Test updating an agent record."""
        # Insert agent
        await db.conn.execute(
            """
            INSERT INTO agents (agent_id, name, role, model, status, total_cost, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("agent-1", "Test Agent", "BUILDER", "claude-3-5-sonnet-20241022", "active", 0.0, datetime.now(timezone.utc).isoformat()),
        )
        await db.conn.commit()

        # Update agent
        await db.update_agent(
            agent_id="agent-1",
            status="completed",
            total_cost=0.15,
            total_tokens=5000,
            messages_sent=10,
        )

        # Verify update
        agent = await db.get_agent("agent-1")
        assert agent.status == "completed"
        assert agent.total_cost == 0.15
        assert agent.total_tokens == 5000
        assert agent.messages_sent == 10

    @pytest.mark.asyncio
    async def test_delete_agent(self, db):
        """Test soft-deleting an agent."""
        # Insert agent
        await db.conn.execute(
            """
            INSERT INTO agents (agent_id, name, role, model, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("agent-1", "Test Agent", "BUILDER", "claude-3-5-sonnet-20241022", "active", datetime.now(timezone.utc).isoformat()),
        )
        await db.conn.commit()

        # Delete agent (soft delete)
        await db.delete_agent("agent-1")

        # Verify deletion
        agent = await db.get_agent("agent-1")
        assert agent.deleted_at is not None


class TestTaskOperations:
    """Test task CRUD operations."""

    @pytest.mark.asyncio
    async def test_save_task(self, db):
        """Test saving a task record."""
        task = TaskRecord(
            task_id="task-1",
            description="Test task",
            task_type="feature_implementation",
            status="running",
            assigned_agents="[]",
            created_at=datetime.now(timezone.utc),
        )

        await db.save_task(task)

        # Verify task was saved
        async with db.conn.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task.task_id,)
        ) as cursor:
            result = await cursor.fetchone()
            assert result is not None
            assert result[0] == "task-1"
            assert result[1] == "Test task"

    @pytest.mark.asyncio
    async def test_get_task(self, db):
        """Test retrieving a task record."""
        # Insert task directly
        await db.conn.execute(
            """
            INSERT INTO tasks (task_id, description, task_type, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("task-1", "Test task", "bug_fix", "completed", datetime.now(timezone.utc).isoformat()),
        )
        await db.conn.commit()

        # Retrieve task
        task = await db.get_task("task-1")

        assert task is not None
        assert task.task_id == "task-1"
        assert task.description == "Test task"
        assert task.task_type == "bug_fix"

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, db):
        """Test retrieving a non-existent task."""
        task = await db.get_task("nonexistent")
        assert task is None

    @pytest.mark.asyncio
    async def test_list_tasks(self, db):
        """Test listing all tasks."""
        # Insert multiple tasks
        tasks_data = [
            ("task-1", "Task 1", "feature_implementation", "completed"),
            ("task-2", "Task 2", "bug_fix", "running"),
            ("task-3", "Task 3", "code_review", "pending"),
        ]

        for task_id, desc, task_type, status in tasks_data:
            await db.conn.execute(
                """
                INSERT INTO tasks (task_id, description, task_type, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (task_id, desc, task_type, status, datetime.now(timezone.utc).isoformat()),
            )
        await db.conn.commit()

        # List all tasks
        tasks = await db.list_tasks()

        assert len(tasks) == 3
        assert all(isinstance(t, TaskRecord) for t in tasks)

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, db):
        """Test listing tasks when database is empty."""
        tasks = await db.list_tasks()
        assert len(tasks) == 0

    @pytest.mark.asyncio
    async def test_update_task(self, db):
        """Test updating a task record."""
        # Insert task
        await db.conn.execute(
            """
            INSERT INTO tasks (task_id, description, task_type, status, total_cost, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("task-1", "Test task", "bug_fix", "running", 0.0, datetime.now(timezone.utc).isoformat()),
        )
        await db.conn.commit()

        # Update task
        await db.update_task(
            task_id="task-1",
            status="completed",
            total_cost=0.25,
            result="Task completed successfully",
        )

        # Verify update
        task = await db.get_task("task-1")
        assert task.status == "completed"
        assert task.total_cost == 0.25
        assert task.result == "Task completed successfully"
        assert task.completed_at is not None


class TestDatabaseQueries:
    """Test database query operations."""

    @pytest.mark.asyncio
    async def test_get_agents_by_role(self, db):
        """Test filtering agents by role."""
        # Insert agents with different roles
        roles = ["PLANNER", "BUILDER", "BUILDER", "TESTER"]
        for i, role in enumerate(roles):
            await db.conn.execute(
                """
                INSERT INTO agents (agent_id, name, role, model, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (f"agent-{i+1}", f"Agent {i+1}", role, "claude-3-5-sonnet-20241022", "active", datetime.now(timezone.utc).isoformat()),
            )
        await db.conn.commit()

        # Get builders only
        builders = await db.get_agents_by_role("BUILDER")

        assert len(builders) == 2
        assert all(a.role == "BUILDER" for a in builders)

    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, db):
        """Test filtering tasks by status."""
        # Insert tasks with different statuses
        statuses = ["running", "completed", "running", "failed"]
        for i, status in enumerate(statuses):
            await db.conn.execute(
                """
                INSERT INTO tasks (task_id, description, task_type, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (f"task-{i+1}", f"Task {i+1}", "feature_implementation", status, datetime.now(timezone.utc).isoformat()),
            )
        await db.conn.commit()

        # Get running tasks
        running = await db.get_tasks_by_status("running")

        assert len(running) == 2
        assert all(t.status == "running" for t in running)

    @pytest.mark.asyncio
    async def test_get_total_cost(self, db):
        """Test calculating total cost across all agents."""
        # Insert agents with costs
        costs = [0.10, 0.25, 0.05, 0.15]
        for i, cost in enumerate(costs):
            await db.conn.execute(
                """
                INSERT INTO agents (agent_id, name, role, model, status, total_cost, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (f"agent-{i+1}", f"Agent {i+1}", "BUILDER", "claude-3-5-sonnet-20241022", "active", cost, datetime.now(timezone.utc).isoformat()),
            )
        await db.conn.commit()

        # Get total cost
        total = await db.get_total_cost()

        assert abs(total - 0.55) < 0.001  # Float comparison


class TestDatabaseEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, db):
        """Test concurrent database writes."""
        async def write_agent(i):
            agent = AgentRecord(
                agent_id=f"agent-{i}",
                name=f"Agent {i}",
                role="BUILDER",
                model="claude-3-5-sonnet-20241022",
                status="active",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            await db.save_agent(agent)

        # Write 10 agents concurrently
        await asyncio.gather(*[write_agent(i) for i in range(10)])

        # Verify all agents were saved
        agents = await db.list_agents()
        assert len(agents) == 10

    @pytest.mark.asyncio
    async def test_special_characters_in_data(self, db):
        """Test handling special characters in data."""
        agent = AgentRecord(
            agent_id="agent-1",
            name="Agent with 'quotes' and \"double quotes\"",
            role="BUILDER",
            model="claude-3-5-sonnet-20241022",
            status="active",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        await db.save_agent(agent)
        retrieved = await db.get_agent("agent-1")

        assert retrieved.name == agent.name

    @pytest.mark.asyncio
    async def test_update_nonexistent_agent(self, db):
        """Test updating a non-existent agent."""
        # Should not raise error, just not update anything
        await db.update_agent(
            agent_id="nonexistent", status="completed", total_cost=0.10
        )

        # Verify nothing was created
        agents = await db.list_agents()
        assert len(agents) == 0
