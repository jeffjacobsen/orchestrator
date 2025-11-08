"""
Agent database model.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Integer
from app.core.database import Base
import enum


class AgentStatus(str, enum.Enum):
    """Agent status enum."""
    ACTIVE = "active"
    IDLE = "idle"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRole(str, enum.Enum):
    """Agent role enum matching orchestrator types."""
    ANALYST = "ANALYST"
    PLANNER = "PLANNER"
    BUILDER = "BUILDER"
    TESTER = "TESTER"
    REVIEWER = "REVIEWER"
    DOCUMENTER = "DOCUMENTER"
    CUSTOM = "CUSTOM"


class Agent(Base):
    """
    Agent model representing a Claude agent instance.
    """
    __tablename__ = "agents"

    # Primary identification
    id = Column(String(36), primary_key=True, index=True)
    role = Column(SQLEnum(AgentRole), nullable=False, index=True)
    status = Column(SQLEnum(AgentStatus), nullable=False, default=AgentStatus.IDLE, index=True)

    # Task association
    task_id = Column(String(36), index=True, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Configuration
    custom_instructions = Column(String, nullable=True)
    system_prompt = Column(String, nullable=True)

    # Metrics
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    cache_creation_tokens = Column(Integer, default=0)
    cache_read_tokens = Column(Integer, default=0)
    total_cost = Column(String, default="$0.00")  # Store as string for precision

    # Context
    conversation_history = Column(JSON, default=list)
    agent_metadata = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, role={self.role.value}, status={self.status.value})>"
