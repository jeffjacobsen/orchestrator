"""
Task API endpoints.
"""
import asyncio
from typing import Optional
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.core.config import settings
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskResponse, TaskCreate, TaskList
from app.schemas.common import ErrorResponse
from app.api.v1.websocket import get_websocket_manager
from app.services.orchestrator_executor import OrchestratorExecutor

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get(
    "",
    response_model=TaskList,
    dependencies=[Depends(verify_api_key)],
    summary="List all tasks",
    description="Get a paginated list of all tasks with optional filtering.",
)
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
) -> TaskList:
    """
    List all tasks with optional filters.

    Returns:
        TaskList: Paginated list of tasks
    """
    # Build query
    query = select(Task)
    if status:
        query = query.where(Task.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Task.created_at.desc())

    # Execute query
    result = await db.execute(query)
    tasks = result.scalars().all()

    return TaskList(
        tasks=[TaskResponse.model_validate(task) for task in tasks],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    dependencies=[Depends(verify_api_key)],
    responses={404: {"model": ErrorResponse}},
    summary="Get task details",
    description="Get detailed information about a specific task.",
)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Get details for a specific task.

    Args:
        task_id: Task ID

    Returns:
        TaskResponse: Task details

    Raises:
        HTTPException: If task not found
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    return TaskResponse.model_validate(task)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
    summary="Create a new task",
    description="Create a new task and execute it with the orchestrator.",
)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Create a new task.

    Args:
        task_data: Task creation data

    Returns:
        TaskResponse: Created task

    Raises:
        HTTPException: If working_directory is provided but doesn't exist or isn't a directory
    """
    import uuid
    import os

    # Validate working directory if provided
    if task_data.working_directory:
        working_dir = os.path.abspath(task_data.working_directory)

        if not os.path.exists(working_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Working directory does not exist: {working_dir}",
            )

        if not os.path.isdir(working_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Working directory path is not a directory: {working_dir}",
            )

        # Check if directory is readable/accessible
        if not os.access(working_dir, os.R_OK | os.X_OK):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Working directory is not accessible (check permissions): {working_dir}",
            )

    # Generate task ID
    task_id = str(uuid.uuid4())

    # Determine complexity based on description
    complexity = "simple" if len(task_data.description.split()) < 50 else "complex"

    # Create task
    task = Task(
        id=task_id,
        description=task_data.description,
        task_type=task_data.task_type,
        status=TaskStatus.PENDING,
        complexity=complexity,
        include_analyst=task_data.include_analyst,
        working_directory=task_data.working_directory,
        task_metadata=task_data.task_metadata,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Broadcast task creation to WebSocket clients
    manager = get_websocket_manager()
    await manager.broadcast_task_update(task)

    # Execute task in background
    async def execute_in_background():
        """Execute task asynchronously"""
        # Create new DB session for background task
        from app.core.database import async_session_maker

        # Use task's working directory if specified, otherwise use default orchestrator root
        if task.working_directory:
            working_dir = os.path.abspath(task.working_directory)
        else:
            # Resolve absolute path to orchestrator root
            working_dir = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    settings.orchestrator_working_directory
                )
            )

        async with async_session_maker() as bg_db:
            executor = OrchestratorExecutor(db=bg_db, working_directory=working_dir)
            await executor.execute_task(task.id)

    # Schedule background execution
    background_tasks.add_task(execute_in_background)

    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_api_key)],
    responses={404: {"model": ErrorResponse}},
    summary="Delete a task",
    description="Delete a specific task.",
)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a task.

    Args:
        task_id: Task ID

    Raises:
        HTTPException: If task not found
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    await db.delete(task)
    await db.commit()

    # Broadcast task deletion to WebSocket clients
    manager = get_websocket_manager()
    await manager.broadcast_task_deleted(task_id)


@router.get(
    "/{task_id}/planner-logs",
    dependencies=[Depends(verify_api_key)],
    responses={404: {"model": ErrorResponse}},
    summary="Get workflow planner logs",
    description="Get the workflow planner logs for a specific task.",
)
async def get_task_planner_logs(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get workflow planner execution logs (prompt.txt and text.txt).

    The planner agent is deleted after execution, so we need to find its logs
    by matching the timestamp with the task creation time.

    Args:
        task_id: Task ID

    Returns:
        dict: Contains 'prompt' and 'output' text, or None if not found

    Raises:
        HTTPException: If task not found
    """
    # Verify task exists
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    # Find planner logs directory
    # Logs are now stored in: agent_logs/{task_id}/{agent_id}_Workflow_Planner_{timestamp}/
    logs_base_dir = Path(__file__).parent.parent.parent.parent / "agent_logs"

    planner_log_dir = None
    if logs_base_dir.exists():
        # Look in the task-specific subdirectory
        task_log_dir = logs_base_dir / task_id
        if task_log_dir.exists():
            # Find the planner directory in this task's logs
            # Check for both "Workflow_Planner" (old name) and "Planner_Agent" (new name)
            for dir_path in task_log_dir.iterdir():
                if dir_path.is_dir() and ("Workflow_Planner" in dir_path.name or "Planner_Agent" in dir_path.name):
                    planner_log_dir = dir_path
                    break
        else:
            # Fallback: search all directories (for logs created before task_id structure)
            # This is for backward compatibility with old log structure
            for dir_path in logs_base_dir.iterdir():
                if dir_path.is_dir() and ("Workflow_Planner" in dir_path.name or "Planner_Agent" in dir_path.name):
                    planner_log_dir = dir_path
                    break

    if not planner_log_dir:
        # Return empty logs if not found (planner might not have run for this task)
        return {
            "prompt": "",
            "output": "",
        }

    # Read prompt.txt and text.txt
    prompt_file = planner_log_dir / "prompt.txt"
    output_file = planner_log_dir / "text.txt"

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
