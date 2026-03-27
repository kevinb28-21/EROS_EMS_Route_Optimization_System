/**
 * HospitalList Component
 * 
 * Compact list of hospitals with capacity bars.
 */

import { AlertTriangle } from 'lucide-react';
import type { Hospital } from '../types';
import clsx from 'clsx';

interface HospitalListProps {
  hospitals: Hospital[];
  loading: boolean;
  onFocusOnMap: (lat: number, lng: number) => void;
}

export default function HospitalList({
  hospitals,
  loading,
  onFocusOnMap,
}: HospitalListProps) {
  if (loading) {
    return (
      <div className="p-4 text-center text-eros-text-muted">
        Loading hospitals...
      </div>
    );
  }

  // Sort by status (open first) then by name
  const sortedHospitals = [...hospitals].sort((a, b) => {
    const statusOrder = { open: 0, diversion: 1, closed: 2 };
    const statusDiff = statusOrder[a.status] - statusOrder[b.status];
    if (statusDiff !== 0) return statusDiff;
    return a.name.localeCompare(b.name);
  });

  return (
    <div className="p-2 space-y-2">
      {sortedHospitals.map((hospital) => {
        const occupancyPercent = hospital.occupancy_rate;
        const isHighOccupancy = occupancyPercent >= 80;
        const isDiversion = hospital.status === 'diversion';
        const isClosed = hospital.status === 'closed';
        
        return (
          <div
            key={hospital.id}
            className={clsx(
              'p-2 rounded-lg border cursor-pointer transition-colors',
              'bg-eros-card hover:bg-eros-card-hover',
              isDiversion && 'border-eros-major/50',
              isClosed && 'border-eros-critical/50 opacity-60',
              !isDiversion && !isClosed && 'border-eros-border'
            )}
            onClick={() => onFocusOnMap(hospital.latitude, hospital.longitude)}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-sm font-medium text-eros-text truncate">
                  {hospital.name}
                </span>
                {hospital.is_trauma_center && (
                  <span className="text-[10px] px-1 py-0.5 bg-eros-critical/20 text-eros-critical rounded">
                    TRAUMA
                  </span>
                )}
              </div>
              
              {isDiversion && (
                <span className="text-[10px] px-1.5 py-0.5 bg-eros-major/20 text-eros-major rounded flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  DIVERSION
                </span>
              )}
              {isClosed && (
                <span className="text-[10px] px-1.5 py-0.5 bg-eros-critical/20 text-eros-critical rounded">
                  CLOSED
                </span>
              )}
            </div>
            
            {/* Capacity bar */}
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-eros-darker rounded-full overflow-hidden">
                <div
                  className={clsx(
                    'h-full rounded-full transition-all',
                    occupancyPercent >= 90 && 'bg-eros-critical',
                    occupancyPercent >= 70 && occupancyPercent < 90 && 'bg-eros-major',
                    occupancyPercent < 70 && 'bg-eros-minor'
                  )}
                  style={{ width: `${Math.min(100, occupancyPercent)}%` }}
                />
              </div>
              <span className={clsx(
                'text-xs font-mono min-w-[60px] text-right',
                isHighOccupancy ? 'text-eros-major' : 'text-eros-text-muted'
              )}>
                {hospital.available_beds}/{hospital.total_er_beds}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
