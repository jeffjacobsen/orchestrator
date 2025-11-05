"""Database models for persistence."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class AgentRecord(BaseModel):
    """Database record for an agent."""

    agent_id: str
    name: str
    role: str
    model: str
    status: str
    total_cost: float = 0.0
    total_tokens: int = 0
    messages_sent: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class TaskRecord(BaseModel):
    """Database record for a task."""

    task_id: str
    description: str
    task_type: str
    status: str
    assigned_agents: str  # JSON array of agent IDs
    total_cost: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Optional[str] = None  # JSON serialized result
