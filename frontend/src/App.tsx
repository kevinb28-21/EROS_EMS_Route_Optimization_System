/**
 * EROS - EMS Route Optimization System
 * Main Application Component
 * 
 * A unified EMS Dispatcher System dashboard with:
 * - Interactive map with incidents, vehicles, and hospitals
 * - Incident management panel
 * - Vehicle status panel
 * - Hospital availability panel
 * - Real-time event log
 */

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { 
  AlertTriangle, 
  Ambulance, 
  Building2, 
  Activity,
  Plus,
  RefreshCw
} from 'lucide-react';

import { incidentsApi, vehiclesApi, hospitalsApi, statusUpdatesApi } from './api/client';
import type { Incident, Vehicle, Hospital } from './types';

import MapPanel from './components/MapPanel';
import IncidentList from './components/IncidentList';
import VehicleList from './components/VehicleList';
import HospitalList from './components/HospitalList';
import EventLog from './components/EventLog';
import CreateIncidentModal from './components/CreateIncidentModal';
import IncidentDetailModal from './components/IncidentDetailModal';

function App() {
  const queryClient = useQueryClient();
  
  // Modal states
  const [showCreateIncident, setShowCreateIncident] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  
  // Map focus state
  const [mapCenter, setMapCenter] = useState<[number, number] | null>(null);
  
  // Fetch data
  const { data: incidentsData, isLoading: incidentsLoading } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => incidentsApi.list({ page_size: 50 }),
  });

  const { data: vehiclesData, isLoading: vehiclesLoading } = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => vehiclesApi.list({ page_size: 50 }),
  });

  const { data: hospitalsData, isLoading: hospitalsLoading } = useQuery({
    queryKey: ['hospitals'],
    queryFn: () => hospitalsApi.list({ page_size: 50 }),
  });

  const { data: statusUpdates } = useQuery({
    queryKey: ['statusUpdates'],
    queryFn: () => statusUpdatesApi.getRecent(30),
  });

  // Active incidents (not completed/cancelled)
  const activeIncidents = incidentsData?.items.filter(
    (i) => !['completed', 'cancelled'].includes(i.status)
  ) || [];
  
  // Available vehicles
  const availableVehicles = vehiclesData?.items.filter(
    (v) => v.status === 'available'
  ) || [];

  const handleRefresh = () => {
    queryClient.invalidateQueries();
  };

  const handleIncidentClick = (incident: Incident) => {
    setSelectedIncident(incident);
  };

  const handleFocusOnMap = (lat: number, lng: number) => {
    setMapCenter([lat, lng]);
  };

  return (
    <div className="h-screen flex flex-col bg-eros-dark overflow-hidden">
      {/* Header */}
      <header className="bg-eros-darker border-b border-eros-border px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-eros-primary/20 rounded-lg flex items-center justify-center">
            <Activity className="w-6 h-6 text-eros-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-eros-text">EROS</h1>
            <p className="text-xs text-eros-text-muted">EMS Route Optimization System</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Quick stats */}
          <div className="hidden md:flex items-center gap-6 mr-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-eros-critical" />
              <span className="text-sm text-eros-text-muted">
                <span className="font-semibold text-eros-text">{activeIncidents.length}</span> Active
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Ambulance className="w-4 h-4 text-eros-available" />
              <span className="text-sm text-eros-text-muted">
                <span className="font-semibold text-eros-text">{availableVehicles.length}</span> Available
              </span>
            </div>
          </div>
          
          <button
            onClick={handleRefresh}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span className="hidden sm:inline">Refresh</span>
          </button>
          
          <button
            onClick={() => setShowCreateIncident(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">New Incident</span>
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left panel - Map */}
        <div className="flex-1 relative">
          <MapPanel
            incidents={activeIncidents}
            vehicles={vehiclesData?.items || []}
            hospitals={hospitalsData?.items || []}
            onIncidentClick={handleIncidentClick}
            center={mapCenter}
          />
        </div>

        {/* Right panel - Dashboard panels */}
        <div className="w-[420px] bg-eros-darker border-l border-eros-border flex flex-col overflow-hidden">
          {/* Incidents Panel */}
          <div className="flex-1 min-h-0 flex flex-col">
            <div className="eros-card-header">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-eros-critical" />
                <span className="font-semibold">Active Incidents</span>
                <span className="text-xs text-eros-text-muted">
                  ({activeIncidents.length})
                </span>
              </div>
            </div>
            <div className="flex-1 overflow-auto">
              <IncidentList
                incidents={activeIncidents}
                loading={incidentsLoading}
                onIncidentClick={handleIncidentClick}
                onFocusOnMap={handleFocusOnMap}
              />
            </div>
          </div>

          {/* Vehicles Panel */}
          <div className="h-[200px] border-t border-eros-border flex flex-col">
            <div className="eros-card-header">
              <div className="flex items-center gap-2">
                <Ambulance className="w-4 h-4 text-eros-primary" />
                <span className="font-semibold">Vehicles</span>
                <span className="text-xs text-eros-text-muted">
                  ({vehiclesData?.items.length || 0})
                </span>
              </div>
            </div>
            <div className="flex-1 overflow-auto">
              <VehicleList
                vehicles={vehiclesData?.items || []}
                loading={vehiclesLoading}
                onFocusOnMap={handleFocusOnMap}
              />
            </div>
          </div>

          {/* Hospitals Panel */}
          <div className="h-[180px] border-t border-eros-border flex flex-col">
            <div className="eros-card-header">
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-eros-major" />
                <span className="font-semibold">Hospitals</span>
              </div>
            </div>
            <div className="flex-1 overflow-auto">
              <HospitalList
                hospitals={hospitalsData?.items || []}
                loading={hospitalsLoading}
                onFocusOnMap={handleFocusOnMap}
              />
            </div>
          </div>

          {/* Event Log */}
          <div className="h-[180px] border-t border-eros-border flex flex-col">
            <div className="eros-card-header">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-eros-text-muted" />
                <span className="font-semibold">Event Log</span>
              </div>
            </div>
            <div className="flex-1 overflow-auto">
              <EventLog updates={statusUpdates || []} />
            </div>
          </div>
        </div>
      </main>

      {/* Modals */}
      {showCreateIncident && (
        <CreateIncidentModal
          onClose={() => setShowCreateIncident(false)}
          onCreated={(incident) => {
            setShowCreateIncident(false);
            setSelectedIncident(incident);
          }}
        />
      )}

      {selectedIncident && (
        <IncidentDetailModal
          incident={selectedIncident}
          vehicles={vehiclesData?.items || []}
          hospitals={hospitalsData?.items || []}
          onClose={() => setSelectedIncident(null)}
          onUpdated={(updated) => setSelectedIncident(updated)}
        />
      )}
    </div>
  );
}

export default App;
