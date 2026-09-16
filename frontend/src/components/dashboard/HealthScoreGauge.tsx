import React from 'react';
import { ShieldCheck, AlertCircle, AlertOctagon } from 'lucide-react';

interface HealthScoreProps {
  scoreData: {
    health_score: number;
    status: string;
    breakdown: {
      sla_compliance_rate: number;
      active_p1: number;
      active_p2: number;
      problem_backlog: number;
      change_success_rate: number;
    };
  };
}

export const HealthScoreGauge: React.FC<HealthScoreProps> = ({ scoreData }) => {
  const { health_score, status, breakdown } = scoreData;

  const getStatusColor = (val: number) => {
    if (val >= 85) return 'var(--status-healthy)';
    if (val >= 70) return 'var(--status-warning)';
    return 'var(--status-critical)';
  };

  const getStatusBg = (val: number) => {
    if (val >= 85) return 'var(--status-healthy-bg)';
    if (val >= 70) return 'var(--status-warning-bg)';
    return 'var(--status-critical-bg)';
  };

  const getStatusBorder = (val: number) => {
    if (val >= 85) return 'var(--status-healthy-border)';
    if (val >= 70) return 'var(--status-warning-border)';
    return 'var(--status-critical-border)';
  };

  const getStatusIcon = (val: number) => {
    if (val >= 85) return <ShieldCheck size={24} color="var(--status-healthy)" />;
    if (val >= 70) return <AlertCircle size={24} color="var(--status-warning)" />;
    return <AlertOctagon size={24} color="var(--status-critical)" />;
  };

  const color = getStatusColor(health_score);
  const bg = getStatusBg(health_score);
  const border = getStatusBorder(health_score);

  return (
    <div className="card" style={{
      backgroundColor: '#FFFFFF',
      border: '1px solid var(--cg-border)',
      borderRadius: '10px',
      position: 'relative',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      height: '100%',
      minHeight: '170px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          {getStatusIcon(health_score)}
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Operational Health Index
            </h3>
            <span style={{ fontSize: '0.725rem', color: 'var(--text-secondary)' }}>
              Composite Service Stability Score
            </span>
          </div>
        </div>

        <span style={{
          padding: '0.2rem 0.65rem',
          borderRadius: '20px',
          fontSize: '0.7rem',
          fontWeight: 700,
          backgroundColor: bg,
          color: color,
          border: `1px solid ${border}`,
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          {status}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', margin: '0.25rem 0 0.75rem 0' }}>
        <span style={{ fontSize: '2.5rem', fontWeight: 800, color: color, lineHeight: 1 }}>{health_score}</span>
        <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: 500 }}>/ 100</span>
      </div>

      {/* Progress Bar */}
      <div style={{
        width: '100%',
        height: '6px',
        backgroundColor: 'var(--cg-surface-secondary)',
        borderRadius: '3px',
        overflow: 'hidden',
        marginBottom: '0.85rem'
      }}>
        <div style={{
          width: `${health_score}%`,
          height: '100%',
          backgroundColor: color,
          borderRadius: '3px',
          transition: 'width 0.8s ease'
        }} />
      </div>

      {/* Breakdown Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '0.5rem',
        paddingTop: '0.75rem',
        borderTop: '1px solid var(--cg-border)'
      }}>
        <div>
          <span style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)' }}>SLA Target</span>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>{breakdown.sla_compliance_rate}%</span>
        </div>
        <div>
          <span style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)' }}>Active P1s</span>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: breakdown.active_p1 > 0 ? 'var(--status-critical)' : 'var(--status-healthy)' }}>
            {breakdown.active_p1}
          </span>
        </div>
        <div>
          <span style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)' }}>Problem Backlog</span>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>{breakdown.problem_backlog}</span>
        </div>
        <div>
          <span style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)' }}>Change Success</span>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>{breakdown.change_success_rate}%</span>
        </div>
      </div>
    </div>
  );
};
