"""
Incident API endpoints.

Handles CRUD operations for emergency incidents and dispatch actions.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import random
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Incident, Vehicle, Hospital, StatusUpdate, IncidentStatus, VehicleStatus
from app.schemas import (
    IncidentCreate, IncidentUpdate, IncidentResponse, IncidentWithDetails,
    PaginatedResponse, AssignVehicleRequest, AssignHospitalRequest,
    VehicleResponse, HospitalResponse
)


router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[IncidentStatus] = Query(None),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all incidents with pagination and optional filtering.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **status**: Filter by incident status
    - **severity**: Filter by severity level
    """
    query = db.query(Incident)
    
    # Apply filters
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
    
    # Order by reported_at descending (newest first)
    query = query.order_by(Incident.reported_at.desc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    incidents = query.offset(offset).limit(page_size).all()
    
    # Convert to response schemas
    items = [IncidentResponse.model_validate(i) for i in incidents]
    
    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """
    Create a new incident.
    
    A new incident starts in PENDING status awaiting dispatch.
    """
    db_incident = Incident(
        latitude=incident.latitude,
        longitude=incident.longitude,
        address=incident.address,
        description=incident.description,
        severity=incident.severity,
        status=IncidentStatus.PENDING,
        reported_at=datetime.utcnow()
    )
    
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    
    # Log the creation
    log = StatusUpdate(
        incident_id=db_incident.id,
        message=f"Incident reported: {incident.description[:100]}",
        update_type="system",
        source="system"
    )
    db.add(log)
    db.commit()
    
    return IncidentResponse.model_validate(db_incident)


@router.get("/{incident_id}", response_model=IncidentWithDetails)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get a specific incident by ID with related entity details."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Incident {incident_id} not found"}
        )
    
    # Build response with related entities
    response = IncidentWithDetails.model_validate(incident)
    
    if incident.assigned_vehicle:
        response.assigned_vehicle = VehicleResponse.model_validate(incident.assigned_vehicle)
    
    if incident.destination_hospital:
        response.destination_hospital = HospitalResponse.from_orm_with_computed(
            incident.destination_hospital
        )
    
    return response


