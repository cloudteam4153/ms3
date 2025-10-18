from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/followup", tags=["followup"])


@router.post("", status_code=501)
async def create_followup():
    """Create a new follow-up task - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/{followup_id}", status_code=501)
async def get_followup(followup_id: int):
    """Get a specific follow-up by ID - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("", status_code=501)
async def get_followups():
    """Get all follow-up tasks - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.put("/{followup_id}", status_code=501)
async def update_followup(followup_id: int):
    """Update a follow-up task - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.delete("/{followup_id}", status_code=501)
async def delete_followup(followup_id: int):
    """Delete a follow-up task - NOT IMPLEMENTED"""
    raise HTTPException(status_code=501, detail="Not Implemented")
