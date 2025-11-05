"""Workflow execution engine."""

import asyncio
from typing import Dict, List, Any
from orchestrator.core.agent_manager import AgentManager
from orchestrator.core.types import OrchestratorTask, AgentStatus, TaskResult
from orchestrator.observability.monitor import AgentMonitor


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
    ):
        self.agent_manager = agent_manager
        self.monitor = monitor

    async def execute_sequential(
        self,
        task: OrchestratorTask,
    ) -> List[TaskResult]:
        """
        Execute subtasks sequentially.

        Each agent passes its results to the next agent in the chain.

        Args:
            task: Orchestrator task with subtasks

        Returns:
            List of results from each subtask
        """
        results = []
        previous_output = None

        for i, subtask in enumerate(task.subtasks):
            # Create specialized agent for this subtask
            agent = await self.agent_manager.create_specialized_agent(
                role=subtask["role"],
                task_context=subtask.get("context", ""),
            )

            task.assigned_agents.append(agent.agent_id)

            # Build task prompt, including previous output if available
            task_prompt = subtask["description"]
            if previous_output:
                task_prompt += f"\n\nPrevious agent output:\n{previous_output}"

            # Execute task
            result = await agent.execute_task(task_prompt)
            results.append(result)

            # Log completion
            await self.monitor.log_task_completed(agent, subtask["description"])

            # Pass output to next agent
            previous_output = result.output

            # Cleanup if specified (default: keep until workflow complete)
            # This demonstrates the CRUD pattern - agents are temporary

        return results

    async def execute_parallel(
        self,
        task: OrchestratorTask,
    ) -> List[TaskResult]:
        """
        Execute subtasks in parallel.

        Deploys multiple agents simultaneously - key to scaling compute.

        Args:
            task: Orchestrator task with parallel subtasks

        Returns:
            List of results from all parallel tasks
        """
        # Create all agents
        agents = []
        for subtask in task.subtasks:
            agent = await self.agent_manager.create_specialized_agent(
                role=subtask["role"],
                task_context=subtask.get("context", ""),
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
        processed_results = []
        for (agent, subtask), result in zip(agents, results):
            if isinstance(result, Exception):
                await self.monitor.log_error(agent, str(result))
                # Create failed result
                result = TaskResult(
                    agent_id=agent.agent_id,
                    task_description=subtask["description"],
                    success=False,
                    output=None,
                    error=str(result),
                    metrics=agent.metrics,
                )
            else:
                await self.monitor.log_task_completed(agent, subtask["description"])

            processed_results.append(result)

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
        completed = set()

        async def execute_subtask(index: int) -> TaskResult:
            subtask = task.subtasks[index]

            # Wait for dependencies
            deps = dependencies.get(index, [])
            while not all(d in completed for d in deps):
                await asyncio.sleep(0.1)

            # Gather outputs from dependencies
            dep_outputs = [results[d].output for d in deps if d in results]

            # Create agent
            agent = await self.agent_manager.create_specialized_agent(
                role=subtask["role"],
                task_context=subtask.get("context", ""),
            )
            task.assigned_agents.append(agent.agent_id)

            # Build prompt with dependency outputs
            task_prompt = subtask["description"]
            if dep_outputs:
                task_prompt += "\n\nInputs from previous tasks:\n"
                task_prompt += "\n\n".join(dep_outputs)

            # Execute
            result = await agent.execute_task(task_prompt)
            results[index] = result
            completed.add(index)

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
