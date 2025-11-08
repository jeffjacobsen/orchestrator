"""
Orchestrator execution service.

This module integrates the orchestrator execution engine with the dashboard,
allowing tasks to be executed via the API.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.models.agent import Agent, AgentStatus, AgentRole
from app.api.v1.websocket import get_websocket_manager

logger = logging.getLogger(__name__)


class DashboardProgressTracker:
    """
    Progress tracker that broadcasts events to dashboard via WebSocket.

    Implements the same interface as ProgressTracker but sends updates
    to the dashboard instead of displaying in console.
    """

    def __init__(self, db: AsyncSession, task_id: str):
        self.db = db
        self.task_id = task_id
        self.manager = get_websocket_manager()
        self.current_step = 0  # Track which workflow step we're on

    def start(self, workflow_steps=None):
        """Start tracking - no-op for dashboard."""
        pass

    def stop(self):
        """Stop tracking - no-op for dashboard."""
        pass

    async def agent_created(self, agent_id: str, name: str, role: str):
        """Broadcast agent creation to dashboard."""
        from sqlalchemy import select

        logger.info(f"Agent created: {agent_id} ({role})")

        # Create agent record in database
        agent = Agent(
            id=agent_id,
            role=AgentRole(role.upper()),
            task_id=self.task_id,
            status=AgentStatus.IDLE,
            custom_instructions=name,
        )
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)

        # Broadcast to WebSocket clients
        await self.manager.broadcast_agent_update(agent)

    async def agent_started(self, agent_id: str):
        """Broadcast agent started to dashboard."""
        from sqlalchemy import select

        logger.info(f"Agent started: {agent_id} (step {self.current_step})")

        # Update agent status to ACTIVE
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

        if agent:
            agent.status = AgentStatus.ACTIVE
            await self.db.commit()
            await self.db.refresh(agent)
            await self.manager.broadcast_agent_update(agent)

        # Update task's current_step to show which workflow step is executing
        task_result = await self.db.execute(select(Task).where(Task.id == self.task_id))
        task = task_result.scalar_one_or_none()

        if task:
            task.current_step = self.current_step
            await self.db.commit()
            await self.db.refresh(task)
            await self.manager.broadcast_task_update(task)

    async def thinking(self, agent_id: str):
        """Agent is thinking - could broadcast activity update."""
        logger.debug(f"Agent thinking: {agent_id}")

    async def tool_call(self, agent_id: str, tool_name: str):
        """Agent made a tool call - could broadcast activity update."""
        logger.info(f"Agent {agent_id} using tool: {tool_name}")

    async def agent_completed(self, agent_id: str, cost: float):
        """Broadcast agent completion to dashboard."""
        from sqlalchemy import select

        logger.info(f"Agent completed: {agent_id}, cost: ${cost:.4f}")

        # Update agent status to COMPLETED immediately
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

        if agent:
            agent.status = AgentStatus.COMPLETED
            await self.db.commit()
            await self.db.refresh(agent)
            await self.manager.broadcast_agent_update(agent)

        # Increment step counter for next agent
        self.current_step += 1
        logger.debug(f"Advanced to step {self.current_step}")

    async def agent_failed(self, agent_id: str, error: str):
        """Broadcast agent failure to dashboard."""
        from sqlalchemy import select

        logger.error(f"Agent failed: {agent_id}, error: {error}")

        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

        if agent:
            agent.status = AgentStatus.FAILED
            await self.db.commit()
            await self.db.refresh(agent)
            await self.manager.broadcast_agent_update(agent)


class OrchestratorExecutor:
    """
    Executes tasks using the orchestrator engine.

    This service:
    - Takes tasks from the database
    - Executes them using the orchestrator
    - Updates task and agent status in real-time
    - Broadcasts updates via WebSocket
    """

    def __init__(self, db: AsyncSession, working_directory: str = "."):
        self.db = db
        self.working_directory = working_directory

    async def execute_task(self, task_id: str) -> None:
        """
        Execute a task using the orchestrator.

        Args:
            task_id: ID of task to execute
        """
        from sqlalchemy import select

        try:
            # Get task from database
            result = await self.db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                logger.error(f"Task not found: {task_id}")
                return

            # Update task status to in_progress
            task.status = TaskStatus.IN_PROGRESS
            await self.db.commit()
            await self.db.refresh(task)

            # Broadcast task update
            manager = get_websocket_manager()
            await manager.broadcast_task_update(task)

            logger.info(f"Starting task execution: {task.id}")

            # Import orchestrator components
            try:
                from orchestrator.core.agent_manager import AgentManager
                from orchestrator.workflow.planner import TaskPlanner
                from orchestrator.workflow.executor import WorkflowExecutor
                from orchestrator.observability.monitor import AgentMonitor
            except ImportError as e:
                logger.error(f"Failed to import orchestrator: {e}")
                task.status = TaskStatus.FAILED
                task.error = f"Orchestrator not installed: {e}"
                await self.db.commit()
                await manager.broadcast_task_update(task)
                return

            # Initialize orchestrator components with dashboard progress tracker
            agent_manager = AgentManager(working_directory=self.working_directory)
            monitor = AgentMonitor()
            progress_tracker = DashboardProgressTracker(db=self.db, task_id=task.id)
            executor = WorkflowExecutor(
                agent_manager=agent_manager,
                monitor=monitor,
                progress_tracker=progress_tracker
            )
            planner = TaskPlanner(
                working_directory=task.working_directory,
                use_ai_planner=True,  # Enable AI PLANNER agent
            )

            # Plan the task
            logger.info(f"Planning task: {task.description}")
            orchestrator_task = await planner.plan_task(
                task_id=task.id,
                description=task.description,
                task_type=task.task_type.value,
            )

            # Store workflow in task (subtasks are dicts with "role" key)
            # Convert orchestrator roles (lowercase) to dashboard format (uppercase for display)
            task.workflow = [subtask["role"].value.upper() for subtask in orchestrator_task.subtasks]
            await self.db.commit()
            await manager.broadcast_task_update(task)

            # Execute the task
            # Agents will be created automatically by the progress tracker callbacks
            logger.info(f"Executing task: {task.id}")
            results = await executor.execute_sequential(orchestrator_task)

            # Update agent records with final metrics and aggregate to task
            total_task_cost_cents = 0
            total_task_duration = 0
            task_start_time = task.created_at

            for result in results:
                # Find the agent created by progress tracker
                agent_result = await self.db.execute(
                    select(Agent).where(Agent.id == result.agent_id)
                )
                agent = agent_result.scalar_one_or_none()

                if agent:
                    # Update with actual metrics
                    agent.status = AgentStatus.COMPLETED if result.success else AgentStatus.FAILED
                    agent.total_input_tokens = result.metrics.input_tokens
                    agent.total_output_tokens = result.metrics.output_tokens
                    agent.cache_creation_tokens = result.metrics.cache_creation_input_tokens
                    agent.cache_read_tokens = result.metrics.cache_read_input_tokens

                    # Calculate cost (rough estimate: $3/M input, $15/M output for Claude)
                    input_cost = (agent.total_input_tokens / 1_000_000) * 3
                    output_cost = (agent.total_output_tokens / 1_000_000) * 15
                    agent.total_cost = f"${input_cost + output_cost:.4f}"

                    # Aggregate cost (convert to cents to store as integer)
                    agent_cost_cents = int((input_cost + output_cost) * 100)
                    total_task_cost_cents += agent_cost_cents

                    await self.db.commit()
                    await self.db.refresh(agent)

                    # Broadcast final agent update with metrics
                    await manager.broadcast_agent_update(agent)

                # Aggregate duration from result metrics
                if result.metrics and hasattr(result.metrics, 'execution_time_seconds'):
                    total_task_duration += int(result.metrics.execution_time_seconds)

            # Calculate total task duration from start to completion
            task_end_time = datetime.now(timezone.utc)
            task_duration_from_timestamps = int((task_end_time - task_start_time).total_seconds())

            # Mark task as completed with aggregated metrics
            task.status = TaskStatus.COMPLETED
            task.completed_at = task_end_time
            task.result = f"Task completed successfully with {len(results)} agents"
            task.total_cost = total_task_cost_cents  # Store in cents
            task.duration_seconds = task_duration_from_timestamps  # Use wall clock time
            await self.db.commit()
            await manager.broadcast_task_update(task)

            logger.info(f"Task completed: {task.id}")

        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.error = str(e)
            await self.db.commit()

            manager = get_websocket_manager()
            await manager.broadcast_task_update(task)


async def execute_task_background(task_id: str, db_url: str, working_directory: str = "."):
    """
    Background task executor that can be run independently.

    Args:
        task_id: ID of task to execute
        db_url: Database URL
        working_directory: Working directory for orchestrator
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.models.task import Task

    # Create database session
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get task
        result = await session.execute(
            "SELECT * FROM tasks WHERE id = :id",
            {"id": task_id}
        )
        task = result.scalar_one_or_none()

        if not task:
            logger.error(f"Task not found: {task_id}")
            return

        # Execute task
        executor = OrchestratorExecutor(db=session, working_directory=working_directory)
        await executor.execute_task(task)