@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int, 
    update: IncidentUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update an incident's details.
    
    Only provided fields will be updated.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Incident {incident_id} not found"}
        )
    
    # Apply updates
    update_data = update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(incident, field, value)
    
    incident.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(incident)
    
    return IncidentResponse.model_validate(incident)


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    """Delete an incident."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Incident {incident_id} not found"}
        )
    
    # Free up the assigned vehicle if any
    if incident.assigned_vehicle:
        incident.assigned_vehicle.status = VehicleStatus.AVAILABLE
        incident.assigned_vehicle.route_progress = None
    
    db.delete(incident)
    db.commit()
    
    return None


@router.post("/{incident_id}/assign-vehicle", response_model=IncidentResponse)
def assign_vehicle(
    incident_id: int,
    request: AssignVehicleRequest,
    db: Session = Depends(get_db)
):
    """
    Assign a vehicle to an incident.
    
    The vehicle must be available, and optionally a route will be calculated.
    """
    # Get incident
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Incident {incident_id} not found"}
        )
    
    # Check incident can be assigned
    if incident.status not in [IncidentStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidState",
                "message": f"Cannot assign vehicle to incident in {incident.status} status"
            }
        )
    
    # Get vehicle
    vehicle = db.query(Vehicle).filter(Vehicle.id == request.vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Vehicle {request.vehicle_id} not found"}
        )
    
    # Check vehicle availability
    if vehicle.status != VehicleStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "VehicleUnavailable",
                "message": f"Vehicle {vehicle.call_sign} is not available (status: {vehicle.status})"
            }
        )
    
    # Assign vehicle
    incident.assigned_vehicle_id = vehicle.id
    incident.status = IncidentStatus.DISPATCHED
    incident.dispatched_at = datetime.utcnow()
    
    # Update vehicle status
    vehicle.status = VehicleStatus.DISPATCHED
    
    # Route + simulated driver timeline (road-following polyline, random ETA to on-scene)
    from app.services.routing import RoutingService
    routing = RoutingService()
    route = routing.calculate_route(
        vehicle.latitude, vehicle.longitude,
        incident.latitude, incident.longitude
    )
    if route:
        to_scene = {
            "polyline": route["polyline"],
            "distance_km": route["distance_km"],
            "estimated_time_minutes": route["estimated_time_minutes"],
            "traffic_level": route.get("traffic_level"),
            "traffic_description": route.get("traffic_description"),
        }
    else:
        pl = routing._densify_polyline(
            [[vehicle.latitude, vehicle.longitude], [incident.latitude, incident.longitude]]
        )
        to_scene = {
            "polyline": pl,
            "distance_km": routing.haversine_distance(
                vehicle.latitude, vehicle.longitude,
                incident.latitude, incident.longitude,
            ),
            "estimated_time_minutes": 1.0,
            "traffic_level": None,
            "traffic_description": None,
        }

    started = datetime.utcnow()
    delay_sec = random.randint(25, 120)
    scene_arrival = started + timedelta(seconds=delay_sec)

    incident.route_data = {
        "to_scene": to_scene,
        "driver_sim": {
            "polyline": to_scene["polyline"],
            "started_at": started.isoformat(),
            "scene_arrival_at": scene_arrival.isoformat(),
            "midpoint_logged": False,
        },
    }
    # Timer + interpolation drive movement; old per-tick waypoint list is not used
    vehicle.route_progress = None
    
    # Log the dispatch
    log = StatusUpdate(
        incident_id=incident.id,
        vehicle_id=vehicle.id,
        message=f"Vehicle {vehicle.call_sign} dispatched to incident",
        update_type="dispatch",
        source="dispatcher"
    )
    db.add(log)
    
    db.commit()
    db.refresh(incident)
    
    return IncidentResponse.model_validate(incident)


@router.post("/{incident_id}/assign-hospital", response_model=IncidentResponse)
def assign_hospital(
    incident_id: int,
    request: AssignHospitalRequest,
    db: Session = Depends(get_db)
):
    """
    Assign a destination hospital for patient transport.
    
    Should be called when vehicle is on scene and patient needs transport.
    """
    # Get incident
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Incident {incident_id} not found"}
        )
    
    # Get hospital
    hospital = db.query(Hospital).filter(Hospital.id == request.hospital_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Hospital {request.hospital_id} not found"}
        )
    
    # Assign hospital
    incident.destination_hospital_id = hospital.id
    
    # Calculate route to hospital if requested and vehicle is assigned
    if request.auto_route and incident.assigned_vehicle:
        from app.services.routing import RoutingService
        routing = RoutingService()
        
        # Route from incident scene to hospital
        route = routing.calculate_route(
            incident.latitude, incident.longitude,
            hospital.latitude, hospital.longitude
        )
        
        if route:
            # Add hospital route to route_data
            route_data = incident.route_data or {}
            route_data["to_hospital"] = {
                "polyline": route["polyline"],
                "distance_km": route["distance_km"],
                "estimated_time_minutes": route["estimated_time_minutes"],
                "traffic_level": route.get("traffic_level"),
                "traffic_description": route.get("traffic_description"),
            }
            incident.route_data = route_data
    
    # Log the assignment
    log = StatusUpdate(
        incident_id=incident.id,
        hospital_id=hospital.id,
        message=f"Destination set to {hospital.name}",
        update_type="info",
        source="dispatcher"
    )
    db.add(log)
    
    db.commit()
    db.refresh(incident)
    
    return IncidentResponse.model_validate(incident)


@router.post("/{incident_id}/update-status", response_model=IncidentResponse)
def update_incident_status(
    incident_id: int,
    new_status: IncidentStatus,
    db: Session = Depends(get_db)
):
    """
    Update the status of an incident.
    
    Handles state transitions and updates related vehicle status.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Incident {incident_id} not found"}
        )
    
    old_status = incident.status
    incident.status = new_status
    
    # Handle status-specific updates
    if new_status == IncidentStatus.ON_SCENE and incident.assigned_vehicle:
        incident.assigned_vehicle.status = VehicleStatus.ON_SCENE
        
    elif new_status == IncidentStatus.TRANSPORTING and incident.assigned_vehicle:
        incident.assigned_vehicle.status = VehicleStatus.TRANSPORTING
        
    elif new_status == IncidentStatus.COMPLETED:
        incident.resolved_at = datetime.utcnow()
        if incident.assigned_vehicle:
            incident.assigned_vehicle.status = VehicleStatus.AVAILABLE
            incident.assigned_vehicle.route_progress = None
            
    elif new_status == IncidentStatus.CANCELLED:
        incident.resolved_at = datetime.utcnow()
        if incident.assigned_vehicle:
            incident.assigned_vehicle.status = VehicleStatus.AVAILABLE
            incident.assigned_vehicle.route_progress = None
    
    # Log the status change
    log = StatusUpdate(
        incident_id=incident.id,
        message=f"Status changed: {old_status.value} → {new_status.value}",
        update_type="info",
        source="system"
    )
    db.add(log)
    
    db.commit()
    db.refresh(incident)
    
    return IncidentResponse.model_validate(incident)
