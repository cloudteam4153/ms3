from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from services import DatabaseManager, ClassificationClient, IntegrationsClient
from services.classification_handler import ClassificationHandler
from models import TaskResponse, TodoResponse, FollowupResponse, TaskCreate, FollowupCreate, TaskStatus, MessageType
import logging
import hashlib

router = APIRouter(prefix="/classifications", tags=["classifications"])
db = DatabaseManager()
classification_handler = ClassificationHandler()
classification_client = ClassificationClient()
integrations_client = IntegrationsClient()
logger = logging.getLogger(__name__)


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


@router.post("/sync")
async def sync_classifications(
    user_id: str = Query(..., description="User ID to sync classifications for (can be string UUID or integer)")
):
    """
    Pull classifications from ms4-classification service and create tasks/followups.
    
    This endpoint:
    1. Fetches all classifications for the given user_id from ms4-classification service
    2. For each classification with label 'todo', creates a task
    3. For each classification with label 'followup', creates a followup
    4. Skips classifications with label 'noise'
    5. Associates each task/followup with msg_id, user_id, and cls_id
    
    Note: If user_id is a string UUID, it will be converted to an integer hash for database storage.
    """
    try:
        # Convert string user_id to int for database (use deterministic hash)
        # If it's already numeric, use it directly
        try:
            db_user_id = int(user_id)
        except ValueError:
            # Convert string UUID to consistent integer hash using MD5 (deterministic)
            hash_obj = hashlib.md5(user_id.encode())
            hash_hex = hash_obj.hexdigest()
            db_user_id = int(hash_hex[:8], 16) % (10**9)  # Use first 8 hex chars, keep within int range
        
        # Pull classifications from ms4
        logger.info(f"Fetching classifications for user_id: {user_id} (db_user_id: {db_user_id})")
        classifications = await classification_client.get_classifications(
            user_id=str(user_id)
        )
        
        if not classifications:
            return {
                "message": "No classifications found",
                "classifications_processed": 0,
                "tasks_created": 0,
                "followups_created": 0
            }
        
        logger.info(f"Found {len(classifications)} classifications for user {user_id}")
        
        tasks_created = 0
        followups_created = 0
        errors = []
        
        for cls in classifications:
            try:
                label = cls.get('label', '').lower()
                cls_id = str(cls.get('cls_id', ''))
                msg_id = str(cls.get('msg_id', ''))
                priority = cls.get('priority', 1)
                
                # Skip noise
                if label == 'noise':
                    logger.debug(f"Skipping noise classification {cls_id}")
                    continue
                
                # Convert priority from 1-10 scale to 1-5 scale
                priority_1_5 = min(max(priority // 2, 1), 5)
                
                # Try to get message details from integrations service
                message = None
                try:
                    message = await integrations_client.get_message(msg_id)
                except Exception as e:
                    logger.warning(f"Could not fetch message {msg_id} from integrations service: {e}")
                
                # Extract message details if available
                sender = message.get('sender', '') if message else ''
                subject = message.get('subject', None) if message else None
                message_type_str = message.get('type', 'email') if message else 'email'
                message_type = MessageType.EMAIL if message_type_str.lower() == 'email' else MessageType.SLACK
                
                # Generate title from message or use default
                if message and message.get('subject'):
                    title = message.get('subject', f"Task from {sender}")
                elif message and message.get('body'):
                    # Use first 100 chars of body as title
                    body = message.get('body', '')
                    title = body[:100] + ('...' if len(body) > 100 else '')
                else:
                    title = f"Task from classification {cls_id[:8]}"
                
                if label == 'todo':
                    # Create task
                    task = TaskCreate(
                        user_id=db_user_id,
                        source_msg_id=msg_id,
                        cls_id=cls_id,
                        title=title,
                        status=TaskStatus.OPEN,
                        priority=priority_1_5,
                        message_type=message_type,
                        sender=sender,
                        subject=subject
                    )
                    task_id = db.create_task(task)
                    if task_id:
                        tasks_created += 1
                        logger.info(f"Created task {task_id} from classification {cls_id}")
                    else:
                        errors.append(f"Failed to create task for classification {cls_id}")
                
                elif label == 'followup':
                    # Create followup
                    followup = FollowupCreate(
                        user_id=db_user_id,
                        source_msg_id=msg_id,
                        cls_id=cls_id,
                        title=title,
                        status=TaskStatus.OPEN,
                        priority=priority_1_5,
                        message_type=message_type,
                        sender=sender,
                        subject=subject
                    )
                    followup_id = db.create_followup(followup)
                    if followup_id:
                        followups_created += 1
                        logger.info(f"Created followup {followup_id} from classification {cls_id}")
                    else:
                        errors.append(f"Failed to create followup for classification {cls_id}")
                
            except Exception as e:
                error_msg = f"Error processing classification {cls.get('cls_id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = {
            "message": "Classifications synced successfully",
            "classifications_processed": len(classifications),
            "tasks_created": tasks_created,
            "followups_created": followups_created
        }
        
        if errors:
            result["errors"] = errors
            result["error_count"] = len(errors)
        
        return result
        
    except Exception as e:
        logger.error(f"Error syncing classifications: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync classifications: {str(e)}"
        )

