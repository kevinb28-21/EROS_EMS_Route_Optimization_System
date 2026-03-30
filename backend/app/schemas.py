"""
Pydantic schemas for API request/response validation.

These schemas define the API contract and handle serialization.
Following REST API design principles with clear separation of:
- Base schemas (shared fields)
- Create schemas (input for POST)
- Update schemas (input for PATCH, all fields optional)
- Response schemas (output with IDs and timestamps)
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models import (
    IncidentSeverity, IncidentStatus, 
    VehicleStatus, HospitalStatus
)


# =============================================================================
# Common/Shared Schemas
# =============================================================================

class LocationBase(BaseModel):
    """Base location fields used across entities."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class PaginatedResponse(BaseModel):
    """Standard pagination wrapper for list endpoints."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int
    
    @classmethod
    def create(cls, items: List[Any], total: int, page: int, page_size: int):
        """Factory method to create paginated response."""
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )


# =============================================================================
# Incident Schemas
# =============================================================================

class IncidentBase(BaseModel):
    """Base incident fields."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    description: str = Field(..., min_length=1, max_length=2000)
    severity: IncidentSeverity = IncidentSeverity.UNKNOWN


class IncidentCreate(IncidentBase):
    """Schema for creating a new incident."""
    pass


class IncidentUpdate(BaseModel):
    """Schema for updating an incident (all fields optional)."""
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = None
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    assigned_vehicle_id: Optional[int] = None
    destination_hospital_id: Optional[int] = None


class IncidentResponse(IncidentBase):
    """Schema for incident in API responses."""
    id: int
    status: IncidentStatus
    reported_at: datetime
    dispatched_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    assigned_vehicle_id: Optional[int] = None
    destination_hospital_id: Optional[int] = None
    route_data: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class IncidentWithDetails(IncidentResponse):
    """Incident response with related entity details."""
    assigned_vehicle: Optional["VehicleResponse"] = None
    destination_hospital: Optional["HospitalResponse"] = None


# =============================================================================
# Vehicle Schemas
# =============================================================================

class VehicleBase(BaseModel):
    """Base vehicle fields."""
    call_sign: str = Field(..., min_length=1, max_length=50)
    vehicle_type: str = Field(default="ALS", max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    crew_count: int = Field(default=2, ge=1, le=10)


class VehicleCreate(VehicleBase):
    """Schema for creating a new vehicle."""
    status: VehicleStatus = VehicleStatus.AVAILABLE


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle (all fields optional)."""
    call_sign: Optional[str] = Field(None, min_length=1, max_length=50)
    vehicle_type: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    status: Optional[VehicleStatus] = None
    crew_count: Optional[int] = Field(None, ge=1, le=10)


class VehicleResponse(VehicleBase):
    """Schema for vehicle in API responses."""
    id: int
    status: VehicleStatus
    route_progress: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Hospital Schemas
# =============================================================================

class HospitalBase(BaseModel):
    """Base hospital fields."""
    name: str = Field(..., min_length=1, max_length=200)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    total_er_beds: int = Field(default=20, ge=0)
    specialties: List[str] = Field(default_factory=list)
    is_trauma_center: bool = False


class HospitalCreate(HospitalBase):
    """Schema for creating a new hospital."""
    occupied_er_beds: int = Field(default=0, ge=0)
    status: HospitalStatus = HospitalStatus.OPEN


class HospitalUpdate(BaseModel):
    """Schema for updating a hospital (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = None
    total_er_beds: Optional[int] = Field(None, ge=0)
    occupied_er_beds: Optional[int] = Field(None, ge=0)
    status: Optional[HospitalStatus] = None
    specialties: Optional[List[str]] = None
    is_trauma_center: Optional[bool] = None


class HospitalResponse(HospitalBase):
    """Schema for hospital in API responses."""
    id: int
    occupied_er_beds: int
    status: HospitalStatus
    available_beds: int
    occupancy_rate: float
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm_with_computed(cls, hospital):
        """Create response with computed properties."""
        return cls(
            id=hospital.id,
            name=hospital.name,
            latitude=hospital.latitude,
            longitude=hospital.longitude,
            address=hospital.address,
            total_er_beds=hospital.total_er_beds,
            occupied_er_beds=hospital.occupied_er_beds,
            status=hospital.status,
            specialties=hospital.specialties or [],
            is_trauma_center=hospital.is_trauma_center,
            available_beds=hospital.available_beds,
            occupancy_rate=hospital.occupancy_rate,
            created_at=hospital.created_at,
            updated_at=hospital.updated_at
        )


# =============================================================================
# Status Update Schemas
# =============================================================================

class StatusUpdateBase(BaseModel):
    """Base status update fields."""
    message: str = Field(..., min_length=1, max_length=2000)
    update_type: str = Field(default="info", max_length=50)
    source: str = Field(default="system", max_length=100)


class StatusUpdateCreate(StatusUpdateBase):
    """Schema for creating a status update."""
    incident_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    hospital_id: Optional[int] = None


class StatusUpdateResponse(StatusUpdateBase):
    """Schema for status update in API responses."""
    id: int
    incident_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    hospital_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Route Schemas
# =============================================================================

class RouteRequest(BaseModel):
    """Request for route calculation."""
    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lng: float = Field(..., ge=-180, le=180)
    destination_lat: float = Field(..., ge=-90, le=90)
    destination_lng: float = Field(..., ge=-180, le=180)


class RouteResponse(BaseModel):
    """Response with calculated route."""
    origin: LocationBase
    destination: LocationBase
    distance_km: float
    estimated_time_minutes: float
    polyline: List[List[float]]  # List of [lat, lng] pairs
    traffic_level: Optional[str] = None
    traffic_description: Optional[str] = None
    route_source: Optional[str] = None  # osrm | graph | fallback


class HospitalRecommendation(BaseModel):
    """A hospital recommendation with scoring details."""
    hospital: HospitalResponse
    score: float
    distance_km: float
    estimated_time_minutes: float
    reasons: List[str]  # Why this hospital was recommended


class HospitalRecommendationRequest(BaseModel):
    """Request for hospital recommendations."""
    incident_id: int
    patient_needs: Optional[List[str]] = None  # e.g., ["trauma", "cardiac"]


class HospitalRecommendationResponse(BaseModel):
    """Response with ranked hospital recommendations."""
    incident_id: int
    recommendations: List[HospitalRecommendation]


# =============================================================================
# Assignment Schemas
# =============================================================================

class AssignVehicleRequest(BaseModel):
    """Request to assign a vehicle to an incident."""
    vehicle_id: int
    auto_route: bool = True  # Automatically calculate route


class AssignHospitalRequest(BaseModel):
    """Request to assign a destination hospital."""
    hospital_id: int
    auto_route: bool = True  # Automatically calculate route from scene


# Enable forward references
IncidentWithDetails.model_rebuild()
