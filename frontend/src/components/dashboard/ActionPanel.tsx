import React, { useEffect, useState } from 'react';
import apiClient from '../../api/client';
import { FileText, Download, Play, Eye, X, RefreshCw } from 'lucide-react';

export const ActionPanel: React.FC = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [period, setPeriod] = useState<string>('daily');
  const [generating, setGenerating] = useState(false);
  const [selectedReportContent, setSelectedReportContent] = useState<string | null>(null);
  const [selectedReportTitle, setSelectedReportTitle] = useState<string>('');

  const fetchReports = () => {
    apiClient.get('/reports/recent')
      .then(res => setReports(res.data))
      .catch(err => console.error("Failed to load recent reports", err));
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await apiClient.post(`/reports/generate?period=${period}`);
      fetchReports();
    } catch (err) {
      console.error("Failed to generate report", err);
    } finally {
      setGenerating(false);
    }
  };

  const handleView = async (reportId: string, title: string) => {
    try {
      const res = await apiClient.get(`/reports/${reportId}/content`, { responseType: 'text' });
      setSelectedReportContent(res.data);
      setSelectedReportTitle(title);
    } catch (err) {
      console.error("Failed to fetch report content", err);
    }
  };

  const handleDownload = async (reportId: string) => {
    try {
      const res = await apiClient.get(`/reports/${reportId}/content`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', reportId);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Failed to download report", err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Generate Report Control Card */}
      <div className="card" style={{
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)',
        border: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{ marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Generate Executive Report</h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>On-demand AI Narrative Synthesis</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <select
            value={period}
            onChange={e => setPeriod(e.target.value)}
            style={{
              padding: '0.65rem 0.85rem',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              backgroundColor: '#0f172a',
              color: '#fff',
              fontSize: '0.875rem',
              outline: 'none'
            }}
          >
            <option value="daily">Daily Operational Digest</option>
            <option value="weekly">Weekly Performance Review</option>
            <option value="monthly">Monthly Executive Report</option>
          </select>

          <button
            onClick={handleGenerate}
            disabled={generating}
            style={{
              padding: '0.75rem',
              borderRadius: '6px',
              backgroundColor: 'var(--accent-primary)',
              color: '#fff',
              border: 'none',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: generating ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              opacity: generating ? 0.7 : 1
            }}
          >
            {generating ? <RefreshCw size={16} className="animate-spin" /> : <Play size={16} />}
            {generating ? "Synthesizing..." : "Generate Report Now"}
          </button>
        </div>
      </div>

      {/* Recent Reports List */}
      <div className="card action-panel">
        <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Recent AI Reports</h3>
          <button onClick={fetchReports} className="btn-icon" title="Refresh">
            <RefreshCw size={14} />
          </button>
        </div>
        
        {reports.length === 0 ? (
          <p className="text-secondary" style={{ fontSize: '0.85rem' }}>No recent reports available.</p>
        ) : (
          <ul className="report-list">
            {reports.map(report => (
              <li key={report.report_id} className="report-item">
                <div className="report-info">
                  <FileText size={18} className="text-blue" />
                  <div>
                    <h4>{report.title}</h4>
                    <span className="text-secondary" style={{ fontSize: '0.75rem' }}>
                      {report.generated_at}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  <button
                    className="btn-icon"
                    onClick={() => handleView(report.report_id, report.title)}
                    title="View Report"
                  >
                    <Eye size={16} />
                  </button>
                  <button
                    className="btn-icon"
                    onClick={() => handleDownload(report.report_id)}
                    title="Download Markdown"
                  >
                    <Download size={16} />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Report Preview Modal */}
      {selectedReportContent && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(5px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000,
          padding: '2rem'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '800px',
            maxHeight: '85vh',
            backgroundColor: '#0f172a',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '12px',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)'
          }}>
            <div style={{
              padding: '1.25rem 1.5rem',
              backgroundColor: '#1e293b',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>{selectedReportTitle}</h3>
              <button
                onClick={() => setSelectedReportContent(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{
              padding: '1.5rem',
              overflowY: 'auto',
              flex: 1,
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              whiteSpace: 'pre-wrap',
              color: '#e2e8f0',
              backgroundColor: 'rgba(0,0,0,0.2)'
            }}>
              {selectedReportContent}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
