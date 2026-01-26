/**
 * TypeScript types for EROS frontend.
 * 
 * These mirror the backend Pydantic schemas.
 */

// Enums
export type IncidentSeverity = 'critical' | 'major' | 'minor' | 'unknown';
export type IncidentStatus = 'pending' | 'dispatched' | 'on_scene' | 'transporting' | 'completed' | 'cancelled';
export type VehicleStatus = 'available' | 'dispatched' | 'on_scene' | 'transporting' | 'at_hospital' | 'off_duty';
export type HospitalStatus = 'open' | 'diversion' | 'closed';

// Base entities
export interface Incident {
  id: number;
  latitude: number;
  longitude: number;
  address: string | null;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  reported_at: string;
  dispatched_at: string | null;
  resolved_at: string | null;
  assigned_vehicle_id: number | null;
  destination_hospital_id: number | null;
  route_data: RouteData | null;
  created_at: string;
  updated_at: string;
}

export interface Vehicle {
  id: number;
  call_sign: string;
  vehicle_type: string;
  latitude: number;
  longitude: number;
  status: VehicleStatus;
  crew_count: number;
  route_progress: RouteProgress | null;
  created_at: string;
  updated_at: string;
}

export interface Hospital {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  address: string | null;
  total_er_beds: number;
  occupied_er_beds: number;
  status: HospitalStatus;
  specialties: string[];
  is_trauma_center: boolean;
  available_beds: number;
  occupancy_rate: number;
  created_at: string;
  updated_at: string;
}

export interface StatusUpdate {
  id: number;
  incident_id: number | null;
  vehicle_id: number | null;
  hospital_id: number | null;
  message: string;
  update_type: string;
  source: string;
  created_at: string;
}

// Route-related types
export interface RouteData {
  to_scene?: RouteSegment;
  to_hospital?: RouteSegment;
}

export interface RouteSegment {
  polyline: [number, number][];
  distance_km: number;
  estimated_time_minutes: number;
}

export interface RouteProgress {
  waypoints: [number, number][];
  current_index: number;
  target: 'scene' | 'hospital';
}

// Hospital recommendation
export interface HospitalRecommendation {
  hospital: Hospital;
  score: number;
  distance_km: number;
  estimated_time_minutes: number;
  reasons: string[];
}

// API response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// Create/Update types
export interface IncidentCreate {
  latitude: number;
  longitude: number;
  address?: string;
  description: string;
  severity: IncidentSeverity;
}

export interface AssignVehicleRequest {
  vehicle_id: number;
  auto_route?: boolean;
}

export interface AssignHospitalRequest {
  hospital_id: number;
  auto_route?: boolean;
}
