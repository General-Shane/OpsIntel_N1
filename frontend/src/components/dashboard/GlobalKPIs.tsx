import React, { useEffect, useState } from 'react';
import apiClient from '../../api/client';
import { Activity, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

import { HealthScoreGauge } from './HealthScoreGauge';

export const GlobalKPIs: React.FC = () => {
  const [kpis, setKpis] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get('/analytics/kpis')
      .then(res => {
        setKpis(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load KPIs", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="card loading-placeholder">Loading KPIs...</div>;
  if (!kpis) return <div className="card error-placeholder">Failed to load KPIs</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {kpis.health_score && <HealthScoreGauge scoreData={kpis.health_score} />}
      
      <div className="kpi-grid">
        <div className="card kpi-card">
          <div className="kpi-header">
            <Activity size={24} className="icon-blue" />
            <span>Total Incidents</span>
          </div>
          <div className="kpi-value">{kpis.incidents.total_incidents}</div>
          <div className="kpi-subtext">{kpis.incidents.open_incidents} Open</div>
        </div>
        
        <div className="card kpi-card">
          <div className="kpi-header">
            <Clock size={24} className="icon-amber" />
            <span>MTTR (Hours)</span>
          </div>
          <div className="kpi-value">{kpis.incidents.mttr_hours}</div>
          <div className="kpi-subtext">Avg Resolution Time</div>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <AlertTriangle size={24} className="icon-red" />
            <span>Problem Backlog</span>
          </div>
          <div className="kpi-value">{kpis.problems.problem_backlog}</div>
          <div className="kpi-subtext">Avg Age: {kpis.problems.average_age_days}d</div>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <CheckCircle size={24} className={kpis.slas.compliance_rate_percent >= 95 ? "icon-green" : "icon-red"} />
            <span>SLA Compliance</span>
          </div>
          <div className="kpi-value">{kpis.slas.compliance_rate_percent}%</div>
          <div className="kpi-subtext">{kpis.slas.breached_slas} Breached</div>
        </div>
      </div>
    </div>
  );
};
