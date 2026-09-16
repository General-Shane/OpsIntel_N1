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
import {
  GitCommit,
  Download,
  RefreshCw,
  Search,
  PlusCircle,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ShieldCheck,
  FileText,
  X,
  ChevronRight,
  RotateCcw,
  PlayCircle,
  AlertCircle
} from 'lucide-react';
import apiClient from '../../api/client';
import { downloadCSV } from '../../utils/export';
import { formatDateLocal } from '../../utils/date';

interface ChangeItem {
  id: string;
  change_id: string;
  title: string;
  description?: string;
  service: string;
  service_id?: string;
  type: string;
  change_type?: string;
  status: string;
  risk: string;
  risk_level?: string;
  impact?: string;
  cab_status?: string;
  approval_status?: string;
  requester_username?: string;
  implementer_username?: string;
  assignment_group?: string;
  rollback_required?: boolean;
  successful?: boolean;
  completed_at?: string;
  created: string;
  created_at?: string;
  implementation_start?: string;
  implementation_end?: string;
}

interface ChangeDetail extends ChangeItem {
  implementation_plan?: string;
  rollback_plan?: string;
  problem_id?: string;
  correlated_incidents?: Array<{
    incident_id: string;
    title: string;
    priority: string;
    status: string;
    created_at?: string;
  }>;
  audit_trail?: Array<{
    id: string;
    actor_username: string | null;
    action: string;
    timestamp_utc: string;
    old_state?: any;
    new_state?: any;
  }>;
}

