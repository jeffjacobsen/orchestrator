"""
Task Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.task import TaskStatus, TaskType


class TaskBase(BaseModel):
    """Base task schema with common fields."""
    description: str = Field(..., description="Task description", min_length=1)
    task_type: TaskType = Field(..., description="Task type")


class TaskCreate(TaskBase):
    """
    Schema for creating a new task.

    Example:
        ```json
        {
            "description": "Add user authentication feature",
            "task_type": "feature_implementation",
            "include_analyst": "auto"
        }
        ```
    """
    include_analyst: Optional[str] = Field("auto", description="Include ANALYST: 'yes', 'no', or 'auto'")
    task_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata", alias="metadata")


class TaskResponse(TaskBase):
    """
    Schema for task response.

    This is returned by GET endpoints and includes full task details.

    Example:
        ```json
        {
            "id": "task-123",
            "description": "Add authentication",
            "task_type": "feature_implementation",
            "status": "in_progress",
            "workflow": ["PLANNER", "BUILDER"],
            "complexity": "complex",
            "created_at": "2025-11-05T12:00:00Z"
        }
        ```
    """
    id: str = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="Current task status")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    workflow: List[str] = Field(default_factory=list, description="List of agent roles in workflow")
    complexity: Optional[str] = Field(None, description="Task complexity: 'simple' or 'complex'")
    include_analyst: Optional[str] = Field(None, description="ANALYST inclusion setting")

    result: Optional[str] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")

    task_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata", alias="metadata")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,  # Allow both 'metadata' and 'task_metadata'
        "protected_namespaces": (),  # Disable protected namespace warnings
    }


class TaskList(BaseModel):
    """
    Schema for paginated task list.

    Example:
        ```json
        {
            "tasks": [...],
            "total": 5,
            "page": 1,
            "page_size": 20
        }
        ```
    """
    tasks: List[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Items per page")
