from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from typing import List, Optional
from models import TodoCreate, TodoResponse, TodoUpdate, TaskStatus, MessageType
from services import DatabaseManager, IntegrationsClient

router = APIRouter(prefix="/todo", tags=["todo"])
db = DatabaseManager()
integrations_client = IntegrationsClient()


@router.post("", response_model=TodoResponse, status_code=201)
async def create_todo(todo: TodoCreate, response: Response):
    """Create a new todo"""
    todo_id = db.create_todo(todo)

    if todo_id is None:
        raise HTTPException(status_code=500, detail="Failed to create todo (DB error, check logs)")

    created_todo = db.get_todo(todo_id)
    if created_todo is None:
        raise HTTPException(status_code=500, detail="Failed to fetch created todo")

    # HTTP 201 best practice: send Location header
    response.headers["Location"] = f"/todo/{todo_id}"
    return created_todo


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int):
    """Get a specific todo by ID"""
    todo = db.get_todo(todo_id)

    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    return todo


@router.get("", response_model=List[TodoResponse])
async def get_todos(
    user_id: Optional[str] = Query(None, description="Filter by user_id (UUID)"),
    todo_id: Optional[int] = Query(None, description="Filter by todo_id"),
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
    Get todos with optional filters on any attribute.
    Returns all todos matching the provided filters.
    """
    # Build filters dictionary from query parameters
    filters = {}
    
    if user_id is not None:
        filters['user_id'] = user_id
    if todo_id is not None:
        filters['todo_id'] = todo_id
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
    
    todos, total = db.get_todos(filters=filters, limit=limit, offset=offset)
    return todos


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, updates: TodoUpdate):
    """Update a todo"""
    success = db.update_todo(todo_id, updates)
    
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found or update failed")
    
    updated_todo = db.get_todo(todo_id)
    return updated_todo


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(todo_id: int):
    """Delete a todo"""
    success = db.delete_todo(todo_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return JSONResponse(status_code=204, content=None)
