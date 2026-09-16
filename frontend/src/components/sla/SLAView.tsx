import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip
} from 'recharts';
import { BarChart3, Search, Download, RefreshCw } from 'lucide-react';
import apiClient from '../../api/client';
import { downloadCSV } from '../../utils/export';

export const SLAView: React.FC = () => {
  const [filter, setFilter] = useState<'ALL' | 'BREACHED' | 'COMPLIANT'>('ALL');
  const [search, setSearch] = useState('');
  const [slas, setSlas] = useState<any[]>([]);
  const [kpis, setKpis] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      apiClient.get('/analytics/raw/slas?limit=250'),
      apiClient.get('/analytics/kpis'),
      apiClient.get('/analytics/trends?days=7')
    ]).then(([slaRes, kpiRes, trendRes]) => {
      setSlas(slaRes.data);
      setKpis(kpiRes.data);
      setTrends(trendRes.data);
      setLoading(false);
    }).catch(err => {
      console.error("Failed loading SLA data", err);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleExport = () => {
    downloadCSV(slas, 'sla_export');
  };

  const slaTrendData = trends.map(t => ({
    date: t.date,
    compliance: t.sla_compliance,
    target: 95.0
  }));

  const filteredServices = slas.filter(s => {
    const status = s.breached ? 'BREACHED' : 'COMPLIANT';
    const matchFilter = filter === 'ALL' || status === filter;
    const serviceName = (s.service || '').toLowerCase();
    const recordId = (s.id || '').toLowerCase();
    const matchSearch = serviceName.includes(search.toLowerCase()) || recordId.includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  const chartTooltipStyle = {
    backgroundColor: 'var(--chart-tooltip-bg)',
    borderColor: 'var(--chart-tooltip-border)',
    color: 'var(--text-primary)',
    borderRadius: '6px',
    boxShadow: 'var(--chart-tooltip-shadow)',
    fontSize: '12px'
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <BarChart3 color="var(--status-healthy)" size={24} />
            <h1 className="page-title" style={{ margin: 0 }}>SLA Compliance & Service Level Objectives</h1>
          </div>
          <p className="page-subtitle">
            Contractual SLA compliance • Breach distribution • Error budget consumption • Target threshold monitoring
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
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Overall SLA Compliance</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: (kpis?.slas?.compliance_rate_percent || 0) >= 95 ? 'var(--status-healthy)' : 'var(--status-warning)', margin: '0.35rem 0' }}>
            {kpis?.slas?.compliance_rate_percent || 0}%
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Baseline Target: 95.0%</span>
        </div>

        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Evaluated SLA Records</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.35rem 0' }}>{kpis?.slas?.total_slas || 0}</div>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Evaluated contracts</span>
        </div>

        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Breached SLA Contracts</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: (kpis?.slas?.breached_slas || 0) > 0 ? 'var(--status-critical)' : 'var(--text-primary)', margin: '0.35rem 0' }}>
            {kpis?.slas?.breached_slas || 0}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-critical)' }}>Requires triage</span>
        </div>

        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Governance State</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: (kpis?.slas?.compliance_rate_percent || 0) >= 95 ? 'var(--status-healthy)' : 'var(--status-warning)', margin: '0.35rem 0' }}>
            {(kpis?.slas?.compliance_rate_percent || 0) >= 95 ? 'Compliant' : 'Breach Risk'}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Threshold evaluation</span>
        </div>
      </div>

      {/* 7-Day Trend Card */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">7-Day SLA Compliance Trend vs 95% Target Baseline</h3>
          <span className="badge badge-info">Evaluation Window</span>
        </div>
        <div style={{ width: '100%', height: 210 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={slaTrendData}>
              <defs>
                <linearGradient id="slaColor" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--cg-blue-primary)" stopOpacity={0.25}/>
                  <stop offset="95%" stopColor="var(--cg-blue-primary)" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
              <YAxis domain={[0, 100]} stroke="var(--text-muted)" fontSize={11} tickLine={false} />
              <Tooltip contentStyle={chartTooltipStyle} />
              <Area type="monotone" dataKey="compliance" stroke="var(--cg-blue-primary)" strokeWidth={2.5} fillOpacity={1} fill="url(#slaColor)" />
            </AreaChart>
          </ResponsiveContainer>
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
            placeholder="Search SLA Record ID or Service..."
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
          {(['ALL', 'BREACHED', 'COMPLIANT'] as const).map((st) => (
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

      {/* SLA Records Table */}
      <div className="card" style={{ overflowX: 'auto', padding: 0 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--cg-border)', color: 'var(--text-secondary)', backgroundColor: 'var(--cg-surface-secondary)' }}>
              <th style={{ padding: '0.85rem 1.25rem' }}>SLA Record ID</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Service</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Target MTTR</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Actual MTTR</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Compliance Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredServices.slice(0, 50).map(s => (
              <tr key={s.id} style={{ borderBottom: '1px solid #F0F4F7' }}>
                <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: 'var(--cg-blue-primary)' }}>{s.id}</td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-primary)', fontWeight: 600 }}>{s.service}</td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-secondary)' }}>{s.target_hours} h</td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-primary)', fontWeight: 600 }}>{s.actual_hours} h</td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  <span className={`badge ${s.breached ? 'badge-critical' : 'badge-healthy'}`}>
                    {s.breached ? 'BREACHED' : 'COMPLIANT'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
};
