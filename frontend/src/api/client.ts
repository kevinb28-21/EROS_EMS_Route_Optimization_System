/**
 * API client for EROS backend.
 * 
 * Uses axios with base URL pointing to the FastAPI backend.
 */

import axios from 'axios';
import type {
  Incident,
  Vehicle,
  Hospital,
  StatusUpdate,
  PaginatedResponse,
  IncidentCreate,
  AssignVehicleRequest,
  AssignHospitalRequest,
  HospitalRecommendation,
  IncidentStatus,
} from '../types';

/**
 * API base URL for axios.
 * - Local dev: leave VITE_API_URL unset → `/api/v1` (Vite proxies to backend).
 * - Production (Netlify): set VITE_API_URL to your Railway backend origin, e.g. `https://eros-api.up.railway.app`
 */
function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_URL as string | undefined;
  const trimmed = raw?.replace(/\/$/, '') ?? '';
  return trimmed ? `${trimmed}/api/v1` : '/api/v1';
}

const api = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Incidents API
// ============================================================================

export const incidentsApi = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }): Promise<PaginatedResponse<Incident>> => {
    const { data } = await api.get('/incidents', { params });
    return data;
  },

  get: async (id: number): Promise<Incident> => {
    const { data } = await api.get(`/incidents/${id}`);
    return data;
  },

  create: async (incident: IncidentCreate): Promise<Incident> => {
    const { data } = await api.post('/incidents', incident);
    return data;
  },

  update: async (
    id: number,
    updates: Partial<Incident>
  ): Promise<Incident> => {
    const { data } = await api.patch(`/incidents/${id}`, updates);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/incidents/${id}`);
  },

  assignVehicle: async (
    id: number,
    request: AssignVehicleRequest
  ): Promise<Incident> => {
    const { data } = await api.post(`/incidents/${id}/assign-vehicle`, request);
    return data;
  },

  assignHospital: async (
    id: number,
    request: AssignHospitalRequest
  ): Promise<Incident> => {
    const { data } = await api.post(`/incidents/${id}/assign-hospital`, request);
    return data;
  },

  updateStatus: async (
    id: number,
    status: IncidentStatus
  ): Promise<Incident> => {
    const { data } = await api.post(
      `/incidents/${id}/update-status`,
      null,
      { params: { new_status: status } }
    );
    return data;
  },
};

// ============================================================================
// Vehicles API
// ============================================================================

export const vehiclesApi = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }): Promise<PaginatedResponse<Vehicle>> => {
    const { data } = await api.get('/vehicles', { params });
    return data;
  },

  listAvailable: async (): Promise<Vehicle[]> => {
    const { data } = await api.get('/vehicles/available');
    return data;
  },

  get: async (id: number): Promise<Vehicle> => {
    const { data } = await api.get(`/vehicles/${id}`);
    return data;
  },

  updatePosition: async (
    id: number,
    lat: number,
    lng: number
  ): Promise<Vehicle> => {
    const { data } = await api.post(
      `/vehicles/${id}/update-position`,
      null,
      { params: { latitude: lat, longitude: lng } }
    );
    return data;
  },
};

// ============================================================================
// Hospitals API
// ============================================================================

export const hospitalsApi = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }): Promise<PaginatedResponse<Hospital>> => {
    const { data } = await api.get('/hospitals', { params });
    return data;
  },

  listAccepting: async (): Promise<Hospital[]> => {
    const { data } = await api.get('/hospitals/accepting');
    return data;
  },

  get: async (id: number): Promise<Hospital> => {
    const { data } = await api.get(`/hospitals/${id}`);
    return data;
  },

  recommend: async (
    incidentId: number,
    patientNeeds?: string[]
  ): Promise<{ incident_id: number; recommendations: HospitalRecommendation[] }> => {
    const { data } = await api.post('/hospitals/recommend', {
      incident_id: incidentId,
      patient_needs: patientNeeds || [],
    });
    return data;
  },

  updateCapacity: async (
    id: number,
    occupiedBeds: number
  ): Promise<Hospital> => {
    const { data } = await api.post(
      `/hospitals/${id}/update-capacity`,
      null,
      { params: { occupied_beds: occupiedBeds } }
    );
    return data;
  },
};

// ============================================================================
// Status Updates API
// ============================================================================

export const statusUpdatesApi = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    incident_id?: number;
  }): Promise<PaginatedResponse<StatusUpdate>> => {
    const { data } = await api.get('/status-updates', { params });
    return data;
  },

  getRecent: async (limit = 20): Promise<StatusUpdate[]> => {
    const { data } = await api.get('/status-updates/recent', {
      params: { limit },
    });
    return data;
  },

  create: async (update: {
    message: string;
    incident_id?: number;
    vehicle_id?: number;
    hospital_id?: number;
    update_type?: string;
    source?: string;
  }): Promise<StatusUpdate> => {
    const { data } = await api.post('/status-updates', update);
    return data;
  },
};

// ============================================================================
// Routes API
// ============================================================================

export const routesApi = {
  calculate: async (
    originLat: number,
    originLng: number,
    destLat: number,
    destLng: number
  ): Promise<{
    distance_km: number;
    estimated_time_minutes: number;
    polyline: [number, number][];
  }> => {
    const { data } = await api.post('/routes/calculate', {
      origin_lat: originLat,
      origin_lng: originLng,
      destination_lat: destLat,
      destination_lng: destLng,
    });
    return data;
  },
};

// ============================================================================
// Simulation API
// ============================================================================

export const simulationApi = {
  getStatus: async (): Promise<{
    simulation_running: boolean;
    interval_seconds: number | null;
    traffic: {
      hour: number;
      level: string;
      description: string;
      civilian_multiplier: number;
      ems_multiplier: number;
    };
  }> => {
    const { data } = await api.get('/simulation/status');
    return data;
  },

  tick: async (): Promise<{ status: string; message: string }> => {
    const { data } = await api.post('/simulation/tick');
    return data;
  },

  generateIncident: async (): Promise<{
    status: string;
    incident_id?: number;
    description?: string;
    message?: string;
  }> => {
    const { data } = await api.post('/simulation/generate-incident');
    return data;
  },
};

export default api;
