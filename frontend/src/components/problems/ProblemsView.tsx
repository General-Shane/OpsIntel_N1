import React, { useEffect, useState } from 'react';
import {
  Target,
  Download,
  RefreshCw,
  Search,
  AlertTriangle,
  ChevronRight,
  X,
  Activity,
  PlusCircle,
  BookOpen,
  History,
  CheckSquare,
  AlertCircle
} from 'lucide-react';
import apiClient from '../../api/client';
import { downloadCSV } from '../../utils/export';
import { formatDateLocal } from '../../utils/date';

interface ProblemItem {
  id: string;
  problem_id?: string;
  title: string;
  status: string;
  priority: string;
  raw_priority?: string;
  service: string;
  service_id?: string;
  root_cause_category?: string;
  workaround?: string;
  kedb_status?: string;
  age_days: number;
  created: string;
}

interface ProblemDetail {
  problem_id: string;
  title: string;
  description?: string;
  service_id: string;
  service_name: string;
  status: string;
  priority: string;
  age_days: number;
  created_at: string;
  resolved_at: string | null;
  root_cause_category?: string;
  root_cause_text?: string;
  workaround?: string;
  resolution?: string;
  kedb_status?: string;
  assignment_group?: string;
  owner_username?: string;
  confidence?: string;
  related_incidents_count?: number;
  linked_incidents?: Array<{
    incident_id: string;
    title?: string;
    priority: string;
    status: string;
    resolution_time_hours: number | null;
    created_at: string;
  }>;
  audit_trail?: Array<{
    id: string;
    actor_username: string | null;
    action: string;
    timestamp_utc: string;
    old_state?: any;
    new_state?: any;
  }>;
  recommended_actions?: string[];
  operational_impact?: string;
}

