/**
 * VehicleList Component
 * 
 * Compact list of EMS vehicles with status indicators.
 */

import type { Vehicle } from '../types';
import clsx from 'clsx';

interface VehicleListProps {
  vehicles: Vehicle[];
  loading: boolean;
  onFocusOnMap: (lat: number, lng: number) => void;
}

const statusConfig: Record<string, { color: string; bg: string; label: string }> = {
  available: {
    color: 'text-eros-available',
    bg: 'bg-eros-available',
    label: 'Available',
  },
  dispatched: {
    color: 'text-eros-dispatched',
    bg: 'bg-eros-dispatched',
    label: 'Dispatched',
  },
  on_scene: {
    color: 'text-eros-on-scene',
    bg: 'bg-eros-on-scene',
    label: 'On Scene',
  },
  transporting: {
    color: 'text-eros-transporting',
    bg: 'bg-eros-transporting',
    label: 'Transport',
  },
  at_hospital: {
    color: 'text-cyan-400',
    bg: 'bg-cyan-400',
    label: 'At Hospital',
  },
  off_duty: {
    color: 'text-eros-text-dim',
    bg: 'bg-eros-text-dim',
    label: 'Off Duty',
  },
};

export default function VehicleList({
  vehicles,
  loading,
  onFocusOnMap,
}: VehicleListProps) {
  if (loading) {
    return (
      <div className="p-4 text-center text-eros-text-muted">
        Loading vehicles...
      </div>
    );
  }

  // Sort: available first, then by call sign
  const sortedVehicles = [...vehicles].sort((a, b) => {
    if (a.status === 'available' && b.status !== 'available') return -1;
    if (a.status !== 'available' && b.status === 'available') return 1;
    return a.call_sign.localeCompare(b.call_sign);
  });

  return (
    <div className="grid grid-cols-2 gap-2 p-2">
      {sortedVehicles.map((vehicle) => {
        const config = statusConfig[vehicle.status] || statusConfig.off_duty;
        
        return (
          <div
            key={vehicle.id}
            className={clsx(
              'p-2 rounded-lg border transition-colors cursor-pointer',
              'bg-eros-card hover:bg-eros-card-hover border-eros-border'
            )}
            onClick={() => onFocusOnMap(vehicle.latitude, vehicle.longitude)}
          >
            <div className="flex items-center gap-2 mb-1">
              {/* Status indicator dot */}
              <div className={clsx('w-2 h-2 rounded-full', config.bg)} />
              
              {/* Call sign */}
              <span className="font-mono text-sm font-medium text-eros-text">
                {vehicle.call_sign}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className={clsx('text-xs', config.color)}>
                {config.label}
              </span>
              <span className="text-[10px] text-eros-text-dim">
                {vehicle.vehicle_type}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
