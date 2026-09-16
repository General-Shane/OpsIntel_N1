import React, { useState } from 'react';
import apiClient from '../../api/client';
import { ExecutiveReportView } from './ExecutiveReportView';
import {
  FileText,
  ToggleLeft,
  ToggleRight,
  Eye,
  RefreshCw,
  Play
} from 'lucide-react';

export const ReportsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'builder' | 'viewer'>('builder');
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('weekly');
  const [selectedReportType, setSelectedReportType] = useState('weekly_ops');
  const [generating, setGenerating] = useState(false);
  const [selectedRangeIndex, setSelectedRangeIndex] = useState(0);

  const generateDateRanges = (type: 'daily' | 'weekly' | 'monthly') => {
    const options = [];
    const now = new Date();
    for (let i = 0; i < 3; i++) {
      if (type === 'daily') {
        const d = new Date(now);
        d.setDate(d.getDate() - i);
        options.push({ label: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }), periodStr: `Aug ${d.getDate()}, 2026` });
      } else if (type === 'weekly') {
        const end = new Date(now);
        end.setDate(end.getDate() - (i * 7));
        const start = new Date(end);
        start.setDate(start.getDate() - 6);
        options.push({ 
          label: `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} (Week ${32 - i})`,
          periodStr: `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} → ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
        });
      } else {
        const d = new Date(now);
        d.setMonth(d.getMonth() - i);
        options.push({ label: d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }), periodStr: `${d.toLocaleDateString('en-US', { month: 'long' })} 1 - 31` });
      }
    }
    return options;
  };
  const dynamicRanges = generateDateRanges(period);
  const activeRange = dynamicRanges[selectedRangeIndex] || dynamicRanges[0];

  const [toggles, setToggles] = useState({
    executiveSummary: true,
    keyMetrics: true,
    incidentOverview: true,
    problemOverview: true,
    changeOverview: true,
    slaPerformance: true,
    serviceHealth: true,
    riskAnomalies: true,
    aiInsights: true,
  });

  const toggleHandler = (key: keyof typeof toggles) => {
    setToggles(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSelectAll = () => {
    setToggles({
      executiveSummary: true,
      keyMetrics: true,
      incidentOverview: true,
      problemOverview: true,
      changeOverview: true,
      slaPerformance: true,
      serviceHealth: true,
      riskAnomalies: true,
      aiInsights: true,
    });
  };

  const handleClearAll = () => {
    setToggles({
      executiveSummary: false,
      keyMetrics: false,
      incidentOverview: false,
      problemOverview: false,
      changeOverview: false,
      slaPerformance: false,
      serviceHealth: false,
      riskAnomalies: false,
      aiInsights: false,
    });
  };

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      await apiClient.post(`/reports/generate?period=${period}`);
      setActiveTab('viewer');
    } catch (err) {
      console.error("Report generation failed", err);
    } finally {
      setGenerating(false);
    }
  };

  if (activeTab === 'viewer') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <button
          onClick={() => setActiveTab('builder')}
          className="btn-cg-secondary"
          style={{ alignSelf: 'flex-start' }}
        >
          ← Back to Report Builder
        </button>
        <ExecutiveReportView />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <FileText color="var(--cg-blue-primary)" size={24} />
            Reports Engine
          </h1>
          <p className="page-subtitle">
            Generate and customize executive operational reports
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={() => setActiveTab('viewer')}
            className="btn-cg-secondary"
          >
            <Eye size={16} />
            <span>View Generated Reports</span>
          </button>
        </div>
      </div>

      <div className="tab-container">
        {(['daily', 'weekly', 'monthly'] as const).map((p) => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`tab-button ${period === p ? 'active' : ''}`}
            style={{ textTransform: 'capitalize' }}
          >
            {p}
          </button>
        ))}
      </div>

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1.25rem' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '50%', backgroundColor: 'var(--cg-blue-primary)', color: '#FFFFFF', fontWeight: 800, fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            1
          </div>
          <h3 className="card-title" style={{ margin: 0 }}>Select Reporting Period</h3>
        </div>

        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Time Range</span>
            <select
              value={selectedRangeIndex}
              onChange={(e) => setSelectedRangeIndex(Number(e.target.value))}
              style={{
                padding: '0.65rem 1rem',
                borderRadius: '7px',
                border: '1px solid var(--cg-border)',
                backgroundColor: 'var(--cg-surface-card)',
                color: 'var(--text-primary)',
                fontSize: '0.875rem',
                outline: 'none',
                minWidth: '280px'
              }}
            >
              {dynamicRanges.map((range, idx) => (
                <option key={idx} value={idx}>{range.label}</option>
              ))}
            </select>
          </div>

          <div style={{ padding: '0.65rem 1rem', borderRadius: '7px', backgroundColor: 'var(--cg-surface-secondary)', border: '1px solid var(--cg-border)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block' }}>Period Window</span>
            <strong style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>{activeRange.periodStr}</strong>
          </div>
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1.25rem' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '50%', backgroundColor: 'var(--cg-blue-primary)', color: '#FFFFFF', fontWeight: 800, fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            2
          </div>
          <h3 className="card-title" style={{ margin: 0 }}>Select Report Type</h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
          {[
            { id: 'weekly_ops', title: 'Weekly Operations Report', desc: 'Comprehensive overview of weekly operational health, trends, and insights.', icon: FileText, color: 'var(--cg-blue-primary)' },
            { id: 'incident_summary', title: 'Incident Summary Report', desc: 'Detailed summary of incidents, trends, and impact analysis.', icon: FileText, color: 'var(--status-critical)' },
            { id: 'sla_compliance', title: 'SLA Compliance Report', desc: 'SLA performance, compliance metrics, and breach analysis.', icon: FileText, color: 'var(--status-healthy)' },
            { id: 'change_success', title: 'Change Success Report', desc: 'Change success rate, failure analysis, and risk overview.', icon: FileText, color: 'var(--cg-cyan-accent)' },
          ].map((rt) => {
            const isSelected = selectedReportType === rt.id;
            return (
              <div
                key={rt.id}
                onClick={() => setSelectedReportType(rt.id)}
                style={{
                  padding: '1.25rem',
                  borderRadius: '8px',
                  border: isSelected ? '2px solid var(--cg-blue-primary)' : '1px solid var(--cg-border)',
                  backgroundColor: isSelected ? 'var(--cg-blue-soft)' : 'var(--cg-surface-card)',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <rt.icon size={22} color={rt.color} />
                  <div style={{
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    border: isSelected ? '5px solid var(--cg-blue-primary)' : '2px solid var(--cg-border)',
                    backgroundColor: 'var(--cg-surface-card)'
                  }} />
                </div>
                <div>
                  <h4 style={{ fontSize: '0.925rem', fontWeight: 700, color: 'var(--text-primary)' }}>{rt.title}</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.35rem', lineHeight: 1.4 }}>{rt.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1.25rem' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '50%', backgroundColor: 'var(--cg-blue-primary)', color: '#FFFFFF', fontWeight: 800, fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            3
          </div>
          <h3 className="card-title" style={{ margin: 0 }}>Configure Report Content</h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '2rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button onClick={handleSelectAll} className="btn-cg-secondary" style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}>Select All</button>
              <button onClick={handleClearAll} className="btn-cg-secondary" style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}>Clear All</button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.85rem' }}>
              {[
                { key: 'executiveSummary', label: 'Executive Summary' },
                { key: 'keyMetrics', label: 'Key Metrics' },
                { key: 'incidentOverview', label: 'Incident Overview' },
                { key: 'problemOverview', label: 'Problem Overview' },
                { key: 'changeOverview', label: 'Change Overview' },
                { key: 'slaPerformance', label: 'SLA Performance' },
                { key: 'serviceHealth', label: 'Service Health' },
                { key: 'riskAnomalies', label: 'Risk & Anomalies' },
                { key: 'aiInsights', label: 'AI Insights & Recommendations' },
              ].map((item) => {
                const k = item.key as keyof typeof toggles;
                const isOn = toggles[k];
                return (
                  <div
                    key={item.key}
                    onClick={() => toggleHandler(k)}
                    style={{
                      padding: '0.75rem 1rem',
                      borderRadius: '7px',
                      backgroundColor: 'var(--cg-surface-secondary)',
                      border: '1px solid var(--cg-border)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer'
                    }}
                  >
                    <span style={{ fontSize: '0.825rem', fontWeight: 500, color: 'var(--text-primary)' }}>{item.label}</span>
                    {isOn ? <ToggleRight size={24} color="var(--cg-blue-primary)" /> : <ToggleLeft size={24} color="var(--text-muted)" />}
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{
            padding: '1.25rem',
            borderRadius: '8px',
            backgroundColor: 'var(--cg-surface-secondary)',
            border: '1px solid var(--cg-border)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem'
          }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Report Preview
            </span>
            <div style={{ padding: '1rem', borderRadius: '7px', backgroundColor: 'var(--cg-surface-card)', border: '1px solid var(--cg-border)', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              <strong style={{ color: 'var(--text-primary)', display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>OPSINTEL</strong>
              <span>Weekly Operations Report</span>
              <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <div style={{ height: '6px', backgroundColor: '#CBD5E1', borderRadius: '3px', width: '80%' }} />
                <div style={{ height: '6px', backgroundColor: '#E2E8F0', borderRadius: '3px', width: '95%' }} />
                <div style={{ height: '6px', backgroundColor: '#E2E8F0', borderRadius: '3px', width: '60%' }} />
              </div>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>Estimated Pages: 12 - 15</span>
          </div>
        </div>
      </div>

      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 className="card-title" style={{ margin: 0 }}>Generate Report</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.825rem', marginTop: '0.2rem' }}>
            Click the button below to synthesize your operational intelligence document
          </p>
        </div>

        <button
          onClick={handleGenerateReport}
          disabled={generating}
          className="btn-cg-primary"
          style={{ padding: '0.75rem 1.75rem' }}
        >
          {generating ? <RefreshCw size={18} className="animate-spin" /> : <Play size={18} />}
          <span>{generating ? "Synthesizing Report..." : `Generate ${period.toUpperCase()} Report`}</span>
        </button>
      </div>
    </div>
  );
};
