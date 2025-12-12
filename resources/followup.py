from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from typing import List, Optional
from models import FollowupCreate, FollowupResponse, FollowupUpdate, TaskStatus, MessageType
from services import DatabaseManager, IntegrationsClient

router = APIRouter(prefix="/followup", tags=["followup"])
db = DatabaseManager()
integrations_client = IntegrationsClient()


@router.post("", response_model=FollowupResponse, status_code=201)
async def create_followup(followup: FollowupCreate, response: Response):
    """Create a new followup"""
    followup_id = db.create_followup(followup)

    if followup_id is None:
        raise HTTPException(status_code=500, detail="Failed to create followup (DB error, check logs)")

    created_followup = db.get_followup(followup_id)
    if created_followup is None:
        raise HTTPException(status_code=500, detail="Failed to fetch created followup")

    # HTTP 201 best practice: send Location header
    response.headers["Location"] = f"/followup/{followup_id}"
    return created_followup


@router.get("/{followup_id}", response_model=FollowupResponse)
async def get_followup(followup_id: int):
    """Get a specific followup by ID"""
    followup = db.get_followup(followup_id)

    if followup is None:
        raise HTTPException(status_code=404, detail="Followup not found")

    return followup


@router.get("", response_model=List[FollowupResponse])
async def get_followups(
    user_id: Optional[str] = Query(None, description="Filter by user_id (UUID)"),
    followup_id: Optional[int] = Query(None, description="Filter by followup_id"),
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
    Get followups with optional filters on any attribute.
    Returns all followups matching the provided filters.
    """
    # Build filters dictionary from query parameters
    filters = {}
    
    if user_id is not None:
        filters['user_id'] = user_id
    if followup_id is not None:
        filters['followup_id'] = followup_id
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
    
    followups, total = db.get_followups(filters=filters, limit=limit, offset=offset)
    return followups


@router.put("/{followup_id}", response_model=FollowupResponse)
async def update_followup(followup_id: int, updates: FollowupUpdate):
    """Update a followup"""
    success = db.update_followup(followup_id, updates)
    
    if not success:
        raise HTTPException(status_code=404, detail="Followup not found or update failed")
    
    updated_followup = db.get_followup(followup_id)
    return updated_followup


@router.delete("/{followup_id}", status_code=204)
async def delete_followup(followup_id: int):
    """Delete a followup"""
    success = db.delete_followup(followup_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Followup not found")
    
    return JSONResponse(status_code=204, content=None)
