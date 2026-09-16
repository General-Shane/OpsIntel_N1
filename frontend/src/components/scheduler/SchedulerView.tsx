import React, { useEffect, useState } from 'react';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import {
  Clock,
  Play,
  RefreshCw,
  Plus,
  Pause,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Activity
} from 'lucide-react';

interface ScheduledJobItem {
  id: string;
  name: string;
  description: string | null;
  job_type: string;
  status: string;
  cron_expression: string;
  timezone: string;
  payload: any;
  owner_username: string | null;
  next_run_at: string | null;
  last_run_at: string | null;
  last_success_at: string | null;
  last_failure_at: string | null;
  max_retries: number;
  retry_delay_seconds: number;
  concurrency_policy: string;
}

interface JobExecutionItem {
  id: string;
  job_id: string | null;
  job_name: string;
  job_type: string;
  run_id: string;
  worker_id: string | null;
  status: string;
  attempt_number: number;
  started_at: string | null;
  finished_at: string | null;
  next_retry_at: string | null;
  error_class: string | null;
  error_message: string | null;
  correlation_id: string | null;
  deliveries_count: number;
}

interface SchedulerStatusResponse {
  status: string;
  worker_id: string;
  poll_interval_seconds: number;
  lease_duration_seconds: number;
  total_jobs: number;
  active_jobs: number;
  running_executions: number;
  retrying_executions: number;
  approved_handlers: Record<string, string>;
}

