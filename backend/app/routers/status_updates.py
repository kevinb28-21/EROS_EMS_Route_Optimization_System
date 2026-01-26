"""
Status Update API endpoints.

Handles the event log / communication system.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StatusUpdate
from app.schemas import (
    StatusUpdateCreate, StatusUpdateResponse,
    PaginatedResponse
)


router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def list_status_updates(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    incident_id: Optional[int] = Query(None),
    vehicle_id: Optional[int] = Query(None),
    hospital_id: Optional[int] = Query(None),
    update_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List status updates with pagination and optional filtering.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 200)
    - **incident_id**: Filter by incident
    - **vehicle_id**: Filter by vehicle
    - **hospital_id**: Filter by hospital
    - **update_type**: Filter by update type (info, dispatch, arrival, alert, system)
    """
    query = db.query(StatusUpdate)
    
    # Apply filters
    if incident_id is not None:
        query = query.filter(StatusUpdate.incident_id == incident_id)
    if vehicle_id is not None:
        query = query.filter(StatusUpdate.vehicle_id == vehicle_id)
    if hospital_id is not None:
        query = query.filter(StatusUpdate.hospital_id == hospital_id)
    if update_type:
        query = query.filter(StatusUpdate.update_type == update_type)
    
    # Order by created_at descending (newest first)
    query = query.order_by(StatusUpdate.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    updates = query.offset(offset).limit(page_size).all()
    
    # Convert to response schemas
    items = [StatusUpdateResponse.model_validate(u) for u in updates]
    
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/recent", response_model=list[StatusUpdateResponse])
def get_recent_updates(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get the most recent status updates.
    
    Convenience endpoint for the dashboard event feed.
    """
    updates = db.query(StatusUpdate).order_by(
        StatusUpdate.created_at.desc()
    ).limit(limit).all()
    
    return [StatusUpdateResponse.model_validate(u) for u in updates]


@router.post("", response_model=StatusUpdateResponse, status_code=status.HTTP_201_CREATED)
def create_status_update(update: StatusUpdateCreate, db: Session = Depends(get_db)):
    """
    Create a new status update / log entry.
    
    Used to record dispatcher notes, system events, and communications.
    """
    db_update = StatusUpdate(
        incident_id=update.incident_id,
        vehicle_id=update.vehicle_id,
        hospital_id=update.hospital_id,
        message=update.message,
        update_type=update.update_type,
        source=update.source
    )
    
    db.add(db_update)
    db.commit()
    db.refresh(db_update)
    
    return StatusUpdateResponse.model_validate(db_update)


@router.get("/{update_id}", response_model=StatusUpdateResponse)
def get_status_update(update_id: int, db: Session = Depends(get_db)):
    """Get a specific status update by ID."""
    update = db.query(StatusUpdate).filter(StatusUpdate.id == update_id).first()
    
    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Status update {update_id} not found"}
        )
    
    return StatusUpdateResponse.model_validate(update)
