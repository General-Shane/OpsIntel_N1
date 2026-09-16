import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';
import { GitCommit, Download, RefreshCw } from 'lucide-react';
import apiClient from '../../api/client';

import { downloadCSV } from '../../utils/export';
import { formatDateLocal } from '../../utils/date';

export const ChangesView: React.FC = () => {
  const [changes, setChanges] = useState<any[]>([]);
  const [kpis, setKpis] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      apiClient.get('/analytics/raw/changes?limit=250'),
      apiClient.get('/analytics/kpis')
    ]).then(([chgRes, kpiRes]) => {
      setChanges(chgRes.data);
      setKpis(kpiRes.data);
      setLoading(false);
    }).catch(err => {
      console.error("Failed loading changes", err);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleExport = () => {
    downloadCSV(changes, 'changes_export');
  };

  const changeTypeData = (() => {
    const counts = changes.reduce((acc: Record<string, number>, c: any) => {
      const t = (c.type || '').toLowerCase();
      acc[t] = (acc[t] || 0) + 1;
      return acc;
    }, {});
    const colorMap: Record<string, string> = {
      normal: 'var(--cg-blue-primary)',
      standard: 'var(--status-healthy)',
      emergency: 'var(--status-critical)',
      major: 'var(--status-warning)',
      minor: 'var(--cg-cyan-accent)'
    };
    return Object.entries(counts).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value,
      color: colorMap[name] || '#64748b'
    })).filter(d => d.value > 0);
  })();

  const changeTrendData = (() => {
    const buckets: Record<string, number> = {};
    changes.forEach((c: any) => {
      if (!c.created) return;
      const d = new Date(c.created);
      if (isNaN(d.getTime())) return;
      const label = d.toLocaleDateString([], { month: 'short', day: 'numeric' });
      buckets[label] = (buckets[label] || 0) + 1;
    });
    return Object.entries(buckets).slice(-7).map(([date, count]) => ({ date, changes: count }));
  })();

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
      
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <GitCommit color="var(--cg-blue-primary)" size={24} />
            <h1 className="page-title" style={{ margin: 0 }}>Change Management & Release Governance</h1>
          </div>
          <p className="page-subtitle">
            Deployment tracking • Risk evaluation • Release success rate • Change failure telemetry
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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Total Changes</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.35rem 0' }}>{kpis?.changes?.total_changes || 0}</div>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Historical executions</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Successful Changes</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-healthy)', margin: '0.35rem 0' }}>{kpis?.changes?.successful_changes || 0}</div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-healthy)' }}>● Passed verification</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Failed / Rollbacks</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: (kpis?.changes?.failed_changes || 0) > 0 ? 'var(--status-critical)' : 'var(--text-primary)', margin: '0.35rem 0' }}>
            {kpis?.changes?.failed_changes ?? 0}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Rollbacks recorded</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Success Rate</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--cg-blue-primary)', margin: '0.35rem 0' }}>{kpis?.changes?.success_rate_percent || 0}%</div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-healthy)' }}>Target: &gt; 95.0%</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Emergency Changes</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-warning)', margin: '0.35rem 0' }}>
            {changes.filter((c: any) => (c.type || '').toLowerCase() === 'emergency').length}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-warning)' }}>Expedited releases</span>
        </div>
      </div>

      {/* Visual Analytics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Change Requests by Type</h3>
            <span className="badge badge-info">Classification</span>
          </div>
          <div style={{ width: '100%', height: 210 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={changeTypeData} cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={4} dataKey="value">
                  {changeTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={chartTooltipStyle} />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">7-Day Change Velocity</h3>
            <span className="badge badge-healthy">Throughput</span>
          </div>
          <div style={{ width: '100%', height: 210 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={changeTrendData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Line type="monotone" dataKey="changes" stroke="var(--cg-blue-primary)" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Changes Registry Table */}
      <div className="card" style={{ overflowX: 'auto', padding: 0 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--cg-border)', color: 'var(--text-secondary)', backgroundColor: 'var(--cg-surface-secondary)' }}>
              <th style={{ padding: '0.85rem 1.25rem' }}>Change ID</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Service</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Type</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Status</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Risk Level</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Completed Date</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Rollback</th>
            </tr>
          </thead>
          <tbody>
            {changes.slice(0, 50).map(c => (
              <tr key={c.id} style={{ borderBottom: '1px solid #F0F4F7' }}>
                <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: 'var(--cg-blue-primary)' }}>{c.id}</td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-primary)', fontWeight: 500 }}>{c.service}</td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  <span className="badge badge-info">{c.type}</span>
                </td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-secondary)' }}>{c.status}</td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  <span className={`badge ${c.risk === 'High' ? 'badge-critical' : c.risk === 'Medium' ? 'badge-warning' : 'badge-healthy'}`}>
                    {c.risk}
                  </span>
                </td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-muted)' }}>{formatDateLocal(c.completed_at || c.created)}</td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  {c.rollback_required ? (
                    <span className="badge badge-critical">Yes</span>
                  ) : (
                    <span className="badge badge-healthy">No</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
};
