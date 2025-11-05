"""Real-time agent monitoring."""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone

from orchestrator.core.agent import Agent
from orchestrator.core.types import AgentStatus
from orchestrator.observability.logger import StructuredLogger
from orchestrator.observability.metrics import MetricsCollector


class AgentMonitor:
    """
    Real-time monitoring of agent fleet.

    Provides observability into:
    - Agent status and progress
    - Cost and performance metrics
    - Files consumed vs produced
    - Tool usage and errors
    """

    def __init__(
        self,
        logger: Optional[StructuredLogger] = None,
        metrics: Optional[MetricsCollector] = None,
    ) -> None:
        self.logger = logger or StructuredLogger()
        self.metrics = metrics or MetricsCollector()
        self.status_callbacks: List[Callable[..., Any]] = []
        self.monitoring = False

    async def log_agent_created(self, agent: Agent) -> None:
        """Log agent creation."""
        self.logger.info(
            "agent_created",
            agent_id=agent.agent_id,
            name=agent.config.name,
            role=agent.config.role.value,
            model=agent.config.model,
        )

        self.metrics.record_event("agent_created", {
            "agent_id": agent.agent_id,
            "name": agent.config.name,
            "role": agent.config.role.value,
        })

    async def log_agent_deleted(self, agent: Agent) -> None:
        """Log agent deletion."""
        self.logger.info(
            "agent_deleted",
            agent_id=agent.agent_id,
            name=agent.config.name,
            total_cost=agent.metrics.total_cost,
            total_tokens=agent.metrics.total_tokens,
        )

        self.metrics.record_event("agent_deleted", {
            "agent_id": agent.agent_id,
            "metrics": agent.metrics.model_dump(),
        })

    async def log_status_change(
        self,
        agent: Agent,
        old_status: AgentStatus,
        new_status: AgentStatus,
    ) -> None:
        """Log status change."""
        self.logger.info(
            "agent_status_changed",
            agent_id=agent.agent_id,
            name=agent.config.name,
            old_status=old_status.value,
            new_status=new_status.value,
        )

        self.metrics.record_event("status_change", {
            "agent_id": agent.agent_id,
            "old_status": old_status.value,
            "new_status": new_status.value,
        })

    async def log_task_completed(self, agent: Agent, task_description: str) -> None:
        """Log task completion."""
        self.logger.info(
            "task_completed",
            agent_id=agent.agent_id,
            name=agent.config.name,
            task=task_description,
            cost=agent.metrics.total_cost,
            tokens=agent.metrics.total_tokens,
        )

        # Record updated metrics
        self.metrics.record_agent_metrics(agent.metrics)

    async def log_error(self, agent: Agent, error: str) -> None:
        """Log an error."""
        self.logger.error(
            "agent_error",
            agent_id=agent.agent_id,
            name=agent.config.name,
            error=error,
        )

        self.metrics.record_event("error", {
            "agent_id": agent.agent_id,
            "error": error,
        })

    async def start_monitoring(
        self,
        agents: Dict[str, Agent],
        interval_seconds: int = 15,
    ) -> None:
        """
        Start monitoring agents at regular intervals.

        Args:
            agents: Dict of agent_id -> Agent to monitor
            interval_seconds: How often to check agents
        """
        self.monitoring = True

        while self.monitoring:
            await asyncio.sleep(interval_seconds)

            for agent_id, agent in agents.items():
                if agent.status == AgentStatus.DELETED:
                    continue

                # Update metrics
                self.metrics.record_agent_metrics(agent.metrics)

                # Check context window usage
                context_usage = agent.get_context_window_usage()
                if context_usage["usage_percentage"] > 80:
                    self.logger.warning(
                        "high_context_usage",
                        agent_id=agent_id,
                        name=agent.config.name,
                        usage_percentage=context_usage["usage_percentage"],
                    )

    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self.monitoring = False

    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": self.metrics.get_summary(),
            "files": self.metrics.get_files_consumed_and_produced(),
        }

    def register_status_callback(self, callback: Callable[..., Any]) -> None:
        """Register a callback for status updates."""
        self.status_callbacks.append(callback)
