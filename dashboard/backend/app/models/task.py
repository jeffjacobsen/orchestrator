"""
Task database model.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Text, Integer
from app.core.database import Base
import enum


class TaskStatus(str, enum.Enum):
    """Task status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, enum.Enum):
    """Task type enum matching orchestrator task types."""

    FEATURE_IMPLEMENTATION = "feature_implementation"
    BUG_FIX = "bug_fix"
    CODE_REVIEW = "code_review"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    INVESTIGATION = "investigation"
    CUSTOM = "custom"
    AUTO = "auto"


class Task(Base):
    """
    Task model representing a high-level task executed by agents.
    """

    __tablename__ = "tasks"

    # Primary identification
    id = Column(String(36), primary_key=True, index=True)
    description = Column(Text, nullable=False)
    task_type = Column(SQLEnum(TaskType), nullable=False, index=True)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True)

    # Timestamps
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime, nullable=True)

    # Workflow configuration
    workflow = Column(JSON, default=list)  # List of agent roles
    current_step = Column(Integer, nullable=True)  # Current workflow step index (0-based)
    complexity = Column(String, nullable=True)  # "simple" or "complex"
    include_analyst = Column(String, nullable=True)  # "yes", "no", or "auto"
    working_directory = Column(String, nullable=True)  # Working directory for task execution

    # Metrics (aggregated from all agents)
    total_cost = Column(
        Integer, nullable=True, default=0, index=True
    )  # Total cost in USD (stored as cents to avoid float issues)
    duration_seconds = Column(
        Integer, nullable=True, default=0, index=True
    )  # Total execution time in seconds

    # Results
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

    # Metadata
    task_metadata = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, type={self.task_type.value}, status={self.status.value})>"
