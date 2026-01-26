"""
Tests for the Routing Service.

Tests A* pathfinding and distance calculations.
"""

import pytest
from app.services.routing import RoutingService


class TestRoutingService:
    """Test suite for RoutingService."""
    
    @pytest.fixture
    def routing(self):
        """Create a routing service instance."""
        return RoutingService()
    
    # =========================================================================
    # Haversine Distance Tests
    # =========================================================================
    
    def test_haversine_same_point(self, routing):
        """Distance between same point should be zero."""
        dist = routing.haversine_distance(43.65, -79.38, 43.65, -79.38)
        assert dist == 0.0
    
    def test_haversine_known_distance(self, routing):
        """Test against a known distance."""
        # Union Station to CN Tower (approximately 0.5 km)
        dist = routing.haversine_distance(
            43.6453, -79.3806,  # Union Station
            43.6426, -79.3871   # CN Tower
        )
        # Should be approximately 0.5 km (within 0.2 km tolerance)
        assert 0.3 < dist < 0.7
    
    def test_haversine_symmetry(self, routing):
        """Distance should be the same in both directions."""
        dist1 = routing.haversine_distance(43.65, -79.38, 43.66, -79.39)
        dist2 = routing.haversine_distance(43.66, -79.39, 43.65, -79.38)
        assert abs(dist1 - dist2) < 0.001
    
    # =========================================================================
    # Route Calculation Tests
    # =========================================================================
    
    def test_route_same_location(self, routing):
        """Route to same location should return minimal path."""
        result = routing.calculate_route(43.65, -79.38, 43.65, -79.38)
        
        assert result is not None
        assert result["distance_km"] < 0.1
        assert len(result["polyline"]) >= 2
    
    def test_route_returns_required_fields(self, routing):
        """Route result should have all required fields."""
        result = routing.calculate_route(
            43.6453, -79.3806,  # Near Union Station
            43.6600, -79.3885   # Near Toronto General
        )
        
        assert result is not None
        assert "polyline" in result
        assert "distance_km" in result
        assert "estimated_time_minutes" in result
        assert isinstance(result["polyline"], list)
        assert len(result["polyline"]) >= 2
    
    def test_route_polyline_format(self, routing):
        """Polyline should be list of [lat, lng] pairs."""
        result = routing.calculate_route(
            43.6453, -79.3806,
            43.6600, -79.3885
        )
        
        assert result is not None
        for point in result["polyline"]:
            assert len(point) == 2
            assert isinstance(point[0], float)  # lat
            assert isinstance(point[1], float)  # lng
    
    def test_route_starts_and_ends_correctly(self, routing):
        """Route should start at origin and end at destination."""
        origin = (43.6453, -79.3806)
        destination = (43.6600, -79.3885)
        
        result = routing.calculate_route(
            origin[0], origin[1],
            destination[0], destination[1]
        )
        
        assert result is not None
        polyline = result["polyline"]
        
        # First point should be near origin
        assert abs(polyline[0][0] - origin[0]) < 0.01
        assert abs(polyline[0][1] - origin[1]) < 0.01
        
        # Last point should be near destination
        assert abs(polyline[-1][0] - destination[0]) < 0.01
        assert abs(polyline[-1][1] - destination[1]) < 0.01
    
    def test_route_reasonable_distance(self, routing):
        """Calculated distance should be reasonable (not absurdly long)."""
        # Route within downtown (should be < 10 km)
        result = routing.calculate_route(
            43.6453, -79.3806,  # Union Station
            43.6709, -79.3857   # Bloor-Yonge
        )
        
        assert result is not None
        # Should be under 10 km for this downtown route
        assert result["distance_km"] < 10
        # Should be more than straight-line distance
        assert result["distance_km"] > 2
    
    def test_route_reasonable_time(self, routing):
        """Estimated time should be reasonable."""
        result = routing.calculate_route(
            43.6453, -79.3806,
            43.6709, -79.3857
        )
        
        assert result is not None
        # Time should be positive
        assert result["estimated_time_minutes"] > 0
        # For ~3-5 km, with EMS speeds, should be < 20 minutes
        assert result["estimated_time_minutes"] < 20
    
    # =========================================================================
    # Network Information Tests
    # =========================================================================
    
    def test_network_has_nodes(self, routing):
        """Network should have nodes defined."""
        info = routing.get_network_info()
        assert info["nodes"] > 0
    
    def test_network_has_edges(self, routing):
        """Network should have edges connecting nodes."""
        info = routing.get_network_info()
        assert info["edges"] > 0
    
    def test_network_nodes_have_coordinates(self, routing):
        """All nodes should have valid coordinates."""
        info = routing.get_network_info()
        for node in info["node_list"]:
            assert "lat" in node
            assert "lng" in node
            # Coordinates should be in Toronto area
            assert 43.6 < node["lat"] < 43.8
            assert -79.5 < node["lng"] < -79.3


class TestRoutingEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def routing(self):
        return RoutingService()
    
    def test_route_far_outside_network(self, routing):
        """Route far outside network should still return (straight-line fallback)."""
        # Point far from Toronto
        result = routing.calculate_route(
            45.0, -75.0,  # Ottawa
            43.65, -79.38  # Toronto
        )
        
        # Should return a result (fallback behavior)
        assert result is not None
    
    def test_route_with_negative_coords(self, routing):
        """Should handle negative coordinates correctly."""
        result = routing.calculate_route(
            43.65, -79.38,
            43.66, -79.39
        )
        
        assert result is not None
        assert result["distance_km"] > 0
