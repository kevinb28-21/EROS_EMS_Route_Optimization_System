"""
Simulation Engine - Makes the demo "alive".

Provides background simulation for:
- Vehicle movement along routes
- Hospital capacity fluctuations
- Random incident generation (optional)

This is designed for course project demos, not production use.
"""

import random
import asyncio
from datetime import datetime
from typing import Optional, List, Tuple, Any, Dict
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import (
    Vehicle, Hospital, Incident, StatusUpdate,
    VehicleStatus, HospitalStatus, IncidentStatus, IncidentSeverity
)
from app.services.routing import RoutingService


class SimulationEngine:
    """
    Background simulation engine for demo purposes.
    
    Runs periodic updates to simulate:
    - Vehicles moving along their assigned routes
    - Hospital bed occupancy changes
    - Optional: new incident generation
    """
    
    def __init__(self, interval_seconds: int = 5):
        """
        Initialize the simulation engine.
        
        Args:
            interval_seconds: How often to run simulation updates
        """
        self.interval = interval_seconds
        self.routing = RoutingService()
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the simulation loop."""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._simulation_loop())
        print(f"🎮 Simulation engine started (interval: {self.interval}s)")
    
    async def stop(self):
        """Stop the simulation loop."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("🛑 Simulation engine stopped")
    
    async def _simulation_loop(self):
        """Main simulation loop."""
        while self.running:
            try:
                await self._run_simulation_tick()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Simulation error: {e}")
                await asyncio.sleep(self.interval)
    
    async def _run_simulation_tick(self):
        """Run a single simulation tick."""
        db = SessionLocal()
        try:
            # Timer-based dispatch → on-scene (driver sim along road polyline)
            self._update_driver_simulation(db)
            # Legacy waypoint movement (transport / no driver_sim)
            self._update_vehicle_positions(db)

            # Fluctuate hospital capacity
            self._fluctuate_hospital_capacity(db)

            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    @staticmethod
    def _position_on_polyline(polyline: List[List[float]], t: float) -> Tuple[float, float]:
        """Linear interpolation along polyline, t in [0, 1]."""
        t = max(0.0, min(1.0, t))
        if not polyline:
            return 0.0, 0.0
        if len(polyline) == 1:
            return polyline[0][0], polyline[0][1]
        idx = t * (len(polyline) - 1)
        i = int(idx)
        f = idx - i
        if i >= len(polyline) - 1:
            return polyline[-1][0], polyline[-1][1]
        a, b = polyline[i], polyline[i + 1]
        return (
            a[0] + f * (b[0] - a[0]),
            a[1] + f * (b[1] - a[1]),
        )

    def _parse_dt(self, s: str) -> datetime:
        """Parse naive UTC ISO from incident JSON."""
        if not s:
            return datetime.utcnow()
        s = s.replace("Z", "")
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return datetime.utcnow()

    def _update_driver_simulation(self, db: Session):
        """
        Move dispatched units along the densified road polyline and auto-transition
        to on-scene when the random ETA elapses (simulated radio / MDT updates).
        """
        incidents = (
            db.query(Incident)
            .filter(Incident.status == IncidentStatus.DISPATCHED)
            .all()
        )
        now = datetime.utcnow()

        for incident in incidents:
            rd: Optional[Dict[str, Any]] = incident.route_data
            if not rd or "driver_sim" not in rd:
                continue
            ds = rd["driver_sim"]
            if not ds:
                continue

            vehicle = incident.assigned_vehicle
            if not vehicle:
                continue

            poly = ds.get("polyline") or []
            if len(poly) < 2:
                continue

            start = self._parse_dt(ds.get("started_at", ""))
            end = self._parse_dt(ds.get("scene_arrival_at", ""))
            total_sec = max(1.0, (end - start).total_seconds())
            elapsed = (now - start).total_seconds()

            if now >= end:
                vehicle.latitude = incident.latitude
                vehicle.longitude = incident.longitude
                vehicle.status = VehicleStatus.ON_SCENE
                vehicle.updated_at = now
                incident.status = IncidentStatus.ON_SCENE
                incident.updated_at = now
                # Clear driver sim; keep to_scene polyline for map history
                rd["driver_sim"] = None
                incident.route_data = rd
                log = StatusUpdate(
                    incident_id=incident.id,
                    vehicle_id=vehicle.id,
                    message=f"{vehicle.call_sign} on scene — unit arrived (simulated)",
                    update_type="arrival",
                    source="unit",
                )
                db.add(log)
                continue

            t_prog = min(1.0, max(0.0, elapsed / total_sec))
            lat, lng = self._position_on_polyline(poly, t_prog)
            vehicle.latitude = lat
            vehicle.longitude = lng
            vehicle.updated_at = now

            # Mid-route radio-style update once per run
            if t_prog >= 0.45 and not ds.get("midpoint_logged"):
                ds["midpoint_logged"] = True
                eta_left = max(0, int((end - now).total_seconds()))
                log = StatusUpdate(
                    incident_id=incident.id,
                    vehicle_id=vehicle.id,
                    message=(
                        f"{vehicle.call_sign} en route — ETA ~{eta_left}s "
                        f"(simulated driver update)"
                    ),
                    update_type="radio",
                    source="unit",
                )
                db.add(log)
                rd["driver_sim"] = ds
                incident.route_data = rd

    def _update_vehicle_positions(self, db: Session):
        """
        Move vehicles along their routes.
        
        Vehicles with route_progress data will advance one waypoint
        per simulation tick.
        """
        vehicles = db.query(Vehicle).filter(
            Vehicle.status.in_([
                VehicleStatus.DISPATCHED,
                VehicleStatus.TRANSPORTING
            ])
        ).all()
        
        for vehicle in vehicles:
            # Driver simulation handles DISPATCHED → on_scene when driver_sim is set
            inc = (
                db.query(Incident)
                .filter(
                    Incident.assigned_vehicle_id == vehicle.id,
                    Incident.status == IncidentStatus.DISPATCHED,
                )
                .first()
            )
            if inc and inc.route_data and inc.route_data.get("driver_sim"):
                continue

            if not vehicle.route_progress:
                continue

            waypoints = vehicle.route_progress.get("waypoints", [])
            current_index = vehicle.route_progress.get("current_index", 0)
            target = vehicle.route_progress.get("target", "scene")
            
            if current_index < len(waypoints):
                # Move to next waypoint
                next_point = waypoints[current_index]
                vehicle.latitude = next_point[0]
                vehicle.longitude = next_point[1]
                vehicle.route_progress["current_index"] = current_index + 1
                vehicle.updated_at = datetime.utcnow()
                
                # Check if arrived at destination
                if current_index + 1 >= len(waypoints):
                    self._handle_vehicle_arrival(db, vehicle, target)
    
    def _handle_vehicle_arrival(
        self, 
        db: Session, 
        vehicle: Vehicle, 
        target: str
    ):
        """
        Handle vehicle arriving at destination.
        
        Args:
            vehicle: The arriving vehicle
            target: "scene" or "hospital"
        """
        # Find the incident this vehicle is assigned to
        incident = db.query(Incident).filter(
            Incident.assigned_vehicle_id == vehicle.id,
            Incident.status.in_([
                IncidentStatus.DISPATCHED,
                IncidentStatus.ON_SCENE,
                IncidentStatus.TRANSPORTING
            ])
        ).first()
        
        if not incident:
            return
        
        if target == "scene":
            # Arrived at incident scene
            vehicle.status = VehicleStatus.ON_SCENE
            incident.status = IncidentStatus.ON_SCENE
            vehicle.route_progress = None
            
            # Log arrival
            log = StatusUpdate(
                incident_id=incident.id,
                vehicle_id=vehicle.id,
                message=f"{vehicle.call_sign} arrived on scene",
                update_type="arrival",
                source="system"
            )
            db.add(log)
            
        elif target == "hospital":
            # Arrived at hospital
            vehicle.status = VehicleStatus.AT_HOSPITAL
            vehicle.route_progress = None
            
            # Log arrival
            hospital_name = "destination hospital"
            if incident.destination_hospital:
                hospital_name = incident.destination_hospital.name
                # Increase hospital occupancy
                if incident.destination_hospital.occupied_er_beds < incident.destination_hospital.total_er_beds:
                    incident.destination_hospital.occupied_er_beds += 1
            
            log = StatusUpdate(
                incident_id=incident.id,
                vehicle_id=vehicle.id,
                hospital_id=incident.destination_hospital_id,
                message=f"{vehicle.call_sign} arrived at {hospital_name}",
                update_type="arrival",
                source="system"
            )
            db.add(log)
    
    def _fluctuate_hospital_capacity(self, db: Session):
        """
        Simulate random fluctuations in hospital capacity.
        
        Small random changes to occupied beds to simulate
        patients being admitted/discharged.
        """
        # Only fluctuate occasionally (20% chance per tick)
        if random.random() > 0.2:
            return
        
        hospitals = db.query(Hospital).filter(
            Hospital.status != HospitalStatus.CLOSED
        ).all()
        
        for hospital in hospitals:
            # Random change: -2 to +2 beds
            change = random.randint(-2, 2)
            new_occupied = hospital.occupied_er_beds + change
            
            # Clamp to valid range
            new_occupied = max(0, min(new_occupied, hospital.total_er_beds))
            
            if new_occupied != hospital.occupied_er_beds:
                hospital.occupied_er_beds = new_occupied
                hospital.updated_at = datetime.utcnow()
                
                # Auto-update status based on occupancy
                occupancy = hospital.occupancy_rate
                if occupancy >= 95 and hospital.status == HospitalStatus.OPEN:
                    hospital.status = HospitalStatus.DIVERSION
                    log = StatusUpdate(
                        hospital_id=hospital.id,
                        message=f"{hospital.name} on DIVERSION ({occupancy:.0f}% capacity)",
                        update_type="alert",
                        source="system"
                    )
                    db.add(log)
                elif occupancy < 80 and hospital.status == HospitalStatus.DIVERSION:
                    hospital.status = HospitalStatus.OPEN
                    log = StatusUpdate(
                        hospital_id=hospital.id,
                        message=f"{hospital.name} now ACCEPTING ({occupancy:.0f}% capacity)",
                        update_type="info",
                        source="system"
                    )
                    db.add(log)


