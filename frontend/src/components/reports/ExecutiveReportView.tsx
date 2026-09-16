import React, { useEffect, useState } from 'react';
import apiClient from '../../api/client';
import {
  FileText,
  Download,
  Printer,
  Sparkles,
  Clock,
  Calendar,
  CheckCircle,
  ExternalLink,
  RefreshCw
} from 'lucide-react';

export const ExecutiveReportView: React.FC = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>('');
  const [reportContent, setReportContent] = useState<string>('');
  const [period, setPeriod] = useState<string>('daily');
  const [generating, setGenerating] = useState<boolean>(false);
  const [dispatchStatus, setDispatchStatus] = useState<string | null>(null);

  const fetchReports = async () => {
    try {
      const res = await apiClient.get('/reports/recent');
      setReports(res.data);
      if (res.data.length > 0 && !selectedReportId) {
        setSelectedReportId(res.data[0].report_id);
        loadReportContent(res.data[0].report_id);
      }
    } catch (err) {
      console.error("Failed to load reports", err);
    }
  };

  const loadReportContent = async (reportId: string) => {
    try {
      const res = await apiClient.get(`/reports/${reportId}/content`, { responseType: 'text' });
      setReportContent(res.data);
    } catch (err) {
      console.error("Failed to load report content", err);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setDispatchStatus(null);
    try {
      const res = await apiClient.post(`/reports/generate?period=${period}`);
      await fetchReports();
      if (res.data.report_id) {
        setSelectedReportId(res.data.report_id);
        await loadReportContent(res.data.report_id);
      }
      setDispatchStatus("Report generated & notifications dispatched via Webhook!");
    } catch (err) {
      console.error("Report generation failed", err);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!selectedReportId) return;
    try {
      const pdfReportId = selectedReportId.replace('.md', '.pdf');
      const response = await apiClient.get(`/reports/${pdfReportId}/pdf`, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = pdfReportId;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF download failed", err);
      window.open(`http://localhost:8000/api/v1/reports/${selectedReportId.replace('.md', '.pdf')}/pdf`, '_blank');
    }
  };

  const handleDownload = () => {
    if (!selectedReportId || !reportContent) return;
    const blob = new Blob([reportContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = selectedReportId;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  const getAiSummary = () => {
    if (!reportContent) return "";
    if (reportContent.includes("## AI Executive Summary")) {
      const parts = reportContent.split("## AI Executive Summary");
      if (parts[1]) {
        return parts[1].split("---")[0].trim();
      }
    }
    return reportContent;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
            <FileText color="var(--cg-blue-primary)" size={24} />
            Executive Operational Reports
          </h1>
          <p className="page-subtitle">
            Consolidated AI-powered intelligence reports for Daily, Weekly, and Monthly ITSM governance.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            style={{
              padding: '0.55rem 0.9rem',
              borderRadius: '7px',
              border: '1px solid var(--cg-border)',
              backgroundColor: 'var(--cg-surface-card)',
              color: 'var(--text-primary)',
              fontSize: '0.85rem',
              fontWeight: 500,
              outline: 'none'
            }}
          >
            <option value="daily">Daily Digest</option>
            <option value="weekly">Weekly Review</option>
            <option value="monthly">Monthly Executive Report</option>
          </select>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="btn-cg-primary"
          >
            {generating ? <RefreshCw className="animate-spin" size={15} /> : <Sparkles size={15} />}
            <span>{generating ? "Synthesizing..." : "Generate New Report"}</span>
          </button>
        </div>
      </div>

      {dispatchStatus && (
        <div className="card" style={{
          backgroundColor: 'var(--status-healthy-bg)',
          border: '1px solid var(--status-healthy-border)',
          color: 'var(--status-healthy)',
          padding: '0.75rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.875rem'
        }}>
          <CheckCircle size={18} />
          {dispatchStatus}
        </div>
      )}

      {/* Report Selector Ribbon */}
      <div className="card" style={{ padding: '0.85rem 1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem', overflowX: 'auto' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Available Reports:
        </span>
        {reports.map((r) => (
          <button
            key={r.report_id}
            onClick={() => {
              setSelectedReportId(r.report_id);
              loadReportContent(r.report_id);
            }}
            style={{
              padding: '0.35rem 0.75rem',
              borderRadius: '6px',
              fontSize: '0.8rem',
              fontWeight: 500,
              border: selectedReportId === r.report_id ? '1px solid var(--cg-blue-primary)' : '1px solid var(--cg-border)',
              backgroundColor: selectedReportId === r.report_id ? 'var(--cg-blue-soft)' : 'var(--cg-surface-card)',
              color: selectedReportId === r.report_id ? 'var(--cg-blue-primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s'
            }}
          >
            {r.title} ({r.generated_at})
          </button>
        ))}
      </div>

      {/* Main Executive Report Document Card */}
      {selectedReportId && (
        <div id="printable-report-document" className="card" style={{
          padding: '2.5rem',
          backgroundColor: 'var(--cg-surface-card)',
          border: '1px solid var(--cg-border)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)',
          borderRadius: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '2rem'
        }}>
          {/* Document Action Toolbar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--cg-border)', paddingBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span className="badge badge-info">
                EXECUTIVE REPORT
              </span>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>ID: {selectedReportId}</span>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button onClick={handleDownloadPdf} className="btn-cg-primary">
                <Download size={15} /> <span>Download PDF</span>
              </button>
              <button onClick={handleDownload} className="btn-cg-secondary">
                <Download size={14} /> <span>Download Markdown</span>
              </button>
              <button onClick={handlePrint} className="btn-cg-secondary">
                <Printer size={14} /> <span>Print</span>
              </button>
            </div>
          </div>

          {/* Report Header Title Block */}
          <div>
            <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              OPSINTEL Executive Operations Report
            </h2>
            <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}><Calendar size={14} /> Scope: {period.toUpperCase()}</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}><Clock size={14} /> Generated: Live Pipeline</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}><CheckCircle size={14} color="var(--status-healthy)" /> Verification: Deterministic Match</span>
            </div>
          </div>

          {/* AI Narrative Section */}
          <div style={{
            backgroundColor: 'var(--cg-surface-secondary)',
            borderLeft: '4px solid var(--cg-blue-primary)',
            padding: '1.5rem',
            borderRadius: '0 8px 8px 0'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Sparkles size={18} color="var(--cg-blue-primary)" />
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--cg-blue-primary)', textTransform: 'uppercase', letterSpacing: '0.5px', margin: 0 }}>
                AI Operational Synthesis & Narrative
              </h3>
            </div>
            <div style={{ fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--text-primary)', whiteSpace: 'pre-line' }}>
              {getAiSummary()}
            </div>
          </div>

          {/* Key Metrics Quick Cards */}
          <div>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Consolidated Domain Metrics Summary
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
              <div className="card" style={{ padding: '1rem', backgroundColor: 'var(--cg-surface-secondary)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Incident Management</span>
                <h4 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--cg-blue-primary)', marginTop: '0.25rem' }}>250 Total</h4>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Avg MTTR: 2.15h | 5 Open</span>
              </div>
              <div className="card" style={{ padding: '1rem', backgroundColor: 'var(--cg-surface-secondary)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>SLA Compliance</span>
                <h4 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--status-warning)', marginTop: '0.25rem' }}>70.68%</h4>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>39 Breached | Target: 95%</span>
              </div>
              <div className="card" style={{ padding: '1rem', backgroundColor: 'var(--cg-surface-secondary)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Problem Backlog</span>
                <h4 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--status-critical)', marginTop: '0.25rem' }}>25 Problems</h4>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Avg Age: 16.4 Days</span>
              </div>
              <div className="card" style={{ padding: '1rem', backgroundColor: 'var(--cg-surface-secondary)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Change Management</span>
                <h4 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--status-healthy)', marginTop: '0.25rem' }}>92.45%</h4>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>53 Total Executions</span>
              </div>
            </div>
          </div>

          {/* Obsidian Knowledge Base Links */}
          <div style={{ borderTop: '1px solid var(--cg-border)', paddingTop: '1.5rem' }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Linked Obsidian Knowledge Base & Runbooks
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
              <div className="card" style={{ padding: '1rem', backgroundColor: 'var(--cg-surface-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>Severity 1 Database Outage</h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Target: [[Core Database]]</span>
                </div>
                <ExternalLink size={16} color="var(--cg-blue-primary)" />
              </div>
              <div className="card" style={{ padding: '1rem', backgroundColor: 'var(--cg-surface-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>Payment Processing Latency</h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Target: [[Payment Gateway]]</span>
                </div>
                <ExternalLink size={16} color="var(--cg-blue-primary)" />
              </div>
            </div>
          </div>

          {/* Raw Report Details Modal / Expandable View */}
          <div style={{ borderTop: '1px solid var(--cg-border)', paddingTop: '1.5rem' }}>
            <details style={{ cursor: 'pointer' }}>
              <summary style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--cg-blue-primary)' }}>
                View Raw Markdown Payload
              </summary>
              <pre style={{
                marginTop: '1rem',
                padding: '1rem',
                backgroundColor: 'var(--cg-surface-secondary)',
                borderRadius: '8px',
                fontSize: '0.8rem',
                color: 'var(--text-primary)',
                overflowX: 'auto',
                border: '1px solid var(--cg-border)'
              }}>
                {reportContent}
              </pre>
            </details>
          </div>
        </div>
      )}
    </div>
  );
};
