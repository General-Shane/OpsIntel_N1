import React, { useState } from 'react';
import apiClient from '../../api/client';
import { Upload, CheckCircle2, AlertCircle, FileText, ArrowRight } from 'lucide-react';

export const DataIngestion: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a CSV file first.");
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/ingest/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
      setUploading(false);
    } catch (err: any) {
      console.error("Upload error:", err);
      setError(err.response?.data?.detail || "Failed to upload file. Ensure format matches canonical ITSM CSV model.");
      setUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="page-title" style={{ margin: 0 }}>Data Ingestion Pipeline</h1>
        <p className="page-subtitle">
          Upload ITSM Operational CSV files to feed the deterministic normalization and analytics engine.
        </p>
      </div>

      <div className="card" style={{
        padding: '3rem 2rem',
        border: '2px dashed var(--cg-border)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        background: 'var(--cg-surface-secondary)',
        borderRadius: '10px'
      }}>
        <Upload size={44} color="var(--cg-blue-primary)" style={{ marginBottom: '1rem' }} />
        <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>Select ITSM CSV File</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
          Supports Incidents, Problems, Changes & SLA Records
        </p>

        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          style={{ display: 'none' }}
          id="csv-upload-input"
        />

        <label
          htmlFor="csv-upload-input"
          className="btn-cg-secondary"
          style={{ cursor: 'pointer', padding: '0.65rem 1.5rem' }}
        >
          {file ? file.name : "Choose CSV File"}
        </label>

        {file && (
          <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', fontSize: '0.85rem' }}>
            <FileText size={16} />
            <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
          </div>
        )}
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="btn-cg-primary"
        style={{ padding: '0.85rem', width: '100%', justifyContent: 'center' }}
      >
        <span>{uploading ? "Ingesting & Normalizing..." : "Process ITSM Data"}</span>
        <ArrowRight size={18} />
      </button>

      {error && (
        <div className="card" style={{ borderLeft: '4px solid var(--status-critical)', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <AlertCircle color="var(--status-critical)" size={22} />
          <div>
            <h4 style={{ color: 'var(--status-critical)', fontWeight: 600, margin: 0 }}>Ingestion Error</h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '0.25rem 0 0 0' }}>{error}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="card" style={{ borderLeft: '4px solid var(--status-healthy)', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <CheckCircle2 color="var(--status-healthy)" size={24} />
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--status-healthy)', margin: 0 }}>Ingestion Job Completed</h3>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Job ID: {result.job_id}</span>
            </div>
          </div>

          <div style={{ backgroundColor: 'var(--cg-surface-secondary)', padding: '0.85rem 1rem', borderRadius: '6px' }}>
            <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Processed {result.result?.processed_count || 0} Incident Records Successfully.</p>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Database canonical tables normalized and global KPIs recalculated.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
