"""Workflow execution engine."""

import asyncio
import inspect
from typing import Any, Awaitable, Callable, Dict, List, Optional, cast
from orchestrator.core.agent_manager import AgentManager
from orchestrator.core.types import OrchestratorTask, TaskResult
from orchestrator.observability.monitor import AgentMonitor
from orchestrator.observability.progress import ProgressTracker
from orchestrator.workflow.context_parser import extract_structured_output, AgentContext


class WorkflowExecutor:
    """
    Executes workflows by coordinating multiple agents.

    Handles:
    - Sequential task execution
    - Parallel task execution
    - Task dependencies
    - Error handling and recovery
    """

    def __init__(
        self,
        agent_manager: AgentManager,
        monitor: AgentMonitor,
        progress_tracker: Optional[ProgressTracker] = None,
    ) -> None:
        self.agent_manager = agent_manager
        self.monitor = monitor
        self.progress_tracker = progress_tracker
        # Store agent contexts for non-sequential passing and feedback loops
        self.agent_contexts: Dict[str, AgentContext] = {}

    async def execute_sequential(
        self,
        task: OrchestratorTask,
    ) -> List[TaskResult]:
        """
        Execute subtasks sequentially with output passing between agents.

        Each agent executes in order, receiving the previous agent's output
        as context. This creates a pipeline where each step builds upon the
        previous one. Ideal for workflows with clear dependencies.

        Args:
            task: Orchestrator task with subtasks to execute in sequence

        Returns:
            List of TaskResult objects, one per subtask in execution order.
            Each result contains output, metrics, and artifacts from that agent.

        Examples:
            Basic sequential workflow execution:

            >>> from orchestrator.workflow.executor import WorkflowExecutor
            >>> from orchestrator.workflow.planner import TaskPlanner
            >>> from orchestrator.core.agent_manager import AgentManager
            >>> from orchestrator.observability.monitor import AgentMonitor
            >>>
            >>> # Setup components
            >>> manager = AgentManager(working_directory="/path/to/project")
            >>> monitor = AgentMonitor()
            >>> executor = WorkflowExecutor(agent_manager=manager, monitor=monitor)
            >>> planner = TaskPlanner()
            >>>
            >>> # Create a task plan
            >>> task = planner.plan_task(
            ...     task_id="seq-001",
            ...     description="Add authentication to the API",
            ...     task_type="feature_implementation"
            ... )
            >>>
            >>> # Execute sequentially
            >>> results = await executor.execute_sequential(task)
            >>>
            >>> # Each agent executes in order:
            >>> # 1. Analyst analyzes requirements
            >>> # 2. Planner receives analyst output, creates plan
            >>> # 3. Builder receives plan, implements feature
            >>> # 4. Tester receives implementation, writes tests
            >>> # 5. Reviewer receives all previous outputs, reviews quality
            >>>
            >>> print(f"Completed {len(results)} sequential tasks")
            >>> for i, result in enumerate(results, 1):
            ...     print(f"{i}. Agent {result.agent_id[:8]}: {result.success}")
            Completed 5 sequential tasks
            1. Agent abc12345: True
            2. Agent def67890: True
            3. Agent ghi13579: True
            4. Agent jkl24680: True
            5. Agent mno86420: True

            Understanding the sequential pipeline:

            >>> # Execute and examine output flow
            >>> task = planner.plan_task(
            ...     task_id="seq-002",
            ...     description="Fix bug in payment processing",
            ...     task_type="bug_fix"
            ... )
            >>>
            >>> results = await executor.execute_sequential(task)
            >>>
            >>> # First agent (Analyst) gets only the task description
            >>> print("Analyst input: task description only")
            >>> print(f"Analyst output: {results[0].output[:100]}...")
            >>>
            >>> # Second agent (Planner) gets analyst's output
            >>> print("\nPlanner input: task description + analyst output")
            >>> print(f"Planner output: {results[1].output[:100]}...")
            >>>
            >>> # Third agent (Builder) gets planner's output (and so on)
            >>> print("\nBuilder input: task description + planner output")
            >>> print(f"Builder output: {results[2].output[:100]}...")
            Analyst input: task description only
            Analyst output: Root cause identified in transaction.py line 145. Race condition when processing...

            Planner input: task description + analyst output
            Planner output: Fix plan: 1. Add transaction lock 2. Implement retry logic 3. Add error handling...

            Builder input: task description + planner output
            Builder output: Implemented fix with database locks and retry mechanism. Modified 3 files...

            Accessing individual agent results:

            >>> # Execute workflow
            >>> task = planner.plan_task(
            ...     task_id="seq-003",
            ...     description="Optimize database queries",
            ...     task_type="feature_implementation"
            ... )
            >>> results = await executor.execute_sequential(task)
            >>>
            >>> # Access each agent's result
            >>> analyst_result = results[0]
            >>> planner_result = results[1]
            >>> builder_result = results[2]
            >>>
            >>> print(f"Analyst found: {analyst_result.output}")
            >>> print(f"Planner created: {planner_result.output}")
            >>> print(f"Builder modified: {builder_result.artifacts}")
            Analyst found: Identified 12 slow queries in user_service.py...
            Planner created: Plan to add indexes on user_id and created_at...
            Builder modified: ['src/models.py', 'migrations/001_add_indexes.sql']

            Tracking metrics across the pipeline:

            >>> task = planner.plan_task(
            ...     task_id="seq-004",
            ...     description="Implement caching layer",
            ...     task_type="feature_implementation"
            ... )
            >>> results = await executor.execute_sequential(task)
            >>>
            >>> # Analyze metrics for each step
            >>> total_tokens = 0
            >>> total_cost = 0.0
            >>> total_time = 0.0
            >>>
            >>> for i, result in enumerate(results):
            ...     tokens = result.metrics.total_tokens
            ...     cost = result.metrics.total_cost
            ...     time = result.metrics.execution_time_seconds
            ...     total_tokens += tokens
            ...     total_cost += cost
            ...     total_time += time
            ...     print(f"Step {i+1}: {tokens:,} tokens, ${cost:.4f}, {time:.1f}s")
            >>>
            >>> print(f"\nTotal: {total_tokens:,} tokens, ${total_cost:.4f}, {total_time:.1f}s")
            Step 1: 15,420 tokens, $0.0234, 12.3s
            Step 2: 8,150 tokens, $0.0123, 8.1s
            Step 3: 25,680 tokens, $0.0389, 28.5s
            Step 4: 18,900 tokens, $0.0286, 15.7s
            Step 5: 12,340 tokens, $0.0187, 9.8s

            Total: 80,490 tokens, $0.1219, 74.4s

            Handling errors in sequential execution:

            >>> task = planner.plan_task(
            ...     task_id="seq-005",
            ...     description="Complex refactoring task",
            ...     task_type="feature_implementation"
            ... )
            >>>
            >>> # If an agent fails, execution continues but results show failure
            >>> results = await executor.execute_sequential(task)
            >>>
            >>> # Check for failures
            >>> for i, result in enumerate(results):
            ...     status = "✓" if result.success else "✗"
            ...     print(f"{status} Step {i+1}: {result.task_description[:50]}...")
            ...     if not result.success:
            ...         print(f"  Error: {result.error}")
            ✓ Step 1: Research requirements and analyze existing codebase...
            ✓ Step 2: Create implementation plan based on analysis...
            ✗ Step 3: Implement the feature following the plan...
              Error: Compilation error in generated code
            ✓ Step 4: Write and run tests for the new feature...
            ✓ Step 5: Review that implementation follows the plan...

            Sequential execution with agent tracking:

            >>> task = planner.plan_task(
            ...     task_id="seq-006",
            ...     description="Add API endpoint for user profile",
            ...     task_type="feature_implementation"
            ... )
            >>>
            >>> print(f"Agents before execution: {task.assigned_agents}")
            >>> results = await executor.execute_sequential(task)
            >>> print(f"Agents after execution: {task.assigned_agents}")
            >>>
            >>> # Task now tracks all agents that worked on it
            >>> print(f"\nTotal agents used: {len(task.assigned_agents)}")
            >>> for agent_id in task.assigned_agents:
            ...     agent = manager.get_agent(agent_id)
            ...     print(f"  - {agent.config.name} ({agent.config.role.value})")
            Agents before execution: []
            Agents after execution: ['uuid-1', 'uuid-2', 'uuid-3', 'uuid-4', 'uuid-5']

            Total agents used: 5
              - Analyst Agent (analyst)
              - Planner Agent (planner)
              - Builder Agent (builder)
              - Tester Agent (tester)
              - Reviewer Agent (reviewer)

            Files produced by sequential workflow:

            >>> task = planner.plan_task(
            ...     task_id="seq-007",
            ...     description="Implement user authentication",
            ...     task_type="feature_implementation"
            ... )
            >>> results = await executor.execute_sequential(task)
            >>>
            >>> # Collect all artifacts produced across the pipeline
            >>> all_artifacts = []
            >>> for result in results:
            ...     all_artifacts.extend(result.artifacts)
            >>>
            >>> print(f"Total files produced: {len(all_artifacts)}")
            >>> for file in set(all_artifacts):
            ...     print(f"  - {file}")
            Total files produced: 6
              - src/auth/service.py
              - src/auth/models.py
              - src/auth/routes.py
              - tests/test_auth.py
              - tests/test_auth_integration.py
              - docs/auth_api.md

            Output passing between agents in detail:

            >>> # Create minimal task for demonstration
            >>> from orchestrator.core.types import OrchestratorTask, AgentRole
            >>> task = OrchestratorTask(
            ...     task_id="demo-seq",
            ...     description="Demonstrate output passing",
            ...     subtasks=[
            ...         {"role": AgentRole.ANALYST, "description": "Analyze the problem"},
            ...         {"role": AgentRole.BUILDER, "description": "Build the solution"},
            ...     ]
            ... )
            >>>
            >>> results = await executor.execute_sequential(task)
            >>>
            >>> # The Builder agent received Analyst's output in its prompt:
            >>> # "Build the solution\n\nPrevious agent output:\n{analyst_output}"
            >>> print(f"Step 1 output length: {len(results[0].output)} chars")
            >>> print(f"Step 2 received context with previous output")
            Step 1 output length: 452 chars
            Step 2 received context with previous output

            Comparing sequential vs parallel:

            >>> # Sequential: agents execute one after another
            >>> # - Each agent sees previous outputs
            >>> # - Execution time = sum of all agent times
            >>> # - Use for dependent tasks (plan → build → test → review)
            >>>
            >>> task = planner.plan_task(
            ...     task_id="comparison",
            ...     description="Add feature",
            ...     task_type="feature_implementation"
            ... )
            >>>
            >>> import time
            >>> start = time.time()
            >>> results = await executor.execute_sequential(task)
            >>> duration = time.time() - start
            >>>
            >>> print(f"Sequential execution:")
            >>> print(f"  - Agents: {len(results)}")
            >>> print(f"  - Total time: {duration:.1f}s (cumulative)")
            >>> print(f"  - Output passing: Yes (agent 2 sees agent 1 output)")
            Sequential execution:
              - Agents: 5
              - Total time: 74.3s (cumulative)
              - Output passing: Yes (agent 2 sees agent 1 output)
        """
        results = []
        previous_context: Optional[AgentContext] = None

        for i, subtask in enumerate(task.subtasks):
            # Create progress callback for this agent
            def make_progress_callback(agent_id: str, agent_name: str, agent_role: str) -> Callable[[str, str], Awaitable[None]]:
                """Create a progress callback for an agent."""
                async def progress_callback(event: str, data: str) -> None:
                    if not self.progress_tracker:
                        return

                    # Helper to call method and await if it's a coroutine
                    async def call_method(method: Any, *args: Any) -> None:
                        result = method(*args)
                        if inspect.iscoroutine(result):
                            await result

                    if event == "started":
                        await call_method(self.progress_tracker.agent_created, agent_id, agent_name, agent_role)
                        await call_method(self.progress_tracker.agent_started, agent_id)
                    elif event == "thinking":
                        await call_method(self.progress_tracker.thinking, agent_id)
                    elif event == "tool_call":
                        await call_method(self.progress_tracker.tool_call, agent_id, data)
                    elif event == "completed":
                        # Will update with cost after task completes
                        pass
                    elif event == "failed":
                        await call_method(self.progress_tracker.agent_failed, agent_id, data)

                return progress_callback

            # Create specialized agent for this subtask
            agent = await self.agent_manager.create_specialized_agent(
                role=subtask["role"],
                task_context=subtask.get("context", ""),
                constraints=subtask.get("constraints", []),
                task_id=task.task_id,
            )

            # Set up progress callback
            if self.progress_tracker:
                agent.progress_callback = make_progress_callback(
                    agent.agent_id,
                    agent.config.name,
                    agent.config.role.value
                )

            task.assigned_agents.append(agent.agent_id)

            # Build task prompt, including previous context if available
            task_prompt = subtask["description"]
            if previous_context:
                # Pass minimal forward context instead of full output
                forward_context = previous_context.get_forward_context()
                if forward_context:
                    task_prompt += f"\n\n{forward_context}"

            # Execute task
            result = await agent.execute_task(task_prompt)
            results.append(result)

            # Log completion
            await self.monitor.log_task_completed(agent, subtask["description"])

            # Update progress tracker with completion and cost
            if self.progress_tracker:
                self.progress_tracker.agent_completed(agent.agent_id, agent.metrics.total_cost)

            # Extract structured context from agent output
            if result.success and result.output:
                agent_context = extract_structured_output(
                    result.output,
                    subtask["role"].value
                )
                # Store for potential feedback loops or non-sequential access
                self.agent_contexts[agent.agent_id] = agent_context
                # Pass to next agent
                previous_context = agent_context
            else:
                # On failure, clear context
                previous_context = None

            # Cleanup if specified (default: keep until workflow complete)
            # This demonstrates the CRUD pattern - agents are temporary

        return results

    async def execute_parallel(
        self,
        task: OrchestratorTask,
    ) -> List[TaskResult]:
        """
        Execute subtasks in parallel for maximum throughput.

        Deploys multiple agents simultaneously to work independently on
        different aspects of the same task. This is the key to scaling
        compute power - N agents can do N times the work in the same time.

        Args:
            task: Orchestrator task with parallel subtasks

        Returns:
            List of TaskResult objects from all agents in the same order as
            subtasks. Results arrive when all agents complete (asyncio.gather).

        Examples:
            Basic parallel workflow execution:

            >>> from orchestrator.workflow.executor import WorkflowExecutor
            >>> from orchestrator.workflow.planner import TaskPlanner
            >>> from orchestrator.core.agent_manager import AgentManager
            >>> from orchestrator.observability.monitor import AgentMonitor
            >>> from orchestrator.core.types import AgentRole
            >>>
            >>> # Setup components
            >>> manager = AgentManager(working_directory="/path/to/project")
            >>> monitor = AgentMonitor()
            >>> executor = WorkflowExecutor(agent_manager=manager, monitor=monitor)
            >>> planner = TaskPlanner()
            >>>
            >>> # Create parallel task plan
            >>> task = planner.plan_parallel_tasks(
            ...     task_id="par-001",
            ...     description="Analyze different modules for optimization",
            ...     agent_roles=[AgentRole.ANALYST, AgentRole.ANALYST, AgentRole.ANALYST]
            ... )
            >>>
            >>> # Execute in parallel - all agents run simultaneously
            >>> results = await executor.execute_parallel(task)
            >>>
            >>> print(f"Completed {len(results)} parallel tasks")
            >>> for i, result in enumerate(results, 1):
            ...     print(f"{i}. Agent {result.agent_id[:8]}: {result.success}")
            Completed 3 parallel tasks
            1. Agent abc12345: True
            2. Agent def67890: True
            3. Agent ghi13579: True

            Performance benefits of parallel execution:

            >>> import time
            >>> from orchestrator.core.types import OrchestratorTask, AgentRole
            >>>
            >>> # Create task with 4 independent analysis subtasks
            >>> task = OrchestratorTask(
            ...     task_id="perf-001",
            ...     description="Analyze codebase",
            ...     subtasks=[
            ...         {"role": AgentRole.ANALYST, "description": "Analyze frontend code"},
            ...         {"role": AgentRole.ANALYST, "description": "Analyze backend code"},
            ...         {"role": AgentRole.ANALYST, "description": "Analyze database queries"},
            ...         {"role": AgentRole.ANALYST, "description": "Analyze test coverage"},
            ...     ]
            ... )
            >>>
            >>> # Execute in parallel
            >>> start = time.time()
            >>> results = await executor.execute_parallel(task)
            >>> parallel_time = time.time() - start
            >>>
            >>> # If each agent takes ~20s, sequential would be 80s
            >>> # Parallel completes in ~20s (the slowest agent)
            >>> print(f"Parallel execution: {parallel_time:.1f}s")
            >>> print(f"Sequential would take: ~{len(results) * 20}s")
            >>> print(f"Speedup: {len(results)}x faster")
            Parallel execution: 22.3s
            Sequential would take: ~80s
            Speedup: 4x faster

            Independent agents working on different codebases:

            >>> # Create specialized agents for different parts of a monorepo
            >>> task = OrchestratorTask(
            ...     task_id="monorepo-001",
            ...     description="Upgrade dependencies across all services",
            ...     subtasks=[
            ...         {
            ...             "role": AgentRole.BUILDER,
            ...             "description": "Upgrade frontend dependencies",
            ...             "context": "Work in /frontend directory"
            ...         },
            ...         {
            ...             "role": AgentRole.BUILDER,
            ...             "description": "Upgrade backend dependencies",
            ...             "context": "Work in /backend directory"
            ...         },
            ...         {
            ...             "role": AgentRole.BUILDER,
            ...             "description": "Upgrade mobile dependencies",
            ...             "context": "Work in /mobile directory"
            ...         },
            ...     ]
            ... )
            >>>
            >>> results = await executor.execute_parallel(task)
            >>>
            >>> # Each agent worked independently in different directories
            >>> for result in results:
            ...     print(f"{result.task_description}: {len(result.artifacts)} files")
            Upgrade frontend dependencies: 3 files
            Upgrade backend dependencies: 5 files
            Upgrade mobile dependencies: 2 files

            Parallel document generation:

            >>> # Generate multiple documentation files simultaneously
            >>> task = planner.plan_parallel_tasks(
            ...     task_id="docs-001",
            ...     description="Generate comprehensive documentation",
            ...     agent_roles=[
            ...         AgentRole.DOCUMENTER,  # API docs
            ...         AgentRole.DOCUMENTER,  # User guide
            ...         AgentRole.DOCUMENTER,  # Architecture docs
            ...         AgentRole.DOCUMENTER,  # Contributing guide
            ...     ]
            ... )
            >>>
            >>> # All documentation written in parallel
            >>> results = await executor.execute_parallel(task)
            >>>
            >>> all_docs = []
            >>> for result in results:
            ...     all_docs.extend(result.artifacts)
            >>>
            >>> print(f"Generated {len(all_docs)} documentation files in parallel")
            >>> for doc in all_docs:
            ...     print(f"  - {doc}")
            Generated 4 documentation files in parallel
              - docs/api_reference.md
              - docs/user_guide.md
              - docs/architecture.md
              - docs/CONTRIBUTING.md

            Error handling in parallel execution:

            >>> task = planner.plan_parallel_tasks(
            ...     task_id="err-001",
            ...     description="Complex parallel tasks",
            ...     agent_roles=[AgentRole.BUILDER, AgentRole.BUILDER, AgentRole.BUILDER]
            ... )
            >>>
            >>> # Execute - some agents may fail but others continue
            >>> results = await executor.execute_parallel(task)
            >>>
            >>> # Check results for failures
            >>> success_count = sum(1 for r in results if r.success)
            >>> failure_count = len(results) - success_count
            >>>
            >>> print(f"Successful: {success_count}/{len(results)}")
            >>> print(f"Failed: {failure_count}/{len(results)}")
            >>>
            >>> # Inspect failures
            >>> for i, result in enumerate(results):
            ...     if not result.success:
            ...         print(f"Agent {i+1} failed: {result.error}")
            Successful: 2/3
            Failed: 1/3
            Agent 2 failed: Compilation error in generated code

            Collecting aggregated metrics from parallel execution:

            >>> task = planner.plan_parallel_tasks(
            ...     task_id="metrics-001",
            ...     description="Parallel analysis tasks",
            ...     agent_roles=[AgentRole.ANALYST] * 5
            ... )
            >>>
            >>> results = await executor.execute_parallel(task)
            >>>
            >>> # Aggregate metrics across all parallel agents
            >>> total_tokens = sum(r.metrics.total_tokens for r in results)
            >>> total_cost = sum(r.metrics.total_cost for r in results)
            >>> max_time = max(r.metrics.execution_time_seconds for r in results)
            >>> avg_time = sum(r.metrics.execution_time_seconds for r in results) / len(results)
            >>>
            >>> print(f"Total tokens used: {total_tokens:,}")
            >>> print(f"Total cost: ${total_cost:.4f}")
            >>> print(f"Longest agent: {max_time:.1f}s")
            >>> print(f"Average agent: {avg_time:.1f}s")
            Total tokens used: 142,350
            Total cost: $0.2156
            Longest agent: 18.3s
            Average agent: 15.7s

            Parallel testing across different test suites:

            >>> # Run different test suites in parallel
            >>> task = OrchestratorTask(
            ...     task_id="test-001",
            ...     description="Run all test suites",
            ...     subtasks=[
            ...         {"role": AgentRole.TESTER, "description": "Run unit tests"},
            ...         {"role": AgentRole.TESTER, "description": "Run integration tests"},
            ...         {"role": AgentRole.TESTER, "description": "Run e2e tests"},
            ...         {"role": AgentRole.TESTER, "description": "Run performance tests"},
            ...     ]
            ... )
            >>>
            >>> results = await executor.execute_parallel(task)
            >>>
            >>> # Check test results
            >>> for result in results:
            ...     status = "✓" if result.success else "✗"
            ...     suite = result.task_description.replace("Run ", "")
            ...     print(f"{status} {suite}")
            ✓ unit tests
            ✓ integration tests
            ✓ e2e tests
            ✗ performance tests

            Parallel code review of multiple PRs:

            >>> # Review multiple pull requests simultaneously
            >>> task = OrchestratorTask(
            ...     task_id="review-batch",
            ...     description="Review multiple PRs",
            ...     subtasks=[
            ...         {"role": AgentRole.REVIEWER, "description": "Review PR #101"},
            ...         {"role": AgentRole.REVIEWER, "description": "Review PR #102"},
            ...         {"role": AgentRole.REVIEWER, "description": "Review PR #103"},
            ...     ]
            ... )
            >>>
            >>> results = await executor.execute_parallel(task)
            >>>
            >>> print(f"Reviewed {len(results)} PRs in parallel")
            >>> for i, result in enumerate(results, 101):
            ...     print(f"PR #{i}: {result.output[:60]}...")
            Reviewed 3 PRs in parallel
            PR #101: Code quality looks good. Suggested 2 minor improvements...
            PR #102: Found security issue in authentication logic. Must fix...
            PR #103: Well-tested changes. Approved for merge...

            Mixed roles working in parallel:

            >>> # Different agent types working on the same overall task
            >>> task = OrchestratorTask(
            ...     task_id="mixed-001",
            ...     description="Full-stack feature development",
            ...     subtasks=[
            ...         {"role": AgentRole.BUILDER, "description": "Build backend API"},
            ...         {"role": AgentRole.BUILDER, "description": "Build frontend UI"},
            ...         {"role": AgentRole.DOCUMENTER, "description": "Write API docs"},
            ...         {"role": AgentRole.TESTER, "description": "Write test plan"},
            ...     ]
            ... )
            >>>
            >>> results = await executor.execute_parallel(task)
            >>>
            >>> # All aspects developed simultaneously
            >>> print("Parallel work completed:")
            >>> for result in results:
            ...     print(f"  - {result.task_description}: {len(result.artifacts)} artifacts")
            Parallel work completed:
              - Build backend API: 4 artifacts
              - Build frontend UI: 6 artifacts
              - Write API docs: 1 artifacts
              - Write test plan: 2 artifacts

            Tracking agent assignments in parallel execution:

            >>> task = planner.plan_parallel_tasks(
            ...     task_id="track-001",
            ...     description="Parallel feature work",
            ...     agent_roles=[AgentRole.BUILDER] * 3
            ... )
            >>>
            >>> print(f"Agents before: {len(task.assigned_agents)}")
            >>> results = await executor.execute_parallel(task)
            >>> print(f"Agents after: {len(task.assigned_agents)}")
            >>>
            >>> # All agents assigned at once, execute simultaneously
            >>> for agent_id in task.assigned_agents:
            ...     agent = manager.get_agent(agent_id)
            ...     print(f"  - {agent_id[:8]}: {agent.status.value}")
            Agents before: 0
            Agents after: 3
              - uuid-1ab: completed
              - uuid-2cd: completed
              - uuid-3ef: completed

            Comparing parallel vs sequential execution:

            >>> # Same task executed both ways for comparison
            >>> task_seq = planner.plan_task(
            ...     task_id="compare-seq",
            ...     description="Analyze codebase",
            ...     task_type="feature_implementation"  # 5 sequential steps
            ... )
            >>>
            >>> task_par = planner.plan_parallel_tasks(
            ...     task_id="compare-par",
            ...     description="Analyze codebase",
            ...     agent_roles=[AgentRole.ANALYST] * 5  # 5 parallel agents
            ... )
            >>>
            >>> import time
            >>>
            >>> # Sequential execution
            >>> start = time.time()
            >>> seq_results = await executor.execute_sequential(task_seq)
            >>> seq_time = time.time() - start
            >>>
            >>> # Parallel execution
            >>> start = time.time()
            >>> par_results = await executor.execute_parallel(task_par)
            >>> par_time = time.time() - start
            >>>
            >>> print("Comparison:")
            >>> print(f"Sequential: {seq_time:.1f}s (sum of all agent times)")
            >>> print(f"Parallel:   {par_time:.1f}s (slowest agent time)")
            >>> print(f"Speedup:    {seq_time/par_time:.1f}x faster with parallel")
            >>>
            >>> print("\nSequential: agents share context (output passing)")
            >>> print("Parallel:   agents work independently (no context sharing)")
            Comparison:
            Sequential: 74.3s (sum of all agent times)
            Parallel:   18.7s (slowest agent time)
            Speedup:    4.0x faster with parallel

            Sequential: agents share context (output passing)
            Parallel:   agents work independently (no context sharing)

            Cost efficiency with parallel execution:

            >>> # Parallel execution doesn't increase cost, just reduces time
            >>> task = planner.plan_parallel_tasks(
            ...     task_id="cost-001",
            ...     description="Multiple independent tasks",
            ...     agent_roles=[AgentRole.ANALYST] * 4
            ... )
            >>>
            >>> results = await executor.execute_parallel(task)
            >>>
            >>> # Each agent has independent cost
            >>> for i, result in enumerate(results, 1):
            ...     print(f"Agent {i}: ${result.metrics.total_cost:.4f}")
            >>>
            >>> total_cost = sum(r.metrics.total_cost for r in results)
            >>> print(f"\nTotal cost: ${total_cost:.4f}")
            >>> print("Note: Same total cost as sequential, but much faster!")
            Agent 1: $0.0234
            Agent 2: $0.0198
            Agent 3: $0.0256
            Agent 4: $0.0212

            Total cost: $0.0900
            Note: Same total cost as sequential, but much faster!

            When to use parallel execution:

            >>> # Parallel is ideal for:
            >>> # 1. Independent tasks (no dependencies between agents)
            >>> # 2. Same operation on different data/files
            >>> # 3. Time-sensitive tasks needing fast completion
            >>> # 4. Embarrassingly parallel problems
            >>>
            >>> # Sequential is ideal for:
            >>> # 1. Dependent tasks (output of one feeds into next)
            >>> # 2. Workflows requiring shared context
            >>> # 3. Tasks following a logical pipeline
            >>> # 4. When order matters (analyze → plan → build → test → review)
        """
        # Create progress callback function
        def make_progress_callback(agent_id: str, agent_name: str, agent_role: str) -> Callable[[str, str], Awaitable[None]]:
            """Create a progress callback for an agent."""
            async def progress_callback(event: str, data: str) -> None:
                if not self.progress_tracker:
                    return

                # Helper to call method and await if it's a coroutine
                async def call_method(method: Any, *args: Any) -> None:
                    result = method(*args)
                    if inspect.iscoroutine(result):
                        await result

                if event == "started":
                    await call_method(self.progress_tracker.agent_created, agent_id, agent_name, agent_role)
                    await call_method(self.progress_tracker.agent_started, agent_id)
                elif event == "thinking":
                    await call_method(self.progress_tracker.thinking, agent_id)
                elif event == "tool_call":
                    await call_method(self.progress_tracker.tool_call, agent_id, data)
                elif event == "completed":
                    # Will update with cost after task completes
                    pass
                elif event == "failed":
                    await call_method(self.progress_tracker.agent_failed, agent_id, data)

            return progress_callback

        # Create all agents
        agents = []
        for subtask in task.subtasks:
            agent = await self.agent_manager.create_specialized_agent(
                role=subtask["role"],
                task_context=subtask.get("context", ""),
                constraints=subtask.get("constraints", []),
                task_id=task.task_id,
            )

            # Set up progress callback
            if self.progress_tracker:
                agent.progress_callback = make_progress_callback(
                    agent.agent_id,
                    agent.config.name,
                    agent.config.role.value
                )

            agents.append((agent, subtask))
            task.assigned_agents.append(agent.agent_id)

        # Execute all tasks in parallel
        tasks_to_execute = [
            agent.execute_task(subtask["description"])
            for agent, subtask in agents
        ]

        results = await asyncio.gather(*tasks_to_execute, return_exceptions=True)

        # Process results and log
        processed_results: List[TaskResult] = []
        for (agent, subtask), result in zip(agents, results):
            if isinstance(result, Exception):
                await self.monitor.log_error(agent, str(result))
                # Create failed result
                task_result = TaskResult(
                    agent_id=agent.agent_id,
                    task_description=subtask["description"],
                    success=False,
                    output=None,
                    error=str(result),
                    metrics=agent.metrics,
                )
                processed_results.append(task_result)
            else:
                # Type narrowing: result is TaskResult here (not BaseException)
                await self.monitor.log_task_completed(agent, subtask["description"])

                # Update progress tracker with completion and cost
                if self.progress_tracker:
                    self.progress_tracker.agent_completed(agent.agent_id, agent.metrics.total_cost)

                processed_results.append(cast(TaskResult, result))

        return processed_results

    async def execute_with_dependencies(
        self,
        task: OrchestratorTask,
        dependencies: Dict[int, List[int]],
    ) -> List[TaskResult]:
        """
        Execute subtasks respecting dependencies.

        Args:
            task: Orchestrator task
            dependencies: Dict mapping subtask index to list of prerequisite indices

        Returns:
            List of results in execution order
        """
        results: Dict[int, TaskResult] = {}
        contexts: Dict[int, AgentContext] = {}
        completed = set()

        async def execute_subtask(index: int) -> TaskResult:
            subtask = task.subtasks[index]

            # Wait for dependencies
            deps = dependencies.get(index, [])
            while not all(d in completed for d in deps):
                await asyncio.sleep(0.1)

            # Gather structured contexts from dependencies
            dep_contexts = []
            for dep_idx in deps:
                if dep_idx in contexts:
                    dep_contexts.append(contexts[dep_idx].get_forward_context())

            # Create agent
            agent = await self.agent_manager.create_specialized_agent(
                role=subtask["role"],
                task_context=subtask.get("context", ""),
                constraints=subtask.get("constraints", []),
                task_id=task.task_id,
            )
            task.assigned_agents.append(agent.agent_id)

            # Build prompt with dependency contexts (not full outputs)
            task_prompt = subtask["description"]
            if dep_contexts:
                task_prompt += "\n\nContext from previous tasks:\n"
                task_prompt += "\n\n".join(dep_contexts)

            # Execute
            result = await agent.execute_task(task_prompt)
            results[index] = result
            completed.add(index)

            # Extract structured context
            if result.success and result.output:
                agent_context = extract_structured_output(
                    result.output,
                    subtask["role"].value
                )
                contexts[index] = agent_context
                self.agent_contexts[agent.agent_id] = agent_context

            await self.monitor.log_task_completed(agent, subtask["description"])

            return result

        # Execute all subtasks respecting dependencies
        execution_tasks = [
            execute_subtask(i)
            for i in range(len(task.subtasks))
        ]

        await asyncio.gather(*execution_tasks)

        # Return results in order
        return [results[i] for i in range(len(task.subtasks))]

    async def cleanup_workflow_agents(self, task: OrchestratorTask) -> int:
        """
        Cleanup all agents created for a workflow.

        Demonstrates the CRUD delete pattern - free resources after completion.

        Args:
            task: Task whose agents should be cleaned up

        Returns:
            Number of agents deleted
        """
        count = 0
        for agent_id in task.assigned_agents:
            if await self.agent_manager.delete_agent(agent_id):
                count += 1

        return count
