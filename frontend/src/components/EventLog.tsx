/**
 * EventLog Component
 * 
 * Real-time feed of system events and status updates.
 */

import { formatDistanceToNow } from 'date-fns';
import { 
  Info, 
  AlertTriangle, 
  Bell, 
  ArrowRight, 
  Radio,
  Activity 
} from 'lucide-react';
import type { StatusUpdate } from '../types';
import clsx from 'clsx';

interface EventLogProps {
  updates: StatusUpdate[];
}

const typeConfig: Record<string, { icon: typeof Info; color: string }> = {
  system: { icon: Activity, color: 'text-eros-text-dim' },
  info: { icon: Info, color: 'text-eros-primary' },
  dispatch: { icon: ArrowRight, color: 'text-eros-dispatched' },
  arrival: { icon: Radio, color: 'text-eros-major' },
  alert: { icon: AlertTriangle, color: 'text-eros-critical' },
};

export default function EventLog({ updates }: EventLogProps) {
  if (updates.length === 0) {
    return (
      <div className="p-4 text-center text-eros-text-muted">
        <Bell className="w-6 h-6 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No recent events</p>
      </div>
    );
  }

  return (
    <div className="p-2 space-y-1">
      {updates.map((update) => {
        const config = typeConfig[update.update_type] || typeConfig.info;
        const Icon = config.icon;
        
        return (
          <div
            key={update.id}
            className="flex items-start gap-2 p-1.5 rounded hover:bg-eros-card-hover/50"
          >
            <Icon className={clsx('w-3 h-3 mt-0.5 flex-shrink-0', config.color)} />
            
            <div className="flex-1 min-w-0">
              <p className="text-xs text-eros-text-muted line-clamp-2">
                {update.message}
              </p>
            </div>
            
            <span className="text-[10px] text-eros-text-dim whitespace-nowrap">
              {formatDistanceToNow(new Date(update.created_at), { addSuffix: true })}
            </span>
          </div>
        );
      })}
    </div>
  );
}
