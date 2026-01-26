"""
Tests for the Hospital Recommender Service.

Tests hospital recommendation logic based on distance, capacity, and specialties.
"""

import pytest
from unittest.mock import MagicMock
from app.services.hospital_recommender import HospitalRecommender
from app.models import Hospital, HospitalStatus, IncidentSeverity


def create_mock_hospital(
    id: int,
    name: str,
    lat: float,
    lng: float,
    total_beds: int = 20,
    occupied_beds: int = 10,
    specialties: list = None,
    is_trauma: bool = False
) -> MagicMock:
    """Create a mock hospital for testing."""
    hospital = MagicMock(spec=Hospital)
    hospital.id = id
    hospital.name = name
    hospital.latitude = lat
    hospital.longitude = lng
    hospital.address = f"{name} Address"
    hospital.total_er_beds = total_beds
    hospital.occupied_er_beds = occupied_beds
    hospital.specialties = specialties or []
    hospital.is_trauma_center = is_trauma
    hospital.status = HospitalStatus.OPEN
    hospital.available_beds = total_beds - occupied_beds
    hospital.occupancy_rate = (occupied_beds / total_beds) * 100 if total_beds > 0 else 100
    hospital.created_at = MagicMock()
    hospital.updated_at = MagicMock()
    return hospital


