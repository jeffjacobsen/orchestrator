"""
Task API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskResponse, TaskCreate, TaskList
from app.schemas.common import ErrorResponse

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
    description="Create a new task.",
)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Create a new task.

    Args:
        task_data: Task creation data

    Returns:
        TaskResponse: Created task
    """
    # Generate task ID
    import uuid
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
        metadata=task_data.metadata,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

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
