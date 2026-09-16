import React, { useEffect, useState } from 'react';
import apiClient from '../../api/client';
import { Activity } from 'lucide-react';

interface TrendData {
  date: string;
  incidents: number;
}

export const IncidentsHeatmap: React.FC = () => {
  const [data, setData] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/analytics/trends?days=90');
        setData(response.data);
      } catch (err) {
        console.error("Failed to load heatmap data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>Loading Heatmap...</div>;
  }

  const maxIncidents = Math.max(...data.map(d => d.incidents), 1);

  const getBackgroundColor = (count: number) => {
    if (count === 0) return '#EEF3F7';
    const ratio = count / maxIncidents;
    if (ratio < 0.2) return '#DCECF7';
    if (ratio < 0.4) return '#A7CCE7';
    if (ratio < 0.6) return '#5F9ECE';
    if (ratio < 0.8) return '#1769AA';
    return '#0F4E82';
  };

  return (
    <div className="card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={16} color="var(--cg-blue-primary)" />
          <h3 className="card-title">90-Day Incident Inflow Heatmap</h3>
        </div>
        <span className="badge badge-info">Daily Density</span>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(13px, 1fr))', gap: '4px' }}>
          {data.map((day, idx) => (
            <div 
              key={idx} 
              title={`${day.date}: ${day.incidents} incidents`}
              style={{
                width: '100%',
                aspectRatio: '1',
                borderRadius: '2px',
                backgroundColor: getBackgroundColor(day.incidents),
                cursor: 'pointer',
                transition: 'transform 0.15s ease'
              }}
            />
          ))}
        </div>
        
        <div style={{ marginTop: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.35rem', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
          <span>Less</span>
          <div style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: '#EEF3F7' }} />
          <div style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: '#DCECF7' }} />
          <div style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: '#A7CCE7' }} />
          <div style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: '#5F9ECE' }} />
          <div style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: '#1769AA' }} />
          <div style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: '#0F4E82' }} />
          <span>More</span>
        </div>
      </div>
    </div>
  );
};
