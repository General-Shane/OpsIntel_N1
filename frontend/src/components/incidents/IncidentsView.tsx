import React, { useEffect, useState } from 'react';
import { AlertTriangle, Download, RefreshCw, GitCommit, Sparkles } from 'lucide-react';
import apiClient from '../../api/client';
import { downloadCSV } from '../../utils/export';
import { formatDateLocal } from '../../utils/date';

export const IncidentsView: React.FC = () => {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [kpis, setKpis] = useState<any>(null);
  const [correlations, setCorrelations] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [rcaModal, setRcaModal] = useState<{
    isOpen: boolean;
    incidentId: string | null;
    content: string | null;
    loading: boolean;
  }>({ isOpen: false, incidentId: null, content: null, loading: false });

  const fetchData = () => {
    setLoading(true);
    Promise.allSettled([
      apiClient.get('/analytics/raw/incidents?limit=250'),
      apiClient.get('/analytics/kpis'),
      apiClient.get('/analytics/correlation?hours=24')
    ]).then((results) => {
      const [incRes, kpiRes, corrRes] = results;

      if (incRes.status === 'fulfilled') setIncidents(incRes.value.data);
      if (kpiRes.status === 'fulfilled') setKpis(kpiRes.value.data);
      
      const corrMap: Record<string, any> = {};
      if (corrRes.status === 'fulfilled' && corrRes.value.data) {
        corrRes.value.data.forEach((c: any) => {
          corrMap[c.incident_id] = c;
        });
      }
      setCorrelations(corrMap);
      setLoading(false);
    }).catch(err => {
      console.error("Failed loading incidents", err);
      setLoading(false);
    });
  };

  const handleGenerateRca = async (inc: any) => {
    setRcaModal({ isOpen: true, incidentId: inc.id, content: null, loading: true });
    try {
      const res = await apiClient.post('/ai/rca', {
        incident_id: inc.id,
        incident_title: inc.title,
        incident_priority: inc.priority,
        incident_service: inc.service,
        incident_created: inc.created
      });
      setRcaModal(prev => ({ ...prev, content: res.data.markdown_content, loading: false }));
    } catch (err) {
      console.error("RCA generation failed", err);
      setRcaModal(prev => ({ ...prev, content: "Failed to generate RCA. Please try again.", loading: false }));
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleExport = () => {
    downloadCSV(incidents, 'incidents_export');
  };

  const getPriorityBadgeClass = (priority: string) => {
    if (priority === 'P1' || priority === 'Critical') return 'badge-critical';
    if (priority === 'P2' || priority === 'High') return 'badge-warning';
    if (priority === 'P3' || priority === 'Medium') return 'badge-info';
    return 'badge-healthy';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <AlertTriangle color="var(--status-critical)" size={24} />
            <h1 className="page-title" style={{ margin: 0 }}>Incident Management & Resolution</h1>
          </div>
          <p className="page-subtitle">
            Track, prioritize, correlate changes, and resolve operational incidents
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={fetchData} disabled={loading} className="btn-cg-secondary">
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
            <span>{loading ? "Loading..." : "Refresh"}</span>
          </button>
          <button onClick={handleExport} className="btn-cg-primary">
            <Download size={15} />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Total Incidents</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.35rem 0' }}>{kpis?.incidents?.total_incidents || 0}</div>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Open Incidents</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-warning)', margin: '0.35rem 0' }}>{kpis?.incidents?.open_incidents || 0}</div>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>P1 Critical</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-critical)', margin: '0.35rem 0' }}>{kpis?.incidents?.p1_incidents || 0}</div>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Avg MTTR</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-healthy)', margin: '0.35rem 0' }}>{kpis?.incidents?.mttr_hours || 0} h</div>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="card" style={{ overflowX: 'auto', padding: 0 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--cg-border)', color: 'var(--text-secondary)', backgroundColor: 'var(--cg-surface-secondary)' }}>
              <th style={{ padding: '0.85rem 1.25rem' }}>Incident ID</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Title</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Priority</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Status</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Service</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Created At</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map(inc => (
              <tr key={inc.id} style={{ borderBottom: '1px solid #F0F4F7' }}>
                <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: 'var(--cg-blue-primary)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <span>{inc.id}</span>
                    {correlations[inc.id] && (
                      <span title={`Correlated with ${correlations[inc.id].change_id} (Diff: ${correlations[inc.id].time_diff_hours}h)`} className="badge badge-warning" style={{ fontSize: '0.65rem', width: 'fit-content' }}>
                        <GitCommit size={10} />
                        {correlations[inc.id].change_id}
                      </span>
                    )}
                  </div>
                </td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-primary)', fontWeight: 500 }}>{inc.title}</td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  <span className={`badge ${getPriorityBadgeClass(inc.priority)}`}>
                    {inc.priority}
                  </span>
                </td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-secondary)' }}>{inc.status}</td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-primary)' }}>{inc.service}</td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-muted)' }}>{formatDateLocal(inc.created)}</td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  {(inc.priority === 'P1' || inc.priority === 'P2' || inc.priority === 'Critical' || inc.priority === 'High') && (
                    <button 
                      onClick={() => handleGenerateRca(inc)}
                      className="btn-cg-primary"
                      style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                    >
                      <Sparkles size={12} />
                      <span>AI RCA</span>
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* RCA Modal */}
      {rcaModal.isOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(0, 0, 0, 0.4)',
          backdropFilter: 'blur(3px)',
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'var(--cg-surface-elevated)',
            border: '1px solid var(--cg-border)',
            borderRadius: '10px',
            boxShadow: '0 20px 50px rgba(0,0,0,0.15)',
            width: '100%',
            maxWidth: '750px',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            <div style={{
              padding: '1rem 1.25rem',
              borderBottom: '1px solid var(--cg-border)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: 'var(--cg-surface-secondary)'
            }}>
              <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle color="var(--status-warning)" size={18} />
                Root Cause Analysis: {rcaModal.incidentId}
              </h2>
              <button 
                onClick={() => setRcaModal({ isOpen: false, incidentId: null, content: null, loading: false })}
                style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.1rem' }}
              >
                ✕
              </button>
            </div>
            
            <div style={{ padding: '1.5rem', overflowY: 'auto', color: 'var(--text-primary)', fontSize: '0.875rem', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
              {rcaModal.loading ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 0', gap: '1rem' }}>
                  <RefreshCw className="animate-spin" size={28} color="var(--cg-blue-primary)" />
                  <p style={{ color: 'var(--text-muted)' }}>Generating SRE-level Root Cause Analysis...</p>
                </div>
              ) : (
                <div style={{ color: 'var(--text-primary)' }}>
                  {rcaModal.content?.replace(/\*\*/g, '')}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
