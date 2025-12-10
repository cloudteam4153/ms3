from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from typing import List, Optional
from models import FollowupCreate, FollowupResponse, FollowupUpdate, TaskStatus
from services import DatabaseManager

router = APIRouter(prefix="/followup", tags=["followup"])
db = DatabaseManager()


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


@router.get("/{followup_id}")
async def get_followup(followup_id: int):
    """
    Get a specific followup by ID + linked data
    """
    followup = db.get_followup(followup_id)

    if followup is None:
        raise HTTPException(status_code=404, detail="Followup not found")

    return {
        **followup.model_dump(),
        "links": {
            "self": f"/followup/{followup.followup_id}",
            "owner": f"/users/{followup.user_id}",
            "task": f"/tasks?source_msg_id={followup.source_msg_id}",
            "todo": f"/todo?source_msg_id={followup.source_msg_id}",
        },
    }


@router.get("", response_model=List[FollowupResponse])
async def get_followups(
    user_id: int = Query(..., description="User ID to filter followups"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[int] = Query(None, ge=1, le=5, description="Minimum priority")
):
    """Get followups with optional filters"""
    followups, total = db.get_followups(user_id, status, priority)
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
