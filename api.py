from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from models import (
    TaskCreate, TaskResponse, TaskUpdate, TaskStatus, 
    IncomingMessage
)
from database import DatabaseManager
from generateTaskList import TaskListGenerator

app = FastAPI(title="Actions Service", version="1.0.0")
db = DatabaseManager()
task_generator = TaskListGenerator()

# TASKS RESOURCE - Full CRUD


@app.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task"""
    task_id = db.create_task(task)
    
    if task_id is None:
        raise HTTPException(status_code=500, detail="Failed to create task")
    
    created_task = db.get_task(task_id)
    return created_task


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """Get a specific task by ID"""
    task = db.get_task(task_id)
    
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    user_id: int = Query(..., description="User ID to filter tasks"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[int] = Query(None, ge=1, le=5, description="Minimum priority")
):
    """Get tasks with optional filters"""
    tasks = db.get_tasks(user_id, status, priority)
    return tasks


@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, updates: TaskUpdate):
    """Update a task"""
    success = db.update_task(task_id, updates)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or update failed")
    
    updated_task = db.get_task(task_id)
    return updated_task


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int):
    """Delete a task"""
    success = db.delete_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return JSONResponse(status_code=204, content=None)


# TODO RESOURCE - Full CRUD (subset of tasks with type filter)

@app.post("/todo", status_code=501)
async def create_todo():
    """Create a new todo - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@app.get("/todo/{todo_id}", status_code=501)
async def get_todo(todo_id: int):
    """Get a specific todo by ID - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@app.get("/todo", status_code=501)
async def get_todos():
    """Get all todos - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@app.put("/todo/{todo_id}", status_code=501)
async def update_todo(todo_id: int):
    """Update a todo - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@app.delete("/todo/{todo_id}", status_code=501)
async def delete_todo(todo_id: int):
    """Delete a todo - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")

# FOLLOWUP RESOURCE - Full CRUD (tasks that need reply/follow-up action)

@app.post("/followup", status_code=501)
async def create_followup():
    """Create a new follow-up task - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@app.get("/followup/{followup_id}", status_code=501)
async def get_followup(followup_id: int):
    """Get a specific follow-up by ID - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@app.get("/followup", status_code=501)
async def get_followups():
    """Get all follow-up tasks - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@app.put("/followup/{followup_id}", status_code=501)
async def update_followup(followup_id: int):
    """Update a follow-up task - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@app.delete("/followup/{followup_id}", status_code=501)
async def delete_followup(followup_id: int):
    """Delete a follow-up task - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")

# BATCH PROCESSING - Special endpoint for LLM output

@app.post("/tasks/batch", response_model=List[TaskResponse], status_code=201)
async def create_tasks_from_messages(
    messages: List[dict],
    user_id: int = Query(..., description="User ID for task ownership")
):
    """
    Process LLM output and create multiple tasks.
    This is the main endpoint that uses generateTaskList functionality.
    """
    try:
        # Generate task list from messages
        tasks = task_generator.generate_task_list(messages, user_id)
        
        # Insert all tasks into database
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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "actions-service"}


@app.on_event("shutdown")
def shutdown_event():
    """Clean up database connection on shutdown"""
    db.close()

