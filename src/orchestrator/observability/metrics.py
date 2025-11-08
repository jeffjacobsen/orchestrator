"""Metrics collection and aggregation."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from orchestrator.core.types import AgentMetrics


class MetricsCollector:
    """
    Collects and aggregates metrics across all agents.

    Critical principle: "If you can't measure it, you can't improve it.
    If you can't measure it, you can't scale it."
    """

    def __init__(self) -> None:
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.events: List[Dict[str, Any]] = []

    def record_agent_metrics(self, metrics: AgentMetrics) -> None:
        """Record metrics for an agent."""
        self.agent_metrics[metrics.agent_id] = metrics

    def record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record an event."""
        self.events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "data": data,
        })

    def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get metrics for a specific agent."""
        return self.agent_metrics.get(agent_id)

    def get_total_cost(self) -> float:
        """Get total cost across all agents."""
        return sum(m.total_cost for m in self.agent_metrics.values())

    def get_total_tokens(self) -> int:
        """Get total tokens used."""
        return sum(m.total_tokens for m in self.agent_metrics.values())

    def get_cost_by_agent(self) -> Dict[str, float]:
        """Get cost breakdown by agent."""
        return {
            agent_id: metrics.total_cost
            for agent_id, metrics in self.agent_metrics.items()
        }

    def get_files_consumed_and_produced(self) -> Dict[str, Any]:
        """
        Get files consumed vs produced - key observability metric.

        Returns:
            Dict with 'consumed' and 'produced' file lists
        """
        consumed = set()
        produced = set()

        for metrics in self.agent_metrics.values():
            consumed.update(metrics.files_read)
            produced.update(metrics.files_written)

        return {
            "consumed": sorted(list(consumed)),
            "produced": sorted(list(produced)),
            "net_files_created": len(produced - consumed),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        files_data = self.get_files_consumed_and_produced()

        return {
            "total_agents": len(self.agent_metrics),
            "total_cost": f"${self.get_total_cost():.4f}",
            "total_tokens": self.get_total_tokens(),
            "total_tool_calls": sum(m.tool_calls for m in self.agent_metrics.values()),
            "total_messages": sum(m.messages_sent for m in self.agent_metrics.values()),
            "files_consumed": len(files_data["consumed"]),
            "files_produced": len(files_data["produced"]),
            "net_files_created": files_data["net_files_created"],
            "total_events": len(self.events),
        }

    def filter_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Filter events by type."""
        return [e for e in self.events if e["type"] == event_type]

    def get_agent_timeline(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get timeline of events for a specific agent."""
        return [
            e for e in self.events
            if e.get("data", {}).get("agent_id") == agent_id
        ]
