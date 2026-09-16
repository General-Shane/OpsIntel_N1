import React, { useState, useEffect } from 'react';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import {
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Activity,
  ArrowRightLeft,
  ShieldCheck,
  RotateCcw,
  Zap
} from 'lucide-react';

interface EntitySyncState {
  status: string;
  last_successful_sync: string | null;
  last_attempted_sync: string | null;
  records_fetched: number;
  records_inserted: number;
  records_updated: number;
  records_failed: number;
  error_summary: string | null;
}

interface IntegrationStatusResponse {
  connector: string;
  config: {
    is_configured: boolean;
    auth_mode: string;
    instance_url: string;
    username_configured: boolean;
    client_id_masked: string;
    token_configured: boolean;
  };
  entities: Record<string, EntitySyncState>;
  metrics: {
    service_now_requests_total: number;
    service_now_request_failures_total: number;
    service_now_rate_limits_total: number;
    service_now_sync_records_total: number;
    service_now_sync_failures_total: number;
    service_now_writebacks_total: number;
    service_now_webhooks_total: number;
  };
  unresolved_failures_count: number;
  total_webhooks_processed: number;
}

interface IntegrationErrorItem {
  id: string;
  entity_name: string;
  external_id: string | null;
  error_class: string | null;
  error_message: string;
  attempt_count: number;
  status: string;
  first_failure_at: string | null;
  last_failure_at: string | null;
  resolved_at: string | null;
}

