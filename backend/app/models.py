"""
SQLAlchemy database models for EROS.

Entities:
- Incident: Emergency incidents requiring EMS response
- Vehicle: EMS vehicles (ambulances)
- Hospital: Medical facilities with capacity tracking
- StatusUpdate: Log of status changes and communications
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, 
    Enum, ForeignKey, Boolean, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class IncidentSeverity(str, PyEnum):
    """Severity levels for incidents (affects priority and hospital selection)."""
    CRITICAL = "critical"  # Life-threatening, needs immediate advanced care
    MAJOR = "major"        # Serious but stable, needs hospital care
    MINOR = "minor"        # Non-life-threatening, may be treated on scene
    UNKNOWN = "unknown"    # Severity not yet assessed


class IncidentStatus(str, PyEnum):
    """Lifecycle status of an incident."""
    PENDING = "pending"          # Reported, awaiting dispatch
    DISPATCHED = "dispatched"    # Vehicle assigned, en route to scene
    ON_SCENE = "on_scene"        # Vehicle arrived at incident
    TRANSPORTING = "transporting"  # Patient being transported to hospital
    COMPLETED = "completed"      # Incident resolved
    CANCELLED = "cancelled"      # Incident cancelled (false alarm, etc.)


class VehicleStatus(str, PyEnum):
    """Status of an EMS vehicle."""
    AVAILABLE = "available"      # Ready for dispatch
    DISPATCHED = "dispatched"    # Assigned to incident, en route
    ON_SCENE = "on_scene"        # At incident location
    TRANSPORTING = "transporting"  # Transporting patient
    AT_HOSPITAL = "at_hospital"  # At hospital, patient handoff
    OFF_DUTY = "off_duty"        # Not available for dispatch


class HospitalStatus(str, PyEnum):
    """Operational status of a hospital."""
    OPEN = "open"                # Accepting patients
    DIVERSION = "diversion"      # Not accepting new patients (overloaded)
    CLOSED = "closed"            # Closed (rare, for disasters)


class Incident(Base):
    """
    An emergency incident requiring EMS response.
    
    Incidents are the core dispatch unit - they represent a call for help
    at a specific location that needs to be assigned to a vehicle.
    """
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(500), nullable=True)  # Human-readable address
    
    # Incident details
    description = Column(Text, nullable=False)
    severity = Column(Enum(IncidentSeverity), default=IncidentSeverity.UNKNOWN)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.PENDING)
    
    # Timing
    reported_at = Column(DateTime, default=datetime.utcnow)
    dispatched_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    assigned_vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    assigned_vehicle = relationship("Vehicle", back_populates="current_incident")
    
    destination_hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    destination_hospital = relationship("Hospital", back_populates="incoming_incidents")
    
    # Route data (stored as JSON for flexibility)
    # Contains: polyline coordinates, estimated time, distance
    route_data = Column(JSON, nullable=True)
    
    status_updates = relationship("StatusUpdate", back_populates="incident", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Vehicle(Base):
    """
    An EMS vehicle (ambulance).
    
    Tracks real-time position and status. Can be assigned to incidents
    and routes are calculated from their current position.
    """
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identification
    call_sign = Column(String(50), unique=True, nullable=False)  # e.g., "MEDIC-12"
    vehicle_type = Column(String(100), default="ALS")  # ALS, BLS, etc.
    
    # Current position (updated in real-time during simulation)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Status
    status = Column(Enum(VehicleStatus), default=VehicleStatus.AVAILABLE)
    
    # Current assignment
    current_incident = relationship("Incident", back_populates="assigned_vehicle", uselist=False)
    
    # Crew info (simplified)
    crew_count = Column(Integer, default=2)
    
    # For simulation: route progress
    # If vehicle is en route, this stores the remaining route waypoints
    route_progress = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Hospital(Base):
    """
    A hospital/medical facility.
    
    Tracks capacity and specialties to inform destination recommendations.
    The recommender considers distance, current load, and patient needs.
    """
    __tablename__ = "hospitals"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String(200), nullable=False)
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(500), nullable=True)
    
    # Capacity tracking
    total_er_beds = Column(Integer, default=20)
    occupied_er_beds = Column(Integer, default=0)
    
    # Status
    status = Column(Enum(HospitalStatus), default=HospitalStatus.OPEN)
    
    # Specialties (e.g., ["trauma", "cardiac", "pediatric", "stroke"])
    specialties = Column(JSON, default=list)
    
    # Is this a trauma center?
    is_trauma_center = Column(Boolean, default=False)
    
    # Incoming incidents (patients being transported here)
    incoming_incidents = relationship("Incident", back_populates="destination_hospital")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def available_beds(self) -> int:
        """Calculate available ER beds."""
        return max(0, self.total_er_beds - self.occupied_er_beds)
    
    @property
    def occupancy_rate(self) -> float:
        """Calculate ER occupancy as a percentage."""
        if self.total_er_beds == 0:
            return 100.0
        return (self.occupied_er_beds / self.total_er_beds) * 100


class StatusUpdate(Base):
    """
    A log entry for status changes and communications.
    
    Provides an audit trail and mimics dispatcher-unit communication.
    This is a simplified log, not a full chat system.
    """
    __tablename__ = "status_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # What this update relates to
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    incident = relationship("Incident", back_populates="status_updates")
    
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    
    # Update content
    message = Column(Text, nullable=False)
    update_type = Column(String(50), default="info")  # info, dispatch, arrival, alert, system
    
    # Who/what generated this update
    source = Column(String(100), default="system")  # system, dispatcher, vehicle, hospital
    
    created_at = Column(DateTime, default=datetime.utcnow)
