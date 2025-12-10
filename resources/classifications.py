from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from services import DatabaseManager
from services.classification_handler import ClassificationHandler
from models import TaskResponse, TodoResponse, FollowupResponse

router = APIRouter(prefix="/classifications", tags=["classifications"])
db = DatabaseManager()
classification_handler = ClassificationHandler()


@router.post("/webhook")
async def process_classifications(
    messages: List[Dict[str, Any]],
    user_id: int = Query(..., description="User ID for task/todo/followup ownership")
):
    """
    Webhook endpoint to receive classified messages from classification microservice.
    Automatically creates tasks, todos, or followups based on message classification.
    """
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    try:
        # Process classifications and route to appropriate creation logic
        processed = classification_handler.process_classifications(messages, user_id)
        
        created_items = {
            'tasks': [],
            'todos': [],
            'followups': []
        }
        
        # Create tasks
        for task in processed['tasks']:
            task_id = db.create_task(task)
            if task_id:
                created_task = db.get_task(task_id)
                if created_task:
                    created_items['tasks'].append(created_task)
        
        # Create todos
        for todo in processed['todos']:
            todo_id = db.create_todo(todo)
            if todo_id:
                created_todo = db.get_todo(todo_id)
                if created_todo:
                    created_items['todos'].append(created_todo)
        
        # Create followups
        for followup in processed['followups']:
            followup_id = db.create_followup(followup)
            if followup_id:
                created_followup = db.get_followup(followup_id)
                if created_followup:
                    created_items['followups'].append(created_followup)
        
        return {
            "message": "Classifications processed successfully",
            "created": {
                "tasks_count": len(created_items['tasks']),
                "todos_count": len(created_items['todos']),
                "followups_count": len(created_items['followups'])
            },
            "items": created_items
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process classifications: {str(e)}"
        )

