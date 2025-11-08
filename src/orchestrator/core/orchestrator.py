"""Main orchestrator class - the unified interface for multi-agent control."""

import uuid
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path

from orchestrator.core.agent_manager import AgentManager
from orchestrator.core.types import AgentRole, AgentMetrics, AgentStatus, OrchestratorTask, TaskResult
from orchestrator.workflow.planner import TaskPlanner
from orchestrator.workflow.executor import WorkflowExecutor
from orchestrator.observability.monitor import AgentMonitor
from orchestrator.observability.logger import StructuredLogger
from orchestrator.observability.metrics import MetricsCollector
from orchestrator.observability.progress import ProgressTracker


class Orchestrator:
    """
    The Orchestrator - Unified Interface for Multi-Agent Control.

    Key Principles:
    1. Single interface to manage entire agent fleet
    2. Protects its own context by delegating work
    3. Creates, monitors, and deletes agents as needed
    4. Handles high-level prompts and decomposes them
    5. Provides full observability

    This is the central component that implements the multi-agent
    orchestration philosophy described in the markdown.
    """

    def __init__(
        self,
        working_directory: Optional[str] = None,
        db_path: Optional[Path] = None,
        log_path: Optional[Path] = None,
        enable_monitoring: bool = True,
        enable_progress_display: bool = True,
    ) -> None:
        """
        Initialize the orchestrator.

        Note: No API key needed - Claude Code SDK uses CLI authentication.

        Args:
            working_directory: Default working directory for all agents
            db_path: Path to SQLite database (optional)
            log_path: Path to log file (optional)
            enable_monitoring: Enable real-time monitoring
            enable_progress_display: Enable real-time progress display
        """
        # Store working directory
        self.working_directory = working_directory

        # Observability
        self.logger = StructuredLogger(log_file=log_path)
        self.metrics = MetricsCollector()
        self.monitor = AgentMonitor(logger=self.logger, metrics=self.metrics)
        self.progress_tracker = ProgressTracker(enabled=enable_progress_display)

        # Core components
        self.agent_manager = AgentManager(
            working_directory=working_directory,
            monitor=self.monitor,
        )
        self.planner = TaskPlanner(
            working_directory=working_directory,
            use_ai_planner=True,  # Enable AI PLANNER agent by default
        )
        self.executor = WorkflowExecutor(
            agent_manager=self.agent_manager,
            monitor=self.monitor,
            progress_tracker=self.progress_tracker,
        )

        # State
        self.tasks: Dict[str, OrchestratorTask] = {}
        self.enable_monitoring = enable_monitoring
        self.monitoring_task: Optional[asyncio.Task[None]] = None

        self.logger.info("orchestrator_initialized")

    async def start(self) -> None:
        """Start the orchestrator and monitoring."""
        if self.enable_monitoring:
            self.monitoring_task = asyncio.create_task(
                self.monitor.start_monitoring(
                    agents=self.agent_manager.agents,
                    interval_seconds=15,
                )
            )
            self.logger.info("monitoring_started")

    async def stop(self) -> None:
        """Stop the orchestrator and cleanup."""
        if self.monitoring_task:
            self.monitor.stop_monitoring()
            await self.monitoring_task
            self.logger.info("monitoring_stopped")

        # Cleanup all agents
        deleted = await self.agent_manager.delete_all_agents()
        self.logger.info("orchestrator_stopped", agents_deleted=deleted)

    async def execute(
        self,
        prompt: str,
        task_type: str = "custom",
        execution_mode: str = "sequential",
    ) -> TaskResult:
        """
        Execute a high-level task using the orchestrator.

        This is the main entry point that demonstrates the full workflow:
        1. User gives high-level prompt
        2. Orchestrator thinks and creates plan
        3. Orchestrator spawns specialized agents
        4. Each agent executes focused work
        5. Orchestrator monitors progress
        6. Results are collected and aggregated
        7. Agents are deleted

        Args:
            prompt: High-level task description
            task_type: Type of task (feature_implementation, bug_fix, etc.)
            execution_mode: 'sequential' or 'parallel'

        Returns:
            Aggregated TaskResult containing success status, combined outputs,
            aggregated metrics (tokens, cost), and list of artifacts produced.

        Examples:
            Basic feature implementation workflow:

            >>> orchestrator = Orchestrator(working_directory="/path/to/project")
            >>> await orchestrator.start()
            >>>
            >>> # Simple feature implementation - uses predefined workflow template
            >>> result = await orchestrator.execute(
            ...     prompt="Add user authentication to the API",
            ...     task_type="feature_implementation",
            ...     execution_mode="sequential"
            ... )
            >>>
            >>> # Workflow executed:
            >>> # 1. Analyst: Research requirements and analyze existing codebase
            >>> # 2. Planner: Create implementation plan based on analysis
            >>> # 3. Builder: Implement the feature following the plan
            >>> # 4. Tester: Write and run tests for the new feature
            >>> # 5. Reviewer: Review implementation quality
            >>>
            >>> print(f"Success: {result.success}")
            >>> print(f"Total cost: ${result.metrics.total_cost:.4f}")
            >>> print(f"Files modified: {result.metrics.files_written}")
            Success: True
            Total cost: $0.2450
            Files modified: ['src/auth.py', 'tests/test_auth.py']

            Bug fix workflow with sequential execution:

            >>> # Bug fix - uses specialized template
            >>> result = await orchestrator.execute(
            ...     prompt="Fix memory leak in data processing pipeline",
            ...     task_type="bug_fix",
            ...     execution_mode="sequential"
            ... )
            >>>
            >>> # Workflow executed:
            >>> # 1. Analyst: Investigate and analyze the root cause
            >>> # 2. Planner: Create a fix plan based on root cause
            >>> # 3. Builder: Implement the fix
            >>> # 4. Tester: Test the fix and add regression tests
            >>> # 5. Reviewer: Review that fix resolves the issue
            >>>
            >>> if result.success:
            ...     print(f"Bug fixed! Check {result.artifacts}")
            Bug fixed! Check ['src/pipeline.py', 'tests/test_pipeline_memory.py']

            Code review workflow:

            >>> result = await orchestrator.execute(
            ...     prompt="Review the changes in pull request #123",
            ...     task_type="code_review",
            ...     execution_mode="sequential"
            ... )
            >>>
            >>> # Workflow executed:
            >>> # 1. Analyst: Analyze code changes and identify areas to review
            >>> # 2. Planner: Create review plan with checklist and priorities
            >>> # 3. Reviewer: Review code for quality, security, best practices
            >>> # 4. Tester: Verify test coverage is adequate
            >>>
            >>> print(result.output)
            [analyst-uuid]: Analyzed 12 files with 450 lines changed...
            [planner-uuid]: Review plan created with 5 priority areas...
            [reviewer-uuid]: Found 3 issues: 2 minor, 1 moderate...
            [tester-uuid]: Test coverage at 85%, 3 edge cases need tests...

            Parallel execution for independent tasks:

            >>> # Auto-detect task complexity and execute in parallel
            >>> result = await orchestrator.execute(
            ...     prompt="Generate comprehensive API documentation",
            ...     task_type="auto",
            ...     execution_mode="parallel"
            ... )
            >>>
            >>> # Orchestrator analyzes prompt and creates parallel plan
            >>> # Multiple agents work simultaneously on different aspects
            >>> print(f"Execution time: {result.metrics.execution_time_seconds:.1f}s")
            >>> print(f"Agents used: {len(result.metrics.files_read)} concurrent")
            Execution time: 45.3s
            Agents used: 3 concurrent

            Custom workflow with auto task type:

            >>> # Let orchestrator determine optimal workflow
            >>> result = await orchestrator.execute(
            ...     prompt="Analyze the codebase and create a refactoring plan "
            ...            "to improve performance in the database layer",
            ...     task_type="auto",
            ...     execution_mode="sequential"
            ... )
            >>>
            >>> # Orchestrator analyzes keywords and suggests roles:
            >>> # - "analyze" → Analyst
            >>> # - "plan" → Planner
            >>> # Creates custom workflow based on complexity estimation
            >>>
            >>> # Access detailed metrics
            >>> metrics = result.metrics
            >>> print(f"Total tokens: {metrics.total_tokens:,}")
            >>> print(f"Cached tokens: {metrics.cache_read_input_tokens:,}")
            >>> print(f"Tool calls: {metrics.tool_calls}")
            Total tokens: 125,430
            Cached tokens: 42,150
            Tool calls: 28

            Error handling:

            >>> try:
            ...     result = await orchestrator.execute(
            ...         prompt="Impossible task that will fail",
            ...         task_type="feature_implementation"
            ...     )
            ... except Exception as e:
            ...     print(f"Task failed: {e}")
            ...     # Orchestrator automatically cleans up agents even on failure
            ...     status = orchestrator.get_status()
            ...     print(f"Active agents after failure: {status['fleet']['active_agents']}")
            Task failed: Agent execution error
            Active agents after failure: 0

            Monitoring and status during execution:

            >>> import asyncio
            >>>
            >>> # Start long-running task
            >>> task = asyncio.create_task(
            ...     orchestrator.execute(
            ...         prompt="Migrate database schema to new version",
            ...         task_type="feature_implementation"
            ...     )
            ... )
            >>>
            >>> # Check status while running
            >>> await asyncio.sleep(5)
            >>> status = orchestrator.get_status()
            >>> print(f"Active agents: {status['fleet']['active_agents']}")
            >>> print(f"Current cost: {status['metrics']['total_cost']}")
            >>>
            >>> # Wait for completion
            >>> result = await task
            Active agents: 2
            Current cost: $0.0450
        """
        task_id = str(uuid.uuid4())

        self.logger.info(
            "task_started",
            task_id=task_id,
            prompt=prompt,
            task_type=task_type,
        )

        # Step 1: Plan the task
        if task_type == "auto":
            # Analyze prompt and determine task type
            complexity = self.planner.estimate_task_complexity(prompt)
            suggested_roles = complexity["suggested_roles"]

            task = self.planner.plan_parallel_tasks(
                task_id=task_id,
                description=prompt,
                agent_roles=suggested_roles,
            )
        else:
            task = await self.planner.plan_task(
                task_id=task_id,
                description=prompt,
                task_type=task_type,
            )

        self.tasks[task_id] = task

        self.logger.info(
            "task_planned",
            task_id=task_id,
            subtasks=len(task.subtasks),
        )

        # Extract workflow step names for progress display
        workflow_steps = [subtask["description"] for subtask in task.subtasks]

        # Start progress tracking
        self.progress_tracker.start(workflow_steps=workflow_steps)

        # Step 2: Execute the workflow
        try:
            if execution_mode == "parallel":
                results = await self.executor.execute_parallel(task)
            else:
                results = await self.executor.execute_sequential(task)

            # Step 3: Aggregate results
            aggregated = self._aggregate_results(results)

            # Update task status
            task.status = AgentStatus.COMPLETED if aggregated.success else AgentStatus.FAILED
            task.completed_at = aggregated.timestamp
            task.result = aggregated

            self.logger.info(
                "task_completed",
                task_id=task_id,
                success=aggregated.success,
                total_cost=aggregated.metrics.total_cost,
            )

            return aggregated

        except Exception as e:
            self.logger.error(
                "task_failed",
                task_id=task_id,
                error=str(e),
            )
            raise

        finally:
            # Stop progress tracking
            self.progress_tracker.stop()

            # Step 4: Cleanup agents
            deleted = await self.executor.cleanup_workflow_agents(task)
            self.logger.info("workflow_cleanup", agents_deleted=deleted)

    async def execute_custom_workflow(
        self,
        prompt: str,
        roles: List[AgentRole],
        parallel: bool = False,
    ) -> List[TaskResult]:
        """
        Execute a custom workflow with specified agent roles.

        Args:
            prompt: Task description
            roles: List of agent roles to use
            parallel: Execute in parallel if True

        Returns:
            List of results from each agent
        """
        task_id = str(uuid.uuid4())

        task = self.planner.plan_parallel_tasks(
            task_id=task_id,
            description=prompt,
            agent_roles=roles,
        )

        self.tasks[task_id] = task

        try:
            if parallel:
                results = await self.executor.execute_parallel(task)
            else:
                results = await self.executor.execute_sequential(task)

            return results

        finally:
            await self.executor.cleanup_workflow_agents(task)

    def _aggregate_results(self, results: List[TaskResult]) -> TaskResult:
        """
        Aggregate results from multiple agents.

        Args:
            results: List of task results

        Returns:
            Single aggregated result
        """
        # Combine outputs
        outputs = []
        all_artifacts = []
        total_metrics: Optional[AgentMetrics] = None

        all_success = True

        for result in results:
            if not result.success:
                all_success = False

            if result.output:
                outputs.append(f"[{result.agent_id}]: {result.output}")

            all_artifacts.extend(result.artifacts)

            # Aggregate metrics
            if total_metrics is None:
                total_metrics = result.metrics.model_copy()
            else:
                total_metrics.total_tokens += result.metrics.total_tokens
                total_metrics.input_tokens += result.metrics.input_tokens
                total_metrics.output_tokens += result.metrics.output_tokens
                total_metrics.cache_creation_input_tokens += result.metrics.cache_creation_input_tokens
                total_metrics.cache_read_input_tokens += result.metrics.cache_read_input_tokens
                total_metrics.total_cost += result.metrics.total_cost
                total_metrics.tool_calls += result.metrics.tool_calls
                total_metrics.messages_sent += result.metrics.messages_sent
                total_metrics.files_read.extend(result.metrics.files_read)
                total_metrics.files_written.extend(result.metrics.files_written)
                total_metrics.execution_time_seconds += result.metrics.execution_time_seconds

        # If no results, create default metrics
        if total_metrics is None:
            total_metrics = AgentMetrics(agent_id="orchestrator")

        return TaskResult(
            agent_id="orchestrator",
            task_description="Aggregated workflow results",
            success=all_success,
            output="\n\n".join(outputs),
            metrics=total_metrics,
            artifacts=list(set(all_artifacts)),
        )

    # Observability methods

    def get_status(self) -> Dict[str, Any]:
        """
        Get current orchestrator status.

        Returns comprehensive view of:
        - Active agents
        - Costs and metrics
        - Files consumed/produced
        - Task status
        """
        return {
            "fleet": self.agent_manager.get_fleet_summary(),
            "metrics": self.metrics.get_summary(),
            "tasks": {
                "total": len(self.tasks),
                "active": len([t for t in self.tasks.values() if t.completed_at is None]),
            },
            "monitoring": self.monitor.get_summary(),
        }

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            "task_id": task_id,
            "description": task.description,
            "status": task.status.value,
            "subtasks": len(task.subtasks),
            "assigned_agents": task.assigned_agents,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result.model_dump() if task.result else None,
        }

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks."""
        return [
            status
            for task_id in self.tasks.keys()
            if (status := self.get_task_status(task_id)) is not None
        ]

    def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an agent."""
        agent = self.agent_manager.get_agent(agent_id)
        if not agent:
            return None

        return agent.get_summary()

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all active agents with details."""
        return [
            agent.get_summary()
            for agent in self.agent_manager.get_active_agents()
        ]

    # Manual agent control (for advanced use)

    async def create_agent(
        self,
        role: AgentRole,
        name: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Manually create an agent.

        Args:
            role: Agent role
            name: Optional custom name
            system_prompt: Optional custom system prompt

        Returns:
            Agent ID
        """
        if name and system_prompt:
            agent = await self.agent_manager.create_agent(
                name=name,
                role=role,
                system_prompt=system_prompt,
            )
        else:
            agent = await self.agent_manager.create_specialized_agent(role)

        return agent.agent_id

    async def send_to_agent(self, agent_id: str, message: str) -> Optional[str]:
        """
        Send a message to a specific agent.

        Args:
            agent_id: Target agent
            message: Message to send

        Returns:
            Agent's response or None if agent not found
        """
        agent = self.agent_manager.get_agent(agent_id)
        if not agent:
            return None

        response = await agent.send_message(message)
        await self.monitor.log_task_completed(agent, message)

        return response

    async def delete_agent(self, agent_id: str) -> bool:
        """
        Manually delete an agent.

        Args:
            agent_id: Agent to delete

        Returns:
            True if successful
        """
        return await self.agent_manager.delete_agent(agent_id)
