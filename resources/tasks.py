from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
from models import TaskCreate, TaskResponse, TaskUpdate, TaskStatus, MessageType
from services import DatabaseManager, TaskListGenerator, IntegrationsClient

router = APIRouter(prefix="/tasks", tags=["tasks"])
db = DatabaseManager()
task_generator = TaskListGenerator()
integrations_client = IntegrationsClient()


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate, response: Response):
    """Create a new task"""
    task_id = db.create_task(task)

    if task_id is None:
        raise HTTPException(status_code=500, detail="Failed to create task (DB error, check logs)")

    created_task = db.get_task(task_id)
    if created_task is None:
        raise HTTPException(status_code=500, detail="Failed to fetch created task")

    # HTTP 201 best practice: send Location header
    response.headers["Location"] = f"/tasks/{task_id}"
    return created_task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """Get a specific task by ID"""
    task = db.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    user_id: Optional[str] = Query(None, description="Filter by user_id (UUID)"),
    task_id: Optional[int] = Query(None, description="Filter by task_id"),
    cls_id: Optional[str] = Query(None, description="Filter by classification_id"),
    classification_id: Optional[str] = Query(None, description="Filter by classification_id (alias)"),
    source_msg_id: Optional[str] = Query(None, description="Filter by source_msg_id (UUID)"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[int] = Query(None, description="Filter by priority"),
    message_type: Optional[MessageType] = Query(None, description="Filter by message_type"),
    sender: Optional[str] = Query(None, description="Filter by sender"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    created_at: Optional[str] = Query(None, description="Filter by created_at (ISO format)"),
    updated_at: Optional[str] = Query(None, description="Filter by updated_at (ISO format)"),
    due_at: Optional[str] = Query(None, description="Filter by due_at (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    Get tasks with optional filters on any attribute.
    Returns all tasks matching the provided filters.
    """
    # Build filters dictionary from query parameters
    filters = {}
    
    if user_id is not None:
        filters['user_id'] = user_id
    if task_id is not None:
        filters['task_id'] = task_id
    if cls_id is not None:
        filters['cls_id'] = cls_id
    if classification_id is not None:
        filters['classification_id'] = classification_id
    if source_msg_id is not None:
        filters['source_msg_id'] = source_msg_id
    if status is not None:
        filters['status'] = status.value if hasattr(status, 'value') else status
    if priority is not None:
        filters['priority'] = priority
    if message_type is not None:
        filters['message_type'] = message_type.value if hasattr(message_type, 'value') else message_type
    if sender is not None:
        filters['sender'] = sender
    if subject is not None:
        filters['subject'] = subject
    if created_at is not None:
        filters['created_at'] = created_at
    if updated_at is not None:
        filters['updated_at'] = updated_at
    if due_at is not None:
        filters['due_at'] = due_at
    
    tasks, total = db.get_tasks(filters=filters, limit=limit, offset=offset)
    return tasks


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, updates: TaskUpdate):
    """Update a task"""
    success = db.update_task(task_id, updates)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or update failed")
    
    updated_task = db.get_task(task_id)
    return updated_task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int):
    """Delete a task"""
    success = db.delete_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return JSONResponse(status_code=204, content=None)
