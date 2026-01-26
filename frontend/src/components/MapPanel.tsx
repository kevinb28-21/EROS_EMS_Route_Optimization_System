/**
 * MapPanel Component
 * 
 * Interactive Leaflet map showing:
 * - Incident markers (color-coded by severity)
 * - Vehicle markers (color-coded by status)
 * - Hospital markers
 * - Route polylines for dispatched vehicles
 */

import { useEffect, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { Incident, Vehicle, Hospital } from '../types';

// Fix for default marker icons in Leaflet with Vite
// @ts-expect-error - Leaflet icon fix
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface MapPanelProps {
  incidents: Incident[];
  vehicles: Vehicle[];
  hospitals: Hospital[];
  onIncidentClick?: (incident: Incident) => void;
  center?: [number, number] | null;
}

// Custom marker icons
const createIncidentIcon = (severity: string) => {
  const colors: Record<string, string> = {
    critical: '#ef4444',
    major: '#f59e0b',
    minor: '#22c55e',
    unknown: '#64748b',
  };
  const color = colors[severity] || colors.unknown;
  
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: 24px;
        height: 24px;
        background: ${color};
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          width: 8px;
          height: 8px;
          background: white;
          border-radius: 50%;
        "></div>
      </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

const createVehicleIcon = (status: string) => {
  const colors: Record<string, string> = {
    available: '#22c55e',
    dispatched: '#3b82f6',
    on_scene: '#f59e0b',
    transporting: '#8b5cf6',
    at_hospital: '#06b6d4',
    off_duty: '#64748b',
  };
  const color = colors[status] || colors.off_duty;
  
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: 28px;
        height: 28px;
        background: ${color};
        border: 3px solid white;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
      ">
        🚑
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
};

const hospitalIcon = L.divIcon({
  className: 'custom-marker',
  html: `
    <div style="
      width: 32px;
      height: 32px;
      background: #0ea5e9;
      border: 3px solid white;
      border-radius: 6px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
    ">
      🏥
    </div>
  `,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

// Component to handle map centering
function MapController({ center }: { center?: [number, number] | null }) {
  const map = useMap();
  const hasSetInitial = useRef(false);

  useEffect(() => {
    if (center) {
      map.setView(center, 15);
    } else if (!hasSetInitial.current) {
      // Default to downtown Toronto
      map.setView([43.6532, -79.3832], 14);
      hasSetInitial.current = true;
    }
  }, [center, map]);

  return null;
}

export default function MapPanel({
  incidents,
  vehicles,
  hospitals,
  onIncidentClick,
  center,
}: MapPanelProps) {
  // Extract route polylines from incidents
  const routePolylines = useMemo(() => {
    const routes: { positions: [number, number][]; color: string }[] = [];
    
    incidents.forEach((incident) => {
      if (incident.route_data?.to_scene?.polyline) {
        routes.push({
          positions: incident.route_data.to_scene.polyline.map(
            (p) => [p[0], p[1]] as [number, number]
          ),
          color: '#3b82f6', // Blue for to-scene routes
        });
      }
      if (incident.route_data?.to_hospital?.polyline) {
        routes.push({
          positions: incident.route_data.to_hospital.polyline.map(
            (p) => [p[0], p[1]] as [number, number]
          ),
          color: '#8b5cf6', // Purple for to-hospital routes
        });
      }
    });
    
    return routes;
  }, [incidents]);

  return (
    <MapContainer
      center={[43.6532, -79.3832]}
      zoom={14}
      className="w-full h-full"
      zoomControl={false}
    >
      <MapController center={center} />
      
      {/* Dark theme map tiles */}
      <TileLayer
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />

      {/* Route polylines */}
      {routePolylines.map((route, index) => (
        <Polyline
          key={`route-${index}`}
          positions={route.positions}
          color={route.color}
          weight={4}
          opacity={0.8}
          dashArray="10, 10"
        />
      ))}

      {/* Hospital markers */}
      {hospitals.map((hospital) => (
        <Marker
          key={`hospital-${hospital.id}`}
          position={[hospital.latitude, hospital.longitude]}
          icon={hospitalIcon}
        >
          <Popup>
            <div className="min-w-[200px]">
              <h3 className="font-bold text-lg mb-2">{hospital.name}</h3>
              <div className="space-y-1 text-sm">
                <p>
                  <span className={`
                    px-2 py-0.5 rounded text-xs font-medium
                    ${hospital.status === 'open' ? 'bg-green-500/20 text-green-400' : ''}
                    ${hospital.status === 'diversion' ? 'bg-amber-500/20 text-amber-400' : ''}
                    ${hospital.status === 'closed' ? 'bg-red-500/20 text-red-400' : ''}
                  `}>
                    {hospital.status.toUpperCase()}
                  </span>
                </p>
                <p>
                  Beds: {hospital.available_beds} / {hospital.total_er_beds} available
                </p>
                <p>
                  Occupancy: {hospital.occupancy_rate.toFixed(0)}%
                </p>
                {hospital.is_trauma_center && (
                  <p className="text-red-400 font-medium">
                    ⚡ Trauma Center
                  </p>
                )}
              </div>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Vehicle markers */}
      {vehicles.map((vehicle) => (
        <Marker
          key={`vehicle-${vehicle.id}`}
          position={[vehicle.latitude, vehicle.longitude]}
          icon={createVehicleIcon(vehicle.status)}
        >
          <Popup>
            <div className="min-w-[180px]">
              <h3 className="font-bold text-lg">{vehicle.call_sign}</h3>
              <p className="text-sm text-gray-400">{vehicle.vehicle_type}</p>
              <p className="mt-2">
                <span className={`
                  px-2 py-0.5 rounded text-xs font-medium capitalize
                  ${vehicle.status === 'available' ? 'bg-green-500/20 text-green-400' : ''}
                  ${vehicle.status === 'dispatched' ? 'bg-blue-500/20 text-blue-400' : ''}
                  ${vehicle.status === 'on_scene' ? 'bg-amber-500/20 text-amber-400' : ''}
                  ${vehicle.status === 'transporting' ? 'bg-purple-500/20 text-purple-400' : ''}
                  ${vehicle.status === 'off_duty' ? 'bg-gray-500/20 text-gray-400' : ''}
                `}>
                  {vehicle.status.replace('_', ' ')}
                </span>
              </p>
              <p className="text-sm mt-1">Crew: {vehicle.crew_count}</p>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Incident markers */}
      {incidents.map((incident) => (
        <Marker
          key={`incident-${incident.id}`}
          position={[incident.latitude, incident.longitude]}
          icon={createIncidentIcon(incident.severity)}
          eventHandlers={{
            click: () => onIncidentClick?.(incident),
          }}
        >
          <Popup>
            <div className="min-w-[220px]">
              <div className="flex items-center gap-2 mb-2">
                <span className={`
                  px-2 py-0.5 rounded text-xs font-bold uppercase
                  ${incident.severity === 'critical' ? 'bg-red-500/20 text-red-400' : ''}
                  ${incident.severity === 'major' ? 'bg-amber-500/20 text-amber-400' : ''}
                  ${incident.severity === 'minor' ? 'bg-green-500/20 text-green-400' : ''}
                  ${incident.severity === 'unknown' ? 'bg-gray-500/20 text-gray-400' : ''}
                `}>
                  {incident.severity}
                </span>
                <span className="text-xs text-gray-400">
                  #{incident.id}
                </span>
              </div>
              <p className="text-sm mb-2">{incident.description}</p>
              {incident.address && (
                <p className="text-xs text-gray-400">{incident.address}</p>
              )}
              <button
                onClick={() => onIncidentClick?.(incident)}
                className="mt-2 text-xs text-blue-400 hover:text-blue-300"
              >
                View Details →
              </button>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
