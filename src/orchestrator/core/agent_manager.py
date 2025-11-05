"""Agent lifecycle management with CRUD operations."""

import uuid
from typing import Any, Callable, Dict, List, Optional

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
    ) -> None:
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
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        working_directory: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        permission_mode: str = "bypassPermissions",
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ) -> Agent:
        """
        Create a new agent with custom configuration.

        This is the core CREATE operation in the agent lifecycle CRUD pattern.
        Each agent is independent with its own context, model, and tools.

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
            Created Agent instance with unique ID and configured settings

        Examples:
            Basic custom agent creation:

            >>> from orchestrator.core.agent_manager import AgentManager
            >>> from orchestrator.core.types import AgentRole
            >>>
            >>> manager = AgentManager(working_directory="/path/to/project")
            >>>
            >>> # Create a simple custom agent
            >>> agent = await manager.create_agent(
            ...     name="Code Analyzer",
            ...     role=AgentRole.ANALYST,
            ...     system_prompt="You analyze code for performance issues."
            ... )
            >>>
            >>> print(f"Created agent: {agent.agent_id}")
            >>> print(f"Role: {agent.config.role.value}")
            >>> print(f"Model: {agent.config.model}")
            Created agent: abc123-def-456-789
            Role: analyst
            Model: claude-sonnet-4-5-20250929

            Advanced configuration with specific model and settings:

            >>> # Create agent with Opus model for complex reasoning
            >>> senior_reviewer = await manager.create_agent(
            ...     name="Senior Code Reviewer",
            ...     role=AgentRole.REVIEWER,
            ...     model="claude-opus-4-20250514",
            ...     system_prompt='''You are a senior code reviewer with expertise in:
            ...     - Security vulnerabilities
            ...     - Performance optimization
            ...     - Design patterns and architecture
            ...     - Best practices across Python, Go, and TypeScript
            ...
            ...     Provide detailed, actionable feedback.''',
            ...     max_tokens=16384,  # Larger context for detailed reviews
            ...     temperature=0.7,    # Lower temperature for consistency
            ...     metadata={"expertise": "security", "seniority": "senior"}
            ... )
            >>>
            >>> print(f"Reviewer configured with {senior_reviewer.config.max_tokens} tokens")
            Reviewer configured with 16384 tokens

            Fast agent with Haiku model for simple tasks:

            >>> # Use Haiku for quick, simple tasks to reduce cost
            >>> quick_analyzer = await manager.create_agent(
            ...     name="Quick File Scanner",
            ...     role=AgentRole.ANALYST,
            ...     model="claude-haiku-4-20250514",
            ...     system_prompt="Quickly scan files and count lines of code.",
            ...     max_tokens=4096,
            ...     temperature=1.0
            ... )
            >>>
            >>> # Haiku is ~20x cheaper and faster for simple tasks
            >>> print(f"Quick analyzer: {quick_analyzer.config.name}")
            Quick analyzer: Quick File Scanner

            Tool-restricted agent for security:

            >>> # Create agent with restricted tool access
            >>> read_only_agent = await manager.create_agent(
            ...     name="Read-Only Auditor",
            ...     role=AgentRole.REVIEWER,
            ...     system_prompt="Review code but never modify files.",
            ...     allowed_tools=["Read", "Glob", "Grep"],  # No Write or Edit
            ...     permission_mode="bypassPermissions",
            ...     metadata={"permissions": "read-only"}
            ... )
            >>>
            >>> # This agent can only read, not write
            >>> print(f"Allowed tools: {read_only_agent.config.allowed_tools}")
            Allowed tools: ['Read', 'Glob', 'Grep']

            Agent with custom working directory:

            >>> # Create agent working in specific subdirectory
            >>> frontend_builder = await manager.create_agent(
            ...     name="Frontend Builder",
            ...     role=AgentRole.BUILDER,
            ...     system_prompt="Build React components following our style guide.",
            ...     working_directory="/path/to/project/frontend",
            ...     metadata={"focus": "react", "layer": "frontend"}
            ... )
            >>>
            >>> print(f"Working in: {frontend_builder.config.working_directory}")
            Working in: /path/to/project/frontend

            Multiple specialized agents for parallel work:

            >>> # Create multiple agents for different tasks
            >>> agents = []
            >>>
            >>> # Backend specialist
            >>> backend_agent = await manager.create_agent(
            ...     name="Backend Engineer",
            ...     role=AgentRole.BUILDER,
            ...     system_prompt="Expert in Python, FastAPI, and SQLAlchemy.",
            ...     working_directory="/path/to/project/backend",
            ...     metadata={"specialty": "backend"}
            ... )
            >>> agents.append(backend_agent)
            >>>
            >>> # Frontend specialist
            >>> frontend_agent = await manager.create_agent(
            ...     name="Frontend Engineer",
            ...     role=AgentRole.BUILDER,
            ...     system_prompt="Expert in React, TypeScript, and Tailwind.",
            ...     working_directory="/path/to/project/frontend",
            ...     metadata={"specialty": "frontend"}
            ... )
            >>> agents.append(frontend_agent)
            >>>
            >>> # DevOps specialist
            >>> devops_agent = await manager.create_agent(
            ...     name="DevOps Engineer",
            ...     role=AgentRole.BUILDER,
            ...     system_prompt="Expert in Docker, K8s, and CI/CD.",
            ...     working_directory="/path/to/project",
            ...     metadata={"specialty": "devops"}
            ... )
            >>> agents.append(devops_agent)
            >>>
            >>> print(f"Created {len(agents)} specialized agents")
            >>> for agent in agents:
            ...     print(f"  - {agent.config.name}: {agent.config.metadata['specialty']}")
            Created 3 specialized agents
              - Backend Engineer: backend
              - Frontend Engineer: frontend
              - DevOps Engineer: devops

            Agent with custom tools configuration:

            >>> # Create agent with specific tools
            >>> custom_tools = [
            ...     {
            ...         "name": "database_query",
            ...         "description": "Query the database",
            ...         "parameters": {"query": "string"}
            ...     }
            ... ]
            >>>
            >>> db_agent = await manager.create_agent(
            ...     name="Database Agent",
            ...     role=AgentRole.ANALYST,
            ...     system_prompt="Analyze database performance and queries.",
            ...     tools=custom_tools,
            ...     metadata={"database": "postgresql"}
            ... )
            >>>
            >>> print(f"Agent has {len(db_agent.config.tools)} custom tools")
            Agent has 1 custom tools

            Temperature settings for different use cases:

            >>> # Low temperature (0.3-0.7) for deterministic tasks
            >>> code_generator = await manager.create_agent(
            ...     name="Code Generator",
            ...     role=AgentRole.BUILDER,
            ...     system_prompt="Generate boilerplate code following strict patterns.",
            ...     temperature=0.3,  # Very deterministic
            ...     metadata={"task": "code-generation"}
            ... )
            >>>
            >>> # High temperature (1.0-1.5) for creative tasks
            >>> creative_writer = await manager.create_agent(
            ...     name="Documentation Writer",
            ...     role=AgentRole.DOCUMENTER,
            ...     system_prompt="Write engaging, creative documentation.",
            ...     temperature=1.0,  # More creative
            ...     metadata={"task": "documentation"}
            ... )
            >>>
            >>> print(f"Generator temp: {code_generator.config.temperature}")
            >>> print(f"Writer temp: {creative_writer.config.temperature}")
            Generator temp: 0.3
            Writer temp: 1.0

            Permission modes:

            >>> # Bypass permissions for autonomous operation
            >>> autonomous_agent = await manager.create_agent(
            ...     name="Autonomous Builder",
            ...     role=AgentRole.BUILDER,
            ...     system_prompt="Build features autonomously.",
            ...     permission_mode="bypassPermissions"  # No prompts
            ... )
            >>>
            >>> # Ask permission for supervised operation
            >>> supervised_agent = await manager.create_agent(
            ...     name="Supervised Builder",
            ...     role=AgentRole.BUILDER,
            ...     system_prompt="Build features with oversight.",
            ...     permission_mode="ask"  # Ask before actions
            ... )
            >>>
            >>> print(f"Autonomous: {autonomous_agent.config.permission_mode}")
            >>> print(f"Supervised: {supervised_agent.config.permission_mode}")
            Autonomous: bypassPermissions
            Supervised: ask
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
            progress_callback=progress_callback,
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

    def get_fleet_summary(self) -> Dict[str, Any]:
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