export const ChangesView: React.FC = () => {
  const [changes, setChanges] = useState<ChangeItem[]>([]);
  const [kpis, setKpis] = useState<any>(null);
  const [servicesList, setServicesList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters & Search
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Detail Drawer State
  const [selectedChangeId, setSelectedChangeId] = useState<string | null>(null);
  const [changeDetail, setChangeDetail] = useState<ChangeDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'workflow' | 'audit'>('overview');

  // CAB Decision Modal / Action State
  const [cabDecisionModal, setCabDecisionModal] = useState<{
    isOpen: boolean;
    decision: 'APPROVED' | 'REJECTED';
    comments: string;
    submitting: boolean;
  }>({ isOpen: false, decision: 'APPROVED', comments: '', submitting: false });

  // Rollback Modal State
  const [rollbackModal, setRollbackModal] = useState<{
    isOpen: boolean;
    reason: string;
    notes: string;
    submitting: boolean;
  }>({ isOpen: false, reason: '', notes: '', submitting: false });

  // Create Change Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newServiceId, setNewServiceId] = useState('');
  const [newChangeType, setNewChangeType] = useState('NORMAL');
  const [newRiskLevel, setNewRiskLevel] = useState('MEDIUM');
  const [newImpact, setNewImpact] = useState('MEDIUM');
  const [newAssignmentGroup, setNewAssignmentGroup] = useState('Release Engineering');
  const [newProblemId, setNewProblemId] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newImplPlan, setNewImplPlan] = useState('');
  const [newRollbackPlan, setNewRollbackPlan] = useState('');
  const [newAutoSubmitCab, setNewAutoSubmitCab] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchData = () => {
    setLoading(true);
    Promise.allSettled([
      apiClient.get('/changes?limit=250'),
      apiClient.get('/analytics/kpis'),
      apiClient.get('/analytics/services')
    ]).then((results) => {
      const [chgRes, kpiRes, svcRes] = results;

      if (chgRes.status === 'fulfilled' && chgRes.value.data?.items) {
        const formatted: ChangeItem[] = chgRes.value.data.items.map((c: any) => ({
          id: c.change_id || c.id,
          change_id: c.change_id || c.id,
          title: c.title || 'Untitled Change',
          description: c.description,
          service: c.service_name || c.service_id,
          service_id: c.service_id,
          type: c.change_type || 'NORMAL',
          change_type: c.change_type || 'NORMAL',
          status: c.status,
          risk: c.risk_level || 'MEDIUM',
          risk_level: c.risk_level || 'MEDIUM',
          impact: c.impact,
          cab_status: c.cab_status,
          approval_status: c.approval_status,
          requester_username: c.requester_username,
          implementer_username: c.implementer_username,
          assignment_group: c.assignment_group,
          rollback_required: c.rollback_required,
          successful: c.successful,
          completed_at: c.completed_at,
          created: c.created_at || '',
          created_at: c.created_at,
          implementation_start: c.implementation_start,
          implementation_end: c.implementation_end
        }));
        setChanges(formatted);
      } else {
        // Fallback to legacy raw analytics route
        apiClient.get('/analytics/raw/changes?limit=250')
          .then(res => setChanges(res.data))
          .catch(() => {});
      }

      if (kpiRes.status === 'fulfilled') {
        setKpis(kpiRes.value.data);
      }

      if (svcRes.status === 'fulfilled') {
        setServicesList(svcRes.value.data || []);
        if (svcRes.value.data?.length > 0 && !newServiceId) {
          setNewServiceId(svcRes.value.data[0].service_id);
        }
      }
      setLoading(false);
    }).catch(err => {
      console.error("Failed loading changes", err);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenDetail = async (changeId: string) => {
    setSelectedChangeId(changeId);
    setDetailLoading(true);
    setActiveTab('overview');
    try {
      const res = await apiClient.get(`/changes/${changeId}`);
      setChangeDetail(res.data);
    } catch (err) {
      console.warn("Direct /changes/:id call failed, finding local change item", err);
      const local = changes.find(c => c.change_id === changeId || c.id === changeId);
      if (local) {
        setChangeDetail({ ...local, correlated_incidents: [], audit_trail: [] });
      }
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedChangeId(null);
    setChangeDetail(null);
    setCabDecisionModal({ isOpen: false, decision: 'APPROVED', comments: '', submitting: false });
    setRollbackModal({ isOpen: false, reason: '', notes: '', submitting: false });
  };

  const handleSubmitToCab = async () => {
    if (!selectedChangeId) return;
    try {
      const res = await apiClient.post(`/changes/${selectedChangeId}/cab-review`);
      setChangeDetail(prev => prev ? {
        ...prev,
        status: res.data.status,
        cab_status: res.data.cab_status,
        approval_status: res.data.approval_status
      } : null);
      fetchData();
      alert("Change request successfully submitted to CAB for formal review!");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to submit to CAB.");
    }
  };

  const handleCabDecisionSubmit = async () => {
    if (!selectedChangeId) return;
    setCabDecisionModal(prev => ({ ...prev, submitting: true }));
    try {
      const res = await apiClient.post(`/changes/${selectedChangeId}/approve`, {
        decision: cabDecisionModal.decision,
        comments: cabDecisionModal.comments || undefined
      });
      setChangeDetail(prev => prev ? {
        ...prev,
        status: res.data.status,
        cab_status: res.data.cab_status,
        approval_status: res.data.approval_status
      } : null);
      setCabDecisionModal({ isOpen: false, decision: 'APPROVED', comments: '', submitting: false });
      fetchData();
      alert(`Change ${cabDecisionModal.decision.toLowerCase()} recorded by CAB.`);
    } catch (err: any) {
      alert(err.response?.data?.detail || "CAB decision recording failed. Check permissions.");
      setCabDecisionModal(prev => ({ ...prev, submitting: false }));
    }
  };

  const handleDeployAction = async (action: 'START' | 'COMPLETE') => {
    if (!selectedChangeId) return;
    try {
      const res = await apiClient.post(`/changes/${selectedChangeId}/deploy`, { action });
      setChangeDetail(prev => prev ? {
        ...prev,
        status: res.data.status,
        implementation_start: res.data.implementation_start,
        implementation_end: res.data.implementation_end,
        completed_at: res.data.completed_at
      } : null);
      fetchData();
      alert(`Deployment status updated: ${res.data.status}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Deployment action failed.");
    }
  };

  const handleRollbackSubmit = async () => {
    if (!selectedChangeId || !rollbackModal.reason.trim()) {
      alert("Rollback reason is mandatory.");
      return;
    }
    setRollbackModal(prev => ({ ...prev, submitting: true }));
    try {
      const res = await apiClient.post(`/changes/${selectedChangeId}/rollback`, {
        reason: rollbackModal.reason,
        notes: rollbackModal.notes || undefined
      });
      setChangeDetail(prev => prev ? {
        ...prev,
        status: res.data.status,
        rollback_required: res.data.rollback_required,
        successful: res.data.successful,
        completed_at: res.data.completed_at
      } : null);
      setRollbackModal({ isOpen: false, reason: '', notes: '', submitting: false });
      fetchData();
      alert("Emergency Rollback recorded. Change flagged as FAILED.");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to record rollback.");
      setRollbackModal(prev => ({ ...prev, submitting: false }));
    }
  };

  const handleCreateChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newServiceId) {
      setFormError("Change title and target service are mandatory.");
      return;
    }
    setIsCreating(true);
    setFormError(null);
    try {
      const res = await apiClient.post('/changes', {
        service_id: newServiceId,
        title: newTitle,
        description: newDescription || undefined,
        change_type: newChangeType,
        risk_level: newRiskLevel,
        impact: newImpact,
        implementation_plan: newImplPlan || undefined,
        rollback_plan: newRollbackPlan || undefined,
        problem_id: newProblemId || undefined,
        assignment_group: newAssignmentGroup,
        auto_submit_cab: newAutoSubmitCab
      });
      setIsCreateOpen(false);
      setNewTitle('');
      setNewDescription('');
      setNewImplPlan('');
      setNewRollbackPlan('');
      setNewProblemId('');
      fetchData();
      handleOpenDetail(res.data.change_id);
    } catch (err: any) {
      setFormError(err.response?.data?.detail || "Failed to create change request.");
    } finally {
      setIsCreating(false);
    }
  };

  const handleExport = () => {
    downloadCSV(changes, 'changes_governance_export');
  };

  // Filter changes
  const filteredChanges = changes.filter(c => {
    const matchesSearch = !searchTerm ||
      (c.change_id && c.change_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (c.title && c.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (c.service && c.service.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesType = typeFilter === 'ALL' || (c.type || c.change_type || '').toUpperCase() === typeFilter;
    const matchesRisk = riskFilter === 'ALL' || (c.risk || c.risk_level || '').toUpperCase() === riskFilter;
    const matchesStatus = statusFilter === 'ALL' || (c.status || '').toUpperCase() === statusFilter;

    return matchesSearch && matchesType && matchesRisk && matchesStatus;
  });

  // Chart aggregations
  const changeTypeData = (() => {
    const counts = changes.reduce((acc: Record<string, number>, c: any) => {
      const t = (c.type || c.change_type || 'normal').toLowerCase();
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
      const rawDate = c.created || c.created_at;
      if (!rawDate) return;
      const d = new Date(rawDate);
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

  const getStatusBadge = (status: string) => {
    switch ((status || '').toUpperCase()) {
      case 'APPROVED':
      case 'COMPLETED':
        return <span className="badge badge-healthy">{status}</span>;
      case 'IN_PROGRESS':
      case 'REQUESTED':
        return <span className="badge badge-info">{status}</span>;
      case 'DRAFT':
        return <span className="badge" style={{ backgroundColor: 'var(--cg-surface-secondary)', color: 'var(--text-secondary)' }}>DRAFT</span>;
      case 'FAILED':
      case 'CANCELLED':
        return <span className="badge badge-critical">{status}</span>;
      default:
        return <span className="badge badge-warning">{status}</span>;
    }
  };

  const getRiskBadge = (risk: string) => {
    const r = (risk || '').toUpperCase();
    if (r === 'HIGH') return <span className="badge badge-critical">HIGH</span>;
    if (r === 'MEDIUM') return <span className="badge badge-warning">MEDIUM</span>;
    return <span className="badge badge-healthy">LOW</span>;
  };

  const getCabBadge = (cabStatus: string) => {
    const c = (cabStatus || 'NONE').toUpperCase();
    if (c === 'APPROVED') return <span className="badge badge-healthy">CAB APPROVED</span>;
    if (c === 'PENDING') return <span className="badge badge-warning">CAB PENDING</span>;
    if (c === 'REJECTED') return <span className="badge badge-critical">CAB REJECTED</span>;
    return <span className="badge" style={{ backgroundColor: 'var(--cg-surface-secondary)', color: 'var(--text-muted)' }}>NO CAB</span>;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', position: 'relative' }}>
      
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <GitCommit color="var(--cg-blue-primary)" size={24} />
            <h1 className="page-title" style={{ margin: 0 }}>Change Management & Release Governance</h1>
          </div>
          <p className="page-subtitle">
            Deployment tracking • Risk evaluation • CAB approval workflows • Failure telemetry & rollbacks
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button 
            onClick={() => setIsCreateOpen(true)}
            className="btn-cg-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}
          >
            <PlusCircle size={16} />
            <span>Submit Change Request</span>
          </button>
          <button onClick={fetchData} disabled={loading} className="btn-cg-secondary">
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
            <span>{loading ? "Refreshing..." : "Refresh"}</span>
          </button>
          <button onClick={handleExport} className="btn-cg-secondary">
            <Download size={15} />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Total Changes</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.35rem 0' }}>
            {changes.length || kpis?.changes?.total_changes || 0}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Enterprise registry</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Successful Releases</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-healthy)', margin: '0.35rem 0' }}>
            {changes.filter(c => c.status === 'COMPLETED' || c.successful).length}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-healthy)' }}>● Verified deployed</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Pending CAB Review</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-warning)', margin: '0.35rem 0' }}>
            {changes.filter(c => c.cab_status === 'PENDING' || c.status === 'REQUESTED').length}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-warning)' }}>Awaiting approval</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Failed / Rollbacks</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: (changes.filter(c => c.rollback_required || c.status === 'FAILED').length > 0) ? 'var(--status-critical)' : 'var(--text-primary)', margin: '0.35rem 0' }}>
            {changes.filter(c => c.rollback_required || c.status === 'FAILED').length}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Rollbacks recorded</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Emergency Changes</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-critical)', margin: '0.35rem 0' }}>
            {changes.filter(c => (c.type || c.change_type || '').toUpperCase() === 'EMERGENCY').length}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-critical)' }}>Expedited releases</span>
        </div>
      </div>

      {/* Visual Analytics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Change Requests by Type</h3>
            <span className="badge badge-info">Classification</span>
          </div>
          <div style={{ width: '100%', height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={changeTypeData} cx="50%" cy="50%" innerRadius={42} outerRadius={70} paddingAngle={4} dataKey="value">
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
          <div style={{ width: '100%', height: 200 }}>
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

      {/* Interactive Filter Bar */}
      <div className="card" style={{ padding: '0.85rem 1.25rem', display: 'flex', flexWrap: 'wrap', gap: '0.85rem', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: '1 1 240px', minWidth: '220px' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
          <input 
            type="text" 
            placeholder="Search Change ID, title, or service..." 
            value={searchTerm} 
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '0.55rem 0.85rem 0.55rem 2.4rem',
              borderRadius: '6px',
              border: '1px solid var(--cg-border)',
              backgroundColor: 'var(--cg-surface-input)',
              color: 'var(--text-primary)',
              fontSize: '0.85rem'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Type:</label>
          <select 
            value={typeFilter} 
            onChange={(e) => setTypeFilter(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid var(--cg-border)',
              backgroundColor: 'var(--cg-surface-input)',
              color: 'var(--text-primary)',
              fontSize: '0.85rem'
            }}
          >
            <option value="ALL">All Types</option>
            <option value="NORMAL">Normal</option>
            <option value="STANDARD">Standard</option>
            <option value="EMERGENCY">Emergency</option>
          </select>

          <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600, marginLeft: '0.5rem' }}>Risk:</label>
          <select 
            value={riskFilter} 
            onChange={(e) => setRiskFilter(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid var(--cg-border)',
              backgroundColor: 'var(--cg-surface-input)',
              color: 'var(--text-primary)',
              fontSize: '0.85rem'
            }}
          >
            <option value="ALL">All Risk Levels</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600, marginLeft: '0.5rem' }}>Status:</label>
          <select 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid var(--cg-border)',
              backgroundColor: 'var(--cg-surface-input)',
              color: 'var(--text-primary)',
              fontSize: '0.85rem'
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="REQUESTED">Requested (CAB)</option>
            <option value="APPROVED">Approved</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMPLETED">Completed</option>
            <option value="FAILED">Failed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Changes Registry Table */}
      <div className="card" style={{ overflowX: 'auto', padding: 0 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--cg-border)', color: 'var(--text-secondary)', backgroundColor: 'var(--cg-surface-secondary)' }}>
              <th style={{ padding: '0.85rem 1.25rem' }}>Change ID</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Title & Description</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Service</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Type</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Risk Level</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>CAB Status</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Lifecycle Status</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Created</th>
              <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredChanges.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No changes match current filters or search criteria.
                </td>
              </tr>
            ) : (
              filteredChanges.map(c => (
                <tr 
                  key={c.change_id || c.id} 
                  style={{ borderBottom: '1px solid var(--cg-border)', cursor: 'pointer', transition: 'background-color 0.15s' }}
                  onClick={() => handleOpenDetail(c.change_id || c.id)}
                  className="hover-row"
                >
                  <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700, color: 'var(--cg-blue-primary)' }}>
                    {c.change_id || c.id}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem', maxWidth: '320px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {c.title}
                    </div>
                    {c.description && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {c.description}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                    {c.service}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem' }}>
                    <span className="badge badge-info">{c.type || c.change_type}</span>
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem' }}>
                    {getRiskBadge(c.risk || c.risk_level || 'MEDIUM')}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem' }}>
                    {getCabBadge(c.cab_status || 'NONE')}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem' }}>
                    {getStatusBadge(c.status)}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-muted)' }}>
                    {formatDateLocal(c.created || c.created_at || '')}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenDetail(c.change_id || c.id);
                      }}
                      className="btn-cg-secondary"
                      style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                    >
                      <span>Govern</span>
                      <ChevronRight size={13} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Change Detail & Governance Drawer */}
      {selectedChangeId && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1000,
          display: 'flex',
          justifyContent: 'flex-end',
          backgroundColor: 'rgba(0, 0, 0, 0.45)',
          backdropFilter: 'blur(3px)'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '680px',
            height: '100%',
            backgroundColor: 'var(--cg-surface-elevated)',
            borderLeft: '1px solid var(--cg-border)',
            boxShadow: '-10px 0 35px rgba(0,0,0,0.2)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            
            {/* Drawer Header */}
            <div style={{
              padding: '1.25rem 1.5rem',
              borderBottom: '1px solid var(--cg-border)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              backgroundColor: 'var(--cg-surface-secondary)'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
                  <span style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--cg-blue-primary)' }}>
                    {selectedChangeId}
                  </span>
                  {changeDetail && getStatusBadge(changeDetail.status)}
                  {changeDetail && getCabBadge(changeDetail.cab_status || 'NONE')}
                </div>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                  {changeDetail?.title || "Loading Change Request..."}
                </h2>
              </div>
              <button 
                onClick={handleCloseDetail}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  padding: '0.25rem'
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Drawer Tabs */}
            <div style={{
              display: 'flex',
              borderBottom: '1px solid var(--cg-border)',
              backgroundColor: 'var(--cg-surface-secondary)'
            }}>
              <button 
                onClick={() => setActiveTab('overview')}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  border: 'none',
                  borderBottom: activeTab === 'overview' ? '2.5px solid var(--cg-blue-primary)' : '2.5px solid transparent',
                  backgroundColor: 'transparent',
                  color: activeTab === 'overview' ? 'var(--cg-blue-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer'
                }}
              >
                Overview & Plans
              </button>
              <button 
                onClick={() => setActiveTab('workflow')}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  border: 'none',
                  borderBottom: activeTab === 'workflow' ? '2.5px solid var(--cg-blue-primary)' : '2.5px solid transparent',
                  backgroundColor: 'transparent',
                  color: activeTab === 'workflow' ? 'var(--cg-blue-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer'
                }}
              >
                CAB & Execution Workflow
              </button>
              <button 
                onClick={() => setActiveTab('audit')}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  border: 'none',
                  borderBottom: activeTab === 'audit' ? '2.5px solid var(--cg-blue-primary)' : '2.5px solid transparent',
                  backgroundColor: 'transparent',
                  color: activeTab === 'audit' ? 'var(--cg-blue-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer'
                }}
              >
                Audit Trail ({changeDetail?.audit_trail?.length || 0})
              </button>
            </div>

            {/* Drawer Body */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {detailLoading ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '0.75rem' }}>
                  <RefreshCw className="animate-spin" size={32} color="var(--cg-blue-primary)" />
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Retrieving Change Dossier...</span>
                </div>
              ) : changeDetail ? (
                <>
                  {/* TAB 1: OVERVIEW */}
                  {activeTab === 'overview' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                      
                      {/* Meta Matrix */}
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, 1fr)',
                        gap: '0.75rem',
                        padding: '1rem',
                        backgroundColor: 'var(--cg-surface-secondary)',
                        borderRadius: '8px',
                        fontSize: '0.825rem'
                      }}>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Target Service:</span>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{changeDetail.service}</div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Change Type / Risk:</span>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {changeDetail.type || changeDetail.change_type} • {changeDetail.risk || changeDetail.risk_level}
                          </div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Assignment Group:</span>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {changeDetail.assignment_group || 'Release Engineering'}
                          </div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Requester:</span>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {changeDetail.requester_username || 'SYSTEM'}
                          </div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Execution Window:</span>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.75rem' }}>
                            {changeDetail.implementation_start ? formatDateLocal(changeDetail.implementation_start) : 'Not Started'}
                            {changeDetail.implementation_end ? ` → ${formatDateLocal(changeDetail.implementation_end)}` : ''}
                          </div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Linked Problem:</span>
                          <div style={{ fontWeight: 600, color: changeDetail.problem_id ? 'var(--cg-blue-primary)' : 'var(--text-muted)' }}>
                            {changeDetail.problem_id || 'None'}
                          </div>
                        </div>
                      </div>

                      {/* Description */}
                      <div className="card" style={{ padding: '1rem' }}>
                        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <FileText size={15} color="var(--cg-blue-primary)" />
                          Description & Scope
                        </h4>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                          {changeDetail.description || 'No detailed scope provided.'}
                        </p>
                      </div>

                      {/* Implementation Plan */}
                      <div className="card" style={{ padding: '1rem', borderLeft: '4px solid var(--cg-blue-primary)' }}>
                        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                          Implementation & Verification Plan
                        </h4>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap' }}>
                          {changeDetail.implementation_plan || 'Standard release procedure applied.'}
                        </p>
                      </div>

                      {/* Rollback Plan */}
                      <div className="card" style={{ padding: '1rem', borderLeft: '4px solid var(--status-critical)' }}>
                        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <RotateCcw size={14} color="var(--status-critical)" />
                          Backout & Rollback Plan
                        </h4>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap' }}>
                          {changeDetail.rollback_plan || 'Revert release binary and verify previous baseline.'}
                        </p>
                      </div>

                      {/* Correlated Incidents */}
                      {changeDetail.correlated_incidents && changeDetail.correlated_incidents.length > 0 && (
                        <div className="card" style={{ padding: '1rem' }}>
                          <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--status-critical)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <AlertTriangle size={15} color="var(--status-critical)" />
                            Correlated Downstream Incidents ({changeDetail.correlated_incidents.length})
                          </h4>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {changeDetail.correlated_incidents.map((inc: any) => (
                              <div key={inc.incident_id} style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '0.65rem',
                                backgroundColor: 'var(--cg-surface-secondary)',
                                borderRadius: '6px',
                                fontSize: '0.8rem'
                              }}>
                                <div>
                                  <span style={{ fontWeight: 700, color: 'var(--cg-blue-primary)', marginRight: '0.5rem' }}>
                                    {inc.incident_id}
                                  </span>
                                  <span style={{ color: 'var(--text-primary)' }}>{inc.title}</span>
                                </div>
                                <span className={`badge ${inc.priority === 'P1' ? 'badge-critical' : 'badge-warning'}`}>
                                  {inc.priority}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                    </div>
                  )}

                  {/* TAB 2: CAB & WORKFLOW */}
                  {activeTab === 'workflow' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                      
                      {/* Step Progress Tracker */}
                      <div className="card" style={{ padding: '1.25rem' }}>
                        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '1rem' }}>
                          Release Governance Pipeline
                        </h4>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'relative' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem', zIndex: 1 }}>
                            <div style={{
                              width: '28px',
                              height: '28px',
                              borderRadius: '50%',
                              backgroundColor: 'var(--status-healthy)',
                              color: 'white',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '0.75rem',
                              fontWeight: 700
                            }}>✓</div>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Draft</span>
                          </div>

                          <div style={{ height: '2px', flex: 1, backgroundColor: changeDetail.status !== 'DRAFT' ? 'var(--status-healthy)' : 'var(--cg-border)' }} />

                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem', zIndex: 1 }}>
                            <div style={{
                              width: '28px',
                              height: '28px',
                              borderRadius: '50%',
                              backgroundColor: changeDetail.cab_status === 'APPROVED' ? 'var(--status-healthy)' : changeDetail.status === 'REQUESTED' ? 'var(--status-warning)' : 'var(--cg-border)',
                              color: 'white',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '0.75rem',
                              fontWeight: 700
                            }}>
                              {changeDetail.cab_status === 'APPROVED' ? '✓' : '2'}
                            </div>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>CAB Review</span>
                          </div>

                          <div style={{ height: '2px', flex: 1, backgroundColor: (changeDetail.status === 'IN_PROGRESS' || changeDetail.status === 'COMPLETED') ? 'var(--status-healthy)' : 'var(--cg-border)' }} />

                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem', zIndex: 1 }}>
                            <div style={{
                              width: '28px',
                              height: '28px',
                              borderRadius: '50%',
                              backgroundColor: changeDetail.status === 'IN_PROGRESS' ? 'var(--cg-blue-primary)' : changeDetail.status === 'COMPLETED' ? 'var(--status-healthy)' : 'var(--cg-border)',
                              color: 'white',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '0.75rem',
                              fontWeight: 700
                            }}>
                              {changeDetail.status === 'COMPLETED' ? '✓' : '3'}
                            </div>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Deploying</span>
                          </div>

                          <div style={{ height: '2px', flex: 1, backgroundColor: changeDetail.status === 'COMPLETED' ? 'var(--status-healthy)' : changeDetail.status === 'FAILED' ? 'var(--status-critical)' : 'var(--cg-border)' }} />

                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem', zIndex: 1 }}>
                            <div style={{
                              width: '28px',
                              height: '28px',
                              borderRadius: '50%',
                              backgroundColor: changeDetail.status === 'COMPLETED' ? 'var(--status-healthy)' : changeDetail.status === 'FAILED' ? 'var(--status-critical)' : 'var(--cg-border)',
                              color: 'white',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '0.75rem',
                              fontWeight: 700
                            }}>
                              {changeDetail.status === 'COMPLETED' ? '✓' : changeDetail.status === 'FAILED' ? '!' : '4'}
                            </div>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Closed</span>
                          </div>
                        </div>
                      </div>

                      {/* Interactive Actions Panel */}
                      <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                          Available Governance Transitions
                        </h4>

                        {/* If DRAFT */}
                        {changeDetail.status === 'DRAFT' && (
                          <div>
                            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                              This change is currently in DRAFT status. Submit to CAB when the implementation and rollback plans are validated.
                            </p>
                            <button onClick={handleSubmitToCab} className="btn-cg-primary">
                              <ShieldCheck size={16} />
                              <span>Submit to CAB for Formal Review</span>
                            </button>
                          </div>
                        )}

                        {/* If REQUESTED / PENDING CAB */}
                        {(changeDetail.status === 'REQUESTED' || changeDetail.cab_status === 'PENDING') && (
                          <div>
                            <div style={{ padding: '0.75rem', backgroundColor: 'var(--status-warning-bg)', border: '1px solid var(--status-warning-border)', borderRadius: '6px', marginBottom: '1rem' }}>
                              <p style={{ fontSize: '0.825rem', color: 'var(--text-primary)', margin: 0, fontWeight: 500 }}>
                                Awaiting Change Advisory Board approval decision. Authorized CAB chairs and release managers may cast decision.
                              </p>
                            </div>
                            <div style={{ display: 'flex', gap: '0.75rem' }}>
                              <button 
                                onClick={() => setCabDecisionModal({ isOpen: true, decision: 'APPROVED', comments: '', submitting: false })}
                                className="btn-cg-primary"
                                style={{ backgroundColor: 'var(--status-healthy)', borderColor: 'var(--status-healthy)' }}
                              >
                                <CheckCircle2 size={16} />
                                <span>Approve Change Request</span>
                              </button>
                              <button 
                                onClick={() => setCabDecisionModal({ isOpen: true, decision: 'REJECTED', comments: '', submitting: false })}
                                className="btn-cg-secondary"
                                style={{ color: 'var(--status-critical)', borderColor: 'var(--status-critical)' }}
                              >
                                <XCircle size={16} />
                                <span>Reject Change Request</span>
                              </button>
                            </div>
                          </div>
                        )}

                        {/* If APPROVED or EMERGENCY: Deployment can start */}
                        {(changeDetail.status === 'APPROVED' || changeDetail.status === 'EMERGENCY') && (
                          <div>
                            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                              Change is approved and authorized for release window execution.
                            </p>
                            <button 
                              onClick={() => handleDeployAction('START')}
                              className="btn-cg-primary"
                            >
                              <PlayCircle size={16} />
                              <span>Start Deployment Execution</span>
                            </button>
                          </div>
                        )}

                        {/* If IN_PROGRESS */}
                        {changeDetail.status === 'IN_PROGRESS' && (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            <div style={{ padding: '0.75rem', backgroundColor: 'var(--status-info-bg)', border: '1px solid var(--status-info-border)', borderRadius: '6px' }}>
                              <p style={{ fontSize: '0.825rem', color: 'var(--text-primary)', margin: 0, fontWeight: 500 }}>
                                Deployment active. Implementation started at {formatDateLocal(changeDetail.implementation_start || '')}.
                              </p>
                            </div>
                            <div style={{ display: 'flex', gap: '0.75rem' }}>
                              <button 
                                onClick={() => handleDeployAction('COMPLETE')}
                                className="btn-cg-primary"
                                style={{ backgroundColor: 'var(--status-healthy)', borderColor: 'var(--status-healthy)' }}
                              >
                                <CheckCircle2 size={16} />
                                <span>Verify & Complete Release (Success)</span>
                              </button>
                              <button 
                                onClick={() => setRollbackModal({ isOpen: true, reason: '', notes: '', submitting: false })}
                                className="btn-cg-secondary"
                                style={{ color: 'var(--status-critical)', borderColor: 'var(--status-critical)' }}
                              >
                                <RotateCcw size={16} />
                                <span>Trigger Emergency Rollback</span>
                              </button>
                            </div>
                          </div>
                        )}

                        {/* If COMPLETED */}
                        {changeDetail.status === 'COMPLETED' && (
                          <div style={{ padding: '0.75rem', backgroundColor: 'var(--status-healthy-bg)', border: '1px solid var(--status-healthy-border)', borderRadius: '6px' }}>
                            <span style={{ fontSize: '0.825rem', color: 'var(--status-healthy)', fontWeight: 600 }}>
                              ✓ Deployment completed and operational health verified at {formatDateLocal(changeDetail.completed_at || '')}.
                            </span>
                          </div>
                        )}

                        {/* If FAILED */}
                        {changeDetail.status === 'FAILED' && (
                          <div style={{ padding: '0.75rem', backgroundColor: 'var(--status-critical-bg)', border: '1px solid var(--status-critical-border)', borderRadius: '6px' }}>
                            <span style={{ fontSize: '0.825rem', color: 'var(--status-critical)', fontWeight: 600 }}>
                              ⚠ Deployment failed. Rollback procedure was executed.
                            </span>
                          </div>
                        )}

                        {/* If CANCELLED */}
                        {changeDetail.status === 'CANCELLED' && (
                          <div style={{ padding: '0.75rem', backgroundColor: 'var(--cg-surface-secondary)', border: '1px solid var(--cg-border)', borderRadius: '6px' }}>
                            <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                              This change was rejected or cancelled by CAB.
                            </span>
                          </div>
                        )}

                      </div>

                    </div>
                  )}

                  {/* TAB 3: AUDIT TRAIL */}
                  {activeTab === 'audit' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                      <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                        Immutable Governance Audit Timeline
                      </h4>
                      {(!changeDetail.audit_trail || changeDetail.audit_trail.length === 0) ? (
                        <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>No audit events logged yet.</p>
                      ) : (
                        changeDetail.audit_trail.map((audit) => (
                          <div 
                            key={audit.id} 
                            style={{
                              padding: '0.85rem 1rem',
                              backgroundColor: 'var(--cg-surface-secondary)',
                              borderRadius: '6px',
                              borderLeft: '3px solid var(--cg-blue-primary)',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.35rem',
                              fontSize: '0.8rem'
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                                {audit.action}
                              </span>
                              <span style={{ color: 'var(--text-muted)', fontSize: '0.725rem' }}>
                                {formatDateLocal(audit.timestamp_utc)}
                              </span>
                            </div>
                            <span style={{ color: 'var(--text-secondary)' }}>
                              Actor: <strong>{audit.actor_username || 'SYSTEM'}</strong>
                            </span>
                            {audit.new_state?.status && (
                              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                                State Transition: {audit.old_state?.status || 'INIT'} → <strong>{audit.new_state.status}</strong>
                              </span>
                            )}
                            {audit.new_state?.rollback_reason && (
                              <div style={{ padding: '0.4rem', backgroundColor: 'var(--status-critical-bg)', borderRadius: '4px', color: 'var(--status-critical)', fontSize: '0.75rem' }}>
                                Reason: {audit.new_state.rollback_reason}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </>
              ) : (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                  Unable to load change details.
                </div>
              )}
            </div>

          </div>
        </div>
      )}

      {/* CAB Approval / Rejection Modal */}
      {cabDecisionModal.isOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(0,0,0,0.5)',
          backdropFilter: 'blur(3px)',
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'var(--cg-surface-elevated)',
            border: '1px solid var(--cg-border)',
            borderRadius: '8px',
            width: '100%',
            maxWidth: '480px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
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
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                {cabDecisionModal.decision === 'APPROVED' ? 'Approve Change Request' : 'Reject Change Request'}
              </h3>
              <button 
                onClick={() => setCabDecisionModal(prev => ({ ...prev, isOpen: false }))}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>
            <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', margin: 0 }}>
                Please provide formal review feedback or conditions for this decision:
              </p>
              <textarea 
                rows={4}
                placeholder="Review notes, testing evidence, or rejection rationale..."
                value={cabDecisionModal.comments}
                onChange={(e) => setCabDecisionModal(prev => ({ ...prev, comments: e.target.value }))}
                style={{
                  width: '100%',
                  padding: '0.65rem',
                  borderRadius: '6px',
                  border: '1px solid var(--cg-border)',
                  backgroundColor: 'var(--cg-surface-input)',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem'
                }}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button 
                  onClick={() => setCabDecisionModal(prev => ({ ...prev, isOpen: false }))}
                  className="btn-cg-secondary"
                  disabled={cabDecisionModal.submitting}
                >
                  Cancel
                </button>
                <button 
                  onClick={handleCabDecisionSubmit}
                  className="btn-cg-primary"
                  disabled={cabDecisionModal.submitting}
                  style={cabDecisionModal.decision === 'REJECTED' ? { backgroundColor: 'var(--status-critical)', borderColor: 'var(--status-critical)' } : {}}
                >
                  {cabDecisionModal.submitting ? 'Submitting...' : `Confirm ${cabDecisionModal.decision}`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Emergency Rollback Modal */}
      {rollbackModal.isOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(0,0,0,0.5)',
          backdropFilter: 'blur(3px)',
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'var(--cg-surface-elevated)',
            border: '1px solid var(--cg-border)',
            borderRadius: '8px',
            width: '100%',
            maxWidth: '520px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
            overflow: 'hidden'
          }}>
            <div style={{
              padding: '1rem 1.25rem',
              borderBottom: '1px solid var(--cg-border)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: 'var(--status-critical-bg)'
            }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--status-critical)', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={18} />
                Trigger Emergency Deployment Rollback
              </h3>
              <button 
                onClick={() => setRollbackModal(prev => ({ ...prev, isOpen: false }))}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>
            <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Primary Rollback Trigger / Reason *
                </label>
                <input 
                  type="text"
                  placeholder="e.g. Critical 500 error spike post-release, latency degradation"
                  value={rollbackModal.reason}
                  onChange={(e) => setRollbackModal(prev => ({ ...prev, reason: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '0.55rem',
                    borderRadius: '6px',
                    border: '1px solid var(--cg-border)',
                    backgroundColor: 'var(--cg-surface-input)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem'
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Execution Details & Notes
                </label>
                <textarea 
                  rows={3}
                  placeholder="Rollback command executed, verification metrics, downstream impact..."
                  value={rollbackModal.notes}
                  onChange={(e) => setRollbackModal(prev => ({ ...prev, notes: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '0.55rem',
                    borderRadius: '6px',
                    border: '1px solid var(--cg-border)',
                    backgroundColor: 'var(--cg-surface-input)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem'
                  }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button 
                  onClick={() => setRollbackModal(prev => ({ ...prev, isOpen: false }))}
                  className="btn-cg-secondary"
                  disabled={rollbackModal.submitting}
                >
                  Cancel
                </button>
                <button 
                  onClick={handleRollbackSubmit}
                  className="btn-cg-primary"
                  disabled={rollbackModal.submitting}
                  style={{ backgroundColor: 'var(--status-critical)', borderColor: 'var(--status-critical)' }}
                >
                  {rollbackModal.submitting ? 'Executing...' : 'Confirm Rollback'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Submit Change Request Modal */}
      {isCreateOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(0,0,0,0.5)',
          backdropFilter: 'blur(3px)',
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'var(--cg-surface-elevated)',
            border: '1px solid var(--cg-border)',
            borderRadius: '8px',
            width: '100%',
            maxWidth: '620px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
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
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <PlusCircle size={18} color="var(--cg-blue-primary)" />
                Submit New Change Request (CR)
              </h3>
              <button 
                onClick={() => setIsCreateOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateChange} style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {formError && (
                <div style={{ padding: '0.65rem', backgroundColor: 'var(--status-critical-bg)', color: 'var(--status-critical)', borderRadius: '6px', fontSize: '0.8rem' }}>
                  {formError}
                </div>
              )}

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Target Service *
                </label>
                <select 
                  value={newServiceId}
                  onChange={(e) => setNewServiceId(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.55rem',
                    borderRadius: '6px',
                    border: '1px solid var(--cg-border)',
                    backgroundColor: 'var(--cg-surface-input)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem'
                  }}
                  required
                >
                  {servicesList.map(s => (
                    <option key={s.service_id} value={s.service_id}>
                      {s.service_name} ({s.service_id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Change Title *
                </label>
                <input 
                  type="text"
                  placeholder="e.g. Upgrade payment service DB connection pool to v3.2"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.55rem',
                    borderRadius: '6px',
                    border: '1px solid var(--cg-border)',
                    backgroundColor: 'var(--cg-surface-input)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem'
                  }}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                    Type
                  </label>
                  <select 
                    value={newChangeType}
                    onChange={(e) => setNewChangeType(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.55rem',
                      borderRadius: '6px',
                      border: '1px solid var(--cg-border)',
                      backgroundColor: 'var(--cg-surface-input)',
                      color: 'var(--text-primary)',
                      fontSize: '0.85rem'
                    }}
                  >
                    <option value="NORMAL">Normal</option>
                    <option value="STANDARD">Standard</option>
                    <option value="EMERGENCY">Emergency</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                    Risk Level
                  </label>
                  <select 
                    value={newRiskLevel}
                    onChange={(e) => setNewRiskLevel(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.55rem',
                      borderRadius: '6px',
                      border: '1px solid var(--cg-border)',
                      backgroundColor: 'var(--cg-surface-input)',
                      color: 'var(--text-primary)',
                      fontSize: '0.85rem'
                    }}
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                    Impact
                  </label>
                  <select 
                    value={newImpact}
                    onChange={(e) => setNewImpact(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.55rem',
                      borderRadius: '6px',
                      border: '1px solid var(--cg-border)',
                      backgroundColor: 'var(--cg-surface-input)',
                      color: 'var(--text-primary)',
                      fontSize: '0.85rem'
                    }}
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Scope Description
                </label>
                <textarea 
                  rows={2}
                  placeholder="Detailed context and business justification..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.55rem',
                    borderRadius: '6px',
                    border: '1px solid var(--cg-border)',
                    backgroundColor: 'var(--cg-surface-input)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem'
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Implementation Plan
                </label>
                <textarea 
                  rows={2}
                  placeholder="Step-by-step commands and validation tests..."
                  value={newImplPlan}
                  onChange={(e) => setNewImplPlan(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.55rem',
                    borderRadius: '6px',
                    border: '1px solid var(--cg-border)',
                    backgroundColor: 'var(--cg-surface-input)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem'
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Backout / Rollback Plan
                </label>
                <textarea 
                  rows={2}
                  placeholder="Steps to revert changes if verification fails..."
                  value={newRollbackPlan}
                  onChange={(e) => setNewRollbackPlan(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.55rem',
                    borderRadius: '6px',
                    border: '1px solid var(--cg-border)',
                    backgroundColor: 'var(--cg-surface-input)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem'
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                    Linked Problem ID (optional)
                  </label>
                  <input 
                    type="text"
                    placeholder="e.g. PRB000001"
                    value={newProblemId}
                    onChange={(e) => setNewProblemId(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.55rem',
                      borderRadius: '6px',
                      border: '1px solid var(--cg-border)',
                      backgroundColor: 'var(--cg-surface-input)',
                      color: 'var(--text-primary)',
                      fontSize: '0.85rem'
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                    Assignment Group
                  </label>
                  <input 
                    type="text"
                    value={newAssignmentGroup}
                    onChange={(e) => setNewAssignmentGroup(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.55rem',
                      borderRadius: '6px',
                      border: '1px solid var(--cg-border)',
                      backgroundColor: 'var(--cg-surface-input)',
                      color: 'var(--text-primary)',
                      fontSize: '0.85rem'
                    }}
                  />
                </div>
              </div>

              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.825rem', color: 'var(--text-primary)', cursor: 'pointer', marginTop: '0.25rem' }}>
                <input 
                  type="checkbox" 
                  checked={newAutoSubmitCab} 
                  onChange={(e) => setNewAutoSubmitCab(e.target.checked)}
                />
                <span>Directly submit for CAB review upon creation</span>
              </label>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button 
                  type="button" 
                  onClick={() => setIsCreateOpen(false)}
                  className="btn-cg-secondary"
                  disabled={isCreating}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn-cg-primary"
                  disabled={isCreating}
                >
                  {isCreating ? 'Submitting...' : 'Register Change Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