class TestHospitalRecommender:
    """Test suite for HospitalRecommender."""
    
    @pytest.fixture
    def recommender(self):
        """Create a recommender instance."""
        return HospitalRecommender()
    
    @pytest.fixture
    def sample_hospitals(self):
        """Create a set of sample hospitals."""
        return [
            create_mock_hospital(
                1, "Toronto General",
                43.6600, -79.3885,
                total_beds=30, occupied_beds=15,
                specialties=["trauma", "cardiac"],
                is_trauma=True
            ),
            create_mock_hospital(
                2, "St. Michael's",
                43.6538, -79.3775,
                total_beds=25, occupied_beds=20,  # Higher occupancy
                specialties=["trauma", "neurosurgery"],
                is_trauma=True
            ),
            create_mock_hospital(
                3, "Mount Sinai",
                43.6585, -79.3895,
                total_beds=20, occupied_beds=8,  # Lower occupancy
                specialties=["obstetrics"],
                is_trauma=False
            ),
        ]
    
    # =========================================================================
    # Basic Recommendation Tests
    # =========================================================================
    
    def test_returns_recommendations(self, recommender, sample_hospitals):
        """Should return a list of recommendations."""
        results = recommender.recommend(
            incident_lat=43.6530,
            incident_lng=-79.3800,
            incident_severity=IncidentSeverity.MAJOR,
            patient_needs=[],
            hospitals=sample_hospitals
        )
        
        assert len(results) > 0
        assert len(results) <= len(sample_hospitals)
    
    def test_recommendations_have_required_fields(self, recommender, sample_hospitals):
        """Recommendations should have all required fields."""
        results = recommender.recommend(
            incident_lat=43.6530,
            incident_lng=-79.3800,
            incident_severity=IncidentSeverity.MAJOR,
            patient_needs=[],
            hospitals=sample_hospitals
        )
        
        for rec in results:
            assert hasattr(rec, 'hospital')
            assert hasattr(rec, 'score')
            assert hasattr(rec, 'distance_km')
            assert hasattr(rec, 'estimated_time_minutes')
            assert hasattr(rec, 'reasons')
    
    def test_recommendations_sorted_by_score(self, recommender, sample_hospitals):
        """Recommendations should be sorted by score descending."""
        results = recommender.recommend(
            incident_lat=43.6530,
            incident_lng=-79.3800,
            incident_severity=IncidentSeverity.MAJOR,
            patient_needs=[],
            hospitals=sample_hospitals
        )
        
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_max_results_limit(self, recommender, sample_hospitals):
        """Should respect max_results parameter."""
        results = recommender.recommend(
            incident_lat=43.6530,
            incident_lng=-79.3800,
            incident_severity=IncidentSeverity.MAJOR,
            patient_needs=[],
            hospitals=sample_hospitals,
            max_results=2
        )
        
        assert len(results) <= 2
    
    # =========================================================================
    # Distance Scoring Tests
    # =========================================================================
    
    def test_closer_hospital_scored_higher(self, recommender):
        """Closer hospitals should score higher on distance."""
        # Incident location
        incident_lat, incident_lng = 43.6530, -79.3800
        
        close_hospital = create_mock_hospital(
            1, "Close Hospital",
            43.6535, -79.3805,  # Very close
            total_beds=20, occupied_beds=10
        )
        far_hospital = create_mock_hospital(
            2, "Far Hospital",
            43.6800, -79.4200,  # Further away
            total_beds=20, occupied_beds=10
        )
        
        results = recommender.recommend(
            incident_lat=incident_lat,
            incident_lng=incident_lng,
            incident_severity=IncidentSeverity.MINOR,
            patient_needs=[],
            hospitals=[close_hospital, far_hospital]
        )
        
        # Close hospital should be ranked first
        assert results[0].hospital.name == "Close Hospital"
    
    # =========================================================================
    # Capacity Scoring Tests
    # =========================================================================
    
    def test_lower_occupancy_preferred(self, recommender):
        """Hospitals with more available beds should be preferred."""
        # Two hospitals at similar distances
        low_occupancy = create_mock_hospital(
            1, "Empty Hospital",
            43.6550, -79.3850,
            total_beds=20, occupied_beds=5  # 25% occupancy
        )
        high_occupancy = create_mock_hospital(
            2, "Full Hospital",
            43.6550, -79.3850,  # Same location
            total_beds=20, occupied_beds=18  # 90% occupancy
        )
        
        results = recommender.recommend(
            incident_lat=43.6530,
            incident_lng=-79.3800,
            incident_severity=IncidentSeverity.MINOR,
            patient_needs=[],
            hospitals=[low_occupancy, high_occupancy]
        )
        
        # Lower occupancy should be ranked first
        assert results[0].hospital.name == "Empty Hospital"
    
    # =========================================================================
    # Specialty Matching Tests
    # =========================================================================
    
    def test_matching_specialty_preferred(self, recommender):
        """Hospitals with matching specialties should be preferred."""
        has_cardiac = create_mock_hospital(
            1, "Cardiac Center",
            43.6550, -79.3850,
            specialties=["cardiac", "trauma"]
        )
        no_cardiac = create_mock_hospital(
            2, "General Hospital",
            43.6550, -79.3850,  # Same location
            specialties=["obstetrics"]
        )
        
        results = recommender.recommend(
            incident_lat=43.6530,
            incident_lng=-79.3800,
            incident_severity=IncidentSeverity.MAJOR,
            patient_needs=["cardiac"],  # Need cardiac care
            hospitals=[has_cardiac, no_cardiac]
        )
        
        # Hospital with cardiac specialty should be ranked first
        assert results[0].hospital.name == "Cardiac Center"
    
    def test_no_specialty_requirement_all_equal(self, recommender):
        """Without specialty requirements, all hospitals qualify equally."""
        hospital1 = create_mock_hospital(
            1, "Hospital 1",
            43.6550, -79.3850,
            specialties=["cardiac"]
        )
        hospital2 = create_mock_hospital(
            2, "Hospital 2",
            43.6550, -79.3850,
            specialties=["trauma"]
        )
        
        results = recommender.recommend(
            incident_lat=43.6530,
            incident_lng=-79.3800,
            incident_severity=IncidentSeverity.MINOR,
            patient_needs=[],  # No specific needs
            hospitals=[hospital1, hospital2]
        )
        
        # Both should have similar scores (specialty component equal)
        assert len(results) == 2
    
    # =========================================================================
    # Trauma Center Tests
    # =========================================================================
    
    def test_trauma_center_preferred_for_critical(self, recommender):
        """Trauma centers should be preferred for critical incidents."""
        trauma_center = create_mock_hospital(
            1, "Trauma Center",
            43.6550, -79.3850,
            is_trauma=True
        )
        regular = create_mock_hospital(
            2, "Regular Hospital",
            43.6550, -79.3850,  # Same location
            is_trauma=False
        )
        
        results = recommender.recommend(
            incident_lat=43.6530,
            incident_lng=-79.3800,
            incident_severity=IncidentSeverity.CRITICAL,
            patient_needs=[],
            hospitals=[trauma_center, regular]
        )
        
        # Trauma center should be ranked first for critical
        assert results[0].hospital.name == "Trauma Center"
    
    def test_trauma_status_less_important_for_minor(self, recommender):
        """Trauma center status matters less for minor incidents."""
        trauma_center = create_mock_hospital(
            1, "Trauma Center",
            43.6550, -79.3850,
            is_trauma=True
        )
        regular = create_mock_hospital(
            2, "Regular Hospital",
            43.6550, -79.3850,
            is_trauma=False
        )
        
        results = recommender.recommend(
            incident_lat=43.6530,
            incident_lng=-79.3800,
            incident_severity=IncidentSeverity.MINOR,
            patient_needs=[],
            hospitals=[trauma_center, regular]
        )
        
        # Scores should be closer for minor incidents
        score_diff = abs(results[0].score - results[1].score)
        assert score_diff < 0.2  # Small difference
    
    # =========================================================================
    # Reason Generation Tests
    # =========================================================================
    
    def test_reasons_not_empty(self, recommender, sample_hospitals):
        """Recommendations should include reasons."""
        results = recommender.recommend(
            incident_lat=43.6530,
            incident_lng=-79.3800,
            incident_severity=IncidentSeverity.MAJOR,
            patient_needs=[],
            hospitals=sample_hospitals
        )
        
        for rec in results:
            assert len(rec.reasons) > 0
    
    def test_reasons_include_distance_info(self, recommender, sample_hospitals):
        """Reasons should mention distance."""
        results = recommender.recommend(
            incident_lat=43.6530,
            incident_lng=-79.3800,
            incident_severity=IncidentSeverity.MAJOR,
            patient_needs=[],
            hospitals=sample_hospitals
        )
        
        for rec in results:
            # At least one reason should mention distance/km/min
            distance_mentioned = any(
                "km" in r.lower() or "min" in r.lower() or "close" in r.lower() or "distance" in r.lower()
                for r in rec.reasons
            )
            assert distance_mentioned
