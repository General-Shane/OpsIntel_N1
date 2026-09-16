import React, { useEffect, useState } from 'react';
import apiClient from '../../api/client';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { TrendingUp, BarChart2 } from 'lucide-react';

export const TrendCharts: React.FC = () => {
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get('/analytics/trends?days=14')
      .then(res => {
        setTrends(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load trends", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading Trend Visualizations...</div>;
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', margin: '1.5rem 0' }}>
      {/* Incident Velocity Trend */}
      <div className="card" style={{
        background: 'rgba(30, 41, 59, 0.7)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.08)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
          <TrendingUp size={20} color="#3b82f6" />
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>14-Day Incident Volume Trend</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Daily Inflow & Resolution Patterns</span>
          </div>
        </div>
        <div style={{ width: '100%', height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="incGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
              <XAxis dataKey="date" stroke="var(--text-secondary)" fontSize={11} tickLine={false} />
              <YAxis stroke="var(--text-secondary)" fontSize={11} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255, 255, 255, 0.1)', borderRadius: '6px' }}
                itemStyle={{ color: '#f8fafc' }}
              />
              <Area type="monotone" dataKey="incidents" stroke="#3b82f6" strokeWidth={2.5} fillOpacity={1} fill="url(#incGradient)" name="Incidents" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* SLA & Change Execution Comparison */}
      <div className="card" style={{
        background: 'rgba(30, 41, 59, 0.7)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.08)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
          <BarChart2 size={20} color="#22c55e" />
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Change Activity & SLA Compliance</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Executions vs. Target Rates</span>
          </div>
        </div>
        <div style={{ width: '100%', height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
              <XAxis dataKey="date" stroke="var(--text-secondary)" fontSize={11} tickLine={false} />
              <YAxis stroke="var(--text-secondary)" fontSize={11} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255, 255, 255, 0.1)', borderRadius: '6px' }}
              />
              <Bar dataKey="changes" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Changes" />
              <Bar dataKey="problems" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Problems" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
