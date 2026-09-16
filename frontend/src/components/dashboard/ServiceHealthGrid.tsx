import React, { useEffect, useState } from 'react';
import apiClient from '../../api/client';
import { Server, AlertOctagon, AlertCircle, CheckCircle2, Search, X, BookOpen, Activity, AlertTriangle } from 'lucide-react';

export const ServiceHealthGrid: React.FC = () => {
  const [services, setServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [selectedService, setSelectedService] = useState<any | null>(null);

  useEffect(() => {
    apiClient.get('/analytics/services')
      .then(res => {
        setServices(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load service analytics", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="card loading-placeholder">Loading Service Health Grid...</div>;

  const filteredServices = services.filter(svc => {
    const matchesFilter = filter === 'ALL' || svc.health_status === filter;
    const matchesSearch = svc.service_name.toLowerCase().includes(search.toLowerCase()) ||
                          svc.service_id.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Search & Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {['ALL', 'CRITICAL', 'WARNING', 'HEALTHY'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              style={{
                padding: '0.4rem 0.85rem',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: filter === status ? '1px solid var(--accent-primary)' : '1px solid rgba(255, 255, 255, 0.1)',
                backgroundColor: filter === status ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                color: filter === status ? '#fff' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {status}
            </button>
          ))}
        </div>

        <div style={{ position: 'relative', minWidth: '240px' }}>
          <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
          <input
            type="text"
            placeholder="Search service name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem 0.75rem 0.5rem 2.25rem',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              backgroundColor: '#0f172a',
              color: '#fff',
              fontSize: '0.85rem',
              outline: 'none'
            }}
          />
        </div>
      </div>

      {/* Grid of Service Cards */}
      <div className="service-grid">
        {filteredServices.map(svc => {
          let statusClass = "status-healthy";
          let Icon = CheckCircle2;
          
          if (svc.health_status === "WARNING") {
            statusClass = "status-warning";
            Icon = AlertCircle;
          } else if (svc.health_status === "CRITICAL") {
            statusClass = "status-critical";
            Icon = AlertOctagon;
          }

          return (
            <div
              key={svc.service_id}
              onClick={() => setSelectedService(svc)}
              className={`card service-card border-${statusClass}`}
              style={{ cursor: 'pointer', transition: 'transform 0.2s ease, box-shadow 0.2s ease' }}
            >
              <div className="service-header">
                <div className="service-title">
                  <Server size={20} color="var(--accent-primary)" />
                  <h3>{svc.service_name}</h3>
                </div>
                <div className={`status-badge bg-${statusClass}`}>
                  <Icon size={14} />
                  {svc.health_status}
                </div>
              </div>

              <div style={{ marginBottom: '0.75rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                ID: {svc.service_id} | Criticality: <strong style={{ color: '#fff' }}>{svc.criticality}</strong>
              </div>
              
              <div className="service-metrics">
                <div className="metric-col">
                  <span className="metric-label">Active P1s</span>
                  <span className={`metric-val ${svc.metrics.p1_incidents_active > 0 ? 'text-red' : ''}`}>
                    {svc.metrics.p1_incidents_active}
                  </span>
                </div>
                <div className="metric-col">
                  <span className="metric-label">Open Incidents</span>
                  <span className="metric-val">{svc.metrics.open_incidents}</span>
                </div>
                <div className="metric-col">
                  <span className="metric-label">Open Problems</span>
                  <span className="metric-val">{svc.metrics.open_problems}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Service Detail Triage Modal */}
      {selectedService && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000,
          padding: '2rem'
        }}>
          <div className="card" style={{
            width: '100%',
            maxWidth: '650px',
            backgroundColor: '#0f172a',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '12px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
            padding: '2rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Server size={28} color="var(--accent-primary)" />
                <div>
                  <h2 style={{ fontSize: '1.3rem', fontWeight: 700 }}>{selectedService.service_name}</h2>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>ID: {selectedService.service_id} | Criticality: {selectedService.criticality}</span>
                </div>
              </div>
              <button onClick={() => setSelectedService(null)} className="btn-icon">
                <X size={22} />
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
              <div className="card" style={{ padding: '1rem', backgroundColor: 'rgba(255,255,255,0.03)', textAlign: 'center' }}>
                <Activity size={20} color="var(--accent-primary)" style={{ margin: '0 auto 0.25rem' }} />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total Incidents</span>
                <h4 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{selectedService.metrics.total_incidents}</h4>
              </div>
              <div className="card" style={{ padding: '1rem', backgroundColor: 'rgba(255,255,255,0.03)', textAlign: 'center' }}>
                <AlertTriangle size={20} color="var(--status-critical)" style={{ margin: '0 auto 0.25rem' }} />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Active P1s</span>
                <h4 style={{ fontSize: '1.25rem', fontWeight: 700, color: selectedService.metrics.p1_incidents_active > 0 ? 'var(--status-critical)' : '#fff' }}>
                  {selectedService.metrics.p1_incidents_active}
                </h4>
              </div>
              <div className="card" style={{ padding: '1rem', backgroundColor: 'rgba(255,255,255,0.03)', textAlign: 'center' }}>
                <AlertCircle size={20} color="var(--status-warning)" style={{ margin: '0 auto 0.25rem' }} />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Open Problems</span>
                <h4 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{selectedService.metrics.open_problems}</h4>
              </div>
            </div>

            <div style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '1rem', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <BookOpen size={24} color="var(--accent-primary)" />
              <div>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--accent-primary)' }}>Recommended Obsidian Runbook</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Linked Knowledge Vault: <code>knowledge/runbooks/[[{selectedService.service_name}]].md</code>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
