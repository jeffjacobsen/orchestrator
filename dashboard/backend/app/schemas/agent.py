"""
Agent Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.agent import AgentStatus, AgentRole


class AgentBase(BaseModel):
    """Base agent schema with common fields."""
    role: AgentRole = Field(..., description="Agent role")
    custom_instructions: Optional[str] = Field(None, description="Custom instructions for the agent")


class AgentCreate(AgentBase):
    """
    Schema for creating a new agent.

    Example:
        ```json
        {
            "role": "PLANNER",
            "custom_instructions": "Focus on performance optimization"
        }
        ```
    """
    task_id: Optional[str] = Field(None, description="Associated task ID")


class AgentResponse(AgentBase):
    """
    Schema for agent response.

    This is returned by GET endpoints and includes full agent details.

    Example:
        ```json
        {
            "id": "abc-123",
            "role": "PLANNER",
            "status": "active",
            "task_id": "task-456",
            "created_at": "2025-11-05T12:00:00Z",
            "total_input_tokens": 1000,
            "total_output_tokens": 500,
            "total_cost": "$0.05"
        }
        ```
    """
    id: str = Field(..., description="Agent ID")
    status: AgentStatus = Field(..., description="Current agent status")
    task_id: Optional[str] = Field(None, description="Associated task ID")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    total_input_tokens: int = Field(0, description="Total input tokens used")
    total_output_tokens: int = Field(0, description="Total output tokens generated")
    cache_creation_tokens: int = Field(0, description="Cache creation tokens")
    cache_read_tokens: int = Field(0, description="Cache read tokens")
    total_cost: str = Field("$0.00", description="Total cost")

    agent_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata", alias="metadata")

    class Config:
        from_attributes = True
        populate_by_name = True  # Allow both 'metadata' and 'agent_metadata'


class AgentList(BaseModel):
    """
    Schema for paginated agent list.

    Example:
        ```json
        {
            "agents": [...],
            "total": 10,
            "page": 1,
            "page_size": 20
        }
        ```
    """
    agents: List[AgentResponse] = Field(..., description="List of agents")
    total: int = Field(..., description="Total number of agents")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Items per page")
