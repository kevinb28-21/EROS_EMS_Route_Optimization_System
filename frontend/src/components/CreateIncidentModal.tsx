/**
 * CreateIncidentModal Component
 * 
 * Modal form for creating new incidents.
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, MapPin, AlertTriangle } from 'lucide-react';
import { incidentsApi } from '../api/client';
import type { Incident, IncidentSeverity } from '../types';

interface CreateIncidentModalProps {
  onClose: () => void;
  onCreated: (incident: Incident) => void;
}

// Default location: downtown Toronto
const DEFAULT_LAT = 43.6532;
const DEFAULT_LNG = -79.3832;

export default function CreateIncidentModal({
  onClose,
  onCreated,
}: CreateIncidentModalProps) {
  const queryClient = useQueryClient();
  
  const [formData, setFormData] = useState({
    description: '',
    severity: 'unknown' as IncidentSeverity,
    latitude: DEFAULT_LAT,
    longitude: DEFAULT_LNG,
    address: '',
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});

  const createMutation = useMutation({
    mutationFn: () => incidentsApi.create(formData),
    onSuccess: (incident) => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      queryClient.invalidateQueries({ queryKey: ['statusUpdates'] });
      onCreated(incident);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate
    const newErrors: Record<string, string> = {};
    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }
    if (formData.latitude < -90 || formData.latitude > 90) {
      newErrors.latitude = 'Invalid latitude';
    }
    if (formData.longitude < -180 || formData.longitude > 180) {
      newErrors.longitude = 'Invalid longitude';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    createMutation.mutate();
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4" style={{ zIndex: 9999 }}>
      <div className="bg-eros-card rounded-xl border border-eros-border w-full max-w-lg shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-eros-border">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-eros-critical" />
            <h2 className="text-lg font-semibold">Report New Incident</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-eros-card-hover rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Description */}
          <div>
            <label className="block text-sm font-medium mb-1.5">
              Description <span className="text-eros-critical">*</span>
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe the emergency situation..."
              rows={3}
              className={`input ${errors.description ? 'border-eros-critical' : ''}`}
            />
            {errors.description && (
              <p className="text-xs text-eros-critical mt-1">{errors.description}</p>
            )}
          </div>
          
          {/* Severity */}
          <div>
            <label className="block text-sm font-medium mb-1.5">Severity</label>
            <div className="grid grid-cols-4 gap-2">
              {(['critical', 'major', 'minor', 'unknown'] as IncidentSeverity[]).map((severity) => (
                <button
                  key={severity}
                  type="button"
                  onClick={() => setFormData({ ...formData, severity })}
                  className={`
                    py-2 px-3 rounded-lg text-sm font-medium capitalize transition-all
                    border
                    ${formData.severity === severity
                      ? severity === 'critical' ? 'bg-eros-critical/20 border-eros-critical text-eros-critical'
                      : severity === 'major' ? 'bg-eros-major/20 border-eros-major text-eros-major'
                      : severity === 'minor' ? 'bg-eros-minor/20 border-eros-minor text-eros-minor'
                      : 'bg-eros-text-dim/20 border-eros-text-dim text-eros-text-dim'
                      : 'bg-eros-darker border-eros-border hover:border-eros-text-dim'
                    }
                  `}
                >
                  {severity}
                </button>
              ))}
            </div>
          </div>
          
          {/* Location */}
          <div>
            <label className="block text-sm font-medium mb-1.5">
              <MapPin className="w-4 h-4 inline mr-1" />
              Location
            </label>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <input
                  type="number"
                  step="any"
                  value={formData.latitude}
                  onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) || 0 })}
                  placeholder="Latitude"
                  className={`input ${errors.latitude ? 'border-eros-critical' : ''}`}
                />
                {errors.latitude && (
                  <p className="text-xs text-eros-critical mt-1">{errors.latitude}</p>
                )}
              </div>
              <div>
                <input
                  type="number"
                  step="any"
                  value={formData.longitude}
                  onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) || 0 })}
                  placeholder="Longitude"
                  className={`input ${errors.longitude ? 'border-eros-critical' : ''}`}
                />
                {errors.longitude && (
                  <p className="text-xs text-eros-critical mt-1">{errors.longitude}</p>
                )}
              </div>
            </div>
            <p className="text-xs text-eros-text-dim mt-1">
              Tip: Use coordinates within downtown Toronto (43.64-43.68, -79.42--79.36)
            </p>
          </div>
          
          {/* Address */}
          <div>
            <label className="block text-sm font-medium mb-1.5">
              Address (optional)
            </label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              placeholder="e.g., 100 Queen St W, Toronto"
              className="input"
            />
          </div>
          
          {/* Error message */}
          {createMutation.isError && (
            <div className="p-3 bg-eros-critical/10 border border-eros-critical/30 rounded-lg">
              <p className="text-sm text-eros-critical">
                Failed to create incident. Please try again.
              </p>
            </div>
          )}
          
          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="btn btn-danger flex-1"
            >
              {createMutation.isPending ? 'Creating...' : 'Report Incident'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
