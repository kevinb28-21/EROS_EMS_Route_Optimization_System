"""
Routing Service - Intelligent path-finding for EMS vehicles.

Uses A* algorithm on a simplified Toronto road network.
For a course project, we use a pre-defined graph of major roads
rather than full OSM data to keep it simple and fast.

The routing considers:
- Road network topology
- Estimated travel speeds per road type
- Real-time-simulatable traffic conditions (future enhancement)
"""

import math
import heapq
from datetime import datetime
from typing import Optional, List, Tuple, Dict
import networkx as nx


# Traffic condition multipliers by hour of day
# EMS vehicles run lights/sirens but are still affected by congestion
# Values < 1.0 = slower (heavy traffic), values > 1.0 = faster (clear roads)
TRAFFIC_PROFILE = {
    # Overnight (very clear)
    0: 1.4, 1: 1.4, 2: 1.5, 3: 1.5, 4: 1.4,
    # Early morning ramp-up
    5: 1.2, 6: 1.0,
    # Morning rush hour
    7: 0.65, 8: 0.6, 9: 0.75,
    # Mid-day moderate
    10: 0.9, 11: 0.9, 12: 0.85, 13: 0.85, 14: 0.9, 15: 0.85,
    # Afternoon/evening rush
    16: 0.65, 17: 0.6, 18: 0.65, 19: 0.75,
    # Evening
    20: 0.9, 21: 1.0, 22: 1.1, 23: 1.3,
}


