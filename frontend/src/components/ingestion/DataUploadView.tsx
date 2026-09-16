import React, { useState, useEffect } from 'react';
import apiClient from '../../api/client';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { UploadCloud, RefreshCw, Upload, CheckCircle2, AlertCircle, FileText } from 'lucide-react';
import { formatDateLocal } from '../../utils/date';

export const DataUploadView: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{ status: 'success' | 'error'; message: string } | null>(null);

  const [recentUploads, setRecentUploads] = useState<any[]>([]);

  const uploadActivityData = [
    { date: 'Jul 25', count: 18 },
    { date: 'Jul 26', count: 24 },
    { date: 'Jul 27', count: 32 },
    { date: 'Jul 28', count: 48 },
    { date: 'Jul 29', count: 40 },
    { date: 'Jul 30', count: 35 },
    { date: 'Jul 31', count: 52 },
    { date: 'Aug 01', count: 45 },
  ];

  const fetchHistory = () => {
    apiClient.get('/ingest/history').then(res => {
      setRecentUploads(res.data);
    }).catch(err => console.error("Failed to fetch upload history", err));
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const processFileUpload = async (fileToUpload: File) => {
    setUploading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append('file', fileToUpload);

    try {
      const res = await apiClient.post('/ingest/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      const resData = res.data;
      const count = resData.result?.success || 0;
      const entityType = resData.result?.type || 'Records';

      setUploadStatus({
        status: 'success',
        message: `Successfully processed & ingested "${fileToUpload.name}"! Loaded ${count} ${entityType} into SQLite database.`
      });

      fetchHistory();
      setFile(null);
    } catch (err: any) {
      console.error("Upload failed", err);
      let errMsg = "Failed to ingest CSV file. Please verify CSV column headers.";
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === 'string') {
          errMsg = detail;
        } else if (Array.isArray(detail)) {
          errMsg = detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
        } else {
          errMsg = JSON.stringify(detail);
        }
      }
      setUploadStatus({
        status: 'error',
        message: errMsg
      });
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      processFileUpload(selected);
    }
  };

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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <UploadCloud color="var(--cg-blue-primary)" size={24} />
            Data Upload & Ingestion Center
          </h1>
          <p className="page-subtitle">
            Upload CSV datasets (Incidents, Problems, Changes, SLAs, Services) to ingest into SQLite
          </p>
        </div>

        {file && (
          <button
            onClick={() => file && processFileUpload(file)}
            disabled={uploading}
            className="btn-cg-primary"
          >
            {uploading ? <RefreshCw className="animate-spin" size={16} /> : <Upload size={16} />}
            <span>{uploading ? "Ingesting..." : "Process Upload Now"}</span>
          </button>
        )}
      </div>

      {uploadStatus && (
        <div className="card" style={{
          backgroundColor: uploadStatus.status === 'success' ? 'var(--status-healthy-bg)' : 'var(--status-critical-bg)',
          border: uploadStatus.status === 'success' ? '1px solid var(--status-healthy-border)' : '1px solid var(--status-critical-border)',
          color: uploadStatus.status === 'success' ? 'var(--status-healthy)' : 'var(--status-critical)',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.875rem',
          fontWeight: 600
        }}>
          {uploadStatus.status === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
          <span>{uploadStatus.message}</span>
        </div>
      )}

      {/* Upload Box with Immediate Action Button */}
      <div className="card" style={{
        padding: '3rem 2rem',
        border: uploading ? '2px solid var(--cg-blue-primary)' : '2px dashed var(--cg-border)',
        backgroundColor: 'var(--cg-surface-secondary)',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '1.25rem',
        borderRadius: '10px'
      }}>
        {uploading ? (
          <RefreshCw size={48} color="var(--cg-blue-primary)" className="animate-spin" />
        ) : (
          <UploadCloud size={48} color="var(--cg-blue-primary)" />
        )}

        <div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            {uploading ? "Processing CSV File..." : "Select or Drop CSV Dataset Here"}
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.825rem', marginTop: '0.25rem' }}>
            Supports files in <code>data/</code> folder e.g. <code>large_incidents_data.csv</code>, <code>large_problems_data.csv</code>
          </p>
        </div>

        {file && !uploading && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.45rem 0.85rem',
            backgroundColor: 'var(--cg-blue-soft)',
            border: '1px solid var(--cg-blue-primary)',
            borderRadius: '6px',
            color: 'var(--cg-blue-primary)',
            fontSize: '0.825rem',
            fontWeight: 600
          }}>
            <FileText size={15} />
            <span>Selected File: {file.name}</span>
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <input type="file" accept=".csv" onChange={handleFileChange} id="file-drop-input" style={{ display: 'none' }} />
          <label
            htmlFor="file-drop-input"
            className="btn-cg-secondary"
            style={{ padding: '0.65rem 1.5rem', cursor: 'pointer' }}
          >
            {file ? 'Change File' : 'Browse CSV File'}
          </label>

          {file && (
            <button
              onClick={() => processFileUpload(file)}
              disabled={uploading}
              className="btn-cg-primary"
              style={{ padding: '0.65rem 1.5rem' }}
            >
              {uploading ? <RefreshCw className="animate-spin" size={16} /> : <Upload size={16} />}
              <span>{uploading ? "Ingesting Now..." : "Process & Ingest File Now"}</span>
            </button>
          )}
        </div>
      </div>

      {/* Summary Cards + Chart Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.25rem' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3 className="card-title">Upload Summary</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
            <div style={{ padding: '0.85rem', borderRadius: '6px', backgroundColor: 'var(--cg-surface-secondary)', border: '1px solid var(--cg-border)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total Files</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>{recentUploads.length}</div>
            </div>
            <div style={{ padding: '0.85rem', borderRadius: '6px', backgroundColor: 'var(--cg-surface-secondary)', border: '1px solid var(--cg-border)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Processed</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--status-healthy)' }}>{recentUploads.length}</div>
            </div>
            <div style={{ padding: '0.85rem', borderRadius: '6px', backgroundColor: 'var(--cg-surface-secondary)', border: '1px solid var(--cg-border)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Failed</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>0</div>
            </div>
            <div style={{ padding: '0.85rem', borderRadius: '6px', backgroundColor: 'var(--cg-surface-secondary)', border: '1px solid var(--cg-border)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Active Pipeline</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--cg-blue-primary)' }}>SQLite</div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '1rem' }}>Upload Activity</h3>
          <div style={{ width: '100%', height: 160 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={uploadActivityData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#EEF3F7" />
                <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Bar dataKey="count" fill="var(--cg-blue-primary)" radius={[4, 4, 0, 0]} name="Files Processed" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Uploads Data Table */}
      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--cg-border)' }}>
          <h3 className="card-title">Recent Ingested Uploads</h3>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--cg-border)', color: 'var(--text-secondary)', backgroundColor: 'var(--cg-surface-secondary)' }}>
              <th style={{ padding: '0.75rem 1rem' }}>File Name</th>
              <th style={{ padding: '0.75rem 1rem' }}>Entity Type</th>
              <th style={{ padding: '0.75rem 1rem' }}>Upload Date</th>
              <th style={{ padding: '0.75rem 1rem' }}>Ingested Records</th>
              <th style={{ padding: '0.75rem 1rem' }}>Status</th>
              <th style={{ padding: '0.75rem 1rem' }}>Uploaded By</th>
            </tr>
          </thead>
          <tbody>
            {recentUploads.map(up => (
              <tr key={up.id} style={{ borderBottom: '1px solid #F0F4F7' }}>
                <td style={{ padding: '0.85rem 1rem', fontWeight: 600, color: 'var(--text-primary)' }}>{up.name}</td>
                <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)' }}>{up.type}</td>
                <td style={{ padding: '0.85rem 1rem', color: 'var(--text-muted)' }}>{formatDateLocal(up.date)}</td>
                <td style={{ padding: '0.85rem 1rem', color: 'var(--text-primary)', fontWeight: 600 }}>{up.records}</td>
                <td style={{ padding: '0.85rem 1rem' }}>
                  <span className="badge badge-healthy">
                    {up.status}
                  </span>
                </td>
                <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)' }}>{up.uploadedBy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
