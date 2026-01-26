/**
 * IncidentList Component
 * 
 * Displays list of active incidents with severity badges and status.
 */

import { formatDistanceToNow } from 'date-fns';
import { MapPin, Clock, AlertTriangle, AlertCircle, Info, HelpCircle } from 'lucide-react';
import type { Incident } from '../types';
import clsx from 'clsx';

interface IncidentListProps {
  incidents: Incident[];
  loading: boolean;
  onIncidentClick: (incident: Incident) => void;
  onFocusOnMap: (lat: number, lng: number) => void;
}

const severityConfig = {
  critical: {
    icon: AlertTriangle,
    color: 'text-eros-critical',
    bg: 'bg-eros-critical/10',
    border: 'border-eros-critical/30',
    label: 'CRITICAL',
  },
  major: {
    icon: AlertCircle,
    color: 'text-eros-major',
    bg: 'bg-eros-major/10',
    border: 'border-eros-major/30',
    label: 'MAJOR',
  },
  minor: {
    icon: Info,
    color: 'text-eros-minor',
    bg: 'bg-eros-minor/10',
    border: 'border-eros-minor/30',
    label: 'MINOR',
  },
  unknown: {
    icon: HelpCircle,
    color: 'text-eros-text-dim',
    bg: 'bg-eros-text-dim/10',
    border: 'border-eros-text-dim/30',
    label: 'UNKNOWN',
  },
};

const statusLabels: Record<string, string> = {
  pending: 'Awaiting Dispatch',
  dispatched: 'Unit En Route',
  on_scene: 'On Scene',
  transporting: 'Transporting',
  completed: 'Completed',
  cancelled: 'Cancelled',
};

export default function IncidentList({
  incidents,
  loading,
  onIncidentClick,
  onFocusOnMap,
}: IncidentListProps) {
  if (loading) {
    return (
      <div className="p-4 text-center text-eros-text-muted">
        Loading incidents...
      </div>
    );
  }

  if (incidents.length === 0) {
    return (
      <div className="p-4 text-center text-eros-text-muted">
        <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>No active incidents</p>
      </div>
    );
  }

  // Sort by severity (critical first) then by time (newest first)
  const sortedIncidents = [...incidents].sort((a, b) => {
    const severityOrder = { critical: 0, major: 1, minor: 2, unknown: 3 };
    const sevDiff = severityOrder[a.severity] - severityOrder[b.severity];
    if (sevDiff !== 0) return sevDiff;
    return new Date(b.reported_at).getTime() - new Date(a.reported_at).getTime();
  });

  return (
    <div className="divide-y divide-eros-border">
      {sortedIncidents.map((incident) => {
        const config = severityConfig[incident.severity];
        const Icon = config.icon;
        
        return (
          <div
            key={incident.id}
            className={clsx(
              'p-3 hover:bg-eros-card-hover cursor-pointer transition-colors',
              incident.severity === 'critical' && incident.status === 'pending' && 'incident-pulse'
            )}
            onClick={() => onIncidentClick(incident)}
          >
            <div className="flex items-start gap-3">
              {/* Severity icon */}
              <div className={clsx(
                'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
                config.bg
              )}>
                <Icon className={clsx('w-4 h-4', config.color)} />
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={clsx(
                    'text-[10px] font-bold px-1.5 py-0.5 rounded',
                    config.bg, config.color, config.border, 'border'
                  )}>
                    {config.label}
                  </span>
                  <span className="text-xs text-eros-text-dim">
                    #{incident.id}
                  </span>
                </div>
                
                <p className="text-sm text-eros-text line-clamp-2 mb-1">
                  {incident.description}
                </p>
                
                <div className="flex items-center gap-3 text-xs text-eros-text-muted">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDistanceToNow(new Date(incident.reported_at), { addSuffix: true })}
                  </span>
                  <span className="text-eros-text-dim">•</span>
                  <span className={clsx(
                    incident.status === 'pending' && 'text-eros-major',
                    incident.status === 'dispatched' && 'text-eros-primary',
                    incident.status === 'on_scene' && 'text-eros-major',
                    incident.status === 'transporting' && 'text-purple-400'
                  )}>
                    {statusLabels[incident.status]}
                  </span>
                </div>
                
                {incident.address && (
                  <button
                    className="flex items-center gap-1 text-xs text-eros-text-dim hover:text-eros-primary mt-1"
                    onClick={(e) => {
                      e.stopPropagation();
                      onFocusOnMap(incident.latitude, incident.longitude);
                    }}
                  >
                    <MapPin className="w-3 h-3" />
                    <span className="truncate max-w-[200px]">{incident.address}</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
