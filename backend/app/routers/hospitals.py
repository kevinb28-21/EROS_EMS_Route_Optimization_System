"""
Hospital API endpoints.

Handles CRUD operations for hospitals and capacity tracking.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Hospital, HospitalStatus
from app.schemas import (
    HospitalCreate, HospitalUpdate, HospitalResponse,
    PaginatedResponse, HospitalRecommendationRequest, HospitalRecommendationResponse
)


router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def list_hospitals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[HospitalStatus] = Query(None),
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    db: Session = Depends(get_db)
):
    """
    List all hospitals with pagination and optional filtering.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **status**: Filter by hospital status
    - **specialty**: Filter by specialty (e.g., "trauma", "cardiac")
    """
    query = db.query(Hospital)
    
    # Apply filters
    if status:
        query = query.filter(Hospital.status == status)
    
    # Filter by specialty (JSON array contains)
    # Note: This is a simple implementation; for production, use proper JSON querying
    if specialty:
        # SQLite doesn't support JSON operators well, so we filter in Python
        all_hospitals = query.all()
        filtered = [
            h for h in all_hospitals 
            if h.specialties and specialty.lower() in [s.lower() for s in h.specialties]
        ]
        total = len(filtered)
        offset = (page - 1) * page_size
        hospitals = filtered[offset:offset + page_size]
    else:
        # Order by name
        query = query.order_by(Hospital.name)
        total = query.count()
        offset = (page - 1) * page_size
        hospitals = query.offset(offset).limit(page_size).all()
    
    # Convert to response schemas with computed properties
    items = [HospitalResponse.from_orm_with_computed(h) for h in hospitals]
    
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/accepting", response_model=list[HospitalResponse])
def list_accepting_hospitals(db: Session = Depends(get_db)):
    """
    Get all hospitals currently accepting patients.
    
    Convenience endpoint for dispatch decisions.
    """
    hospitals = db.query(Hospital).filter(
        Hospital.status == HospitalStatus.OPEN
    ).order_by(Hospital.name).all()
    
    return [HospitalResponse.from_orm_with_computed(h) for h in hospitals]


@router.post("", response_model=HospitalResponse, status_code=status.HTTP_201_CREATED)
def create_hospital(hospital: HospitalCreate, db: Session = Depends(get_db)):
    """Create a new hospital."""
    db_hospital = Hospital(
        name=hospital.name,
        latitude=hospital.latitude,
        longitude=hospital.longitude,
        address=hospital.address,
        total_er_beds=hospital.total_er_beds,
        occupied_er_beds=hospital.occupied_er_beds,
        status=hospital.status,
        specialties=hospital.specialties,
        is_trauma_center=hospital.is_trauma_center
    )
    
    db.add(db_hospital)
    db.commit()
    db.refresh(db_hospital)
    
    return HospitalResponse.from_orm_with_computed(db_hospital)


@router.get("/{hospital_id}", response_model=HospitalResponse)
def get_hospital(hospital_id: int, db: Session = Depends(get_db)):
    """Get a specific hospital by ID."""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Hospital {hospital_id} not found"}
        )
    
    return HospitalResponse.from_orm_with_computed(hospital)


@router.patch("/{hospital_id}", response_model=HospitalResponse)
def update_hospital(
    hospital_id: int,
    update: HospitalUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a hospital's details.
    
    Only provided fields will be updated.
    """
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Hospital {hospital_id} not found"}
        )
    
    # Apply updates
    update_data = update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(hospital, field, value)
    
    hospital.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(hospital)
    
    return HospitalResponse.from_orm_with_computed(hospital)


@router.delete("/{hospital_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hospital(hospital_id: int, db: Session = Depends(get_db)):
    """Delete a hospital."""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Hospital {hospital_id} not found"}
        )
    
    db.delete(hospital)
    db.commit()
    
    return None


@router.post("/{hospital_id}/update-capacity", response_model=HospitalResponse)
def update_capacity(
    hospital_id: int,
    occupied_beds: int,
    db: Session = Depends(get_db)
):
    """
    Update a hospital's current ER bed occupancy.
    
    Used by simulation or manual updates to track capacity.
    """
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Hospital {hospital_id} not found"}
        )
    
    if occupied_beds < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InvalidValue", "message": "Occupied beds cannot be negative"}
        )
    
    if occupied_beds > hospital.total_er_beds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"Occupied beds ({occupied_beds}) cannot exceed total beds ({hospital.total_er_beds})"
            }
        )
    
    hospital.occupied_er_beds = occupied_beds
    hospital.updated_at = datetime.utcnow()
    
    # Auto-set diversion status if over threshold
    occupancy = (occupied_beds / hospital.total_er_beds) * 100 if hospital.total_er_beds > 0 else 100
    if occupancy >= 95 and hospital.status == HospitalStatus.OPEN:
        hospital.status = HospitalStatus.DIVERSION
    elif occupancy < 85 and hospital.status == HospitalStatus.DIVERSION:
        hospital.status = HospitalStatus.OPEN
    
    db.commit()
    db.refresh(hospital)
    
    return HospitalResponse.from_orm_with_computed(hospital)


@router.post("/recommend", response_model=HospitalRecommendationResponse)
def recommend_hospitals(
    request: HospitalRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Get hospital recommendations for an incident.
    
    Recommends hospitals based on:
    - Distance from incident
    - Current capacity/availability
    - Required specialties
    - Trauma center designation
    """
    from app.models import Incident
    from app.services.hospital_recommender import HospitalRecommender
    
    # Get incident
    incident = db.query(Incident).filter(Incident.id == request.incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Incident {request.incident_id} not found"}
        )
    
    # Get all open hospitals
    hospitals = db.query(Hospital).filter(Hospital.status == HospitalStatus.OPEN).all()
    
    # Get recommendations
    recommender = HospitalRecommender()
    recommendations = recommender.recommend(
        incident_lat=incident.latitude,
        incident_lng=incident.longitude,
        incident_severity=incident.severity,
        patient_needs=request.patient_needs or [],
        hospitals=hospitals
    )
    
    return HospitalRecommendationResponse(
        incident_id=request.incident_id,
        recommendations=recommendations
    )
