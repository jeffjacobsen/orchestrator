"""Type definitions for the orchestrator system."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent lifecycle states."""

    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class AgentRole(str, Enum):
    """Specialized agent roles."""

    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"  # Task planning and decomposition
    BUILDER = "builder"  # Implementation and coding
    REVIEWER = "reviewer"  # Code review and QA
    ANALYST = "analyst"  # Data analysis and research
    TESTER = "tester"  # Testing and validation
    DOCUMENTER = "documenter"  # Documentation writing
    CUSTOM = "custom"  # User-defined role


class ToolCall(BaseModel):
    """Record of a tool invocation."""

    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = True
    error: Optional[str] = None


class AgentMetrics(BaseModel):
    """Performance and cost metrics for an agent."""

    agent_id: str
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0  # Tokens used to create cache
    cache_read_input_tokens: int = 0  # Tokens read from cache
    total_cost: float = 0.0
    tool_calls: int = 0
    messages_sent: int = 0
    files_read: List[str] = Field(default_factory=list)
    files_written: List[str] = Field(default_factory=list)
    execution_time_seconds: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    name: str
    role: AgentRole = AgentRole.CUSTOM
    model: str = "claude-sonnet-4-5-20250929"
    system_prompt: str = ""
    max_tokens: int = 8192
    temperature: float = 1.0
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Working directory and tool control
    working_directory: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    permission_mode: str = "bypassPermissions"  # "bypassPermissions" or "ask"

    # Session and task management
    session_id: Optional[str] = None
    task_id: Optional[str] = None  # For log organization and context tracking


class TaskResult(BaseModel):
    """Result from an agent's task execution."""

    agent_id: str
    task_description: str
    success: bool
    output: Any
    error: Optional[str] = None
    metrics: AgentMetrics
    artifacts: List[str] = Field(default_factory=list)  # Files produced
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrchestratorTask(BaseModel):
    """High-level task for the orchestrator to decompose."""

    task_id: str
    description: str
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    assigned_agents: List[str] = Field(default_factory=list)
    status: AgentStatus = AgentStatus.CREATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Optional[TaskResult] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Workflow planning metadata
