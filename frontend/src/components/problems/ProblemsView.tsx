import React, { useEffect, useState } from 'react';
import {
  Target,
  Download,
  RefreshCw,
  Search,
  AlertTriangle,
  Clock,
  Layers,
  Sparkles,
  ChevronRight,
  X,
  CheckCircle2,
  Activity,
  ShieldCheck
} from 'lucide-react';
import apiClient from '../../api/client';
import { downloadCSV } from '../../utils/export';
import { formatDateLocal } from '../../utils/date';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  CartesianGrid
} from 'recharts';

interface ProblemItem {
  id: string;
  title: string;
  status: string;
  priority: string;
  raw_priority?: string;
  service: string;
  root_cause_category?: string;
  age_days: number;
  created: string;
}

interface ProblemDetail {
  problem_id: string;
  title: string;
  service_id: string;
  service_name: string;
  status: string;
  priority: string;
  age_days: number;
  created_at: string;
  resolved_at: string | null;
  root_cause_category: string;
  confidence: string;
  related_incidents_count: number;
  related_incidents: Array<{
    incident_id: string;
    priority: string;
    status: string;
    resolution_time_hours: number | null;
    created_at: string;
  }>;
  recommended_actions: string[];
  operational_impact: string;
}

export const ProblemsView: React.FC = () => {
  const [problems, setProblems] = useState<ProblemItem[]>([]);
  const [summaryData, setSummaryData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  // Search and Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [serviceFilter, setServiceFilter] = useState('ALL');

  // Detail Drawer State
  const [selectedProblemId, setSelectedProblemId] = useState<string | null>(null);
  const [problemDetail, setProblemDetail] = useState<ProblemDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchData = () => {
    setLoading(true);
    Promise.allSettled([
      apiClient.get('/analytics/raw/problems?limit=300'),
      apiClient.get('/analytics/problems/summary')
    ]).then((results) => {
      const [rawRes, summaryRes] = results;
      if (rawRes.status === 'fulfilled') {
        setProblems(rawRes.value.data);
      }
      if (summaryRes.status === 'fulfilled') {
        setSummaryData(summaryRes.value.data);
      }
      setLoading(false);
    }).catch(err => {
      console.error("Failed loading problems data", err);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenDetail = async (problemId: string) => {
    setSelectedProblemId(problemId);
    setDetailLoading(true);
    try {
      const res = await apiClient.get(`/analytics/problems/${problemId}`);
      setProblemDetail(res.data);
    } catch (err) {
      console.error("Failed loading problem detail", err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedProblemId(null);
    setProblemDetail(null);
  };

  const handleExport = () => {
    downloadCSV(problems, 'problem_management_export');
  };

  const filteredProblems = problems.filter(prb => {
    const matchesSearch = 
      prb.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prb.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prb.service.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'ALL' || prb.status.toUpperCase() === statusFilter;
    const matchesPriority = priorityFilter === 'ALL' || prb.priority.toUpperCase() === priorityFilter.toUpperCase();
    const matchesService = serviceFilter === 'ALL' || prb.service === serviceFilter;

    return matchesSearch && matchesStatus && matchesPriority && matchesService;
  });

  const uniqueServices = Array.from(new Set(problems.map(p => p.service))).filter(Boolean);

  const summary = summaryData?.summary || {};
  const agingChartData = (summaryData?.aging_distribution || []).map((item: any) => ({
    range: item.range,
    count: item.count,
    fill: item.status === 'critical' ? 'var(--status-critical)' : item.status === 'warning' ? 'var(--status-warning)' : item.status === 'info' ? 'var(--cg-blue-primary)' : 'var(--cg-cyan-accent)'
  }));

  const rootCauses = summaryData?.root_cause_breakdown || [];

  const chartTooltipStyle = {
    backgroundColor: 'var(--chart-tooltip-bg)',
    borderColor: 'var(--chart-tooltip-border)',
    color: 'var(--text-primary)',
    borderRadius: '6px',
    boxShadow: 'var(--chart-tooltip-shadow)',
    fontSize: '12px'
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', position: 'relative' }}>
      
      {/* Header & Primary Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Target color="var(--status-warning)" size={24} />
            <h1 className="page-title" style={{ margin: 0 }}>Problem Management Intelligence</h1>
          </div>
          <p className="page-subtitle">
            Root-cause governance • Aging telemetry • Recurring incident clusters • Corrective action tracking
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={fetchData} disabled={loading} className="btn-cg-secondary">
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
            <span>{loading ? "Loading..." : "Refresh"}</span>
          </button>
          <button onClick={handleExport} className="btn-cg-primary">
            <Download size={15} />
            <span>Export Registry</span>
          </button>
        </div>
      </div>

      {/* Executive Problem Summary Row (4 Compact Cards) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem'
      }}>
        {/* Active Problem Backlog */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Open Problem Backlog</span>
            <Target size={16} color="var(--cg-blue-primary)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.35rem 0' }}>
            {summary.open_backlog || 0}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            <span style={{ color: 'var(--status-healthy)', fontWeight: 700 }}>{summary.resolved_problems || 0}</span> Resolved total
          </div>
        </div>

        {/* Critical & High Priority */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Critical & High Priority</span>
            <AlertTriangle size={16} color="var(--status-critical)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-critical)', margin: '0.35rem 0' }}>
            {summary.critical_high_count || 0}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            Active P1/P2 root-cause investigations
          </div>
        </div>

        {/* Stale Backlog (>60d) */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Stale Problems (&gt; 60d)</span>
            <Clock size={16} color="var(--status-warning)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: (summary.stale_problems_count || 0) > 0 ? 'var(--status-warning)' : 'var(--text-primary)', margin: '0.35rem 0' }}>
            {summary.stale_problems_count || 0}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            Avg age: <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{summary.average_age_days || 0} days</span>
          </div>
        </div>

        {/* Recurring Clusters */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Recurring Clusters</span>
            <Activity size={16} color="var(--cg-blue-primary)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--cg-blue-primary)', margin: '0.35rem 0' }}>
            {summary.recurring_clusters_count || 0}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            <span className="badge badge-info" style={{ fontSize: '0.6rem', padding: '0.1rem 0.35rem' }}>Analytics Derived</span>
          </div>
        </div>
      </div>

      {/* Problem Intelligence Visual Insights (Aging Buckets + Root Cause Categories) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {/* Aging Distribution */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Clock size={16} color="var(--cg-blue-primary)" />
              <h3 className="card-title">Problem Backlog Aging Distribution</h3>
            </div>
            <span className="badge badge-info">4-Tier Buckets</span>
          </div>
          <div style={{ width: '100%', height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={agingChartData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#EEF3F7" />
                <XAxis dataKey="range" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {agingChartData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Derived Root Cause Categories */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Layers size={16} color="var(--cg-blue-primary)" />
              <h3 className="card-title">Derived Root Cause Breakdown</h3>
            </div>
            <span className="badge badge-info">Hypothesis Mix</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', flex: 1, justifyContent: 'center' }}>
            {rootCauses.slice(0, 4).map((rc: any, idx: number) => (
              <div key={idx} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.45rem 0.65rem',
                borderRadius: '6px',
                backgroundColor: 'var(--cg-surface-secondary)',
                border: '1px solid var(--cg-border)'
              }}>
                <span style={{ fontSize: '0.775rem', color: 'var(--text-primary)', fontWeight: 500 }}>{rc.category}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--cg-blue-primary)' }}>{rc.count}</span>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>({rc.percentage}%)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filter and Search Toolbar */}
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
            placeholder="Search by Problem ID, Title, or Service..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
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

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            style={{
              backgroundColor: 'var(--cg-surface-secondary)',
              border: '1px solid var(--cg-border)',
              color: 'var(--text-primary)',
              borderRadius: '6px',
              padding: '0.35rem 0.65rem',
              fontSize: '0.775rem',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="RESOLVED">Resolved</option>
          </select>

          {/* Priority Filter */}
          <select
            value={priorityFilter}
            onChange={e => setPriorityFilter(e.target.value)}
            style={{
              backgroundColor: 'var(--cg-surface-secondary)',
              border: '1px solid var(--cg-border)',
              color: 'var(--text-primary)',
              borderRadius: '6px',
              padding: '0.35rem 0.65rem',
              fontSize: '0.775rem',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">Critical (P1)</option>
            <option value="HIGH">High (P2)</option>
            <option value="MEDIUM">Medium (P3)</option>
            <option value="LOW">Low (P4)</option>
          </select>

          {/* Service Filter */}
          <select
            value={serviceFilter}
            onChange={e => setServiceFilter(e.target.value)}
            style={{
              backgroundColor: 'var(--cg-surface-secondary)',
              border: '1px solid var(--cg-border)',
              color: 'var(--text-primary)',
              borderRadius: '6px',
              padding: '0.35rem 0.65rem',
              fontSize: '0.775rem',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Services</option>
            {uniqueServices.map(svc => (
              <option key={svc} value={svc}>{svc}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Problem Registry Table */}
      <div className="card" style={{ overflowX: 'auto', padding: 0 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--cg-border)', color: 'var(--text-secondary)', backgroundColor: 'var(--cg-surface-secondary)' }}>
              <th style={{ padding: '0.85rem 1.25rem' }}>Problem ID</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Problem Title & Root Cause</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Priority</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Status</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Service</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Aging</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Date Created</th>
              <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredProblems.slice(0, 100).map(prb => (
              <tr
                key={prb.id}
                onClick={() => handleOpenDetail(prb.id)}
                style={{
                  borderBottom: '1px solid #F0F4F7',
                  cursor: 'pointer',
                  transition: 'background-color 0.15s ease'
                }}
                onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--cg-surface-hover)'}
                onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700, color: 'var(--cg-blue-primary)' }}>
                  {prb.id}
                </td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span>{prb.title}</span>
                    <span style={{ fontSize: '0.675rem', color: 'var(--text-muted)' }}>{prb.root_cause_category}</span>
                  </div>
                </td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  <span className={`badge ${(prb.priority === 'P1' || prb.priority === 'Critical') ? 'badge-critical' : (prb.priority === 'P2' || prb.priority === 'High') ? 'badge-warning' : 'badge-info'}`}>
                    {prb.priority}
                  </span>
                </td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-secondary)' }}>
                  {prb.status}
                </td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                  {prb.service}
                </td>
                <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: prb.age_days > 60 ? 'var(--status-critical)' : prb.age_days > 30 ? 'var(--status-warning)' : 'var(--text-secondary)' }}>
                  {prb.age_days} days
                </td>
                <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-muted)' }}>
                  {formatDateLocal(prb.created)}
                </td>
                <td style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenDetail(prb.id);
                    }}
                    className="btn-cg-secondary"
                    style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}
                  >
                    <span>Investigate</span>
                    <ChevronRight size={13} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Slide-over Problem Intelligence Detail Drawer */}
      {selectedProblemId && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1000,
          display: 'flex',
          justifyContent: 'flex-end',
          backgroundColor: 'rgba(0, 0, 0, 0.4)',
          backdropFilter: 'blur(3px)'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '560px',
            height: '100vh',
            backgroundColor: 'var(--cg-surface-elevated)',
            borderLeft: '1px solid var(--cg-border)',
            boxShadow: '-10px 0 30px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            flexDirection: 'column',
            overflowY: 'auto'
          }}>
            {/* Drawer Header */}
            <div style={{
              padding: '1.25rem 1.5rem',
              backgroundColor: 'var(--cg-surface-secondary)',
              borderBottom: '1px solid var(--cg-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              position: 'sticky',
              top: 0,
              zIndex: 10
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <div style={{
                  padding: '0.4rem',
                  borderRadius: '6px',
                  backgroundColor: 'var(--cg-blue-soft)',
                  color: 'var(--cg-blue-primary)'
                }}>
                  <Target size={20} />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                    {selectedProblemId}
                  </h2>
                  <span style={{ fontSize: '0.725rem', color: 'var(--cg-blue-primary)', fontWeight: 600 }}>
                    Problem Root Cause Intelligence
                  </span>
                </div>
              </div>
              <button
                onClick={handleCloseDetail}
                style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Drawer Body */}
            <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {detailLoading || !problemDetail ? (
                <div style={{ padding: '4rem 0', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <RefreshCw size={24} className="animate-spin" color="var(--cg-blue-primary)" style={{ margin: '0 auto 0.75rem auto' }} />
                  <p>Loading Problem Intelligence Dossier...</p>
                </div>
              ) : (
                <>
                  {/* Status & Service Metadata Card */}
                  <div className="card" style={{ padding: '1rem', backgroundColor: 'var(--cg-surface-secondary)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Target Service</span>
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>{problemDetail.service_name}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <span className={`badge ${problemDetail.priority === 'Critical' ? 'badge-critical' : problemDetail.priority === 'High' ? 'badge-warning' : 'badge-info'}`}>
                        {problemDetail.priority} Priority
                      </span>
                      <span className="badge badge-info">
                        Status: {problemDetail.status}
                      </span>
                      <span className="badge badge-warning">
                        Age: {problemDetail.age_days} Days
                      </span>
                    </div>
                  </div>

                  {/* Derived Root Cause Hypothesis */}
                  <div className="card">
                    <div className="card-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Sparkles size={16} color="var(--cg-blue-primary)" />
                        <h3 className="card-title">Root Cause Assessment</h3>
                      </div>
                      <span className="badge badge-info">{problemDetail.confidence}</span>
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                      {problemDetail.root_cause_category}
                    </div>
                    <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                      {problemDetail.operational_impact}
                    </p>
                  </div>

                  {/* Recommended Engineering Action Plan */}
                  <div className="card">
                    <div className="card-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <ShieldCheck size={16} color="var(--status-healthy)" />
                        <h3 className="card-title">Recommended Corrective Actions</h3>
                      </div>
                      <span className="badge badge-healthy">Remediation</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {problemDetail.recommended_actions.map((act, idx) => (
                        <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                          <CheckCircle2 size={14} color="var(--status-healthy)" style={{ flexShrink: 0, marginTop: 2 }} />
                          <span>{act}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Linked Recent Incident Clusters */}
                  <div className="card">
                    <div className="card-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Activity size={16} color="var(--cg-blue-primary)" />
                        <h3 className="card-title">Correlated Service Incidents</h3>
                      </div>
                      <span className="badge badge-warning">{problemDetail.related_incidents_count} Linked</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                      {problemDetail.related_incidents.map((inc) => (
                        <div key={inc.incident_id} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '0.45rem 0.65rem',
                          borderRadius: '6px',
                          backgroundColor: 'var(--cg-surface-secondary)',
                          border: '1px solid var(--cg-border)',
                          fontSize: '0.775rem'
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                            <span style={{ fontWeight: 700, color: 'var(--cg-blue-primary)' }}>{inc.incident_id}</span>
                            <span className={`badge ${inc.priority === 'Critical' ? 'badge-critical' : inc.priority === 'High' ? 'badge-warning' : 'badge-info'}`} style={{ fontSize: '0.6rem', padding: '0.05rem 0.35rem' }}>
                              {inc.priority}
                            </span>
                          </div>
                          <span style={{ color: 'var(--text-muted)' }}>
                            {inc.resolution_time_hours ? `${inc.resolution_time_hours}h MTTR` : inc.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
