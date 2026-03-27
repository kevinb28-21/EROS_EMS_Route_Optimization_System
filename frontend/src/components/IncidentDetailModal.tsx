/**
 * IncidentDetailModal Component
 * 
 * Detailed view of an incident with dispatch controls.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { formatDistanceToNow, format } from 'date-fns';
import { 
  X, 
  MapPin, 
  Clock, 
  Ambulance, 
  Building2, 
  CheckCircle,
  XCircle,
  Truck,
  Navigation
} from 'lucide-react';
import { incidentsApi, hospitalsApi } from '../api/client';
import type { Incident, Vehicle, Hospital, IncidentStatus } from '../types';
import clsx from 'clsx';

interface IncidentDetailModalProps {
  incident: Incident;
  vehicles: Vehicle[];
  hospitals: Hospital[];
  onClose: () => void;
  onUpdated: (incident: Incident) => void;
}

const statusFlow: { status: IncidentStatus; label: string; icon: typeof Clock }[] = [
  { status: 'pending', label: 'Pending', icon: Clock },
  { status: 'dispatched', label: 'Dispatched', icon: Truck },
  { status: 'on_scene', label: 'On Scene', icon: MapPin },
  { status: 'transporting', label: 'Transporting', icon: Navigation },
  { status: 'completed', label: 'Completed', icon: CheckCircle },
];

export default function IncidentDetailModal({
  incident,
  vehicles,
  hospitals,
  onClose,
  onUpdated,
}: IncidentDetailModalProps) {
  const queryClient = useQueryClient();
  const [selectedVehicleId, setSelectedVehicleId] = useState<number | null>(null);
  const [selectedHospitalId, setSelectedHospitalId] = useState<number | null>(null);
  
  // Fetch hospital recommendations
  const { data: recommendations } = useQuery({
    queryKey: ['hospitalRecommendations', incident.id],
    queryFn: () => hospitalsApi.recommend(incident.id),
    enabled: incident.status === 'on_scene' && !incident.destination_hospital_id,
  });
  
  // Available vehicles for dispatch
  const availableVehicles = vehicles.filter(v => v.status === 'available');
  
  // Mutations
  const assignVehicleMutation = useMutation({
    mutationFn: (vehicleId: number) => 
      incidentsApi.assignVehicle(incident.id, { vehicle_id: vehicleId, auto_route: true }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      queryClient.invalidateQueries({ queryKey: ['statusUpdates'] });
      onUpdated(updated);
    },
  });
  
  const assignHospitalMutation = useMutation({
    mutationFn: (hospitalId: number) =>
      incidentsApi.assignHospital(incident.id, { hospital_id: hospitalId, auto_route: true }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      queryClient.invalidateQueries({ queryKey: ['statusUpdates'] });
      onUpdated(updated);
    },
  });
  
  const updateStatusMutation = useMutation({
    mutationFn: (status: IncidentStatus) => incidentsApi.updateStatus(incident.id, status),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      queryClient.invalidateQueries({ queryKey: ['statusUpdates'] });
      onUpdated(updated);
    },
  });
  
  const handleAssignVehicle = () => {
    if (selectedVehicleId) {
      assignVehicleMutation.mutate(selectedVehicleId);
    }
  };
  
  const handleAssignHospital = () => {
    if (selectedHospitalId) {
      assignHospitalMutation.mutate(selectedHospitalId);
    }
  };
  
  const handleStatusChange = (newStatus: IncidentStatus) => {
    updateStatusMutation.mutate(newStatus);
  };
  
  // Assigned vehicle info
  const assignedVehicle = vehicles.find(v => v.id === incident.assigned_vehicle_id);
  const destinationHospital = hospitals.find(h => h.id === incident.destination_hospital_id);

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4" style={{ zIndex: 9999 }}>
      <div className="bg-eros-card rounded-xl border border-eros-border w-full max-w-2xl shadow-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className={clsx(
          'flex items-center justify-between p-4 border-b border-eros-border',
          incident.severity === 'critical' && 'bg-eros-critical/10',
          incident.severity === 'major' && 'bg-eros-major/10'
        )}>
          <div className="flex items-center gap-3">
            <span className={clsx(
              'px-2 py-1 rounded text-xs font-bold uppercase',
              incident.severity === 'critical' && 'bg-eros-critical/20 text-eros-critical',
              incident.severity === 'major' && 'bg-eros-major/20 text-eros-major',
              incident.severity === 'minor' && 'bg-eros-minor/20 text-eros-minor',
              incident.severity === 'unknown' && 'bg-eros-text-dim/20 text-eros-text-dim'
            )}>
              {incident.severity}
            </span>
            <h2 className="text-lg font-semibold">Incident #{incident.id}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-eros-card-hover rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {/* Description */}
          <div>
            <p className="text-eros-text">{incident.description}</p>
            {incident.address && (
              <p className="text-sm text-eros-text-muted mt-1 flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {incident.address}
              </p>
            )}
            <p className="text-xs text-eros-text-dim mt-1 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Reported {formatDistanceToNow(new Date(incident.reported_at), { addSuffix: true })}
              {' · '}
              {format(new Date(incident.reported_at), 'MMM d, yyyy h:mm a')}
            </p>
          </div>
          
          {/* Status Flow */}
          <div className="bg-eros-darker rounded-lg p-3">
            <div className="flex items-center justify-between">
              {statusFlow.map((step, index) => {
                const isActive = incident.status === step.status;
                const isPast = statusFlow.findIndex(s => s.status === incident.status) > index;
                const Icon = step.icon;
                
                return (
                  <div key={step.status} className="flex items-center">
                    <div className={clsx(
                      'flex flex-col items-center',
                      isActive && 'text-eros-primary',
                      isPast && 'text-eros-minor',
                      !isActive && !isPast && 'text-eros-text-dim'
                    )}>
                      <div className={clsx(
                        'w-8 h-8 rounded-full flex items-center justify-center',
                        isActive && 'bg-eros-primary/20',
                        isPast && 'bg-eros-minor/20',
                        !isActive && !isPast && 'bg-eros-card-hover'
                      )}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className="text-[10px] mt-1">{step.label}</span>
                    </div>
                    {index < statusFlow.length - 1 && (
                      <div className={clsx(
                        'w-8 h-0.5 mx-1',
                        isPast ? 'bg-eros-minor' : 'bg-eros-border'
                      )} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          
          {/* Vehicle Assignment */}
          {incident.status === 'pending' && (
            <div className="bg-eros-darker rounded-lg p-4">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Ambulance className="w-4 h-4 text-eros-primary" />
                Assign Vehicle
              </h3>
              
              {availableVehicles.length === 0 ? (
                <p className="text-sm text-eros-text-muted">
                  No vehicles available for dispatch
                </p>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    {availableVehicles.map((vehicle) => (
                      <button
                        key={vehicle.id}
                        onClick={() => setSelectedVehicleId(vehicle.id)}
                        className={clsx(
                          'p-2 rounded-lg border text-left transition-all',
                          selectedVehicleId === vehicle.id
                            ? 'border-eros-primary bg-eros-primary/10'
                            : 'border-eros-border hover:border-eros-primary/50'
                        )}
                      >
                        <span className="font-mono text-sm font-medium">
                          {vehicle.call_sign}
                        </span>
                        <span className="text-xs text-eros-text-muted ml-2">
                          {vehicle.vehicle_type}
                        </span>
                      </button>
                    ))}
                  </div>
                  
                  <button
                    onClick={handleAssignVehicle}
                    disabled={!selectedVehicleId || assignVehicleMutation.isPending}
                    className="btn btn-primary w-full"
                  >
                    {assignVehicleMutation.isPending ? 'Dispatching...' : 'Dispatch Vehicle'}
                  </button>
                </>
              )}
            </div>
          )}
          
          {/* Assigned Vehicle Info */}
          {assignedVehicle && (
            <div className="bg-eros-dispatched/10 border border-eros-dispatched/30 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Ambulance className="w-4 h-4 text-eros-dispatched" />
                  <span className="font-mono font-medium">{assignedVehicle.call_sign}</span>
                  <span className="text-xs text-eros-text-muted">{assignedVehicle.vehicle_type}</span>
                </div>
                <span className="text-xs capitalize text-eros-dispatched">
                  {assignedVehicle.status.replace('_', ' ')}
                </span>
              </div>
              
              {incident.route_data?.to_scene && (
                <div className="mt-2 text-xs text-eros-text-muted space-y-0.5">
                  <span>
                    ETA: ~{incident.route_data.to_scene.estimated_time_minutes.toFixed(0)} min
                    ({incident.route_data.to_scene.distance_km.toFixed(1)} km)
                  </span>
                  {incident.route_data.to_scene.traffic_level && (
                    <span className={`ml-2 capitalize ${
                      incident.route_data.to_scene.traffic_level === 'heavy' ? 'text-eros-critical' :
                      incident.route_data.to_scene.traffic_level === 'moderate' ? 'text-eros-major' :
                      'text-eros-minor'
                    }`}>
                      · {incident.route_data.to_scene.traffic_level} traffic
                    </span>
                  )}
                </div>
              )}
            </div>
          )}
          
          {/* Hospital Assignment (when on scene) */}
          {(incident.status === 'on_scene' || incident.status === 'dispatched') && !incident.destination_hospital_id && (
            <div className="bg-eros-darker rounded-lg p-4">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-eros-major" />
                Assign Hospital
              </h3>
              
              {recommendations?.recommendations && recommendations.recommendations.length > 0 ? (
                <>
                  <p className="text-xs text-eros-text-muted mb-2">
                    Recommended based on distance, capacity, and specialties:
                  </p>
                  <div className="space-y-2 mb-3">
                    {recommendations.recommendations.slice(0, 3).map((rec) => (
                      <button
                        key={rec.hospital.id}
                        onClick={() => setSelectedHospitalId(rec.hospital.id)}
                        className={clsx(
                          'w-full p-2 rounded-lg border text-left transition-all',
                          selectedHospitalId === rec.hospital.id
                            ? 'border-eros-primary bg-eros-primary/10'
                            : 'border-eros-border hover:border-eros-primary/50'
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">{rec.hospital.name}</span>
                          <span className="text-xs text-eros-text-muted">
                            Score: {(rec.score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-eros-text-muted mt-1">
                          <span>{rec.distance_km.toFixed(1)} km</span>
                          <span>~{rec.estimated_time_minutes.toFixed(0)} min</span>
                          <span>{rec.hospital.available_beds} beds free</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </>
              ) : (
                <div className="space-y-2 mb-3">
                  {hospitals.filter(h => h.status === 'open').slice(0, 3).map((hospital) => (
                    <button
                      key={hospital.id}
                      onClick={() => setSelectedHospitalId(hospital.id)}
                      className={clsx(
                        'w-full p-2 rounded-lg border text-left transition-all',
                        selectedHospitalId === hospital.id
                          ? 'border-eros-primary bg-eros-primary/10'
                          : 'border-eros-border hover:border-eros-primary/50'
                      )}
                    >
                      <span className="text-sm font-medium">{hospital.name}</span>
                      <span className="text-xs text-eros-text-muted ml-2">
                        {hospital.available_beds} beds free
                      </span>
                    </button>
                  ))}
                </div>
              )}
              
              <button
                onClick={handleAssignHospital}
                disabled={!selectedHospitalId || assignHospitalMutation.isPending}
                className="btn btn-primary w-full"
              >
                {assignHospitalMutation.isPending ? 'Assigning...' : 'Set Destination'}
              </button>
            </div>
          )}
          
          {/* Destination Hospital Info */}
          {destinationHospital && (
            <div className="bg-eros-major/10 border border-eros-major/30 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-eros-major" />
                  <span className="font-medium">{destinationHospital.name}</span>
                </div>
                <span className="text-xs text-eros-text-muted">
                  {destinationHospital.available_beds} beds free
                </span>
              </div>
              
              {incident.route_data?.to_hospital && (
                <div className="mt-2 text-xs text-eros-text-muted">
                  ETA: ~{incident.route_data.to_hospital.estimated_time_minutes.toFixed(0)} min
                  ({incident.route_data.to_hospital.distance_km.toFixed(1)} km)
                  {incident.route_data.to_hospital.traffic_level && (
                    <span className={`ml-1 capitalize ${
                      incident.route_data.to_hospital.traffic_level === 'heavy' ? 'text-eros-critical' :
                      incident.route_data.to_hospital.traffic_level === 'moderate' ? 'text-eros-major' :
                      'text-eros-minor'
                    }`}>
                      · {incident.route_data.to_hospital.traffic_level} traffic
                    </span>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Footer actions */}
        <div className="p-4 border-t border-eros-border flex gap-3">
          {incident.status === 'dispatched' && (
            <button
              onClick={() => handleStatusChange('on_scene')}
              disabled={updateStatusMutation.isPending}
              className="btn btn-primary flex-1"
            >
              Mark On Scene
            </button>
          )}
          
          {incident.status === 'on_scene' && incident.destination_hospital_id && (
            <button
              onClick={() => handleStatusChange('transporting')}
              disabled={updateStatusMutation.isPending}
              className="btn btn-primary flex-1"
            >
              Begin Transport
            </button>
          )}
          
          {incident.status === 'transporting' && (
            <button
              onClick={() => handleStatusChange('completed')}
              disabled={updateStatusMutation.isPending}
              className="btn bg-eros-minor hover:bg-eros-minor-dim text-white flex-1"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Complete Incident
            </button>
          )}
          
          {!['completed', 'cancelled'].includes(incident.status) && (
            <button
              onClick={() => handleStatusChange('cancelled')}
              disabled={updateStatusMutation.isPending}
              className="btn btn-secondary"
            >
              <XCircle className="w-4 h-4 mr-2" />
              Cancel
            </button>
          )}
          
          <button onClick={onClose} className="btn btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