# API endpoint for manual simulation control
def run_single_tick():
    """
    Run a single simulation tick manually.
    
    Useful for testing or manual demo control.
    """
    engine = SimulationEngine()
    db = SessionLocal()
    try:
        engine._update_vehicle_positions(db)
        engine._fluctuate_hospital_capacity(db)
        db.commit()
        return {"status": "ok", "message": "Simulation tick completed"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def generate_random_incident():
    """
    Generate a random incident for demo purposes.
    
    Creates a new incident at a random location in downtown Toronto.
    """
    db = SessionLocal()
    try:
        # Random location in downtown Toronto
        lat = 43.645 + random.uniform(0, 0.03)
        lng = -79.41 + random.uniform(0, 0.04)
        
        descriptions = [
            "Chest pain, patient conscious",
            "Fall victim, possible fracture",
            "Difficulty breathing, elderly patient",
            "Unconscious person reported",
            "Motor vehicle collision, injuries reported",
            "Allergic reaction, swelling observed",
            "Seizure activity, patient responsive now",
            "Laceration with heavy bleeding",
            "Diabetic emergency, altered mental status",
            "Stroke symptoms, face drooping reported"
        ]
        
        severities = [
            IncidentSeverity.MINOR,
            IncidentSeverity.MAJOR,
            IncidentSeverity.MAJOR,
            IncidentSeverity.CRITICAL,
            IncidentSeverity.MAJOR
        ]
        
        incident = Incident(
            latitude=lat,
            longitude=lng,
            address=f"Random location, Downtown Toronto",
            description=random.choice(descriptions),
            severity=random.choice(severities),
            status=IncidentStatus.PENDING,
            reported_at=datetime.utcnow()
        )
        
        db.add(incident)
        
        log = StatusUpdate(
            incident=incident,
            message=f"New incident reported: {incident.description}",
            update_type="system",
            source="system"
        )
        db.add(log)
        
        db.commit()
        return {
            "status": "ok",
            "incident_id": incident.id,
            "description": incident.description
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