class RoutingService:
    """
    Route calculation service using A* pathfinding.

    For simplicity, uses a pre-built graph of downtown Toronto.
    In production, this could be replaced with OSRM or GraphHopper.

    Traffic conditions are simulated using time-of-day speed multipliers
    that model real rush-hour patterns in downtown Toronto.
    """

    def __init__(self):
        """Initialize the routing service with the road network."""
        self.graph = self._build_toronto_network()
        # Base speeds (km/h) by road type for EMS (with lights/sirens)
        self.speeds = {
            "highway": 80,
            "arterial": 50,
            "collector": 40,
            "local": 30
        }

    def get_traffic_multiplier(self, hour: Optional[int] = None) -> float:
        """
        Get the current traffic speed multiplier based on time of day.

        EMS vehicles running lights/sirens are partially buffered from traffic
        (factor of 0.5 applied to the traffic impact), so rush hour still slows
        them but less than civilian vehicles.

        Args:
            hour: Hour of day (0-23). Defaults to current local hour.

        Returns:
            Speed multiplier (e.g. 0.8 = 20% slower than base speed)
        """
        if hour is None:
            hour = datetime.now().hour

        raw = TRAFFIC_PROFILE.get(hour, 1.0)
        # EMS with lights/sirens only partially affected by traffic
        # Scale impact: neutral is 1.0; deviation is halved for EMS
        ems_multiplier = 1.0 + (raw - 1.0) * 0.5
        return round(ems_multiplier, 3)

    def get_traffic_conditions(self) -> Dict:
        """
        Return a human-readable summary of current traffic conditions.

        Used by the simulation status endpoint.
        """
        hour = datetime.now().hour
        raw = TRAFFIC_PROFILE.get(hour, 1.0)
        ems = self.get_traffic_multiplier(hour)

        if raw <= 0.65:
            level = "heavy"
            description = "Rush hour - heavy congestion"
        elif raw <= 0.85:
            level = "moderate"
            description = "Moderate traffic"
        elif raw <= 1.1:
            level = "normal"
            description = "Normal traffic flow"
        else:
            level = "clear"
            description = "Clear roads"

        return {
            "hour": hour,
            "level": level,
            "description": description,
            "civilian_multiplier": round(raw, 2),
            "ems_multiplier": ems,
        }
    
    def _build_toronto_network(self) -> nx.Graph:
        """
        Build a simplified road network graph for downtown Toronto.
        
        This is a manually-defined network for demo purposes.
        Nodes are intersections, edges are road segments.
        Each node has (lat, lng) coordinates.
        Each edge has distance and road_type attributes.
        """
        G = nx.Graph()
        
        # Define key intersections in downtown Toronto
        # Format: node_id -> (lat, lng, name)
        nodes = {
            # Financial District / Union Station area
            "union": (43.6453, -79.3806, "Union Station"),
            "bay_front": (43.6425, -79.3775, "Bay & Front"),
            "yonge_front": (43.6448, -79.3743, "Yonge & Front"),
            "king_bay": (43.6490, -79.3795, "King & Bay"),
            "queen_bay": (43.6520, -79.3807, "Queen & Bay"),
            
            # Queen Street corridor
            "queen_spadina": (43.6488, -79.3957, "Queen & Spadina"),
            "queen_university": (43.6515, -79.3858, "Queen & University"),
            "queen_yonge": (43.6533, -79.3795, "Queen & Yonge"),
            "queen_church": (43.6540, -79.3755, "Queen & Church"),
            
            # Dundas Street corridor
            "dundas_spadina": (43.6527, -79.3977, "Dundas & Spadina"),
            "dundas_university": (43.6558, -79.3870, "Dundas & University"),
            "dundas_yonge": (43.6561, -79.3815, "Dundas & Yonge"),
            "dundas_church": (43.6575, -79.3770, "Dundas & Church"),
            
            # College/Carlton corridor
            "college_spadina": (43.6578, -79.4011, "College & Spadina"),
            "college_university": (43.6605, -79.3905, "College & University"),
            "college_yonge": (43.6618, -79.3832, "College & Yonge"),
            
            # Bloor Street corridor
            "bloor_spadina": (43.6632, -79.4030, "Bloor & Spadina"),
            "bloor_st_george": (43.6675, -79.3995, "Bloor & St George"),
            "bloor_yonge": (43.6709, -79.3857, "Bloor & Yonge"),
            "bloor_sherbourne": (43.6720, -79.3760, "Bloor & Sherbourne"),
            
            # Hospital locations (approximate)
            "toronto_general": (43.6600, -79.3885, "Toronto General Hospital"),
            "st_michaels": (43.6538, -79.3775, "St. Michael's Hospital"),
            "sick_kids": (43.6568, -79.3878, "SickKids Hospital"),
            "mount_sinai": (43.6585, -79.3895, "Mount Sinai Hospital"),
            
            # Additional connectors
            "university_king": (43.6480, -79.3845, "University & King"),
            "spadina_king": (43.6450, -79.3943, "Spadina & King"),
            "church_king": (43.6500, -79.3750, "Church & King"),
            
            # Waterfront
            "harbourfront": (43.6390, -79.3800, "Harbourfront"),
            "distillery": (43.6505, -79.3595, "Distillery District"),
        }
        
        # Add nodes to graph
        for node_id, (lat, lng, name) in nodes.items():
            G.add_node(node_id, lat=lat, lng=lng, name=name)
        
        # Define edges (road segments)
        # Format: (node1, node2, road_type)
        edges = [
            # East-West roads
            # Front Street
            ("bay_front", "yonge_front", "arterial"),
            ("union", "bay_front", "arterial"),
            ("yonge_front", "distillery", "arterial"),
            
            # King Street
            ("spadina_king", "university_king", "arterial"),
            ("university_king", "king_bay", "arterial"),
            ("king_bay", "church_king", "arterial"),
            
            # Queen Street
            ("queen_spadina", "queen_university", "arterial"),
            ("queen_university", "queen_bay", "arterial"),
            ("queen_bay", "queen_yonge", "arterial"),
            ("queen_yonge", "queen_church", "arterial"),
            
            # Dundas Street
            ("dundas_spadina", "dundas_university", "arterial"),
            ("dundas_university", "dundas_yonge", "arterial"),
            ("dundas_yonge", "dundas_church", "arterial"),
            
            # College/Carlton
            ("college_spadina", "college_university", "arterial"),
            ("college_university", "college_yonge", "arterial"),
            
            # Bloor Street
            ("bloor_spadina", "bloor_st_george", "arterial"),
            ("bloor_st_george", "bloor_yonge", "arterial"),
            ("bloor_yonge", "bloor_sherbourne", "arterial"),
            
            # North-South roads
            # Spadina
            ("spadina_king", "queen_spadina", "arterial"),
            ("queen_spadina", "dundas_spadina", "arterial"),
            ("dundas_spadina", "college_spadina", "arterial"),
            ("college_spadina", "bloor_spadina", "arterial"),
            
            # University
            ("university_king", "queen_university", "arterial"),
            ("queen_university", "dundas_university", "arterial"),
            ("dundas_university", "college_university", "arterial"),
            ("college_university", "bloor_st_george", "collector"),
            
            # Bay
            ("bay_front", "king_bay", "arterial"),
            ("king_bay", "queen_bay", "arterial"),
            
            # Yonge Street
            ("yonge_front", "queen_yonge", "arterial"),
            ("queen_yonge", "dundas_yonge", "arterial"),
            ("dundas_yonge", "college_yonge", "arterial"),
            ("college_yonge", "bloor_yonge", "arterial"),
            
            # Church
            ("church_king", "queen_church", "collector"),
            ("queen_church", "dundas_church", "collector"),
            
            # Hospital connectors
            ("toronto_general", "college_university", "local"),
            ("toronto_general", "dundas_university", "local"),
            ("st_michaels", "queen_church", "local"),
            ("st_michaels", "dundas_church", "local"),
            ("sick_kids", "dundas_university", "local"),
            ("mount_sinai", "college_university", "local"),
            
            # Waterfront connectors
            ("union", "harbourfront", "collector"),
            ("bay_front", "harbourfront", "collector"),
        ]
        
        # Add edges with calculated distances
        for node1, node2, road_type in edges:
            if node1 in nodes and node2 in nodes:
                lat1, lng1, _ = nodes[node1]
                lat2, lng2, _ = nodes[node2]
                dist = self.haversine_distance(lat1, lng1, lat2, lng2)
                G.add_edge(node1, node2, distance=dist, road_type=road_type)
        
        return G
    
    def haversine_distance(
        self, 
        lat1: float, lng1: float, 
        lat2: float, lng2: float
    ) -> float:
        """
        Calculate the great-circle distance between two points.
        
        Uses the Haversine formula for accuracy on Earth's surface.
        
        Args:
            lat1, lng1: Origin coordinates
            lat2, lng2: Destination coordinates
            
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * 
            math.sin(delta_lng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def _densify_polyline(
        self,
        points: List[List[float]],
        max_segment_km: float = 0.025,
    ) -> List[List[float]]:
        """
        Insert intermediate points along each segment so the map polyline follows
        the road graph visually (short straight segments, not one long chord).

        max_segment_km ~25 m between points for a smooth street-following look.
        """
        if len(points) < 2:
            return points
        out: List[List[float]] = []
        for i in range(len(points) - 1):
            lat1, lng1 = points[i][0], points[i][1]
            lat2, lng2 = points[i + 1][0], points[i + 1][1]
            seg_km = self.haversine_distance(lat1, lng1, lat2, lng2)
            if seg_km < 0.0005:
                if not out or out[-1] != [lat1, lng1]:
                    out.append([lat1, lng1])
                continue
            n_steps = max(2, int(seg_km / max_segment_km) + 1)
            for s in range(n_steps):
                t = s / (n_steps - 1) if n_steps > 1 else 0.0
                lat = lat1 + t * (lat2 - lat1)
                lng = lng1 + t * (lng2 - lng1)
                pt = [lat, lng]
                if not out or (abs(out[-1][0] - pt[0]) > 1e-7 or abs(out[-1][1] - pt[1]) > 1e-7):
                    out.append(pt)
        # Degenerate segment (same start/end) must still yield ≥2 points for map clients
        if len(out) < 2 and len(points) >= 2:
            return [points[0], points[-1]]
        return out

    def _find_nearest_node(self, lat: float, lng: float) -> Optional[str]:
        """
        Find the nearest graph node to a given coordinate.
        
        Args:
            lat, lng: Target coordinates
            
        Returns:
            Node ID of nearest node, or None if graph is empty
        """
        nearest = None
        min_dist = float('inf')
        
        for node_id in self.graph.nodes():
            node = self.graph.nodes[node_id]
            dist = self.haversine_distance(lat, lng, node['lat'], node['lng'])
            if dist < min_dist:
                min_dist = dist
                nearest = node_id
        
        return nearest
    
    def _astar_heuristic(self, node1: str, node2: str) -> float:
        """
        A* heuristic function using straight-line distance.
        
        Args:
            node1, node2: Node IDs to calculate heuristic between
            
        Returns:
            Estimated distance (heuristic value)
        """
        n1 = self.graph.nodes[node1]
        n2 = self.graph.nodes[node2]
        return self.haversine_distance(n1['lat'], n1['lng'], n2['lat'], n2['lng'])
    
    def calculate_route(
        self,
        origin_lat: float, origin_lng: float,
        dest_lat: float, dest_lng: float,
        hour: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Calculate the optimal route between two points.
        
        Uses A* algorithm on the road network graph.
        
        Args:
            origin_lat, origin_lng: Starting coordinates
            dest_lat, dest_lng: Destination coordinates
            
        Returns:
            Dictionary with route details or None if no route found:
            {
                "polyline": [[lat, lng], ...],
                "distance_km": float,
                "estimated_time_minutes": float,
                "traffic_level": str,
            }
        """
        traffic_multiplier = self.get_traffic_multiplier(hour)

        # Find nearest nodes
        origin_node = self._find_nearest_node(origin_lat, origin_lng)
        dest_node = self._find_nearest_node(dest_lat, dest_lng)
        
        if not origin_node or not dest_node:
            return None
        
        # Handle same node case
        if origin_node == dest_node:
            pl = self._densify_polyline([[origin_lat, origin_lng], [dest_lat, dest_lng]])
            return {
                "polyline": pl,
                "distance_km": self.haversine_distance(
                    origin_lat, origin_lng, dest_lat, dest_lng
                ),
                "estimated_time_minutes": 1.0,
                "traffic_level": self.get_traffic_conditions()["level"],
            }
        
        # Use NetworkX's A* implementation
        try:
            path = nx.astar_path(
                self.graph,
                origin_node,
                dest_node,
                heuristic=self._astar_heuristic,
                weight='distance'
            )
        except nx.NetworkXNoPath:
            # No path found - return straight line as fallback (still densified)
            distance = self.haversine_distance(
                origin_lat, origin_lng, dest_lat, dest_lng
            )
            effective_speed = 40 * traffic_multiplier
            pl = self._densify_polyline([[origin_lat, origin_lng], [dest_lat, dest_lng]])
            return {
                "polyline": pl,
                "distance_km": distance,
                "estimated_time_minutes": (distance / effective_speed) * 60,
                "traffic_level": self.get_traffic_conditions()["level"],
            }
        
        # Build polyline and calculate total distance and time
        polyline = [[origin_lat, origin_lng]]  # Start with actual origin
        total_distance = 0.0
        total_time = 0.0

        # Add distance from origin to first node (local-speed approach)
        first_node = self.graph.nodes[path[0]]
        initial_dist = self.haversine_distance(
            origin_lat, origin_lng, first_node['lat'], first_node['lng']
        )
        effective_local = self.speeds["local"] * traffic_multiplier
        total_distance += initial_dist
        total_time += (initial_dist / effective_local) * 60

        # Process path
        for i, node_id in enumerate(path):
            node = self.graph.nodes[node_id]
            polyline.append([node['lat'], node['lng']])

            # Calculate edge distance and time with traffic multiplier
            if i > 0:
                prev_node = path[i - 1]
                edge = self.graph.edges[prev_node, node_id]
                dist = edge['distance']
                road_type = edge.get('road_type', 'local')
                base_speed = self.speeds.get(road_type, 30)
                effective_speed = base_speed * traffic_multiplier

                total_distance += dist
                total_time += (dist / effective_speed) * 60  # Convert to minutes

        # Add distance from last node to destination
        last_node = self.graph.nodes[path[-1]]
        final_dist = self.haversine_distance(
            last_node['lat'], last_node['lng'], dest_lat, dest_lng
        )
        total_distance += final_dist
        total_time += (final_dist / effective_local) * 60

        polyline.append([dest_lat, dest_lng])  # End with actual destination

        traffic_info = self.get_traffic_conditions()
        dense_polyline = self._densify_polyline(polyline)
        return {
            "polyline": dense_polyline,
            "distance_km": round(total_distance, 2),
            "estimated_time_minutes": round(total_time, 1),
            "traffic_level": traffic_info["level"],
            "traffic_description": traffic_info["description"],
        }
    
    def get_network_info(self) -> Dict:
        """
        Get information about the routing network.
        
        Useful for debugging and understanding coverage.
        """
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "coverage_area": "Downtown Toronto",
            "node_list": [
                {
                    "id": n,
                    "name": self.graph.nodes[n].get('name', n),
                    "lat": self.graph.nodes[n]['lat'],
                    "lng": self.graph.nodes[n]['lng']
                }
                for n in self.graph.nodes()
            ]
        }
