"""
Task API endpoints.
"""
import logging
import shutil
from typing import Optional
from pathlib import Path
from datetime import datetime
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get(
    "",
    response_model=TaskList,
    dependencies=[Depends(verify_api_key)],
    summary="List all tasks",
    description="Get a paginated list of all tasks with optional filtering, search, and sorting.",
)
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in task description"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format: YYYY-MM-DD)"),
    cost_min: Optional[int] = Query(None, ge=0, description="Minimum total cost in cents"),
    cost_max: Optional[int] = Query(None, ge=0, description="Maximum total cost in cents"),
    duration_min: Optional[int] = Query(None, ge=0, description="Minimum duration in seconds"),
    duration_max: Optional[int] = Query(None, ge=0, description="Maximum duration in seconds"),
    sort_by: str = Query("created_at", description="Sort field: created_at, updated_at, total_cost, duration_seconds"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
) -> TaskList:
    """
    List all tasks with optional filters, search, and sorting.

    Returns:
        TaskList: Paginated list of tasks
    """
    # Build query
    query = select(Task)

    # Apply filters
    if status:
        query = query.where(Task.status == status)

    if search:
        query = query.where(Task.description.ilike(f"%{search}%"))

    if date_from:
        try:
            from_dt = datetime.fromisoformat(date_from)
            query = query.where(Task.created_at >= from_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date_from format: {date_from}. Use YYYY-MM-DD"
            )

    if date_to:
        try:
            to_dt = datetime.fromisoformat(date_to)
            # Include the entire day by setting time to 23:59:59
            to_dt = to_dt.replace(hour=23, minute=59, second=59)
            query = query.where(Task.created_at <= to_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date_to format: {date_to}. Use YYYY-MM-DD"
            )

    # Cost filtering
    if cost_min is not None:
        query = query.where(Task.total_cost >= cost_min)

    if cost_max is not None:
        query = query.where(Task.total_cost <= cost_max)

    # Duration filtering
    if duration_min is not None:
        query = query.where(Task.duration_seconds >= duration_min)

    if duration_max is not None:
        query = query.where(Task.duration_seconds <= duration_max)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Apply sorting
    valid_sort_fields = {
        "created_at": Task.created_at,
        "updated_at": Task.updated_at,
        "total_cost": Task.total_cost,
        "duration_seconds": Task.duration_seconds
    }
    sort_field = valid_sort_fields.get(sort_by, Task.created_at)

    if sort_order.lower() == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)

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

    # Delete task from database (agents will be cascade deleted due to foreign key)
    await db.delete(task)
    await db.commit()

    # Delete associated log files
    logs_base_dir = Path(__file__).parent.parent.parent.parent / "agent_logs"
    task_log_dir = logs_base_dir / task_id

    if task_log_dir.exists() and task_log_dir.is_dir():
        try:
            shutil.rmtree(task_log_dir)
            logger.info(f"Deleted logs for task {task_id}")
        except Exception as e:
            # Log error but don't fail the deletion
            logger.error(f"Failed to delete logs for task {task_id}: {e}")

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
