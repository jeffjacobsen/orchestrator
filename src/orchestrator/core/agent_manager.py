"""Agent lifecycle management with CRUD operations."""

import uuid
from typing import Dict, List, Optional

from orchestrator.core.agent import Agent
from orchestrator.core.types import AgentConfig, AgentStatus, AgentRole
from orchestrator.observability.monitor import AgentMonitor


class AgentManager:
    """
    Manages the full lifecycle of agents with CRUD operations.

    Core Four Management:
    1. Context window - Tracked per agent
    2. Model - Configured per agent
    3. Prompt - System prompt for each agent
    4. Tools - Available tools per agent
    """

    def __init__(
        self,
        working_directory: Optional[str] = None,
        monitor: Optional[AgentMonitor] = None,
    ):
        """
        Initialize AgentManager.

        Note: No API key needed - Claude Code SDK uses CLI authentication.

        Args:
            working_directory: Default working directory for agents
            monitor: Optional AgentMonitor for observability
        """
        self.agents: Dict[str, Agent] = {}
        self.working_directory = working_directory
        self.monitor = monitor

    # CREATE
    async def create_agent(
        self,
        name: str,
        role: AgentRole = AgentRole.CUSTOM,
        model: str = "claude-sonnet-4-5-20250929",
        system_prompt: str = "",
        max_tokens: int = 8192,
        temperature: float = 1.0,
        tools: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None,
        working_directory: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        permission_mode: str = "bypassPermissions",
    ) -> Agent:
        """
        Create a new agent.

        Args:
            name: Human-readable name for the agent
            role: Specialized role (Scout, Builder, Reviewer, etc.)
            model: Claude model to use
            system_prompt: System instructions for the agent
            max_tokens: Max tokens per response
            temperature: Sampling temperature
            tools: Available tools for the agent
            metadata: Additional metadata
            working_directory: Working directory for this agent (overrides manager default)
            allowed_tools: List of allowed tool names for this agent
            permission_mode: Permission mode ("bypassPermissions" or "ask")

        Returns:
            Created Agent instance
        """
        agent_id = str(uuid.uuid4())

        config = AgentConfig(
            name=name,
            role=role,
            model=model,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools or [],
            metadata=metadata or {},
            working_directory=working_directory or self.working_directory,
            allowed_tools=allowed_tools,
            permission_mode=permission_mode,
        )

        agent = Agent(
            agent_id=agent_id,
            config=config,
        )

        self.agents[agent_id] = agent

        # Log to monitor
        if self.monitor:
            await self.monitor.log_agent_created(agent)

        return agent

    async def create_specialized_agent(
        self,
        role: AgentRole,
        task_context: str = "",
        working_directory: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        permission_mode: str = "bypassPermissions",
    ) -> Agent:
        """
        Create an agent with role-specific configuration.

        Args:
            role: The specialized role
            task_context: Additional context for the agent's system prompt
            working_directory: Working directory for this agent (overrides manager default)
            allowed_tools: List of allowed tool names for this agent
            permission_mode: Permission mode ("bypassPermissions" or "ask")

        Returns:
            Created Agent with role-specific configuration
        """
        prompts = {
            AgentRole.PLANNER: """You are a Planner agent specialized in task planning and decomposition.

Your responsibilities:
- Break down complex tasks into manageable subtasks
- Create clear execution plans with dependencies
- Estimate effort and identify potential challenges
- Coordinate between different agent roles

{context}""",
            AgentRole.BUILDER: """You are a Builder agent specialized in implementation and coding.

Your responsibilities:
- Write clean, maintainable code
- Follow existing code patterns and conventions
- Implement features based on specifications
- Focus on correctness and quality

{context}""",
            AgentRole.REVIEWER: """You are a Reviewer agent specialized in code review and quality assurance.

Your responsibilities:
- Review code for bugs, security issues, and best practices
- Provide constructive feedback
- Check for edge cases and error handling
- Ensure code meets quality standards

{context}""",
            AgentRole.ANALYST: """You are an Analyst agent specialized in data analysis and research.

Your responsibilities:
- Analyze data and code to extract insights
- Research solutions and best practices
- Provide data-driven recommendations
- Synthesize information from multiple sources

{context}""",
            AgentRole.TESTER: """You are a Tester agent specialized in testing and validation.

Your responsibilities:
- Write comprehensive tests
- Validate functionality against requirements
- Identify edge cases and failure modes
- Ensure test coverage and quality

{context}""",
            AgentRole.DOCUMENTER: """You are a Documenter agent specialized in documentation.

Your responsibilities:
- Write clear, comprehensive documentation
- Document APIs, functions, and systems
- Create examples and usage guides
- Maintain documentation quality and accuracy

{context}""",
        }

        system_prompt = prompts.get(role, "{context}").format(
            context=task_context if task_context else ""
        )

        return await self.create_agent(
            name=f"{role.value.capitalize()} Agent",
            role=role,
            system_prompt=system_prompt,
            working_directory=working_directory,
            allowed_tools=allowed_tools,
            permission_mode=permission_mode,
        )

    # READ
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(
        self,
        status: Optional[AgentStatus] = None,
        role: Optional[AgentRole] = None,
    ) -> List[Agent]:
        """
        List agents with optional filtering.

        Args:
            status: Filter by agent status
            role: Filter by agent role

        Returns:
            List of matching agents
        """
        agents = list(self.agents.values())

        if status:
            agents = [a for a in agents if a.status == status]

        if role:
            agents = [a for a in agents if a.config.role == role]

        return agents

    def get_active_agents(self) -> List[Agent]:
        """Get all active (non-deleted) agents."""
        return [
            agent
            for agent in self.agents.values()
            if agent.status != AgentStatus.DELETED
        ]

    # UPDATE
    async def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus,
    ) -> bool:
        """
        Update an agent's status.

        Args:
            agent_id: Agent to update
            status: New status

        Returns:
            True if successful
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        old_status = agent.status
        agent.status = status

        if self.monitor:
            await self.monitor.log_status_change(agent, old_status, status)

        return True

    # DELETE
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent and free its resources.

        This is the key to scaling - agents are temporary and deletable.

        Args:
            agent_id: Agent to delete

        Returns:
            True if successful
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        # Cleanup agent resources
        await agent.cleanup()

        # Log deletion
        if self.monitor:
            await self.monitor.log_agent_deleted(agent)

        # Remove from active agents
        del self.agents[agent_id]

        return True

    async def delete_all_agents(self) -> int:
        """
        Delete all agents. Useful for cleanup.

        Returns:
            Number of agents deleted
        """
        agent_ids = list(self.agents.keys())
        count = 0

        for agent_id in agent_ids:
            if await self.delete_agent(agent_id):
                count += 1

        return count

    async def cleanup_completed_agents(self) -> int:
        """
        Delete all completed or failed agents.

        Returns:
            Number of agents deleted
        """
        completed = [
            a.agent_id
            for a in self.agents.values()
            if a.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
        ]

        count = 0
        for agent_id in completed:
            if await self.delete_agent(agent_id):
                count += 1

        return count

    # METRICS AND OBSERVABILITY
    def get_total_cost(self) -> float:
        """Get total cost across all agents."""
        return sum(agent.metrics.total_cost for agent in self.agents.values())

    def get_total_tokens(self) -> int:
        """Get total tokens used across all agents."""
        return sum(agent.metrics.total_tokens for agent in self.agents.values())

    def get_fleet_summary(self) -> Dict:
        """
        Get a summary of the entire agent fleet.

        Returns:
            Dict with fleet statistics
        """
        agents = list(self.agents.values())
        active_agents = self.get_active_agents()

        return {
            "total_agents": len(agents),
            "active_agents": len(active_agents),
            "by_status": {
                status.value: len([a for a in agents if a.status == status])
                for status in AgentStatus
            },
            "by_role": {
                role.value: len([a for a in agents if a.config.role == role])
                for role in AgentRole
            },
            "total_cost": f"${self.get_total_cost():.4f}",
            "total_tokens": self.get_total_tokens(),
        }
