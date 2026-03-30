"""
Route calculation API endpoints.

Handles route calculations between points using the routing engine.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas import RouteRequest, RouteResponse, LocationBase
from app.services.routing import RoutingService


router = APIRouter()


@router.post("/calculate", response_model=RouteResponse)
def calculate_route(request: RouteRequest):
    """
    Calculate an optimal route between two points.
    
    Returns the route polyline, distance, and estimated travel time.
    Uses A* pathfinding on the Toronto road network.
    """
    routing = RoutingService()
    
    result = routing.calculate_route(
        request.origin_lat, request.origin_lng,
        request.destination_lat, request.destination_lng
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "RouteNotFound",
                "message": "Could not calculate a route between the specified points"
            }
        )
    
    return RouteResponse(
        origin=LocationBase(latitude=request.origin_lat, longitude=request.origin_lng),
        destination=LocationBase(latitude=request.destination_lat, longitude=request.destination_lng),
        distance_km=result["distance_km"],
        estimated_time_minutes=result["estimated_time_minutes"],
        polyline=result["polyline"],
        traffic_level=result.get("traffic_level"),
        traffic_description=result.get("traffic_description"),
        route_source=result.get("route_source"),
    )


@router.get("/distance")
def get_distance(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float
):
    """
    Get the straight-line (Haversine) distance between two points.
    
    Quick distance check without full route calculation.
    """
    routing = RoutingService()
    distance = routing.haversine_distance(
        origin_lat, origin_lng,
        dest_lat, dest_lng
    )
    
    return {
        "distance_km": round(distance, 2),
        "origin": {"latitude": origin_lat, "longitude": origin_lng},
        "destination": {"latitude": dest_lat, "longitude": dest_lng}
    }