export const SchedulerView: React.FC = () => {
  const { role } = useAuth();
  const isAdmin = role?.toUpperCase() === 'ADMIN';
  const isAnalystOrAdmin = isAdmin || role?.toUpperCase() === 'ANALYST';

  const [jobs, setJobs] = useState<ScheduledJobItem[]>([]);
  const [executions, setExecutions] = useState<JobExecutionItem[]>([]);
  const [dispatcherStatus, setDispatcherStatus] = useState<SchedulerStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  // Modal State for New Job
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [newJobName, setNewJobName] = useState('');
  const [newJobDescription, setNewJobDescription] = useState('');
  const [newJobType, setNewJobType] = useState('report.generate');
  const [newJobCron, setNewJobCron] = useState('0 6 * * *');
  const [newJobTz, setNewJobTz] = useState('UTC');
  const [newJobPeriod, setNewJobPeriod] = useState('daily');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [jobsRes, execRes, statusRes] = await Promise.all([
        apiClient.get('/scheduler/jobs'),
        apiClient.get('/scheduler/executions?limit=30'),
        apiClient.get('/scheduler/status')
      ]);
      setJobs(jobsRes.data);
      setExecutions(execRes.data);
      setDispatcherStatus(statusRes.data);
    } catch (err: any) {
      console.error('Failed fetching scheduler data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleExecuteJob = async (jobId: string) => {
    setActionLoading(`exec_${jobId}`);
    setFeedback(null);
    try {
      const res = await apiClient.post(`/scheduler/jobs/${jobId}/execute`);
      setFeedback({
        type: 'success',
        message: `Job '${res.data.job_name}' triggered ad-hoc! Execution Run: ${res.data.run_id} (${res.data.execution_status})`
      });
      fetchData();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to trigger job execution.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleTogglePause = async (job: ScheduledJobItem) => {
    setActionLoading(`toggle_${job.id}`);
    setFeedback(null);
    try {
      if (job.status === 'ACTIVE') {
        await apiClient.post(`/scheduler/jobs/${job.id}/pause`);
        setFeedback({ type: 'info', message: `Job '${job.name}' paused.` });
      } else {
        await apiClient.post(`/scheduler/jobs/${job.id}/resume`);
        setFeedback({ type: 'success', message: `Job '${job.name}' resumed.` });
      }
      fetchData();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to update job status.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteJob = async (jobId: string, jobName: string) => {
    if (!window.confirm(`Are you sure you want to delete scheduled job '${jobName}'?`)) return;
    setActionLoading(`delete_${jobId}`);
    try {
      await apiClient.delete(`/scheduler/jobs/${jobId}`);
      setFeedback({ type: 'info', message: `Scheduled job '${jobName}' deleted.` });
      fetchData();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to delete job.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRetryExecution = async (execId: string) => {
    setActionLoading(`retry_${execId}`);
    try {
      await apiClient.post(`/scheduler/executions/${execId}/retry`);
      setFeedback({ type: 'success', message: `Execution ${execId} queued for immediate retry.` });
      fetchData();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to retry execution.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleCreateJobSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading('create_job');
    try {
      const payload = newJobType === 'report.generate' ? { period: newJobPeriod, enable_email: true } : {};
      await apiClient.post('/scheduler/jobs', {
        name: newJobName.trim(),
        description: newJobDescription.trim() || undefined,
        job_type: newJobType,
        cron_expression: newJobCron.trim(),
        timezone: newJobTz.trim(),
        payload: payload,
        enabled: true
      });
      setShowCreateModal(false);
      setNewJobName('');
      setNewJobDescription('');
      setFeedback({ type: 'success', message: `Scheduled job '${newJobName}' created successfully!` });
      fetchData();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to create scheduled job.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px', margin: '0 auto', padding: '1rem 0' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Clock color="var(--cg-blue-primary)" size={24} />
            <h1 className="page-title" style={{ margin: 0 }}>Production Scheduler & Dispatcher</h1>
          </div>
          <p className="page-subtitle" style={{ margin: '0.25rem 0 0' }}>
            Durable database-backed job registry • Multi-worker lease concurrency • Automatic retry engine
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={fetchData} disabled={loading} className="btn-cg-secondary">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
          {isAdmin && (
            <button onClick={() => setShowCreateModal(true)} className="btn-cg-primary">
              <Plus size={14} />
              <span>Register New Job</span>
            </button>
          )}
        </div>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <div
          style={{
            padding: '0.75rem 1rem',
            borderRadius: '6px',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            backgroundColor:
              feedback.type === 'success'
                ? 'rgba(46, 133, 64, 0.12)'
                : feedback.type === 'error'
                ? 'rgba(217, 83, 79, 0.12)'
                : 'rgba(0, 112, 173, 0.12)',
            color:
              feedback.type === 'success'
                ? '#2E8540'
                : feedback.type === 'error'
                ? '#D9534F'
                : 'var(--cg-blue-primary)',
            border: `1px solid ${
              feedback.type === 'success'
                ? 'rgba(46, 133, 64, 0.3)'
                : feedback.type === 'error'
                ? 'rgba(217, 83, 79, 0.3)'
                : 'rgba(0, 112, 173, 0.3)'
            }`
          }}
        >
          {feedback.type === 'success' && <CheckCircle2 size={16} />}
          {feedback.type === 'error' && <AlertTriangle size={16} />}
          {feedback.type === 'info' && <Activity size={16} />}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Status Scorecards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cg-text-muted)', textTransform: 'uppercase' }}>
            Dispatcher State
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: dispatcherStatus?.status === 'RUNNING' ? '#2E8540' : '#D9534F' }} />
            <span style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--cg-text-primary)' }}>
              {dispatcherStatus?.status || 'INITIALIZING'}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
            Worker: {dispatcherStatus?.worker_id || 'active'}
          </span>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cg-text-muted)', textTransform: 'uppercase' }}>
            Active Scheduled Jobs
          </span>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--cg-blue-primary)' }}>
            {dispatcherStatus?.active_jobs ?? 0} <span style={{ fontSize: '0.85rem', color: 'var(--cg-text-muted)' }}>/ {dispatcherStatus?.total_jobs ?? 0} Total</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
            Poll Interval: {dispatcherStatus?.poll_interval_seconds ?? 5}s
          </span>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cg-text-muted)', textTransform: 'uppercase' }}>
            Running Executions
          </span>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--cg-text-primary)' }}>
            {dispatcherStatus?.running_executions ?? 0}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
            Lease Duration: {dispatcherStatus?.lease_duration_seconds ?? 300}s
          </span>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cg-text-muted)', textTransform: 'uppercase' }}>
            Retrying Queue
          </span>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: (dispatcherStatus?.retrying_executions ?? 0) > 0 ? '#E6A23C' : '#2E8540' }}>
            {dispatcherStatus?.retrying_executions ?? 0}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
            Automatic backoff retry
          </span>
        </div>
      </div>

      {/* Persistent Scheduled Jobs Table */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--cg-text-primary)' }}>
            Persistent Scheduled Jobs Registry
          </h2>
          <p style={{ margin: '0.2rem 0 0', fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
            Configured cron schedules, timezone specifications, and automated execution handlers
          </p>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--cg-border-card)', color: 'var(--cg-text-muted)', textAlign: 'left' }}>
                <th style={{ padding: '0.6rem 0.75rem' }}>Job Name</th>
                <th style={{ padding: '0.6rem 0.75rem' }}>Type</th>
                <th style={{ padding: '0.6rem 0.75rem' }}>Cron (UTC / TZ)</th>
                <th style={{ padding: '0.6rem 0.75rem' }}>Status</th>
                <th style={{ padding: '0.6rem 0.75rem' }}>Next Run</th>
                <th style={{ padding: '0.6rem 0.75rem' }}>Last Run</th>
                {isAnalystOrAdmin && <th style={{ padding: '0.6rem 0.75rem', textAlign: 'right' }}>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id} style={{ borderBottom: '1px solid var(--cg-border-card)' }}>
                  <td style={{ padding: '0.75rem' }}>
                    <div style={{ fontWeight: 600, color: 'var(--cg-text-primary)' }}>{job.name}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--cg-text-muted)' }}>{job.description || 'No description'}</div>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--cg-blue-primary)' }}>
                      {job.job_type}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <div style={{ fontFamily: 'monospace', fontWeight: 600 }}>{job.cron_expression}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--cg-text-muted)' }}>{job.timezone}</div>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <span
                      style={{
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        backgroundColor: job.status === 'ACTIVE' ? 'rgba(46, 133, 64, 0.12)' : 'rgba(128, 128, 128, 0.12)',
                        color: job.status === 'ACTIVE' ? '#2E8540' : 'var(--cg-text-muted)'
                      }}
                    >
                      {job.status}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem', color: 'var(--cg-text-muted)' }}>
                    {job.next_run_at ? new Date(job.next_run_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-'}
                  </td>
                  <td style={{ padding: '0.75rem', color: 'var(--cg-text-muted)' }}>
                    {job.last_run_at ? new Date(job.last_run_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Never'}
                  </td>
                  {isAnalystOrAdmin && (
                    <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.35rem' }}>
                        <button
                          onClick={() => handleExecuteJob(job.id)}
                          disabled={actionLoading === `exec_${job.id}`}
                          title="Trigger Ad-Hoc Execution"
                          style={{
                            padding: '0.3rem 0.5rem',
                            borderRadius: '4px',
                            backgroundColor: 'var(--cg-blue-primary)',
                            color: '#FFFFFF',
                            border: 'none',
                            fontSize: '0.7rem',
                            cursor: 'pointer'
                          }}
                        >
                          <Play size={10} style={{ display: 'inline', marginRight: 3 }} />
                          Run
                        </button>
                        {isAdmin && (
                          <>
                            <button
                              onClick={() => handleTogglePause(job)}
                              disabled={actionLoading === `toggle_${job.id}`}
                              title={job.status === 'ACTIVE' ? 'Pause Job' : 'Resume Job'}
                              style={{
                                padding: '0.3rem 0.5rem',
                                borderRadius: '4px',
                                backgroundColor: 'transparent',
                                border: '1px solid var(--cg-border-card)',
                                color: 'var(--cg-text-primary)',
                                fontSize: '0.7rem',
                                cursor: 'pointer'
                              }}
                            >
                              {job.status === 'ACTIVE' ? <Pause size={10} /> : <Play size={10} />}
                            </button>
                            <button
                              onClick={() => handleDeleteJob(job.id, job.name)}
                              disabled={actionLoading === `delete_${job.id}`}
                              title="Delete Job"
                              style={{
                                padding: '0.3rem 0.5rem',
                                borderRadius: '4px',
                                backgroundColor: 'transparent',
                                border: '1px solid rgba(217, 83, 79, 0.3)',
                                color: '#D9534F',
                                fontSize: '0.7rem',
                                cursor: 'pointer'
                              }}
                            >
                              <Trash2 size={10} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Durable Execution History Table */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--cg-text-primary)' }}>
            Durable Execution & Delivery Log
          </h2>
          <p style={{ margin: '0.2rem 0 0', fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
            Persistent run traces, worker assignment, and automatic retry states
          </p>
        </div>

        {executions.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--cg-text-muted)', fontSize: '0.85rem' }}>
            No execution runs recorded yet.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--cg-border-card)', color: 'var(--cg-text-muted)', textAlign: 'left' }}>
                  <th style={{ padding: '0.5rem 0.75rem' }}>Run ID</th>
                  <th style={{ padding: '0.5rem 0.75rem' }}>Job Name</th>
                  <th style={{ padding: '0.5rem 0.75rem' }}>Worker</th>
                  <th style={{ padding: '0.5rem 0.75rem' }}>Status</th>
                  <th style={{ padding: '0.5rem 0.75rem' }}>Attempt</th>
                  <th style={{ padding: '0.5rem 0.75rem' }}>Started At</th>
                  <th style={{ padding: '0.5rem 0.75rem' }}>Error / Result</th>
                  {isAnalystOrAdmin && <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {executions.map((exec) => (
                  <tr key={exec.id} style={{ borderBottom: '1px solid var(--cg-border-card)' }}>
                    <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'monospace', fontWeight: 600 }}>
                      {exec.run_id}
                    </td>
                    <td style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>
                      {exec.job_name}
                    </td>
                    <td style={{ padding: '0.5rem 0.75rem', color: 'var(--cg-text-muted)' }}>
                      {exec.worker_id || 'system'}
                    </td>
                    <td style={{ padding: '0.5rem 0.75rem' }}>
                      <span
                        style={{
                          padding: '0.15rem 0.4rem',
                          borderRadius: '4px',
                          fontSize: '0.65rem',
                          fontWeight: 700,
                          backgroundColor:
                            exec.status === 'SUCCEEDED'
                              ? 'rgba(46, 133, 64, 0.12)'
                              : exec.status === 'RUNNING'
                              ? 'rgba(0, 112, 173, 0.12)'
                              : exec.status === 'RETRYING'
                              ? 'rgba(230, 162, 60, 0.12)'
                              : 'rgba(217, 83, 79, 0.12)',
                          color:
                            exec.status === 'SUCCEEDED'
                              ? '#2E8540'
                              : exec.status === 'RUNNING'
                              ? 'var(--cg-blue-primary)'
                              : exec.status === 'RETRYING'
                              ? '#E6A23C'
                              : '#D9534F'
                        }}
                      >
                        {exec.status}
                      </span>
                    </td>
                    <td style={{ padding: '0.5rem 0.75rem' }}>{exec.attempt_number}</td>
                    <td style={{ padding: '0.5rem 0.75rem', color: 'var(--cg-text-muted)' }}>
                      {exec.started_at ? new Date(exec.started_at).toLocaleTimeString() : '-'}
                    </td>
                    <td style={{ padding: '0.5rem 0.75rem', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {exec.error_message ? (
                        <span style={{ color: '#D9534F' }}>{exec.error_message}</span>
                      ) : (
                        <span style={{ color: 'var(--cg-text-muted)' }}>Completed successfully</span>
                      )}
                    </td>
                    {isAnalystOrAdmin && (
                      <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right' }}>
                        {exec.status === 'FAILED' && (
                          <button
                            onClick={() => handleRetryExecution(exec.id)}
                            disabled={actionLoading === `retry_${exec.id}`}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.2rem',
                              padding: '0.25rem 0.5rem',
                              borderRadius: '4px',
                              backgroundColor: 'transparent',
                              border: '1px solid var(--cg-border-card)',
                              color: 'var(--cg-text-primary)',
                              fontSize: '0.7rem',
                              cursor: 'pointer'
                            }}
                          >
                            <RotateCcw size={10} />
                            Retry
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Register New Job */}
      {showCreateModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: '500px',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Register New Scheduled Job</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.2rem', cursor: 'pointer', color: 'var(--cg-text-muted)' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateJobSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                  Job Name *
                </label>
                <input
                  type="text"
                  required
                  value={newJobName}
                  onChange={(e) => setNewJobName(e.target.value)}
                  placeholder="e.g. night-operations-digest"
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--cg-border-card)', backgroundColor: 'var(--cg-surface-card)', color: 'var(--cg-text-primary)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                  Description
                </label>
                <input
                  type="text"
                  value={newJobDescription}
                  onChange={(e) => setNewJobDescription(e.target.value)}
                  placeholder="e.g. Automated nightly digest"
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--cg-border-card)', backgroundColor: 'var(--cg-surface-card)', color: 'var(--cg-text-primary)' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                    Job Handler Type *
                  </label>
                  <select
                    value={newJobType}
                    onChange={(e) => setNewJobType(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--cg-border-card)', backgroundColor: 'var(--cg-surface-card)', color: 'var(--cg-text-primary)' }}
                  >
                    <option value="report.generate">report.generate</option>
                    <option value="notification.send">notification.send</option>
                    <option value="executive.digest">executive.digest</option>
                    <option value="servicenow.sync">servicenow.sync</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                    Period Parameter
                  </label>
                  <select
                    value={newJobPeriod}
                    onChange={(e) => setNewJobPeriod(e.target.value)}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--cg-border-card)', backgroundColor: 'var(--cg-surface-card)', color: 'var(--cg-text-primary)' }}
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                    Cron Expression *
                  </label>
                  <input
                    type="text"
                    required
                    value={newJobCron}
                    onChange={(e) => setNewJobCron(e.target.value)}
                    placeholder="0 6 * * *"
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--cg-border-card)', backgroundColor: 'var(--cg-surface-card)', color: 'var(--cg-text-primary)', fontFamily: 'monospace' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                    Timezone (IANA)
                  </label>
                  <input
                    type="text"
                    value={newJobTz}
                    onChange={(e) => setNewJobTz(e.target.value)}
                    placeholder="UTC"
                    style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--cg-border-card)', backgroundColor: 'var(--cg-surface-card)', color: 'var(--cg-text-primary)' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-cg-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading === 'create_job'}
                  className="btn-cg-primary"
                >
                  {actionLoading === 'create_job' ? 'Registering...' : 'Register Job'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
