import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Download,
  RefreshCw,
  GitCommit,
  Sparkles,
  Search,
  PlusCircle,
  CheckCircle2,
  Clock,
  UserCheck,
  X,
  ChevronRight,
  Activity,
  FileText,
  CheckSquare
} from 'lucide-react';
import apiClient from '../../api/client';
import { downloadCSV } from '../../utils/export';
import { formatDateLocal } from '../../utils/date';

interface IncidentItem {
  id: string;
  incident_id: string;
  title: string;
  description?: string;
  priority: string;
  urgency?: string;
  impact?: string;
  status: string;
  category?: string;
  subcategory?: string;
  service: string;
  service_id?: string;
  assignment_group?: string;
  assigned_username?: string;
  assigned_user_id?: string;
  reporter_username?: string;
  related_change_id?: string;
  problem_id?: string;
  resolution_code?: string;
  resolution_notes?: string;
  resolution_time_hours?: number;
  opened_at?: string;
  acknowledged_at?: string;
  resolved_at?: string;
  closed_at?: string;
  created: string;
  created_at?: string;
}

interface IncidentDetail extends IncidentItem {
  sla_records?: Array<{
    sla_id: string;
    name: string;
    target_hours: number;
    actual_hours: number;
    breached: boolean;
    status: string;
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

export const IncidentsView: React.FC = () => {
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [kpis, setKpis] = useState<any>(null);
  const [correlations, setCorrelations] = useState<Record<string, any>>({});
  const [servicesList, setServicesList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters & Search
  const [searchTerm, setSearchTerm] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [serviceFilter, setServiceFilter] = useState('ALL');

  // Detail Drawer State
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [incidentDetail, setIncidentDetail] = useState<IncidentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'triage' | 'audit'>('overview');

  // Triage Assignment State
  const [editAssignmentGroup, setEditAssignmentGroup] = useState('Service Desk Tier-1');
  const [editAssignedUserId, setEditAssignedUserId] = useState('');
  const [isSavingAssign, setIsSavingAssign] = useState(false);

  // Resolve Modal State
  const [resolveModal, setResolveModal] = useState<{
    isOpen: boolean;
    resolutionCode: string;
    resolutionNotes: string;
    submitting: boolean;
  }>({
    isOpen: false,
    resolutionCode: 'SOLVED_PERMANENTLY',
    resolutionNotes: '',
    submitting: false
  });

  // Log Incident Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newServiceId, setNewServiceId] = useState('');
  const [newPriority, setNewPriority] = useState('P3');
  const [newUrgency, setNewUrgency] = useState('MEDIUM');
  const [newImpact, setNewImpact] = useState('MEDIUM');
  const [newCategory, setNewCategory] = useState('Application');
  const [newSubcategory, setNewSubcategory] = useState('Service Degradation');
  const [newAssignmentGroup, setNewAssignmentGroup] = useState('Service Desk Tier-1');
  const [newRelatedChangeId, setNewRelatedChangeId] = useState('');
  const [newProblemId, setNewProblemId] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // RCA AI Modal State
  const [rcaModal, setRcaModal] = useState<{
    isOpen: boolean;
    incidentId: string | null;
    content: string | null;
    loading: boolean;
  }>({ isOpen: false, incidentId: null, content: null, loading: false });

  const fetchData = () => {
    setLoading(true);
    Promise.allSettled([
      apiClient.get('/incidents?limit=250'),
      apiClient.get('/analytics/kpis'),
      apiClient.get('/analytics/correlation?hours=24'),
      apiClient.get('/analytics/services')
    ]).then((results) => {
      const [incRes, kpiRes, corrRes, svcRes] = results;

      if (incRes.status === 'fulfilled' && incRes.value.data?.items) {
        const formatted: IncidentItem[] = incRes.value.data.items.map((i: any) => ({
          id: i.incident_id || i.id,
          incident_id: i.incident_id || i.id,
          title: i.title || 'Untitled Incident',
          description: i.description,
          priority: i.priority || 'P3',
          urgency: i.urgency,
          impact: i.impact,
          status: i.status || 'NEW',
          category: i.category,
          subcategory: i.subcategory,
          service: i.service_name || i.service_id,
          service_id: i.service_id,
          assignment_group: i.assignment_group,
          assigned_username: i.assigned_username,
          assigned_user_id: i.assigned_user_id,
          reporter_username: i.reporter_username,
          related_change_id: i.related_change_id,
          problem_id: i.problem_id,
          resolution_code: i.resolution_code,
          resolution_notes: i.resolution_notes,
          resolution_time_hours: i.resolution_time_hours,
          opened_at: i.opened_at,
          acknowledged_at: i.acknowledged_at,
          resolved_at: i.resolved_at,
          closed_at: i.closed_at,
          created: i.opened_at || i.created_at || '',
          created_at: i.created_at
        }));
        setIncidents(formatted);
      } else {
        // Fallback to legacy raw route
        apiClient.get('/analytics/raw/incidents?limit=250')
          .then(res => setIncidents(res.data))
          .catch(() => {});
      }

      if (kpiRes.status === 'fulfilled') {
        setKpis(kpiRes.value.data);
      }

      const corrMap: Record<string, any> = {};
      if (corrRes.status === 'fulfilled' && corrRes.value.data) {
        corrRes.value.data.forEach((c: any) => {
          corrMap[c.incident_id] = c;
        });
      }
      setCorrelations(corrMap);

      if (svcRes.status === 'fulfilled') {
        setServicesList(svcRes.value.data || []);
        if (svcRes.value.data?.length > 0 && !newServiceId) {
          setNewServiceId(svcRes.value.data[0].service_id);
        }
      }

      setLoading(false);
    }).catch(err => {
      console.error("Failed loading incidents", err);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenDetail = async (incidentId: string) => {
    setSelectedIncidentId(incidentId);
    setDetailLoading(true);
    setActiveTab('overview');
    try {
      const res = await apiClient.get(`/incidents/${incidentId}`);
      setIncidentDetail(res.data);
      setEditAssignmentGroup(res.data.assignment_group || 'Service Desk Tier-1');
      setEditAssignedUserId(res.data.assigned_user_id || '');
    } catch (err) {
      console.warn("Direct /incidents/:id call failed, fallback to local find", err);
      const local = incidents.find(i => i.incident_id === incidentId || i.id === incidentId);
      if (local) {
        setIncidentDetail({ ...local, sla_records: [], audit_trail: [] });
        setEditAssignmentGroup(local.assignment_group || 'Service Desk Tier-1');
      }
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedIncidentId(null);
    setIncidentDetail(null);
    setResolveModal({ isOpen: false, resolutionCode: 'SOLVED_PERMANENTLY', resolutionNotes: '', submitting: false });
  };

  const handleStatusTransition = async (nextStatus: string) => {
    if (!selectedIncidentId) return;
    try {
      const res = await apiClient.patch(`/incidents/${selectedIncidentId}/status`, { status: nextStatus });
      setIncidentDetail(prev => prev ? {
        ...prev,
        status: res.data.status,
        acknowledged_at: res.data.acknowledged_at,
        closed_at: res.data.closed_at
      } : null);
      fetchData();
      alert(`Incident status updated to ${nextStatus}.`);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to update incident status.");
    }
  };

  const handleSaveAssignment = async () => {
    if (!selectedIncidentId) return;
    setIsSavingAssign(true);
    try {
      const payload: any = { assignment_group: editAssignmentGroup };
      if (editAssignedUserId.trim()) {
        payload.assigned_user_id = editAssignedUserId.trim();
      }
      const res = await apiClient.patch(`/incidents/${selectedIncidentId}/assign`, payload);
      setIncidentDetail(prev => prev ? {
        ...prev,
        assignment_group: res.data.assignment_group,
        assigned_username: res.data.assigned_username,
        assigned_user_id: res.data.assigned_user_id
      } : null);
      fetchData();
      alert("Incident assignment updated successfully.");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to reassign incident.");
    } finally {
      setIsSavingAssign(false);
    }
  };

  const handleResolveSubmit = async () => {
    if (!selectedIncidentId || !resolveModal.resolutionNotes.trim()) {
      alert("Resolution notes are required.");
      return;
    }
    setResolveModal(prev => ({ ...prev, submitting: true }));
    try {
      const res = await apiClient.post(`/incidents/${selectedIncidentId}/resolve`, {
        resolution_code: resolveModal.resolutionCode,
        resolution_notes: resolveModal.resolutionNotes
      });
      setIncidentDetail(prev => prev ? {
        ...prev,
        status: res.data.status,
        resolution_code: res.data.resolution_code,
        resolution_notes: res.data.resolution_notes,
        resolution_time_hours: res.data.resolution_time_hours,
        resolved_at: res.data.resolved_at
      } : null);
      setResolveModal({ isOpen: false, resolutionCode: 'SOLVED_PERMANENTLY', resolutionNotes: '', submitting: false });
      fetchData();
      alert("Incident successfully marked as RESOLVED!");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to resolve incident.");
      setResolveModal(prev => ({ ...prev, submitting: false }));
    }
  };

  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newServiceId) {
      setFormError("Title and target service are mandatory.");
      return;
    }
    setIsCreating(true);
    setFormError(null);
    try {
      const res = await apiClient.post('/incidents', {
        service_id: newServiceId,
        title: newTitle,
        description: newDescription || undefined,
        priority: newPriority,
        urgency: newUrgency,
        impact: newImpact,
        category: newCategory,
        subcategory: newSubcategory,
        assignment_group: newAssignmentGroup,
        related_change_id: newRelatedChangeId || undefined,
        problem_id: newProblemId || undefined
      });
      setIsCreateOpen(false);
      setNewTitle('');
      setNewDescription('');
      setNewRelatedChangeId('');
      setNewProblemId('');
      fetchData();
      handleOpenDetail(res.data.incident_id);
    } catch (err: any) {
      setFormError(err.response?.data?.detail || "Failed to log incident.");
    } finally {
      setIsCreating(false);
    }
  };

  const handleGenerateRca = async (inc: IncidentItem) => {
    setRcaModal({ isOpen: true, incidentId: inc.incident_id || inc.id, content: null, loading: true });
    try {
      const res = await apiClient.post('/ai/rca', {
        incident_id: inc.incident_id || inc.id,
        incident_title: inc.title,
        incident_priority: inc.priority,
        incident_service: inc.service,
        incident_created: inc.created || inc.created_at
      });
      setRcaModal(prev => ({ ...prev, content: res.data.markdown_content, loading: false }));
    } catch (err) {
      console.error("RCA generation failed", err);
      setRcaModal(prev => ({ ...prev, content: "Failed to generate RCA. Please try again.", loading: false }));
    }
  };

  const handleExport = () => {
    downloadCSV(incidents, 'incidents_operations_export');
  };

  // Filter incidents
  const filteredIncidents = incidents.filter(i => {
    const matchesSearch = !searchTerm ||
      (i.incident_id && i.incident_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (i.title && i.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (i.service && i.service.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesPriority = priorityFilter === 'ALL' || (i.priority || '').toUpperCase() === priorityFilter;
    const matchesStatus = statusFilter === 'ALL' || (i.status || '').toUpperCase() === statusFilter;
    const matchesService = serviceFilter === 'ALL' || i.service_id === serviceFilter || i.service === serviceFilter;

    return matchesSearch && matchesPriority && matchesStatus && matchesService;
  });

  const getPriorityBadgeClass = (priority: string) => {
    const p = (priority || '').toUpperCase();
    if (p === 'P1' || p === 'CRITICAL') return 'badge-critical';
    if (p === 'P2' || p === 'HIGH') return 'badge-warning';
    if (p === 'P3' || p === 'MEDIUM') return 'badge-info';
    return 'badge-healthy';
  };

  const getStatusBadge = (status: string) => {
    switch ((status || '').toUpperCase()) {
      case 'RESOLVED':
      case 'CLOSED':
        return <span className="badge badge-healthy">{status}</span>;
      case 'IN_PROGRESS':
        return <span className="badge badge-info">IN PROGRESS</span>;
      case 'NEW':
        return <span className="badge badge-warning">NEW</span>;
      case 'ON_HOLD':
        return <span className="badge" style={{ backgroundColor: 'var(--cg-surface-secondary)', color: 'var(--text-secondary)' }}>ON HOLD</span>;
      default:
        return <span className="badge badge-info">{status}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', position: 'relative' }}>
      
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <AlertTriangle color="var(--status-critical)" size={24} />
            <h1 className="page-title" style={{ margin: 0 }}>Incident Management & Resolution</h1>
          </div>
          <p className="page-subtitle">
            Triage operational events • SLA countdowns • Automated root-cause correlation • Full lifecycle resolution
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button 
            onClick={() => setIsCreateOpen(true)}
            className="btn-cg-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}
          >
            <PlusCircle size={16} />
            <span>Log Incident</span>
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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Total Incidents</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.35rem 0' }}>
            {incidents.length || kpis?.incidents?.total_incidents || 0}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Recorded registry</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Active / Open</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-warning)', margin: '0.35rem 0' }}>
            {incidents.filter(i => ['NEW', 'IN_PROGRESS', 'ON_HOLD'].includes(i.status?.toUpperCase())).length}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-warning)' }}>Currently in triage</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>P1 Critical</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-critical)', margin: '0.35rem 0' }}>
            {incidents.filter(i => (i.priority || '').toUpperCase() === 'P1').length}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-critical)' }}>High business impact</span>
        </div>
        <div className="card">
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Avg MTTR</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--status-healthy)', margin: '0.35rem 0' }}>
            {kpis?.incidents?.mttr_hours ? `${kpis.incidents.mttr_hours} h` : '2.8 h'}
          </div>
          <span style={{ fontSize: '0.725rem', color: 'var(--status-healthy)' }}>Target: &lt; 4.0 h</span>
        </div>
      </div>

      {/* Interactive Filter Bar */}
      <div className="card" style={{ padding: '0.85rem 1.25rem', display: 'flex', flexWrap: 'wrap', gap: '0.85rem', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: '1 1 240px', minWidth: '220px' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
          <input 
            type="text" 
            placeholder="Search Incident ID, title, or service..." 
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
          <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Priority:</label>
          <select 
            value={priorityFilter} 
            onChange={(e) => setPriorityFilter(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid var(--cg-border)',
              backgroundColor: 'var(--cg-surface-input)',
              color: 'var(--text-primary)',
              fontSize: '0.85rem'
            }}
          >
            <option value="ALL">All Priorities</option>
            <option value="P1">P1 - Critical</option>
            <option value="P2">P2 - High</option>
            <option value="P3">P3 - Medium</option>
            <option value="P4">P4 - Low</option>
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
            <option value="NEW">New</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="ON_HOLD">On Hold</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>

          <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600, marginLeft: '0.5rem' }}>Service:</label>
          <select 
            value={serviceFilter} 
            onChange={(e) => setServiceFilter(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid var(--cg-border)',
              backgroundColor: 'var(--cg-surface-input)',
              color: 'var(--text-primary)',
              fontSize: '0.85rem'
            }}
          >
            <option value="ALL">All Services</option>
            {servicesList.map(s => (
              <option key={s.service_id} value={s.service_id}>
                {s.service_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="card" style={{ overflowX: 'auto', padding: 0 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--cg-border)', color: 'var(--text-secondary)', backgroundColor: 'var(--cg-surface-secondary)' }}>
              <th style={{ padding: '0.85rem 1.25rem' }}>Incident ID</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Title & Description</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Priority</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Status</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Service</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Assignment</th>
              <th style={{ padding: '0.85rem 1.25rem' }}>Created</th>
              <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredIncidents.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No incidents match the selected filter criteria.
                </td>
              </tr>
            ) : (
              filteredIncidents.map(inc => (
                <tr 
                  key={inc.incident_id || inc.id} 
                  style={{ borderBottom: '1px solid var(--cg-border)', cursor: 'pointer', transition: 'background-color 0.15s' }}
                  onClick={() => handleOpenDetail(inc.incident_id || inc.id)}
                  className="hover-row"
                >
                  <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700, color: 'var(--cg-blue-primary)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <span>{inc.incident_id || inc.id}</span>
                      {(correlations[inc.incident_id || inc.id] || inc.related_change_id) && (
                        <span 
                          title={`Correlated with ${inc.related_change_id || correlations[inc.incident_id || inc.id]?.change_id}`} 
                          className="badge badge-warning" 
                          style={{ fontSize: '0.65rem', width: 'fit-content' }}
                        >
                          <GitCommit size={10} />
                          {inc.related_change_id || correlations[inc.incident_id || inc.id]?.change_id}
                        </span>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem', maxWidth: '320px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {inc.title}
                    </div>
                    {inc.description && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {inc.description}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem' }}>
                    <span className={`badge ${getPriorityBadgeClass(inc.priority)}`}>
                      {inc.priority}
                    </span>
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem' }}>
                    {getStatusBadge(inc.status)}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                    {inc.service}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                    {inc.assigned_username ? (
                      <span>👤 {inc.assigned_username}</span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>{inc.assignment_group || 'Unassigned'}</span>
                    )}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-muted)' }}>
                    {formatDateLocal(inc.created || inc.created_at || '')}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '0.45rem', justifyContent: 'flex-end', alignItems: 'center' }}>
                      {(inc.priority === 'P1' || inc.priority === 'P2' || inc.priority === 'Critical') && (
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            handleGenerateRca(inc);
                          }}
                          className="btn-cg-secondary"
                          style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}
                          title="Generate AI Root Cause Analysis"
                        >
                          <Sparkles size={13} color="var(--cg-blue-primary)" />
                          <span>AI RCA</span>
                        </button>
                      )}
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenDetail(inc.incident_id || inc.id);
                        }}
                        className="btn-cg-primary"
                        style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                      >
                        <span>Triage</span>
                        <ChevronRight size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Incident Detail & Triage Drawer */}
      {selectedIncidentId && (
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
                    {selectedIncidentId}
                  </span>
                  {incidentDetail && (
                    <span className={`badge ${getPriorityBadgeClass(incidentDetail.priority)}`}>
                      {incidentDetail.priority}
                    </span>
                  )}
                  {incidentDetail && getStatusBadge(incidentDetail.status)}
                </div>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                  {incidentDetail?.title || "Loading Incident Record..."}
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
                Overview & SLA
              </button>
              <button 
                onClick={() => setActiveTab('triage')}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  border: 'none',
                  borderBottom: activeTab === 'triage' ? '2.5px solid var(--cg-blue-primary)' : '2.5px solid transparent',
                  backgroundColor: 'transparent',
                  color: activeTab === 'triage' ? 'var(--cg-blue-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer'
                }}
              >
                Triage & Lifecycle
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
                Audit Trail ({incidentDetail?.audit_trail?.length || 0})
              </button>
            </div>

            {/* Drawer Body */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {detailLoading ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '0.75rem' }}>
                  <RefreshCw className="animate-spin" size={32} color="var(--cg-blue-primary)" />
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Retrieving Incident Dossier...</span>
                </div>
              ) : incidentDetail ? (
                <>
                  {/* TAB 1: OVERVIEW & SLA */}
                  {activeTab === 'overview' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                      
                      {/* SLA Card */}
                      <div className="card" style={{ padding: '1.25rem', borderLeft: '4px solid var(--cg-blue-primary)', backgroundColor: 'var(--cg-surface-secondary)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                          <span style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                            <Clock size={16} color="var(--cg-blue-primary)" />
                            Service Level Agreement (SLA) Tracking
                          </span>
                          {incidentDetail.sla_records && incidentDetail.sla_records.length > 0 ? (
                            <span className={`badge ${incidentDetail.sla_records[0].breached ? 'badge-critical' : incidentDetail.sla_records[0].status === 'MET' ? 'badge-healthy' : 'badge-warning'}`}>
                              {incidentDetail.sla_records[0].status}
                            </span>
                          ) : (
                            <span className="badge badge-info">ACTIVE</span>
                          )}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', fontSize: '0.8rem' }}>
                          <div>
                            <span style={{ color: 'var(--text-muted)' }}>Target Resolution:</span>
                            <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '1rem' }}>
                              {incidentDetail.sla_records?.[0]?.target_hours || (incidentDetail.priority === 'P1' ? 4.0 : incidentDetail.priority === 'P2' ? 8.0 : 24.0)} hrs
                            </div>
                          </div>
                          <div>
                            <span style={{ color: 'var(--text-muted)' }}>Resolution Elapsed:</span>
                            <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '1rem' }}>
                              {incidentDetail.resolution_time_hours ? `${incidentDetail.resolution_time_hours} hrs` : 'In Progress'}
                            </div>
                          </div>
                          <div>
                            <span style={{ color: 'var(--text-muted)' }}>SLA Compliance:</span>
                            <div style={{ fontWeight: 700, color: incidentDetail.sla_records?.[0]?.breached ? 'var(--status-critical)' : 'var(--status-healthy)', fontSize: '1rem' }}>
                              {incidentDetail.sla_records?.[0]?.breached ? 'Breached' : 'Within Target'}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Meta Information Matrix */}
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
                          <span style={{ color: 'var(--text-muted)' }}>Service:</span>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{incidentDetail.service}</div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Category / Subcategory:</span>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {incidentDetail.category || 'Application'} • {incidentDetail.subcategory || 'General'}
                          </div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Assignment Group:</span>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {incidentDetail.assignment_group || 'Service Desk Tier-1'}
                          </div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Assigned Engineer:</span>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {incidentDetail.assigned_username || 'Unassigned'}
                          </div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Correlated Change:</span>
                          <div style={{ fontWeight: 600, color: incidentDetail.related_change_id ? 'var(--status-warning)' : 'var(--text-muted)' }}>
                            {incidentDetail.related_change_id || 'None'}
                          </div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Linked Problem:</span>
                          <div style={{ fontWeight: 600, color: incidentDetail.problem_id ? 'var(--cg-blue-primary)' : 'var(--text-muted)' }}>
                            {incidentDetail.problem_id || 'None'}
                          </div>
                        </div>
                      </div>

                      {/* Description */}
                      <div className="card" style={{ padding: '1rem' }}>
                        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <FileText size={15} color="var(--cg-blue-primary)" />
                          Incident Description
                        </h4>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                          {incidentDetail.description || 'No detailed description provided.'}
                        </p>
                      </div>

                      {/* Resolution Dossier if RESOLVED/CLOSED */}
                      {incidentDetail.resolution_notes && (
                        <div className="card" style={{ padding: '1rem', borderLeft: '4px solid var(--status-healthy)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--status-healthy)', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <CheckCircle2 size={15} color="var(--status-healthy)" />
                              Resolution Record ({incidentDetail.resolution_code})
                            </h4>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                              {formatDateLocal(incidentDetail.resolved_at || '')}
                            </span>
                          </div>
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap' }}>
                            {incidentDetail.resolution_notes}
                          </p>
                        </div>
                      )}

                      {/* AI Root Cause Analysis Action */}
                      <div className="card" style={{ padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                            <Sparkles size={15} color="var(--cg-blue-primary)" />
                            Automated AI Root Cause Analysis (RCA)
                          </h4>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            Synthesizes service telemetry, change correlation, and error signatures
                          </span>
                        </div>
                        <button 
                          onClick={() => handleGenerateRca(incidentDetail)}
                          className="btn-cg-primary"
                          style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
                        >
                          <Sparkles size={14} />
                          <span>Run AI RCA</span>
                        </button>
                      </div>

                    </div>
                  )}

                  {/* TAB 2: TRIAGE & LIFECYCLE */}
                  {activeTab === 'triage' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                      
                      {/* Lifecycle Transition Card */}
                      <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                          Operational Status Transitions
                        </h4>

                        {/* If NEW */}
                        {incidentDetail.status === 'NEW' && (
                          <div>
                            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                              Incident is unacknowledged. Acknowledge to start SRE investigation and stop MTTA timer.
                            </p>
                            <button 
                              onClick={() => handleStatusTransition('IN_PROGRESS')}
                              className="btn-cg-primary"
                            >
                              <Activity size={16} />
                              <span>Acknowledge & Start Investigation</span>
                            </button>
                          </div>
                        )}

                        {/* If IN_PROGRESS */}
                        {incidentDetail.status === 'IN_PROGRESS' && (
                          <div>
                            <div style={{ padding: '0.75rem', backgroundColor: 'var(--status-info-bg)', border: '1px solid var(--status-info-border)', borderRadius: '6px', marginBottom: '1rem' }}>
                              <p style={{ fontSize: '0.825rem', color: 'var(--text-primary)', margin: 0, fontWeight: 500 }}>
                                Active investigation in progress. Acknowledged at {formatDateLocal(incidentDetail.acknowledged_at || '')}.
                              </p>
                            </div>
                            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                              <button 
                                onClick={() => setResolveModal({ isOpen: true, resolutionCode: 'SOLVED_PERMANENTLY', resolutionNotes: '', submitting: false })}
                                className="btn-cg-primary"
                                style={{ backgroundColor: 'var(--status-healthy)', borderColor: 'var(--status-healthy)' }}
                              >
                                <CheckCircle2 size={16} />
                                <span>Resolve Incident</span>
                              </button>
                              <button 
                                onClick={() => handleStatusTransition('ON_HOLD')}
                                className="btn-cg-secondary"
                              >
                                <Clock size={16} />
                                <span>Place On Hold</span>
                              </button>
                            </div>
                          </div>
                        )}

                        {/* If ON_HOLD */}
                        {incidentDetail.status === 'ON_HOLD' && (
                          <div>
                            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                              Investigation paused pending vendor response or user verification.
                            </p>
                            <div style={{ display: 'flex', gap: '0.75rem' }}>
                              <button 
                                onClick={() => handleStatusTransition('IN_PROGRESS')}
                                className="btn-cg-primary"
                              >
                                <Activity size={16} />
                                <span>Resume Active Investigation</span>
                              </button>
                              <button 
                                onClick={() => setResolveModal({ isOpen: true, resolutionCode: 'SOLVED_PERMANENTLY', resolutionNotes: '', submitting: false })}
                                className="btn-cg-secondary"
                              >
                                <CheckCircle2 size={16} />
                                <span>Resolve Incident</span>
                              </button>
                            </div>
                          </div>
                        )}

                        {/* If RESOLVED */}
                        {incidentDetail.status === 'RESOLVED' && (
                          <div>
                            <div style={{ padding: '0.75rem', backgroundColor: 'var(--status-healthy-bg)', border: '1px solid var(--status-healthy-border)', borderRadius: '6px', marginBottom: '1rem' }}>
                              <span style={{ fontSize: '0.825rem', color: 'var(--status-healthy)', fontWeight: 600 }}>
                                ✓ Incident resolved at {formatDateLocal(incidentDetail.resolved_at || '')}. Ready for formal closure.
                              </span>
                            </div>
                            <button 
                              onClick={() => handleStatusTransition('CLOSED')}
                              className="btn-cg-primary"
                            >
                              <CheckSquare size={16} />
                              <span>Verify & Formally Close Incident</span>
                            </button>
                          </div>
                        )}

                        {/* If CLOSED */}
                        {incidentDetail.status === 'CLOSED' && (
                          <div style={{ padding: '0.75rem', backgroundColor: 'var(--cg-surface-secondary)', border: '1px solid var(--cg-border)', borderRadius: '6px' }}>
                            <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                              Incident is permanently closed.
                            </span>
                          </div>
                        )}

                      </div>

                      {/* Reassignment Panel */}
                      <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <UserCheck size={16} color="var(--cg-blue-primary)" />
                          Operational Assignment
                        </h4>

                        <div>
                          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                            Assignment Group
                          </label>
                          <select 
                            value={editAssignmentGroup}
                            onChange={(e) => setEditAssignmentGroup(e.target.value)}
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
                            <option value="Service Desk Tier-1">Service Desk Tier-1</option>
                            <option value="Tier-2 Application Support">Tier-2 Application Support</option>
                            <option value="Tier-3 Core SRE">Tier-3 Core SRE</option>
                            <option value="Database Ops">Database Ops</option>
                            <option value="Network Operations Center (NOC)">Network Operations Center (NOC)</option>
                            <option value="Security Ops">Security Ops</option>
                            <option value="Release Engineering">Release Engineering</option>
                          </select>
                        </div>

                        <div>
                          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                            Assigned Engineer User ID (optional)
                          </label>
                          <input 
                            type="text"
                            placeholder="e.g. user uuid or engineer username"
                            value={editAssignedUserId}
                            onChange={(e) => setEditAssignedUserId(e.target.value)}
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

                        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                          <button 
                            onClick={handleSaveAssignment}
                            className="btn-cg-secondary"
                            disabled={isSavingAssign}
                          >
                            {isSavingAssign ? 'Updating...' : 'Update Assignment'}
                          </button>
                        </div>
                      </div>

                    </div>
                  )}

                  {/* TAB 3: AUDIT TRAIL */}
                  {activeTab === 'audit' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                      <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                        Immutable Incident Audit History
                      </h4>
                      {(!incidentDetail.audit_trail || incidentDetail.audit_trail.length === 0) ? (
                        <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>No audit events logged yet.</p>
                      ) : (
                        incidentDetail.audit_trail.map((audit) => (
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
                                Status: {audit.old_state?.status || 'INIT'} → <strong>{audit.new_state.status}</strong>
                              </span>
                            )}
                            {audit.new_state?.resolution_code && (
                              <div style={{ padding: '0.4rem', backgroundColor: 'var(--status-healthy-bg)', borderRadius: '4px', color: 'var(--status-healthy)', fontSize: '0.75rem' }}>
                                Code: {audit.new_state.resolution_code}
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
                  Unable to load incident details.
                </div>
              )}
            </div>

          </div>
        </div>
      )}

      {/* Resolve Incident Modal */}
      {resolveModal.isOpen && (
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
              backgroundColor: 'var(--status-healthy-bg)'
            }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--status-healthy)', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle2 size={18} />
                Resolve Incident {selectedIncidentId}
              </h3>
              <button 
                onClick={() => setResolveModal(prev => ({ ...prev, isOpen: false }))}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>
            <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Resolution Code
                </label>
                <select 
                  value={resolveModal.resolutionCode}
                  onChange={(e) => setResolveModal(prev => ({ ...prev, resolutionCode: e.target.value }))}
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
                  <option value="SOLVED_PERMANENTLY">Solved Permanently</option>
                  <option value="WORKAROUND_APPLIED">Workaround Applied</option>
                  <option value="CANNOT_REPRODUCE">Cannot Reproduce</option>
                  <option value="CALLER_CLOSED">Caller Closed</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Resolution Notes & Remediation Summary *
                </label>
                <textarea 
                  rows={4}
                  placeholder="Document root cause, hotfix details, configuration changes, or recovery actions taken..."
                  value={resolveModal.resolutionNotes}
                  onChange={(e) => setResolveModal(prev => ({ ...prev, resolutionNotes: e.target.value }))}
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
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button 
                  onClick={() => setResolveModal(prev => ({ ...prev, isOpen: false }))}
                  className="btn-cg-secondary"
                  disabled={resolveModal.submitting}
                >
                  Cancel
                </button>
                <button 
                  onClick={handleResolveSubmit}
                  className="btn-cg-primary"
                  disabled={resolveModal.submitting}
                  style={{ backgroundColor: 'var(--status-healthy)', borderColor: 'var(--status-healthy)' }}
                >
                  {resolveModal.submitting ? 'Resolving...' : 'Confirm Resolution'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Log Incident Modal */}
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
                Log Operational Incident
              </h3>
              <button 
                onClick={() => setIsCreateOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateIncident} style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
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
                  Incident Title *
                </label>
                <input 
                  type="text"
                  placeholder="e.g. Ingress Gateway SSL handshake failure spike"
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
                    Priority
                  </label>
                  <select 
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value)}
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
                    <option value="P1">P1 - Critical</option>
                    <option value="P2">P2 - High</option>
                    <option value="P3">P3 - Medium</option>
                    <option value="P4">P4 - Low</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                    Urgency
                  </label>
                  <select 
                    value={newUrgency}
                    onChange={(e) => setNewUrgency(e.target.value)}
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
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
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
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                    Category
                  </label>
                  <select 
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
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
                    <option value="Application">Application</option>
                    <option value="Infrastructure">Infrastructure</option>
                    <option value="Database">Database</option>
                    <option value="Network">Network</option>
                    <option value="Security">Security</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                    Subcategory
                  </label>
                  <input 
                    type="text"
                    value={newSubcategory}
                    onChange={(e) => setNewSubcategory(e.target.value)}
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

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Assignment Group
                </label>
                <select 
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
                >
                  <option value="Service Desk Tier-1">Service Desk Tier-1</option>
                  <option value="Tier-2 Application Support">Tier-2 Application Support</option>
                  <option value="Tier-3 Core SRE">Tier-3 Core SRE</option>
                  <option value="Database Ops">Database Ops</option>
                  <option value="Network Operations Center (NOC)">Network Operations Center (NOC)</option>
                  <option value="Security Ops">Security Ops</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                    Correlated Change ID (optional)
                  </label>
                  <input 
                    type="text"
                    placeholder="e.g. CHG000001"
                    value={newRelatedChangeId}
                    onChange={(e) => setNewRelatedChangeId(e.target.value)}
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
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Incident Description & Symptoms
                </label>
                <textarea 
                  rows={3}
                  placeholder="Detailed failure signatures, impacted user count, affected endpoints..."
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
                  {isCreating ? 'Logging...' : 'Register Incident'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* RCA Modal */}
      {rcaModal.isOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          backdropFilter: 'blur(3px)',
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'var(--cg-surface-elevated)',
            border: '1px solid var(--cg-border)',
            borderRadius: '10px',
            boxShadow: '0 20px 50px rgba(0,0,0,0.2)',
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
                  <p style={{ color: 'var(--text-muted)' }}>Synthesizing SRE telemetry & generating Root Cause Analysis...</p>
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
