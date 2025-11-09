"""
Agent API endpoints.
"""

from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.agent import Agent, AgentStatus
from app.schemas.agent import AgentResponse, AgentCreate, AgentList
from app.schemas.common import ErrorResponse
from app.api.v1.websocket import get_websocket_manager

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get(
    "",
    response_model=AgentList,
    dependencies=[Depends(verify_api_key)],
    summary="List all agents",
    description="Get a paginated list of all agents with optional filtering.",
)
async def list_agents(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[AgentStatus] = Query(None, description="Filter by status"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
) -> AgentList:
    """
    List all agents with optional filters.

    Returns:
        AgentList: Paginated list of agents
    """
    # Build query
    query = select(Agent)
    if status:
        query = query.where(Agent.status == status)
    if task_id:
        query = query.where(Agent.task_id == task_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Agent.created_at.desc())

    # Execute query
    result = await db.execute(query)
    agents = result.scalars().all()

    return AgentList(
        agents=[AgentResponse.model_validate(agent) for agent in agents],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    dependencies=[Depends(verify_api_key)],
    responses={404: {"model": ErrorResponse}},
    summary="Get agent details",
    description="Get detailed information about a specific agent.",
)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """
    Get details for a specific agent.

    Args:
        agent_id: Agent ID

    Returns:
        AgentResponse: Agent details

    Raises:
        HTTPException: If agent not found
    """
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    return AgentResponse.model_validate(agent)


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
    summary="Create a new agent",
    description="Create a new agent instance.",
)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """
    Create a new agent.

    Args:
        agent_data: Agent creation data

    Returns:
        AgentResponse: Created agent
    """
    # Generate agent ID
    import uuid

    agent_id = str(uuid.uuid4())

    # Create agent
    agent = Agent(
        id=agent_id,
        role=agent_data.role,
        custom_instructions=agent_data.custom_instructions,
        task_id=agent_data.task_id,
        status=AgentStatus.IDLE,
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    # Broadcast agent creation to WebSocket clients
    manager = get_websocket_manager()
    await manager.broadcast_agent_update(agent)

    return AgentResponse.model_validate(agent)


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_api_key)],
    responses={404: {"model": ErrorResponse}},
    summary="Delete an agent",
    description="Delete a specific agent.",
)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an agent.

    Args:
        agent_id: Agent ID

    Raises:
        HTTPException: If agent not found
    """
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    await db.delete(agent)
    await db.commit()

    # Broadcast agent deletion to WebSocket clients
    manager = get_websocket_manager()
    await manager.broadcast_agent_deleted(agent_id)


@router.get(
    "/{agent_id}/logs",
    dependencies=[Depends(verify_api_key)],
    responses={404: {"model": ErrorResponse}},
    summary="Get agent logs",
    description="Get the prompt and output logs for a specific agent.",
)
async def get_agent_logs(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get agent execution logs (prompt.txt and text.txt).

    Args:
        agent_id: Agent ID (short form, e.g., "444d7be7")

    Returns:
        dict: Contains 'prompt' and 'output' text

    Raises:
        HTTPException: If agent not found or logs not available
    """
    # Verify agent exists
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    # Find agent logs directory
    # Logs are stored in: agent_logs/{task_id}/{agent_id}_{name}_{timestamp}/
    logs_base_dir = Path(__file__).parent.parent.parent.parent / "agent_logs"

    # Try to find directory matching the agent ID
    agent_log_dir = None
    if logs_base_dir.exists() and agent.task_id:
        # Look in the task-specific subdirectory
        task_log_dir = logs_base_dir / agent.task_id
        if task_log_dir.exists():
            for dir_path in task_log_dir.iterdir():
                if dir_path.is_dir() and dir_path.name.startswith(agent_id[:8]):
                    agent_log_dir = dir_path
                    break
    elif logs_base_dir.exists():
        # Fallback: search all directories (for logs created before task_id structure)
        for dir_path in logs_base_dir.iterdir():
            if dir_path.is_dir() and dir_path.name.startswith(agent_id[:8]):
                agent_log_dir = dir_path
                break

    if not agent_log_dir:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log directory for agent {agent_id} not found",
        )

    # Read prompt.txt and text.txt
    prompt_file = agent_log_dir / "prompt.txt"
    output_file = agent_log_dir / "text.txt"

    prompt_text = ""
    output_text = ""

    if prompt_file.exists():
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt_text = f.read()
        except Exception as e:
            prompt_text = f"Error reading prompt: {str(e)}"

    if output_file.exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                output_text = f.read()
        except Exception as e:
            output_text = f"Error reading output: {str(e)}"

    return {
        "prompt": prompt_text,
        "output": output_text,
    }
