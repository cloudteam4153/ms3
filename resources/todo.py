from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/todo", tags=["todo"])


@router.post("", status_code=501)
async def create_todo():
    """Create a new todo - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/{todo_id}", status_code=501)
async def get_todo(todo_id: int):
    """Get a specific todo by ID - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("", status_code=501)
async def get_todos():
    """Get all todos - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.put("/{todo_id}", status_code=501)
async def update_todo(todo_id: int):
    """Update a todo - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.delete("/{todo_id}", status_code=501)
async def delete_todo(todo_id: int):
    """Delete a todo - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")