export const IntegrationsView: React.FC = () => {
  const { role } = useAuth();
  const isAdmin = role?.toUpperCase() === 'ADMIN';
  const isAnalystOrAdmin = isAdmin || role?.toUpperCase() === 'ANALYST';

  const [data, setData] = useState<IntegrationStatusResponse | null>(null);
  const [errors, setErrors] = useState<IntegrationErrorItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await apiClient.get('/integrations/servicenow/status');
      setData(res.data);
    } catch (err: any) {
      console.error('Failed to fetch ServiceNow integration status', err);
    }
  };

  const fetchErrors = async () => {
    try {
      const res = await apiClient.get('/integrations/servicenow/errors?limit=25');
      setErrors(res.data);
    } catch (err: any) {
      console.error('Failed to fetch integration errors', err);
    }
  };

  const refreshAll = async () => {
    setLoading(true);
    await Promise.all([fetchStatus(), fetchErrors()]);
    setLoading(false);
  };

  useEffect(() => {
    refreshAll();
  }, []);

  const handleTestConnection = async () => {
    setActionLoading('test_connection');
    setFeedback(null);
    try {
      const res = await apiClient.post('/integrations/servicenow/test-connection');
      if (res.data.status === 'CONNECTED') {
        setFeedback({
          type: 'success',
          message: `${res.data.message} (Latency: ${res.data.latency_ms}ms)`
        });
      } else if (res.data.status === 'NOT_CONFIGURED') {
        setFeedback({
          type: 'info',
          message: 'ServiceNow instance URL and credentials are not configured in environment.'
        });
      } else {
        setFeedback({
          type: 'error',
          message: res.data.message || 'Connection test failed.'
        });
      }
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to execute connection test.'
      });
    } finally {
      setActionLoading(null);
      fetchStatus();
    }
  };

  const handleSyncAll = async (fullSync: boolean = false) => {
    setActionLoading('sync_all');
    setFeedback(null);
    try {
      const res = await apiClient.post('/integrations/servicenow/sync', { full_sync: fullSync });
      setFeedback({
        type: 'success',
        message: `Sync completed! Fetched: ${res.data.total_fetched}, Inserted: ${res.data.total_inserted}, Updated: ${res.data.total_updated}`
      });
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'ServiceNow synchronization failed.'
      });
    } finally {
      setActionLoading(null);
      refreshAll();
    }
  };

  const handleSyncEntity = async (entity: string) => {
    setActionLoading(`sync_${entity}`);
    setFeedback(null);
    try {
      const res = await apiClient.post(`/integrations/servicenow/sync/${entity}`, { full_sync: false });
      setFeedback({
        type: 'success',
        message: `${entity.toUpperCase()} sync completed! Fetched: ${res.data.records_fetched}, Inserted: ${res.data.records_inserted}, Updated: ${res.data.records_updated}`
      });
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || `Failed to sync ${entity}.`
      });
    } finally {
      setActionLoading(null);
      refreshAll();
    }
  };

  const handleRetryError = async (errorId: string) => {
    setActionLoading(`retry_${errorId}`);
    try {
      const res = await apiClient.post(`/integrations/servicenow/errors/${errorId}/retry`);
      if (res.data.status === 'RESOLVED') {
        setFeedback({ type: 'success', message: `Failure ${errorId} resolved successfully.` });
      } else {
        setFeedback({ type: 'error', message: `Retry failed: ${res.data.error || 'Unknown error'}` });
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Retry execution failed.' });
    } finally {
      setActionLoading(null);
      refreshAll();
    }
  };

  const entityKeys = ['service', 'problem', 'change', 'incident', 'sla'];

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0, color: 'var(--cg-text-primary)' }}>
            ServiceNow Live Integration
          </h1>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.875rem', color: 'var(--cg-text-muted)' }}>
            Enterprise ITSM connector, bidirectional synchronization, and real-time webhook ingestion
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={refreshAll}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.5rem 0.85rem',
              borderRadius: '6px',
              backgroundColor: 'var(--cg-surface-card)',
              border: '1px solid var(--cg-border-card)',
              color: 'var(--cg-text-primary)',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          {isAdmin && (
            <button
              onClick={handleTestConnection}
              disabled={actionLoading === 'test_connection'}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.5rem 0.85rem',
                borderRadius: '6px',
                backgroundColor: 'var(--cg-blue-primary)',
                border: 'none',
                color: '#FFFFFF',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: actionLoading === 'test_connection' ? 'not-allowed' : 'pointer'
              }}
            >
              <Zap size={14} />
              {actionLoading === 'test_connection' ? 'Testing...' : 'Test Connection'}
            </button>
          )}
          {isAnalystOrAdmin && (
            <button
              onClick={() => handleSyncAll(false)}
              disabled={actionLoading === 'sync_all'}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.5rem 0.85rem',
                borderRadius: '6px',
                backgroundColor: 'var(--cg-surface-card)',
                border: '1px solid var(--cg-blue-primary)',
                color: 'var(--cg-blue-primary)',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: actionLoading === 'sync_all' ? 'not-allowed' : 'pointer'
              }}
            >
              <ArrowRightLeft size={14} />
              {actionLoading === 'sync_all' ? 'Syncing...' : 'Sync All'}
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

      {/* Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div
          style={{
            backgroundColor: 'var(--cg-surface-card)',
            border: '1px solid var(--cg-border-card)',
            borderRadius: '8px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cg-text-muted)', textTransform: 'uppercase' }}>
            Connection State
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor: data?.config.is_configured ? '#2E8540' : '#E6A23C'
              }}
            />
            <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--cg-text-primary)' }}>
              {data?.config.is_configured ? 'Configured' : 'Not Configured'}
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
            URL: {data?.config.instance_url}
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--cg-surface-card)',
            border: '1px solid var(--cg-border-card)',
            borderRadius: '8px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cg-text-muted)', textTransform: 'uppercase' }}>
            Authentication Mode
          </div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--cg-text-primary)', textTransform: 'uppercase' }}>
            {data?.config.auth_mode || 'BASIC'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
            Client ID: {data?.config.client_id_masked}
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--cg-surface-card)',
            border: '1px solid var(--cg-border-card)',
            borderRadius: '8px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cg-text-muted)', textTransform: 'uppercase' }}>
            Synced Records / Calls
          </div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--cg-text-primary)' }}>
            {data?.metrics.service_now_sync_records_total.toLocaleString() || '0'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
            API Calls: {data?.metrics.service_now_requests_total.toLocaleString() || '0'}
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--cg-surface-card)',
            border: '1px solid var(--cg-border-card)',
            borderRadius: '8px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cg-text-muted)', textTransform: 'uppercase' }}>
            Dead-Letter Failures
          </div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: data?.unresolved_failures_count ? '#D9534F' : '#2E8540' }}>
            {data?.unresolved_failures_count || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
            Webhooks Processed: {data?.total_webhooks_processed || 0}
          </div>
        </div>
      </div>

      {/* Entity Synchronization Matrix */}
      <div
        style={{
          backgroundColor: 'var(--cg-surface-card)',
          border: '1px solid var(--cg-border-card)',
          borderRadius: '8px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--cg-text-primary)' }}>
              ITSM Entity Synchronization States
            </h2>
            <p style={{ margin: '0.2rem 0 0', fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
              Granular sync timestamps, record throughput, and per-entity triggers
            </p>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--cg-border-card)', color: 'var(--cg-text-muted)', textAlign: 'left' }}>
                <th style={{ padding: '0.6rem 0.75rem' }}>Entity</th>
                <th style={{ padding: '0.6rem 0.75rem' }}>Status</th>
                <th style={{ padding: '0.6rem 0.75rem' }}>Fetched</th>
                <th style={{ padding: '0.6rem 0.75rem' }}>Inserted</th>
                <th style={{ padding: '0.6rem 0.75rem' }}>Updated</th>
                <th style={{ padding: '0.6rem 0.75rem' }}>Last Sync</th>
                {isAnalystOrAdmin && <th style={{ padding: '0.6rem 0.75rem', textAlign: 'right' }}>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {entityKeys.map((entity) => {
                const s = data?.entities?.[entity];
                const isRunning = actionLoading === `sync_${entity}`;
                return (
                  <tr
                    key={entity}
                    style={{
                      borderBottom: '1px solid var(--cg-border-card)',
                      color: 'var(--cg-text-primary)'
                    }}
                  >
                    <td style={{ padding: '0.75rem', fontWeight: 600, textTransform: 'capitalize' }}>
                      {entity}s
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                          padding: '0.2rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          backgroundColor:
                            s?.status === 'SUCCESS'
                              ? 'rgba(46, 133, 64, 0.12)'
                              : s?.status === 'FAILED'
                              ? 'rgba(217, 83, 79, 0.12)'
                              : 'rgba(128, 128, 128, 0.12)',
                          color:
                            s?.status === 'SUCCESS'
                              ? '#2E8540'
                              : s?.status === 'FAILED'
                              ? '#D9534F'
                              : 'var(--cg-text-muted)'
                        }}
                      >
                        {s?.status || 'IDLE'}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem' }}>{s?.records_fetched ?? 0}</td>
                    <td style={{ padding: '0.75rem' }}>{s?.records_inserted ?? 0}</td>
                    <td style={{ padding: '0.75rem' }}>{s?.records_updated ?? 0}</td>
                    <td style={{ padding: '0.75rem', color: 'var(--cg-text-muted)' }}>
                      {s?.last_successful_sync ? new Date(s.last_successful_sync).toLocaleString() : 'Never'}
                    </td>
                    {isAnalystOrAdmin && (
                      <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                        <button
                          onClick={() => handleSyncEntity(entity)}
                          disabled={isRunning || !data?.config.is_configured}
                          style={{
                            padding: '0.35rem 0.65rem',
                            borderRadius: '4px',
                            backgroundColor: 'transparent',
                            border: '1px solid var(--cg-border-card)',
                            color: 'var(--cg-text-primary)',
                            fontSize: '0.75rem',
                            cursor: isRunning || !data?.config.is_configured ? 'not-allowed' : 'pointer'
                          }}
                        >
                          {isRunning ? 'Syncing...' : 'Sync Entity'}
                        </button>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Dead-Letter Queue / Errors Table */}
      <div
        style={{
          backgroundColor: 'var(--cg-surface-card)',
          border: '1px solid var(--cg-border-card)',
          borderRadius: '8px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--cg-text-primary)' }}>
              Dead-Letter Failure Queue
            </h2>
            <p style={{ margin: '0.2rem 0 0', fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
              Unresolved ingestion errors and malformed record payloads
            </p>
          </div>
        </div>

        {errors.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--cg-text-muted)', fontSize: '0.85rem' }}>
            <ShieldCheck size={32} color="#2E8540" style={{ margin: '0 auto 0.5rem' }} />
            No active dead-letter ingestion failures recorded.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--cg-border-card)', color: 'var(--cg-text-muted)', textAlign: 'left' }}>
                  <th style={{ padding: '0.5rem' }}>Time</th>
                  <th style={{ padding: '0.5rem' }}>Entity</th>
                  <th style={{ padding: '0.5rem' }}>External ID</th>
                  <th style={{ padding: '0.5rem' }}>Error Class</th>
                  <th style={{ padding: '0.5rem' }}>Message</th>
                  <th style={{ padding: '0.5rem' }}>Attempts</th>
                  <th style={{ padding: '0.5rem' }}>Status</th>
                  {isAnalystOrAdmin && <th style={{ padding: '0.5rem', textAlign: 'right' }}>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {errors.map((err) => (
                  <tr key={err.id} style={{ borderBottom: '1px solid var(--cg-border-card)' }}>
                    <td style={{ padding: '0.5rem', color: 'var(--cg-text-muted)' }}>
                      {err.last_failure_at ? new Date(err.last_failure_at).toLocaleTimeString() : '-'}
                    </td>
                    <td style={{ padding: '0.5rem', fontWeight: 600, textTransform: 'capitalize' }}>
                      {err.entity_name}
                    </td>
                    <td style={{ padding: '0.5rem' }}>{err.external_id || '-'}</td>
                    <td style={{ padding: '0.5rem', color: '#D9534F' }}>{err.error_class || 'Error'}</td>
                    <td style={{ padding: '0.5rem', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {err.error_message}
                    </td>
                    <td style={{ padding: '0.5rem' }}>{err.attempt_count}</td>
                    <td style={{ padding: '0.5rem' }}>
                      <span
                        style={{
                          padding: '0.15rem 0.4rem',
                          borderRadius: '4px',
                          fontSize: '0.65rem',
                          fontWeight: 700,
                          backgroundColor: err.status === 'RESOLVED' ? 'rgba(46, 133, 64, 0.12)' : 'rgba(217, 83, 79, 0.12)',
                          color: err.status === 'RESOLVED' ? '#2E8540' : '#D9534F'
                        }}
                      >
                        {err.status}
                      </span>
                    </td>
                    {isAnalystOrAdmin && (
                      <td style={{ padding: '0.5rem', textAlign: 'right' }}>
                        {err.status !== 'RESOLVED' && (
                          <button
                            onClick={() => handleRetryError(err.id)}
                            disabled={actionLoading === `retry_${err.id}`}
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

      {/* Webhook Configuration Guide */}
      <div
        style={{
          backgroundColor: 'var(--cg-surface-card)',
          border: '1px solid var(--cg-border-card)',
          borderRadius: '8px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem'
        }}
      >
        <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--cg-text-primary)' }}>
          Inbound Webhook Endpoint & Security Architecture
        </h2>
        <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--cg-text-muted)' }}>
          To stream real-time events directly from ServiceNow Business Rules / Flow Designer into OPSINTEL:
        </p>
        <div
          style={{
            backgroundColor: 'var(--cg-navy-sidebar)',
            color: '#A9BAC8',
            padding: '0.75rem',
            borderRadius: '6px',
            fontFamily: 'monospace',
            fontSize: '0.75rem'
          }}
        >
          POST /api/v1/integrations/servicenow/webhook<br />
          Headers: X-ServiceNow-Signature: &lt;HMAC-SHA256&gt;, X-ServiceNow-Timestamp: &lt;UNIX_TIMESTAMP&gt;
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--cg-text-muted)' }}>
          • Replay attacks are automatically rejected via cryptographic timestamp validation and idempotency keys.<br />
          • Every webhook payload is normalized into Stage 7 relational models and logged to the immutable audit trail.
        </div>
      </div>
    </div>
  );
};