export const ProblemsView: React.FC = () => {
  const [problems, setProblems] = useState<ProblemItem[]>([]);
  const [summaryData, setSummaryData] = useState<any>(null);
  const [servicesList, setServicesList] = useState<any[]>([]);
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
  const [activeTab, setActiveTab] = useState<'overview' | 'workaround' | 'audit'>('overview');

  // Workaround editing state
  const [editWorkaround, setEditWorkaround] = useState('');
  const [editRootCauseText, setEditRootCauseText] = useState('');
  const [editKedbStatus, setEditKedbStatus] = useState('DRAFT');
  const [isSavingInvestigation, setIsSavingInvestigation] = useState(false);

  // Resolve modal state
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [resolutionText, setResolutionText] = useState('');
  const [isResolving, setIsResolving] = useState(false);

  // Create Problem modal state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newServiceId, setNewServiceId] = useState('');
  const [newPriority, setNewPriority] = useState('P2');
  const [newCategory, setNewCategory] = useState('Infrastructure');
  const [newAssignmentGroup, setNewAssignmentGroup] = useState('Tier-3 Core SRE');
  const [newDescription, setNewDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchData = () => {
    setLoading(true);
    Promise.allSettled([
      apiClient.get('/problems?limit=250'),
      apiClient.get('/analytics/problems/summary'),
      apiClient.get('/analytics/services')
    ]).then((results) => {
      const [prbRes, summaryRes, svcRes] = results;
      if (prbRes.status === 'fulfilled' && prbRes.value.data?.items) {
        // Normalize for table
        const formatted = prbRes.value.data.items.map((p: any) => ({
          id: p.problem_id,
          problem_id: p.problem_id,
          title: p.title || 'Untitled Problem',
          status: p.status,
          priority: p.priority,
          service: p.service_name || p.service_id,
          service_id: p.service_id,
          root_cause_category: p.root_cause_category,
          workaround: p.workaround,
          kedb_status: p.kedb_status,
          age_days: p.age_days || 0,
          created: p.opened_at || p.created_at
        }));
        setProblems(formatted);
      } else {
        // Fallback to legacy analytics route
        apiClient.get('/analytics/raw/problems?limit=250').then(res => setProblems(res.data)).catch(() => {});
      }

      if (summaryRes.status === 'fulfilled') {
        setSummaryData(summaryRes.value.data);
      }
      if (svcRes.status === 'fulfilled') {
        setServicesList(svcRes.value.data || []);
        if (svcRes.value.data?.length > 0 && !newServiceId) {
          setNewServiceId(svcRes.value.data[0].service_id);
        }
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
    setActiveTab('overview');
    try {
      const res = await apiClient.get(`/problems/${problemId}`);
      setProblemDetail(res.data);
      setEditWorkaround(res.data.workaround || '');
      setEditRootCauseText(res.data.root_cause_text || '');
      setEditKedbStatus(res.data.kedb_status || 'DRAFT');
    } catch (err) {
      console.warn("Direct /problems/:id call failed, trying analytics endpoint", err);
      try {
        const fallback = await apiClient.get(`/analytics/problems/${problemId}`);
        setProblemDetail(fallback.data);
      } catch (fErr) {
        console.error("Failed to load problem detail", fErr);
      }
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedProblemId(null);
    setProblemDetail(null);
    setIsResolveModalOpen(false);
  };

  const handleTransitionStatus = async (nextStatus: string) => {
    if (!selectedProblemId) return;
    try {
      const res = await apiClient.patch(`/problems/${selectedProblemId}/status`, { status: nextStatus });
      setProblemDetail(prev => prev ? { ...prev, status: res.data.status } : null);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Status transition failed.");
    }
  };

  const handleSaveInvestigation = async () => {
    if (!selectedProblemId) return;
    setIsSavingInvestigation(true);
    try {
      const res = await apiClient.patch(`/problems/${selectedProblemId}/investigation`, {
        workaround: editWorkaround,
        root_cause_text: editRootCauseText,
        kedb_status: editKedbStatus
      });
      setProblemDetail(prev => prev ? {
        ...prev,
        workaround: res.data.workaround,
        root_cause_text: res.data.root_cause_text,
        kedb_status: res.data.kedb_status
      } : null);
      alert("Investigation findings & KEDB status updated successfully!");
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to update investigation.");
    } finally {
      setIsSavingInvestigation(false);
    }
  };

  const handleResolveProblem = async () => {
    if (!selectedProblemId || !resolutionText.trim()) {
      alert("Please enter a resolution description.");
      return;
    }
    setIsResolving(true);
    try {
      const res = await apiClient.post(`/problems/${selectedProblemId}/resolve`, {
        resolution: resolutionText,
        workaround: editWorkaround || undefined,
        root_cause_text: editRootCauseText || undefined,
        kedb_status: "PUBLISHED"
      });
      setProblemDetail(prev => prev ? {
        ...prev,
        status: res.data.status,
        resolution: res.data.resolution,
        resolved_at: res.data.resolved_at,
        kedb_status: res.data.kedb_status
      } : null);
      setIsResolveModalOpen(false);
      setResolutionText('');
      alert("Problem successfully marked as RESOLVED and published to KEDB!");
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to resolve problem.");
    } finally {
      setIsResolving(false);
    }
  };

  const handleCreateProblem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newServiceId) {
      setFormError("Title and target service are mandatory.");
      return;
    }
    setIsCreating(true);
    setFormError(null);
    try {
      const res = await apiClient.post('/problems', {
        service_id: newServiceId,
        title: newTitle,
        description: newDescription,
        priority: newPriority,
        category: newCategory,
        assignment_group: newAssignmentGroup
      });
      setIsCreateOpen(false);
      setNewTitle('');
      setNewDescription('');
      fetchData();
      handleOpenDetail(res.data.problem_id);
    } catch (err: any) {
      setFormError(err.response?.data?.detail || "Failed to create problem record.");
    } finally {
      setIsCreating(false);
    }
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
    const matchesService = serviceFilter === 'ALL' || prb.service === serviceFilter || prb.service_id === serviceFilter;

    return matchesSearch && matchesStatus && matchesPriority && matchesService;
  });

  const uniqueServices = Array.from(new Set(problems.map(p => p.service))).filter(Boolean);
  const summary = summaryData?.summary || {};

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
            Root-cause governance • Aging telemetry • Known Error Database (KEDB) • Lifecycle tracking
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button onClick={() => setIsCreateOpen(true)} className="btn-cg-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <PlusCircle size={16} />
            <span>Create Problem</span>
          </button>
          <button onClick={fetchData} disabled={loading} className="btn-cg-secondary">
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
            <span>{loading ? "Loading..." : "Refresh"}</span>
          </button>
          <button onClick={handleExport} className="btn-cg-secondary">
            <Download size={15} />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Executive Problem Summary Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem'
      }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Open Problem Backlog</span>
            <Target size={16} color="var(--cg-blue-primary)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.35rem 0' }}>
            {summary.open_backlog || problems.filter(p => p.status !== 'RESOLVED' && p.status !== 'CLOSED').length}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            <span style={{ color: 'var(--status-healthy)', fontWeight: 700 }}>{summary.resolved_problems || problems.filter(p => p.status === 'RESOLVED' || p.status === 'CLOSED').length}</span> Resolved total
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Critical & High Priority</span>
            <AlertTriangle size={16} color="var(--status-critical)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-critical)', margin: '0.35rem 0' }}>
            {summary.critical_high_count || problems.filter(p => (p.priority === 'P1' || p.priority === 'P2') && p.status !== 'CLOSED').length}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            Active P1/P2 root-cause investigations
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Average Backlog Age</span>
            <AlertCircle size={16} color="var(--status-warning)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.35rem 0' }}>
            {summary.avg_age_days ? `${summary.avg_age_days}d` : '18.4d'}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            Target threshold: &lt; 30 days
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Published to KEDB</span>
            <BookOpen size={16} color="var(--status-healthy)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-healthy)', margin: '0.35rem 0' }}>
            {problems.filter(p => p.kedb_status === 'PUBLISHED').length}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--status-healthy)' }}>
            Verified operational workarounds
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="card" style={{ padding: '0.85rem 1.25rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ flex: 1, minWidth: '220px', position: 'relative' }}>
            <Search size={15} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search problem ID, root cause, or service..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-cg"
              style={{ width: '100%', paddingLeft: '2.25rem' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="select-cg">
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="INVESTIGATING">Investigating</option>
              <option value="KNOWN_ERROR">Known Error</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>

            <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)} className="select-cg">
              <option value="ALL">All Priorities</option>
              <option value="P1">P1 Critical</option>
              <option value="P2">P2 High</option>
              <option value="P3">P3 Medium</option>
              <option value="P4">P4 Low</option>
            </select>

            <select value={serviceFilter} onChange={(e) => setServiceFilter(e.target.value)} className="select-cg">
              <option value="ALL">All Services</option>
              {uniqueServices.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Problems Registry Table */}
      <div className="card" style={{ overflowX: 'auto', padding: 0 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--cg-border)', color: 'var(--text-secondary)', backgroundColor: 'var(--cg-surface-secondary)' }}>
              <th style={{ padding: '0.85rem 1.25rem' }}>Problem ID</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Title & Description</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Target Service</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Priority</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Status</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>KEDB</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Age</th>
              <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredProblems.slice(0, 50).map(prb => (
              <tr
                key={prb.id}
                onClick={() => handleOpenDetail(prb.id)}
                style={{
                  borderBottom: '1px solid var(--cg-border)',
                  cursor: 'pointer',
                  backgroundColor: selectedProblemId === prb.id ? 'var(--cg-blue-soft)' : 'transparent',
                  transition: 'background-color 0.15s ease'
                }}
              >
                <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700, color: 'var(--cg-blue-primary)' }}>
                  {prb.id}
                </td>
                <td style={{ padding: '0.85rem 1.25rem', maxWidth: '280px' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {prb.title}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {prb.root_cause_category || 'Investigation pending'}
                  </div>
                </td>
                <td style={{ padding: '0.85rem 1.25rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                  {prb.service}
                </td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  <span className={`badge ${prb.priority === 'P1' ? 'badge-critical' : prb.priority === 'P2' ? 'badge-warning' : 'badge-info'}`}>
                    {prb.priority}
                  </span>
                </td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  <span className={`badge ${prb.status === 'RESOLVED' ? 'badge-healthy' : prb.status === 'KNOWN_ERROR' ? 'badge-warning' : prb.status === 'INVESTIGATING' ? 'badge-info' : 'badge-neutral'}`}>
                    {prb.status}
                  </span>
                </td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  {prb.kedb_status === 'PUBLISHED' ? (
                    <span className="badge badge-healthy" style={{ fontSize: '0.7rem' }}>Published</span>
                  ) : prb.workaround ? (
                    <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>Draft</span>
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>None</span>
                  )}
                </td>
                <td style={{ padding: '0.85rem 1.25rem', color: prb.age_days > 30 ? 'var(--status-critical)' : 'var(--text-secondary)' }}>
                  {prb.age_days}d
                </td>
                <td style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>
                  <ChevronRight size={16} color="var(--text-muted)" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Slide-over Detail Drawer */}
      {selectedProblemId && (
        <div style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          left: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.45)',
          zIndex: 999,
          display: 'flex',
          justifyContent: 'flex-end',
          animation: 'fadeIn 0.2s ease-out'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '680px',
            backgroundColor: 'var(--cg-surface)',
            height: '100%',
            boxShadow: '-4px 0 24px rgba(0,0,0,0.15)',
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
                    Problem Root Cause & Governance Dossier
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

            {/* Navigation Tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid var(--cg-border)', padding: '0 1.5rem', backgroundColor: 'var(--cg-surface-secondary)' }}>
              <button
                onClick={() => setActiveTab('overview')}
                style={{
                  padding: '0.75rem 1rem',
                  border: 'none',
                  background: 'none',
                  borderBottom: activeTab === 'overview' ? '2px solid var(--cg-blue-primary)' : '2px solid transparent',
                  color: activeTab === 'overview' ? 'var(--cg-blue-primary)' : 'var(--text-secondary)',
                  fontWeight: activeTab === 'overview' ? 700 : 500,
                  cursor: 'pointer'
                }}
              >
                Overview & Lifecycle
              </button>
              <button
                onClick={() => setActiveTab('workaround')}
                style={{
                  padding: '0.75rem 1rem',
                  border: 'none',
                  background: 'none',
                  borderBottom: activeTab === 'workaround' ? '2px solid var(--cg-blue-primary)' : '2px solid transparent',
                  color: activeTab === 'workaround' ? 'var(--cg-blue-primary)' : 'var(--text-secondary)',
                  fontWeight: activeTab === 'workaround' ? 700 : 500,
                  cursor: 'pointer'
                }}
              >
                Workaround & KEDB
              </button>
              <button
                onClick={() => setActiveTab('audit')}
                style={{
                  padding: '0.75rem 1rem',
                  border: 'none',
                  background: 'none',
                  borderBottom: activeTab === 'audit' ? '2px solid var(--cg-blue-primary)' : '2px solid transparent',
                  color: activeTab === 'audit' ? 'var(--cg-blue-primary)' : 'var(--text-secondary)',
                  fontWeight: activeTab === 'audit' ? 700 : 500,
                  cursor: 'pointer'
                }}
              >
                Audit Trail ({problemDetail?.audit_trail?.length || 0})
              </button>
            </div>

            {/* Drawer Body */}
            <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', flex: 1 }}>
              {detailLoading || !problemDetail ? (
                <div style={{ padding: '4rem 0', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <RefreshCw size={24} className="animate-spin" color="var(--cg-blue-primary)" style={{ margin: '0 auto 0.75rem auto' }} />
                  <p>Loading Problem Intelligence Dossier...</p>
                </div>
              ) : (
                <>
                  {activeTab === 'overview' && (
                    <>
                      {/* State Machine Transition Bar */}
                      <div className="card" style={{ backgroundColor: 'var(--cg-surface-secondary)', border: '1px solid var(--cg-border)' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.65rem' }}>
                          LIFECYCLE TRANSITION CONTROLS
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          {problemDetail.status === 'OPEN' && (
                            <button
                              onClick={() => handleTransitionStatus('INVESTIGATING')}
                              className="btn-cg-primary"
                              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                            >
                              Start Investigation
                            </button>
                          )}
                          {problemDetail.status === 'INVESTIGATING' && (
                            <>
                              <button
                                onClick={() => handleTransitionStatus('KNOWN_ERROR')}
                                className="btn-cg-secondary"
                                style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                              >
                                Mark as Known Error
                              </button>
                              <button
                                onClick={() => setIsResolveModalOpen(true)}
                                className="btn-cg-primary"
                                style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', backgroundColor: 'var(--status-healthy)' }}
                              >
                                Resolve Problem
                              </button>
                            </>
                          )}
                          {problemDetail.status === 'KNOWN_ERROR' && (
                            <button
                              onClick={() => setIsResolveModalOpen(true)}
                              className="btn-cg-primary"
                              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', backgroundColor: 'var(--status-healthy)' }}
                            >
                              Resolve Problem
                            </button>
                          )}
                          {problemDetail.status === 'RESOLVED' && (
                            <button
                              onClick={() => handleTransitionStatus('CLOSED')}
                              className="btn-cg-secondary"
                              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                            >
                              Close Problem
                            </button>
                          )}
                          {problemDetail.status === 'CLOSED' && (
                            <span className="badge badge-healthy">Problem Lifecycle Completed</span>
                          )}
                        </div>
                      </div>

                      {/* Status & Service Metadata Card */}
                      <div className="card" style={{ padding: '1rem', backgroundColor: 'var(--cg-surface-secondary)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Target Service</span>
                          <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>{problemDetail.service_name}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <span className={`badge ${problemDetail.priority === 'P1' ? 'badge-critical' : problemDetail.priority === 'P2' ? 'badge-warning' : 'badge-info'}`}>
                            {problemDetail.priority} Priority
                          </span>
                          <span className="badge badge-info">
                            Status: {problemDetail.status}
                          </span>
                          <span className="badge badge-warning">
                            Age: {problemDetail.age_days} Days
                          </span>
                          {problemDetail.kedb_status === 'PUBLISHED' && (
                            <span className="badge badge-healthy">KEDB Published</span>
                          )}
                        </div>
                      </div>

                      {/* Problem Narrative */}
                      <div className="card">
                        <h3 className="card-title" style={{ marginBottom: '0.4rem' }}>{problemDetail.title}</h3>
                        <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                          {problemDetail.description || 'No detailed narrative provided.'}
                        </p>
                      </div>

                      {/* Resolution details if resolved */}
                      {problemDetail.resolution && (
                        <div className="card" style={{ borderLeft: '4px solid var(--status-healthy)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem' }}>
                            <CheckSquare size={16} color="var(--status-healthy)" />
                            <h4 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>Permanent Resolution</h4>
                          </div>
                          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', margin: 0 }}>
                            {problemDetail.resolution}
                          </p>
                        </div>
                      )}

                      {/* Linked Recent Incident Clusters */}
                      <div className="card">
                        <div className="card-header">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Activity size={16} color="var(--cg-blue-primary)" />
                            <h3 className="card-title">Correlated Service Incidents</h3>
                          </div>
                          <span className="badge badge-warning">{problemDetail.linked_incidents?.length || 0} Linked</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                          {(problemDetail.linked_incidents || []).map((inc) => (
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
                                <span className={`badge ${inc.priority === 'P1' ? 'badge-critical' : inc.priority === 'P2' ? 'badge-warning' : 'badge-info'}`} style={{ fontSize: '0.6rem', padding: '0.05rem 0.35rem' }}>
                                  {inc.priority}
                                </span>
                              </div>
                              <span style={{ color: 'var(--text-muted)' }}>
                                {inc.resolution_time_hours ? `${inc.resolution_time_hours}h MTTR` : inc.status}
                              </span>
                            </div>
                          ))}
                          {(!problemDetail.linked_incidents || problemDetail.linked_incidents.length === 0) && (
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '0.5rem 0' }}>
                              No correlated incident records attached.
                            </div>
                          )}
                        </div>
                      </div>
                    </>
                  )}

                  {activeTab === 'workaround' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div className="card">
                        <h3 className="card-title" style={{ marginBottom: '0.5rem' }}>Known Error Database (KEDB) Publisher</h3>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                          Document validated workarounds so NOC operators can mitigate active service degradation while permanent root-cause remediation is underway.
                        </p>

                        <div style={{ marginBottom: '1rem' }}>
                          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                            Root Cause Hypothesis / Analysis
                          </label>
                          <textarea
                            rows={3}
                            value={editRootCauseText}
                            onChange={(e) => setEditRootCauseText(e.target.value)}
                            placeholder="Detailed technical hypothesis of the defect or resource leak..."
                            className="input-cg"
                            style={{ width: '100%', fontSize: '0.85rem' }}
                          />
                        </div>

                        <div style={{ marginBottom: '1rem' }}>
                          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                            Documented Workaround (Actionable Procedure)
                          </label>
                          <textarea
                            rows={4}
                            value={editWorkaround}
                            onChange={(e) => setEditWorkaround(e.target.value)}
                            placeholder="Step-by-step mitigation (e.g. failover procedure, thread pool restart)..."
                            className="input-cg"
                            style={{ width: '100%', fontSize: '0.85rem' }}
                          />
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>KEDB Publishing Status:</label>
                            <select
                              value={editKedbStatus}
                              onChange={(e) => setEditKedbStatus(e.target.value)}
                              className="select-cg"
                              style={{ fontSize: '0.8rem' }}
                            >
                              <option value="DRAFT">DRAFT (Internal Review)</option>
                              <option value="PUBLISHED">PUBLISHED (Available in KEDB)</option>
                              <option value="NONE">NONE</option>
                            </select>
                          </div>

                          <button
                            onClick={handleSaveInvestigation}
                            disabled={isSavingInvestigation}
                            className="btn-cg-primary"
                          >
                            {isSavingInvestigation ? "Saving..." : "Save Workaround & KEDB"}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'audit' && (
                    <div className="card">
                      <div className="card-header">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <History size={16} color="var(--cg-blue-primary)" />
                          <h3 className="card-title">Immutable Audit Trail</h3>
                        </div>
                        <span className="badge badge-info">Compliance Log</span>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {(problemDetail.audit_trail || []).map((audit) => (
                          <div key={audit.id} style={{
                            padding: '0.75rem',
                            borderRadius: '6px',
                            backgroundColor: 'var(--cg-surface-secondary)',
                            border: '1px solid var(--cg-border)',
                            fontSize: '0.8rem'
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                              <span style={{ fontWeight: 700, color: 'var(--cg-blue-primary)' }}>{audit.action}</span>
                              <span style={{ color: 'var(--text-muted)', fontSize: '0.725rem' }}>{formatDateLocal(audit.timestamp_utc)}</span>
                            </div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                              Actor: <strong>{audit.actor_username || 'SYSTEM'}</strong>
                            </div>
                          </div>
                        ))}
                        {(!problemDetail.audit_trail || problemDetail.audit_trail.length === 0) && (
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1rem 0' }}>
                            No audit events recorded for this problem yet.
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Resolve Problem Modal */}
      {isResolveModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '520px', width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                Resolve Problem {selectedProblemId}
              </h3>
              <button onClick={() => setIsResolveModalOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                <X size={18} />
              </button>
            </div>

            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Document the permanent engineering fix that eliminates this defect from recurrence.
            </p>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                Resolution Statement *
              </label>
              <textarea
                rows={4}
                value={resolutionText}
                onChange={(e) => setResolutionText(e.target.value)}
                placeholder="Describe the permanent code, configuration, or infrastructure fix applied..."
                className="input-cg"
                style={{ width: '100%', fontSize: '0.85rem' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button onClick={() => setIsResolveModalOpen(false)} className="btn-cg-secondary">
                Cancel
              </button>
              <button
                onClick={handleResolveProblem}
                disabled={isResolving || !resolutionText.trim()}
                className="btn-cg-primary"
                style={{ backgroundColor: 'var(--status-healthy)' }}
              >
                {isResolving ? "Resolving..." : "Confirm Problem Resolution"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Problem Modal */}
      {isCreateOpen && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '1rem'
        }}>
          <form onSubmit={handleCreateProblem} className="card" style={{ maxWidth: '560px', width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <PlusCircle size={20} color="var(--cg-blue-primary)" />
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Log New Problem Record
                </h3>
              </div>
              <button type="button" onClick={() => setIsCreateOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                <X size={18} />
              </button>
            </div>

            {formError && (
              <div style={{ padding: '0.65rem', marginBottom: '1rem', borderRadius: '6px', backgroundColor: 'var(--status-critical-soft, #fee2e2)', color: 'var(--status-critical)', fontSize: '0.8rem' }}>
                {formError}
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Target Service *
                </label>
                <select
                  value={newServiceId}
                  onChange={(e) => setNewServiceId(e.target.value)}
                  className="select-cg"
                  style={{ width: '100%' }}
                >
                  {servicesList.map(s => (
                    <option key={s.service_id} value={s.service_id}>{s.service_name} ({s.service_id})</option>
                  ))}
                  {servicesList.length === 0 && (
                    <option value="SVC_PAYMENT">Payment Gateway (SVC_PAYMENT)</option>
                  )}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Priority *
                </label>
                <select
                  value={newPriority}
                  onChange={(e) => setNewPriority(e.target.value)}
                  className="select-cg"
                  style={{ width: '100%' }}
                >
                  <option value="P1">P1 Critical</option>
                  <option value="P2">P2 High</option>
                  <option value="P3">P3 Medium</option>
                  <option value="P4">P4 Low</option>
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                Problem Title *
              </label>
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="e.g. Memory leak on API Gateway worker instances"
                className="input-cg"
                style={{ width: '100%' }}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Category
                </label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="select-cg"
                  style={{ width: '100%' }}
                >
                  <option value="Infrastructure">Infrastructure</option>
                  <option value="Application">Application</option>
                  <option value="Database">Database</option>
                  <option value="Network">Network</option>
                  <option value="Security">Security</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Assignment Group
                </label>
                <select
                  value={newAssignmentGroup}
                  onChange={(e) => setNewAssignmentGroup(e.target.value)}
                  className="select-cg"
                  style={{ width: '100%' }}
                >
                  <option value="Tier-3 Core SRE">Tier-3 Core SRE</option>
                  <option value="Tier-2 Platform Ops">Tier-2 Platform Ops</option>
                  <option value="Database Administrators">Database Administrators</option>
                  <option value="Security Operations">Security Operations</option>
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                Technical Description & Symptoms
              </label>
              <textarea
                rows={3}
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Detailed technical description of the recurring failure patterns..."
                className="input-cg"
                style={{ width: '100%', fontSize: '0.85rem' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button type="button" onClick={() => setIsCreateOpen(false)} className="btn-cg-secondary">
                Cancel
              </button>
              <button
                type="submit"
                disabled={isCreating}
                className="btn-cg-primary"
              >
                {isCreating ? "Logging..." : "Create Problem"}
              </button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
};
