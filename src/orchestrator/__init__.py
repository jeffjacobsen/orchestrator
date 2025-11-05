"""
Claude Multi-Agent Orchestrator

A powerful orchestration system for managing multiple Claude agents with CRUD operations,
observability, and intelligent task decomposition.
"""

from orchestrator.core.orchestrator import Orchestrator
from orchestrator.core.agent import Agent
from orchestrator.core.agent_manager import AgentManager
from orchestrator.core.types import AgentConfig, AgentStatus, AgentMetrics, AgentRole

__version__ = "0.1.0"
__all__ = [
    "Orchestrator",
    "Agent",
    "AgentManager",
    "AgentConfig",
    "AgentStatus",
    "AgentMetrics",
    "AgentRole",
]
