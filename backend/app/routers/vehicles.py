"""
Vehicle API endpoints.

Handles CRUD operations for EMS vehicles (ambulances).
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Vehicle, VehicleStatus
from app.schemas import (
    VehicleCreate, VehicleUpdate, VehicleResponse,
    PaginatedResponse
)


router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def list_vehicles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[VehicleStatus] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all vehicles with pagination and optional filtering.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **status**: Filter by vehicle status
    """
    query = db.query(Vehicle)
    
    # Apply filters
    if status:
        query = query.filter(Vehicle.status == status)
    
    # Order by call_sign
    query = query.order_by(Vehicle.call_sign)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    vehicles = query.offset(offset).limit(page_size).all()
    
    # Convert to response schemas
    items = [VehicleResponse.model_validate(v) for v in vehicles]
    
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/available", response_model=list[VehicleResponse])
def list_available_vehicles(db: Session = Depends(get_db)):
    """
    Get all available vehicles for dispatch.
    
    Convenience endpoint for the dispatch UI.
    """
    vehicles = db.query(Vehicle).filter(
        Vehicle.status == VehicleStatus.AVAILABLE
    ).order_by(Vehicle.call_sign).all()
    
    return [VehicleResponse.model_validate(v) for v in vehicles]


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    """Create a new vehicle."""
    # Check for duplicate call sign
    existing = db.query(Vehicle).filter(Vehicle.call_sign == vehicle.call_sign).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Conflict",
                "message": f"Vehicle with call sign '{vehicle.call_sign}' already exists"
            }
        )
    
    db_vehicle = Vehicle(
        call_sign=vehicle.call_sign,
        vehicle_type=vehicle.vehicle_type,
        latitude=vehicle.latitude,
        longitude=vehicle.longitude,
        status=vehicle.status,
        crew_count=vehicle.crew_count
    )
    
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    
    return VehicleResponse.model_validate(db_vehicle)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Get a specific vehicle by ID."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Vehicle {vehicle_id} not found"}
        )
    
    return VehicleResponse.model_validate(vehicle)


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    update: VehicleUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a vehicle's details.
    
    Only provided fields will be updated.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Vehicle {vehicle_id} not found"}
        )
    
    # Check for call_sign conflict if updating
    update_data = update.model_dump(exclude_unset=True)
    if "call_sign" in update_data:
        existing = db.query(Vehicle).filter(
            Vehicle.call_sign == update_data["call_sign"],
            Vehicle.id != vehicle_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Conflict",
                    "message": f"Vehicle with call sign '{update_data['call_sign']}' already exists"
                }
            )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(vehicle, field, value)
    
    vehicle.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(vehicle)
    
    return VehicleResponse.model_validate(vehicle)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Delete a vehicle."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Vehicle {vehicle_id} not found"}
        )
    
    # Check if vehicle is currently assigned
    if vehicle.status not in [VehicleStatus.AVAILABLE, VehicleStatus.OFF_DUTY]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "VehicleBusy",
                "message": f"Cannot delete vehicle {vehicle.call_sign} - currently {vehicle.status}"
            }
        )
    
    db.delete(vehicle)
    db.commit()
    
    return None


@router.post("/{vehicle_id}/update-position", response_model=VehicleResponse)
def update_position(
    vehicle_id: int,
    latitude: float,
    longitude: float,
    db: Session = Depends(get_db)
):
    """
    Update a vehicle's current position.
    
    Used by simulation or real GPS tracking to update vehicle location.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Vehicle {vehicle_id} not found"}
        )
    
    vehicle.latitude = latitude
    vehicle.longitude = longitude
    vehicle.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(vehicle)
    
    return VehicleResponse.model_validate(vehicle)
