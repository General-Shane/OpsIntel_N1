import React, { useEffect, useState } from 'react';
import apiClient from '../../api/client';
import { Activity, Search, RefreshCw } from 'lucide-react';

export const ServiceHealthView: React.FC = () => {
  const [services, setServices] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);

  const fetchServices = () => {
    setLoading(true);
    apiClient.get('/analytics/services')
      .then(res => {
        setServices(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed loading service health data", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchServices();
  }, []);

  const filteredServices = services.filter(svc => {
    const matchFilter = filter === 'ALL' || svc.health_status === filter;
    const matchSearch = svc.service_name.toLowerCase().includes(search.toLowerCase()) ||
                        svc.service_id.toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  const totalServices = services.length;
  const healthyCount = services.filter(s => s.health_status === 'HEALTHY').length;
  const warningCount = services.filter(s => s.health_status === 'WARNING').length;
  const criticalCount = services.filter(s => s.health_status === 'CRITICAL').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Activity color="var(--cg-blue-primary)" size={24} />
            <h1 className="page-title" style={{ margin: 0 }}>Service Health & Infrastructure Catalog</h1>
          </div>
          <p className="page-subtitle">
            Fleet availability • Service criticality tiers • Error budget monitoring • MTTR telemetry
          </p>
        </div>

        <button onClick={fetchServices} disabled={loading} className="btn-cg-secondary">
          <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          <span>{loading ? "Loading..." : "Refresh Status"}</span>
        </button>
      </div>

      {/* KPI Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Monitored Services</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.35rem 0' }}>{totalServices}</div>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Core production catalog</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Healthy Tier</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-healthy)', margin: '0.35rem 0' }}>{healthyCount}</div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-healthy)' }}>● Operating normally</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Degraded / Warning</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-warning)', margin: '0.35rem 0' }}>{warningCount}</div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-warning)' }}>SLA threshold watch</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Critical Health State</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: criticalCount > 0 ? 'var(--status-critical)' : 'var(--text-primary)', margin: '0.35rem 0' }}>{criticalCount}</div>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Priority remediation</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        padding: '0.75rem 1rem',
        backgroundColor: 'var(--cg-surface-card)',
        border: '1px solid var(--cg-border)',
        borderRadius: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: '220px' }}>
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search service name or ID..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              width: '100%',
              backgroundColor: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.825rem',
              outline: 'none'
            }}
          />
        </div>

        <div className="tab-container">
          {['ALL', 'HEALTHY', 'WARNING', 'CRITICAL'].map((st) => (
            <button
              key={st}
              onClick={() => setFilter(st)}
              className={`tab-button ${filter === st ? 'active' : ''}`}
              style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Services Fleet Table */}
      <div className="card" style={{ overflowX: 'auto', padding: 0 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--cg-border)', color: 'var(--text-secondary)', backgroundColor: 'var(--cg-surface-secondary)' }}>
              <th style={{ padding: '0.85rem 1.25rem' }}>Service ID</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Service Name</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Criticality</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Health Status</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Total Incidents</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Open Incidents</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Open Problems</th>
            </tr>
          </thead>
          <tbody>
            {filteredServices.map(svc => {
              const m = svc.metrics || {};
              return (
                <tr key={svc.service_id} style={{ borderBottom: '1px solid #F0F4F7' }}>
                  <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: 'var(--cg-blue-primary)' }}>{svc.service_id}</td>
                  <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-primary)', fontWeight: 600 }}>{svc.service_name}</td>
                  <td style={{ padding: '0.85rem 1.25rem' }}>
                    <span className={`badge ${svc.criticality === 'HIGH' ? 'badge-critical' : svc.criticality === 'MEDIUM' ? 'badge-warning' : 'badge-info'}`}>
                      {svc.criticality}
                    </span>
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem' }}>
                    <span className={`badge ${svc.health_status === 'HEALTHY' ? 'badge-healthy' : svc.health_status === 'WARNING' ? 'badge-warning' : 'badge-critical'}`}>
                      {svc.health_status}
                    </span>
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-primary)' }}>{m.total_incidents || 0}</td>
                  <td style={{ padding: '0.85rem 1.25rem', color: (m.open_incidents || 0) > 0 ? 'var(--status-warning)' : 'var(--text-secondary)', fontWeight: 600 }}>{m.open_incidents || 0}</td>
                  <td style={{ padding: '0.85rem 1.25rem', color: (m.open_problems || 0) > 0 ? 'var(--status-critical)' : 'var(--text-secondary)', fontWeight: 600 }}>{m.open_problems || 0}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

    </div>
  );
};
