from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from models import TaskCreate, TaskResponse, TaskUpdate, TaskStatus
from services import DatabaseManager, TaskListGenerator

router = APIRouter(prefix="/tasks", tags=["tasks"])
db = DatabaseManager()
task_generator = TaskListGenerator()


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task"""
    task_id = db.create_task(task)
    
    if task_id is None:
        raise HTTPException(status_code=500, detail="Failed to create task")
    
    created_task = db.get_task(task_id)
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
    user_id: int = Query(..., description="User ID to filter tasks"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[int] = Query(None, ge=1, le=5, description="Minimum priority")
):
    """Get tasks with optional filters"""
    tasks = db.get_tasks(user_id, status, priority)
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


@router.post("/batch", response_model=List[TaskResponse], status_code=201)
async def create_tasks_from_messages(
    messages: List[dict],
    user_id: int = Query(..., description="User ID for task ownership")
):
    """Process LLM output and create multiple tasks"""
    try:
        tasks = task_generator.generate_task_list(messages, user_id)
        
        created_tasks = []
        for task in tasks:
            task_id = db.create_task(task)
            if task_id:
                created_task = db.get_task(task_id)
                created_tasks.append(created_task)
        
        return created_tasks
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to process messages: {str(e)}"
        )
    