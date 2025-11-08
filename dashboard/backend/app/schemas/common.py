"""
Common Pydantic schemas.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    Standardized error response format.

    This provides consistent error responses across all API endpoints.

    Attributes:
        code: Machine-readable error code (e.g., "AGENT_NOT_FOUND")
        message: Human-readable error message
        details: Optional additional error context
        request_id: Optional request ID for debugging
        timestamp: When the error occurred

    Example:
        ```json
        {
            "code": "AGENT_NOT_FOUND",
            "message": "Agent with ID abc-123 not found",
            "details": {"agent_id": "abc-123"},
            "request_id": "req-456",
            "timestamp": "2025-11-05T12:34:56Z"
        }
        ```
    """
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict = Field(default_factory=dict, description="Additional error context")
    request_id: str = Field(default="", description="Request ID for debugging")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "json_schema_extra": {
            "example": {
                "code": "AGENT_NOT_FOUND",
                "message": "Agent with ID abc-123 not found",
                "details": {"agent_id": "abc-123"},
                "request_id": "req-456",
                "timestamp": "2025-11-05T12:34:56Z"
            }
        }
    }
