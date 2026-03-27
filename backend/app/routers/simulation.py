"""
Simulation control API endpoints.

Provides manual control over the simulation engine for demo purposes:
- Run a single simulation tick (advance vehicle positions, fluctuate hospital capacity)
- Generate a random incident at a downtown Toronto location
- Query current simulation and traffic status
"""

from typing import Optional
from fastapi import APIRouter

from app.services.simulation import SimulationEngine, run_single_tick, generate_random_incident
from app.services.routing import RoutingService

router = APIRouter()

# Shared reference to the running engine (set by main.py on startup)
_engine: Optional[SimulationEngine] = None


def set_engine(engine: SimulationEngine) -> None:
    """Register the running simulation engine with this router."""
    global _engine
    _engine = engine


@router.get("/status")
def get_simulation_status():
    """
    Get the current simulation and traffic conditions status.

    Returns whether the simulation is running and current traffic levels,
    which affect EMS route time estimates.
    """
    routing = RoutingService()
    traffic = routing.get_traffic_conditions()

    return {
        "simulation_running": _engine is not None and _engine.running,
        "interval_seconds": _engine.interval if _engine else None,
        "traffic": traffic,
    }


@router.post("/tick")
def manual_tick():
    """
    Manually run a single simulation tick.

    Advances vehicle positions one waypoint along their routes and
    randomly fluctuates hospital bed occupancy. Useful for demo control
    when you want to step through the simulation manually.
    """
    return run_single_tick()


@router.post("/generate-incident")
def create_random_incident():
    """
    Generate a random emergency incident at a downtown Toronto location.

    Creates a new PENDING incident with a realistic description and random
    severity level. Useful for populating the demo with active incidents.
    """
    return generate_random_incident()
