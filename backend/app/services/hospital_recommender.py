"""
Hospital Recommender Service.

Recommends optimal hospitals for patient transport based on:
- Distance from incident
- Current ER capacity / availability
- Required specialties (trauma, cardiac, pediatric, etc.)
- Incident severity

The scoring algorithm balances multiple factors to provide
ranked recommendations with explanations.
"""

from typing import List, Optional
from app.models import Hospital, IncidentSeverity
from app.schemas import HospitalRecommendation, HospitalResponse
from app.services.routing import RoutingService


class HospitalRecommender:
    """
    Hospital recommendation engine for EMS dispatch.
    
    Uses a weighted scoring system to rank hospitals.
    """
    
    def __init__(self):
        """Initialize the recommender with routing service."""
        self.routing = RoutingService()
        
        # Scoring weights (total = 1.0)
        self.weights = {
            "distance": 0.35,      # Closer is better
            "capacity": 0.30,      # More available beds is better
            "specialty": 0.25,     # Matching specialties is critical
            "trauma_center": 0.10  # Bonus for trauma centers on critical cases
        }
        
        # Distance scoring parameters
        self.max_distance_km = 15.0  # Beyond this, distance score drops to 0
        
        # Capacity scoring thresholds
        self.critical_occupancy = 90  # Above this, heavily penalized
        self.preferred_occupancy = 70  # Below this is ideal
    
    def recommend(
        self,
        incident_lat: float,
        incident_lng: float,
        incident_severity: IncidentSeverity,
        patient_needs: List[str],
        hospitals: List[Hospital],
        max_results: int = 5
    ) -> List[HospitalRecommendation]:
        """
        Generate ranked hospital recommendations.
        
        Args:
            incident_lat, incident_lng: Incident location
            incident_severity: Severity level of the incident
            patient_needs: List of required specialties (e.g., ["trauma", "cardiac"])
            hospitals: List of available hospitals to consider
            max_results: Maximum number of recommendations to return
            
        Returns:
            List of HospitalRecommendation objects, ranked by score
        """
        recommendations = []
        
        for hospital in hospitals:
            # Calculate route to hospital
            route = self.routing.calculate_route(
                incident_lat, incident_lng,
                hospital.latitude, hospital.longitude
            )
            
            if not route:
                continue
            
            distance_km = route["distance_km"]
            eta_minutes = route["estimated_time_minutes"]
            
            # Calculate component scores
            distance_score = self._score_distance(distance_km)
            capacity_score = self._score_capacity(hospital)
            specialty_score = self._score_specialty(hospital, patient_needs)
            trauma_score = self._score_trauma(hospital, incident_severity)
            
            # Calculate weighted total score
            total_score = (
                self.weights["distance"] * distance_score +
                self.weights["capacity"] * capacity_score +
                self.weights["specialty"] * specialty_score +
                self.weights["trauma_center"] * trauma_score
            )
            
            # Generate reasons for this recommendation
            reasons = self._generate_reasons(
                hospital, distance_km, eta_minutes,
                distance_score, capacity_score, specialty_score, trauma_score,
                patient_needs, incident_severity
            )
            
            recommendations.append(HospitalRecommendation(
                hospital=HospitalResponse.from_orm_with_computed(hospital),
                score=round(total_score, 2),
                distance_km=distance_km,
                estimated_time_minutes=eta_minutes,
                reasons=reasons
            ))
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        return recommendations[:max_results]
    
    def _score_distance(self, distance_km: float) -> float:
        """
        Score based on distance (0-1, higher is better = closer).
        
        Uses linear decay from max_distance_km.
        """
        if distance_km >= self.max_distance_km:
            return 0.0
        return 1.0 - (distance_km / self.max_distance_km)
    
    def _score_capacity(self, hospital: Hospital) -> float:
        """
        Score based on ER capacity (0-1, higher is better = more available).
        
        Penalizes hospitals near or at capacity.
        """
        occupancy = hospital.occupancy_rate
        
        if occupancy >= 100:
            return 0.0
        elif occupancy >= self.critical_occupancy:
            # Heavy penalty for near-capacity
            return 0.2 * (100 - occupancy) / (100 - self.critical_occupancy)
        elif occupancy >= self.preferred_occupancy:
            # Moderate penalty
            return 0.2 + 0.5 * (self.critical_occupancy - occupancy) / (self.critical_occupancy - self.preferred_occupancy)
        else:
            # Good capacity
            return 0.7 + 0.3 * (self.preferred_occupancy - occupancy) / self.preferred_occupancy
    
    def _score_specialty(
        self, 
        hospital: Hospital, 
        patient_needs: List[str]
    ) -> float:
        """
        Score based on matching specialties (0-1).
        
        Full score if all needs are met, partial for partial matches.
        """
        if not patient_needs:
            return 1.0  # No specific needs, all hospitals qualify
        
        hospital_specialties = [s.lower() for s in (hospital.specialties or [])]
        needs_lower = [n.lower() for n in patient_needs]
        
        matches = sum(1 for need in needs_lower if need in hospital_specialties)
        return matches / len(patient_needs)
    
    def _score_trauma(
        self, 
        hospital: Hospital, 
        severity: IncidentSeverity
    ) -> float:
        """
        Bonus score for trauma centers on critical incidents.
        
        Only applies for critical severity incidents.
        """
        if severity == IncidentSeverity.CRITICAL and hospital.is_trauma_center:
            return 1.0
        elif severity == IncidentSeverity.MAJOR and hospital.is_trauma_center:
            return 0.5
        return 0.0
    
    def _generate_reasons(
        self,
        hospital: Hospital,
        distance_km: float,
        eta_minutes: float,
        distance_score: float,
        capacity_score: float,
        specialty_score: float,
        trauma_score: float,
        patient_needs: List[str],
        severity: IncidentSeverity
    ) -> List[str]:
        """
        Generate human-readable reasons for the recommendation.
        """
        reasons = []
        
        # Distance reason
        if distance_score >= 0.8:
            reasons.append(f"Very close ({distance_km:.1f} km, ~{eta_minutes:.0f} min)")
        elif distance_score >= 0.5:
            reasons.append(f"Moderate distance ({distance_km:.1f} km, ~{eta_minutes:.0f} min)")
        else:
            reasons.append(f"Farther away ({distance_km:.1f} km, ~{eta_minutes:.0f} min)")
        
        # Capacity reason
        if capacity_score >= 0.7:
            reasons.append(f"Good ER availability ({hospital.available_beds} beds free)")
        elif capacity_score >= 0.3:
            reasons.append(f"Limited ER space ({hospital.available_beds} beds free)")
        else:
            reasons.append(f"ER near capacity ({hospital.occupancy_rate:.0f}% full)")
        
        # Specialty reason
        if patient_needs and specialty_score >= 1.0:
            reasons.append(f"Has all required specialties: {', '.join(patient_needs)}")
        elif patient_needs and specialty_score > 0:
            hospital_specs = [s.lower() for s in (hospital.specialties or [])]
            matched = [n for n in patient_needs if n.lower() in hospital_specs]
            reasons.append(f"Has specialties: {', '.join(matched)}")
        
        # Trauma center reason
        if hospital.is_trauma_center:
            if severity == IncidentSeverity.CRITICAL:
                reasons.append("Trauma center - critical for this severity")
            else:
                reasons.append("Designated trauma center")
        
        return reasons
