from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from typing import List, Optional
from models import TodoCreate, TodoResponse, TodoUpdate, TaskStatus
from services import DatabaseManager

router = APIRouter(prefix="/todo", tags=["todo"])
db = DatabaseManager()


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


@router.get("/{todo_id}")
async def get_todo(todo_id: int):
    """
    Get a specific todo by ID + linked data
    """
    todo = db.get_todo(todo_id)

    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    return {
        **todo.model_dump(),
        "links": {
            "self": f"/todo/{todo.todo_id}",
            "owner": f"/users/{todo.user_id}",
            "task": f"/tasks?source_msg_id={todo.source_msg_id}",
            "followup": f"/followup?source_msg_id={todo.source_msg_id}",
        },
    }


@router.get("", response_model=List[TodoResponse])
async def get_todos(
    user_id: int = Query(..., description="User ID to filter todos"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[int] = Query(None, ge=1, le=5, description="Minimum priority")
):
    """Get todos with optional filters"""
    todos, total = db.get_todos(user_id, status, priority)
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
