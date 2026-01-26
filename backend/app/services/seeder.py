"""
Database Seeder - Populates demo data for presentations.

Seeds the database with:
- Hospitals in downtown Toronto
- EMS vehicles with call signs
- Sample incidents at various states

This data makes the system "alive" for demos.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import (
    Hospital, Vehicle, Incident, StatusUpdate,
    HospitalStatus, VehicleStatus, IncidentStatus, IncidentSeverity
)


def seed_demo_data():
    """
    Seed the database with demo data if empty.
    
    Only seeds if there are no hospitals (assumes fresh database).
    """
    db = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(Hospital).count() > 0:
            print("📊 Database already has data, skipping seed")
            return
        
        print("🌱 Seeding demo data...")
        
        # Seed hospitals
        hospitals = _seed_hospitals(db)
        print(f"   ✅ Created {len(hospitals)} hospitals")
        
        # Seed vehicles
        vehicles = _seed_vehicles(db)
        print(f"   ✅ Created {len(vehicles)} vehicles")
        
        # Seed sample incidents
        incidents = _seed_incidents(db, vehicles, hospitals)
        print(f"   ✅ Created {len(incidents)} incidents")
        
        db.commit()
        print("✅ Demo data seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()


def _seed_hospitals(db: Session) -> list[Hospital]:
    """Create hospitals in downtown Toronto."""
    hospitals_data = [
        {
            "name": "Toronto General Hospital",
            "latitude": 43.6600,
            "longitude": -79.3885,
            "address": "200 Elizabeth St, Toronto, ON",
            "total_er_beds": 30,
            "occupied_er_beds": 18,
            "specialties": ["trauma", "cardiac", "stroke", "transplant"],
            "is_trauma_center": True
        },
        {
            "name": "St. Michael's Hospital",
            "latitude": 43.6538,
            "longitude": -79.3775,
            "address": "36 Queen St E, Toronto, ON",
            "total_er_beds": 25,
            "occupied_er_beds": 15,
            "specialties": ["trauma", "cardiac", "neurosurgery"],
            "is_trauma_center": True
        },
        {
            "name": "Mount Sinai Hospital",
            "latitude": 43.6585,
            "longitude": -79.3895,
            "address": "600 University Ave, Toronto, ON",
            "total_er_beds": 20,
            "occupied_er_beds": 12,
            "specialties": ["obstetrics", "oncology", "orthopedics"],
            "is_trauma_center": False
        },
        {
            "name": "SickKids Hospital",
            "latitude": 43.6568,
            "longitude": -79.3878,
            "address": "555 University Ave, Toronto, ON",
            "total_er_beds": 35,
            "occupied_er_beds": 20,
            "specialties": ["pediatric", "pediatric trauma", "pediatric cardiac"],
            "is_trauma_center": True
        },
        {
            "name": "Women's College Hospital",
            "latitude": 43.6615,
            "longitude": -79.3890,
            "address": "76 Grenville St, Toronto, ON",
            "total_er_beds": 15,
            "occupied_er_beds": 8,
            "specialties": ["obstetrics", "gynecology", "mental health"],
            "is_trauma_center": False
        },
        {
            "name": "Toronto Western Hospital",
            "latitude": 43.6535,
            "longitude": -79.4055,
            "address": "399 Bathurst St, Toronto, ON",
            "total_er_beds": 22,
            "occupied_er_beds": 16,
            "specialties": ["neurology", "orthopedics", "stroke"],
            "is_trauma_center": False
        },
    ]
    
    hospitals = []
    for data in hospitals_data:
        hospital = Hospital(**data, status=HospitalStatus.OPEN)
        db.add(hospital)
        hospitals.append(hospital)
    
    db.flush()  # Get IDs
    return hospitals


def _seed_vehicles(db: Session) -> list[Vehicle]:
    """Create EMS vehicles positioned around downtown Toronto."""
    vehicles_data = [
        {
            "call_sign": "MEDIC-01",
            "vehicle_type": "ALS",
            "latitude": 43.6480,
            "longitude": -79.3810,
            "status": VehicleStatus.AVAILABLE,
            "crew_count": 2
        },
        {
            "call_sign": "MEDIC-02",
            "vehicle_type": "ALS",
            "latitude": 43.6550,
            "longitude": -79.3950,
            "status": VehicleStatus.AVAILABLE,
            "crew_count": 2
        },
        {
            "call_sign": "MEDIC-03",
            "vehicle_type": "BLS",
            "latitude": 43.6620,
            "longitude": -79.3870,
            "status": VehicleStatus.AVAILABLE,
            "crew_count": 2
        },
        {
            "call_sign": "MEDIC-04",
            "vehicle_type": "ALS",
            "latitude": 43.6510,
            "longitude": -79.3750,
            "status": VehicleStatus.AVAILABLE,
            "crew_count": 2
        },
        {
            "call_sign": "MEDIC-05",
            "vehicle_type": "BLS",
            "latitude": 43.6590,
            "longitude": -79.4010,
            "status": VehicleStatus.AVAILABLE,
            "crew_count": 2
        },
        {
            "call_sign": "RESCUE-01",
            "vehicle_type": "Heavy Rescue",
            "latitude": 43.6500,
            "longitude": -79.3850,
            "status": VehicleStatus.AVAILABLE,
            "crew_count": 3
        },
        {
            "call_sign": "SUPER-01",
            "vehicle_type": "Supervisor",
            "latitude": 43.6560,
            "longitude": -79.3820,
            "status": VehicleStatus.AVAILABLE,
            "crew_count": 1
        },
        {
            "call_sign": "MEDIC-06",
            "vehicle_type": "ALS",
            "latitude": 43.6700,
            "longitude": -79.3860,
            "status": VehicleStatus.OFF_DUTY,
            "crew_count": 2
        },
    ]
    
    vehicles = []
    for data in vehicles_data:
        vehicle = Vehicle(**data)
        db.add(vehicle)
        vehicles.append(vehicle)
    
    db.flush()
    return vehicles


def _seed_incidents(
    db: Session, 
    vehicles: list[Vehicle], 
    hospitals: list[Hospital]
) -> list[Incident]:
    """Create sample incidents at various stages."""
    now = datetime.utcnow()
    
    incidents_data = [
        # Active incidents
        {
            "latitude": 43.6530,
            "longitude": -79.3800,
            "address": "Queen St & Bay St, Toronto",
            "description": "Chest pain, 65-year-old male, conscious and alert",
            "severity": IncidentSeverity.MAJOR,
            "status": IncidentStatus.PENDING,
            "reported_at": now - timedelta(minutes=2)
        },
        {
            "latitude": 43.6570,
            "longitude": -79.3920,
            "address": "Dundas St & University Ave, Toronto",
            "description": "Motor vehicle collision, multiple patients reported",
            "severity": IncidentSeverity.CRITICAL,
            "status": IncidentStatus.PENDING,
            "reported_at": now - timedelta(minutes=5)
        },
        {
            "latitude": 43.6610,
            "longitude": -79.3850,
            "address": "College St & Yonge St, Toronto",
            "description": "Fall from height, construction site, patient unconscious",
            "severity": IncidentSeverity.CRITICAL,
            "status": IncidentStatus.PENDING,
            "reported_at": now - timedelta(minutes=1)
        },
        {
            "latitude": 43.6490,
            "longitude": -79.3780,
            "address": "King St & Church St, Toronto",
            "description": "Difficulty breathing, 45-year-old female, history of asthma",
            "severity": IncidentSeverity.MAJOR,
            "status": IncidentStatus.PENDING,
            "reported_at": now - timedelta(minutes=8)
        },
        {
            "latitude": 43.6650,
            "longitude": -79.4000,
            "address": "Bloor St & Spadina Ave, Toronto",
            "description": "Allergic reaction, swelling observed, patient has EpiPen",
            "severity": IncidentSeverity.MAJOR,
            "status": IncidentStatus.PENDING,
            "reported_at": now - timedelta(minutes=3)
        },
        # Minor incident
        {
            "latitude": 43.6440,
            "longitude": -79.3730,
            "address": "Front St & Jarvis St, Toronto",
            "description": "Minor laceration from broken glass, bleeding controlled",
            "severity": IncidentSeverity.MINOR,
            "status": IncidentStatus.PENDING,
            "reported_at": now - timedelta(minutes=15)
        },
    ]
    
    incidents = []
    for data in incidents_data:
        incident = Incident(**data)
        db.add(incident)
        incidents.append(incident)
        
        # Add status update for the incident
        log = StatusUpdate(
            incident=incident,
            message=f"Incident reported: {data['description'][:80]}",
            update_type="system",
            source="system"
        )
        db.add(log)
    
    db.flush()
    return incidents
