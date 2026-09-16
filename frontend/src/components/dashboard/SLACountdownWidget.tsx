import React, { useEffect, useState } from 'react';
import { Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';
import apiClient from '../../api/client';

interface OpenIncident {
  id: string;
  incident_id?: string;
  service: string;
  service_id?: string;
  priority: string;
  created: string;
  created_at?: string;
}

export const SLACountdownWidget: React.FC = () => {
  const [incidents, setIncidents] = useState<OpenIncident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOpenIncidents = async () => {
      try {
        const response = await apiClient.get('/analytics/raw/incidents?limit=50');
        const openCritical = response.data.filter(
          (inc: any) => inc.status === 'OPEN' && (
            inc.priority === 'P1' || 
            inc.priority === 'P2' || 
            inc.priority === 'Critical' || 
            inc.priority === 'High'
          )
        );
        setIncidents(openCritical.slice(0, 4));
      } catch (err) {
        console.error("Failed to load SLA countdown data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchOpenIncidents();
  }, []);

  if (loading) {
    return <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>Loading SLA Status...</div>;
  }

  if (incidents.length === 0) {
    return (
      <div className="card" style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '1.5rem', backgroundColor: 'var(--status-healthy-bg)', border: '1px solid var(--status-healthy-border)' }}>
        <CheckCircle2 size={36} color="var(--status-healthy)" style={{ marginBottom: '0.75rem' }} />
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 0.25rem 0' }}>Zero Critical Breaches</h3>
        <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', margin: 0 }}>All P1/P2 critical incidents are within compliance window.</p>
      </div>
    );
  }

  const SLA_TARGETS: Record<string, number> = {
    P1: 4 * 60 * 60 * 1000,
    Critical: 4 * 60 * 60 * 1000,
    P2: 8 * 60 * 60 * 1000,
    High: 8 * 60 * 60 * 1000,
  };

  const calculateSlaStatus = (inc: OpenIncident) => {
    const rawDate = inc.created || inc.created_at || new Date().toISOString();
    const created = new Date(rawDate).getTime();
    const now = new Date().getTime();
    const elapsed = now - created;
    const target = SLA_TARGETS[inc.priority] || (8 * 60 * 60 * 1000);
    
    const remaining = target - elapsed;
    const percentConsumed = (elapsed / target) * 100;
    
    let statusColor = 'var(--status-healthy)';
    let bgColor = 'var(--status-healthy-bg)';
    let borderColor = 'var(--status-healthy-border)';
    
    if (percentConsumed >= 100) {
      statusColor = 'var(--status-critical)';
      bgColor = 'var(--status-critical-bg)';
      borderColor = 'var(--status-critical-border)';
    } else if (percentConsumed >= 80) {
      statusColor = 'var(--status-warning)';
      bgColor = 'var(--status-warning-bg)';
      borderColor = 'var(--status-warning-border)';
    }

    const absRemaining = Math.abs(remaining);
    const hours = Math.floor(absRemaining / (1000 * 60 * 60));
    const mins = Math.floor((absRemaining % (1000 * 60 * 60)) / (1000 * 60));
    const timeStr = `${hours}h ${mins}m`;
    const label = remaining < 0 ? `Breached by ${timeStr}` : `${timeStr} left`;

    return { label, statusColor, bgColor, borderColor, percentConsumed };
  };

  return (
    <div className="card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Clock size={16} color="var(--cg-blue-primary)" />
          <h3 className="card-title">Active SLA Resolution Watch</h3>
        </div>
        <span className="badge badge-critical">P1 / P2 Target</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', flex: 1, overflowY: 'auto' }}>
        {incidents.map(inc => {
          const { label, statusColor, bgColor, borderColor, percentConsumed } = calculateSlaStatus(inc);
          const incId = inc.id || inc.incident_id;
          const serviceName = inc.service || inc.service_id;
          return (
            <div key={incId} style={{
              padding: '0.65rem 0.85rem',
              borderRadius: '8px',
              backgroundColor: bgColor,
              border: `1px solid ${borderColor}`,
              display: 'flex',
              flexDirection: 'column',
              gap: '0.35rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '4px', backgroundColor: '#FFFFFF', border: '1px solid var(--cg-border)', color: 'var(--text-primary)' }}>
                    {incId}
                  </span>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: (inc.priority === 'P1' || inc.priority === 'Critical') ? 'var(--status-critical)' : 'var(--status-warning)' }}>
                    {inc.priority}
                  </span>
                  <span style={{ fontSize: '0.775rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {serviceName}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: statusColor, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  {percentConsumed >= 100 && <AlertTriangle size={13} />}
                  <span>{label}</span>
                </div>
              </div>
              
              {/* Progress Bar */}
              <div style={{ width: '100%', height: '4px', backgroundColor: 'rgba(0,0,0,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                <div 
                  style={{
                    width: `${Math.min(percentConsumed, 100)}%`,
                    height: '100%',
                    backgroundColor: percentConsumed >= 100 ? 'var(--status-critical)' : percentConsumed >= 80 ? 'var(--status-warning)' : 'var(--status-healthy)',
                    borderRadius: '2px',
                    transition: 'width 0.6s ease'
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
