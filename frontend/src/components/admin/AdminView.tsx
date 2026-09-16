import React, { useState } from 'react';
import apiClient from '../../api/client';
import {
  Settings,
  Trash2,
  RefreshCw,
  FileText,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Database,
  ShieldAlert,
  Server
} from 'lucide-react';

export const AdminView: React.FC = () => {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [confirmInput, setConfirmInput] = useState('');

  const handleRemoveAllData = async () => {
    if (confirmInput.trim().toUpperCase() !== 'REMOVE ALL DATA') {
      setStatusMessage({ type: 'error', text: 'Please type "REMOVE ALL DATA" to confirm database wipe.' });
      return;
    }
    
    setLoadingAction('delete');
    setStatusMessage(null);
    setShowDeleteModal(false);
    setConfirmInput('');

    try {
      const res = await apiClient.post('/admin/remove-all-data');
      setStatusMessage({ type: 'success', text: res.data.message || 'All operational data removed successfully!' });
    } catch (err: any) {
      console.error("Failed to remove all data", err);
      setStatusMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to remove all data from database.' });
    } finally {
      setLoadingAction(null);
    }
  };

  const handleReseedData = async () => {
    setLoadingAction('reseed');
    setStatusMessage(null);
    try {
      const res = await apiClient.post('/admin/reseed-data');
      if (res.data.status === 'SUCCESS') {
        setStatusMessage({ type: 'success', text: res.data.message || 'Re-seeding completed with fresh July 2026 data!' });
        setLoadingAction(null);
        return;
      }

      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await apiClient.get('/admin/reseed-status');
          if (statusRes.data.status === 'SUCCESS') {
            clearInterval(pollInterval);
            setStatusMessage({ type: 'success', text: statusRes.data.message || 'Re-seeding completed with fresh July 2026 data!' });
            setLoadingAction(null);
          } else if (statusRes.data.status === 'FAILED') {
            clearInterval(pollInterval);
            setStatusMessage({ type: 'error', text: statusRes.data.message || statusRes.data.error || 'Failed re-seeding system data.' });
            setLoadingAction(null);
          }
        } catch (pollErr: any) {
          clearInterval(pollInterval);
          setStatusMessage({ type: 'error', text: 'Error checking re-seed status.' });
          setLoadingAction(null);
        }
      }, 1500);
    } catch (err: any) {
      console.error("Re-seeding failed", err);
      setStatusMessage({ type: 'error', text: err.response?.data?.detail || 'Failed re-seeding system data.' });
      setLoadingAction(null);
    }
  };

  const handlePurgeReports = async () => {
    setLoadingAction('purge_reports');
    setStatusMessage(null);
    try {
      const res = await apiClient.post('/admin/purge-reports');
      setStatusMessage({ type: 'success', text: res.data.message || 'Report documents purged successfully.' });
    } catch (err: any) {
      console.error("Purge reports failed", err);
      setStatusMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to purge report files.' });
    } finally {
      setLoadingAction(null);
    }
  };

  const handleClearSchedulerLogs = async () => {
    setLoadingAction('clear_scheduler');
    setStatusMessage(null);
    try {
      const res = await apiClient.post('/admin/clear-scheduler-history');
      setStatusMessage({ type: 'success', text: res.data.message || 'Scheduler history cleared successfully.' });
    } catch (err: any) {
      console.error("Clear scheduler history failed", err);
      setStatusMessage({ type: 'error', text: err.response?.data?.detail || 'Failed clearing scheduler history.' });
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Settings color="var(--cg-blue-primary)" size={24} />
            System Administration & Control Center
          </h1>
          <p className="page-subtitle">
            Execute administrative operations, database maintenance, data purges, and environment re-seeding
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.45rem 0.85rem', borderRadius: '8px', backgroundColor: 'var(--status-healthy-bg)', border: '1px solid var(--status-healthy-border)' }}>
          <Server size={15} color="var(--status-healthy)" />
          <span style={{ fontSize: '0.8rem', color: 'var(--status-healthy)', fontWeight: 600 }}>System Status: Operational</span>
        </div>
      </div>

      {/* Global Action Status Alert Banner */}
      {statusMessage && (
        <div className="card" style={{
          backgroundColor: statusMessage.type === 'success' ? 'var(--status-healthy-bg)' : 'var(--status-critical-bg)',
          border: statusMessage.type === 'success' ? '1px solid var(--status-healthy-border)' : '1px solid var(--status-critical-border)',
          color: statusMessage.type === 'success' ? 'var(--status-healthy)' : 'var(--status-critical)',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.9rem',
          fontWeight: 600
        }}>
          {statusMessage.type === 'success' ? <CheckCircle2 size={20} /> : <AlertTriangle size={20} />}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Admin Actions Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
        
        {/* Danger Zone Card - Remove All Data */}
        <div className="card" style={{
          backgroundColor: 'var(--status-critical-bg)',
          border: '1px solid var(--status-critical-border)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '1.25rem'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.75rem' }}>
              <div style={{ padding: '0.45rem', borderRadius: '6px', backgroundColor: 'var(--cg-surface-card)', color: 'var(--status-critical)', border: '1px solid var(--status-critical-border)' }}>
                <ShieldAlert size={20} />
              </div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--status-critical)', margin: 0 }}>Remove All Data (Database Wipe)</h3>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Completely purges all operational records including Incidents, Problems, Changes, SLA records, and Scheduler Runs from the SQLite database.
            </p>
          </div>

          <button
            onClick={() => setShowDeleteModal(true)}
            disabled={loadingAction === 'delete'}
            className="btn-cg-danger"
            style={{ width: '100%' }}
          >
            {loadingAction === 'delete' ? <RefreshCw className="animate-spin" size={16} /> : <Trash2 size={16} />}
            <span>{loadingAction === 'delete' ? "Wiping Database..." : "Remove All Data"}</span>
          </button>
        </div>

        {/* Data Re-seeding Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.75rem' }}>
              <div style={{ padding: '0.45rem', borderRadius: '6px', backgroundColor: 'var(--cg-blue-soft)', color: 'var(--cg-blue-primary)' }}>
                <Database size={20} />
              </div>
              <h3 className="card-title" style={{ margin: 0 }}>Re-seed System Datasets</h3>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Runs the synthetic data generator to initialize SQLite schema with fresh deterministic July 2026 operational datasets.
            </p>
          </div>

          <button
            onClick={handleReseedData}
            disabled={loadingAction === 'reseed'}
            className="btn-cg-primary"
            style={{ width: '100%' }}
          >
            {loadingAction === 'reseed' ? <RefreshCw className="animate-spin" size={16} /> : <RefreshCw size={16} />}
            <span>{loadingAction === 'reseed' ? "Re-seeding Data..." : "Re-seed July Datasets"}</span>
          </button>
        </div>

        {/* Report Storage Maintenance Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.75rem' }}>
              <div style={{ padding: '0.45rem', borderRadius: '6px', backgroundColor: 'var(--cg-surface-secondary)', color: 'var(--cg-blue-primary)', border: '1px solid var(--cg-border)' }}>
                <FileText size={20} />
              </div>
              <h3 className="card-title" style={{ margin: 0 }}>Purge Generated Reports</h3>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Deletes all generated Markdown (`.md`) and PDF (`.pdf`) executive operational report files from server disk storage.
            </p>
          </div>

          <button
            onClick={handlePurgeReports}
            disabled={loadingAction === 'purge_reports'}
            className="btn-cg-secondary"
            style={{ width: '100%' }}
          >
            {loadingAction === 'purge_reports' ? <RefreshCw className="animate-spin" size={16} /> : <Trash2 size={16} />}
            <span>{loadingAction === 'purge_reports' ? "Purging Files..." : "Purge Report Storage"}</span>
          </button>
        </div>

        {/* Audit Log Cleanup Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.75rem' }}>
              <div style={{ padding: '0.45rem', borderRadius: '6px', backgroundColor: 'var(--status-warning-bg)', color: 'var(--status-warning)' }}>
                <Clock size={20} />
              </div>
              <h3 className="card-title" style={{ margin: 0 }}>Clear Execution Audit History</h3>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Resets the background scheduler execution audit log records stored in the SQLite database table (`scheduler_runs`).
            </p>
          </div>

          <button
            onClick={handleClearSchedulerLogs}
            disabled={loadingAction === 'clear_scheduler'}
            className="btn-cg-secondary"
            style={{ width: '100%' }}
          >
            {loadingAction === 'clear_scheduler' ? <RefreshCw className="animate-spin" size={16} /> : <Trash2 size={16} />}
            <span>{loadingAction === 'clear_scheduler' ? "Clearing History..." : "Clear Execution History"}</span>
          </button>
        </div>

      </div>

      {/* Confirmation Modal for Remove All Data */}
      {showDeleteModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(23, 43, 58, 0.45)',
          backdropFilter: 'blur(3px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem'
        }}>
          <div className="card" style={{
            maxWidth: '480px',
            width: '100%',
            backgroundColor: 'var(--cg-surface-elevated)',
            border: '1px solid var(--status-critical-border)',
            padding: '2rem',
            borderRadius: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.25rem',
            boxShadow: '0 12px 36px rgba(0,0,0,0.15)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--status-critical)' }}>
              <AlertTriangle size={24} />
              <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>Confirm Data Removal</h2>
            </div>

            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
              Are you sure you want to <strong>REMOVE ALL DATA</strong>? This will permanently delete all Incidents, Problems, Changes, SLA records, and Scheduler Runs from your SQLite database.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Type <code style={{ color: 'var(--status-critical)', fontWeight: 700 }}>REMOVE ALL DATA</code> to confirm:
              </label>
              <input
                type="text"
                value={confirmInput}
                onChange={e => setConfirmInput(e.target.value)}
                placeholder="REMOVE ALL DATA"
                style={{
                  padding: '0.65rem 0.85rem',
                  borderRadius: '6px',
                  border: '1px solid var(--cg-border)',
                  backgroundColor: 'var(--cg-surface-card)',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem',
                  outline: 'none'
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
              <button
                onClick={() => { setShowDeleteModal(false); setConfirmInput(''); }}
                className="btn-cg-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleRemoveAllData}
                className="btn-cg-danger"
              >
                Permanently Delete All Data
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
